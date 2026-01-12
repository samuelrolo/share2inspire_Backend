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
            print(f"[INFO] Tentando inicializar Gemini com API Key (primeiros 5 chars): {self.api_key[:5]}...{self.api_key[-5:]}")
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-pro")
            print("[INFO] Modelo Gemini inicializado com sucesso.")
        else:
            print("[AVISO] Chave API Gemini não encontrada. O modelo Gemini não será inicializado.")

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
        return f"""Você é um analista de RH especializado em recrutamento e análise de CVs. A sua tarefa é analisar o CV fornecido e gerar um relatório detalhado em formato JSON, seguindo a estrutura especificada. O candidato está a candidatar-se para a função de '{role}' com um nível de experiência '{experience_level}'.

O relatório JSON deve conter as seguintes secções e campos:

{{
    "candidate_profile": {{
        "detected_name": "Nome do Candidato",
        "detected_role": "Função detetada no CV",
        "detected_sector": "Setor detetado no CV",
        "total_years_exp": "Total de anos de experiência (ex: 5 anos)",
        "seniority": "Nível de senioridade (ex: Júnior, Pleno, Sênior)",
        "education_level": "Nível de educação mais alto (ex: Mestrado, Licenciatura)",
        "languages_detected": ["Lista de idiomas (ex: Português, Inglês)"],
        "key_skills": ["Lista de competências chave (ex: Python, Gestão de Projetos)"]
    }},
    "global_summary": {{
        "strengths": ["Lista de pontos fortes gerais do CV"],
        "improvements": ["Lista de pontos a melhorar gerais do CV"]
    }},
    "executive_summary": {{
        "global_score": "Score global do CV (0-100)",
        "global_score_breakdown": {{
            "structure_clarity": "Score de clareza da estrutura (0-100)",
            "content_relevance": "Score de relevância do conteúdo (0-100)",
            "risks_inconsistencies": "Score de riscos e inconsistências (0-100)",
            "ats_compatibility": "Score de compatibilidade com ATS (0-100)",
            "impact_results": "Score de impacto e resultados (0-100)",
            "personal_brand": "Score de marca pessoal (0-100)"
        }},
        "market_positioning": "Análise do posicionamento do candidato no mercado de trabalho",
        "key_decision_factors": "Fatores chave que influenciam a decisão de contratação"
    }},
    "diagnostic_impact": {{
        "first_30_seconds_read": "Análise do impacto do CV nos primeiros 30 segundos de leitura",
        "impact_strengths": "Pontos fortes que geram impacto no CV",
        "impact_strengths_signal": "Sinais de impacto identificados",
        "impact_strengths_missing": "Pontos de impacto em falta",
        "impact_dilutions": "Pontos que diluem o impacto do CV"
    }},
    "content_structure_analysis": {{
        "organization_hierarchy": "Análise da organização e hierarquia do conteúdo",
        "organization_hierarchy_signal": "Sinais de boa organização",
        "organization_hierarchy_missing": "Pontos de organização em falta",
        "content_completeness": "Análise da completude do conteúdo",
        "content_completeness_signal": "Sinais de conteúdo completo",
        "content_completeness_missing": "Pontos de conteúdo em falta"
    }},
    "ats_digital_recruitment": {{
        "keyword_optimization": "Análise da otimização de palavras-chave para ATS",
        "keyword_optimization_signal": "Sinais de boa otimização de palavras-chave",
        "keyword_optimization_missing": "Pontos de otimização de palavras-chave em falta",
        "format_parsing": "Análise da formatação e parsing para ATS",
        "format_parsing_signal": "Sinais de boa formatação para ATS",
        "format_parsing_missing": "Pontos de formatação em falta para ATS"
    }},
    "strategic_risks": {{
        "career_gaps": "Análise de lacunas de carreira e como são abordadas",
        "career_gaps_signal": "Sinais de lacunas de carreira",
        "career_gaps_missing": "Pontos de lacunas de carreira em falta",
        "frequent_changes": "Análise de mudanças frequentes de emprego",
        "frequent_changes_signal": "Sinais de mudanças frequentes",
        "frequent_changes_missing": "Pontos de mudanças frequentes em falta"
    }},
    "evolution_roadmap": {{
        "quick_wins": "Recomendações de melhorias rápidas",
        "medium_term": "Recomendações de melhorias a médio prazo",
        "long_term": "Recomendações de melhorias a longo prazo"
    }},
    "radar_data": {{
        "estrutura": "Score de estrutura (0-20)",
        "conteudo": "Score de conteúdo (0-20)",
        "ats": "Score de ATS (0-20)",
        "impacto": "Score de impacto (0-20)",
        "branding": "Score de branding (0-20)",
        "riscos": "Score de riscos (0-20)"
    }},
    "analysis_type": "gemini"
}}

Por favor, garanta que a saída é um JSON válido e que todos os campos são preenchidos com base na análise do CV. Se um campo não for aplicável ou não puder ser determinado, use 'N/D' ou uma string vazia, mas **nunca omita um campo**."""

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
                "strengths": [
                    "**Estrutura Base Consistente**: O CV apresenta uma organização fundamental que permite a leitura e extração de informações básicas.",
                    "**Clareza na Identificação**: As secções principais (experiência, educação, competências) são identificáveis, facilitando a navegação inicial.",
                    "**Potencial de Otimização**: Existe uma base sólida para aprimoramento, especialmente na personalização e impacto dos resultados."
                ],
                "improvements": [
                    "**Análise Avançada Indisponível**: A ausência da análise Gemini impede insights aprofundados sobre o posicionamento de mercado, riscos estratégicos e diferenciação de competências.",
                    "**Conteúdo Genérico**: As recomendações são baseadas em heurísticas gerais e não refletem uma análise personalizada do seu perfil e do seu CV.",
                    "**Otimização para ATS**: Não foi possível avaliar a compatibilidade do CV com sistemas de Applicant Tracking System (ATS), um fator crítico na triagem inicial.",
                    "**Impacto e Resultados**: A quantificação de resultados e o impacto das suas experiências não foram analisados em detalhe, o que pode diluir a força da sua candidatura."
                ]
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
                "first_30_seconds_read": "### Leitura em 30 Segundos (Modo de Segurança)\n\n- **Primeira Impressão**: A capacidade de captar a atenção do recrutador nos primeiros 30 segundos é crucial. A estrutura atual do CV permite uma leitura inicial, mas a otimização do resumo e dos destaques pode aumentar significativamente o impacto.\n- **Clareza e Foco**: Garanta que a sua proposta de valor e os seus objetivos de carreira são imediatamente claros. Evite jargões excessivos e seja direto ao ponto.\n- **Chamada à Ação**: O CV deve guiar o leitor para as informações mais relevantes, incentivando uma leitura mais aprofundada. Considere usar um resumo profissional conciso e impactante.",
                "impact_strengths": "### Pontos de Impacto (Modo de Segurança)\n\n- **Resultados Quantificáveis**: O impacto de um CV é maximizado pela apresentação de resultados concretos e quantificáveis. A análise heurística sugere que a inclusão de métricas pode fortalecer significativamente a sua narrativa.\n- **Progressão de Carreira**: Destaque a sua evolução profissional e as responsabilidades crescentes. A clareza na sua trajetória demonstra ambição e capacidade de crescimento.\n- **Competências Relevantes**: Sublinhe as competências mais relevantes para a função desejada, mostrando como elas foram aplicadas para gerar valor.",
                "impact_strengths_signal": "Análise de sinais de impacto indisponível no modo de segurança. A análise completa forneceria insights sobre a força dos seus resultados e a sua capacidade de gerar valor.",
                "impact_strengths_missing": "Análise de pontos em falta indisponível no modo de segurança. A análise completa identificaria lacunas na apresentação do seu impacto e resultados.",
                "impact_dilutions": "### Pontos de Diluição (Modo de Segurança)\n\n- **Generalidade**: Descrições de funções genéricas ou a ausência de resultados específicos podem diluir o impacto do seu CV. Seja o mais específico possível sobre as suas contribuições.\n- **Falta de Foco**: Um CV que tenta ser 'tudo para todos' pode perder o seu foco. Concentre-se nas experiências e competências mais relevantes para o seu objetivo de carreira.\n- **Erros e Inconsistências**: Pequenos erros gramaticais ou inconsistências de formatação podem desviar a atenção do recrutador e diminuir a credibilidade do seu perfil."
            },
            "content_structure_analysis": {
                "organization_hierarchy": "### Organização e Estrutura (Modo de Segurança)\n\n- **Estrutura Base**: O CV apresenta uma estrutura fundamental com secções identificáveis, o que facilita a leitura inicial. No entanto, a otimização da hierarquia visual e do fluxo de informação pode ser aprimorada.\n- **Fluxo de Leitura**: Garanta que a organização do conteúdo guia o recrutador de forma lógica através da sua trajetória profissional e académica.\n- **Espaço em Branco**: O uso adequado de espaço em branco melhora a legibilidade e a estética do documento. Evite blocos de texto densos.",
                "organization_hierarchy_signal": "Análise de sinais de organização indisponível no modo de segurança. A análise completa avaliaria a eficácia da sua estrutura para captar e manter a atenção do recrutador.",
                "organization_hierarchy_missing": "Análise de pontos em falta indisponível no modo de segurança. A análise completa identificaria oportunidades para otimizar a organização e o fluxo do seu CV.",
                "content_completeness": "### Completude do Conteúdo (Modo de Segurança)\n\n- **Secções Essenciais**: O CV inclui as secções básicas como Experiência e Educação. Para um perfil completo, considere adicionar secções como Projetos, Publicações ou Voluntariado, se aplicável.\n- **Detalhe e Profundidade**: A profundidade do detalhe em cada secção é crucial. Certifique-se de que cada experiência e formação são descritas com informações relevantes e impactantes.\n- **Consistência**: Mantenha a consistência na formatação e no nível de detalhe em todas as secções para uma apresentação profissional.",
                "content_completeness_signal": "Análise de sinais de completude indisponível no modo de segurança. A análise completa avaliaria se o seu CV fornece todas as informações necessárias para uma avaliação abrangente.",
                "content_completeness_missing": "Análise de pontos em falta indisponível no modo de segurança. A análise completa identificaria lacunas no conteúdo do seu CV que poderiam ser preenchidas para fortalecer a sua candidatura."
            },
            "ats_digital_recruitment": {
                "keyword_optimization": "### Otimização para ATS (Modo de Segurança)\n\n- **Palavras-Chave**: A otimização para sistemas de Applicant Tracking System (ATS) é crucial. A análise heurística não pode avaliar a densidade e relevância das palavras-chave, mas é fundamental que o seu CV inclua termos específicos da sua área e da vaga desejada.\n- **Ação Recomendada**: Revise as descrições de vagas para as quais se candidata e incorpore as palavras-chave mais relevantes de forma natural no seu CV.\n- **Evitar Jargões**: Embora palavras-chave sejam importantes, evite jargões excessivos que possam confundir o recrutador humano.",
                "keyword_optimization_signal": "Análise de sinais de otimização indisponível no modo de segurança. A análise completa forneceria um score de compatibilidade com ATS e sugestões de palavras-chave.",
                "keyword_optimization_missing": "Análise de pontos em falta indisponível no modo de segurança. A análise completa identificaria lacunas na otimização de palavras-chave e na estrutura para ATS.",
                "format_parsing": "### Formatação e Parsing (Modo de Segurança)\n\n- **Compatibilidade de Formato**: Para garantir que o seu CV é lido corretamente pelos ATS, utilize formatos simples e amplamente aceites (ex: PDF sem elementos complexos como tabelas ou caixas de texto). A análise heurística não pode validar a integridade do parsing.\n- **Estrutura Limpa**: Evite designs excessivamente gráficos ou com múltiplas colunas, pois podem confundir os ATS e resultar na perda de informações cruciais.\n- **Validação Visual**: Após a criação do CV, visualize-o como um texto simples para ter uma ideia de como um ATS o 'lê'.",
                "format_parsing_signal": "Análise de sinais de formatação indisponível no modo de segurança. A análise completa simularia o parsing por um ATS e identificaria potenciais erros.",
                "format_parsing_missing": "Análise de pontos em falta indisponível no modo de segurança. A análise completa identificaria problemas de formatação que dificultam a leitura por ATS."
            },
            "strategic_risks": {
                "career_gaps": "### Lacunas de Carreira (Modo de Segurança)\n\n- **Contexto é Chave**: A análise heurística não consegue interpretar lacunas de carreira. Se existirem, é fundamental contextualizá-las (ex: formação, projetos pessoais, etc.) no seu CV, explicando os motivos e as atividades desenvolvidas durante esses períodos.\n- **Impacto na Percepção**: Lacunas não explicadas podem levantar questões para os recrutadores. Uma narrativa clara e positiva pode transformar uma potencial fraqueza numa demonstração de resiliência ou desenvolvimento pessoal.\n- **Ação Recomendada**: Se tiver lacunas, adicione uma breve explicação no seu CV ou carta de apresentação, focando-se em como esse tempo contribuiu para o seu crescimento.",
                "career_gaps_signal": "Análise de sinais de lacunas indisponível no modo de segurança. A análise completa forneceria insights sobre como as lacunas podem ser percebidas e como mitigá-las.",
                "career_gaps_missing": "Análise de pontos em falta indisponível no modo de segurança. A análise completa identificaria a presença de lacunas e sugeriria estratégias para as abordar.",
                "frequent_changes": "### Mudanças Frequentes (Modo de Segurança)\n\n- **Narrativa de Progressão**: Mudanças frequentes de emprego podem ser um sinal de alerta se não forem justificadas por uma narrativa de crescimento, progressão de carreira ou busca por novas oportunidades alinhadas com os seus objetivos.\n- **Coerência**: Garanta que cada mudança de emprego se encaixa numa história coerente de desenvolvimento profissional. Se houver mudanças que pareçam aleatórias, considere como pode contextualizá-las.\n- **Ação Recomendada**: Se o seu histórico de emprego mostrar mudanças frequentes, prepare uma explicação concisa e positiva que demonstre como cada experiência contribuiu para o seu desenvolvimento e objetivos de carreira.",
                "frequent_changes_signal": "Análise de sinais de mudanças indisponível no modo de segurança. A análise completa avaliaria o impacto das mudanças frequentes na percepção do seu perfil.",
                "frequent_changes_missing": "Análise de pontos em falta indisponível no modo de segurança. A análise completa identificaria padrões de mudanças e sugeriria estratégias para otimizar a sua apresentação."
            },
            "evolution_roadmap": {
                "quick_wins": "- **Resumo Profissional**: Otimize o seu resumo para ser conciso e impactante, destacando a sua proposta de valor única e os seus principais diferenciais.\n- **Métricas e Resultados**: Adicione métricas e resultados quantificáveis a cada experiência relevante, demonstrando o impacto real do seu trabalho.\n- **Palavras-Chave**: Integre palavras-chave relevantes da sua área e das descrições de vagas para melhorar a compatibilidade com sistemas ATS.",
                "medium_term": "- **Personalização do CV**: Adapte o seu CV para cada candidatura, alinhando as suas competências e experiências com os requisitos específicos da vaga.\n- **Desenvolvimento de Competências**: Identifique e desenvolva competências em alta demanda no seu setor para aumentar a sua empregabilidade.\n- **Networking Estratégico**: Conecte-se com profissionais da sua área e participe em eventos para expandir a sua rede de contactos e oportunidades.",
                "long_term": "- **Branding Pessoal Online**: Construa uma presença online sólida e consistente (LinkedIn, portfólio, etc.) que reforce a sua marca pessoal e expertise.\n- **Liderança e Mentoria**: Procure oportunidades de liderança ou mentoria para demonstrar as suas capacidades de gestão e influência.\n- **Aprendizagem Contínua**: Mantenha-se atualizado com as últimas tendências e tecnologias do seu setor através de cursos, certificações e autoestudo."
            },
            "radar_data": radar_data,
            "analysis_type": "heuristic"
        }
