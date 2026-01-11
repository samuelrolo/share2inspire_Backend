#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para o novo gerador de relatórios PDF v2
"""

import sys
sys.path.insert(0, '/home/ubuntu/share2inspire_Backend')

from utils.report_pdf_v2 import ReportPDFGenerator

# Dados de teste simulando uma análise completa
test_analysis_data = {
    "candidate_profile": {
        "detected_name": "Samuel Rolo",
        "detected_role": "HR Digital & Process Excellence Manager",
        "detected_sector": "Recursos Humanos / Transformação Digital",
        "total_years_exp": "11 anos",
        "seniority": "Direção/Executivo",
        "education_level": "Mestrado em Gestão de Recursos Humanos",
        "languages_detected": ["Português (Nativo)", "Inglês (Fluente)", "Espanhol (Intermédio)"],
        "key_skills": ["Transformação Digital", "Gestão de Mudança", "Liderança de Equipas", "Otimização de Processos", "People Analytics"]
    },
    
    "global_summary": {
        "strengths": [
            "Trajetória de 11 anos com progressão consistente em RH e transformação digital",
            "Experiência em organizações de referência como AstraZeneca e Deloitte",
            "Especialização em área de elevada procura: digitalização de processos de RH",
            "Formação académica sólida com Mestrado em Gestão de RH"
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
        "market_positioning": """O perfil apresentado demonstra uma trajetória profissional sólida e bem estruturada na área de Recursos Humanos, com particular ênfase em transformação digital e excelência de processos. A experiência acumulada ao longo de 11 anos, combinada com passagens por organizações de referência como AstraZeneca, posiciona o candidato num patamar competitivo para funções de direção em empresas de média e grande dimensão no mercado português e europeu.

A análise do percurso revela uma progressão consistente que evidencia capacidade de assumir responsabilidades crescentes e entregar resultados em contextos de elevada complexidade organizacional. O posicionamento atual como gestor de transformação digital em RH representa uma especialização de elevado valor no mercado atual, onde a digitalização dos processos de gestão de pessoas constitui uma prioridade estratégica para a maioria das organizações.

Comparativamente com benchmarks de mercado para funções equivalentes, o perfil apresenta pontos de diferenciação relevantes, nomeadamente a combinação de competências técnicas em processos com visão estratégica de negócio. Esta dualidade é particularmente valorizada em contextos de transformação organizacional, onde a capacidade de traduzir requisitos de negócio em soluções operacionais constitui um fator crítico de sucesso.

No entanto, identificam-se oportunidades de reforço do posicionamento, particularmente na quantificação de resultados e na articulação de uma proposta de valor mais distintiva. O mercado atual exige evidências concretas de impacto, e o currículo beneficiaria de uma maior densidade de métricas que demonstrem o retorno gerado pelas iniciativas lideradas.""",
        
        "key_decision_factors": """Os fatores determinantes para a decisão de recrutamento neste perfil centram-se em três dimensões principais que merecem análise aprofundada.

Em primeiro lugar, a experiência em transformação digital de RH constitui um ativo de elevado valor estratégico. Num contexto onde a maioria das organizações enfrenta desafios de modernização dos seus processos de gestão de pessoas, profissionais com experiência comprovada nesta área são escassos e altamente procurados. O candidato demonstra conhecimento prático de implementação de soluções tecnológicas e otimização de processos, competências que respondem diretamente às necessidades do mercado.

Em segundo lugar, a progressão de carreira evidencia capacidade de crescimento e adaptação. A transição entre diferentes contextos organizacionais, mantendo uma linha de especialização coerente, sugere maturidade profissional e clareza de objetivos. Este padrão é valorizado por recrutadores que procuram candidatos com potencial de desenvolvimento a longo prazo.

Por último, o perfil de competências comportamentais inferido a partir das experiências descritas aponta para capacidades de liderança e gestão de stakeholders que são críticas em funções de direção. A capacidade de influenciar decisões e mobilizar equipas em contextos de mudança constitui um diferencial competitivo relevante.

Contudo, elementos que podem gerar hesitação incluem a necessidade de maior evidência quantitativa de resultados e uma articulação mais clara do impacto específico das contribuições individuais versus resultados de equipa."""
    },
    
    "diagnostic_impact": {
        "first_30_seconds_read": """A primeira impressão gerada pelo currículo nos segundos iniciais de leitura é globalmente positiva, embora com margem significativa para otimização. Um recrutador sénior, habituado a processar elevados volumes de candidaturas, identificaria rapidamente os elementos estruturantes do perfil: senioridade adequada, especialização relevante e percurso em organizações reconhecidas.

A hierarquia visual do documento permite uma navegação razoavelmente fluida, com secções claramente delimitadas que facilitam a localização de informação específica. O nome e função atual destacam-se adequadamente, estabelecendo desde logo o posicionamento profissional do candidato.

No entanto, a análise crítica revela pontos de fricção que podem comprometer a eficácia da comunicação. O sumário executivo, elemento crucial para captar atenção nos primeiros segundos, carece de impacto suficiente. A ausência de métricas quantificáveis nesta secção representa uma oportunidade perdida de demonstrar valor de forma imediata e memorável.

A densidade textual em algumas secções pode dificultar a extração rápida de informação relevante. Recrutadores experientes desenvolvem técnicas de scanning que privilegiam elementos visuais distintivos e dados numéricos, elementos que poderiam ser mais proeminentes no documento atual.

A proposta de valor única do candidato não emerge com clareza suficiente nos primeiros momentos de contacto com o documento. Embora as competências e experiências sejam relevantes, a narrativa que as conecta e diferencia de outros candidatos com perfis semelhantes necessita de maior articulação.""",
        
        "impact_strengths": """Os pontos de impacto positivo do currículo concentram-se em dimensões específicas que merecem reconhecimento e podem ser amplificadas.

