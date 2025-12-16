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
            self.model = genai.GenerativeModel('gemini-flash-latest')
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

    def analyze(self, file_storage, filename, role=None, experience_level=None):
        """
        Main analysis method using Gemini File API for robust PDF handling.
        """
        if not self.model:
            # Try to re-init model with standard 1.5 flash name if not set
            if self.api_key:
                 self.model = genai.GenerativeModel('gemini-1.5-flash')
            else:
                return {
                    "error": "Gemini Model not initialized. Check API Key.",
                    "analysis_type": "error"
                }

        uploaded_file = None
        try:
            print(f"Iniciando análise AI via File API para {filename}...")
            
            # Save file temporarily to upload (File API requires path or file-like with name often)
            # We will use a temp file for safety
            import tempfile
            
            suffix = ".pdf" if filename.lower().endswith(".pdf") else ".txt"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                file_storage.seek(0)
                tmp.write(file_storage.read())
                tmp_path = tmp.name

            # Upload to Gemini
            uploaded_file = genai.upload_file(tmp_path, mime_type="application/pdf" if suffix == ".pdf" else "text/plain")
            
            # Wait for file processing if needed (small PDFs are usually instant, but good practice)
            # Active wait loop could be added here if files are large, but for CVs usually fine.
            
            # Context info
            role_context = f"Target Role: {role}" if role else "Target Role: Auto-detect from CV"
            exp_context = f"Experience Level: {experience_level}" if experience_level else "Experience Level: Auto-detect"
            
            # Prompt (Reduced for brevity but kept core instructions)
            prompt = f"""
            You are Marlene Ruivo, a Senior Strategic Recruitment Consultant.
            Analyze this CV.
            
            OBJECTIVE:
            1. Auto-detect Target Role and Seniority.
            2. Evaluate against detected standard or: {role_context}, {exp_context}.
            
            OUTPUT: JSON ONLY (No markdown). Strict Portuguese (PT-PT).
            Structure:
            {{
                "candidate_profile": {{
                    "detected_name": "Name", "detected_role": "Role", "detected_years_exp": "Years", "seniority_level": "Level"
                }},
                "executive_summary": {{ "vision": "Summary", "market_fit_score": 0-100, "strategic_feedback": "Feedback" }},
                "ats_compatibility": {{ "score": 0-100, "risk_factors": [], "advice": "" }},
                "content_analysis": {{ "impact_score": 0-100, "verb_power": "", "metrics_usage": "", "critique": "" }},
                "structure_design": {{ "score": 0-100, "feedback": "" }},
                "key_strengths": ["Str1", "Str2"],
                "improvement_areas": [ {{ "area": "", "severity": "", "suggestion": "" }} ],
                "skills_cloud": ["Skill1", "Skill2"],
                "final_verdict": {{ "readiness_score": 0-100, "badge": "", "closing_comment": "" }}
            }}
            """

            # Generate Content with File reference
            response = self.model.generate_content([prompt, uploaded_file])
            
            # Cleanup File from Gemini (Optional but good practice)
            try:
                uploaded_file.delete()
            except:
                pass
                
            # Cleanup Temp File
            os.unlink(tmp_path)

            if not response.text:
                raise ValueError("Empty response from AI")

            # Clean JSON
            json_str = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(json_str)

        except Exception as e:
            print(f"AI Analysis Failed: {e}")
            if uploaded_file:
                try: uploaded_file.delete()
                except: pass
                
            # Fallback
            try:
                file_storage.seek(0)
                text = self.extract_text(file_storage, filename)
                fallback_result = self._analyze_heuristics(text, role, experience_level)
                fallback_result["ai_error"] = str(e)
                return fallback_result
            except Exception as fallback_err:
                 return {"error": f"Critical Analysis Error: {str(e)} -> {str(fallback_err)}"}

    def _analyze_heuristics(self, text, role, experience_level):
        """Fallback estruturado para quando a AI falha ou não está configurada."""
        clean_text = text.lower()
        
        # Lógica simplificada de scores
        structure_score = self._score_structure(clean_text) * 5 # Scale to 100 roughly
        metrics_count = len(self.metrics_pattern.findall(text))
        impact_score = min(100, metrics_count * 10)
        
        # Estrutura compatível com o output da AI
        return {
            "executive_summary": {
                "vision": "Análise preliminar automatizada (Modo Simplificado). O perfil apresenta elementos base, mas requer revisão humana detalhada.",
                "market_fit_percentage": 50,
                "strategic_read": "O CV possui estrutura legível. Recomenda-se adicionar métricas quantitativas para elevar a senioridade percebida."
            },
            "ats_compatibility": {
                "score": 60,
                "explanation": "Formato de texto extraído com sucesso. Estrutura parece standard.",
                "risk_analysis": "Médio. Evite colunas complexas ou gráficos que dificultem a leitura."
            },
            "structural_analysis": {
                "clarity_score": structure_score,
                "organization_feedback": "Secções padrão identificadas. Garanta que o Resumo Profissional está no topo.",
                "legibility_feedback": "Utilize fontes padrão e evite blocos densos de texto."
            },
            "content_impact": {
                "title_strength": "Verificar se os títulos dos cargos são padrão de mercado.",
                "metrics_presence": "Moderada" if metrics_count > 2 else "Fraca",
                "verb_power": "Use verbos de ação como 'Liderei', 'Desenvolvi', 'Aumentei'.",
                "alignment_feedback": f"Verificar alinhamento com {role}."
            },
            "keywords": {
                "missing": ["Liderança", "Estratégia", "Gestão de Projetos", "Inglês", "Orçamento"] if "gestão" not in clean_text else [],
                "suggested_alternatives": ["Management", "Leadership"],
                "language_balance_feedback": "Certifique-se de usar a terminologia técnica da sua área."
            },
            "strengths": [
                "Estrutura base identificável",
                "Informações de contacto presentes"
            ],
            "improvements": [
                {
                    "area": "Impacto e Resultados",
                    "impact": "Alto",
                    "description": "Falta de quantificação de resultados (números, %, valores)."
                },
                {
                    "area": "Palavras-chave",
                    "impact": "Médio",
                    "description": "Pode precisar de mais termos técnicos específicos da vaga."
                }
            ],
            "recommendations": [
                {
                    "section_target": "Experiência Profissional",
                    "actionable_tip": "Transforme responsabilidades em conquistas.",
                    "example": "Em vez de 'Responsável por vendas', use 'Aumentei as vendas em 20%'."
                }
            ],
            "strategic_tips": [
                "Adapte o CV para cada candidatura.",
                "Mantenha o CV em no máximo 2 páginas.",
                "Revise a gramática cuidadosamente."
            ],
            "final_assessment": {
                "score": int((structure_score + impact_score + 60) / 3),
                "readiness_level": "Base sólida"
            },
            "is_fallback": True
        }

    # --- Heuristic Helpers (Mantidos) ---
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

