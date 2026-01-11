# -*- coding: utf-8 -*-
"""
Script de teste para o novo gerador de relatórios PDF v2
"""

import sys
sys.path.insert(0, '/home/ubuntu/share2inspire_Backend')

from utils.report_pdf_v2 import ReportPDFGenerator

# Dados de teste simulando uma análise completa - TEXTOS CURTOS para caber numa página
test_analysis_data = {
    "candidate_profile": {
        "detected_name": "Samuel Rolo",
        "detected_role": "HR Digital & Process Excellence Manager",
        "detected_sector": "Recursos Humanos / Transformação Digital",
        "total_years_exp": "11 anos",
        "seniority": "Direção/Executivo",
        "education_level": "Licenciatura em Gestão de Recursos Humanos",
        "languages_detected": ["Português (Nativo)", "Inglês (Fluente)", "Espanhol (Intermédio)"],
        "key_skills": ["Transformação Digital", "Gestão de Mudança", "Liderança de Equipas", "Otimização de Processos", "People Analytics"]
    },
    
    "global_summary": {
        "strengths": [
            "Trajetória de 11 anos com progressão consistente em RH e transformação digital",
            "Experiência em organizações de referência como AstraZeneca e Deloitte",
            "Especialização em área de elevada procura: digitalização de processos de RH",
            "Formação académica sólida com Licenciatura em Gestão de RH"
        ],
        "improvements": [
            "Quantificar resultados com métricas de impacto e ROI das iniciativas",
            "Reforçar keywords estratégicas para otimização ATS",
            "Articular proposta de valor única e diferenciadora",
            "Adicionar sumário executivo de alto impacto no início do CV"
        ]
    },
    
    "executive_summary": {
        "global_score": 72,
        "market_positioning": """• **Posicionamento competitivo**: Perfil bem posicionado para funções de direção em RH digital, com experiência em organizações de referência como AstraZeneca.
• **Diferenciação**: A combinação de competências em processos de RH com transformação digital responde a uma necessidade crescente do mercado.
• **Benchmark**: Comparativamente com perfis equivalentes, destaca-se pela progressão consistente e especialização em área de elevada procura.
• **Oportunidade**: O mercado atual valoriza evidências concretas de impacto - recomenda-se reforçar métricas quantificáveis.""",
        
        "key_decision_factors": """• **Experiência em transformação digital**: Competência escassa e altamente procurada no mercado atual de RH.
• **Progressão de carreira**: Evidencia capacidade de crescimento e reconhecimento por empregadores anteriores.
• **Competências de liderança**: Capacidade inferida de gestão de stakeholders e condução de mudança organizacional.
• **Área de melhoria**: Necessidade de maior evidência quantitativa de resultados e impacto individual."""
    },
    
    "diagnostic_impact": {
        "first_30_seconds_read": """• **Primeira impressão positiva**: Hierarquia visual clara, senioridade adequada, especialização relevante.
• **Ponto de fricção**: Sumário executivo carece de métricas quantificáveis que demonstrem valor imediato.
• **Densidade textual**: Algumas secções beneficiariam de elementos visuais distintivos para facilitar scanning.
• **Proposta de valor**: Não emerge com clareza suficiente nos primeiros momentos de contacto.""",
        
        "impact_strengths": """• **Credibilidade organizacional**: Experiência em multinacionais de referência (AstraZeneca) confere validação imediata.
• **Especialização estratégica**: Transformação digital de RH posiciona-se como área de elevada procura e diferenciação.
• **Progressão demonstrada**: Assunção crescente de responsabilidades indica reconhecimento e potencial.
• **Competências comportamentais**: Liderança e gestão de mudança alinham-se com requisitos de funções de direção.""",
        
        "impact_strengths_signal": "Experiência em multinacionais, especialização em transformação digital, progressão consistente.",
        "impact_strengths_missing": "Métricas quantificáveis, evidência de impacto específico, contribuição individual vs equipa.",
        
        "impact_dilutions": """• **Ausência de métricas**: Descrições sem quantificação reduzem capacidade de demonstrar valor concreto.
• **Narrativa convencional**: Diferenciação insuficiente face a candidatos com perfis semelhantes.
• **Tendência ao generalismo**: Algumas descrições diluem a perceção de especialização.
• **Hierarquização de competências**: Falta distinção clara entre áreas de excelência e complementares."""
    },
    
    "content_structure_analysis": {
        "organization_hierarchy": """• **Estrutura convencional**: Sequência lógica de secções facilita navegação por recrutadores.
• **Hierarquia visual**: Títulos e subtítulos permitem identificação rápida das componentes.
• **Densidade textual**: Blocos extensos sem destaque visual podem ser ignorados em triagem inicial.
• **Lacuna identificada**: Ausência de sumário executivo robusto no início do documento.""",
        
        "organization_hierarchy_signal": "Estrutura navegável, hierarquia clara, sequência lógica.",
        "organization_hierarchy_missing": "Sumário executivo de impacto, elementos visuais de destaque.",
        
        "responsibilities_results_balance": """• **Predominância de responsabilidades**: Descrições focadas em atividades, com insuficiente ênfase em resultados.
• **Linguagem a transformar**: Expressões como 'responsável por' não comunicam eficácia ou contribuição.
• **Mentalidade orientada a resultados**: Cada experiência deveria responder: 'Qual foi o impacto mensurável?'
• **Oportunidade**: Reflexão estruturada pode revelar métricas não documentadas.""",
        
        "responsibilities_results_balance_signal": "Descrições de âmbito claras, progressão de senioridade evidente.",
        "responsibilities_results_balance_missing": "Métricas quantificáveis, evidência de impacto específico.",
        
        "orientation": """• **Perfil de execução**: Forte capacidade de implementação e gestão operacional.
• **Indicadores de liderança**: Gestão de equipas e condução de iniciativas de transformação.
• **Pensamento estratégico**: Dimensão menos evidente, requer articulação mais explícita.
• **Implicação**: Posicionamento adequado para direção intermédia; C-level exigirá ajustes na narrativa."""
    },
    
    "ats_digital_recruitment": {
        "compatibility": """• **Estrutura favorável**: Secções delimitadas e formatação simples facilitam parsing automatizado.
• **Oportunidade de keywords**: Densidade de termos técnicos poderia ser aumentada estrategicamente.
• **Alinhamento terminológico**: Margem de melhoria na correspondência com linguagem de anúncios.
• **Recomendação**: Analisar descrições de funções similares para informar ajustes.""",
        
        "compatibility_signal": "Estrutura favorável ao parsing, formatação simples, secções convencionais.",
        "compatibility_missing": "Densidade de keywords otimizada, alinhamento com terminologia de mercado.",
        
        "filtering_risks": """• **Risco principal**: Densidade insuficiente de palavras-chave pode resultar em exclusão automática.
• **Filtros binários**: Ausência de termos específicos (ex: SAP SuccessFactors) pode excluir candidatura.
• **Formatação**: Tabelas ou colunas múltiplas podem gerar problemas de parsing em alguns sistemas.
• **Mitigação**: Criar versões específicas otimizadas para diferentes tipos de candidatura.""",
        
        "alignment": """• **Recrutamento digital**: Currículos devem ser otimizados para leitura humana e processamento algorítmico.
• **Presença digital**: Consistência entre CV e perfil LinkedIn é frequentemente verificada.
• **Sourcing ativo**: Perfis com elevada densidade de keywords são favorecidos em pesquisas.
• **Tendência**: Processos mais ágeis valorizam comunicação concisa e impactante."""
    },
    
    "skills_differentiation": {
        "technical_behavioral_analysis": """• **Competências técnicas**: Gestão de processos de RH, implementação de soluções tecnológicas, People Analytics.
• **Ativo de elevado valor**: Experiência em transformação digital alinha-se com exigências do mercado.
• **Competências comportamentais**: Liderança de equipas, gestão de stakeholders, capacidade de influência.
• **Alinhamento**: Globalmente positivo com funções equivalentes; margem para reforço em analytics avançado.""",
        
        "differentiation_factors": """• **Posicionamento distintivo**: Interseção entre competências de RH e transformação digital é menos comum.
• **Experiência multinacional**: Exposição a práticas de classe mundial diferencia de perfis locais.
• **Progressão de carreira**: Assunção crescente de responsabilidades indica potencial futuro.
• **Oportunidade**: Articular proposta de valor única que sintetize estes elementos distintivos.""",
        
        "differentiation_factors_signal": "Especialização em transformação digital de RH, experiência multinacional.",
        "differentiation_factors_missing": "Articulação explícita da proposta de valor única, quantificação do impacto.",
        
        "common_undifferentiated": """• **Competências genéricas**: 'Trabalho em equipa', 'comunicação' perderam capacidade de diferenciação.
• **Descrições standard**: Responsabilidades típicas sem evidência de contribuição específica.
• **Estratégia recomendada**: Contextualizar competências com exemplos concretos e resultados mensuráveis.
• **Transformação**: De 'forte capacidade de comunicação' para situações específicas com impacto demonstrado."""
    },
    
    "strategic_risks": {
        "identified_risks": """• **Lacunas temporais**: Não identificadas lacunas significativas no percurso profissional.
• **Mudanças de emprego**: Frequência dentro de padrões aceitáveis para o setor.
• **Transições de carreira**: Coerência mantida ao longo do percurso, sem desvios problemáticos.
• **Subposicionamento**: Risco de perceção generalista em algumas descrições de experiência.""",
        
        "identified_risks_signal": "Percurso coerente, sem lacunas ou transições problemáticas.",
        "identified_risks_missing": "Especialização mais explícita, diferenciação face a perfis semelhantes.",
        
        "mitigation_recommendations": """• **Quantificação sistemática**: Adicionar métricas de impacto a todas as experiências relevantes.
• **Proposta de valor**: Desenvolver narrativa distintiva que articule valor único.
• **Otimização ATS**: Incorporar keywords estratégicas sem comprometer legibilidade.
• **Sumário executivo**: Criar secção de alto impacto no início do documento."""
    },
    
    "phrase_improvements": [
        {
            "category": "Descrição de Responsabilidades",
            "before": "Responsável pela gestão de processos de RH e implementação de melhorias",
            "after": "Redesenhei 12 processos core de RH, reduzindo tempo de ciclo em 35% e eliminando €180K em custos operacionais anuais através de automação e otimização de workflows",
            "justification": "A versão melhorada transforma uma descrição genérica numa afirmação de impacto quantificável. A utilização de verbo de ação forte ('redesenhei'), números específicos ('12 processos', '35%', '€180K'), e resultados concretos ('reduzindo', 'eliminando') comunica valor de forma imediata e memorável."
        },
        {
            "category": "Liderança e Gestão de Stakeholders",
            "before": "Liderança de equipa e gestão de stakeholders em projetos de transformação",
            "after": "Liderei equipa multidisciplinar de 8 elementos na implementação de HRIS que serviu 2.500 colaboradores, alcançando 94% de adoção em 6 meses e NPS interno de 4.2/5",
            "justification": "A reformulação adiciona escala ('8 elementos', '2.500 colaboradores'), métricas de sucesso ('94% adoção', 'NPS 4.2/5') e contexto temporal ('6 meses') que demonstram capacidade de entrega e impacto mensurável em iniciativas de transformação."
        },
        {
            "category": "Competências Técnicas",
            "before": "Experiência em implementação de sistemas de RH e análise de dados",
            "after": "Implementei SAP SuccessFactors e Workday em 3 organizações, desenvolvendo dashboards de People Analytics que informaram decisões de talent management para 500+ gestores",
            "justification": "A versão otimizada especifica tecnologias concretas (SAP SuccessFactors, Workday), quantifica experiência ('3 organizações') e demonstra impacto estratégico ('500+ gestores'), aumentando significativamente a relevância para sistemas ATS e recrutadores."
        }
    ],
    
    "recommended_certifications": [
        {
            "name": "SHRM Senior Certified Professional (SHRM-SCP)",
            "issuer": "Society for Human Resource Management",
            "priority": "Alta",
            "relevance": "Certificação de referência internacional em RH sénior, validando competências estratégicas e de liderança em gestão de pessoas.",
            "investment": "€400-600 + preparação",
            "where_to_obtain": "shrm.org"
        },
        {
            "name": "SAP SuccessFactors Certification",
            "issuer": "SAP",
            "priority": "Alta",
            "relevance": "Valida competências técnicas em HRIS líder de mercado, aumentando empregabilidade em organizações que utilizam SAP.",
            "investment": "€500-800",
            "where_to_obtain": "training.sap.com"
        },
        {
            "name": "People Analytics Certificate",
            "issuer": "AIHR Academy",
            "priority": "Média",
            "relevance": "Reforça competências em análise de dados de RH, área de crescente importância estratégica.",
            "investment": "€1.000-1.500",
            "where_to_obtain": "aihr.com"
        }
    ],
    
    "priority_recommendations": [
        {
            "priority": "Crítica",
            "action": "Adicionar métricas quantificáveis a todas as experiências profissionais",
            "impact": "Aumento significativo da capacidade de demonstrar valor concreto a potenciais empregadores",
            "timeframe": "1-2 semanas"
        },
        {
            "priority": "Alta",
            "action": "Desenvolver sumário executivo de alto impacto com proposta de valor única",
            "impact": "Melhoria da primeira impressão e diferenciação face a candidatos com perfis semelhantes",
            "timeframe": "1 semana"
        },
        {
            "priority": "Alta",
            "action": "Otimizar keywords para sistemas ATS e alinhamento com terminologia de mercado",
            "impact": "Aumento da visibilidade em processos de recrutamento digital",
            "timeframe": "1 semana"
        },
        {
            "priority": "Média",
            "action": "Obter certificação SHRM-SCP para validação internacional de competências",
            "impact": "Reforço de credibilidade e diferenciação em processos de seleção",
            "timeframe": "3-6 meses"
        }
    ],
    
    "pdf_extended_content": {
        "sector_analysis": {
            "identified_sector": "Recursos Humanos / Transformação Digital",
            "sector_trends": """• **Digitalização acelerada**: A pandemia acelerou a adoção de tecnologias de RH em 3-5 anos.
• **People Analytics**: Crescente importância de decisões baseadas em dados na gestão de pessoas.
• **Employee Experience**: Foco na experiência do colaborador como diferencial competitivo.
• **Trabalho híbrido**: Novas competências necessárias para gestão de equipas distribuídas.""",
            "competitive_landscape": """• **Procura elevada**: Profissionais com competências em transformação digital de RH são escassos.
• **Salários competitivos**: Funções de direção em RH digital apresentam remunerações acima da média.
• **Concorrência**: Perfis com certificações específicas e métricas de impacto são favorecidos.
• **Oportunidade**: Posicionamento distintivo pode garantir acesso a oportunidades premium."""
        }
    },
    
    "market_analysis": {
        "sector_trends": """• **Transformação digital**: Prioridade estratégica para 85% das organizações em 2024-2025.
• **Escassez de talento**: Profissionais de RH com competências digitais são altamente procurados.
• **Certificações valorizadas**: SHRM, SAP SuccessFactors e People Analytics ganham relevância.
• **Remuneração**: Funções de direção em RH digital apresentam crescimento salarial de 15-20%.""",
        "competitive_landscape": """• **Diferenciação crítica**: Métricas de impacto distinguem candidatos em processos competitivos.
• **Experiência multinacional**: Valorizada em organizações com operações internacionais.
• **Competências híbridas**: Combinação de RH tradicional com digital é escassa e procurada.
• **Networking**: Presença ativa em comunidades profissionais aumenta visibilidade.""",
        "opportunities_threats": """• **Oportunidades**: Crescimento do setor, escassez de talento especializado, remunerações atrativas.
• **Ameaças**: Automação de funções operacionais, necessidade de atualização contínua.
• **Recomendação**: Investir em certificações e demonstração de impacto quantificável.
• **Posicionamento**: Focar em funções estratégicas vs operacionais para longevidade de carreira."""
    },
    
    "executive_conclusion": {
        "potential_after_improvements": """• **Score projetado**: Implementação das recomendações pode elevar pontuação global de 62 para 80+.
• **Competitividade**: Perfil passará a destacar-se no top 15% de candidatos para funções equivalentes.
• **Empregabilidade**: Aumento significativo de convites para entrevistas em processos seletivos.
• **Posicionamento**: Transição de candidato competente para candidato de referência no mercado.""",
        "expected_competitiveness": """• **Curto prazo (1-3 meses)**: Melhorias imediatas em métricas e sumário executivo.
• **Médio prazo (3-6 meses)**: Obtenção de certificação e reforço de presença digital.
• **Longo prazo (6-12 meses)**: Consolidação como referência em transformação digital de RH.
• **ROI esperado**: Investimento em otimização de CV tipicamente retorna em 3-6 meses."""
    },
    
    "final_conclusion": {
        "executive_synthesis": """• **Perfil sólido**: Base competitiva forte com experiência relevante e progressão consistente.
• **Oportunidades claras**: Quantificação de resultados e articulação de proposta de valor única.
• **Potencial elevado**: Implementação das recomendações posicionará perfil no top do mercado.
• **Próximos passos**: Priorizar métricas, sumário executivo e otimização ATS.""",
        "next_steps": """• **Imediato**: Adicionar métricas quantificáveis às 3 experiências mais recentes.
• **Semana 1**: Desenvolver sumário executivo de alto impacto.
• **Semana 2**: Otimizar keywords e validar com ferramenta ATS.
• **Mês 1-3**: Iniciar preparação para certificação SHRM-SCP."""
    },
    
    "radar_data": {
        "estrutura": 14,
        "conteudo": 13,
        "ats": 12,
        "impacto": 11,
        "branding": 12,
        "riscos": 13
    }
}

def main():
    print("=" * 60)
    print("TESTE DO GERADOR DE RELATÓRIOS PDF v2")
    print("=" * 60)
    
    generator = ReportPDFGenerator()
    
    output_path = "/home/ubuntu/Relatorio_Analise_CV_Samuel_Rolo.pdf"
    
    print("[INFO] Gerando PDF de teste...")
    
    try:
        result = generator.create_pdf(test_analysis_data)
        
        # Se result for uma tupla, extrair o PDF
        if isinstance(result, tuple):
            pdf_content = result[0]
        else:
            pdf_content = result
        
        # Se for BytesIO, extrair os bytes
        if hasattr(pdf_content, 'getvalue'):
            pdf_bytes = pdf_content.getvalue()
        else:
            pdf_bytes = pdf_content
        
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"[SUCESSO] PDF gerado: {output_path}")
        print(f"[INFO] Tamanho: {len(pdf_bytes)} bytes")
        
    except Exception as e:
        print(f"[ERRO] Falha na geração: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
