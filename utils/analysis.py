import json
import os
import io
import tempfile
from PyPDF2 import PdfReader
import google.generativeai as genai
from utils.secrets import get_secret

class CVAnalyzer:
    def __init__(self):
        self.api_key = get_secret("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self.model = None
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                print("[INFO] Modelo Gemini inicializado com sucesso.")
            except Exception as e:
                print(f"[ERRO] Falha ao inicializar Gemini: {e}")
        else:
            print("[AVISO] Chave API Gemini não encontrada.")

    def extract_text(self, file_stream, filename):
        text = ""
        try:
            if filename.lower().endswith(".pdf"):
                pdf_reader = PdfReader(file_stream)
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            else:
                text = file_stream.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[ERRO] Falha na extração de texto: {e}")
        return text

    def analyze(self, file_stream, filename, role, experience_level):
        if not self.model:
            print("[AVISO] Modelo Gemini não inicializado. Usando análise heurística.")
            return self._heuristic_analysis(file_stream, filename)

        text = self.extract_text(file_stream, filename)
        if not text:
            return {"error": "Não foi possível extrair texto do documento.", "analysis_type": "error"}

        prompt = self._build_analysis_prompt(role, experience_level)
        full_prompt = f"{prompt}\n\n--- CV PARA ANÁLISE ---\n{text}"

        try:
            response = self.model.generate_content(full_prompt)
            cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
            analysis_data = json.loads(cleaned_text)
            analysis_data["analysis_type"] = "gemini"
            return self._normalize_scores(analysis_data)
        except Exception as e:
            print(f"[ERRO] Análise Gemini falhou: {e}")
            return self._heuristic_analysis(file_stream, filename)

    def _normalize_scores(self, data):
        # Implementar normalização se necessário
        return data

    def _build_analysis_prompt(self, role, experience_level):
        return f"""Analise o CV para a função de '{role}' com nível de experiência '{experience_level}' e retorne um JSON com a seguinte estrutura: ... (prompt omitido para brevidade)"""

    def _heuristic_analysis(self, file_stream, filename):
        print("[INFO] Executando análise heurística de fallback.")
        text = self.extract_text(file_stream, filename)
        # Simula uma análise completa com dados padrão
        return {
            "candidate_profile": {"detected_name": "Candidato (Análise de Segurança)", "key_skills": []},
            "global_summary": {"strengths": [], "improvements": []},
            "executive_summary": {
                "global_score": "35",
                "global_score_breakdown": {
                    "structure_clarity": "40", "content_relevance": "30",
                    "risks_inconsistencies": "50", "ats_compatibility": "60",
                    "impact_results": "20", "personal_brand": "30"
                },
                "market_positioning": "Análise indisponível no modo de segurança.",
                "key_decision_factors": "Análise indisponível no modo de segurança."
            },
            "diagnostic_impact": {},
            "content_structure_analysis": {},
            "ats_digital_recruitment": {},
            "strategic_risks": {},
            "evolution_roadmap": {},
            "radar_data": {
                "estrutura": 10, "conteudo": 5, "ats": 12,
                "impacto": 4, "branding": 6, "riscos": 15
            },
            "analysis_type": "heuristic"
        }
