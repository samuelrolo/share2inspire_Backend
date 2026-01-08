# -*- coding: utf-8 -*-
"""
Gerador de Relatório PDF Premium para Análise de CV
Share2Inspire - Versão 2.0 com conteúdo expandido

Inclui:
- Análise dimensional com radar chart
- Frases antes/depois com explicações
- Certificações críticas para o setor
- Dicas de design de CV
- Guia de escrita profissional
- Plano de desenvolvimento de carreira
- Estratégia de networking
- Posicionamento salarial
"""

import io
import math
import datetime
from xhtml2pdf import pisa
from jinja2 import Template
import PyPDF2

class ReportPDFGenerator:
    def __init__(self):
        self.template_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {
                    size: A4;
                    margin: 2cm 1.8cm;
                    @frame footer_frame {
                        -pdf-frame-content: footer_content;
                        left: 1.8cm; width: 17.4cm; top: 27.5cm; height: 1cm;
                    }
                }
                
                body {
                    font-family: Helvetica, Arial, sans-serif;
                    color: #2c3e50;
                    line-height: 1.5;
                    font-size: 10pt;
                }
                
                /* Cores principais */
                .text-gold { color: #BF9A33; }
                .text-dark { color: #2c3e50; }
                .text-muted { color: #7f8c8d; }
                .bg-light { background-color: #f8f9fa; }
                
                /* Tipografia */
                h1 { font-size: 24pt; font-weight: 700; color: #2c3e50; margin-bottom: 5pt; }
                h2 { font-size: 14pt; font-weight: 600; color: #2c3e50; margin-top: 25pt; margin-bottom: 12pt; }
                h3 { font-size: 11pt; font-weight: 600; color: #BF9A33; margin-top: 15pt; margin-bottom: 8pt; }
                h4 { font-size: 10pt; font-weight: 600; color: #2c3e50; margin-bottom: 5pt; }
                p { margin-bottom: 8pt; text-align: justify; }
                
                /* Capa */
                .cover { text-align: center; padding-top: 4cm; }
                .cover-logo { margin-bottom: 1.5cm; }
                .cover-badge { 
                    display: inline-block;
                    background-color: #BF9A33;
                    color: white;
                    padding: 5pt 20pt;
                    font-size: 9pt;
                    font-weight: 600;
                    letter-spacing: 2pt;
                    text-transform: uppercase;
                    margin-bottom: 15pt;
                }
                .cover-title { 
                    font-size: 28pt; 
                    font-weight: 700; 
                    color: #2c3e50; 
                    margin-bottom: 8pt;
                    letter-spacing: -0.5pt;
                }
                .cover-subtitle {
                    font-size: 12pt;
                    color: #7f8c8d;
                    margin-bottom: 3cm;
                }
                .cover-candidate {
                    font-size: 18pt;
                    font-weight: 600;
                    color: #2c3e50;
                    margin-bottom: 5pt;
                }
                .cover-role {
                    font-size: 11pt;
                    color: #BF9A33;
                    margin-bottom: 3cm;
                }
                .cover-meta {
                    font-size: 9pt;
                    color: #95a5a6;
                }
                
                /* Quebra de página */
                .page-break { page-break-before: always; }
                
                /* Secções */
                .section-header {
                    border-bottom: 2pt solid #BF9A33;
                    padding-bottom: 8pt;
                    margin-bottom: 15pt;
                }
                .section-header h2 {
                    margin: 0;
                    color: #2c3e50;
                }
                
                /* Cards e Boxes */
                .info-box {
                    background-color: #f8f9fa;
                    padding: 15pt;
                    margin-bottom: 15pt;
                    border-left: 3pt solid #BF9A33;
                }
                
                .highlight-box {
                    background-color: #fef9e7;
                    border: 1pt solid #f4d03f;
                    padding: 12pt;
                    margin: 15pt 0;
                }
                
                .score-box {
                    text-align: center;
                    padding: 20pt;
                    background-color: #f8f9fa;
                    margin: 15pt 0;
                }
                .score-value {
                    font-size: 36pt;
                    font-weight: 700;
                    color: #BF9A33;
                }
                .score-label {
                    font-size: 9pt;
                    color: #7f8c8d;
                    text-transform: uppercase;
                    letter-spacing: 1pt;
                }
                
                /* Tabelas */
                table { width: 100%; border-collapse: collapse; margin: 10pt 0; }
                th { 
                    background-color: #f8f9fa; 
                    padding: 8pt; 
                    text-align: left; 
                    font-weight: 600;
                    font-size: 9pt;
                    color: #7f8c8d;
                    text-transform: uppercase;
                    border-bottom: 1pt solid #dee2e6;
                }
                td { 
                    padding: 10pt 8pt; 
                    border-bottom: 1pt solid #eee;
                    vertical-align: top;
                }
                
                /* Antes/Depois */
                .before-after {
                    margin: 15pt 0;
                    page-break-inside: avoid;
                }
                .before-box {
                    background-color: #fdf2f2;
                    border-left: 3pt solid #e74c3c;
                    padding: 10pt;
                    margin-bottom: 8pt;
                }
                .after-box {
                    background-color: #eafaf1;
                    border-left: 3pt solid #27ae60;
                    padding: 10pt;
                }
                .ba-label {
                    font-size: 8pt;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 1pt;
                    margin-bottom: 5pt;
                }
                .before-box .ba-label { color: #e74c3c; }
                .after-box .ba-label { color: #27ae60; }
                
                /* Certificações */
                .cert-card {
                    background-color: #f8f9fa;
                    padding: 12pt;
                    margin-bottom: 10pt;
                    page-break-inside: avoid;
                }
                .cert-name {
                    font-weight: 600;
                    color: #2c3e50;
                    margin-bottom: 3pt;
                }
                .cert-issuer {
                    font-size: 9pt;
                    color: #BF9A33;
                    margin-bottom: 5pt;
                }
                .cert-detail {
                    font-size: 9pt;
                    color: #7f8c8d;
                }
                .cert-priority {
                    display: inline-block;
                    font-size: 8pt;
                    padding: 2pt 8pt;
                    background-color: #BF9A33;
                    color: white;
                    font-weight: 600;
                }
                
                /* Timeline/Roadmap */
                .timeline-item {
                    padding-left: 20pt;
                    border-left: 2pt solid #BF9A33;
                    margin-bottom: 15pt;
                    page-break-inside: avoid;
                }
                .timeline-period {
                    font-size: 9pt;
                    font-weight: 600;
                    color: #BF9A33;
                    text-transform: uppercase;
                    margin-bottom: 5pt;
                }
                
                /* Dicas */
                .tip-box {
                    background-color: #e8f4fd;
                    border-left: 3pt solid #3498db;
                    padding: 10pt;
                    margin: 10pt 0;
                }
                .tip-title {
                    font-weight: 600;
                    color: #2980b9;
                    margin-bottom: 5pt;
                }
                
                /* Listas */
                ul { padding-left: 15pt; margin: 8pt 0; }
                li { margin-bottom: 5pt; }
                
                /* Keywords */
                .keyword {
                    display: inline-block;
                    background-color: #f0f0f0;
                    padding: 2pt 8pt;
                    margin: 2pt;
                    font-size: 9pt;
                    border-radius: 2pt;
                }
                
                /* Footer */
                .footer {
                    font-size: 8pt;
                    color: #bdc3c7;
                    text-align: center;
                    border-top: 0.5pt solid #eee;
                    padding-top: 5pt;
                }
                
                /* Radar Chart Container */
                .radar-container {
                    text-align: center;
                    margin: 20pt 0;
                    padding: 15pt;
                    background-color: #f8f9fa;
                }
                
                /* Strategic Bullet (do template antigo) */
                .strategic-bullet { 
                    border-left: 3pt solid #BF9A33; 
                    padding-left: 15pt; 
                    margin-bottom: 20pt; 
                    page-break-inside: avoid; 
                }
                .sb-title { font-weight: bold; font-size: 11pt; margin-bottom: 2pt; }
                .sb-metric { color: #BF9A33; font-size: 9pt; font-weight: bold; text-transform: uppercase; margin-bottom: 4pt; }
                .sb-detail { font-size: 10pt; color: #444; text-align: justify; }
            </style>
        </head>
        <body>
            <!-- Footer -->
            <div id="footer_content" class="footer">
                Share2Inspire | Relatório de Análise de CV | {{ report_id }} | Confidencial
            </div>

            <!-- ==================== CAPA ==================== -->
            <div class="cover">
                <div class="cover-logo">
                    <img src="https://share2inspire.pt/images/logo.png" width="160" />
                </div>
                
                <div class="cover-badge">Análise Profissional</div>
                
                <h1 class="cover-title">Relatório de Análise de CV</h1>
                <p class="cover-subtitle">Diagnóstico completo e recomendações estratégicas</p>
                
                <p class="cover-candidate">{{ report.candidate_profile.detected_name }}</p>
                <p class="cover-role">{{ report.candidate_profile.detected_role }}</p>
                
                <p class="cover-meta">
                    Gerado em {{ generation_date }}<br>
                    ID: {{ report_id }}
                </p>
            </div>

            <!-- ==================== SUMÁRIO EXECUTIVO ==================== -->
            <div class="page-break"></div>
            
            <div class="section-header">
                <h2>Sumário Executivo</h2>
            </div>
            
            <div class="score-box">
                <div class="score-value">{{ report.final_verdict.score }}<span style="font-size: 14pt; color: #95a5a6;">/100</span></div>
                <div class="score-label">Pontuação Global</div>
                <p style="margin-top: 10pt; font-size: 11pt; color: #BF9A33; font-weight: 600;">{{ report.final_verdict.badge }}</p>
            </div>
            
            <table>
                <tr>
                    <td width="50%">
                        <strong>Nome:</strong> {{ report.candidate_profile.detected_name }}<br>
                        <strong>Função:</strong> {{ report.candidate_profile.detected_role }}
                    </td>
                    <td width="50%">
                        <strong>Experiência:</strong> {{ report.candidate_profile.total_years_exp }}<br>
                        <strong>Senioridade:</strong> {{ report.candidate_profile.seniority }}
                    </td>
                </tr>
            </table>
            
            {% if report.candidate_profile.detected_sector %}
            <div class="info-box">
                <strong>Setor Identificado:</strong> {{ report.candidate_profile.detected_sector }}
            </div>
            {% endif %}
            
            <h3>Diagnóstico em 3 Frases</h3>
            {% if report.executive_summary and report.executive_summary.three_sentences %}
            <ol>
                {% for sentence in report.executive_summary.three_sentences %}
                <li style="margin-bottom: 8pt;">{{ sentence }}</li>
                {% endfor %}
            </ol>
            {% endif %}

            <!-- ==================== COMPETÊNCIAS E PONTOS FORTES ==================== -->
            <div class="page-break"></div>
            
            <div class="section-header">
                <h2>Competências e Pontos Fortes</h2>
            </div>
            
            {% if report.maturity_and_skills %}
            <h3>Domínios e Competências</h3>
            {% for item in report.maturity_and_skills %}
            <div class="strategic-bullet">
                <div class="sb-title">{{ item.title }}</div>
                <div class="sb-metric">{{ item.metric }}</div>
                <div class="sb-detail">{{ item.detail }}</div>
            </div>
            {% endfor %}
            {% endif %}
            
            {% if report.key_strengths %}
            <h3>Diferenciadores Identificados</h3>
            {% for item in report.key_strengths %}
            <div class="strategic-bullet">
                <div class="sb-title">{{ item.title }}</div>
                <div class="sb-metric">{{ item.metric }}</div>
                <div class="sb-detail">{{ item.detail }}</div>
            </div>
            {% endfor %}
            {% endif %}

            <!-- ==================== ANÁLISE DIMENSIONAL ==================== -->
            <div class="page-break"></div>
            
            <div class="section-header">
                <h2>Análise Dimensional</h2>
            </div>
            
            <p>Cada dimensão foi avaliada numa escala de 0 a 20 pontos, com base em critérios específicos de recrutamento e ATS.</p>
            
            <!-- Radar Chart -->
            <div class="radar-container">
                {{ radar_svg | safe }}
            </div>
            
            {% if report.dimensions %}
            <table>
                <tr>
                    <th>Dimensão</th>
                    <th>Pontos</th>
                    <th>O que está bem</th>
                    <th>O que melhorar</th>
                </tr>
                {% for dim_name, dim_data in report.dimensions.items() %}
                {% if dim_data is mapping %}
                <tr>
                    <td><strong>{{ dim_name | replace('_', ' ') | capitalize }}</strong></td>
                    <td style="text-align: center; color: #BF9A33; font-weight: 600;">{{ dim_data.score }}/20</td>
                    <td style="font-size: 9pt;">{{ dim_data.signal }}</td>
                    <td style="font-size: 9pt;">{{ dim_data.upgrade }}</td>
                </tr>
                {% endif %}
                {% endfor %}
            </table>
            {% endif %}

            <!-- ==================== FRASES ANTES/DEPOIS ==================== -->
            {% if report.pdf_extended_content and report.pdf_extended_content.phrase_improvements %}
            <div class="page-break"></div>
            
            <div class="section-header">
                <h2>Como Melhorar as Tuas Frases</h2>
            </div>
            
            <p>Analisámos frases do teu CV e mostramos como podem ser transformadas para maior impacto. Usa estes exemplos como guia para reescrever todo o documento.</p>
            
            {% for phrase in report.pdf_extended_content.phrase_improvements %}
            <div class="before-after">
                <h4 style="color: #7f8c8d; font-size: 9pt;">Exemplo {{ loop.index }}</h4>
                
                <div class="before-box">
                    <div class="ba-label">Antes (Original)</div>
                    <p style="margin: 0; font-style: italic;">"{{ phrase.original }}"</p>
                </div>
                
                <div class="after-box">
                    <div class="ba-label">Depois (Melhorado)</div>
                    <p style="margin: 0; font-weight: 500;">"{{ phrase.improved }}"</p>
                </div>
                
                <div class="tip-box" style="margin-top: 8pt;">
                    <div class="tip-title">Porquê esta mudança?</div>
                    <p style="margin: 0; font-size: 9pt;">{{ phrase.explanation }}</p>
                </div>
            </div>
            {% endfor %}
            {% endif %}

            <!-- ==================== CERTIFICAÇÕES CRÍTICAS ==================== -->
            {% if report.pdf_extended_content and report.pdf_extended_content.critical_certifications %}
            <div class="page-break"></div>
            
            <div class="section-header">
                <h2>Certificações Recomendadas para o Teu Setor</h2>
            </div>
            
            <p>Com base no teu perfil e setor identificado, estas são as certificações que mais valorizam o teu CV e aumentam a tua competitividade no mercado português e europeu.</p>
            
            {% for cert in report.pdf_extended_content.critical_certifications %}
            <div class="cert-card">
                <table width="100%">
                    <tr>
                        <td>
                            <div class="cert-name">{{ cert.name }}</div>
                            <div class="cert-issuer">{{ cert.issuer }}</div>
                        </td>
                        <td width="80" style="text-align: right;">
                            <span class="cert-priority">{{ cert.priority }}</span>
                        </td>
                    </tr>
                </table>
                <p style="margin: 8pt 0 5pt 0; font-size: 10pt;">{{ cert.relevance }}</p>
                <div class="cert-detail">
                    <strong>Investimento:</strong> {{ cert.estimated_investment }}<br>
                    <strong>Onde obter:</strong> {{ cert.where_to_get }}
                </div>
            </div>
            {% endfor %}
            {% endif %}

            <!-- ==================== DICAS DE DESIGN ==================== -->
            {% if report.pdf_extended_content and report.pdf_extended_content.cv_design_tips %}
            <div class="page-break"></div>
            
            <div class="section-header">
                <h2>Dicas de Design do CV</h2>
            </div>
            
            <p>Um CV bem desenhado é lido em menos de 20 segundos. Segue estas recomendações para maximizar o impacto visual e a legibilidade.</p>
            
            {% set tips = report.pdf_extended_content.cv_design_tips %}
            
            <h3>Layout e Estrutura</h3>
            <div class="info-box">
                {{ tips.layout }}
            </div>
            
            <h3>Tipografia</h3>
            <div class="info-box">
                {{ tips.typography }}
            </div>
            
            <h3>Espaçamento e Margens</h3>
            <div class="info-box">
                {{ tips.spacing }}
            </div>
            
            <h3>Ordem das Secções</h3>
            <div class="info-box">
                {{ tips.sections_order }}
            </div>
            
            <h3>Extensão Recomendada</h3>
            <div class="info-box">
                {{ tips.length }}
            </div>
            
            {% if tips.visual_elements %}
            <h3>Elementos Visuais</h3>
            <div class="info-box">
                {{ tips.visual_elements }}
            </div>
            {% endif %}
            {% endif %}

            <!-- ==================== GUIA DE ESCRITA ==================== -->
            {% if report.pdf_extended_content and report.pdf_extended_content.writing_guide %}
            <div class="page-break"></div>
            
            <div class="section-header">
                <h2>Guia de Escrita para o Teu CV</h2>
            </div>
            
            {% set guide = report.pdf_extended_content.writing_guide %}
            
            <h3>Verbos de Ação Recomendados</h3>
            <p>Começa cada bullet point com um verbo forte. Estes são os mais eficazes para a tua área:</p>
            <div style="margin: 10pt 0;">
                {% for verb in guide.power_verbs %}
                <span class="keyword" style="background-color: #e8f8f5; color: #1abc9c;">{{ verb }}</span>
                {% endfor %}
            </div>
            
            <h3>Keywords ATS Críticas</h3>
            <p>Inclui estas palavras-chave para passar nos filtros automáticos de recrutamento:</p>
            <div style="margin: 10pt 0;">
                {% for keyword in guide.keywords_to_add %}
                <span class="keyword" style="background-color: #fef9e7; color: #f39c12;">{{ keyword }}</span>
                {% endfor %}
            </div>
            
            <h3>Expressões a Evitar</h3>
            <p>Remove ou substitui estas expressões genéricas que enfraquecem o teu CV:</p>
            <div style="margin: 10pt 0;">
                {% for phrase in guide.phrases_to_avoid %}
                <span class="keyword" style="background-color: #fdedec; color: #e74c3c; text-decoration: line-through;">{{ phrase }}</span>
                {% endfor %}
            </div>
            
            <h3>Como Quantificar Resultados</h3>
            <div class="highlight-box">
                {{ guide.quantification_tips }}
            </div>
            {% endif %}

            <!-- ==================== PLANO DE DESENVOLVIMENTO ==================== -->
            {% if report.pdf_extended_content and report.pdf_extended_content.professional_development %}
            <div class="page-break"></div>
            
            <div class="section-header">
                <h2>Plano de Desenvolvimento Profissional</h2>
            </div>
            
            <p>Um roadmap personalizado para acelerar a tua progressão de carreira, com ações concretas e prazos definidos.</p>
            
            {% set dev = report.pdf_extended_content.professional_development %}
            
            <div class="timeline-item">
                <div class="timeline-period">Próximos 30 Dias</div>
                {% for item in dev.short_term %}
                <h4>{{ item.action }}</h4>
                <p style="font-size: 9pt; color: #7f8c8d;">
                    <strong>Impacto esperado:</strong> {{ item.expected_impact }}<br>
                    <strong>Recursos:</strong> {{ item.resources }}
                </p>
                {% endfor %}
            </div>
            
            <div class="timeline-item">
                <div class="timeline-period">3 a 6 Meses</div>
                {% for item in dev.medium_term %}
                <h4>{{ item.action }}</h4>
                <p style="font-size: 9pt; color: #7f8c8d;">
                    <strong>Impacto esperado:</strong> {{ item.expected_impact }}<br>
                    <strong>Recursos:</strong> {{ item.resources }}
                </p>
                {% endfor %}
            </div>
            
            <div class="timeline-item">
                <div class="timeline-period">1 a 2 Anos</div>
                {% for item in dev.long_term %}
                <h4>{{ item.action }}</h4>
                <p style="font-size: 9pt; color: #7f8c8d;">
                    <strong>Impacto esperado:</strong> {{ item.expected_impact }}<br>
                    <strong>Recursos:</strong> {{ item.resources }}
                </p>
                {% endfor %}
            </div>
            {% endif %}

            <!-- ==================== NETWORKING & POSICIONAMENTO ==================== -->
            {% if report.pdf_extended_content and report.pdf_extended_content.networking_strategy %}
            <div class="page-break"></div>
            
            <div class="section-header">
                <h2>Estratégia de Networking</h2>
            </div>
            
            {% set network = report.pdf_extended_content.networking_strategy %}
            
            <h3>Otimização do LinkedIn</h3>
            <div class="info-box">
                {{ network.linkedin_optimization }}
            </div>
            
            <h3>Comunidades Profissionais</h3>
            <ul>
                {% for community in network.key_communities %}
                <li>{{ community }}</li>
                {% endfor %}
            </ul>
            
            <h3>Eventos Recomendados</h3>
            <ul>
                {% for event in network.events_to_attend %}
                <li>{{ event }}</li>
                {% endfor %}
            </ul>
            
            <h3>Construir Autoridade na Área</h3>
            <div class="info-box">
                {{ network.thought_leadership }}
            </div>
            {% endif %}
            
            {% if report.pdf_extended_content and report.pdf_extended_content.salary_positioning %}
            <h3>Posicionamento Salarial</h3>
            {% set salary = report.pdf_extended_content.salary_positioning %}
            
            <div class="highlight-box">
                <strong>Intervalo de Mercado:</strong> {{ salary.market_range }}
            </div>
            
            <table>
                <tr>
                    <td width="50%">
                        <strong style="color: #27ae60;">Pontos Fortes para Negociação:</strong><br>
                        <span style="font-size: 9pt;">{{ salary.negotiation_leverage }}</span>
                    </td>
                    <td width="50%">
                        <strong style="color: #e74c3c;">Gaps a Colmatar:</strong><br>
                        <span style="font-size: 9pt;">{{ salary.gaps_to_address }}</span>
                    </td>
                </tr>
            </table>
            {% endif %}

            <!-- ==================== RECOMENDAÇÕES ESTRATÉGICAS ==================== -->
            {% if report.strategic_feedback %}
            <div class="page-break"></div>
            
            <div class="section-header">
                <h2>Recomendações Estratégicas</h2>
            </div>
            
            {% if report.strategic_feedback.pdf_details %}
            <div class="info-box" style="border-left-color: #27ae60;">
                <h4 style="color: #27ae60; margin-top: 0;">O que reforçar (Aumentar Impacto)</h4>
                <p>{{ report.strategic_feedback.pdf_details.what_to_reinforce }}</p>
            </div>

            <div class="info-box" style="border-left-color: #e74c3c;">
                <h4 style="color: #e74c3c; margin-top: 0;">O que ajustar já (Correção Imediata)</h4>
                <p>{{ report.strategic_feedback.pdf_details.what_to_adjust }}</p>
            </div>
            {% endif %}
            
            {% if report.evolution_roadmap and report.evolution_roadmap.pdf_details %}
            <h3>Plano de Evolução</h3>
            {% for item in report.evolution_roadmap.pdf_details %}
            <div style="margin-bottom: 15pt;">
                <h4>{{ item.title }}</h4>
                <ul style="font-size: 9pt;">
                    {% for action in item.actions %}
                    <li>{{ action }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endfor %}
            {% endif %}
            {% endif %}

            <!-- ==================== PRÓXIMOS PASSOS ==================== -->
            <div class="page-break"></div>
            
            <div class="section-header">
                <h2>Próximos Passos</h2>
            </div>
            
            <p style="font-size: 12pt; text-align: center; margin: 30pt 0;">
                A tua jornada para uma carreira de impacto continua aqui.
            </p>
            
            <table>
                <tr>
                    <td width="33%" style="background-color: #f8f9fa; padding: 15pt; text-align: center; vertical-align: top;">
                        <div style="font-weight: 600; color: #BF9A33; margin-bottom: 8pt; font-size: 11pt;">Kickstart Pro</div>
                        <div style="font-size: 9pt; color: #666;">Sessão estratégica de 1h para decisões críticas de carreira.</div>
                    </td>
                    <td width="33%" style="background-color: #f8f9fa; padding: 15pt; text-align: center; vertical-align: top;">
                        <div style="font-weight: 600; color: #BF9A33; margin-bottom: 8pt; font-size: 11pt;">Revisão de CV</div>
                        <div style="font-size: 9pt; color: #666;">Feedback humano especializado com reescrita completa.</div>
                    </td>
                    <td width="33%" style="background-color: #f8f9fa; padding: 15pt; text-align: center; vertical-align: top;">
                        <div style="font-weight: 600; color: #BF9A33; margin-bottom: 8pt; font-size: 11pt;">CV Analyzer</div>
                        <div style="font-size: 9pt; color: #666;">Novos diagnósticos após implementares as melhorias.</div>
                    </td>
                </tr>
            </table>
            
            <div style="text-align: center; margin-top: 50pt;">
                <img src="https://share2inspire.pt/images/logo.png" width="100" /><br>
                <p style="font-size: 9pt; color: #95a5a6; margin-top: 15pt;">
                    Carreira com clareza, estratégia e narrativa de impacto.<br>
                    <strong>www.share2inspire.pt</strong> | srshare2inspire@gmail.com
                </p>
            </div>
            
        </body>
        </html>
        """

    def generate_radar_svg(self, data):
        """Generates a clean, minimalist SVG radar chart."""
        labels = ['Estrutura', 'Conteúdo', 'ATS', 'Impacto', 'Branding', 'Riscos']
        
        # Tentar obter valores do radar_data ou dimensions
        if isinstance(data, dict):
            values = [
                data.get('estrutura', data.get('structure', 10)),
                data.get('conteudo', data.get('content', 10)),
                data.get('ats', 10),
                data.get('impacto', data.get('impact', 10)),
                data.get('branding', data.get('market_fit', 10)),
                data.get('riscos', data.get('readiness', 10))
            ]
        else:
            values = [10, 10, 10, 10, 10, 10]
        
        size = 300
        center = size / 2
        radius = size * 0.35
        num_points = len(labels)
        
        svg = f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">'
        
        # Background circle
        svg += f'<circle cx="{center}" cy="{center}" r="{radius + 10}" fill="#f8f9fa" />'
        
        # Grid polygons
        for r in [0.25, 0.5, 0.75, 1.0]:
            grid_points = []
            for i in range(num_points):
                angle = (math.pi * 2 * i / num_points) - (math.pi / 2)
                x = center + radius * r * math.cos(angle)
                y = center + radius * r * math.sin(angle)
                grid_points.append(f"{x},{y}")
            svg += f'<polygon points="{" ".join(grid_points)}" fill="none" stroke="#dee2e6" stroke-width="0.5" />'
        
        # Axis lines and labels
        points = []
        for i in range(num_points):
            angle = (math.pi * 2 * i / num_points) - (math.pi / 2)
            x_end = center + radius * math.cos(angle)
            y_end = center + radius * math.sin(angle)
            svg += f'<line x1="{center}" y1="{center}" x2="{x_end}" y2="{y_end}" stroke="#dee2e6" stroke-width="0.5" />'
            
            # Labels
            lx = center + (radius + 25) * math.cos(angle)
            ly = center + (radius + 25) * math.sin(angle)
            svg += f'<text x="{lx}" y="{ly}" text-anchor="middle" dominant-baseline="middle" font-size="9" font-family="Helvetica, Arial" fill="#7f8c8d">{labels[i]}</text>'
            
            # Data points (scale 0-20 to 0-100%)
            val_radius = radius * (max(min(values[i], 20), 0) / 20)
            dx = center + val_radius * math.cos(angle)
            dy = center + val_radius * math.sin(angle)
            points.append(f"{dx},{dy}")
        
        # Data polygon
        svg += f'<polygon points="{" ".join(points)}" fill="rgba(191, 154, 51, 0.2)" stroke="#BF9A33" stroke-width="2" />'
        
        # Data points
        for p in points:
            px, py = p.split(',')
            svg += f'<circle cx="{px}" cy="{py}" r="4" fill="#BF9A33" />'
            
        svg += '</svg>'
        return svg

    def create_pdf(self, report_data):
        """Generates the PDF bytes from report data."""
        
        # Generate radar SVG
        radar_data = report_data.get('radar_data', {})
        radar_svg = self.generate_radar_svg(radar_data)
        
        # Generate ID and Date
        now = datetime.datetime.now()
        report_id = f"CVA-{now.strftime('%Y%m%d-%H%M')}"
        gen_date = now.strftime('%d/%m/%Y às %H:%M')
        
        # Render template
        tm = Template(self.template_html)
        html_content = tm.render(
            report=report_data, 
            radar_svg=radar_svg, 
            report_id=report_id,
            generation_date=gen_date
        )
        
        # Generate PDF
        result_bytes = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=result_bytes, encoding='utf-8')
        
        if pisa_status.err:
            return None, f"Erro na geração do PDF: {pisa_status.err}"
            
        pdf_content = result_bytes.getvalue()
        
        # Validation
        size_kb = len(pdf_content) / 1024
        if size_kb < 30:
            return pdf_content, f"Aviso: PDF pequeno ({size_kb:.1f}KB)"
        
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            pages = len(reader.pages)
            if pages < 4:
                return pdf_content, f"Aviso: PDF tem apenas {pages} páginas"
        except Exception as e:
            return pdf_content, f"Aviso ao validar: {str(e)}"

        return pdf_content, "OK"
