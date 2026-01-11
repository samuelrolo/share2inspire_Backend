# -*- coding: utf-8 -*-
"""
Gerador de Relatório PDF Premium para Análise de CV
Share2Inspire - Versão 6.0 
Design Sofisticado e Minimalista com Scorecards Circulares
"""

import io
import math
import datetime
import base64
from xhtml2pdf import pisa
from jinja2 import Template

class ReportPDFGenerator:
    """Gerador de relatórios PDF com design premium e análises aprofundadas."""
    
    def __init__(self):
        self.colors = {
            'gold': '#BF9A33',
            'gold_light': '#D4B35A',
            'black': '#1A1A1A',
            'gray_dark': '#333333',
            'gray_medium': '#6c757d',
            'gray_light': '#e9ecef',
            'gray_bg': '#f8f9fa',
            'white': '#FFFFFF',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c'
        }

    def _get_template(self):
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: 1.5cm;
        }
        
        body {
            font-family: Helvetica, Arial, sans-serif;
            color: #333333;
            line-height: 1.5;
            font-size: 10pt;
        }
        
        h1 { font-size: 24pt; font-weight: bold; color: #1A1A1A; margin: 0 0 10pt 0; }
        h2 { font-size: 14pt; font-weight: bold; color: #1A1A1A; margin: 20pt 0 10pt 0; border-left: 3pt solid #BF9A33; padding-left: 10pt; }
        h3 { font-size: 11pt; font-weight: bold; color: #BF9A33; margin: 15pt 0 6pt 0; }
        h4 { font-size: 10pt; font-weight: bold; color: #1A1A1A; margin: 10pt 0 4pt 0; }
        
        p { margin: 0 0 8pt 0; text-align: justify; }
        
        .text-gold { color: #BF9A33; }
        .text-muted { color: #6c757d; }
        .text-center { text-align: center; }
        .text-small { font-size: 9pt; }
        
        .page-break { page-break-before: always; }
        
        /* Capa */
        .cover { text-align: center; padding-top: 100pt; }
        .cover-subtitle { font-size: 11pt; color: #BF9A33; letter-spacing: 2pt; margin-bottom: 40pt; }
        .cover-title { font-size: 28pt; font-weight: bold; color: #1A1A1A; margin-bottom: 20pt; }
        .cover-candidate { font-size: 16pt; font-weight: bold; color: #333333; margin-bottom: 10pt; }
        .cover-id { font-size: 9pt; color: #6c757d; margin-bottom: 60pt; }
        .cover-date { font-size: 10pt; color: #6c757d; }
        .cover-tagline { font-size: 10pt; color: #BF9A33; margin-top: 5pt; }
        
        /* Header */
        .page-header { border-bottom: 1pt solid #e9ecef; padding-bottom: 8pt; margin-bottom: 15pt; }
        .header-text { font-size: 8pt; color: #adb5bd; text-align: right; }
        
        /* Profile Grid */
        .profile-table { width: 100%; border-collapse: collapse; margin: 15pt 0; }
        .profile-table td { padding: 10pt; border: 1pt solid #e9ecef; vertical-align: top; }
        .profile-label { font-size: 8pt; color: #BF9A33; text-transform: uppercase; margin-bottom: 3pt; }
        .profile-value { font-size: 11pt; font-weight: bold; color: #1A1A1A; }
        
        /* Scorecard */
        .scorecard-container { text-align: center; margin: 20pt 0; }
        .mini-scorecard-row { text-align: center; margin: 15pt 0; }
        .mini-scorecard { display: inline-block; width: 80pt; text-align: center; margin: 0 5pt; }
        .scorecard-label { font-size: 8pt; color: #6c757d; text-transform: uppercase; margin-top: 5pt; }
        
        /* Dimension Item */
        .dimension-item { margin-bottom: 15pt; padding-left: 10pt; border-left: 2pt solid #e9ecef; }
        .dimension-header { margin-bottom: 5pt; }
        .dimension-title { font-size: 11pt; font-weight: bold; color: #1A1A1A; }
        .dimension-score { font-size: 12pt; font-weight: bold; color: #BF9A33; float: right; }
        .dimension-bar { height: 6pt; background: #e9ecef; margin: 8pt 0; }
        .dimension-bar-fill { height: 6pt; background: #BF9A33; }
        .dimension-analysis { font-size: 9.5pt; color: #495057; }
        .dimension-focus { font-size: 9pt; color: #6c757d; margin-top: 6pt; padding: 8pt; background: #f8f9fa; border-left: 2pt solid #BF9A33; }
        
        /* Before/After */
        .before-after { margin: 12pt 0; padding: 12pt; background: #f8f9fa; border-left: 3pt solid #BF9A33; }
        .ba-label { font-size: 8pt; font-weight: bold; text-transform: uppercase; margin-bottom: 4pt; }
        .ba-before { color: #e74c3c; }
        .ba-after { color: #27ae60; }
        .ba-text { font-style: italic; color: #495057; font-size: 10pt; margin-bottom: 8pt; padding: 6pt; background: #FFFFFF; border: 1pt solid #e9ecef; }
        
        /* Certification */
        .cert-item { margin-bottom: 12pt; padding: 10pt; border: 1pt solid #e9ecef; }
        .cert-name { font-size: 11pt; font-weight: bold; color: #1A1A1A; }
        .cert-priority { font-size: 9pt; font-weight: bold; float: right; }
        .cert-issuer { font-size: 9pt; color: #BF9A33; margin: 4pt 0; }
        .cert-relevance { font-size: 9.5pt; color: #495057; }
        .priority-alta { color: #e74c3c; }
        .priority-media { color: #f39c12; }
        .priority-baixa { color: #27ae60; }
        
        /* Recommendation */
        .recommendation-item { margin-bottom: 12pt; padding: 10pt; background: #f8f9fa; border-left: 3pt solid #BF9A33; }
        .recommendation-priority { font-size: 8pt; font-weight: bold; text-transform: uppercase; margin-bottom: 4pt; }
        
        /* Services */
        .services-table { width: 100%; border-collapse: collapse; margin: 15pt 0; }
        .services-table td { width: 33%; padding: 12pt; text-align: center; vertical-align: top; border: 1pt solid #e9ecef; }
        .service-icon { font-size: 20pt; color: #BF9A33; margin-bottom: 8pt; }
        .service-title { font-size: 11pt; font-weight: bold; color: #1A1A1A; margin-bottom: 6pt; }
        .service-desc { font-size: 9pt; color: #6c757d; }
        .service-link { font-size: 9pt; color: #BF9A33; font-weight: bold; margin-top: 8pt; }
        
        /* Footer */
        .page-footer { font-size: 8pt; color: #adb5bd; text-align: center; border-top: 1pt solid #e9ecef; padding-top: 10pt; margin-top: 20pt; }
        
        /* Clear float */
        .clearfix { clear: both; }
        
        /* Analysis Lists */
        .analysis-list { margin: 8pt 0; padding-left: 0; }
        .analysis-list li { margin-bottom: 6pt; font-size: 9.5pt; color: #495057; list-style-type: none; padding-left: 15pt; position: relative; }
        .analysis-list li:before { content: "●"; color: #BF9A33; font-size: 8pt; position: absolute; left: 0; top: 2pt; }
        .insight-key { font-weight: bold; color: #1A1A1A; }
        .insight-highlight { background: #FFF9E6; padding: 1pt 4pt; }
        
        /* No items message */
        .no-items { font-style: italic; color: #6c757d; padding: 10pt; background: #f8f9fa; text-align: center; }
    </style>
</head>
<body>

<!-- CAPA -->
<div style="text-align: center; padding-top: 200pt; page-break-after: always;">
    <div style="font-size: 11pt; color: #BF9A33; letter-spacing: 2pt; margin-bottom: 60pt;">POSICIONAMENTO DE CARREIRA</div>
    <div style="font-size: 28pt; font-weight: bold; color: #1A1A1A; margin-bottom: 40pt;">RELATÓRIO DE ANÁLISE DE CV</div>
    <div style="font-size: 16pt; font-weight: bold; color: #333333; margin-bottom: 20pt;">{{ candidate_name }}</div>
    <div style="font-size: 9pt; color: #6c757d; margin-bottom: 100pt;">ID: {{ report_id }}</div>
    <div style="font-size: 10pt; color: #6c757d;">Gerado em: {{ date_formatted }}</div>
    <div style="font-size: 10pt; color: #BF9A33; margin-top: 8pt;">Human Centred Career & Knowledge Platform</div>
    <div style="font-size: 8pt; color: #adb5bd; margin-top: 40pt;">Relatório de Análise de CV - Share2Inspire | Privado e Confidencial</div>
</div>

<!-- PÁGINA 2: VISÃO GERAL -->

<div class="page-header">
    <div class="header-text">{{ candidate_name }} | {{ date_formatted }}</div>
</div>

<h2>Visão Geral e Maturidade</h2>

<table class="profile-table">
    <tr>
        <td style="width: 50%;">
            <div class="profile-label">Candidato</div>
            <div class="profile-value">{{ candidate_name }}</div>
        </td>
        <td style="width: 50%;">
            <div class="profile-label">Anos de Experiência</div>
            <div class="profile-value">{{ analysis.candidate_profile.total_years_exp | default('N/D') }}</div>
        </td>
    </tr>
    <tr>
        <td>
            <div class="profile-label">Função Atual</div>
            <div class="profile-value">{{ analysis.candidate_profile.detected_role | default('N/D') }}</div>
        </td>
        <td>
            <div class="profile-label">Senioridade</div>
            <div class="profile-value">{{ analysis.candidate_profile.seniority | default('N/D') }}</div>
        </td>
    </tr>
    <tr>
        <td>
            <div class="profile-label">Setor Principal</div>
            <div class="profile-value">{{ analysis.candidate_profile.detected_sector | default('N/D') }}</div>
        </td>
        <td>
            <div class="profile-label">Formação Académica</div>
            <div class="profile-value">{{ analysis.candidate_profile.education_level | default('N/D') }}</div>
        </td>
    </tr>
</table>

<!-- SCORECARD PRINCIPAL -->
<div class="scorecard-container">
    <img src="{{ main_scorecard }}" width="180" alt="Score Global">
</div>

<!-- SCORECARDS DIMENSIONAIS -->
<table style="width: 100%; margin: 15pt 0;">
    <tr>
        <td style="width: 16.66%; text-align: center; vertical-align: top;">
            <img src="{{ scorecard_estrutura }}" width="60" alt="Estrutura">
            <div class="scorecard-label">Estrutura</div>
            <div style="font-size: 7pt; color: #6c757d; margin-top: 2pt;">Organização e clareza visual</div>
        </td>
        <td style="width: 16.66%; text-align: center; vertical-align: top;">
            <img src="{{ scorecard_conteudo }}" width="60" alt="Conteúdo">
            <div class="scorecard-label">Conteúdo</div>
            <div style="font-size: 7pt; color: #6c757d; margin-top: 2pt;">Relevância e profundidade</div>
        </td>
        <td style="width: 16.66%; text-align: center; vertical-align: top;">
            <img src="{{ scorecard_consistencia }}" width="60" alt="Consistência">
            <div class="scorecard-label">Consistência</div>
            <div style="font-size: 7pt; color: #6c757d; margin-top: 2pt;">Coerência e ausência de lacunas</div>
        </td>
        <td style="width: 16.66%; text-align: center; vertical-align: top;">
            <img src="{{ scorecard_ats }}" width="60" alt="ATS">
            <div class="scorecard-label">ATS</div>
            <div style="font-size: 7pt; color: #6c757d; margin-top: 2pt;">Compatibilidade com sistemas</div>
        </td>
        <td style="width: 16.66%; text-align: center; vertical-align: top;">
            <img src="{{ scorecard_impacto }}" width="60" alt="Impacto">
            <div class="scorecard-label">Impacto</div>
            <div style="font-size: 7pt; color: #6c757d; margin-top: 2pt;">Resultados e métricas</div>
        </td>
        <td style="width: 16.66%; text-align: center; vertical-align: top;">
            <img src="{{ scorecard_branding }}" width="60" alt="Branding">
            <div class="scorecard-label">Branding</div>
            <div style="font-size: 7pt; color: #6c757d; margin-top: 2pt;">Marca pessoal e diferenciação</div>
        </td>
    </tr>
</table>

<!-- PÁGINA 3: SUMÁRIO EXECUTIVO -->
<div class="page-break"></div>

<div class="page-header">
    <div class="header-text">{{ candidate_name }} | {{ date_formatted }}</div>
</div>

<h2>Sumário Executivo Estratégico</h2>

<h3>Posicionamento de Mercado</h3>
<p>{{ analysis.executive_summary.market_positioning | default('Análise não disponível.') }}</p>

<h3>Fatores-Chave de Decisão</h3>
<p>{{ analysis.executive_summary.key_decision_factors | default('Análise não disponível.') }}</p>

<!-- PÁGINA 4: ANÁLISE DIMENSIONAL -->
<div class="page-break"></div>

<div class="page-header">
    <div class="header-text">{{ candidate_name }} | {{ date_formatted }}</div>
</div>

<h2>Análise Dimensional Detalhada</h2>

<!-- Gráfico de Barras -->
<div style="text-align: center; margin: 15pt 0;">
    <img src="{{ bar_chart }}" width="480" alt="Análise Dimensional">
</div>

<!-- Estrutura -->
<div class="dimension-item">
    <div class="dimension-header">
        <span class="dimension-score">{{ scores.estrutura }}/100</span>
        <span class="dimension-title">Estrutura e Clareza</span>
        <div class="clearfix"></div>
    </div>
    <div class="dimension-bar">
        <div class="dimension-bar-fill" style="width: {{ scores.estrutura }}%;"></div>
    </div>
    <p class="dimension-analysis">{{ analysis.content_structure_analysis.organization_hierarchy | default('Análise não disponível.') | truncate(500) }}</p>
    {% if analysis.content_structure_analysis.organization_hierarchy_missing %}
    <div class="dimension-focus">
        <strong class="text-gold">Foco de Melhoria:</strong> {{ analysis.content_structure_analysis.organization_hierarchy_missing | truncate(200) }}
    </div>
    {% endif %}
</div>

<!-- Conteúdo -->
<div class="dimension-item">
    <div class="dimension-header">
        <span class="dimension-score">{{ scores.conteudo }}/100</span>
        <span class="dimension-title">Conteúdo e Relevância</span>
        <div class="clearfix"></div>
    </div>
    <div class="dimension-bar">
        <div class="dimension-bar-fill" style="width: {{ scores.conteudo }}%;"></div>
    </div>
    <p class="dimension-analysis">{{ analysis.content_structure_analysis.responsibilities_results_balance | default('Análise não disponível.') | truncate(500) }}</p>
</div>

<!-- ATS -->
<div class="dimension-item">
    <div class="dimension-header">
        <span class="dimension-score">{{ scores.ats }}/100</span>
        <span class="dimension-title">Compatibilidade ATS</span>
        <div class="clearfix"></div>
    </div>
    <div class="dimension-bar">
        <div class="dimension-bar-fill" style="width: {{ scores.ats }}%;"></div>
    </div>
    <p class="dimension-analysis">{{ analysis.ats_digital_recruitment.compatibility | default('Análise não disponível.') | truncate(500) }}</p>
</div>

<!-- PÁGINA 5: ANÁLISE DIMENSIONAL (CONT.) -->
<div class="page-break"></div>

<div class="page-header">
    <div class="header-text">{{ candidate_name }} | {{ date_formatted }}</div>
</div>

<h2>Análise Dimensional (Continuação)</h2>

<!-- Impacto -->
<div class="dimension-item">
    <div class="dimension-header">
        <span class="dimension-score">{{ scores.impacto }}/100</span>
        <span class="dimension-title">Impacto e Resultados</span>
        <div class="clearfix"></div>
    </div>
    <div class="dimension-bar">
        <div class="dimension-bar-fill" style="width: {{ scores.impacto }}%;"></div>
    </div>
    <p class="dimension-analysis">{{ analysis.diagnostic_impact.impact_strengths | default('Análise não disponível.') | truncate(500) }}</p>
</div>

<!-- Branding -->
<div class="dimension-item">
    <div class="dimension-header">
        <span class="dimension-score">{{ scores.branding }}/100</span>
        <span class="dimension-title">Marca Pessoal e Proposta de Valor</span>
        <div class="clearfix"></div>
    </div>
    <div class="dimension-bar">
        <div class="dimension-bar-fill" style="width: {{ scores.branding }}%;"></div>
    </div>
    <p class="dimension-analysis">{{ analysis.skills_differentiation.differentiation_factors | default('Análise não disponível.') | truncate(500) }}</p>
</div>

<!-- Consistência -->
<div class="dimension-item">
    <div class="dimension-header">
        <span class="dimension-score">{{ scores.consistencia }}/100</span>
        <span class="dimension-title">Consistência e Coerência</span>
        <div class="clearfix"></div>
    </div>
    <div class="dimension-bar">
        <div class="dimension-bar-fill" style="width: {{ scores.consistencia }}%;"></div>
    </div>
    <p class="dimension-analysis">{{ analysis.strategic_risks.identified_risks | default('Análise não disponível.') | truncate(500) }}</p>
</div>

<!-- PÁGINA 6: DIAGNÓSTICO DE IMPACTO -->
<div class="page-break"></div>

<div class="page-header">
    <div class="header-text">{{ candidate_name }} | {{ date_formatted }}</div>
</div>

<h2>Diagnóstico de Impacto Profissional</h2>

<h3>Leitura em 30 Segundos por um Recrutador Sénior</h3>
<p>{{ analysis.diagnostic_impact.first_30_seconds_read | default('Análise não disponível.') }}</p>

<h3>Pontos Fortes de Impacto</h3>
<p>{{ analysis.diagnostic_impact.impact_strengths | default('Análise não disponível.') }}</p>

<h3>Pontos de Diluição de Impacto</h3>
<p>{{ analysis.diagnostic_impact.impact_dilutions | default('Análise não disponível.') }}</p>

<!-- PÁGINA 7: ANÁLISE ATS -->
<div class="page-break"></div>

<div class="page-header">
    <div class="header-text">{{ candidate_name }} | {{ date_formatted }}</div>
</div>

<h2>Análise ATS e Recrutamento Digital</h2>

<h3>Compatibilidade com Sistemas ATS</h3>
<p>{{ analysis.ats_digital_recruitment.compatibility | default('Análise não disponível.') }}</p>

<h3>Riscos de Filtragem Automática</h3>
<p>{{ analysis.ats_digital_recruitment.filtering_risks | default('Análise não disponível.') }}</p>

<h3>Alinhamento com Práticas de Recrutamento</h3>
<p>{{ analysis.ats_digital_recruitment.alignment | default('Análise não disponível.') }}</p>

<!-- PÁGINA 8: MELHORIAS DE FRASES -->
<div class="page-break"></div>

<div class="page-header">
    <div class="header-text">{{ candidate_name }} | {{ date_formatted }}</div>
</div>

<h2>Exemplos de Melhoria de Frases</h2>

{% for item in analysis.pdf_extended_content.phrase_improvements %}
<div class="before-after">
    <div class="ba-label ba-before">Antes (Original)</div>
    <div class="ba-text">"{{ item.original }}"</div>
    
    <div class="ba-label ba-after">Depois (Otimizado)</div>
    <div class="ba-text">"{{ item.improved }}"</div>
    
    <h4 class="text-gold">Justificação da Melhoria</h4>
    <p style="font-size: 9.5pt;">{{ item.explanation }}</p>
</div>
{% endfor %}

<!-- PÁGINA 9: ANÁLISE DE MERCADO -->
<div class="page-break"></div>

<div class="page-header">
    <div class="header-text">{{ candidate_name }} | {{ date_formatted }}</div>
</div>

<h2>Análise de Mercado e Posicionamento</h2>

<h3>Contexto: {{ analysis.pdf_extended_content.sector_analysis.identified_sector | default('Setor não identificado') }}</h3>
<p>{{ analysis.pdf_extended_content.sector_analysis.sector_trends | default('Análise de tendências não disponível.') }}</p>

<h3>Panorama Competitivo</h3>
<p>{{ analysis.pdf_extended_content.sector_analysis.competitive_landscape | default('Análise competitiva não disponível.') }}</p>

<!-- PÁGINA 10: CERTIFICAÇÕES RECOMENDADAS -->
<div class="page-break"></div>

<div class="page-header">
    <div class="header-text">{{ candidate_name }} | {{ date_formatted }}</div>
</div>

<h2>Certificações Recomendadas</h2>

{% for cert in analysis.pdf_extended_content.critical_certifications %}
<div class="cert-item">
    <span class="cert-priority priority-{{ cert.priority | lower }}">{{ cert.priority }}</span>
    <div class="cert-name">{{ cert.name }}</div>
    <div class="clearfix"></div>
    <div class="cert-issuer">{{ cert.issuer }} | {{ cert.estimated_investment | default('Investimento variável') }}</div>
    <p class="cert-relevance">{{ cert.relevance | truncate(300) }}</p>
</div>
{% endfor %}

<!-- PÁGINA 11: RECOMENDAÇÕES PRIORITÁRIAS -->
<div class="page-break"></div>

<div class="page-header">
    <div class="header-text">{{ candidate_name }} | {{ date_formatted }}</div>
</div>

<h2>Recomendações Prioritárias</h2>

<div class="recommendation-item">
    <div class="recommendation-priority" style="color: #e74c3c;">Ajustes Imediatos</div>
    <p>{{ analysis.priority_recommendations.immediate_adjustments | default('Recomendações não disponíveis.') }}</p>
</div>

<div class="recommendation-item">
    <div class="recommendation-priority" style="color: #f39c12;">Áreas de Refinamento</div>
    <p>{{ analysis.priority_recommendations.refinement_areas | default('Recomendações não disponíveis.') }}</p>
</div>

<div class="recommendation-item">
    <div class="recommendation-priority" style="color: #27ae60;">Reposicionamento Profundo</div>
    <p>{{ analysis.priority_recommendations.deep_repositioning | default('Recomendações não disponíveis.') }}</p>
</div>

<!-- PÁGINA 12: CONCLUSÃO E SERVIÇOS -->
<div class="page-break"></div>

<div class="page-header">
    <div class="header-text">{{ candidate_name }} | {{ date_formatted }}</div>
</div>

<h2>Conclusão Executiva</h2>

<h3>Potencial Após Melhorias</h3>
<p>{{ analysis.executive_conclusion.potential_after_improvements | default('Conclusão não disponível.') }}</p>

<h3>Competitividade Esperada</h3>
<p>{{ analysis.executive_conclusion.expected_competitiveness | default('Análise não disponível.') }}</p>

<h2>Outros Serviços Share2Inspire</h2>

<p class="text-muted">A sua jornada para uma carreira de impacto continua aqui. Potencie o seu percurso com as nossas soluções dedicadas.</p>

<table class="services-table">
    <tr>
        <td>
            <div class="service-icon">◆</div>
            <div class="service-title">Kickstart Pro</div>
            <div class="service-desc">Sessão estratégica de 1h para desbloquear decisões críticas de carreira.</div>
            <div class="service-link">Saber Mais →</div>
        </td>
        <td>
            <div class="service-icon">◆</div>
            <div class="service-title">Mentoria de Carreira</div>
            <div class="service-desc">Programa de acompanhamento personalizado para objetivos ambiciosos.</div>
            <div class="service-link">Saber Mais →</div>
        </td>
        <td>
            <div class="service-icon">◆</div>
            <div class="service-title">Revisão de LinkedIn</div>
            <div class="service-desc">Otimização do perfil para máxima visibilidade e atração de recrutadores.</div>
            <div class="service-link">Saber Mais →</div>
        </td>
    </tr>
</table>

<!-- FOOTER FINAL -->
<div style="text-align: center; margin-top: 30pt; padding-top: 15pt; border-top: 1pt solid #e9ecef;">
    <p class="text-muted text-small">Human Centred Career & Knowledge Platform</p>
    <p class="text-muted text-small">www.share2inspire.pt | srshare2inspire@gmail.com</p>
</div>

<div class="page-footer">
    Relatório de Análise de CV - Share2Inspire | Privado e Confidencial | {{ report_id }}
</div>

</body>
</html>
"""

    def generate_circular_scorecard(self, score, size=200, label="SCORE GERAL", show_label=True):
        """Gera um scorecard circular SVG elegante."""
        center = size / 2
        radius = center * 0.75
        stroke_width = size * 0.06
        
        circumference = 2 * math.pi * radius
        score_normalized = min(max(score, 0), 100) / 100
        dash_length = circumference * score_normalized
        
        if score >= 75:
            score_color = self.colors['success']
        elif score >= 50:
            score_color = self.colors['gold']
        elif score >= 25:
            score_color = self.colors['warning']
        else:
            score_color = self.colors['danger']
        
        svg = f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="{self.colors['white']}"/>
            <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="{self.colors['gray_light']}" stroke-width="{stroke_width}"/>
            <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="{score_color}" stroke-width="{stroke_width}" stroke-dasharray="{dash_length} {circumference}" stroke-linecap="round" transform="rotate(-90 {center} {center})"/>
            <circle cx="{center}" cy="{center}" r="{radius * 0.6}" fill="{self.colors['white']}"/>
            <text x="{center}" y="{center - (size * 0.05)}" font-family="Helvetica, Arial, sans-serif" font-size="{size * 0.22}" fill="{self.colors['black']}" text-anchor="middle" font-weight="bold">{int(score)}</text>
            <text x="{center}" y="{center + (size * 0.08)}" font-family="Helvetica, Arial, sans-serif" font-size="{size * 0.08}" fill="{self.colors['gray_medium']}" text-anchor="middle">/100</text>'''
        
        if show_label:
            svg += f'''<text x="{center}" y="{center + (size * 0.25)}" font-family="Helvetica, Arial, sans-serif" font-size="{size * 0.055}" fill="{self.colors['black']}" text-anchor="middle" font-weight="bold">{label}</text>'''
        
        svg += '</svg>'
        return svg

    def generate_mini_scorecard(self, score, size=70):
        """Gera um mini scorecard circular para as dimensões."""
        center = size / 2
        radius = center * 0.75
        stroke_width = size * 0.08
        
        circumference = 2 * math.pi * radius
        score_normalized = min(max(score, 0), 100) / 100
        dash_length = circumference * score_normalized
        
        svg = f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
            <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="{self.colors['gray_light']}" stroke-width="{stroke_width}"/>
            <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="{self.colors['gold']}" stroke-width="{stroke_width}" stroke-dasharray="{dash_length} {circumference}" stroke-linecap="round" transform="rotate(-90 {center} {center})"/>
            <circle cx="{center}" cy="{center}" r="{radius * 0.55}" fill="{self.colors['white']}"/>
            <text x="{center}" y="{center + (size * 0.1)}" font-family="Helvetica, Arial, sans-serif" font-size="{size * 0.28}" fill="{self.colors['black']}" text-anchor="middle" font-weight="bold">{int(score)}</text>
        </svg>'''
        return svg

    def generate_bar_chart(self, radar_data):
        """Gera um gráfico de barras horizontais SVG elegante."""
        # Ordem fixa consistente com os scorecards
        ordered_keys = ['estrutura', 'conteudo', 'riscos', 'ats', 'impacto', 'branding']
        label_mapping = {
            'estrutura': 'Estrutura & Clareza',
            'conteudo': 'Conteúdo & Relevância',
            'riscos': 'Consistência',
            'ats': 'Compatibilidade ATS',
            'impacto': 'Impacto & Resultados',
            'branding': 'Marca Pessoal'
        }
        
        labels = [label_mapping.get(k, k.capitalize()) for k in ordered_keys if k in radar_data]
        values = [min(radar_data.get(k, 0) * 5, 100) for k in ordered_keys if k in radar_data]
        num_bars = len(labels)

        svg_width = 500
        svg_height = 25 + (num_bars * 40)
        bar_height = 22
        margin_left = 150
        margin_right = 50

        svg = f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">'
        svg += f'<rect width="100%" height="100%" fill="{self.colors["white"]}"/>'

        total_bar_width = svg_width - margin_left - margin_right

        for i, (label, value) in enumerate(zip(labels, values)):
            y_pos = 12 + (i * 40)
            
            svg += f'<rect x="{margin_left}" y="{y_pos}" width="{total_bar_width}" height="{bar_height}" fill="{self.colors["gray_light"]}" rx="3"/>'
            score_bar_width = (total_bar_width / 100) * value
            svg += f'<rect x="{margin_left}" y="{y_pos}" width="{score_bar_width}" height="{bar_height}" fill="{self.colors["gold"]}" rx="3"/>'
            svg += f'<text x="{margin_left - 8}" y="{y_pos + bar_height / 2 + 4}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="{self.colors["black"]}" text-anchor="end" font-weight="bold">{label}</text>'
            svg += f'<text x="{margin_left + total_bar_width + 8}" y="{y_pos + bar_height / 2 + 4}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="{self.colors["gold"]}" font-weight="bold">{int(value)}</text>'

        svg += '</svg>'
        return svg

    def create_pdf(self, analysis_data, radar_chart_path=None):
        """Gera o PDF a partir dos dados de análise."""
        if not analysis_data or 'candidate_profile' not in analysis_data:
            raise ValueError("Dados de análise inválidos ou incompletos.")

        candidate_name = analysis_data.get('candidate_profile', {}).get('detected_name', 'Candidato')
        radar_data = analysis_data.get('radar_data', {})
        
        scores = {
            'estrutura': min(radar_data.get('estrutura', 0) * 5, 100),
            'conteudo': min(radar_data.get('conteudo', 0) * 5, 100),
            'consistencia': min(radar_data.get('riscos', 0) * 5, 100),  # Riscos invertido para Consistência
            'ats': min(radar_data.get('ats', 0) * 5, 100),
            'impacto': min(radar_data.get('impacto', 0) * 5, 100),
            'branding': min(radar_data.get('branding', 0) * 5, 100)
        }
        
        overall_score = sum(scores.values()) / len(scores) if scores else 0
        
        main_scorecard_svg = self.generate_circular_scorecard(overall_score, size=180, label="SCORE GLOBAL")
        main_scorecard = f"data:image/svg+xml;base64,{base64.b64encode(main_scorecard_svg.encode()).decode()}"
        
        scorecard_estrutura = f"data:image/svg+xml;base64,{base64.b64encode(self.generate_mini_scorecard(scores['estrutura'], 60).encode()).decode()}"
        scorecard_conteudo = f"data:image/svg+xml;base64,{base64.b64encode(self.generate_mini_scorecard(scores['conteudo'], 60).encode()).decode()}"
        scorecard_consistencia = f"data:image/svg+xml;base64,{base64.b64encode(self.generate_mini_scorecard(scores['consistencia'], 60).encode()).decode()}"
        scorecard_ats = f"data:image/svg+xml;base64,{base64.b64encode(self.generate_mini_scorecard(scores['ats'], 60).encode()).decode()}"
        scorecard_impacto = f"data:image/svg+xml;base64,{base64.b64encode(self.generate_mini_scorecard(scores['impacto'], 60).encode()).decode()}"
        scorecard_branding = f"data:image/svg+xml;base64,{base64.b64encode(self.generate_mini_scorecard(scores['branding'], 60).encode()).decode()}"
        
        bar_chart_svg = self.generate_bar_chart(radar_data)
        bar_chart = f"data:image/svg+xml;base64,{base64.b64encode(bar_chart_svg.encode()).decode()}"
        
        now = datetime.datetime.now()
        report_id = f"CVA {now.strftime('%Y %m %d %H %M')}"
        date_formatted = now.strftime("%d/%m/%Y %H:%M")

        template = Template(self._get_template())
        html = template.render(
            analysis=analysis_data,
            candidate_name=candidate_name,
            report_id=report_id,
            date_formatted=date_formatted,
            scores=scores,
            main_scorecard=main_scorecard,
            scorecard_estrutura=scorecard_estrutura,
            scorecard_conteudo=scorecard_conteudo,
            scorecard_consistencia=scorecard_consistencia,
            scorecard_ats=scorecard_ats,
            scorecard_impacto=scorecard_impacto,
            scorecard_branding=scorecard_branding,
            bar_chart=bar_chart
        )

        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html), dest=pdf_buffer)

        if pisa_status.err:
            raise Exception(f"Erro ao gerar PDF: {pisa_status.err}")

        pdf_buffer.seek(0)
        filename = f"Relatorio_Analise_CV_{candidate_name.replace(' ', '_')}.pdf"
        return pdf_buffer, filename


def generate_cv_report(analysis_data):
    """Função de conveniência para gerar relatório PDF."""
    generator = ReportPDFGenerator()
    return generator.create_pdf(analysis_data)