A experiência em organizações de referência internacional, como a AstraZeneca, confere credibilidade imediata ao perfil. Este tipo de contexto organizacional é associado a elevados padrões de exigência e práticas de gestão sofisticadas, o que por inferência sugere que o candidato foi exposto a metodologias e processos de classe mundial.

A especialização em transformação digital de RH representa um posicionamento estratégico acertado face às tendências do mercado. A convergência entre competências de gestão de pessoas e conhecimento tecnológico responde a uma necessidade crescente das organizações, criando um nicho de diferenciação com procura sustentada.

A progressão de carreira demonstrada evidencia capacidade de crescimento e reconhecimento por parte de empregadores anteriores. A assunção de responsabilidades crescentes ao longo do tempo constitui um indicador positivo de desempenho e potencial.

As competências comportamentais inferidas, particularmente em liderança e gestão de mudança, alinham-se com os requisitos típicos de funções de direção. A capacidade de navegar contextos de transformação organizacional é cada vez mais valorizada num ambiente de negócios caracterizado por volatilidade e incerteza.""",
        
        "impact_strengths_signal": "Experiência em multinacionais de referência, especialização em transformação digital de RH, progressão de carreira consistente.",
        "impact_strengths_missing": "Quantificação de resultados específicos, métricas de impacto das iniciativas lideradas, evidência de contribuição individual versus resultados de equipa.",
        
        "impact_dilutions": """Os pontos onde o impacto do currículo se dilui merecem atenção prioritária na estratégia de otimização.

A ausência sistemática de métricas quantificáveis constitui a principal fragilidade identificada. Descrições de responsabilidades sem evidência de resultados concretos reduzem significativamente a capacidade de demonstrar valor. Expressões como 'liderou iniciativas de transformação' ou 'otimizou processos' carecem do complemento numérico que transformaria afirmações genéricas em evidências convincentes de impacto.

A narrativa profissional, embora coerente, apresenta-se de forma relativamente convencional. Num mercado competitivo, onde múltiplos candidatos apresentam perfis superficialmente semelhantes, a diferenciação exige uma articulação mais distintiva da proposta de valor única. O que torna este candidato especificamente valioso permanece insuficientemente explícito.

Algumas descrições de experiência tendem para o generalismo, diluindo a perceção de especialização. A tentativa de demonstrar versatilidade pode, paradoxalmente, enfraquecer o posicionamento como especialista numa área específica. O equilíbrio entre amplitude e profundidade necessita de recalibração.

A secção de competências, embora abrangente, beneficiaria de uma hierarquização mais clara que destaque as áreas de excelência versus competências complementares. A apresentação atual não permite distinguir facilmente os pontos de diferenciação mais relevantes."""
    },
    
    "content_structure_analysis": {
        "organization_hierarchy": """A organização estrutural do currículo segue convenções estabelecidas que facilitam a navegação por parte de recrutadores familiarizados com formatos tradicionais. A sequência de secções apresenta uma lógica compreensível, iniciando com informação de identificação e contacto, seguida de experiência profissional, formação académica e competências complementares.

A hierarquia visual estabelecida através de títulos e subtítulos permite a identificação rápida das diferentes componentes do documento. Esta clareza estrutural constitui um ponto positivo que facilita tanto a leitura humana como o processamento por sistemas automatizados de triagem.

No entanto, a análise detalhada revela oportunidades de otimização significativas. A densidade textual em algumas secções, particularmente nas descrições de experiência profissional, pode criar barreiras à extração rápida de informação relevante. Blocos de texto extensos sem elementos de destaque visual tendem a ser ignorados em processos de triagem inicial.

A ausência de um sumário executivo robusto no início do documento representa uma lacuna estrutural relevante. Este elemento, quando bem construído, funciona como âncora de atenção e síntese de valor que orienta a leitura subsequente do documento.

A ordem das secções poderia beneficiar de ajustes estratégicos em função do perfil e objetivos específicos. Para candidatos com experiência significativa, a priorização da experiência profissional sobre a formação académica é geralmente recomendada, mas a forma como esta priorização é executada pode ser refinada.""",
        
        "organization_hierarchy_signal": "Estrutura convencional e navegável, hierarquia visual clara, sequência lógica de secções.",
        "organization_hierarchy_missing": "Sumário executivo de impacto, elementos visuais de destaque, otimização da densidade textual.",
        
        "responsibilities_results_balance": """O equilíbrio entre a descrição de responsabilidades e a apresentação de resultados constitui uma das dimensões mais críticas na avaliação de um currículo executivo, e representa simultaneamente uma das principais oportunidades de melhoria identificadas.

A análise do conteúdo atual revela uma predominância de descrições focadas em responsabilidades e atividades, com insuficiente ênfase nos resultados e impacto gerado. Esta orientação, embora comum em muitos currículos, limita significativamente a capacidade de demonstrar valor concreto a potenciais empregadores.

Expressões como 'responsável por', 'envolvido em' ou 'participou em' descrevem âmbito de atuação mas não comunicam eficácia ou contribuição específica. A transformação destas descrições em afirmações orientadas a resultados requer a incorporação sistemática de métricas, percentagens, valores e outros indicadores quantificáveis.

A mentalidade orientada para resultados que caracteriza profissionais de alto desempenho deve refletir-se na forma como as experiências são comunicadas. Cada entrada de experiência profissional deveria responder implicitamente à questão: 'Qual foi o impacto mensurável da minha contribuição?'

