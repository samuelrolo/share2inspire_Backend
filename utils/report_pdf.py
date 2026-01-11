import io
import math
import datetime
import base64
import cairosvg
import tempfile
import os
from xhtml2pdf import pisa
from jinja2 import Template

class ReportPDFGenerator:
    """Gerador de relatórios PDF com design premium e análises aprofundadas."""
    
    def __init__(self):
        self.colors = {
            'gold': '#BF9A33',
            'black': '#1A1A1A',
            'gray_dark': '#333333',
            'gray_light': '#e9ecef',
            'white': '#FFFFFF',
        }
        with open("/home/ubuntu/share2inspire_Backend/utils/pdf_styles.css", "r") as f:
            self.css = f.read()

    def _svg_to_png_uri(self, svg_code):
        """Converte código SVG para um Data URI de PNG."""
        try:
            png_bytes = cairosvg.svg2png(bytestring=svg_code.encode('utf-8'))
            return f"data:image/png;base64,{base64.b64encode(png_bytes).decode('utf-8')}"
        except Exception as e:
            print(f"[ERRO] Falha na conversão de SVG para PNG: {e}")
            return ""

    def generate_circular_scorecard(self, score, size=180, label="SCORE GLOBAL"):
        # ... (código do scorecard SVG omitido para brevidade)
        svg = f"..."
        return self._svg_to_png_uri(svg)

    def generate_mini_scorecard(self, score, size=80):
        # ... (código do mini scorecard SVG omitido para brevidade)
        svg = f"..."
        return self._svg_to_png_uri(svg)

    def generate_progress_bar(self, label, value, max_value=100):
        # ... (código da barra de progresso SVG omitido para brevidade)
        svg = f"..."
        return self._svg_to_png_uri(svg)

    def _get_template(self):
        return f"""...""" # Template HTML omitido para brevidade

    def create_pdf(self, analysis_data, radar_chart_path=None):
        """Gera o PDF a partir dos dados de análise."""
        if not analysis_data or 'candidate_profile' not in analysis_data:
            raise ValueError("Dados de análise inválidos ou incompletos.")

        # ... (lógica de processamento de dados omitida para brevidade)

        template_vars = {
            'css': self.css,
            'analysis': analysis_data,
            # ... (outras variáveis do template)
        }

        # Gerar scorecards como PNGs
        template_vars['main_scorecard'] = self.generate_circular_scorecard(analysis_data.get('executive_summary', {}).get('global_score', 0))
        # ... (gerar outros scorecards e barras)

        # Adicionar gráfico radar se existir
        if radar_chart_path and os.path.exists(radar_chart_path):
            with open(radar_chart_path, "rb") as f:
                radar_b64 = base64.b64encode(f.read()).decode('utf-8')
                template_vars['radar_chart'] = f"data:image/png;base64,{radar_b64}"

        template = Template(self._get_template())
        html = template.render(template_vars)

        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html), dest=pdf_buffer)

        if pisa_status.err:
            raise Exception(f"Erro ao gerar PDF: {pisa_status.err}")

        pdf_buffer.seek(0)
        filename = f"Relatorio_Analise_CV_{analysis_data.get('candidate_profile', {}).get('detected_name', 'Candidato').replace(' ', '_')}.pdf"
        return pdf_buffer, filename
