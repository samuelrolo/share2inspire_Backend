# Changelog - Share2Inspire CV Analyzer v6.0

## Visão Geral das Melhorias

Esta versão representa uma reformulação completa do sistema de geração de relatórios de análise de CV, com foco em design sofisticado, análises aprofundadas e valor acrescentado para o cliente.

---

## Ficheiros Modificados/Criados

### 1. `utils/report_pdf_v2.py` (Novo)
Gerador de relatórios PDF completamente redesenhado.

### 2. `utils/analysis_v2.py` (Novo)
Analisador de CV com prompts melhorados para a API Gemini.

---

## Melhorias de Design e Layout

### Paleta de Cores
- **Preto** (#1A1A1A) - Títulos e texto principal
- **Dourado** (#BF9A33) - Acentos, destaques e elementos de marca
- **Branco** (#FFFFFF) - Fundos
- **Cinza** (#6c757d, #e9ecef, #f8f9fa) - Textos secundários e fundos subtis

### Tipografia
- Fonte principal: Helvetica/Arial (sans-serif)
- Hierarquia clara: H1 (24pt), H2 (14pt), H3 (11pt), corpo (10pt)
- Estilo minimalista sem sombras ou reflexos pesados

### Scorecards Circulares (SVG)
- Score global central com anel de progresso
- 6 mini-scorecards para dimensões individuais
- Cores dinâmicas baseadas na pontuação:
  - Verde (≥75): Excelente
  - Dourado (50-74): Bom
  - Laranja (25-49): Necessita atenção
  - Vermelho (<25): Crítico

### Gráfico de Barras Horizontais
- Visualização clara das 6 dimensões de análise
- Barras com preenchimento dourado sobre fundo cinza
- Labels à esquerda, scores à direita

### Estrutura de Páginas
1. **Capa** - Design limpo com título, nome do candidato e data
2. **Visão Geral** - Perfil do candidato + scorecards
3. **Sumário Executivo** - Posicionamento e fatores de decisão
4. **Análise Dimensional** - Gráfico + análise detalhada por dimensão
5. **Diagnóstico de Impacto** - Leitura 30 segundos, forças e diluições
6. **Análise ATS** - Compatibilidade, riscos e alinhamento
7. **Melhorias de Frases** - Antes/Depois com justificação
8. **Análise de Mercado** - Tendências e panorama competitivo
9. **Certificações** - Recomendações com prioridade e investimento
10. **Recomendações** - Imediatas, refinamento e reposicionamento
11. **Conclusão** - Potencial e competitividade esperada
12. **Serviços** - Cross-sell de outros serviços Share2Inspire

### Cabeçalho e Rodapé
- Cabeçalho: Nome do candidato + data (alinhado à direita)
- Rodapé: Identificação do relatório + confidencialidade

---

## Melhorias na Profundidade das Análises

### Dimensões de Análise (6 eixos)
1. **Estrutura e Clareza** (0-100)
2. **Conteúdo e Relevância** (0-100)
3. **Compatibilidade ATS** (0-100)
4. **Impacto e Resultados** (0-100)
5. **Marca Pessoal e Proposta de Valor** (0-100)
6. **Riscos e Inconsistências** (0-100)

### Requisitos de Densidade Textual
- Cada campo de análise: 300-500 palavras obrigatórias
- Parágrafos densos com 5-7 frases mínimas
- Proibidas respostas curtas, listas simples ou etiquetas genéricas

### Conteúdo Estendido para PDF
- **Análise de Setor**: Tendências e panorama competitivo
- **Certificações Críticas**: 3-5 recomendações com justificação
- **Melhorias de Frases**: Exemplos reais do CV com versões otimizadas
- **Guia de Escrita**: Verbos de ação, keywords ATS, frases a evitar
- **Desenvolvimento Profissional**: Curto, médio e longo prazo
- **Estratégia de Networking**: LinkedIn, comunidades, eventos
- **Posicionamento Salarial**: Intervalos de mercado e alavancas

### Palavras Proibidas no Prompt
- "Consultoria", "Projeto", "Implementação", "Formação"
- "Metodologia proprietária", "Framework exclusivo"

### Substituições Recomendadas
- "Acompanhamento", "Decisão", "Posicionamento"
- "Clareza estratégica", "Conhecimento aplicável"
- "Iniciativa", "Desenvolvimento", "Capacitação"

---

## Campos Obrigatórios de Análise

### Perfil do Candidato
- Nome detectado
- Função atual
- Setor identificado
- Anos de experiência
- Senioridade
- Nível de formação
- Idiomas
- Competências-chave

### Sumário Executivo
- Score global (0-100)
- Posicionamento de mercado (300-500 palavras)
- Fatores-chave de decisão (300-500 palavras)

### Diagnóstico de Impacto
- Leitura em 30 segundos
- Pontos fortes de impacto
- Pontos de diluição

### Análise ATS
- Compatibilidade
- Riscos de filtragem
- Alinhamento com práticas de recrutamento

### Diferenciação
- Análise técnica e comportamental
- Fatores de diferenciação
- Competências comuns/indiferenciadas

### Riscos Estratégicos
- Identificação de riscos
- Sinais de alerta
- Ações de mitigação

### Idiomas e Formação
- Lista de idiomas com níveis
- Avaliação do perfil linguístico
- Formação académica e relevância

### Recomendações
- Ajustes imediatos
- Áreas de refinamento
- Reposicionamento profundo

### Conclusão
- Potencial após melhorias
- Competitividade esperada

---

## Instruções de Integração

### Substituir ficheiros existentes:
```bash
cp utils/report_pdf_v2.py utils/report_pdf.py
cp utils/analysis_v2.py utils/analysis.py
```

### Ou importar as novas versões:
```python
from utils.report_pdf_v2 import ReportPDFGenerator, generate_cv_report
from utils.analysis_v2 import CVAnalyzer, analyze_cv
```

---

## Dependências
- xhtml2pdf
- jinja2
- PyPDF2
- google-generativeai

---

## Autor
Share2Inspire - Human Centred Career & Knowledge Platform

## Data
Janeiro 2026