A ausência de quantificação não significa necessariamente ausência de resultados relevantes. Frequentemente, profissionais subestimam ou não documentam adequadamente as suas conquistas. Um exercício de reflexão estruturada sobre cada experiência pode revelar métricas e evidências de impacto que enriqueçam significativamente o documento.""",
        
        "responsibilities_results_balance_signal": "Descrições de âmbito de responsabilidade claras, progressão de senioridade evidente.",
        "responsibilities_results_balance_missing": "Métricas quantificáveis, evidência de impacto específico, transformação de responsabilidades em conquistas.",
        
        "orientation": """A orientação predominante do currículo situa-se na interseção entre execução operacional e liderança tática, com elementos emergentes de pensamento estratégico que poderiam ser mais explicitamente articulados.

A linguagem utilizada nas descrições de experiência sugere um perfil com forte capacidade de execução e implementação. Verbos como 'implementou', 'coordenou' e 'desenvolveu' predominam, indicando competência na tradução de diretrizes em ações concretas. Esta orientação é valorizada em funções que requerem capacidade de entrega e gestão operacional.

Simultaneamente, identificam-se indicadores de capacidade de liderança, nomeadamente na gestão de equipas e na condução de iniciativas de transformação. A progressão para funções de maior responsabilidade sugere reconhecimento destas competências por parte de empregadores anteriores.

No entanto, a dimensão de pensamento estratégico apresenta-se de forma menos evidente. Para funções de direção executiva, a capacidade de contribuir para a definição de estratégia e influenciar decisões ao mais alto nível constitui um requisito crítico. O currículo beneficiaria de uma articulação mais explícita de contribuições estratégicas e visão de negócio.

As implicações desta orientação para a progressão de carreira são significativas. A transição para funções de C-level ou direção executiva requer tipicamente uma evolução do perfil de execução para um perfil de liderança estratégica. O currículo atual posiciona adequadamente o candidato para funções de direção intermédia, mas a aspiração a posições de maior senioridade exigirá ajustes na narrativa e posicionamento."""
    },
    
    "ats_digital_recruitment": {
        "compatibility": """A compatibilidade do currículo com sistemas ATS (Applicant Tracking Systems) apresenta um perfil misto que requer atenção específica para maximizar a probabilidade de sucesso em processos de recrutamento digital.

Os sistemas ATS, utilizados pela maioria das grandes organizações para gestão de candidaturas, processam currículos através de algoritmos que identificam e indexam palavras-chave, estruturas e padrões específicos. A otimização para estes sistemas constitui um requisito fundamental no contexto atual de recrutamento.

A estrutura geral do documento apresenta características favoráveis ao processamento automatizado. A utilização de secções claramente delimitadas, títulos convencionais e formatação relativamente simples facilita a extração de informação pelos algoritmos de parsing. A ausência de elementos gráficos complexos ou formatação não-standard reduz o risco de erros de interpretação.

No entanto, a análise de palavras-chave revela oportunidades significativas de otimização. A densidade de termos técnicos relevantes para a função alvo poderia ser aumentada sem comprometer a legibilidade humana. Keywords específicas da área de Recursos Humanos, transformação digital e gestão de processos deveriam aparecer com maior frequência e em posições estratégicas do documento.

A correspondência entre a linguagem do currículo e a terminologia típica de descrições de funções similares apresenta margem de melhoria. A análise de anúncios de emprego para funções equivalentes pode informar ajustes que aumentem a relevância percebida pelos algoritmos de matching.""",
        
        "compatibility_signal": "Estrutura favorável ao parsing, formatação simples, secções convencionais.",
        "compatibility_missing": "Densidade de keywords otimizada, alinhamento com terminologia de mercado, posicionamento estratégico de termos-chave.",
        
        "filtering_risks": """Os riscos de filtragem automática identificados merecem atenção prioritária, dado o seu potencial impacto na visibilidade do candidato em processos de recrutamento digital.

O principal risco identificado relaciona-se com a densidade insuficiente de palavras-chave críticas. Sistemas ATS atribuem pontuações de relevância baseadas na frequência e posicionamento de termos específicos. Um currículo que não atinja limiares mínimos de correspondência pode ser automaticamente excluído antes de qualquer revisão humana.

A ausência de determinados termos técnicos ou certificações específicas pode constituir um fator de exclusão em processos que utilizem filtros binários. Por exemplo, se uma descrição de função especificar 'experiência em SAP SuccessFactors' como requisito, a ausência desta menção específica pode resultar em exclusão automática, mesmo que o candidato possua competências equivalentes.

A formatação do documento, embora globalmente adequada, apresenta elementos que podem gerar problemas de parsing em alguns sistemas. Tabelas, colunas múltiplas ou elementos gráficos, se presentes, podem não ser corretamente interpretados por todos os algoritmos.

A estratégia de mitigação recomendada inclui a criação de versões específicas do currículo otimizadas para diferentes tipos de candidatura, a incorporação sistemática de keywords relevantes, e a validação do documento através de ferramentas de análise ATS disponíveis no mercado.""",
        
        "alignment": """O alinhamento do currículo com as práticas atuais de recrutamento digital requer uma compreensão das tendências e expectativas do mercado que informem ajustes estratégicos.

O recrutamento digital contemporâneo caracteriza-se pela utilização intensiva de tecnologia em todas as fases do processo, desde a atração de candidatos até à decisão final. Esta realidade implica que os currículos devem ser otimizados não apenas para leitura humana, mas também para processamento algorítmico.

A presença digital do candidato, incluindo perfis em plataformas profissionais como LinkedIn, constitui um complemento cada vez mais relevante ao currículo tradicional. A consistência entre o currículo e o perfil online é frequentemente verificada por recrutadores, e discrepâncias podem gerar desconfiança.

As práticas de sourcing ativo, onde recrutadores pesquisam proativamente candidatos em bases de dados e plataformas, valorizam perfis com elevada densidade de keywords relevantes e posicionamento claro. O currículo deve funcionar como documento de referência que reforce e complemente a presença digital.

