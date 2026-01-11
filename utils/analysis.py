import re
import json
import os
import io
import tempfile
from PyPDF2 import PdfReader
import google.genai as genai
from utils.secrets import get_secret


class CVAnalyzer:
    """Analisador de CV com análises aprofundadas e robustas."""
    
    def __init__(self):
        self.api_key = get_secret("GEMINI_API_KEY")
        self.model = None
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-pro")
                print("[INFO] Modelo Gemini inicializado com sucesso.")
            except Exception as e:
                print(f"[ERRO] Falha ao inicializar modelo Gemini: {e}")
        else:
            print("[AVISO] Chave API Gemini não encontrada.")

        self.section_patterns = {
            "experience": ["experiência", "experience", "profissional", "work history", "employment", "carreira"],
            "education": ["formação", "education", "educação", "académico", "academic", "estudos", "qualificações"],
            "skills": ["competências", "skills", "habilidades", "ferramentas", "tools", "tecnologias", "aptidões"],
            "summary": ["resumo", "profile", "perfil", "sobre mim", "about me", "summary", "objetivo"],
            "languages": ["idiomas", "languages", "línguas", "linguístico"],
            "certifications": ["certificações", "certifications", "certificados", "acreditações"]
        }
        
        self.metrics_pattern = re.compile(
            r"(\d+%|\d+[\.,]\d+%?|\d+k|\d+m|\$[\d,]+|€[\d,]+|£[\d,]+|\d+\s*(mil|milhões?|billion|million))",
            re.IGNORECASE
        )

    def extract_text(self, file_stream, filename):
        """Extrai texto de ficheiros PDF ou texto."""
        text = ""
        try:
            if filename.lower().endswith(".pdf"):
                reader = PdfReader(file_stream)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            else:
                text = file_stream.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[ERRO] Falha na extração de texto: {e}")
            return ""
        return text

    def _build_analysis_prompt(self, role, experience_level):
        """Constrói o prompt de análise aprofundada."""
        return f"""...""" # Prompt omitido para brevidade

    def analyze(self, file_stream, filename, role, experience_level):
        """Analisa o CV e retorna um dicionário com os resultados."""
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

        except json.JSONDecodeError as e:
            print(f"[ERRO] Falha ao processar JSON: {e}")
            return self._heuristic_analysis(file_stream, filename)
            
        except Exception as e:
            print(f"[ERRO] Análise falhou: {e}")
            return self._heuristic_analysis(file_stream, filename)

    def _normalize_scores(self, analysis_data):
        """Normaliza e valida os scores para garantir consistência."""
        # ... (código de normalização omitido para brevidade)
        return analysis_data

    def _heuristic_analysis(self, file_stream, filename):
        """Análise heurística de fallback reconstruída."""
        print("[INFO] Executando análise heurística de fallback RECONSTRUÍDA...")
        
        file_stream.seek(0)
        text = self.extract_text(file_stream, filename)
        
        if not text:
            return {"error": "Não foi possível extrair texto do documento.", "analysis_type": "error"}

        section_scores = {}
        for section, keywords in self.section_patterns.items():
            found = any(re.search(r"\b" + kw + r"\b", text, re.IGNORECASE) for kw in keywords)
            section_scores[section] = 15 if found else 5
        
        has_metrics = bool(self.metrics_pattern.search(text))
        metrics_score = 15 if has_metrics else 5
        
        radar_data = {
            'estrutura': section_scores.get('summary', 10),
            'conteudo': section_scores.get('experience', 10),
            'ats': section_scores.get('skills', 10),
            'impacto': metrics_score,
            'branding': section_scores.get('summary', 10),
            'riscos': 10
        }
        
        return {
            "candidate_profile": {
                "detected_name": "Candidato (Análise de Segurança)",
                "detected_role": "Não identificado",
                "detected_sector": "Não identificado",
                "total_years_exp": "N/D",
                "seniority": "N/D",
                "education_level": "N/D",
                "languages_detected": [],
                "key_skills": []
            },
            "global_summary": {
                "strengths": ["Análise de segurança ativa", "Estrutura base do relatório garantida"],
                "improvements": ["API de análise avançada indisponível", "Conteúdo gerado com base em regras heurísticas"]
            },
            "executive_summary": {
                "global_score": int(sum(radar_data.values()) / len(radar_data) * 5),
                "global_score_breakdown": {
                    "structure_clarity": radar_data.get("estrutura", 0) * 5,
                    "content_relevance": radar_data.get("conteudo", 0) * 5,
                    "risks_inconsistencies": radar_data.get("riscos", 0) * 5,
                    "ats_compatibility": radar_data.get("ats", 0) * 5,
                    "impact_results": radar_data.get("impacto", 0) * 5,
                    "personal_brand": radar_data.get("branding", 0) * 5
                },
                "market_positioning": "### Análise de Posicionamento de Mercado (Modo de Segurança)\n\n- **Competitividade**: O seu perfil demonstra competências fundamentais, mas a ausência de uma análise detalhada pela IA impede uma avaliação aprofundada da sua competitividade no mercado atual.\n- **Diferenciação**: Recomenda-se a revisão do CV para garantir que os seus principais diferenciadores estão em destaque e alinhados com as expectativas para a sua função alvo.\n- **Oportunidade**: Utilize a próxima análise completa para obter insights sobre como o seu perfil se compara com benchmarks de mercado e como pode otimizar o seu posicionamento.",
                "key_decision_factors": "### Fatores-Chave de Decisão (Modo de Segurança)\n\n- **Primeira Impressão**: A estrutura do seu CV é o primeiro fator de decisão. Garanta que a leitura inicial seja fluida e que a sua proposta de valor seja clara nos primeiros 20 segundos.\n- **Resultados Quantificáveis**: A inclusão de métricas e resultados concretos é um fator decisivo para recrutadores. A análise completa irá avaliar a força dos seus KPIs.\n- **Alinhamento com a Vaga**: A personalização do CV para cada candidatura, destacando as competências mais relevantes, é um fator crítico de sucesso que a análise completa ajuda a otimizar."
            },
            "diagnostic_impact": {
                "first_30_seconds_read": "### Leitura em 30 Segundos (Modo de Segurança)\n\n- **Clareza**: A análise heurística sugere que a estrutura do CV permite uma leitura inicial, mas a clareza da proposta de valor pode não ser imediatamente óbvia.\n- **Foco**: É crucial que o seu objetivo profissional e a sua principal área de especialização sejam identificáveis à primeira vista.\n- **Ação Recomendada**: Reveja o seu resumo e os títulos das secções para garantir que comunicam o seu valor de forma rápida e eficaz.",
                "impact_strengths": "### Pontos de Impacto (Modo de Segurança)\n\n- **Potencial de Impacto**: A análise completa identifica os pontos do seu CV que geram maior impacto, como resultados quantificados e progressão de carreira.\n- **Oportunidade**: No modo de segurança, recomendamos que verifique se cada ponto da sua experiência profissional responde à pergunta: \'Qual foi o resultado do meu trabalho?\'",
                "impact_strengths_signal": "Análise de sinais de impacto indisponível.",
                "impact_strengths_missing": "Análise de pontos em falta indisponível.",
                "impact_dilutions": "### Pontos de Diluição (Modo de Segurança)\n\n- **Generalidade**: A análise heurística não consegue avaliar a especificidade da linguagem, mas é comum que a falta de detalhes concretos dilua o impacto do CV.\n- **Falta de Foco**: Um CV que tenta abranger demasiadas áreas pode confundir o recrutador. A análise completa ajudaria a focar a sua narrativa."
            },
            "content_structure_analysis": {
                "organization_hierarchy": "### Organização e Estrutura (Modo de Segurança)\n\n- **Estrutura Base**: O sistema identificou a presença de secções chave, o que é um bom ponto de partida.\n- **Otimização**: A análise completa avalia a ordem das secções, o uso de espaço em branco e a hierarquia visual para garantir uma leitura ótima.",
                "organization_hierarchy_signal": "Análise de sinais de organização indisponível.",
                "organization_hierarchy_missing": "Análise de pontos em falta indisponível.",
                "content_completeness": "### Completude do Conteúdo (Modo de Segurança)\n\n- **Secções Essenciais**: A análise heurística verifica a presença de secções como Experiência e Educação.\n- **Profundidade**: A análise completa avalia se cada secção tem a profundidade e o detalhe adequados para a sua senioridade.",
                "content_completeness_signal": "Análise de sinais de completude indisponível.",
                "content_completeness_missing": "Análise de pontos em falta indisponível."
            },
            "ats_digital_recruitment": {
                "keyword_optimization": "### Otimização para ATS (Modo de Segurança)\n\n- **Palavras-Chave**: A análise heurística não avalia a otimização de palavras-chave, um fator crítico para passar nos sistemas de triagem automática (ATS).\n- **Ação Recomendada**: Garanta que o seu CV inclui os termos e tecnologias mais comuns na sua área e nas descrições de vagas para as quais se candidata.",
                "keyword_optimization_signal": "Análise de sinais de otimização indisponível.",
                "keyword_optimization_missing": "Análise de pontos em falta indisponível.",
                "format_parsing": "### Formatação e Parsing (Modo de Segurança)\n\n- **Compatibilidade**: Utilize um formato de ficheiro e uma estrutura simples (evite tabelas, colunas e imagens) para garantir que os ATS conseguem ler o seu CV corretamente.\n- **Validação**: A análise completa simula a leitura por um ATS para identificar potenciais problemas de parsing.",
                "format_parsing_signal": "Análise de sinais de formatação indisponível.",
                "format_parsing_missing": "Análise de pontos em falta indisponível."
            },
            "strategic_risks": {
                "career_gaps": "### Lacunas de Carreira (Modo de Segurança)\n\n- **Contexto é Chave**: A análise heurística não consegue interpretar lacunas de carreira. Se existirem, é fundamental contextualizá-las (ex: formação, projetos pessoais, etc.).",
                "career_gaps_signal": "Análise de sinais de lacunas indisponível.",
                "career_gaps_missing": "Análise de pontos em falta indisponível.",
                "frequent_changes": "### Mudanças Frequentes (Modo de Segurança)\n\n- **Narrativa**: Mudanças frequentes de emprego podem ser um sinal de alerta se não forem justificadas por uma narrativa de crescimento e progressão.",
                "frequent_changes_signal": "Análise de sinais de mudanças indisponível.",
                "frequent_changes_missing": "Análise de pontos em falta indisponível."
            },
            "evolution_roadmap": {
                "quick_wins": "- **Resumo Profissional**: Reveja o seu resumo para garantir que é uma proposta de valor clara e impactante.\n- **Métricas**: Adicione pelo menos uma métrica ou resultado quantificável a cada uma das três experiências mais recentes.",
                "medium_term": "- **Personalização**: Adapte o seu CV para cada candidatura, destacando as competências e experiências mais relevantes para a vaga específica.",
                "long_term": "- **Branding Pessoal**: Desenvolva uma narrativa consistente em todas as suas plataformas profissionais (LinkedIn, etc.) que reforce a sua marca pessoal."
            },
            "radar_data": radar_data,
            "analysis_type": "heuristic"
        }
