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
        # Definição do Prompt Complexo com Persona e Estrutura JSON
        prompt = f"""
        Act as a Senior Recruitment Specialist, Career Consultant, and ATS Expert with specific experience in strategic consulting, technology, and organizational transformation in international markets.
        
        OBJECTIVE:
        Analyze the following CV content for a professional targeting the role/sector of '{role}' with '{experience}' of experience.
        Produce a professional, in-depth, result-oriented assessment suitable for mid-to-high seniority profiles.
        
        INPUT CONTEXT:
        CV Text: {text[:15000]} (truncated if too long)
        Target Role: {role}
        Experience Level: {experience}
        
        OUTPUT LANGUAGE: Portuguese (Portugal) - Professional, clear, non-generic.
        
        MANDATORY OUTPUT STRUCTURE (JSON ONLY):
        You must output ONLY a valid JSON object with the following schema. Do not include markdown code blocks like ```json.
        
        {{
            "executive_summary": {{
                "vision": "Resumo curto e objetivo do posicionamento do candidato no mercado (2-3 frases).",
                "market_fit_percentage": <int 0-100>,
                "strategic_read": "Leitura estratégica do perfil, senioridade percebida e coerência global."
            }},
            "ats_compatibility": {{
                "score": <int 0-100>,
                "explanation": "Explicação clara dos fatores que aumentam ou reduzem a pontuação.",
                "risk_analysis": "Risco estimado de exclusão automática (Baixo/Médio/Alto) e porquê."
            }},
            "structural_analysis": {{
                "clarity_score": <int 0-100>,
                "organization_feedback": "Avaliação da organização das secções.",
                "legibility_feedback": "Legibilidade técnica para humanos e ATS."
            }},
            "content_impact": {{
                "title_strength": "Avaliação da força dos títulos.",
                "metrics_presence": "Avaliação sobre a presença de métricas/resultados (Fraca/Moderada/Forte).",
                "verb_power": "Uso de verbos de ação adequados à senioridade.",
                "alignment_feedback": "Alinhamento entre experiência e setor alvo."
            }},
            "keywords": {{
                "missing": ["palavra1", "palavra2", "palavra3", "palavra4", "palavra5"],
                "suggested_alternatives": ["termo1", "termo2"],
                "language_balance_feedback": "Equilíbrio entre linguagem humana e algorítmica."
            }},
            "strengths": [
                "Ponto forte diferenciador 1",
                "Ponto forte diferenciador 2",
                "Ponto forte diferenciador 3"
            ],
            "improvements": [
                {{
                    "area": "Área de melhoria (ex: Resumo, Experiência)",
                    "impact": "Crítico" | "Alto" | "Médio",
                    "description": "Explicação do problema."
                }},
                {{ "area": "...", "impact": "...", "description": "..." }},
                {{ "area": "...", "impact": "...", "description": "..." }}
            ],
            "recommendations": [
                {{
                    "section_target": "Secção alvo (ex: Experiência Profissional)",
                    "actionable_tip": "Sugestão concreta do que fazer.",
                    "example": "Exemplo de frase ou formatação melhorada."
                }},
                {{ "section_target": "...", "actionable_tip": "...", "example": "..." }}
            ],
            "strategic_tips": [
                "Dica estratégica 1 (não genérica)",
                "Dica estratégica 2",
                "Dica estratégica 3"
            ],
            "final_assessment": {{
                "score": <int 0-100> (Readiness Index),
                "readiness_level": "Base sólida" | "Competitivo" | "Alto potencial" | "Pronto para mercado"
            }}
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text
            
            # Limpeza robusta do JSON
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            return json.loads(content.strip())
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return self._analyze_heuristics(text, role, experience) # Fallback seguro

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