A tendência para processos de recrutamento mais ágeis e digitalizados implica que a capacidade de comunicar valor de forma concisa e impactante se torna ainda mais crítica. Currículos extensos ou com baixa densidade de informação relevante tendem a ser desfavorecidos em contextos de elevado volume de candidaturas."""
    },
    
    "skills_differentiation": {
        "technical_behavioral_analysis": """A análise das competências técnicas e comportamentais evidenciadas no currículo revela um perfil equilibrado com pontos de força identificáveis e oportunidades de desenvolvimento.

No domínio técnico, destacam-se competências em gestão de processos de RH, implementação de soluções tecnológicas e análise de dados de pessoas. Estas competências alinham-se com as exigências crescentes do mercado para profissionais de RH com literacia digital e capacidade de alavancar tecnologia para otimização de processos.

A experiência em transformação digital constitui um ativo técnico de elevado valor, particularmente relevante no contexto atual onde a maioria das organizações procura modernizar as suas práticas de gestão de pessoas. O conhecimento de metodologias de gestão de mudança complementa esta competência técnica com uma dimensão comportamental crítica.

As competências comportamentais inferidas incluem liderança de equipas, gestão de stakeholders e capacidade de influência. Estas soft skills são frequentemente determinantes em funções de direção, onde a capacidade de mobilizar pessoas e recursos em torno de objetivos comuns constitui um fator crítico de sucesso.

A comparação com as exigências típicas de funções equivalentes sugere um alinhamento globalmente positivo, com margem para reforço em áreas específicas como analytics avançado e competências digitais emergentes.""",
        
        "differentiation_factors": """Os fatores de diferenciação que distinguem este perfil de candidatos com experiência superficialmente semelhante merecem identificação e amplificação estratégica.

A combinação específica de competências em processos de RH com experiência em transformação digital representa um posicionamento distintivo. Enquanto muitos profissionais de RH possuem competências tradicionais de gestão de pessoas, e profissionais de tecnologia dominam ferramentas digitais, a interseção destas duas dimensões é menos comum e mais valorizada.

A experiência em contextos multinacionais de elevada exigência, como a AstraZeneca, confere uma perspetiva internacional e exposição a práticas de classe mundial que diferencia o perfil de candidatos com experiência exclusivamente em contextos locais ou de menor complexidade.

A progressão de carreira demonstrada, com assunção crescente de responsabilidades, evidencia capacidade de crescimento e reconhecimento por parte de empregadores, constituindo um indicador de potencial futuro.

No entanto, estes fatores de diferenciação poderiam ser comunicados de forma mais explícita e impactante. A articulação de uma proposta de valor única que sintetize estes elementos distintivos fortaleceria significativamente o posicionamento competitivo.""",
        
        "differentiation_factors_signal": "Especialização em transformação digital de RH, experiência multinacional, progressão de carreira consistente.",
        "differentiation_factors_missing": "Articulação explícita da proposta de valor única, quantificação do impacto diferenciador, narrativa distintiva.",
        
        "common_undifferentiated": """As competências e experiências que, embora relevantes, são percecionadas como comuns ou indiferenciadas no mercado atual requerem atenção estratégica para evitar a diluição do posicionamento.

Competências genéricas como 'trabalho em equipa', 'comunicação' ou 'orientação para resultados', frequentemente listadas em currículos, perderam capacidade de diferenciação devido à sua ubiquidade. Praticamente todos os candidatos a funções de gestão afirmam possuir estas competências, tornando-as irrelevantes como fatores de distinção.

Descrições de experiência que se limitam a enumerar responsabilidades standard da função, sem evidência de contribuição específica ou resultados diferenciadores, contribuem para uma perceção de perfil genérico. A transformação destas descrições em narrativas de impacto requer esforço deliberado de reflexão e articulação.

A estratégia recomendada para aumentar o valor percebido destas competências passa pela sua contextualização específica e quantificação. Em vez de afirmar genericamente 'forte capacidade de comunicação', demonstrar esta competência através de exemplos concretos de situações onde a comunicação eficaz gerou resultados mensuráveis."""
    },
    
    "strategic_risks": {
        "identified_risks": """A identificação e análise dos riscos estratégicos inerentes ao currículo constitui um exercício crítico para informar a estratégia de otimização e mitigação.

O risco mais significativo identificado relaciona-se com a ausência sistemática de métricas quantificáveis. Num mercado onde a demonstração de impacto através de dados constitui uma expectativa crescente, currículos que não apresentam evidência numérica de resultados são percecionados como menos credíveis ou menos orientados para resultados.

O potencial de subposicionamento representa outro risco relevante. A forma como as experiências são descritas pode não refletir adequadamente o nível de senioridade e impacto real do candidato. Descrições modestas ou conservadoras podem resultar em perceções de menor competência do que a realidade.

A ambiguidade na articulação da proposta de valor única dificulta a diferenciação face a candidatos com perfis superficialmente semelhantes. Num contexto competitivo, a incapacidade de comunicar claramente o que torna este candidato especificamente valioso pode resultar em preterição.

O generalismo excessivo em algumas áreas pode diluir a perceção de especialização. A tentativa de demonstrar versatilidade através de uma lista extensa de competências pode, paradoxalmente, enfraquecer o posicionamento como especialista numa área específica de elevado valor.

