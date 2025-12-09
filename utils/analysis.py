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
        result = self._analyze_heuristics(clean_text, role, experience_level)
        result["analysis_type"] = "heuristic"
        result["ai_error"] = "Gemini Model not initialized (Check API Key)" if not self.model else "AI generation failed"
        return result

    def _analyze_with_ai(self, text, role, experience):
        prompt = f"""
        You are an elite Executive Career Coach with 20+ years of experience in Talent Acquisition for Fortune 500 companies.
        Analyze the following CV content for a professional targeting the role of '{role}' with '{experience}' of experience.

        CV Content:
        {text}

        Your goal is to provide a "Tough Love", professional, and highly specific analysis. Avoid generic fluff. Be direct about what is missing.

        You MUST output ONLY a valid JSON object with the following structure:

        {{
            "global_score": <int 0-100>,
            "score_band": <string "Excelente" (90-100) | "Bom" (70-89) | "Razoável" (50-69) | "Fraco" (0-49)>,
            "summary_text": <string: A 2-sentence professional summary of the CV's current state>,
            "dimensions": {{
                "structure": <int 0-100>,
                "content_relevance": <int 0-100>,
                "impact_metrics": <int 0-100>,
                "ats_compatibility": <int 0-100>,
                "visual_clarity": <int 0-100>
            }},
            "key_strengths": [
                <string: Specific strength 1>,
                <string: Specific strength 2>
            ],
            "critical_improvements": [
                <string: High priority fix 1>,
                <string: High priority fix 2>,
                <string: High priority fix 3>
            ],
            "ats_keywords_missing": [
                <string: keyword 1>,
                <string: keyword 2>,
                <string: keyword 3>
            ]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text
            
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        data = json.loads(content)
        data["analysis_type"] = "ai"
        return data
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            # Clean response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            return json.loads(content.strip())
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            # Return a fallback structure so frontend doesn't break
            return {
                "global_score": 50,
                "score_band": "Erro na Análise",
                "summary_text": "Não foi possível processar a análise detalhada neste momento.",
                "dimensions": {k: 50 for k in ["structure", "content_relevance", "impact_metrics", "ats_compatibility", "visual_clarity"]},
                "key_strengths": ["N/A"],
                "critical_improvements": ["Tente novamente"],
                "ats_keywords_missing": []
            }
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

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
