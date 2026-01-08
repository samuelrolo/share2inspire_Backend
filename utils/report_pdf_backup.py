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
                    margin: 1.5cm;
                    @frame footer_frame {
                        -pdf-frame-content: footer_content;
                        left: 1.5cm; width: 18cm; top: 27.5cm; height: 1cm;
                    }
                }
                body {
                    font-family: Helvetica, Arial, sans-serif;
                    color: #212529;
                    line-height: 1.6;
                    font-size: 10pt;
                }
                .text-gold { color: #BF9A33; }
                .bg-gold { background-color: #BF9A33; }
                .text-muted { color: #6c757d; }
                
                h1, h2, h3, h4 { color: #212529; margin-bottom: 8pt; }
                
                .cover { text-align: center; margin-top: 3cm; position: relative; }
                .cover-logo { margin-bottom: 2cm; }
                .cover-title { font-size: 28pt; font-weight: bold; margin-bottom: 10pt; color: #212529; }
                .cover-subtitle { font-size: 16pt; color: #BF9A33; text-transform: uppercase; letter-spacing: 2pt; margin-bottom: 3cm; }
                .cover-candidate { font-size: 20pt; font-weight: bold; margin-bottom: 10pt; }
                .cover-info { font-size: 11pt; color: #6c757d; margin-top: 2cm; }
                .report-id { font-family: monospace; font-size: 9pt; color: #999; margin-top: 5pt; }
                
                .page-break { -pdf-next-page: true; }
                
                .section-title {
                    font-size: 16pt; font-weight: bold; text-transform: uppercase;
                    border-left: 5pt solid #BF9A33; padding-left: 12pt;
                    margin-top: 40pt; margin-bottom: 20pt;
                    background-color: #f8f9fa; padding-top: 5pt; padding-bottom: 5pt;
                }
                
                .profile-grid { background-color: #f8f9fa; padding: 20pt; border-radius: 8pt; border: 1pt solid #dee2e6; margin-bottom: 20pt; }
                .profile-item { margin-bottom: 8pt; }
                .profile-label { font-weight: bold; color: #BF9A33; text-transform: uppercase; font-size: 8pt; margin-bottom: 2pt; }
                .profile-value { font-size: 12pt; color: #212529; }
                
                .maturity-box { text-align: center; padding: 15pt; border: 2pt solid #BF9A33; border-radius: 10pt; width: 4cm; margin: 0 auto; }
                .maturity-label { font-size: 8pt; font-weight: bold; color: #6c757d; }
                .maturity-score { font-size: 24pt; font-weight: bold; color: #BF9A33; }
                
                .strategic-bullet { border-left: 3pt solid #BF9A33; padding-left: 15pt; margin-bottom: 25pt; page-break-inside: avoid; }
                .sb-title { font-weight: bold; font-size: 12pt; margin-bottom: 2pt; }
                .sb-metric { color: #BF9A33; font-size: 9pt; font-weight: bold; text-transform: uppercase; margin-bottom: 4pt; }
                .sb-detail { font-size: 10pt; color: #444; text-align: justify; }
                
                .radar-container { text-align: center; margin: 30pt 0; background-color: #fff; padding: 20pt; border-radius: 10pt; }
                
                .recommendation-box { background-color: #fff; border: 1pt solid #dee2e6; padding: 15pt; margin-bottom: 15pt; border-radius: 8pt; }
                .rec-title { font-weight: bold; color: #BF9A33; margin-bottom: 8pt; border-bottom: 1pt solid #eee; padding-bottom: 5pt; font-size: 11pt; }
                .rec-content { font-size: 10pt; color: #444; }
                
                .footer { font-size: 8pt; color: #adb5bd; text-align: center; border-top: 0.5pt solid #dee2e6; padding-top: 5pt; }
                
                ul { padding-left: 15pt; }
                li { margin-bottom: 5pt; }
            </style>
        </head>
        <body>
            <div id="footer_content" class="footer">
                Relatório de Análise de CV - Share2Inspire | Privado e Confidencial | {{ report_id }}
            </div>

            <!-- CAPA -->
            <div class="cover">
                <div class="cover-logo">
                    <img src="https://share2inspire.pt/images/logo.png" width="180" />
                </div>
                <div class="cover-subtitle">Posicionamento de Carreira</div>
                <h1 class="cover-title">RELATÓRIO DE ANÁLISE DE CV</h1>
                
                <div style="margin-top: 2cm;">
                    <div class="cover-candidate">{{ report.candidate_profile.detected_name }}</div>
                    <div class="report-id">ID: {{ report_id }}</div>
                </div>

                <div class="cover-info">
                    Gerado em: {{ generation_date }}<br>
                    <strong>Share2Inspire - Estratégia e Narrativa de Impacto</strong>
                </div>
            </div>

            <div class="page-break"></div>

            <!-- VISÃO GERAL -->
            <div class="section-title">Visão Geral e Maturidade</div>
            <div class="profile-grid">
                <table width="100%">
                    <tr>
                        <td width="50%">
                            <div class="profile-item">
                                <div class="profile-label">Candidato</div>
                                <div class="profile-value">{{ report.candidate_profile.detected_name }}</div>
                            </div>
                            <div class="profile-item">
                                <div class="profile-label">Função Identificada</div>
                                <div class="profile-value">{{ report.candidate_profile.detected_role }}</div>
                            </div>
                        </td>
                        <td width="50%">
                            <div class="profile-item">
                                <div class="profile-label">Experiência</div>
                                <div class="profile-value">{{ report.candidate_profile.total_years_exp }}</div>
                            </div>
                            <div class="profile-item">
                                <div class="profile-label">Senioridade</div>
                                <div class="profile-value">{{ report.candidate_profile.seniority }}</div>
                            </div>
                        </td>
                    </tr>
                </table>
                <div style="margin-top: 20pt;">
                    <div class="maturity-box">
                        <div class="maturity-label">MATURIDADE</div>
                        <div class="maturity-score">{{ (report.final_verdict.score / 20) | round(1) }} <span style="font-size: 10pt; color: #999;">/ 5</span></div>
                    </div>
                </div>
            </div>

            <!-- COMPETÊNCIAS -->
            <div class="section-title">Domínios e Competências</div>
            {% for item in report.maturity_and_skills %}
            <div class="strategic-bullet">
                <div class="sb-title">{{ item.title }}</div>
                <div class="sb-metric">{{ item.metric }}</div>
                <div class="sb-detail">{{ item.detail }}</div>
            </div>
            {% endfor %}

            <div class="page-break"></div>

            <!-- PONTOS FORTES -->
            <div class="section-title">Pontos Fortes e Diferenciadores</div>
            <div style="margin-bottom: 20pt;">
                {% for item in report.key_strengths %}
                <div class="strategic-bullet">
                    <div class="sb-title">{{ item.title }}</div>
                    <div class="sb-metric">{{ item.metric }}</div>
                    <div class="sb-detail">{{ item.detail }}</div>
                </div>
                {% endfor %}
            </div>

            <!-- RADAR DE PERFORMANCE -->
            <div class="section-title">Radar de Inteligência</div>
            <div class="radar-container">
                {{ radar_svg | safe }}
                <p class="text-muted" style="font-size: 8pt; margin-top: 10pt;">Visualização técnica do equilíbrio entre dimensões estratégicas.</p>
            </div>

            <div class="page-break"></div>

            <!-- RECOMENDAÇÕES -->
            <div class="section-title">Recomendações Estratégicas</div>
            
            <div class="recommendation-box">
                <div class="rec-title">O que reforçar (Aumentar Impacto)</div>
                <div class="rec-content">
                    {{ report.strategic_feedback.pdf_details.what_to_reinforce }}
                </div>
            </div>

            <div class="recommendation-box">
                <div class="rec-title">O que ajustar já (Correção Imediata)</div>
                <div class="rec-content">
                    {{ report.strategic_feedback.pdf_details.what_to_adjust }}
                </div>
            </div>

            <div style="margin-top: 20pt;">
                <h4 class="text-gold">Plano de Evolução</h4>
                {% for item in report.evolution_roadmap.pdf_details %}
                <div style="margin-bottom: 15pt;">
                    <div style="font-weight: bold; margin-bottom: 3pt;">{{ item.title }}</div>
                    <ul style="font-size: 9pt;">
                        {% for action in item.actions %}
                        <li>{{ action }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endfor %}
            </div>

            <div class="page-break"></div>

            <!-- PRÓXIMOS PASSOS -->
            <div class="section-title">Próximos Passos</div>
            <div style="margin-top: 1cm;">
                <p style="font-size: 12pt; text-align: center; margin-bottom: 40pt;">
                    A sua jornada para uma carreira de impacto continua aqui.
                </p>
                
                <table width="100%" cellpadding="10">
                    <tr>
                        <td width="33%" style="background-color: #f8f9fa; border-radius: 8pt; text-align: center;">
                            <div style="font-weight: bold; color: #BF9A33; margin-bottom: 5pt;">Kickstart Pro</div>
                            <div style="font-size: 8pt; color: #666;">Sessão estratégica de 1h para decisões críticas.</div>
                        </td>
                        <td width="33%" style="background-color: #f8f9fa; border-radius: 8pt; text-align: center;">
                            <div style="font-weight: bold; color: #BF9A33; margin-bottom: 5pt;">Revisão de CV</div>
                            <div style="font-size: 8pt; color: #666;">Feedback humano especializado detalhado.</div>
                        </td>
                        <td width="33%" style="background-color: #f8f9fa; border-radius: 8pt; text-align: center;">
                            <div style="font-weight: bold; color: #BF9A33; margin-bottom: 5pt;">CV Analyzer</div>
                            <div style="font-size: 8pt; color: #666;">Novos diagnósticos de mercado e fit.</div>
                        </td>
                    </tr>
                </table>

                <div style="text-align: center; margin-top: 4cm;">
                    <img src="https://share2inspire.pt/images/logo.png" width="120" /><br>
                    <div style="font-size: 9pt; color: #999; margin-top: 10pt;">
                        Carreira com clareza, estratégia e narrativa de impacto.<br>
                        www.share2inspire.pt | srshare2inspire@gmail.com
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    def generate_radar_svg(self, data):
        """Generates a premium SVG radar chart."""
        labels = ['ATS', 'Impacto', 'Estrutura', 'Fit', 'Prontidão']
        values = [data.get(k, 0) for k in ['ats', 'impact', 'structure', 'market_fit', 'readiness']]
        
        size = 350
        center = size / 2
        radius = size * 0.35
        num_points = len(labels)
        
        svg = f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">'
        
        # Grid polygons (hexagons)
        for r in [0.2, 0.4, 0.6, 0.8, 1.0]:
            grid_points = []
            for i in range(num_points):
                angle = (math.pi * 2 * i / num_points) - (math.pi / 2)
                x = center + radius * r * math.cos(angle)
                y = center + radius * r * math.sin(angle)
                grid_points.append(f"{x},{y}")
            svg += f'<polygon points="{" ".join(grid_points)}" fill="none" stroke="#eee" stroke-width="0.5" />'
        
        # Axis lines
        points = []
        for i in range(num_points):
            angle = (math.pi * 2 * i / num_points) - (math.pi / 2)
            x_end = center + radius * math.cos(angle)
            y_end = center + radius * math.sin(angle)
            svg += f'<line x1="{center}" y1="{center}" x2="{x_end}" y2="{y_end}" stroke="#eee" stroke-width="0.5" />'
            
            lx = center + (radius + 25) * math.cos(angle)
            ly = center + (radius + 25) * math.sin(angle)
            svg += f'<text x="{lx}" y="{ly}" text-anchor="middle" dominant-baseline="middle" font-size="10" font-family="Arial" font-weight="bold" fill="#666">{labels[i]}</text>'
            
            val_radius = radius * (max(min(values[i], 100), 10) / 100)
            dx = center + val_radius * math.cos(angle)
            dy = center + val_radius * math.sin(angle)
            points.append(f"{dx},{dy}")
        
        svg += f'<polygon points="{" ".join(points)}" fill="rgba(191, 154, 51, 0.3)" stroke="#BF9A33" stroke-width="2" />'
        for p in points:
            px, py = p.split(',')
            svg += f'<circle cx="{px}" cy="{py}" r="3" fill="#BF9A33" />'
            
        svg += '</svg>'
        return svg

    def create_pdf(self, report_data):
        """Generates the PDF bytes and checks the checklist."""
        radar_svg = self.generate_radar_svg(report_data.get('radar_data', {}))
        
        # Generate ID and Date
        now = datetime.datetime.now()
        report_id = f"CVA {now.strftime('%Y %m %d %H %M')}"
        gen_date = now.strftime('%d/%m/%Y %H:%M')
        
        tm = Template(self.template_html)
        html_content = tm.render(
            report=report_data, 
            radar_svg=radar_svg, 
            report_id=report_id,
            generation_date=gen_date
        )
        
        result_bytes = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=result_bytes, encoding='utf-8')
        
        if pisa_status.err:
            return None, "Erro na geração do PDF"
            
        pdf_content = result_bytes.getvalue()
        
        # VALIDATION CHECKLIST
        # 1. Size > 50KB
        size_kb = len(pdf_content) / 1024
        if size_kb < 50:
             return pdf_content, f"PDF demasiado pequeno ({size_kb:.1f}KB). Mínimo 50KB."
             
        # 2. Pages >= 5
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            pages = len(reader.pages)
            if pages < 5:
                return pdf_content, f"PDF tem apenas {pages} páginas. Mínimo 5."
        except Exception as e:
            return pdf_content, f"Erro ao validar páginas: {str(e)}"

        return pdf_content, "OK"
