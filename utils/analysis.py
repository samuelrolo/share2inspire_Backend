"""
Módulo de Análise de CV - Share2Inspire
Versão 7.0 - Análise Heurística Completa
"""

import json
import os
import re
import io
from PyPDF2 import PdfReader

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("[AVISO] google.generativeai não disponível.")

from utils.secrets import get_secret


class CVAnalyzer:
    """Analisador de CVs com suporte a Gemini AI e fallback heurístico robusto."""
    
    def __init__(self):
        self.api_key = get_secret("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self.model = None
        
        if GENAI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                print("[INFO] Modelo Gemini inicializado com sucesso.")
            except Exception as e:
                print(f"[ERRO] Falha ao inicializar Gemini: {e}")
        else:
            print("[AVISO] Chave API Gemini não encontrada ou biblioteca indisponível.")

    def extract_text(self, file_stream, filename):
        """Extrai texto de PDF ou documento de texto."""
        text = ""
        try:
            file_stream.seek(0)
            if filename.lower().endswith(".pdf"):
                pdf_reader = PdfReader(file_stream)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            else:
                text = file_stream.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[ERRO] Falha na extração de texto: {e}")
        return text.strip()

    def analyze(self, file_stream, filename, role="", experience_level=""):
        """Analisa o CV usando Gemini ou fallback heurístico."""
        if self.model:
            try:
                text = self.extract_text(file_stream, filename)
                if not text:
                    return self._heuristic_analysis(file_stream, filename, role, experience_level)
                
                prompt = self._build_analysis_prompt(role, experience_level)
                full_prompt = f"{prompt}\n\n--- CV PARA ANÁLISE ---\n{text}"
                
                response = self.model.generate_content(full_prompt)
                cleaned_text = response.text.strip()
                
                # Remover marcadores de código
                if "```json" in cleaned_text:
                    cleaned_text = cleaned_text.split("```json")[1].split("```")[0]
                elif "```" in cleaned_text:
                    cleaned_text = cleaned_text.split("```")[1].split("```")[0]
                
                analysis_data = json.loads(cleaned_text)
                analysis_data["analysis_type"] = "gemini"
                return self._ensure_complete_structure(analysis_data)
                
            except Exception as e:
                print(f"[ERRO] Análise Gemini falhou: {e}")
                file_stream.seek(0)
                return self._heuristic_analysis(file_stream, filename, role, experience_level)
        else:
            return self._heuristic_analysis(file_stream, filename, role, experience_level)

    def _build_analysis_prompt(self, role, experience_level):
        """Constrói o prompt para análise com Gemini."""
        return f"""Analisa este CV de forma profissional e detalhada para a função de '{role}' com nível '{experience_level}'.

IMPORTANTE - REGRAS DE IDIOMA:
1. Escreve SEMPRE em Português de Portugal (PT-PT), NUNCA em Português do Brasil
2. NÃO uses gerúndios - usa "a fazer" em vez de "fazendo", "a liderar" em vez de "liderando"
3. Usa vocabulário PT-PT: "equipa" (não "time"), "gestão" (não "gerenciamento"), "colaborador" (não "funcionário")
4. Termos técnicos em inglês são aceitáveis (HR, ATS, skills, LinkedIn, etc.)
5. NUNCA uses "você" - usa "o candidato", "o profissional" ou construções impessoais

IMPORTANTE - FORMATO:
1. Todos os campos de texto devem ser STRINGS contínuas, NÃO arrays
2. Para listas, usa texto com "- " no início de cada item, separados por \n
3. NÃO uses colchetes [ ] nos campos de texto
4. NÃO uses asteriscos ** para bold
        
Retorna APENAS um JSON válido (sem markdown) com esta estrutura exata:
{{
    "candidate_profile": {{
        "detected_name": "Nome completo",
        "total_years_exp": "X anos",
        "detected_role": "Função atual",
        "seniority": "Júnior/Pleno/Sénior/Diretor",
        "detected_sector": "Setor de atividade",
        "education_level": "Nível académico",
        "key_skills": ["skill1", "skill2", "skill3"]
    }},
    "global_summary": {{
        "strengths": ["ponto forte 1", "ponto forte 2", "ponto forte 3", "ponto forte 4"],
        "improvements": ["melhoria 1", "melhoria 2", "melhoria 3", "melhoria 4"]
    }},
    "executive_summary": {{
        "global_score": "75",
        "market_positioning": "Análise detalhada do posicionamento em texto corrido, sem colchetes...",
        "key_decision_factors": "Fatores de decisão detalhados em texto corrido..."
    }},
    "diagnostic_impact": {{
        "first_30_seconds_read": "O que um recrutador vê nos primeiros 30 segundos em texto corrido...",
        "impact_strengths": "Primeiro ponto forte relevante. Segundo ponto forte com detalhe. Terceiro ponto que demonstra valor.",
        "impact_dilutions": "Primeiro ponto de diluição identificado. Segundo aspeto a melhorar."
    }},
    "content_structure_analysis": {{
        "organization_hierarchy": "Análise da organização e hierarquia do CV em texto corrido...",
        "responsibilities_results_balance": "Análise do equilíbrio entre responsabilidades e resultados...",
        "orientation": "Orientação geral do CV..."
    }},
    "ats_digital_recruitment": {{
        "compatibility": "Análise de compatibilidade ATS em texto corrido...",
        "filtering_risks": "Riscos de filtragem automática descritos em texto corrido...",
        "alignment": "Alinhamento com práticas de recrutamento..."
    }},
    "skills_differentiation": {{
        "technical_behavioral_analysis": "Análise técnica vs comportamental em texto corrido...",
        "differentiation_factors": "Fatores de diferenciação descritos em texto corrido...",
        "common_undifferentiated": "Competências comuns descritas em texto corrido..."
    }},
    "strategic_risks": {{
        "identified_risks": "Primeiro risco estratégico identificado. Segundo risco com impacto potencial. Terceiro risco a considerar."
    }},
    "languages_analysis": {{
        "languages_assessment": "Avaliação dos idiomas em texto corrido..."
    }},
    "education_analysis": {{
        "education_assessment": "Avaliação da formação em texto corrido..."
    }},
    "phrase_improvements": [
        {{
            "category": "Descrição de Função",
            "before": "Frase original do CV",
            "after": "Frase melhorada em Português de Portugal",
            "justification": "Razão da melhoria"
        }}
    ],
    "pdf_extended_content": {{
        "sector_analysis": {{
            "identified_sector": "Setor",
            "sector_trends": "Tendências do setor em texto corrido...",
            "competitive_landscape": "Panorama competitivo em texto corrido..."
        }},
        "critical_certifications": [
            {{
                "name": "Nome da Certificação",
                "issuer": "Entidade",
                "priority": "Alta",
                "estimated_investment": "€500-1000",
                "relevance": "Relevância para a carreira em texto corrido..."
            }}
        ]
    }},
    "priority_recommendations": {{
        "immediate_adjustments": "Primeiro ajuste imediato recomendado. Segundo ajuste prioritário. Terceiro ajuste a implementar.",
        "refinement_areas": "Primeira área de refinamento. Segunda área a desenvolver.",
        "deep_repositioning": "Primeira sugestão de reposicionamento. Segunda estratégia de longo prazo."
    }},
    "executive_conclusion": {{
        "potential_after_improvements": "Potencial após implementar melhorias em texto corrido...",
        "expected_competitiveness": "Competitividade esperada no mercado em texto corrido..."
    }},
    "radar_data": {{
        "estrutura": 14,
        "conteudo": 12,
        "riscos": 13,
        "ats": 16,
        "impacto": 11,
        "branding": 12
    }}
}}"""

    def _extract_name(self, text):
        """Extrai o nome do candidato do texto do CV."""
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 3 and len(line) < 50:
                # Verificar se parece um nome (palavras capitalizadas)
                words = line.split()
                if 2 <= len(words) <= 5:
                    if all(w[0].isupper() for w in words if w):
                        # Evitar linhas com emails, telefones, etc
                        if '@' not in line and not any(c.isdigit() for c in line[:10]):
                            return line
        return "Candidato"

    def _extract_email(self, text):
        """Extrai email do texto."""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None

    def _extract_phone(self, text):
        """Extrai telefone do texto."""
        phone_patterns = [
            r'\+351\s*\d{3}\s*\d{3}\s*\d{3}',
            r'\d{3}\s*\d{3}\s*\d{3}',
            r'\(\d{2,3}\)\s*\d{3,4}[-\s]?\d{4}'
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def _extract_years_experience(self, text):
        """Estima anos de experiência baseado em datas no CV."""
        year_pattern = r'20[0-2]\d|19[89]\d'
        years = re.findall(year_pattern, text)
        if years:
            years = [int(y) for y in years]
            min_year = min(years)
            current_year = 2026
            exp = current_year - min_year
            if exp > 0 and exp < 50:
                return f"{exp} anos"
        return "3-5 anos"

    def _extract_skills(self, text):
        """Extrai competências do texto."""
        text_lower = text.lower()
        
        skill_keywords = {
            'técnicas': ['python', 'java', 'javascript', 'sql', 'excel', 'power bi', 'tableau', 
                        'sap', 'salesforce', 'aws', 'azure', 'docker', 'kubernetes', 'react', 
                        'node.js', 'machine learning', 'data analysis', 'project management',
                        'scrum', 'agile', 'jira', 'git', 'linux', 'windows server'],
            'soft': ['liderança', 'comunicação', 'trabalho em equipa', 'gestão de tempo',
                    'resolução de problemas', 'pensamento crítico', 'adaptabilidade',
                    'negociação', 'apresentação', 'mentoria', 'coaching']
        }
        
        found_skills = []
        for category, skills in skill_keywords.items():
            for skill in skills:
                if skill.lower() in text_lower:
                    found_skills.append(skill.title())
        
        if not found_skills:
            found_skills = ["Gestão de Projetos", "Análise de Dados", "Comunicação", "MS Office"]
        
        return found_skills[:8]

    def _extract_languages(self, text):
        """Extrai idiomas do texto."""
        text_lower = text.lower()
        languages = []
        
        lang_keywords = {
            'Português': ['português', 'portuguese', 'pt-pt', 'pt-br'],
            'Inglês': ['inglês', 'english', 'ingles'],
            'Espanhol': ['espanhol', 'spanish', 'español'],
            'Francês': ['francês', 'french', 'français'],
            'Alemão': ['alemão', 'german', 'deutsch'],
            'Italiano': ['italiano', 'italian']
        }
        
        for lang, keywords in lang_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    languages.append(lang)
                    break
        
        if not languages:
            languages = ["Português"]
        
        return languages

    def _detect_sector(self, text):
        """Detecta o setor de atividade."""
        text_lower = text.lower()
        
        sectors = {
            'Tecnologia': ['software', 'developer', 'programador', 'it ', 'tecnologia', 'digital', 'tech'],
            'Finanças': ['banco', 'financeiro', 'contabilidade', 'auditoria', 'finance', 'banking'],
            'Saúde': ['hospital', 'clínica', 'médico', 'enfermeiro', 'farmácia', 'saúde'],
            'Consultoria': ['consultoria', 'consulting', 'consultant', 'advisory'],
            'Marketing': ['marketing', 'publicidade', 'comunicação', 'digital marketing'],
            'Recursos Humanos': ['recursos humanos', 'rh', 'hr', 'human resources', 'recrutamento'],
            'Engenharia': ['engenheiro', 'engineering', 'engenharia'],
            'Vendas': ['vendas', 'sales', 'comercial', 'account manager'],
            'Operações': ['operações', 'operations', 'logística', 'supply chain'],
            'Educação': ['professor', 'formador', 'educação', 'ensino', 'teacher']
        }
        
        for sector, keywords in sectors.items():
            for kw in keywords:
                if kw in text_lower:
                    return sector
        
        return "Serviços Profissionais"

    def _detect_seniority(self, text, years_exp):
        """Detecta nível de senioridade."""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ['diretor', 'director', 'ceo', 'cfo', 'cto', 'vp ', 'vice president']):
            return "Diretor/Executivo"
        elif any(kw in text_lower for kw in ['manager', 'gestor', 'gerente', 'head of', 'lead']):
            return "Gestor/Manager"
        elif any(kw in text_lower for kw in ['senior', 'sénior', 'sr.', 'especialista']):
            return "Sénior"
        elif any(kw in text_lower for kw in ['junior', 'júnior', 'jr.', 'trainee', 'estagiário']):
            return "Júnior"
        else:
            # Baseado em anos de experiência
            try:
                years = int(re.search(r'\d+', years_exp).group())
                if years >= 10:
                    return "Sénior"
                elif years >= 5:
                    return "Pleno"
                else:
                    return "Júnior"
            except:
                return "Pleno"

    def _detect_role(self, text):
        """Detecta a função/cargo do candidato."""
        text_lower = text.lower()
        
        roles = [
            ('Engenheiro de Software', ['software engineer', 'engenheiro de software', 'developer']),
            ('Gestor de Projetos', ['project manager', 'gestor de projetos', 'pm']),
            ('Analista de Dados', ['data analyst', 'analista de dados', 'business analyst']),
            ('Consultor', ['consultant', 'consultor']),
            ('Gestor de Marketing', ['marketing manager', 'gestor de marketing']),
            ('Recursos Humanos', ['hr manager', 'recursos humanos', 'talent acquisition']),
            ('Gestor Comercial', ['sales manager', 'gestor comercial', 'account executive']),
            ('Engenheiro', ['engineer', 'engenheiro']),
            ('Analista', ['analyst', 'analista']),
            ('Gestor', ['manager', 'gestor', 'gerente'])
        ]
        
        for role, keywords in roles:
            for kw in keywords:
                if kw in text_lower:
                    return role
        
        return "Profissional"

    def _detect_education(self, text):
        """Detecta nível de educação."""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ['doutoramento', 'phd', 'ph.d', 'doutor']):
            return "Doutoramento"
        elif any(kw in text_lower for kw in ['mestrado', 'master', 'mba', 'msc']):
            return "Mestrado"
        elif any(kw in text_lower for kw in ['licenciatura', 'bachelor', 'bacharelato', 'graduação']):
            return "Licenciatura"
        elif any(kw in text_lower for kw in ['técnico', 'tecnólogo', 'cet']):
            return "Curso Técnico"
        else:
            return "Ensino Superior"

    def _calculate_scores(self, text, skills, languages):
        """Calcula scores baseados na análise do CV."""
        scores = {
            'estrutura': 12,
            'conteudo': 12,
            'riscos': 14,
            'ats': 13,
            'impacto': 11,
            'branding': 10
        }
        
        # Ajustar estrutura baseado em formatação
        if len(text) > 2000:
            scores['estrutura'] += 2
        if '\n\n' in text:  # Tem parágrafos separados
            scores['estrutura'] += 1
        
        # Ajustar conteúdo baseado em skills
        scores['conteudo'] += min(len(skills) // 2, 4)
        
        # Ajustar ATS baseado em keywords
        ats_keywords = ['experiência', 'responsabilidades', 'competências', 'formação', 'educação']
        for kw in ats_keywords:
            if kw in text.lower():
                scores['ats'] += 1
        
        # Ajustar impacto baseado em números/métricas
        if re.search(r'\d+%', text):
            scores['impacto'] += 3
        if re.search(r'€\d+|EUR\s*\d+', text):
            scores['impacto'] += 2
        
        # Ajustar branding baseado em idiomas e certificações
        scores['branding'] += min(len(languages), 3)
        if 'certificação' in text.lower() or 'certificate' in text.lower():
            scores['branding'] += 2
        
        # Normalizar para máximo de 20
        for key in scores:
            scores[key] = min(scores[key], 20)
        
        return scores

    def _heuristic_analysis(self, file_stream, filename, role="", experience_level=""):
        """Análise heurística completa quando Gemini não está disponível."""
        print("[INFO] Executando análise heurística completa.")
        
        file_stream.seek(0)
        text = self.extract_text(file_stream, filename)
        
        if not text:
            text = "CV sem texto extraível"
        
        # Extrair informações do CV
        name = self._extract_name(text)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        years_exp = self._extract_years_experience(text)
        skills = self._extract_skills(text)
        languages = self._extract_languages(text)
        sector = self._detect_sector(text)
        seniority = self._detect_seniority(text, years_exp)
        detected_role = self._detect_role(text) if not role else role
        education = self._detect_education(text)
        
        # Calcular scores
        scores = self._calculate_scores(text, skills, languages)
        global_score = sum(scores.values()) * 5 // 6  # Média dos 6 scores, escala 0-100
        
        # Construir análise completa
        analysis = {
            "analysis_type": "heuristic",
            
            "candidate_profile": {
                "detected_name": name,
                "total_years_exp": years_exp,
                "detected_role": detected_role,
                "seniority": seniority,
                "detected_sector": sector,
                "education_level": education,
                "key_skills": skills[:6],
                "email": email,
                "phone": phone,
                "languages": languages
            },
            
            "global_summary": {
                "strengths": [
                    f"Experiência de {years_exp} na área de {sector}",
                    f"Perfil de {seniority} com competências em {', '.join(skills[:3])}",
                    f"Formação académica ao nível de {education}",
                    f"Domínio de {len(languages)} idioma(s): {', '.join(languages)}"
                ],
                "improvements": [
                    "Quantificar resultados e conquistas com métricas específicas",
                    "Reforçar keywords relevantes para sistemas ATS",
                    "Desenvolver uma proposta de valor mais diferenciadora",
                    "Incluir mais exemplos concretos de impacto profissional"
                ]
            },
            
            "executive_summary": {
                "global_score": str(global_score),
                "global_score_breakdown": {
                    "structure_clarity": str(scores['estrutura'] * 5),
                    "content_relevance": str(scores['conteudo'] * 5),
                    "risks_inconsistencies": str(scores['riscos'] * 5),
                    "ats_compatibility": str(scores['ats'] * 5),
                    "impact_results": str(scores['impacto'] * 5),
                    "personal_brand": str(scores['branding'] * 5)
                },
                "market_positioning": f"""O perfil de {name} apresenta-se como um profissional de nível {seniority} no setor de {sector}, com aproximadamente {years_exp} de experiência acumulada. A trajetória demonstra uma progressão consistente na área de {detected_role}, com competências técnicas relevantes em {', '.join(skills[:4])}.

**Posicionamento Atual:**
- Perfil alinhado com funções de {detected_role} em organizações de média/grande dimensão
- Competências técnicas adequadas às exigências do mercado atual
- Formação académica ({education}) compatível com o nível de responsabilidade pretendido

**Oportunidades de Diferenciação:**
- Reforçar a narrativa de impacto e resultados quantificáveis
- Desenvolver uma marca pessoal mais distintiva no setor
- Explorar certificações complementares para aumentar competitividade""",

                "key_decision_factors": f"""**Fatores Positivos para Decisão de Contratação:**
- Experiência comprovada de {years_exp} em funções relevantes
- Competências técnicas alinhadas: {', '.join(skills[:4])}
- Perfil linguístico adequado: {', '.join(languages)}
- Formação académica sólida ao nível de {education}

**Fatores que Requerem Atenção:**
- Necessidade de maior quantificação de resultados e impacto
- Oportunidade de reforçar diferenciação face à concorrência
- Potencial para melhorar otimização para sistemas ATS

**Recomendação Geral:**
O candidato apresenta um perfil competitivo para funções de {detected_role}, com margem para otimização que pode elevar significativamente a taxa de conversão em processos de recrutamento."""
            },
            
            "diagnostic_impact": {
                "first_30_seconds_read": f"""**Impressão Inicial (Primeiros 30 Segundos):**
Num primeiro contacto, o CV de {name} transmite a imagem de um profissional de {sector} com experiência em {detected_role}. A estrutura permite identificar rapidamente:

- **Identificação:** Nome e contactos visíveis
- **Experiência:** Aproximadamente {years_exp} de percurso profissional
- **Competências-chave:** {', '.join(skills[:3])}
- **Formação:** {education}

**O que Capta Atenção:**
A trajetória profissional demonstra consistência na área, com progressão adequada ao nível de {seniority}.

**O que Pode Passar Despercebido:**
Sem métricas de impacto claramente destacadas, alguns resultados importantes podem não ser imediatamente percetíveis pelo recrutador.""",

                "impact_strengths": f"""**Pontos Fortes de Impacto Identificados:**

- **Consistência de Carreira:** Trajetória coerente no setor de {sector} demonstra compromisso e especialização
- **Competências Técnicas:** Domínio de {', '.join(skills[:4])} alinhado com requisitos de mercado
- **Perfil Linguístico:** Capacidade de comunicação em {', '.join(languages)} amplia oportunidades
- **Formação Académica:** {education} proporciona base sólida para a função
- **Nível de Senioridade:** Perfil de {seniority} adequado para responsabilidades de {detected_role}""",

                "impact_dilutions": f"""**Pontos de Diluição de Impacto Identificados:**

- **Métricas Quantitativas:** Ausência ou insuficiência de números que demonstrem resultados concretos (%, €, volume)
- **Diferenciação:** Descrições de funções podem parecer genéricas sem exemplos específicos de conquistas
- **Proposta de Valor:** A marca pessoal e proposta de valor única não estão claramente articuladas
- **Keywords ATS:** Potencial para otimizar termos-chave que aumentem visibilidade em sistemas de recrutamento
- **Storytelling:** Oportunidade de criar uma narrativa mais envolvente sobre a progressão de carreira"""
            },
            
            "content_structure_analysis": {
                "organization_hierarchy": f"""**Análise da Organização e Hierarquia do CV:**

O documento apresenta uma estrutura que segue as convenções standard de CVs profissionais, com secções identificáveis para dados pessoais, experiência profissional e formação.

**Pontos Positivos:**
- Informação de contacto acessível
- Secções principais presentes e identificáveis
- Fluxo cronológico compreensível

**Oportunidades de Melhoria:**
- Considerar um sumário executivo no início para captar atenção imediata
- Reorganizar competências por relevância para a função-alvo
- Destacar visualmente as conquistas mais significativas""",

                "responsibilities_results_balance": f"""**Equilíbrio entre Responsabilidades e Resultados:**

A análise do conteúdo revela uma tendência para descrição de responsabilidades em detrimento de resultados quantificáveis.

**Situação Atual:**
- Descrições focadas em "o que fazia" vs "o que alcançou"
- Verbos de ação presentes mas sem métricas de suporte
- Competências listadas sem evidências de aplicação

**Recomendação:**
Transformar descrições de responsabilidades em declarações de impacto usando a fórmula:
**Ação + Contexto + Resultado Quantificado**

Exemplo: "Liderei equipa de 5 pessoas" → "Liderei equipa de 5 pessoas, aumentando produtividade em 25% e reduzindo tempo de entrega em 2 semanas\"""",

                "orientation": f"""**Orientação Geral do CV:**

O CV demonstra uma orientação predominantemente descritiva, com foco na apresentação de experiência e competências de forma tradicional.

**Características Identificadas:**
- Abordagem cronológica da experiência
- Listagem de competências técnicas e comportamentais
- Apresentação de formação académica e complementar

**Sugestões de Reorientação:**
- Adotar uma abordagem mais orientada a resultados
- Personalizar conteúdo para funções-alvo específicas
- Incorporar elementos de marca pessoal distintivos"""
            },
            
            "ats_digital_recruitment": {
                "compatibility": f"""**Compatibilidade com Sistemas ATS (Applicant Tracking Systems):**

Os sistemas ATS são utilizados por mais de 75% das grandes empresas para filtrar candidaturas. A análise do CV revela:

**Pontos de Compatibilidade:**
- Formato de texto extraível (não apenas imagem)
- Secções standard reconhecíveis pelos sistemas
- Presença de algumas keywords relevantes para {sector}

**Score ATS Estimado:** {scores['ats'] * 5}/100

**Fatores Positivos:**
- Estrutura linear facilita parsing automático
- Competências técnicas identificáveis: {', '.join(skills[:4])}""",

                "filtering_risks": f"""**Riscos de Filtragem Automática:**

**Riscos Identificados:**
- **Keywords Insuficientes:** Pode não incluir todos os termos específicos que recrutadores pesquisam para {detected_role}
- **Formatação:** Elementos visuais complexos podem não ser corretamente interpretados
- **Densidade de Termos:** Proporção de keywords relevantes pode ser inferior ao ideal

**Recomendações para Mitigar Riscos:**
- Incluir sinónimos de competências-chave (ex: "Gestão de Projetos" e "Project Management")
- Mencionar ferramentas e tecnologias específicas do setor
- Usar terminologia standard da indústria de {sector}""",

                "alignment": f"""**Alinhamento com Práticas de Recrutamento Digital:**

**Práticas Atuais de Recrutamento:**
O recrutamento moderno combina análise ATS com revisão humana. O CV deve satisfazer ambos.

**Alinhamento Atual:**
- ✓ Formato compatível com parsing digital
- ✓ Informação de contacto acessível
- ⚠ Keywords podem ser reforçadas
- ⚠ Perfil LinkedIn não destacado

**Sugestões de Otimização:**
- Adicionar link para perfil LinkedIn otimizado
- Incluir portfolio ou exemplos de trabalho online (se aplicável)
- Garantir consistência entre CV e presença digital"""
            },
            
            "skills_differentiation": {
                "technical_behavioral_analysis": f"""**Análise de Competências Técnicas vs Comportamentais:**

**Competências Técnicas Identificadas:**
{chr(10).join(['- ' + s for s in skills[:5]])}

**Competências Comportamentais Inferidas:**
- Comunicação profissional
- Trabalho em equipa
- Gestão de tempo e prioridades
- Adaptabilidade

**Equilíbrio Atual:**
O CV apresenta maior ênfase em competências técnicas, o que é adequado para funções de {detected_role}. Recomenda-se complementar com evidências de soft skills através de exemplos concretos.""",

                "differentiation_factors": f"""**Fatores de Diferenciação:**

**Elementos Distintivos Identificados:**
- Combinação específica de experiência em {sector} com competências em {', '.join(skills[:3])}
- Perfil linguístico: {', '.join(languages)}
- Nível de formação: {education}

**Oportunidades de Diferenciação Adicional:**
- Destacar projetos únicos ou inovadores
- Mencionar resultados excecionais com métricas
- Incluir reconhecimentos ou prémios profissionais
- Evidenciar contribuições para além das responsabilidades base""",

                "common_undifferentiated": f"""**Competências Comuns (Não Diferenciadoras):**

As seguintes competências, embora importantes, são comuns no mercado e não constituem diferenciação:

- Microsoft Office / ferramentas de produtividade standard
- "Trabalho em equipa" sem exemplos específicos
- "Boa comunicação" sem evidências concretas
- Competências genéricas sem contexto de aplicação

**Recomendação:**
Transformar competências comuns em diferenciadoras através de:
- Contexto específico de utilização
- Nível de proficiência demonstrável
- Resultados alcançados com essas competências"""
            },
            
            "strategic_risks": {
                "identified_risks": f"""**Riscos Estratégicos Identificados:**

**1. Risco de Subvalorização**
- Sem métricas de impacto, o verdadeiro valor do candidato pode não ser percebido
- Recrutadores podem subestimar contribuições por falta de evidências quantitativas

**2. Risco de Filtragem ATS**
- Keywords insuficientes podem resultar em eliminação automática
- Formatação pode não ser 100% compatível com todos os sistemas

**3. Risco de Indiferenciação**
- Perfil pode parecer similar a outros candidatos do mesmo nível
- Falta de proposta de valor única claramente articulada

**4. Risco de Desatualização**
- Competências tecnológicas podem necessitar de atualização
- Certificações recentes podem reforçar relevância atual

**5. Risco de Inconsistência Digital**
- Potencial desalinhamento entre CV e perfil LinkedIn
- Presença digital pode não refletir o mesmo nível de profissionalismo"""
            },
            
            "languages_analysis": {
                "languages_assessment": f"""**Avaliação de Competências Linguísticas:**

**Idiomas Identificados:** {', '.join(languages)}

**Análise por Idioma:**
{chr(10).join([f'- **{lang}:** Competência indicada no CV' for lang in languages])}

**Relevância para o Mercado:**
- Português: Essencial para mercado nacional
- Inglês: Crítico para empresas internacionais e multinacionais
- Outros idiomas: Diferenciador para mercados específicos

**Recomendações:**
- Indicar nível de proficiência (A1-C2 ou Básico/Intermédio/Avançado/Nativo)
- Mencionar certificações linguísticas se existentes (Cambridge, TOEFL, DELE, etc.)
- Destacar experiência profissional em contexto internacional"""
            },
            
            "education_analysis": {
                "education_assessment": f"""**Avaliação da Formação Académica e Profissional:**

**Nível Académico Identificado:** {education}

**Análise:**
A formação académica ao nível de {education} é adequada para funções de {detected_role} no setor de {sector}.

**Pontos Positivos:**
- Formação alinhada com a área de atuação
- Base teórica para suportar competências práticas

**Oportunidades de Desenvolvimento:**
- Formação contínua em áreas emergentes do setor
- Certificações profissionais reconhecidas
- Especializações que complementem a formação base

**Certificações Recomendadas para {sector}:**
- Certificações técnicas específicas da área
- Formação em metodologias ágeis (se aplicável)
- Certificações de gestão de projetos (PMP, Prince2)"""
            },
            
            "phrase_improvements": [
                {
                    "category": "Descrição de Responsabilidades",
                    "before": "Responsável pela gestão de projetos na empresa",
                    "after": "Liderei a gestão de 12 projetos simultâneos com orçamento total de €500K, alcançando 95% de entregas dentro do prazo",
                    "justification": "A versão melhorada quantifica o âmbito (12 projetos, €500K) e demonstra resultados concretos (95% no prazo), transformando uma descrição genérica numa declaração de impacto."
                },
                {
                    "category": "Competências Técnicas",
                    "before": "Conhecimentos de Excel e análise de dados",
                    "after": "Domínio avançado de Excel (VLOOKUP, Pivot Tables, Macros VBA) aplicado na criação de dashboards que reduziram tempo de reporting em 40%",
                    "justification": "Especifica o nível de competência, detalha funcionalidades dominadas e demonstra impacto mensurável da aplicação da competência."
                },
                {
                    "category": "Experiência de Liderança",
                    "before": "Gestão de equipa",
                    "after": "Gestão e desenvolvimento de equipa de 8 colaboradores, com implementação de programa de mentoria que aumentou retenção em 30%",
                    "justification": "Quantifica a dimensão da equipa, especifica ações concretas (programa de mentoria) e apresenta resultado mensurável (30% retenção)."
                },
                {
                    "category": "Conquistas Profissionais",
                    "before": "Contribuí para o aumento das vendas",
                    "after": "Desenvolvi e implementei estratégia comercial que gerou aumento de 25% nas vendas (€200K adicionais) no primeiro trimestre",
                    "justification": "Substitui linguagem passiva por ativa, quantifica o impacto em percentagem e valor absoluto, e especifica o período temporal."
                }
            ],
            
            "pdf_extended_content": {
                "sector_analysis": {
                    "identified_sector": sector,
                    "sector_trends": f"""**Tendências Atuais no Setor de {sector}:**

O setor de {sector} atravessa um período de transformação significativa, impulsionado por:

**Tendências Tecnológicas:**
- Digitalização acelerada de processos e operações
- Adoção de ferramentas de automação e IA
- Crescente importância de competências digitais

**Tendências de Mercado:**
- Maior exigência de especialização técnica
- Valorização de perfis híbridos (técnico + gestão)
- Foco em resultados mensuráveis e ROI

**Tendências de Talento:**
- Competição intensificada por profissionais qualificados
- Valorização de soft skills e adaptabilidade
- Importância crescente de formação contínua

**Implicações para o Candidato:**
Para maximizar competitividade, recomenda-se foco em atualização de competências digitais e demonstração clara de resultados quantificáveis.""",

                    "competitive_landscape": f"""**Panorama Competitivo para {detected_role} em {sector}:**

**Perfil Típico da Concorrência:**
- Profissionais com {years_exp} de experiência similar
- Formação académica equivalente ({education})
- Competências técnicas comparáveis

**Fatores de Diferenciação no Mercado:**
- Certificações especializadas e reconhecidas
- Experiência internacional ou em empresas de referência
- Portfolio de resultados quantificados
- Presença digital profissional otimizada

**Posicionamento Recomendado:**
O candidato deve posicionar-se como um profissional de {seniority} com track record comprovado em {sector}, destacando:
- Resultados específicos e mensuráveis
- Competências distintivas: {', '.join(skills[:3])}
- Capacidade de adaptação e aprendizagem contínua"""
                },
                
                "critical_certifications": [
                    {
                        "name": "Project Management Professional (PMP)",
                        "issuer": "Project Management Institute (PMI)",
                        "priority": "Alta",
                        "estimated_investment": "€500-800 + exame",
                        "relevance": f"Certificação globalmente reconhecida que valida competências de gestão de projetos, altamente valorizada no setor de {sector} para funções de coordenação e liderança."
                    },
                    {
                        "name": "Scrum Master Certified (SMC)",
                        "issuer": "Scrum Alliance / Scrum.org",
                        "priority": "Alta",
                        "estimated_investment": "€300-500",
                        "relevance": "Essencial para ambientes ágeis, demonstra capacidade de facilitar equipas e processos de desenvolvimento iterativo."
                    },
                    {
                        "name": "Google Analytics Certification",
                        "issuer": "Google",
                        "priority": "Média",
                        "estimated_investment": "Gratuito",
                        "relevance": "Certificação gratuita que demonstra competências em análise de dados digitais, relevante para funções com componente analítica."
                    },
                    {
                        "name": f"Certificação Específica de {sector}",
                        "issuer": "Entidade do Setor",
                        "priority": "Alta",
                        "estimated_investment": "€400-1000",
                        "relevance": f"Certificação técnica específica do setor de {sector} que valida conhecimentos especializados e aumenta credibilidade profissional."
                    }
                ]
            },
            
            "priority_recommendations": {
                "immediate_adjustments": f"""**Ajustes Imediatos (Implementar em 1-2 dias):**

- **Quantificar Resultados:** Adicionar métricas a pelo menos 5 descrições de experiência (%, €, números absolutos)
- **Otimizar Keywords:** Incluir termos específicos de {sector} e {detected_role} para melhorar compatibilidade ATS
- **Sumário Executivo:** Adicionar um parágrafo inicial de 3-4 linhas que sintetize proposta de valor
- **Verificar Formatação:** Garantir consistência de datas, títulos e espaçamentos
- **Atualizar Contactos:** Confirmar que email e telefone estão corretos e profissionais""",

                "refinement_areas": f"""**Áreas de Refinamento (Implementar em 1-2 semanas):**

- **Reescrever Descrições:** Transformar responsabilidades em declarações de impacto usando fórmula Ação + Contexto + Resultado
- **Competências Estratégicas:** Reorganizar skills por relevância para função-alvo, destacando as mais diferenciadoras
- **Formação Complementar:** Identificar e iniciar certificação prioritária para o setor
- **Presença Digital:** Alinhar perfil LinkedIn com CV atualizado
- **Referências:** Preparar lista de referências profissionais contactáveis""",

                "deep_repositioning": f"""**Reposicionamento Profundo (Implementar em 1-3 meses):**

- **Marca Pessoal:** Desenvolver narrativa profissional distintiva e consistente
- **Portfolio de Resultados:** Documentar casos de sucesso com métricas detalhadas
- **Networking Estratégico:** Expandir rede de contactos no setor de {sector}
- **Formação Avançada:** Considerar especialização ou certificação de nível superior
- **Visibilidade:** Criar conteúdo profissional (artigos, posts) para demonstrar expertise
- **Mentoria:** Procurar mentor no setor para orientação de carreira"""
            },
            
            "executive_conclusion": {
                "potential_after_improvements": f"""**Potencial Após Implementação das Melhorias:**

Com a implementação das recomendações identificadas, o perfil de {name} tem potencial para:

**Curto Prazo (1-4 semanas):**
- Aumentar taxa de resposta a candidaturas em 40-60%
- Melhorar posicionamento em filtros ATS
- Captar atenção de recrutadores nos primeiros 30 segundos

**Médio Prazo (1-3 meses):**
- Aceder a oportunidades de maior responsabilidade e remuneração
- Posicionar-se como candidato de referência para funções de {detected_role}
- Desenvolver marca pessoal reconhecível no setor

**Longo Prazo (3-12 meses):**
- Consolidar posição de {seniority} no mercado de {sector}
- Expandir rede de contactos estratégicos
- Criar pipeline de oportunidades de carreira

**Score Potencial Após Melhorias:** 85-90/100""",

                "expected_competitiveness": f"""**Competitividade Esperada no Mercado:**

**Situação Atual:**
O perfil apresenta competitividade moderada, posicionando-se no percentil 50-60 dos candidatos para funções similares de {detected_role}.

**Após Implementação de Ajustes Imediatos:**
Competitividade elevada para percentil 70-75, com maior taxa de conversão em processos de recrutamento.

**Após Refinamento Completo:**
Competitividade alta, percentil 80-85, com capacidade de aceder a oportunidades premium e negociar condições mais favoráveis.

**Fatores Críticos de Sucesso:**
- Consistência na implementação das melhorias
- Atualização contínua de competências
- Manutenção de presença digital profissional
- Networking ativo no setor de {sector}

**Recomendação Final:**
Investir nas melhorias identificadas representa um retorno significativo em termos de oportunidades de carreira e potencial de progressão profissional."""
            },
            
            "radar_data": scores
        }
        
        return analysis

    def _ensure_complete_structure(self, data):
        """Garante que todos os campos necessários existem na estrutura de dados."""
        # Template de estrutura completa
        template = self._heuristic_analysis(io.BytesIO(b""), "dummy.pdf", "", "")
        
        def merge_dicts(base, override):
            """Merge recursivo de dicionários."""
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
            return result
        
        # Merge template com dados recebidos (dados recebidos têm prioridade)
        return merge_dicts(template, data)


    def parse_for_cv_builder(self, file_stream, filename):
        """
        Extrai dados estruturados do CV para preencher o CV Builder.
        Retorna informação pessoal, experiências, educação, skills, idiomas e certificações.
        """
        if not self.model:
            return {"error": "Gemini model not available"}, 500
        
        try:
            text = self.extract_text(file_stream, filename)
            if not text:
                return {"error": "Could not extract text from file"}, 400
            
            prompt = """Extrai TODOS os dados estruturados deste CV em formato JSON.

IMPORTANTE - REGRAS:
1. Extrai TODAS as experiências profissionais (não apenas a última)
2. Extrai TODA a formação académica (não apenas a última)
3. Extrai TODAS as competências/skills mencionadas
4. Extrai TODOS os idiomas com níveis
5. Extrai TODAS as certificações
6. Para datas, usa formato "YYYY-MM" ou "YYYY" (se só tiver ano)
7. Se ainda trabalha numa empresa, usa "current": true
8. Se ainda estuda, usa "current": true

Retorna APENAS um JSON válido (sem markdown) com esta estrutura:

{
    "personalInfo": {
        "fullName": "Nome Completo",
        "email": "email@example.com",
        "phone": "+351 912 345 678",
        "location": "Lisboa, Portugal",
        "linkedin": "https://linkedin.com/in/username",
        "summary": "Resumo profissional se existir no CV"
    },
    "experience": [
        {
            "company": "Nome da Empresa",
            "position": "Cargo/Função",
            "startDate": "2020-01",
            "endDate": "2023-06",
            "current": false,
            "location": "Lisboa, Portugal",
            "description": "Descrição das responsabilidades e conquistas"
        }
    ],
    "education": [
        {
            "institution": "Nome da Instituição",
            "degree": "Licenciatura/Mestrado/etc",
            "field": "Área de Estudo",
            "startDate": "2015-09",
            "endDate": "2018-07",
            "current": false,
            "location": "Porto, Portugal"
        }
    ],
    "skills": [
        {
            "name": "Nome da Competência",
            "category": "Técnica/Comportamental/Idioma",
            "level": "Básico/Intermédio/Avançado/Especialista"
        }
    ],
    "languages": [
        {
            "language": "Português",
            "proficiency": "Nativo",
            "native": true
        },
        {
            "language": "Inglês",
            "proficiency": "Fluente/Avançado/Intermédio/Básico",
            "native": false
        }
    ],
    "certifications": [
        {
            "name": "Nome da Certificação",
            "issuer": "Entidade Emissora",
            "date": "2022-05",
            "url": "URL se disponível"
        }
    ]
}"""
            
            full_prompt = f"{prompt}\n\n--- CV PARA EXTRAÇÃO ---\n{text}"
            
            response = self.model.generate_content(full_prompt)
            cleaned_text = response.text.strip()
            
            # Remover marcadores de código
            if "```json" in cleaned_text:
                cleaned_text = cleaned_text.split("```json")[1].split("```")[0]
            elif "```" in cleaned_text:
                cleaned_text = cleaned_text.split("```")[1].split("```")[0]
            
            cv_data = json.loads(cleaned_text)
            return cv_data, 200
            
        except json.JSONDecodeError as e:
            print(f"[ERRO] JSON inválido retornado pelo Gemini: {e}")
            return {"error": "Failed to parse CV data", "details": str(e)}, 500
        except Exception as e:
            print(f"[ERRO] Parsing CV falhou: {e}")
            return {"error": "Failed to parse CV", "details": str(e)}, 500
