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
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

        # Heuristic fallbacks
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
                text = file_stream.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
        return text

    def analyze(self, file_stream, filename, role, experience_level):
        """
        Main analysis method using Gemini File API for robust PDF handling.
        Generates comprehensive analysis for both screen display and PDF report.
        """
        if not self.model:
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
            
            import tempfile
            
            suffix = ".pdf" if filename.lower().endswith(".pdf") else ".txt"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                file_stream.seek(0)
                tmp.write(file_stream.read())
                tmp_path = tmp.name

            mime_type = "application/pdf" if suffix == ".pdf" else "text/plain"
            uploaded_file = genai.upload_file(tmp_path, mime_type=mime_type)
            
            # PROMPT EXPANDIDO - Análise completa com foco em valor prático
            prompt = f"""
            Atua como Especialista Sénior em Recrutamento, Consultor de Carreira e Especialista em ATS.
            Analisa este CV para um profissional que visa '{role}' com experiência '{experience_level}'.
            
            IMPORTANTE: Toda a resposta DEVE ser em Português de Portugal (PT-PT).
            
            PRINCÍPIOS EDITORIAIS (OBRIGATÓRIOS):
            - Clareza acima de sofisticação. Estratégia acima de elogios. Informação acionável.
            - Linguagem humana e profissional (não promocional).
            - Palavras Proibidas (NUNCA USAR): "Consultoria", "Projeto", "Implementação", "Formação", "Metodologia proprietária", "Framework exclusivo".
            - Substituições: "Acompanhamento", "Decisão", "Posicionamento", "Clareza estratégica", "Conhecimento aplicável".
            
            CONTEXTO DE ENTRADA:
            Função Alvo: {role}
            Senioridade Alvo: {experience_level}
            
            DIMENSÕES DE PONTUAÇÃO (0-20 cada):
            1. Estrutura e Clareza: Ordem lógica, clareza de títulos, fluidez (objetivo: leitura < 20s). Penalizar textos densos.
            2. Conteúdo e Relevância: Adequação à senioridade, especificidade, progressão profissional.
            3. Compatibilidade ATS: Keywords da função, verbos de ação, estrutura de parsing.
            4. Impacto e Resultados: Métricas evidentes, KPIs, percentagens, outcomes vs tarefas.
            5. Marca Pessoal e Proposta de Valor: Identidade profissional clara, narrativa diferenciada, resumo forte.
            6. Riscos e Inconsistências: Lacunas temporais, mudanças frequentes, transições não explicadas.
            
            ESTRUTURA DE OUTPUT (JSON):
            {{
                "candidate_profile": {{
                    "detected_name": "Nome completo do candidato",
                    "detected_role": "Função atual/principal identificada",
                    "detected_sector": "Setor/Indústria identificado (ex: Tecnologia, Banca, Saúde, Retalho, Consultoria, etc.)",
                    "total_years_exp": "X anos",
                    "seniority": "Junior | Mid-Level | Sénior | Executivo"
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
                    "results_density": "<int>%",
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
                    "badge": "Excelente (85-100) | Forte (70-84) | Adequado (50-69) | Necessita Revisão (0-49)"
                }},
                
                "pdf_extended_content": {{
                    "sector_analysis": {{
                        "identified_sector": "Nome do setor identificado",
                        "sector_trends": "Tendências atuais do setor em Portugal e Europa",
                        "competitive_landscape": "Descrição do panorama competitivo para esta função neste setor"
                    }},
                    
                    "critical_certifications": [
                        {{
                            "name": "Nome da certificação (ex: PMP, PROSCI, ITIL, etc.)",
                            "issuer": "Entidade certificadora",
                            "relevance": "Porque é crítica para esta função/setor",
                            "priority": "Alta | Média | Baixa",
                            "estimated_investment": "Custo aproximado e duração",
                            "where_to_get": "Onde obter em Portugal ou online"
                        }}
                    ],
                    
                    "phrase_improvements": [
                        {{
                            "original": "Frase original extraída do CV (copiar exatamente)",
                            "problem": "O que está mal nesta frase",
                            "improved": "Versão melhorada da frase com impacto e métricas",
                            "explanation": "Explicação de porque a versão melhorada é superior"
                        }}
                    ],
                    
                    "cv_design_tips": {{
                        "layout": "Dicas específicas de layout e estrutura visual",
                        "typography": "Recomendações de fontes e tamanhos",
                        "spacing": "Dicas de espaçamento e margens",
                        "sections_order": "Ordem recomendada das secções para este perfil",
                        "length": "Recomendação de número de páginas",
                        "visual_elements": "O que incluir/evitar (gráficos, cores, fotos)"
                    }},
                    
                    "writing_guide": {{
                        "power_verbs": ["Lista de 10 verbos de ação recomendados para esta função"],
                        "keywords_to_add": ["Lista de 10 keywords ATS críticas para esta função"],
                        "phrases_to_avoid": ["Lista de 5 frases/expressões a evitar"],
                        "quantification_tips": "Como quantificar realizações nesta área específica"
                    }},
                    
                    "professional_development": {{
                        "short_term": [
                            {{
                                "action": "Ação específica a tomar nos próximos 30 dias",
                                "expected_impact": "Impacto esperado na carreira",
                                "resources": "Recursos específicos (cursos, livros, eventos)"
                            }}
                        ],
                        "medium_term": [
                            {{
                                "action": "Ação para os próximos 3-6 meses",
                                "expected_impact": "Impacto esperado",
                                "resources": "Recursos específicos"
                            }}
                        ],
                        "long_term": [
                            {{
                                "action": "Objetivos para 1-2 anos",
                                "expected_impact": "Impacto na progressão de carreira",
                                "resources": "Recursos e investimentos necessários"
                            }}
                        ]
                    }},
                    
                    "networking_strategy": {{
                        "linkedin_optimization": "Dicas específicas para otimizar o perfil LinkedIn",
                        "key_communities": ["Comunidades profissionais relevantes em Portugal"],
                        "events_to_attend": ["Tipos de eventos/conferências recomendados"],
                        "thought_leadership": "Como construir presença como especialista na área"
                    }},
                    
                    "salary_positioning": {{
                        "market_range": "Intervalo salarial típico para esta função/senioridade em Portugal",
                        "negotiation_leverage": "Pontos fortes do CV para negociação salarial",
                        "gaps_to_address": "O que falta para justificar salário mais elevado"
                    }}
                }}
            }}
            
            INSTRUÇÕES ADICIONAIS:
            1. Para "phrase_improvements", extrai 3-5 frases REAIS do CV e mostra como melhorá-las
            2. Para "critical_certifications", recomenda 3-5 certificações ESPECÍFICAS para o setor identificado
            3. Todas as recomendações devem ser práticas e acionáveis
            4. Usa exemplos concretos sempre que possível
            5. O conteúdo deve ser útil mesmo para quem não conhece a área
            6. Foca em certificações reconhecidas internacionalmente mas disponíveis em Portugal
            """

            # Generate Content with File reference
            response = self.model.generate_content([prompt, uploaded_file])
            
            # Cleanup File from Gemini
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
                "structure": int(radar.get("estrutura", 0) / 4),
                "content": int(radar.get("conteudo", 0) / 4),
                "ats": int(radar.get("ats", 0) / 4),
                "impact": int(radar.get("impacto", 0) / 4),
                "branding": int(radar.get("branding", 0) / 4),
                "risks": 5 - int(radar.get("riscos", 0) / 4)
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
        
        structure_score = self._score_structure(clean_text) * 5
        metrics_count = len(self.metrics_pattern.findall(text))
        impact_score = min(100, metrics_count * 10)
        
        return {
            "candidate_profile": {
                "detected_name": "Candidato (Análise Básica)",
                "detected_role": role or "Profissional",
                "detected_sector": "A identificar",
                "total_years_exp": experience_level or "Não detetada",
                "seniority": "A verificar"
            },
            "executive_summary": {
                "market_fit_score": 60,
                "three_sentences": [
                    "Perfil com base sólida identificada.",
                    "Necessita de maior detalhe em métricas de impacto.",
                    "Recomenda-se revisão com análise AI completa."
                ]
            },
            "dimensions": {
                "estrutura": {"score": 12, "signal": "Estrutura base presente", "missing": "Análise AI necessária", "upgrade": "Submeter novamente"},
                "conteudo": {"score": 10, "signal": "Conteúdo identificado", "missing": "Análise detalhada", "upgrade": "Verificar manualmente"},
                "ats": {"score": 10, "signal": "Formato básico OK", "missing": "Keywords específicas", "upgrade": "Otimizar para ATS"},
                "impacto": {"score": 8, "signal": "Algumas métricas", "missing": "Quantificação", "upgrade": "Adicionar números"},
                "branding": {"score": 10, "signal": "Perfil identificável", "missing": "Diferenciação", "upgrade": "Reforçar proposta de valor"},
                "riscos": {"score": 5, "signal": "Análise limitada", "missing": "Verificação completa", "upgrade": "Reanalisar"}
            },
            "radar_data": {
                "estrutura": 12,
                "conteudo": 10,
                "ats": 10,
                "impacto": 8,
                "branding": 10,
                "riscos": 5
            },
            "final_verdict": {
                "score": 55,
                "badge": "Análise Básica"
            },
            "global_score": 55,
            "score_band": "Análise Básica",
            "is_fallback": True,
            "pdf_extended_content": {
                "sector_analysis": {
                    "identified_sector": "A identificar com análise completa",
                    "sector_trends": "Submeta novamente para análise detalhada do setor.",
                    "competitive_landscape": "Análise de mercado requer processamento AI."
                },
                "critical_certifications": [
                    {
                        "name": "Certificação Genérica",
                        "issuer": "A determinar",
                        "relevance": "Análise AI necessária para recomendações específicas",
                        "priority": "Média",
                        "estimated_investment": "Variável",
                        "where_to_get": "Pesquisar após análise completa"
                    }
                ],
                "phrase_improvements": [
                    {
                        "original": "Análise de frases requer processamento AI",
                        "problem": "Não foi possível extrair frases sem análise completa",
                        "improved": "Submeta novamente para obter sugestões de melhoria",
                        "explanation": "A análise heurística não permite extração de frases específicas"
                    }
                ],
                "cv_design_tips": {
                    "layout": "Manter estrutura clara com secções bem definidas",
                    "typography": "Usar fontes profissionais como Arial, Calibri ou Helvetica",
                    "spacing": "Margens de 2-2.5cm, espaçamento 1.15",
                    "sections_order": "Resumo > Experiência > Formação > Competências",
                    "length": "1-2 páginas máximo",
                    "visual_elements": "Evitar gráficos excessivos, manter design limpo"
                },
                "writing_guide": {
                    "power_verbs": ["Liderei", "Implementei", "Otimizei", "Desenvolvi", "Geri", "Coordenei", "Alcancei", "Reduzi", "Aumentei", "Transformei"],
                    "keywords_to_add": ["Análise específica necessária"],
                    "phrases_to_avoid": ["Responsável por", "Ajudei a", "Participei em", "Fiz parte de", "Trabalhei com"],
                    "quantification_tips": "Adicionar números, percentagens e valores sempre que possível"
                },
                "professional_development": {
                    "short_term": [{"action": "Reanalisar CV com sistema AI", "expected_impact": "Obter recomendações específicas", "resources": "Share2Inspire CV Analyzer"}],
                    "medium_term": [{"action": "A definir após análise completa", "expected_impact": "A determinar", "resources": "A identificar"}],
                    "long_term": [{"action": "A definir após análise completa", "expected_impact": "A determinar", "resources": "A identificar"}]
                },
                "networking_strategy": {
                    "linkedin_optimization": "Otimizar perfil com keywords da função alvo",
                    "key_communities": ["LinkedIn Groups da área"],
                    "events_to_attend": ["Conferências do setor"],
                    "thought_leadership": "Partilhar conteúdo relevante regularmente"
                },
                "salary_positioning": {
                    "market_range": "Análise específica requer processamento AI",
                    "negotiation_leverage": "A identificar após análise completa",
                    "gaps_to_address": "A determinar"
                }
            }
        }

    # --- Heuristic Helpers ---
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