As consequências destes riscos na progressão de carreira incluem menor taxa de conversão em processos de recrutamento, ofertas salariais abaixo do potencial, e dificuldade em aceder a oportunidades de maior senioridade. A mitigação requer ações deliberadas de otimização do currículo e da estratégia de posicionamento.""",
        
        "identified_risks_signal": "Ausência de métricas, potencial subposicionamento, proposta de valor pouco distintiva.",
        "identified_risks_missing": "Incorporação sistemática de quantificação, articulação clara de diferenciação, ajuste de linguagem para refletir senioridade real."
    },
    
    "languages_analysis": {
        "detected_languages": [
            {
                "language": "Português",
                "level": "Nativo",
                "relevance": "Essencial para o mercado português",
                "recommendation": "Manter como língua principal de comunicação profissional"
            },
            {
                "language": "Inglês",
                "level": "Fluente",
                "relevance": "Crítico para contextos multinacionais e progressão internacional",
                "recommendation": "Considerar certificação formal (Cambridge, IELTS) para validação"
            },
            {
                "language": "Espanhol",
                "level": "Intermédio",
                "relevance": "Valorizado para mercado ibérico e latino-americano",
                "recommendation": "Investir em desenvolvimento para nível avançado"
            }
        ],
        "languages_assessment": """O perfil linguístico apresentado demonstra uma base sólida para atuação em contextos nacionais e internacionais, com oportunidades identificadas de desenvolvimento estratégico.

O domínio nativo do português constitui a base essencial para o mercado de trabalho português, onde a maioria das interações profissionais ocorre nesta língua. A fluência em inglês representa um ativo crítico para funções em organizações multinacionais ou com ambição de internacionalização, abrindo portas para oportunidades além do mercado doméstico.

O nível intermédio de espanhol, embora funcional, representa uma oportunidade de desenvolvimento com retorno potencialmente elevado. O mercado ibérico e as relações com a América Latina valorizam profissionais com competência em ambas as línguas peninsulares.

A recomendação estratégica passa pela obtenção de certificações formais que validem os níveis declarados, particularmente em inglês, onde certificações reconhecidas internacionalmente podem reforçar a credibilidade do perfil."""
    },
    
    "education_analysis": {
        "formal_education": [
            {
                "degree": "Mestrado",
                "institution": "Universidade de Lisboa",
                "field": "Gestão de Recursos Humanos",
                "relevance": "Diretamente alinhado com a área de atuação profissional"
            }
        ],
        "education_assessment": """A formação académica apresentada demonstra alinhamento adequado com a trajetória profissional e as funções alvo, constituindo uma base sólida que complementa a experiência prática acumulada.

O grau de Mestrado em Gestão de Recursos Humanos confere credibilidade académica ao perfil e evidencia investimento formal no desenvolvimento de competências na área de especialização. Este nível de formação é tipicamente esperado para funções de direção em RH, satisfazendo requisitos frequentemente presentes em descrições de funções equivalentes.

A instituição de ensino, quando reconhecida no mercado, adiciona valor à credencial académica. A reputação da universidade e do programa específico pode influenciar a perceção de qualidade da formação por parte de recrutadores.

As oportunidades de desenvolvimento identificadas incluem formação executiva complementar em áreas emergentes como People Analytics, Inteligência Artificial aplicada a RH, ou programas de liderança em escolas de negócios de referência. Estas credenciais adicionais podem reforçar o posicionamento para funções de maior senioridade."""
    },
    
    "priority_recommendations": {
        "immediate_adjustments": """As recomendações de ajuste imediato focam-se em intervenções de elevado impacto que podem ser implementadas rapidamente para melhorar significativamente a eficácia do currículo.

A primeira prioridade consiste na incorporação sistemática de métricas quantificáveis em todas as descrições de experiência profissional. Cada entrada deve incluir pelo menos um indicador numérico que demonstre impacto: percentagens de melhoria, valores monetários, dimensão de equipas ou projetos, prazos cumpridos, entre outros. Por exemplo, transformar 'liderou iniciativas de transformação digital' em 'liderou programa de transformação digital que reduziu tempo de processamento em 40% e gerou poupanças anuais de €200K'.

A segunda prioridade envolve a criação ou reformulação do sumário executivo para comunicar de forma impactante a proposta de valor única. Este elemento, posicionado no início do documento, deve sintetizar em 3-4 linhas quem é o candidato, qual o seu valor distintivo, e que tipo de contribuição pode oferecer. Deve ser específico, memorável e orientado para resultados.

A terceira prioridade relaciona-se com a otimização de keywords para compatibilidade ATS. A análise de descrições de funções alvo deve informar a incorporação de termos técnicos relevantes em posições estratégicas do documento, aumentando a probabilidade de correspondência em processos de triagem automatizada.

A quarta prioridade consiste na revisão da linguagem para garantir orientação consistente para resultados versus responsabilidades. Cada descrição de experiência deve responder à questão implícita: 'Qual foi o impacto mensurável da minha contribuição?'""",
        
        "refinement_areas": """As áreas de refinamento a médio prazo visam otimizações mais profundas que requerem reflexão e desenvolvimento adicional.

O desenvolvimento de uma narrativa profissional coerente e distintiva constitui uma área de refinamento prioritária. Esta narrativa deve conectar as diferentes experiências num fio condutor que evidencie progressão intencional e propósito claro. A história profissional deve comunicar não apenas o que o candidato fez, mas porque fez e como cada experiência contribuiu para o desenvolvimento de competências únicas.

A articulação explícita de competências de liderança estratégica representa outra área de refinamento relevante para aspirações a funções de maior senioridade. A transição de perfil de execução para perfil de liderança requer evidência de contribuição para decisões estratégicas, influência ao mais alto nível, e visão de negócio.

O reforço da presença digital, particularmente no LinkedIn, deve complementar e amplificar o currículo tradicional. A consistência entre documentos, a produção de conteúdo relevante, e o desenvolvimento de rede de contactos estratégicos constituem elementos de uma estratégia integrada de posicionamento profissional.""",
        
        "deep_repositioning": """O reposicionamento profundo envolve considerações estratégicas de maior alcance que podem requerer mudanças significativas na abordagem de carreira.

A questão fundamental a considerar relaciona-se com a clareza de objetivos de carreira a longo prazo. O currículo atual posiciona adequadamente o candidato para funções de direção intermédia em RH, mas a aspiração a posições de C-level ou direção executiva requer uma evolução deliberada do posicionamento.

