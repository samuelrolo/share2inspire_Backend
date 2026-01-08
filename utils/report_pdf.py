
# -*- coding: utf-8 -*-
"""
Gerador de Relatório PDF Premium para Análise de CV
Share2Inspire - Versão 5.0 com Foco em Densidade e Design de Consultoria
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
                    margin: 1.8cm;
                    @frame footer_frame {
                        -pdf-frame-content: footer_content;
                        left: 1.8cm; width: 17.4cm; top: 27.7cm; height: 1cm;
                    }
                    @bottom-left {
                        content: "CV Analyzer | {{ candidate_name }} | {{ date_formatted }}";
                        font-family: Helvetica;
                        font-size: 8pt;
                        color: #adb5bd;
                    }
                    @bottom-right {
                        content: "Página " counter(page) " de " counter(pages);
                        font-family: Helvetica;
                        font-size: 8pt;
                        color: #adb5bd;
                    }
                }

                body {
                    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                    color: #343a40; /* Cinza escuro para texto */
                    line-height: 1.45;
                    font-size: 10pt;
                    font-weight: 400; /* Peso normal para melhor leitura */
                }

                /* --- CORES E TIPOGRAFIA --- */
                .text-gold { color: #BF9A33; }
                h1, h2, h3, h4 {
                    font-weight: 700; /* Negrito para todos os títulos */
                    color: #212529; /* Preto suave */
                    margin: 0;
                    padding: 0;
                    line-height: 1.2;
                }
                h1 { font-size: 22pt; margin-bottom: 10pt; }
                h2 { font-size: 16pt; margin-top: 25pt; margin-bottom: 12pt; border-bottom: 1.5pt solid #BF9A33; padding-bottom: 6pt; }
                h3 { font-size: 12pt; font-weight: 600; color: #BF9A33; margin-top: 20pt; margin-bottom: 8pt; }
                p { margin: 0 0 10pt 0; text-align: justify; }

                /* --- ESTRUTURA E LAYOUT --- */
                .header-logo {
                    text-align: left;
                    margin-bottom: 25pt;
                }
                .header-logo img {
                    height: 25px; /* Logo discreto */
                }

                .footer {
                    font-size: 8pt;
                    color: #adb5bd; /* Cinza claro */
                    text-align: center;
                }

                /* --- BLOCOS DE CONSULTORIA (SUBSTITUI TABELAS E CAIXAS) --- */
                .consulting-block {
                    margin-bottom: 20pt;
                    padding: 0;
                    border: none;
                    background: none;
                }

                /* --- ANTES/DEPOIS --- */
                .before-after-block {
                    margin: 20pt 0;
                    padding: 15pt;
                    background-color: #f8f9fa; /* Fundo muito leve */
                    border-left: 4pt solid #BF9A33;
                }
                .ba-label {
                    font-size: 9pt;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 1pt;
                    margin-bottom: 8pt;
                }
                .before-label { color: #e74c3c; } /* Vermelho para 'Antes' */
                .after-label { color: #27ae60; } /* Verde para 'Depois' */
                .ba-text {
                    font-style: italic;
                    color: #495057;
                    margin-bottom: 15pt;
                }

                /* --- GRÁFICO RADAR --- */
                .radar-container {
                    text-align: center;
                    margin: 30pt 0;
                }

                /* --- PRÓXIMOS PASSOS --- */
                .next-steps-container {
                    margin-top: 30pt;
                    display: block;
                    width: 100%;
                }
                .step-box {
                    width: 30%;
                    display: inline-block;
                    text-align: center;
                    padding: 0 10pt;
                }
                .step-box h4 {
                    color: #BF9A33;
                    font-size: 11pt;
                    margin-bottom: 8pt;
                }
                .step-box p {
                    font-size: 9pt;
                    color: #6c757d;
                    text-align: center;
                }

                /* --- NOVA APRESENTAÇÃO DE PONTUAÇÃO (SEM TABELA) --- */
                .score-item {
                    margin-bottom: 15pt;
                    border-left: 3pt solid #e0e0e0;
                    padding-left: 10pt;
                }
                .score-item-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: baseline;
                    margin-bottom: 5pt;
                }
                .score-item-header h4 {
                    margin: 0;
                    color: #212529;
                    font-size: 11pt;
                }
                .score-item-value {
                    font-size: 14pt;
                    font-weight: 700;
                    color: #BF9A33;
                }
                .score-item-analysis, .score-item-focus {
                    font-size: 9.5pt;
                    color: #495057;
                    margin-bottom: 5pt;
                    text-align: justify;
                }
                .score-item-focus strong { color: #BF9A33; }

            </style>
        </head>
        <body>

            <!-- CABEÇALHO COM LOGO -->
            <div class="header-logo">
                <img src="https://share2inspire.com/wp-content/uploads/2022/06/Share2Inspire-Logo-Gold-1.png" alt="Share2Inspire-Logo">
            </div>

            <!-- TÍTULO DO RELATÓRIO -->
            <h1>Relatório de Análise de Currículo</h1>
            <p style="font-size: 12pt; color: #6c757d; margin-top: -8pt;">Análise Estratégica para {{ analysis.candidate_profile.detected_name }}</p>

            <!-- SUMÁRIO EXECUTIVO -->
            <div class="consulting-block">
                <h2>Sumário Executivo Estratégico</h2>
                <h3>Posicionamento de Mercado</h3>
                <p>{{ analysis.executive_summary.market_positioning }}</p>
                <h3>Fatores-Chave de Decisão</h3>
                <p>{{ analysis.executive_summary.key_decision_factors }}</p>
            </div>

            <!-- SCORECARD CIRCULAR -->
            <div class="scorecard-container">
                <img src="{{ scorecard_path }}" width="280" alt="Scorecard Circular">
            </div>

            <!-- ANÁLISE DIMENSIONAL (BARRAS) -->
            <div class="consulting-block">
                <h2>Análise Dimensional</h2>
                <img src="{{ radar_chart_path }}" width="100%" alt="Análise Dimensional em Barras" style="max-width: 600px; margin: 15pt 0;">
            </div>

            <!-- PONTUAÇÃO DETALHADA DO CURRÍCULO (CONDENSADO) -->
            <div class="consulting-block score-summary">
                <h2>Detalhes por Dimensão</h2>
                <div class="score-item">
                    <div class="score-item-header">
                        <h4>Estrutura e Clareza</h4>
                        <span class="score-item-value">{{ (analysis.radar_data.estrutura * 5)|int }}/100</span>
                    </div>
                    <p class="score-item-analysis">{{ analysis.content_structure_analysis.organization_hierarchy_signal }}</p>
                    <p class="score-item-focus"><strong>Foco de Melhoria:</strong> {{ analysis.content_structure_analysis.organization_hierarchy_missing }}</p>
                </div>
                <div class="score-item">
                    <div class="score-item-header">
                        <h4>Conteúdo e Relevância</h4>
                        <span class="score-item-value">{{ (analysis.radar_data.conteudo * 5)|int }}/100</span>
                    </div>
                    <p class="score-item-analysis">{{ analysis.content_structure_analysis.responsibilities_results_balance_signal }}</p>
                    <p class="score-item-focus"><strong>Foco de Melhoria:</strong> {{ analysis.content_structure_analysis.responsibilities_results_balance_missing }}</p>
                </div>
                <div class="score-item">
                    <div class="score-item-header">
                        <h4>Compatibilidade ATS</h4>
                        <span class="score-item-value">{{ (analysis.radar_data.ats * 5)|int }}/100</span>
                    </div>
                    <p class="score-item-analysis">{{ analysis.ats_digital_recruitment.compatibility_signal }}</p>
                    <p class="score-item-focus"><strong>Foco de Melhoria:</strong> {{ analysis.ats_digital_recruitment.compatibility_missing }}</p>
                </div>
                <div class="score-item">
                    <div class="score-item-header">
                        <h4>Impacto e Resultados</h4>
                        <span class="score-item-value">{{ (analysis.radar_data.impacto * 5)|int }}/100</span>
                    </div>
                    <p class="score-item-analysis">{{ analysis.diagnostic_impact.impact_strengths_signal }}</p>
                    <p class="score-item-focus"><strong>Foco de Melhoria:</strong> {{ analysis.diagnostic_impact.impact_strengths_missing }}</p>
                </div>
                <div class="score-item">
                    <div class="score-item-header">
                        <h4>Marca Pessoal e Proposta de Valor</h4>
                        <span class="score-item-value">{{ (analysis.radar_data.branding * 5)|int }}/100</span>
                    </div>
                    <p class="score-item-analysis">{{ analysis.skills_differentiation.differentiation_factors_signal }}</p>
                    <p class="score-item-focus"><strong>Foco de Melhoria:</strong> {{ analysis.skills_differentiation.differentiation_factors_missing }}</p>
                </div>
                <div class="score-item">
                    <div class="score-item-header">
                        <h4>Riscos e Inconsistências</h4>
                        <span class="score-item-value">{{ (analysis.radar_data.riscos * 5)|int }}/100</span>
                    </div>
                    <p class="score-item-analysis">{{ analysis.strategic_risks.identified_risks_signal }}</p>
                    <p class="score-item-focus"><strong>Foco de Melhoria:</strong> {{ analysis.strategic_risks.identified_risks_missing }}</p>
                </div>
            </div>

            <!-- DIAGNÓSTICO DE IMPACTO -->
            <div class="consulting-block">
                <h2>Diagnóstico de Impacto Profissional</h2>
                <h3>Leitura em 30 Segundos por um Recrutador Sénior</h3>
                <p>{{ analysis.diagnostic_impact.first_30_seconds_read }}</p>
                <h3>Pontos Fortes de Impacto</h3>
                <p>{{ analysis.diagnostic_impact.impact_strengths }}</p>
                <h3>Pontos de Diluição de Impacto</h3>
                <p>{{ analysis.diagnostic_impact.impact_dilutions }}</p>
            </div>

            <!-- ANÁLISE DE CONTEÚDO E ESTRUTURA -->
            <div class="consulting-block">
                <h2>Análise de Conteúdo e Estrutura</h2>
                <h3>Organização e Hierarquia da Informação</h3>
                <p>{{ analysis.content_structure_analysis.organization_hierarchy }}</p>
                <h3>Equilíbrio entre Responsabilidades e Resultados</h3>
                <p>{{ analysis.content_structure_analysis.responsibilities_results_balance }}</p>
                <h3>Orientação do Currículo</h3>
                <p>{{ analysis.content_structure_analysis.orientation }}</p>
            </div>

            <!-- ANÁLISE ATS E RECRUTAMENTO DIGITAL -->
            <div class="consulting-block">
                <h2>Análise ATS e Recrutamento Digital</h2>
                <h3>Compatibilidade com Sistemas ATS</h3>
                <p>{{ analysis.ats_digital_recruitment.compatibility }}</p>
                <h3>Riscos de Filtragem Automática</h3>
                <p>{{ analysis.ats_digital_recruitment.filtering_risks }}</p>
                <h3>Alinhamento com Práticas de Recrutamento</h3>
                <p>{{ analysis.ats_digital_recruitment.alignment }}</p>
            </div>
            
            <!-- COMO MELHORAR AS TUAS FRASES -->
            <div class="consulting-block">
                <h2>Como Melhorar as Tuas Frases</h2>
                {% for item in analysis.pdf_extended_content.phrase_improvements %}
                <div class="before-after-block">
                    <div class="ba-label before-label">Antes (Original)</div>
                    <p class="ba-text">"{{ item.original }}"</p>
                    
                    <div class="ba-label after-label">Depois (Melhorado)</div>
                    <p class="ba-text">"{{ item.improved }}"</p>

                    <h3>Porquê esta mudança?</h3>
                    <p>{{ item.explanation }}</p>
                </div>
                {% endfor %}
            </div>

            <!-- RECOMENDAÇÕES PRIORITÁRIAS -->
            <div class="consulting-block">
                <h2>Recomendações Prioritárias</h2>
                <h3>Ajustes Imediatos</h3>
                <p>{{ analysis.priority_recommendations.immediate_adjustments }}</p>
                <h3>Áreas de Refinamento</h3>
                <p>{{ analysis.priority_recommendations.refinement_areas }}</p>
                <h3>Reposicionamento Profundo</h3>
                <p>{{ analysis.priority_recommendations.deep_repositioning }}</p>
            </div>

            <!-- CONCLUSÃO EXECUTIVA -->
            <div class="consulting-block">
                <h2>Conclusão Executiva</h2>
                <h3>Potencial Após Melhorias</h3>
                <p>{{ analysis.executive_conclusion.potential_after_improvements }}</p>
                <h3>Competitividade Esperada</h3>
                <p>{{ analysis.executive_conclusion.expected_competitiveness }}</p>
            </div>

            <!-- PRÓXIMOS PASSOS -->
            <div class="next-steps-container">
                <h2>A tua jornada para uma carreira de impacto continua aqui.</h2>
                <div class="services-grid">
                    <div class="service-block">
                        <h4>Kickstart Pro</h4>
                        <p>Sessão estratégica de 1h para decisões críticas de carreira.</p>
                    </div>
                    <div class="service-block">
                        <h4>Revisão de CV</h4>
                        <p>Feedback humano especializado com reescrita completa.</p>
                    </div>
                    <div class="service-block">
                        <h4>CV Analyzer</h4>
                        <p>Novos diagnósticos após implementares as melhorias.</p>
                    </div>
                </div>
            </div>

            <!-- FOOTER -->
            <div id="footer_content" class="footer">
                Share2Inspire | Relatório de Análise de CV | Confidencial
            </div>

        </body>
        </html>
        """

    def create_pdf(self, analysis_data, radar_chart_path):
        """Gera o PDF a partir dos dados de análise e do gráfico de radar."""
        if not analysis_data or 'candidate_profile' not in analysis_data:
            raise ValueError("Dados de análise inválidos ou incompletos.")

        # Calcular score geral
        radar_data = analysis_data.get('radar_data', {})
        overall_score = sum(radar_data.values()) / len(radar_data) * 5 if radar_data else 0
        
        # Gerar scorecard circular
        scorecard_svg = self.generate_scorecard_circular(overall_score)
        import base64
        scorecard_path = f"data:image/svg+xml;base64,{base64.b64encode(scorecard_svg.encode()).decode()}"

        template = Template(self.template_html)
        candidate_name = analysis_data.get('candidate_profile', {}).get('detected_name', 'Candidato')
        date_formatted = datetime.datetime.now().strftime("%d.%m.%Y")
        html = template.render(
            analysis=analysis_data, 
            radar_chart_path=radar_chart_path, 
            scorecard_path=scorecard_path, 
            now=datetime.datetime.now(),
            candidate_name=candidate_name,
            date_formatted=date_formatted
        )

        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html), dest=pdf_buffer)

        if pisa_status.err:
            raise Exception(f"Erro ao gerar PDF: {pisa_status.err}")

        pdf_buffer.seek(0)
        return pdf_buffer, f"Relatorio_Analise_CV_{analysis_data['candidate_profile']['detected_name'].replace(' ', '_')}.pdf"

    def generate_scorecard_circular(self, overall_score):
        """Gera um scorecard circular SVG com o score total no limite dourado."""
        
        size = 280
        center = size / 2
        radius = center * 0.75
        
        # Ângulo do score (0-360 graus, começando no topo)
        angle_percent = overall_score / 100.0
        angle_rad = (angle_percent * 360 - 90) * (3.14159 / 180)
        
        # Ponto final do arco
        end_x = center + radius * (3.14159 / 180) * angle_percent * 360
        end_y = center + radius * (3.14159 / 180) * angle_percent * 360
        
        svg = f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">'
        svg += f'<rect width="100%" height="100%" fill="#FFFFFF"/>'
        
        # Círculo de fundo (cinza claro)
        svg += f'<circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="#e9ecef" stroke-width="12"/>'
        
        # Arco de progresso (dourado)
        # Usar SVG path para desenhar o arco
        large_arc = 1 if angle_percent > 0.5 else 0
        end_x = center + radius * (3.14159 / 180) * (angle_percent * 360 - 90)
        end_y = center + radius * (3.14159 / 180) * (angle_percent * 360 - 90)
        
        # Simplificado: usar um arco circular
        svg += f'<circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="#BF9A33" stroke-width="12" stroke-dasharray="{radius * 2 * 3.14159 * angle_percent} {radius * 2 * 3.14159}" stroke-dashoffset="0" stroke-linecap="round" transform="rotate(-90 {center} {center})"/>'
        
        # Círculo interior branco
        svg += f'<circle cx="{center}" cy="{center}" r="{radius * 0.65}" fill="#FFFFFF"/>'
        
        # Score no centro
        svg += f'<text x="{center}" y="{center - 20}" font-family="Helvetica" font-size="48" fill="#BF9A33" text-anchor="middle" font-weight="700">{int(overall_score)}</text>'
        svg += f'<text x="{center}" y="{center + 15}" font-family="Helvetica" font-size="14" fill="#495057" text-anchor="middle">/100</text>'
        
        # Etiqueta
        svg += f'<text x="{center}" y="{center + 50}" font-family="Helvetica" font-size="11" fill="#212529" text-anchor="middle" font-weight="600">SCORE GERAL</text>'
        
        svg += '</svg>'
        return svg

    def generate_bar_chart(self, radar_data):
        """Gera um gráfico de barras horizontais SVG com escala 0-100.
        Barra cinza = 100 (máximo)
        Barra dourada = score do candidato (0-100)"""
        
        label_mapping = {
            'estrutura': 'Estrutura & Clareza',
            'conteudo': 'Conteúdo & Relevância',
            'ats': 'Compatibilidade ATS',
            'impacto': 'Impacto & Resultados',
            'branding': 'Marca Pessoal',
            'riscos': 'Riscos & Inconsistências'
        }
        
        labels = [label_mapping.get(k, k.capitalize()) for k in radar_data.keys()]
        values = [v * 5 for v in radar_data.values()]  # Converter 0-20 para 0-100
        num_bars = len(labels)

        svg_width = 700
        svg_height = 40 + (num_bars * 50)
        bar_height = 32
        margin_left = 180
        margin_right = 50
        max_value = 100

        svg = f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">'
        svg += f'<rect width="100%" height="100%" fill="#FFFFFF"/>'

        # Dimensão total da barra (sempre 100)
        total_bar_width = svg_width - margin_left - margin_right

        for i, (label, value) in enumerate(zip(labels, values)):
            y_pos = 20 + (i * 50)
            
            # Barra de fundo cinza (sempre 100)
            svg += f'<rect x="{margin_left}" y="{y_pos}" width="{total_bar_width}" height="{bar_height}" fill="#e9ecef" rx="4"/>'

            # Barra dourada (score do candidato, proporcional)
            score_bar_width = (total_bar_width / 100) * value
            svg += f'<rect x="{margin_left}" y="{y_pos}" width="{score_bar_width}" height="{bar_height}" fill="#BF9A33" rx="4"/>'

            # Rótulo da barra
            svg += f'<text x="{margin_left - 10}" y="{y_pos + bar_height / 2 + 5}" font-family="Helvetica" font-size="12" fill="#212529" text-anchor="end" font-weight="600">{label}</text>'

            # Valor numérico
            svg += f'<text x="{margin_left + total_bar_width + 10}" y="{y_pos + bar_height / 2 + 5}" font-family="Helvetica" font-size="12" fill="#BF9A33" font-weight="700">{int(value)}/100</text>'

        svg += '</svg>'
        return svg
