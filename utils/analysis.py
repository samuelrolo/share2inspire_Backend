
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
        print(f"[DEBUG] API Key retrieved: {bool(self.api_key)}")
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-pro")
                print("[DEBUG] Gemini model initialized successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to configure Gemini API or initialize model: {e}")
                self.model = None
        else:
            self.model = None
            print("[DEBUG] Gemini API Key not found, model not initialized.")

        # Heuristic fallbacks
        self.sections = {
            "experience": ["experiência", "experience", "profissional", "work history", "employment"],
            "education": ["formação", "education", "educação", "academico", "academic", "estudos"],
            "skills": ["competências", "skills", "habilidades", "ferramentas", "tools", "tecnologias"],
            "summary": ["resumo", "profile", "perfil", "sobre mim", "about me", "summary"],
            "contacts": ["contacto", "contact", "email", "telefone", "phone", "linkedin"]
        }
        self.metrics_pattern = re.compile(r"(\d+%|\d+[\.,]\d+|\d+k|\d+m|\$|€|£|mil|million|bilion|billion)", re.IGNORECASE)

    def extract_text(self, file_stream, filename):
        """Extract text from PDF or plain text file."""
        text = ""
        try:
            if filename.lower().endswith(".pdf"):
                reader = PdfReader(file_stream)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            else:
                text = file_stream.read().decode("utf-8", errors="ignore")
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
            print("[DEBUG] Model is None in analyze method. Attempting re-initialization.")
            if self.api_key:
                try:
                    genai.configure(api_key=self.api_key)
                    self.model = genai.GenerativeModel("gemini-pro")
                    print("[DEBUG] Gemini model re-initialized successfully in analyze method.")
                except Exception as e:
                    print(f"[ERROR] Failed to re-initialize Gemini API or model in analyze method: {e}")
                    self.model = None
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
            Analisa este currículo para um profissional que visa \'{role}\' com experiência \'{experience_level}\'.
            
            
            IMPORTANTE: Toda a resposta DEVE ser em Português de Portugal (PT-PT), com linguagem formal e profissional.
            
            REGRA DE DENSIDADE (OBRIGATÓRIA E CRÍTICA):
            - CADA CAMPO DE TEXTO DEVE CONTER NO MÍNIMO 400 PALAVRAS E NO MÁXIMO 600 PALAVRAS.
            - PROIBIDO TERMINANTEMENTE: Respostas curtas, listas simples, frases isoladas, etiquetas ou bullet points.
            - OBRIGATÓRIO: Parágrafos EXTREMAMENTE densos, interpretativos, analiticamente ricos, com linguagem executiva e profundidade de consultoria sénior.
            - CADA PARÁGRAFO DEVE TER NO MÍNIMO 7-10 FRASES COMPLETAS E CONTEXTUALIZADAS.
            - Desenvolver cada ponto com exemplos concretos, implicações práticas detalhadas, justificação estratégica robusta e comparação explícita com benchmarks de mercado e senioridade.
            - Se a resposta for inferior a 400 palavras, a IA DEVE EXPANDIR O CONTEÚDO COM MAIS ANÁLISE, DETALHE, JUSTIFICAÇÃO E EXEMPLOS ATÉ ATINGIR O MÍNIMO.
            - A IA DEVE AUTO-AVALIAR RIGOROSAMENTE O COMPRIMENTO E A DENSIDADE ANTES DE FINALIZAR CADA RESPOSTA. Se não cumprir, DEVE REESCREVER.
            
            PRINCÍPIOS EDITORIAIS (OBRIGATÓRIOS):
            - Clareza acima de sofisticação. Estratégia acima de elogios. Informação acionável.
            - Linguagem humana e profissional (não promocional), sem clichés ou frases vagas. Rigor na gramática, modos verbais e conjugações do Português de Portugal.
            - Inferir e articular um posicionamento estratégico chave para o candidato, se aplicável, e integrá-lo na análise.
            - Palavras Proibidas (NUNCA USAR): "Consultoria", "Projeto", "Implementação", "Formação", "Metodologia proprietária", "Framework exclusivo".
            - Substituições: "Acompanhamento", "Decisão", "Posicionamento", "Clareza estratégica", "Conhecimento aplicável", "Iniciativa", "Desenvolvimento", "Capacitação", "Modelo exclusivo".
            
            CONTEXTO DE ENTRADA:
            Função Alvo: {role}
            Senioridade Alvo: {experience_level}
            
            DIMENSÕES DE PONTUAÇÃO (0-20 cada):
            1. Estrutura e Clareza: Ordem lógica, clareza de títulos, fluidez (objetivo: leitura < 20s). Penalizar textos densos e excesso de espaço em branco.
            2. Conteúdo e Relevância: Adequação à senioridade, especificidade, progressão profissional, equilíbrio entre responsabilidades e resultados.
            3. Compatibilidade ATS: Palavras-chave da função, verbos de ação, estrutura de parsing, alinhamento com práticas de recrutamento digital.
            4. Impacto e Resultados: Métricas evidentes, KPIs, percentagens, resultados concretos vs tarefas descritivas.
            5. Marca Pessoal e Proposta de Valor: Identidade profissional clara, narrativa diferenciada, resumo estratégico e coerente.
            6. Riscos e Inconsistências: Lacunas temporais, mudanças frequentes, transições não explicadas, subposicionamento, generalismo excessivo.
            
            ESTRUTURA DE OUTPUT (JSON):
            {{
                "candidate_profile": {{
                    "detected_name": "Nome completo do candidato",
                    "detected_role": "Função atual/principal identificada",
                    "detected_sector": "Setor/Indústria identificado (ex: Tecnologia, Banca, Saúde, Retalho, etc.)",
                    "total_years_exp": "X anos",
                    "seniority": "Junior | Mid-Level | Sénior | Executivo"
                }},
                "executive_summary": {{
                    "global_score": <int 0-100>, // Pontuação global do currículo
                    "market_positioning": "Análise EXAUSTIVA do posicionamento do candidato no mercado de trabalho português e europeu. Deve incluir uma avaliação CRÍTICA e detalhada do nível de senioridade percebido, comparando-o RIGOROSAMENTE com benchmarks de mercado para a função alvo. Discutir o grau de competitividade do perfil, identificando os seus principais diferenciais e como estes se alinham ou desalinham com as expectativas de recrutadores de topo. Este texto deve ter no mínimo 400 palavras, estruturado em 5 a 8 parágrafos EXTREMAMENTE ricos em análise e contexto.",
                    "key_decision_factors": "Exploração APROFUNDADA dos principais fatores que influenciam as decisões de recrutamento para este perfil específico. Analisar CRITICAMENTE como a experiência, competências e aspirações do candidato se traduzem em valor para um potencial empregador, e que elementos podem ser DECISIVOS na fase de triagem. Este texto deve ter no mínimo 400 palavras, em 5 a 8 parágrafos."
                }},
                "diagnostic_impact": {{
                    "first_30_seconds_read": "Análise CRÍTICA e DETALHADA de como um recrutador sénior, com experiência em volume e qualidade, interpretaria este currículo nos primeiros 30 segundos. Avaliar a clareza da proposta de valor, o foco do perfil, a coerência narrativa e a capacidade de captar a atenção. Identificar os elementos visuais e textuais que contribuem para esta primeira impressão, e como otimizá-los. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                    "impact_strengths": "Identificação e justificação APROFUNDADA dos pontos onde o currículo gera um impacto forte e positivo. Explicar os elementos que comunicam valor de forma EFICAZ, como resultados quantificáveis, progressão de carreira acelerada ou competências raras e de alto valor. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                    "impact_dilutions": "Análise CRÍTICA dos pontos onde o impacto do currículo se dilui ou é menos eficaz. Identificar áreas de generalidade, falta de especificidade, ou informações que podem confundir ou desinteressar o recrutador. Propor causas para esta diluição e o seu efeito na competitividade em processos de alto nível. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                }},
                "content_structure_analysis": {{
                    "organization_hierarchy": "Avaliação EXAUSTIVA da organização geral do currículo, da hierarquia da informação e da fluidez de leitura. Analisar se a estrutura facilita a navegação rápida e a compreensão dos pontos chave, ou se apresenta barreiras (ex: blocos de texto densos, títulos ambíguos). Propor melhorias concretas. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                    "responsibilities_results_balance": "Análise CRÍTICA do equilíbrio entre a descrição de responsabilidades e a apresentação de resultados concretos. Avaliar se o currículo demonstra uma mentalidade orientada para o impacto e valor, ou se se foca excessivamente em tarefas. Sugerir como melhorar este balanço com exemplos. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                    "orientation": "Determinação da orientação PREDOMINANTE do currículo: execução, liderança ou pensamento estratégico. Justificar esta classificação com base na linguagem utilizada, nos exemplos de experiência e nos resultados apresentados. Explicar as implicações CRÍTICAS desta orientação para as funções alvo e a progressão de carreira. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                }},
                "ats_digital_recruitment": {{
                    "compatibility": "Avaliação DETALHADA da compatibilidade do currículo com os sistemas ATS (Applicant Tracking Systems) mais comuns no mercado português e internacional. Analisar a formatação, o uso de palavras-chave relevantes para a função e setor, e a estrutura que facilita o parsing automático. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                    "filtering_risks": "Identificação de riscos CONCRETOS de filtragem automática por ATS, como a ausência de termos chave, formatação inadequada ou uso de jargão não reconhecido. Explicar em detalhe como estes riscos podem impedir o currículo de chegar ao recrutador humano e como mitigá-los. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                    "alignment": "Análise CRÍTICA do alinhamento de palavras-chave, títulos de secção e estrutura geral do currículo com as práticas atuais de recrutamento digital e ATS. Avaliar a eficácia na otimização para motores de busca de talentos e a relevância para o mercado atual. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                }},
                "skills_differentiation": {{
                    "technical_behavioral_analysis": "Análise APROFUNDADA das competências técnicas e comportamentais demonstradas no currículo, com interpretação contextual e comparação com as exigências da função alvo. Avaliar a relevância destas competências e o nível de proficiência percebido. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                    "differentiation_factors": "Identificação CLARA e justificação ROBUSTA dos fatores que diferenciam este perfil no mercado de trabalho. Explicar como a experiência, competências ou conquistas únicas criam uma proposta de valor distinta e competitiva. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                    "common_undifferentiated": "Análise CRÍTICA das competências ou experiências que, embora importantes, são percecionadas como comuns ou indiferenciadas no mercado. Sugerir como estas podem ser reformuladas ou complementadas para aumentar o seu valor percebido e evitar a diluição do impacto. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                }},
                "strategic_risks": {{
                    "identified_risks": "Identificação e análise APROFUNDADA dos riscos estratégicos inerentes ao currículo. Discutir o potencial de subposicionamento, excesso de generalismo, a ausência de métricas de impacto, ambiguidade na senioridade ou desalinhamento com as funções alvo. Explicar as consequências CRÍTICAS de cada risco na progressão de carreira e como mitigá-los. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                }},
                "priority_recommendations": {{
                    "immediate_adjustments": "Recomendações CONCRETAS e hierarquizadas para ajustes imediatos no currículo. Cada recomendação deve ser ESPECÍFICA, acionável e justificada pela análise prévia, com exemplos práticos. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                    "refinement_areas": "Identificação de áreas que requerem refinamento a médio prazo para otimizar ainda mais o currículo. Estas recomendações devem ser ESTRATÉGICAS e visar um impacto sustentado na carreira, com um plano de ação claro. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                    "deep_repositioning": "Análise de elementos que podem exigir um reposicionamento MAIS PROFUNDO do perfil ou da narrativa do currículo. Discutir cenários onde uma mudança ESTRATÉGICA de abordagem é necessária para atingir objetivos de carreira ambiciosos. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                }},
                "executive_conclusion": {{
                    "potential_after_improvements": "Resumo DETALHADO do potencial transformado do currículo após a implementação das melhorias propostas. Articular como o documento se tornará uma ferramenta PODEROSA para a progressão de carreira e a conquista de novas oportunidades. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                    "expected_competitiveness": "Avaliação do nível de competitividade ESPERADO do currículo em processos seletivos de alto nível e exigência, após a aplicação das recomendações. Justificar esta expectativa com base na otimização do perfil e na sua adequação ao mercado. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                }},
                "radar_data": {{
                    "estrutura": <0-20>, "conteudo": <0-20>, "ats": <0-20>, "impacto": <0-20>, "branding": <0-20>, "riscos": <0-20>
                }},
                "pdf_extended_content": {{
                    "sector_analysis": {{
                        "identified_sector": "Nome do setor identificado",
                        "sector_trends": "Análise APROFUNDADA das tendências atuais do setor em Portugal e na Europa, com uma perspetiva CRÍTICA e implicações para o perfil do candidato. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "competitive_landscape": "Descrição DETALHADA do panorama competitivo para a função alvo neste setor, com implicações PRÁTICAS para a estratégia de candidatura do candidato. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                    }},
                    "critical_certifications": [
                        {{
                            "name": "Nome da certificação (ex: PMP, PROSCI, ITIL, etc.)",
                            "issuer": "Entidade certificadora",
                            "relevance": "Análise DETALHADA da relevância desta certificação para a função e setor, com justificação CLARA do valor que agrega ao perfil do candidato e como a diferencia no mercado. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                            "priority": "Alta | Média | Baixa",
                            "estimated_investment": "Custo aproximado e duração",
                            "where_to_get": "Onde obter em Portugal ou online"
                        }}
                    ],
                    "phrase_improvements": [
                        {{
                            "original": "Frase original extraída do currículo (copiar exatamente)",
                            "problem": "Análise APROFUNDADA do que está incorreto ou subotimizado nesta frase, com uma explicação DETALHADA do seu impacto negativo na perceção do recrutador e na compatibilidade ATS. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                            "improved": "Versão OTIMIZADA da frase, reescrita para maximizar o impacto, integrar métricas QUANTIFICÁVEIS e utilizar linguagem EXECUTIVA. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                            "explanation": "Explicação EXAUSTIVA de porque a versão melhorada é superior, detalhando o seu valor ESTRATÉGICO, como melhora a legibilidade, o impacto e a otimização para ATS. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                        }}
                    ],
                    "cv_design_tips": {{
                        "layout": "Dicas ESPECÍFICAS e DETALHADAS de layout e estrutura visual, com exemplos CONCRETOS e justificação para um currículo executivo de alto impacto. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "typography": "Recomendações APROFUNDADAS sobre a escolha de fontes e tamanhos, com justificação para maximizar a legibilidade, o profissionalismo e a estética do currículo. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "spacing": "Dicas DETALHADAS sobre espaçamento e margens, visando otimizar a densidade textual sem comprometer a legibilidade e a estética profissional. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "sections_order": "Análise da ordem RECOMENDADA das secções para este perfil, com justificação ESTRATÉGICA para maximizar o impacto e a fluidez da leitura. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "length": "Recomendação DETALHADA sobre o número ideal de páginas para o currículo, com base na senioridade e complexidade do perfil, e como gerir a densidade de informação. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "visual_elements": "Análise CRÍTICA sobre o que incluir e evitar em termos de elementos visuais (gráficos, cores, fotos), com uma avaliação do seu impacto na perceção do recrutador e na compatibilidade ATS. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                    }},
                    "writing_guide": {{
                        "power_verbs": "Lista EXAUSTIVA de verbos de ação poderosos e estratégicos, com exemplos de aplicação em currículos executivos. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "keywords_to_add": "Lista de 10 keywords ATS CRÍTICAS para esta função, com justificação DETALHADA da sua importância. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "phrases_to_avoid": "Lista de 5 frases/expressões a EVITAR, com explicação APROFUNDADA do porquê são vagas ou prejudiciais. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "quantification_tips": "Guia PRÁTICO e DETALHADO para quantificar resultados e impacto, com exemplos de como transformar responsabilidades em conquistas MENSURÁVEIS. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                    }},
                    "professional_development": {{
                        "short_term": "Definição de objetivos de desenvolvimento de carreira a CURTO PRAZO (0-12 meses), com ações CONCRETAS e MENSURÁVEIS. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "medium_term": "Definição de objetivos de desenvolvimento de carreira a MÉDIO PRAZO (1-3 anos), alinhados com a visão ESTRATÉGICA do candidato. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "long_term": "Articulação da visão de carreira a LONGO PRAZO (3-5 anos+), com a identificação de marcos e aspirações. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                    }},
                    "networking_strategy": {{
                        "linkedin_optimization": "Dicas ESPECÍFICAS e APROFUNDADAS para otimizar o perfil LinkedIn, visando a MÁXIMA visibilidade executiva e um networking ESTRATÉGICO eficaz. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "key_communities": "Identificação e análise das comunidades profissionais MAIS RELEVANTES em Portugal e internacionalmente, com foco em liderança e desenvolvimento de carreira. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "events_to_attend": "Recomendação de tipos de eventos e conferências ESTRATÉGICOS para networking e desenvolvimento de liderança, com justificação APROFUNDADA do seu valor. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "thought_leadership": "Estratégias DETALHADAS sobre como construir uma presença de liderança de pensamento na área, com exemplos de plataformas e formatos para partilha de conhecimento e influência. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                    }},
                    "salary_positioning": {{
                        "market_range": "Análise do intervalo salarial TÍPICO para esta função e nível de senioridade em Portugal, com base em dados de mercado e tendências atuais. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "negotiation_leverage": "Identificação dos pontos fortes do currículo que servem como ALAVANCA na negociação salarial, com justificação DETALHADA do valor agregado que o candidato traz. Mínimo de 400 palavras, em 5 a 8 parágrafos.",
                        "gaps_to_address": "Análise das lacunas no currículo que podem impedir a justificação de um salário mais elevado, com um plano de ação CONCRETO para colmatar estas falhas. Mínimo de 400 palavras, em 5 a 8 parágrafos."
                    }}
                }}
            }}
            
            INSTRUÇÕES ADICIONAIS:
            1. Para "phrase_improvements", extrai 3-5 frases REAIS do currículo e mostra como melhorá-las, com foco em métricas e impacto.
            2. Para "critical_certifications", recomenda 3-5 certificações ESPECÍFICAS para o setor identificado, justificando a sua relevância executiva.
            3. Todas as recomendações devem ser práticas, acionáveis e com justificação estratégica.
            4. Usa exemplos concretos e quantificáveis sempre que possível.
            5. O conteúdo deve ser útil e de alto valor para um profissional que busca posições de liderança.
            6. Foca em certificações reconhecidas internacionalmente mas com aplicabilidade e disponibilidade em Portugal.
            7. As descrições em "signal", "missing" e "upgrade" para cada dimensão devem ser parágrafos analíticos, não listas simples.
            8. A pontuação global em "executive_summary" deve ser justificada pela análise detalhada das dimensões e riscos.
            9. A densidade textual deve ser triplicada nas secções-chave, com parágrafos interpretativos em vez de etiquetas genéricas.
            10. Reduz espaços vazios, mesmo que isso aumente o número de páginas, priorizando a profundidade analítica.
            11. Inclui exemplos concretos do que ajustar no currículo, ainda que em abstrato, para cada recomendação.
            
            POSICIONAMENTO ESTRATÉGICO CHAVE: (Se aplicável, o modelo deve inferir um posicionamento estratégico para o candidato e refletir na análise, utilizando modos verbais e conjugações que reforcem esta visão e que estejam em conformidade com o português de Portugal.)
            
            IMPORTANTE: Toda a resposta DEVE ser em Português de Portugal (PT-PT).
            
            PRINCÍPIOS EDITORIAIS (OBRIGATÓRIOS):
            - Clareza acima de sofisticação. Estratégia acima de elogios. Informação acionável.
            - Linguagem humana e profissional (não promocional).
            - Palavras Proibidas (NUNCA USAR): "Consultoria", "Projeto", "Implementação", "Formação", "Metodologia proprietária", "Framework exclusivo".
            - Substituições: "Acompanhamento", "Decisão", "Posicionamento", "Clareza estratégica", "Conhecimento aplicável".
            
            CONTEXTO DE ENTRADA:
            Função Alvo: {role}
            """

            # Gerar o conteúdo
            response = self.model.generate_content([prompt, uploaded_file])
            
            # Limpar e extrair o JSON
            cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
            analysis_data = json.loads(cleaned_text)
            
            analysis_data["analysis_type"] = "gemini"
            return analysis_data

        except Exception as e:
            print(f"Análise AI falhou: {e}")
            # Fallback para análise heurística se a API falhar
            return self.heuristic_analysis(file_stream, filename)
        finally:
            # Limpar o ficheiro temporário
            if uploaded_file:
                genai.delete_file(uploaded_file.name)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def heuristic_analysis(self, file_stream, filename):
        """Fallback analysis based on keyword heuristics."""
        print("Executando fallback para análise heurística...")
        text = self.extract_text(file_stream, filename)
        if not text:
            return {"error": "Could not extract text for heuristic analysis.", "analysis_type": "error"}

        scores = {}
        for section, keywords in self.sections.items():
            found = any(re.search(r"\b" + kw + r"\b", text, re.IGNORECASE) for kw in keywords)
            scores[section] = 100 if found else 0
        
        metrics_score = 100 if self.metrics_pattern.search(text) else 0
        scores["metrics"] = metrics_score

        return {
            "scores": scores,
            "analysis_type": "heuristic"
        }