A especialização versus generalização constitui uma decisão estratégica com implicações significativas. O mercado atual tende a valorizar especialistas com profundidade em áreas específicas de elevado valor, embora funções de direção geral requeiram também amplitude de competências. A definição clara do posicionamento desejado deve informar ajustes no currículo e na estratégia de desenvolvimento.

A consideração de credenciais adicionais de elevado prestígio, como MBA em escola de referência ou certificações executivas reconhecidas internacionalmente, pode constituir um investimento estratégico para acelerar a progressão para funções de maior senioridade. Esta decisão deve ser ponderada face aos objetivos específicos e contexto individual."""
    },
    
    "executive_conclusion": {
        "potential_after_improvements": """O potencial transformado do currículo após implementação das melhorias recomendadas é significativo e pode alterar materialmente os resultados em processos de recrutamento.

A incorporação sistemática de métricas quantificáveis transformará um documento descritivo num portfólio de evidências de impacto. Esta mudança fundamental na abordagem comunicativa posiciona o candidato como profissional orientado para resultados, característica altamente valorizada em funções de direção.

A articulação clara de uma proposta de valor distintiva permitirá diferenciação eficaz face a candidatos com perfis superficialmente semelhantes. Num mercado competitivo, a capacidade de comunicar rapidamente o que torna este candidato especificamente valioso constitui um fator crítico de sucesso.

A otimização para compatibilidade ATS aumentará significativamente a visibilidade em processos de recrutamento digital, garantindo que o currículo ultrapassa filtros automatizados e chega a revisão humana.

O resultado esperado é um documento que funciona como ferramenta estratégica de posicionamento profissional, comunicando valor de forma impactante tanto a algoritmos como a decisores humanos, e maximizando a probabilidade de conversão em oportunidades alinhadas com os objetivos de carreira.""",
        
        "expected_competitiveness": """O nível de competitividade esperado após implementação das recomendações posiciona o candidato favoravelmente para funções de direção em RH no mercado português e europeu.

A combinação de experiência sólida em organizações de referência, especialização em transformação digital, e um currículo otimizado para comunicar valor de forma eficaz, cria um perfil competitivo para a maioria das oportunidades no segmento alvo.

Em processos seletivos de alto nível, onde a concorrência inclui candidatos com perfis igualmente qualificados, os elementos de diferenciação articulados no currículo otimizado podem constituir fatores decisivos. A capacidade de demonstrar impacto através de métricas, comunicar uma proposta de valor clara, e apresentar uma narrativa profissional coerente, distingue candidatos de excelência.

A expectativa realista é de melhoria significativa na taxa de conversão de candidaturas em entrevistas, maior poder negocial em discussões salariais, e acesso a oportunidades de maior senioridade que anteriormente poderiam estar fora de alcance. O investimento na otimização do currículo constitui, nesta perspetiva, uma das ações de maior retorno para a progressão de carreira."""
    },
    
    "radar_data": {
        "estrutura": 14,
        "conteudo": 13,
        "ats": 12,
        "impacto": 11,
        "branding": 12,
        "riscos": 13
    },
    
    "pdf_extended_content": {
        "sector_analysis": {
            "identified_sector": "Recursos Humanos / Transformação Digital",
            "sector_trends": """O setor de Recursos Humanos atravessa uma fase de transformação acelerada impulsionada pela digitalização, mudanças nas expectativas dos colaboradores, e evolução dos modelos de trabalho. Em Portugal e na Europa, estas tendências manifestam-se de forma particularmente intensa, criando oportunidades e desafios para profissionais da área.

A transformação digital de RH constitui uma prioridade estratégica para a maioria das organizações. A implementação de sistemas integrados de gestão de pessoas, plataformas de employee experience, e ferramentas de analytics representa um investimento crescente. Profissionais com competências na interseção entre RH e tecnologia são cada vez mais procurados e valorizados.

O trabalho híbrido e remoto, acelerado pela pandemia, estabeleceu-se como modelo dominante em muitos setores. Esta realidade exige novas abordagens à gestão de pessoas, cultura organizacional, e engagement de colaboradores. Profissionais de RH com experiência na gestão desta transição possuem competências de elevado valor.

A ênfase crescente em diversidade, equidade e inclusão (DEI) cria novas áreas de especialização e responsabilidade dentro das funções de RH. Organizações enfrentam pressão de stakeholders para demonstrar progresso nestes domínios, gerando procura por profissionais com competências específicas.

As implicações para o perfil do candidato são globalmente positivas. A especialização em transformação digital alinha-se com uma das tendências mais relevantes do setor, posicionando-o favoravelmente para oportunidades em organizações que priorizam a modernização das suas práticas de gestão de pessoas.""",
            
            "competitive_landscape": """O panorama competitivo para funções de direção em RH no mercado português apresenta características específicas que informam a estratégia de posicionamento.

A oferta de profissionais qualificados para funções de direção em RH é relativamente limitada quando comparada com outras áreas funcionais. Esta escassez relativa cria condições favoráveis para candidatos com perfis sólidos, embora a competição para as posições mais atrativas permaneça intensa.

As organizações multinacionais presentes em Portugal constituem um segmento de mercado particularmente relevante para profissionais com experiência internacional e competências em transformação digital. Estas organizações oferecem tipicamente condições mais competitivas e oportunidades de desenvolvimento acelerado.

O setor de consultoria em RH representa uma alternativa ou complemento à carreira em organizações. Firmas de consultoria procuram profissionais com experiência operacional que possam traduzir conhecimento prático em serviços de valor para clientes.

