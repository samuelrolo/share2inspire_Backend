import re
import json
import os
import io
from PyPDF2 import PdfReader
import google.generativeai as genai
from utils.secrets import get_secret

class CVAnalyzer:
    def __init__(self):
        # Configure Gemini API if key is available
        self.api_key = get_secret("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Use a model that supports JSON mode well, e.g., gemini-1.5-flash or pro
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

        # Heuristic fallbacks (stripped down for class brevity if not used)
        self.sections = {
            "experience": ["experiência", "experience", "profissional", "work history", "employment"],
            "education": ["formação", "education", "educação", "academico", "academic", "estudos"],
            "skills": ["competências", "skills", "habilidades", "ferramentas", "tools", "tecnologias"],
            "summary": ["resumo", "profile", "perfil", "sobre mim", "about me", "summary"],
            "contacts": ["contacto", "contact", "email", "telefone", "phone", "linkedin"]
        }
        self.metrics_pattern = re.compile(r'(\d+%|\d+[\.,]\d+|\d+k|\d+m|\$|€|£|mil|million|bilion|billion)', re.IGNORECASE)

    def extract_text(self, file_stream, filename):
        """Extract text from PDF or plain text file."""
        text = ""
        try:
            if filename.lower().endswith('.pdf'):
                reader = PdfReader(file_stream)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            else:
                # Fallback for text/other formats if supported
                text = file_stream.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
        return text

    def analyze(self, file_stream, filename, role, experience_level):
        """Main analysis method. Tries Gemini first, falls back to heuristics."""
        text = self.extract_text(file_stream, filename)
        if not text:
            return {"error": "Could not extract text from file"}
            
        clean_text = text[:10000] # Limit context window just in case
        
        # 1. Try AI Analysis
        if self.model:
            try:
                print("Iniciando análise com Gemini AI...")
                return self._analyze_with_ai(clean_text, role, experience_level)
            except Exception as e:
                print(f"Erro na análise AI: {e}. Falling back to heuristics.")
        
        # 2. Fallback to Heuristics
        return self._analyze_heuristics(clean_text, role, experience_level)

    def _analyze_with_ai(self, text, role, experience):
        prompt = f"""
        Act as an expert Career Coach and CV Analyst. Analyze the following CV content for a professional targeting the role of '{role}' with '{experience}' of experience.
        
        CV Content:
        {text}

        You must strictly output ONLY a JSON object with the following structure. Do not output markdown code blocks, just the raw JSON.
        
        Structure Requirements:
        1. "global_score": 0-100 (weighted average of dimensions).
        2. "score_band": "Excelente" (85-100), "Forte" (70-84), "Adequado" (50-69), or "Necessita Revisão" (0-49).
        3. "dimensions": Object with 0-20 scores for: "structure", "content", "ats", "impact", "branding", "risks".
        4. "insights": Object with keys "structure", "content", "ats", "impact", "branding", "risks". Each key maps to an object with lists: "signal_strength" (what is good), "missing_pieces" (what is missing), "upgrade_suggestions" (actionable tips).
        5. "premium_indicators": Object with "value_proposition_index" (0-10), "professional_maturity" (string), "result_density" (string %), "narrative_consistency" (string).
        6. "roadmap": Object with lists "quick_wins", "intermediate", "deep".
        7. "executive_summary": List of exactly 3 strings (Strength, Blocker, Competitive Advantage Focus).

        Criteria:
        - Penalize generic descriptions.
        - Reward quantitative metrics (impact).
        - Check alignment with '{role}'.
        - Be critical but constructive.
        """
        
        response = self.model.generate_content(prompt)
        
        # Clean response (sometimes it comes with ```json ... ```)
        content = response.text
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        elif "```" in content:
            content = content.replace("```", "")
            
        return json.loads(content)

    def _analyze_heuristics(self, text, role, experience_level):
        clean_text = text.lower()
        
        scores = {
            "structure": self._score_structure(clean_text),
            "content": self._score_content(clean_text, role),
            "ats": 15, # Optimistic default
            "impact": self._score_impact(clean_text),
            "branding": self._score_branding(clean_text),
            "risks": 18 # Optimistic default
        }
        
        global_score = sum(scores.values()) # Approx sum to 100ish
        global_score = min(100, max(0, int(global_score)))

        return {
            "global_score": global_score,
            "score_band": self._get_score_band(global_score),
            "dimensions": scores,
            "insights": self._generate_heuristic_insights(scores),
            "premium_indicators": {
                "value_proposition_index": 7,
                "professional_maturity": "Adequado",
                "result_density": "15%",
                "narrative_consistency": "Linear"
            },
            "roadmap": {
                "quick_wins": ["Use um template mais limpo"],
                "intermediate": ["Adicione métricas nas experiências"],
                "deep": ["Reescreva o perfil profissional"]
            },
            "executive_summary": [
                "O CV apresenta uma estrutura base funcional.",
                "Falta diferenciação através de resultados quantitativos.",
                "Foques em demonstrar impacto direto nos projetos anteriores."
            ]
        }

    def _get_score_band(self, score):
        if score >= 85: return "Excelente"
        if score >= 70: return "Forte"
        if score >= 50: return "Adequado"
        return "Necessita Revisão"

    # --- Heuristic Helpers (Simplified) ---
    def _score_structure(self, text):
        score = 10
        found_sections = sum(1 for keys in self.sections.values() if any(k in text for k in keys))
        score += min(10, found_sections * 2)
        return min(20, score)

    def _score_content(self, text, role):
        score = 10
        if role and role.lower() in text: score += 5
        return min(20, score)

    def _score_impact(self, text):
        metrics_count = len(self.metrics_pattern.findall(text))
        score = 5 + min(15, metrics_count * 2)
        return min(20, score)

    def _score_branding(self, text):
        return 10 + (5 if any(k in text for k in self.sections["summary"]) else 0)

    def _generate_heuristic_insights(self, scores):
        # Return generic structure to avoid frontend crash
        return {k: {"signal_strength": [], "missing_pieces": [], "upgrade_suggestions": []} for k in scores.keys()}
