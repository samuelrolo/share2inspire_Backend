# Campos Necessários para o PDF de Análise de CV

## 1. candidate_profile (Perfil do Candidato)
- `detected_name` - Nome do candidato
- `total_years_exp` - Anos de experiência (ex: "5-7 anos")
- `detected_role` - Função atual/detectada
- `seniority` - Nível de senioridade (ex: "Pleno", "Sénior")
- `detected_sector` - Setor principal
- `education_level` - Nível de formação académica
- `key_skills` - Lista de competências-chave

## 2. global_summary (Resumo Global)
- `strengths` - Lista de pontos fortes (array de strings)
- `improvements` - Lista de oportunidades de melhoria (array de strings)

## 3. executive_summary (Sumário Executivo)
- `global_score` - Score global (0-100)
- `global_score_breakdown` - Breakdown dos scores:
  - `structure_clarity` - Estrutura e clareza
  - `content_relevance` - Conteúdo e relevância
  - `risks_inconsistencies` - Riscos/inconsistências
  - `ats_compatibility` - Compatibilidade ATS
  - `impact_results` - Impacto e resultados
  - `personal_brand` - Marca pessoal
- `market_positioning` - Texto sobre posicionamento de mercado
- `key_decision_factors` - Texto sobre fatores-chave de decisão

## 4. diagnostic_impact (Diagnóstico de Impacto)
- `first_30_seconds_read` - O que um recrutador vê em 30 segundos
- `impact_strengths` - Pontos fortes de impacto
- `impact_dilutions` - Pontos de diluição de impacto

## 5. content_structure_analysis (Análise de Estrutura e Conteúdo)
- `organization_hierarchy` - Análise da organização e hierarquia
- `responsibilities_results_balance` - Equilíbrio entre responsabilidades e resultados
- `orientation` - Orientação geral do CV

## 6. ats_digital_recruitment (ATS e Recrutamento Digital)
- `compatibility` - Compatibilidade com sistemas ATS
- `filtering_risks` - Riscos de filtragem automática
- `alignment` - Alinhamento com práticas de recrutamento

## 7. skills_differentiation (Diferenciação de Competências)
- `technical_behavioral_analysis` - Análise técnica vs comportamental
- `differentiation_factors` - Fatores de diferenciação
- `common_undifferentiated` - Competências comuns/não diferenciadas

## 8. strategic_risks (Riscos Estratégicos)
- `identified_risks` - Riscos identificados

## 9. languages_analysis (Análise de Idiomas)
- `languages_assessment` - Avaliação de idiomas

## 10. education_analysis (Análise de Formação)
- `education_assessment` - Avaliação da formação

## 11. phrase_improvements (Melhorias de Frases)
Array de objetos com:
- `category` - Categoria da melhoria
- `before` - Texto original
- `after` - Texto melhorado
- `justification` - Justificação da melhoria

## 12. pdf_extended_content (Conteúdo Estendido)
### sector_analysis
- `identified_sector` - Setor identificado
- `sector_trends` - Tendências do setor
- `competitive_landscape` - Panorama competitivo

### critical_certifications
Array de objetos com:
- `name` - Nome da certificação
- `issuer` - Entidade emissora
- `priority` - Prioridade (Alta, Média, Baixa)
- `estimated_investment` - Investimento estimado
- `relevance` - Relevância para a carreira

## 13. priority_recommendations (Recomendações Prioritárias)
- `immediate_adjustments` - Ajustes imediatos
- `refinement_areas` - Áreas de refinamento
- `deep_repositioning` - Reposicionamento profundo

## 14. executive_conclusion (Conclusão Executiva)
- `potential_after_improvements` - Potencial após melhorias
- `expected_competitiveness` - Competitividade esperada

## 15. radar_data (Dados para Gráficos)
- `estrutura` - Score de estrutura (0-20, multiplicado por 5 para 0-100)
- `conteudo` - Score de conteúdo
- `riscos` - Score de riscos/consistência
- `ats` - Score ATS
- `impacto` - Score de impacto
- `branding` - Score de marca pessoal

## 16. market_analysis (Análise de Mercado) - usado em _process_analysis_for_bullets
- `sector_trends` - Tendências do setor
- `competitive_landscape` - Panorama competitivo
- `opportunities_threats` - Oportunidades e ameaças

## 17. final_conclusion (Conclusão Final) - usado em _process_analysis_for_bullets
- `executive_synthesis` - Síntese executiva
- `next_steps` - Próximos passos

---

**NOTA IMPORTANTE:** Os scores em `radar_data` são multiplicados por 5 no código do PDF (linha 756, 796-801), portanto devem ser fornecidos na escala 0-20 para resultar em 0-100.