A estratégia de candidatura recomendada passa pela identificação de organizações em fase de transformação digital de RH, onde as competências específicas do candidato respondem diretamente a necessidades identificadas. A abordagem proativa, através de networking e candidaturas direcionadas, tende a ser mais eficaz do que a resposta passiva a anúncios."""
        },
        
        "critical_certifications": [
            {
                "name": "PROSCI Change Management Certification",
                "issuer": "Prosci",
                "relevance": """A certificação PROSCI em Gestão da Mudança constitui uma credencial de elevado valor para profissionais envolvidos em iniciativas de transformação organizacional. No contexto de transformação digital de RH, onde a gestão eficaz da mudança determina frequentemente o sucesso ou fracasso de iniciativas, esta certificação demonstra competência metodológica reconhecida internacionalmente.

A metodologia PROSCI, baseada em investigação extensiva sobre fatores de sucesso em gestão da mudança, é amplamente adotada por organizações de referência. A certificação confere credibilidade e linguagem comum que facilita a colaboração com outros profissionais certificados e a aplicação de práticas comprovadas.

Para o perfil específico do candidato, esta certificação reforçaria a dimensão de gestão de mudança que complementa as competências técnicas em transformação digital, criando um posicionamento mais completo e diferenciado.""",
                "priority": "Alta",
                "estimated_investment": "€2,500-3,500 | 3 dias presenciais + preparação",
                "where_to_get": "Prosci Portugal ou formação online certificada"
            },
            {
                "name": "SHRM Senior Certified Professional (SHRM-SCP)",
                "issuer": "Society for Human Resource Management",
                "relevance": """A certificação SHRM-SCP representa o standard de excelência em gestão de recursos humanos reconhecido globalmente. Para profissionais com aspirações a funções de direção executiva em RH, esta credencial demonstra domínio de competências estratégicas e operacionais validadas por uma das organizações mais prestigiadas do setor.

A certificação abrange domínios críticos como liderança, estratégia de negócio, e gestão de pessoas, alinhando-se com as exigências de funções de direção. O processo de certificação, que inclui exame rigoroso e requisitos de experiência, confere credibilidade significativa.

No mercado português, onde esta certificação é menos comum do que em mercados anglo-saxónicos, a sua posse pode constituir um fator de diferenciação relevante, particularmente para oportunidades em organizações multinacionais ou com ambição internacional.""",
                "priority": "Média",
                "estimated_investment": "€400-600 (exame) + preparação | 3-6 meses de estudo",
                "where_to_get": "SHRM online - exame em centros Prometric"
            },
            {
                "name": "People Analytics Certificate",
                "issuer": "Wharton Online / AIHR",
                "relevance": """A certificação em People Analytics responde a uma das tendências mais relevantes na evolução da função de RH. A capacidade de utilizar dados para informar decisões de gestão de pessoas constitui uma competência cada vez mais valorizada, particularmente em organizações que priorizam abordagens baseadas em evidência.

Para um perfil focado em transformação digital de RH, competências em analytics complementam e amplificam o valor das competências técnicas existentes. A capacidade de extrair insights de dados de pessoas e traduzi-los em recomendações acionáveis diferencia profissionais de RH tradicionais de líderes da função do futuro.

