# -*- coding: utf-8 -*-
"""
Analisador de CV Premium com API Gemini
Share2Inspire - Versão 6.0
Análises Aprofundadas e Robustas com Foco em Valor para o Cliente
"""

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
                print(f"[ERRO] Falha ao configurar API Gemini: {e}")
        else:
            print("[AVISO] Chave API Gemini não encontrada.")

        # Padrões de secções para análise heurística
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
        return f"""
Atua como Especialista Sénior em Recrutamento Executivo, Consultor de Carreira de Topo e Especialista em Sistemas ATS.
Analisa este currículo para um profissional que visa a função de '{role}' com nível de experiência '{experience_level}'.

═══════════════════════════════════════════════════════════════════════════════
REGRAS FUNDAMENTAIS DE QUALIDADE (OBRIGATÓRIAS)
═══════════════════════════════════════════════════════════════════════════════

1. DENSIDADE TEXTUAL OBRIGATÓRIA:
   - Cada campo de análise textual DEVE conter entre 300 e 500 palavras
   - PROIBIDO: Respostas curtas, listas simples, frases isoladas, etiquetas genéricas
   - OBRIGATÓRIO: Parágrafos densos, analíticos, com linguagem executiva e profundidade de consultoria sénior
   - Cada parágrafo deve ter no mínimo 5-7 frases completas e contextualizadas

2. CONTEÚDO COM VALOR REAL:
   - Desenvolver cada ponto com exemplos concretos e implicações práticas
   - Incluir comparação explícita com benchmarks de mercado e senioridade
   - Fornecer justificação estratégica robusta para cada observação
   - Evitar generalidades e clichés - ser específico e acionável

3. LINGUAGEM E ESTILO:
   - Português de Portugal (PT-PT) formal e profissional
   - Clareza acima de sofisticação - informação acionável
   - Estratégia acima de elogios - análise crítica construtiva
   - Rigor na gramática, modos verbais e conjugações

4. PALAVRAS PROIBIDAS (NUNCA USAR):
   "Consultoria", "Projeto", "Implementação", "Formação", "Metodologia proprietária", "Framework exclusivo"
   
   SUBSTITUIÇÕES RECOMENDADAS:
   "Acompanhamento", "Decisão", "Posicionamento", "Clareza estratégica", "Conhecimento aplicável", "Iniciativa", "Desenvolvimento", "Capacitação"

═══════════════════════════════════════════════════════════════════════════════
DIMENSÕES DE PONTUAÇÃO (0-20 cada, converter para 0-100 no output final)
═══════════════════════════════════════════════════════════════════════════════

1. ESTRUTURA E CLAREZA (0-20):
   - Ordem lógica e fluidez de leitura (objetivo: compreensão em menos de 20 segundos)
   - Clareza de títulos e hierarquia visual
   - Equilíbrio entre densidade e espaço em branco
   - Penalizar: textos densos sem estrutura, excesso de espaço vazio, formatação inconsistente

2. CONTEÚDO E RELEVÂNCIA (0-20):
   - Adequação à senioridade declarada e função alvo
   - Especificidade e profundidade das descrições
   - Progressão profissional clara e coerente
   - Equilíbrio entre responsabilidades e resultados mensuráveis

3. COMPATIBILIDADE ATS (0-20):
   - Presença de palavras-chave relevantes para a função e setor
   - Uso de verbos de ação reconhecidos
   - Estrutura que facilita parsing automático
   - Alinhamento com práticas de recrutamento digital

4. IMPACTO E RESULTADOS (0-20):
   - Métricas quantificáveis (KPIs, percentagens, valores)
   - Resultados concretos vs descrições de tarefas
   - Evidência de contribuição para objetivos organizacionais
   - Demonstração de progressão e crescimento

5. MARCA PESSOAL E PROPOSTA DE VALOR (0-20):
   - Identidade profissional clara e diferenciada
   - Narrativa coerente ao longo do documento
   - Resumo estratégico que comunica valor único
   - Posicionamento distintivo no mercado

6. RISCOS E INCONSISTÊNCIAS (0-20):
   - Lacunas temporais não explicadas
   - Mudanças frequentes sem contexto
   - Transições de carreira ambíguas
   - Subposicionamento ou generalismo excessivo

═══════════════════════════════════════════════════════════════════════════════
ESTRUTURA DE OUTPUT (JSON)
═══════════════════════════════════════════════════════════════════════════════

{{
    "candidate_profile": {{
        "detected_name": "Nome completo do candidato extraído do CV",
        "detected_role": "Função atual ou mais recente identificada",
        "detected_sector": "Setor/Indústria principal (ex: Tecnologia, Banca, Saúde, Retalho, Energia, Consultoria)",
        "total_years_exp": "X anos (calcular com base nas datas do CV)",
        "seniority": "Junior | Mid-Level | Sénior | Executivo | C-Level",
        "education_level": "Grau académico mais elevado identificado",
        "languages_detected": ["Lista de idiomas identificados no CV"],
        "key_skills": ["Top 5-8 competências técnicas ou comportamentais mais relevantes"]
    }},
    
    "global_summary": {{
        "strengths": [
            "Ponto forte 1: frase concisa e específica sobre um aspeto positivo do CV (máx 15 palavras)",
            "Ponto forte 2: frase concisa e específica sobre um aspeto positivo do CV (máx 15 palavras)",
            "Ponto forte 3: frase concisa e específica sobre um aspeto positivo do CV (máx 15 palavras)",
            "Ponto forte 4: frase concisa e específica sobre um aspeto positivo do CV (máx 15 palavras)"
        ],
        "improvements": [
            "Oportunidade 1: frase concisa e específica sobre uma área de melhoria (máx 15 palavras)",
            "Oportunidade 2: frase concisa e específica sobre uma área de melhoria (máx 15 palavras)",
            "Oportunidade 3: frase concisa e específica sobre uma área de melhoria (máx 15 palavras)",
            "Oportunidade 4: frase concisa e específica sobre uma área de melhoria (máx 15 palavras)"
        ]
    }},
    
    "executive_summary": {{
        "global_score": <int 0-100>,
        "market_positioning": "ANÁLISE EXAUSTIVA (300-500 palavras): Avaliação crítica e detalhada do posicionamento do candidato no mercado de trabalho português e europeu. Deve incluir: nível de senioridade percebido vs declarado, comparação rigorosa com benchmarks de mercado para a função alvo, grau de competitividade do perfil, principais diferenciais e como se alinham com expectativas de recrutadores de topo. Estruturar em 4-6 parágrafos ricos em análise contextual.",
        "key_decision_factors": "ANÁLISE APROFUNDADA (300-500 palavras): Exploração dos principais fatores que influenciam decisões de recrutamento para este perfil específico. Analisar como experiência, competências e aspirações se traduzem em valor para potenciais empregadores, elementos decisivos na fase de triagem, e pontos que podem gerar hesitação ou interesse imediato."
    }},
    
    "diagnostic_impact": {{
        "first_30_seconds_read": "ANÁLISE CRÍTICA (300-500 palavras): Como um recrutador sénior interpretaria este CV nos primeiros 30 segundos. Avaliar clareza da proposta de valor, foco do perfil, coerência narrativa, capacidade de captar atenção. Identificar elementos visuais e textuais que contribuem para a primeira impressão.",
        "impact_strengths": "IDENTIFICAÇÃO DETALHADA (300-500 palavras): Pontos onde o CV gera impacto forte e positivo. Explicar elementos que comunicam valor de forma eficaz: resultados quantificáveis, progressão acelerada, competências raras ou de alto valor.",
        "impact_strengths_signal": "Resumo em 2-3 frases dos sinais positivos mais fortes",
        "impact_strengths_missing": "O que falta para maximizar este impacto",
        "impact_dilutions": "ANÁLISE CRÍTICA (300-500 palavras): Pontos onde o impacto se dilui. Identificar áreas de generalidade, falta de especificidade, informações que podem confundir ou desinteressar. Propor causas e efeito na competitividade."
    }},
    
    "content_structure_analysis": {{
        "organization_hierarchy": "AVALIAÇÃO EXAUSTIVA (300-500 palavras): Organização geral, hierarquia da informação, fluidez de leitura. Analisar se estrutura facilita navegação rápida e compreensão dos pontos-chave. Identificar barreiras como blocos densos ou títulos ambíguos.",
        "organization_hierarchy_signal": "Resumo dos pontos fortes estruturais",
        "organization_hierarchy_missing": "Melhorias estruturais prioritárias",
        "responsibilities_results_balance": "ANÁLISE CRÍTICA (300-500 palavras): Equilíbrio entre descrição de responsabilidades e apresentação de resultados. Avaliar se demonstra mentalidade orientada para impacto ou foco excessivo em tarefas.",
        "responsibilities_results_balance_signal": "Resumo do equilíbrio atual",
        "responsibilities_results_balance_missing": "Como melhorar este balanço",
        "orientation": "DETERMINAÇÃO (300-500 palavras): Orientação predominante do CV - execução, liderança ou pensamento estratégico. Justificar com base na linguagem, exemplos e resultados. Explicar implicações para funções alvo."
    }},
    
    "ats_digital_recruitment": {{
        "compatibility": "AVALIAÇÃO DETALHADA (300-500 palavras): Compatibilidade com sistemas ATS mais comuns. Analisar formatação, palavras-chave relevantes, estrutura que facilita parsing automático.",
        "compatibility_signal": "Pontos fortes de compatibilidade ATS",
        "compatibility_missing": "Lacunas críticas para ATS",
        "filtering_risks": "IDENTIFICAÇÃO (300-500 palavras): Riscos concretos de filtragem automática. Ausência de termos-chave, formatação inadequada, jargão não reconhecido. Como mitigar.",
        "alignment": "ANÁLISE (300-500 palavras): Alinhamento com práticas atuais de recrutamento digital. Eficácia na otimização para motores de busca de talentos."
    }},
    
    "skills_differentiation": {{
        "technical_behavioral_analysis": "ANÁLISE APROFUNDADA (300-500 palavras): Competências técnicas e comportamentais demonstradas. Interpretação contextual e comparação com exigências da função alvo. Relevância e nível de proficiência percebido.",
        "differentiation_factors": "IDENTIFICAÇÃO (300-500 palavras): Fatores de diferenciação únicos. Experiências, competências ou conquistas que distinguem este candidato. Como comunicar mais eficazmente.",
        "differentiation_factors_signal": "Principais diferenciais identificados",
        "differentiation_factors_missing": "Oportunidades de diferenciação não exploradas",
        "common_undifferentiated": "ANÁLISE (300-500 palavras): Competências ou experiências percecionadas como comuns. Como reformular para aumentar valor percebido."
    }},
    
    "strategic_risks": {{
        "identified_risks": "IDENTIFICAÇÃO APROFUNDADA (300-500 palavras): Riscos estratégicos inerentes ao CV. Potencial de subposicionamento, generalismo, ausência de métricas, ambiguidade na senioridade, desalinhamento com funções alvo. Consequências e mitigação.",
        "identified_risks_signal": "Resumo dos riscos mais críticos",
        "identified_risks_missing": "Ações prioritárias de mitigação"
    }},
    
    "languages_analysis": {{
        "detected_languages": [
            {{
                "language": "Nome do idioma",
                "level": "Nativo | Fluente | Avançado | Intermédio | Básico",
                "relevance": "Relevância para a função alvo e mercado",
                "recommendation": "Recomendação específica se aplicável"
            }}
        ],
        "languages_assessment": "AVALIAÇÃO (200-300 palavras): Análise do perfil linguístico face às exigências do mercado e função alvo. Lacunas e oportunidades."
    }},
    
    "education_analysis": {{
        "formal_education": [
            {{
                "degree": "Grau académico",
                "institution": "Instituição",
                "field": "Área de estudo",
                "relevance": "Relevância para a função alvo"
            }}
        ],
        "education_assessment": "AVALIAÇÃO (200-300 palavras): Análise da formação académica face às exigências da função e senioridade. Pontos fortes e lacunas."
    }},
    
    "priority_recommendations": {{
        "immediate_adjustments": "RECOMENDAÇÕES CONCRETAS (300-500 palavras): Ajustes imediatos hierarquizados. Cada recomendação deve ser específica, acionável e justificada. Incluir exemplos práticos de como implementar.",
        "refinement_areas": "IDENTIFICAÇÃO (300-500 palavras): Áreas que requerem refinamento a médio prazo. Recomendações estratégicas para impacto sustentado na carreira.",
        "deep_repositioning": "ANÁLISE (300-500 palavras): Elementos que podem exigir reposicionamento mais profundo. Cenários onde mudança estratégica é necessária para objetivos ambiciosos."
    }},
    
    "executive_conclusion": {{
        "potential_after_improvements": "RESUMO DETALHADO (300-500 palavras): Potencial transformado do CV após implementação das melhorias. Como o documento se tornará ferramenta poderosa para progressão de carreira.",
        "expected_competitiveness": "AVALIAÇÃO (300-500 palavras): Nível de competitividade esperado em processos seletivos de alto nível após aplicação das recomendações."
    }},
    
    "radar_data": {{
        "estrutura": <0-20>,
        "conteudo": <0-20>,
        "ats": <0-20>,
        "impacto": <0-20>,
        "branding": <0-20>,
        "riscos": <0-20>
    }},
    
    "pdf_extended_content": {{
        "sector_analysis": {{
            "identified_sector": "Nome do setor identificado",
            "sector_trends": "ANÁLISE (300-500 palavras): Tendências atuais do setor em Portugal e Europa. Perspetiva crítica e implicações para o perfil do candidato.",
            "competitive_landscape": "DESCRIÇÃO (300-500 palavras): Panorama competitivo para a função alvo neste setor. Implicações práticas para estratégia de candidatura."
        }},
        "critical_certifications": [
            {{
                "name": "Nome da certificação (ex: PMP, PROSCI, ITIL, AWS, etc.)",
                "issuer": "Entidade certificadora",
                "relevance": "ANÁLISE (150-250 palavras): Relevância desta certificação para função e setor. Valor que agrega e como diferencia no mercado.",
                "priority": "Alta | Média | Baixa",
                "estimated_investment": "Custo aproximado e duração",
                "where_to_get": "Onde obter em Portugal ou online"
            }}
        ],
        "phrase_improvements": [
            {{
                "original": "COPIAR EXATAMENTE uma frase real do CV - não inventar. Deve ser uma frase que existe no documento.",
                "problem": "ANÁLISE (100-150 palavras): O que está subotimizado e impacto negativo na perceção.",
                "improved": "Versão otimizada da frase com métricas e linguagem executiva",
                "explanation": "EXPLICAÇÃO (100-150 palavras): Porque a versão melhorada é superior. Valor estratégico e otimização ATS."
            }}
        ],
        "cv_design_tips": {{
            "layout": "Dicas específicas de layout e estrutura visual para CV executivo.",
            "typography": "Recomendações sobre fontes e tamanhos para legibilidade profissional.",
            "spacing": "Dicas sobre espaçamento e margens para densidade textual otimizada.",
            "sections_order": "Ordem recomendada das secções com justificação estratégica.",
            "length": "Recomendação sobre número ideal de páginas para este perfil.",
            "visual_elements": "O que incluir e evitar em elementos visuais."
        }},
        "writing_guide": {{
            "power_verbs": "Lista de 15-20 verbos de ação poderosos com exemplos de aplicação.",
            "keywords_to_add": "Lista de 10-15 keywords ATS críticas para esta função com justificação.",
            "phrases_to_avoid": "Lista de 5-8 frases/expressões a evitar com explicação.",
            "quantification_tips": "Guia prático para quantificar resultados e transformar responsabilidades em conquistas."
        }},
        "professional_development": {{
            "short_term": "Objetivos de desenvolvimento a curto prazo (0-12 meses) com ações concretas.",
            "medium_term": "Objetivos a médio prazo (1-3 anos) alinhados com visão estratégica.",
            "long_term": "Visão de carreira a longo prazo (3-5 anos+) com marcos e aspirações."
        }},
        "networking_strategy": {{
            "linkedin_optimization": "Dicas específicas para otimizar perfil LinkedIn para visibilidade executiva.",
            "key_communities": "Comunidades profissionais relevantes em Portugal e internacionalmente.",
            "events_to_attend": "Tipos de eventos e conferências estratégicos para networking.",
            "thought_leadership": "Estratégias para construir presença de liderança de pensamento."
        }},
        "salary_positioning": {{
            "market_range": "Intervalo salarial típico para função e senioridade em Portugal.",
            "negotiation_leverage": "Pontos fortes do CV como alavanca na negociação salarial.",
            "gaps_to_address": "Lacunas que podem impedir justificação de salário mais elevado."
        }}
    }}
}}

═══════════════════════════════════════════════════════════════════════════════
INSTRUÇÕES ADICIONAIS
═══════════════════════════════════════════════════════════════════════════════

1. Para "phrase_improvements", extrair 3-5 frases REAIS do CV e mostrar como melhorá-las com foco em métricas e impacto.

2. Para "critical_certifications", recomendar 3-5 certificações ESPECÍFICAS para o setor identificado, justificando relevância executiva.

3. Para "languages_detected", identificar TODOS os idiomas mencionados no CV com níveis precisos.

4. Todas as recomendações devem ser práticas, acionáveis e com justificação estratégica.

5. Usar exemplos concretos e quantificáveis sempre que possível.

6. O conteúdo deve ser útil e de alto valor para um profissional que busca posições de liderança.

7. A pontuação global deve ser justificada pela análise detalhada das dimensões.

8. AUTO-AVALIAR rigorosamente o comprimento e densidade antes de finalizar. Se não cumprir mínimos, EXPANDIR.

9. Toda a resposta DEVE ser em Português de Portugal (PT-PT).

CONTEXTO DE ENTRADA:
Função Alvo: {role}
Nível de Experiência: {experience_level}
"""

    def analyze(self, file_stream, filename, role, experience_level):
        """Método principal de análise usando Gemini File API."""
        if not self.model:
            if self.api_key:
                try:
                    genai.configure(api_key=self.api_key)
                    self.model = genai.GenerativeModel("gemini-pro")
                except Exception as e:
                    return {"error": f"Falha ao inicializar modelo: {e}", "analysis_type": "error"}
            else:
                return {"error": "Chave API Gemini não configurada.", "analysis_type": "error"}

        uploaded_file = None
        tmp_path = None
        
        try:
            print(f"[INFO] Iniciando análise para {filename}...")
            
            # Criar ficheiro temporário
            suffix = ".pdf" if filename.lower().endswith(".pdf") else ".txt"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                file_stream.seek(0)
                tmp.write(file_stream.read())
                tmp_path = tmp.name

            # Upload para Gemini
            mime_type = "application/pdf" if suffix == ".pdf" else "text/plain"
            uploaded_file = genai.upload_file(tmp_path, mime_type=mime_type)
            
            # Construir e enviar prompt
            prompt = self._build_analysis_prompt(role, experience_level)
            response = self.model.generate_content(contents=[prompt, uploaded_file])
            
            # Processar resposta
            cleaned_text = response.text.strip()
            
            # Remover marcadores de código se presentes
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            # Parse JSON
            analysis_data = json.loads(cleaned_text)
            analysis_data["analysis_type"] = "gemini"
            
            # Validar e normalizar scores
            analysis_data = self._normalize_scores(analysis_data)
            
            return analysis_data

        except json.JSONDecodeError as e:
            print(f"[ERRO] Falha ao processar JSON: {e}")
            return self._heuristic_analysis(file_stream, filename)
            
        except Exception as e:
            print(f"[ERRO] Análise falhou: {e}")
            return self._heuristic_analysis(file_stream, filename)
            
        finally:
            # Limpeza
            if uploaded_file:
                try:
                    genai.delete_file(uploaded_file.name)
                except:
                    pass
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass

    def _normalize_scores(self, analysis_data):
        """Normaliza e valida os scores para garantir consistência."""
        radar_data = analysis_data.get('radar_data', {})
        
        # Garantir que todos os scores estão entre 0 e 20
        for key in ['estrutura', 'conteudo', 'ats', 'impacto', 'branding', 'riscos']:
            if key in radar_data:
                score = radar_data[key]
                if isinstance(score, (int, float)):
                    radar_data[key] = max(0, min(20, score))
                else:
                    radar_data[key] = 10  # Valor padrão se inválido
            else:
                radar_data[key] = 10  # Valor padrão se ausente
        
        analysis_data['radar_data'] = radar_data
        
        # Normalizar score global
        if 'executive_summary' in analysis_data:
            global_score = analysis_data['executive_summary'].get('global_score', 0)
            if isinstance(global_score, (int, float)):
                analysis_data['executive_summary']['global_score'] = max(0, min(100, global_score))
            else:
                # Calcular a partir dos radar_data
                avg = sum(radar_data.values()) / len(radar_data)
                analysis_data['executive_summary']['global_score'] = int(avg * 5)
        
        return analysis_data

    def _heuristic_analysis(self, file_stream, filename):
        """Análise heurística de fallback."""
        print("[INFO] Executando análise heurística de fallback...")
        
        file_stream.seek(0)
        text = self.extract_text(file_stream, filename)
        
        if not text:
            return {"error": "Não foi possível extrair texto do documento.", "analysis_type": "error"}

        # Analisar secções presentes
        section_scores = {}
        for section, keywords in self.section_patterns.items():
            found = any(re.search(r"\b" + kw + r"\b", text, re.IGNORECASE) for kw in keywords)
            section_scores[section] = 15 if found else 5
        
        # Verificar métricas
        has_metrics = bool(self.metrics_pattern.search(text))
        metrics_score = 15 if has_metrics else 5
        
        # Calcular scores dimensionais
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
                "detected_name": "Candidato",
                "detected_role": "Não identificado",
                "detected_sector": "Não identificado",
                "total_years_exp": "N/D",
                "seniority": "N/D",
                "education_level": "N/D",
                "languages_detected": [],
                "key_skills": []
            },
            "executive_summary": {
                "global_score": int(sum(radar_data.values()) / len(radar_data) * 5),
                "market_positioning": "Análise detalhada não disponível. Por favor, tente novamente ou contacte o suporte.",
                "key_decision_factors": "Análise detalhada não disponível."
            },
            "radar_data": radar_data,
            "analysis_type": "heuristic"
        }


# Função de conveniência
def analyze_cv(file_stream, filename, role="Não especificado", experience_level="Não especificado"):
    """Função de conveniência para analisar CV."""
    analyzer = CVAnalyzer()
    return analyzer.analyze(file_stream, filename, role, experience_level)
