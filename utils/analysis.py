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
        """
        Main analysis method using Gemini File API for robust PDF handling.
        Tries Gemini first, falls back to heuristics.
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
                file_stream.seek(0)
                tmp.write(file_stream.read())
                tmp_path = tmp.name

            # Upload to Gemini
            mime_type = "application/pdf" if suffix == ".pdf" else "text/plain"
            uploaded_file = genai.upload_file(tmp_path, mime_type=mime_type)
            
            # Wait for file processing if needed (small PDFs are usually instant, but good practice)
            # Active wait loop could be added here if files are large, but for CVs usually fine.
            
            # Definição do Prompt com princípios editoriais Share2Inspire e Requisitos Funcionais
            prompt = f"""
            Act as a Senior Recruitment Specialist, Career Consultant, and ATS Expert.
            Analyze this CV content for a professional targeting '{role}' with '{experience_level}' experience.
            
            EDITORIAL PRINCIPLES (MANDATORY):
            - Clarity over sophistication. Strategy over praise. Actionable info. 
            - Human, professional language (not promotional).
            - Forbidden Words (NEVER USE): "Consultoria", "Projeto", "Implementação", "Formação", "Metodologia proprietária", "Framework exclusivo".
            - Replacements: "Acompanhamento", "Decisão", "Posicionamento", "Clareza estratégica", "Conhecimento aplicável".
            
            INPUT CONTEXT:
            Target Role: {role}
            Target Seniority: {experience_level}
            
            SCORING DIMENSIONS (0-20 each):
            1. Estrutura e Clareza: Ordem lógica, clareza de títulos, fluidez (objetivo: leitura < 20s). Penalizar textos densos.
            2. Conteúdo e Relevância: Adequação à senioridade, especificidade, progressão profissional.
            3. Compatibilidade ATS: Keywords da função, verbos de ação, estrutura de parsing. (Reconhecer sinónimos).
            4. Impacto e Resultados: Métricas evidentes, KPIs, percentagens, outcomes vs tarefas.
            5. Marca Pessoal e Proposta de Valor: Identidade profissional clara, narrativa diferenciada, resumo forte.
            6. Riscos e Inconsistências: Lacunas temporais, mudanças frequentes, transições não explicadas.
            
            OUTPUT STRUCTURE (JSON):
            {{
                "candidate_profile": {{
                    "detected_name": "Nome",
                    "detected_role": "Função",
                    "total_years_exp": "Anos de experiência acumulada: N",
                    "seniority": "Senioridade Detetada"
                }},
                "executive_summary": {{
                    "three_sentences": [
                        "Frase 1 (Força): [Foco no impacto e domínio principal]",
                        "Frase 2 (Bloqueio): [O que impede a evolução imediata]",
                        "Frase 3 (Foco): [Ação recomendada para vantagem competitiva]"
                    ],
                    "market_fit_score": <int 0-100>
                }},
                "dimensions": {{
                    "estrutura": {{ "score": <0-20>, "signal": "O que está bem", "missing": "O que falta", "upgrade": "O que melhorar" }},
                    "conteudo": {{ "score": <0-20>, "signal": "...", "missing": "...", "upgrade": "..." }},
                    "ats": {{ "score": <0-20>, "signal": "...", "missing": "...", "upgrade": "..." }},
                    "impacto": {{ "score": <0-20>, "signal": "...", "missing": "...", "upgrade": "..." }},
                    "branding": {{ "score": <0-20>, "signal": "...", "missing": "...", "upgrade": "..." }},
                    "riscos": {{ "score": <0-20>, "signal": "...", "missing": "...", "upgrade": "..." }}
                }},
                "premium_indicators": {{
                    "value_prop_index": <int 0-10>,
                    "maturity_vs_role": "abaixo do esperado | adequado | acima da média",
                    "results_density": "<int 0-100>%",
                    "narrative_consistency": <int 0-100>
                }},
                "roadmap": {{
                    "rapido": "Ação imediata/reorganização",
                    "intermedio": "Ajuste de descrições/impacto",
                    "profundo": "Mudança de posicionamento/valor"
                }},
                "radar_data": {{
                    "estrutura": <0-20>, "conteudo": <0-20>, "ats": <0-20>, "impacto": <0-20>, "branding": <0-20>, "riscos": <0-20>
                }},
                "final_verdict": {{
                    "score": <int 0-100>,
                    "badge": "excelente (85-100) | forte (70-84) | adequado (50-69) | necessita revisão (0-49)"
                }}
            }}
            """

            # Generate Content with File reference
            response = self.model.generate_content([prompt, uploaded_file])
            
            # Cleanup File from Gemini (Optional but good practice)
            try:
                uploaded_file.delete()
            except Exception as e:
                print(f"Warning: Could not delete uploaded Gemini file: {e}")
                
            # Cleanup Temp File
            os.unlink(tmp_path)

            if not response.text:
                raise ValueError("Empty response from AI")

            # Robust JSON cleaning
            content = response.text.strip()
            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
                
            report = json.loads(content.strip())
            
            # Backward compatibility for old UI
            report["global_score"] = report.get("final_verdict", {}).get("score", 0)
            report["score_band"] = report.get("final_verdict", {}).get("badge", "N/A")
            radar = report.get("radar_data", {})
            report["dimensions"] = {
                "structure": int(radar.get("estrutura", 0) / 4), # Scale 20 to 5
                "content": int(radar.get("conteudo", 0) / 4),
                "ats": int(radar.get("ats", 0) / 4),
                "impact": int(radar.get("impacto", 0) / 4),
                "branding": int(radar.get("branding", 0) / 4),
                "risks": 5 - int(radar.get("riscos", 0) / 4) # Inverse for risk
            }
            return report

        except Exception as e:
            print(f"AI Analysis Failed: {e}")
            if uploaded_file:
                try: 
                    uploaded_file.delete()
                except: 
                    pass
                
            # Fallback
            try:
                file_stream.seek(0)
                text = self.extract_text(file_stream, filename)
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
        
        # Estrutura compatível com o novo output
        return {
            "candidate_profile": {
                "detected_name": "Candidato (Heurística)",
                "detected_role": role or "Profissional",
                "total_years_exp": experience_level or "Não detetada",
                "seniority": "Verificar manual"
            },
            "executive_summary": {
                "market_fit_score": 60,
                "screen_summary": [
                    { "title": "Estrutura Base", "metric": "Completa", "detail": "Secções essenciais detetadas." }
                ],
                "pdf_extended": "O perfil apresenta uma base sólida, mas requer maior ênfase em decisões estratégicas e métricas de impacto."
            },
            "maturity_and_skills": [
                { "title": "Comunicação", "metric": "Base", "detail": "Capacidade de expressão detetada." },
                { "title": "Organização", "metric": "Base", "detail": "Gestão de fluxos identificada." }
            ],
            "key_strengths": [
                { "title": "Presença Digital", "metric": "Sim", "detail": "LinkedIn ou contactos presentes." },
                { "title": "Estrutura", "metric": "80%", "detail": "Leitura facilitada por secções." }
            ],
            "evolution_roadmap": {
                "screen_summary": [
                    { "title": "Otimização de Métricas", "metric": "Alta", "detail": "Adicionar números às conquistas." }
                ],
                "pdf_details": [
                    { 
                        "title": "Foco em Resultados", 
                        "context": "A análise heurística indica falta de indicadores quantitativos.", 
                        "actions": ["Rever cada cargo", "Adicionar métricas de 0-100%"] 
                    }
                ]
            },
            "strategic_feedback": {
                "screen_summary": "Posicionamento sólido, mas passivo. Necessita de proatividade visual.",
                "pdf_details": {
                    "market_read": "Mercado competitivo exige diferenciação clara.",
                    "what_to_reinforce": "Sinais de liderança e autonomia.",
                    "what_to_adjust": "Verbos de ação e clareza estratégica."
                }
            },
            "radar_data": {
                "ats": 65,
                "impact": 50,
                "structure": 75,
                "market_fit": 60,
                "readiness": 60
            },
            "final_verdict": {
                "score": 60,
                "badge": "Base Sólida"
            },
            "global_score": 60,
            "score_band": "Base Sólida",
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