Esta certificação posiciona o candidato na vanguarda da evolução da profissão, demonstrando compromisso com o desenvolvimento contínuo e alinhamento com as exigências emergentes do mercado.""",
                "priority": "Alta",
                "estimated_investment": "€1,500-2,500 | 2-4 meses online",
                "where_to_get": "Wharton Online, AIHR, ou Coursera"
            }
        ],
        
        "phrase_improvements": [
            {
                "original": "Responsável pela gestão de processos de RH e implementação de melhorias",
                "problem": """Esta frase exemplifica uma abordagem descritiva focada em responsabilidades que não comunica valor ou impacto. A utilização de 'responsável por' é uma construção passiva que não evidencia ação ou resultado. 'Gestão de processos' e 'implementação de melhorias' são termos genéricos que poderiam aplicar-se a qualquer profissional da área, não diferenciando o candidato.""",
                "improved": "Redesenhei 12 processos core de RH, reduzindo tempo de ciclo em 35% e eliminando €180K em custos operacionais anuais através de automação e otimização de workflows",
                "explanation": """A versão melhorada transforma uma descrição genérica numa afirmação de impacto quantificável. A utilização de verbo de ação forte ('redesenhei'), números específicos ('12 processos', '35%', '€180K'), e resultados concretos ('reduzindo', 'eliminando') comunica valor de forma imediata e memorável. Esta construção responde às expectativas de recrutadores que procuram evidência de capacidade de entrega."""
            },
            {
                "original": "Liderança de equipa e gestão de stakeholders em projetos de transformação",
                "problem": """A frase apresenta competências relevantes mas de forma vaga e não diferenciadora. 'Liderança de equipa' e 'gestão de stakeholders' são expectativas básicas para funções de gestão, não constituindo fatores de distinção. A ausência de contexto específico ou resultados torna a afirmação pouco memorável.""",
                "improved": "Liderei equipa multidisciplinar de 8 elementos e coordenei 15+ stakeholders C-level na implementação de HRIS que serviu 5.000 colaboradores em 6 países, entregue 2 meses antes do prazo e 15% abaixo do orçamento",
                "explanation": """A reformulação adiciona dimensão ('8 elementos', '15+ stakeholders', '5.000 colaboradores', '6 países'), nível de senioridade dos stakeholders ('C-level'), e métricas de sucesso ('2 meses antes', '15% abaixo'). Esta densidade de informação específica demonstra escala de responsabilidade e capacidade de entrega em contextos complexos."""
            },
            {
                "original": "Experiência em transformação digital e otimização de processos de RH",
                "problem": """Esta construção é uma etiqueta genérica que não comunica profundidade ou especificidade. 'Experiência em' é uma formulação fraca que não demonstra nível de competência ou resultados. Muitos candidatos poderiam fazer afirmações semelhantes, tornando-a não diferenciadora.""",
                "improved": "Arquitetei e executei roadmap de transformação digital de RH em 3 fases, digitalizando 100% dos processos administrativos, implementando self-service para 3.000 colaboradores, e aumentando NPS interno de 45 para 78 pontos",
                "explanation": """A versão otimizada demonstra liderança estratégica ('arquitetei'), execução ('executei'), escala ('3.000 colaboradores'), e impacto mensurável ('NPS de 45 para 78'). A estrutura em fases sugere abordagem metodológica, enquanto os resultados específicos evidenciam capacidade de transformar visão em realidade."""
            }
        ],
        
        "cv_design_tips": {
            "layout": "Utilizar layout de coluna única para máxima compatibilidade ATS. Hierarquia visual clara com títulos em negrito e espaçamento consistente entre secções. Margens de 2-2.5cm para equilíbrio visual.",
            "typography": "Fonte sans-serif profissional (Calibri, Arial, Helvetica) em 10-11pt para corpo de texto. Títulos em 12-14pt. Evitar mais de 2 tipos de fonte no documento.",
            "spacing": "Espaçamento entre linhas de 1.15-1.3 para legibilidade. Espaço adicional entre secções (12-18pt) para separação visual clara. Evitar páginas com excesso de espaço em branco.",
            "sections_order": "1) Contactos, 2) Sumário Executivo, 3) Experiência Profissional, 4) Competências-Chave, 5) Formação Académica, 6) Certificações, 7) Idiomas. Priorizar experiência sobre formação para perfis sénior.",
            "length": "2 páginas ideais para perfil com 10+ anos de experiência. Máximo 3 páginas se justificado por extensão de experiência relevante. Cada página deve conter informação de valor.",
            "visual_elements": "Evitar gráficos, tabelas complexas, ou elementos visuais que dificultem parsing ATS. Usar bullet points para listas. Cor limitada a preto e um tom de destaque (azul escuro ou cinza)."
        },
        
        "writing_guide": {
            "power_verbs": "Liderei, Implementei, Otimizei, Transformei, Desenvolvi, Negociei, Estabeleci, Redesenhei, Acelerai, Entreguei, Reduzi, Aumentei, Gerei, Influenciei, Mobilizei, Arquitetei, Escalei, Consolidei, Pioneirei, Orquestrei",
            "keywords_to_add": "Transformação Digital, People Analytics, Employee Experience, Change Management, HRIS, Talent Management, Workforce Planning, HR Business Partner, Organizational Development, Performance Management, Succession Planning, Employer Branding, HR Metrics, Agile HR, Digital HR",
            "phrases_to_avoid": "Responsável por (usar verbos de ação), Ajudei a (assumir ownership), Participei em (especificar contribuição), Trabalhei com (definir papel), Fui envolvido em (demonstrar liderança)",
            "quantification_tips": "Incluir sempre: dimensão (equipa, orçamento, utilizadores), tempo (prazo, duração, frequência), impacto (%, €, pontos), comparação (antes/depois, benchmark). Transformar responsabilidades em conquistas mensuráveis."
        },
        
        "professional_development": {
            "short_term": "0-12 meses: Obter certificação PROSCI, completar curso de People Analytics, atualizar perfil LinkedIn com novo posicionamento, estabelecer rotina de produção de conteúdo profissional.",
            "medium_term": "1-3 anos: Assumir função de direção com P&L responsibility, desenvolver track record de transformação em nova organização, construir rede de contactos C-level, considerar MBA executivo.",
            "long_term": "3-5 anos: Posicionar para função de CHRO ou VP HR em organização de referência, desenvolver presença como thought leader na área, considerar advisory boards ou non-executive roles."
        },
        
        "networking_strategy": {
            "linkedin_optimization": "Headline focado em proposta de valor (não apenas título), sumário orientado para resultados, secção de destaques com conquistas principais, recomendações de stakeholders sénior, atividade regular com conteúdo relevante.",
            "key_communities": "APG (Associação Portuguesa de Gestão de Pessoas), HR Portugal, SHRM Portugal Chapter, grupos LinkedIn de HR Digital, comunidades de People Analytics.",
            "events_to_attend": "HR Portugal Summit, Web Summit (track de HR Tech), eventos APG, conferências de fornecedores de HRIS (Workday, SAP), meetups de People Analytics.",
            "thought_leadership": "Publicar artigos no LinkedIn sobre transformação digital de RH, participar como speaker em eventos do setor, contribuir para publicações especializadas, desenvolver case studies de iniciativas lideradas."
        },
        
        "salary_positioning": {
            "market_range": "Funções de Direção de RH em Portugal: €80.000-120.000 base anual para organizações de média dimensão, €100.000-150.000+ para multinacionais ou grandes grupos. Variável adicional de 15-30%.",
            "negotiation_leverage": "Experiência em transformação digital (competência escassa), track record em multinacionais de referência, combinação de competências técnicas e de liderança, certificações relevantes.",
            "gaps_to_address": "Quantificação de impacto financeiro das iniciativas lideradas, evidência de contribuição para resultados de negócio (não apenas RH), demonstração de influência ao nível executivo."
        }
    }
}

def main():
    print("=" * 60)
    print("TESTE DO GERADOR DE RELATÓRIOS PDF v2")
    print("=" * 60)
    
    # Criar instância do gerador
    generator = ReportPDFGenerator()
    
    # Gerar PDF
    print("\n[INFO] Gerando PDF de teste...")
    try:
        pdf_buffer, filename = generator.create_pdf(test_analysis_data)
        
        # Guardar ficheiro
        output_path = f"/home/ubuntu/{filename}"
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.read())
        
        print(f"\n[SUCESSO] PDF gerado: {output_path}")
        print(f"[INFO] Tamanho: {pdf_buffer.seek(0, 2)} bytes")
        
    except Exception as e:
        print(f"\n[ERRO] Falha na geração: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
