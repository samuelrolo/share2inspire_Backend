"""
Share2Inspire Transactional Email Templates
Elegant HTML templates with Share2Inspire branding (Gold/Black/White)
"""

def get_base_template(content, title="Share2Inspire"):
    """
    Template base HTML elegante para todos os e-mails da Share2Inspire.
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #1A1A1A; margin: 0; padding: 0; background-color: #f9f9f9; }}
            .wrapper {{ width: 100%; background-color: #f9f9f9; padding: 40px 0; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .header {{ background-color: #1A1A1A; padding: 30px; text-align: center; }}
            .logo {{ color: #BF9A33; font-size: 24px; font-weight: bold; letter-spacing: 2px; text-transform: uppercase; text-decoration: none; }}
            .content {{ padding: 40px; }}
            .title {{ color: #1A1A1A; font-size: 22px; font-weight: 600; margin-bottom: 20px; border-bottom: 2px solid #BF9A33; padding-bottom: 10px; display: inline-block; }}
            .message {{ font-size: 16px; color: #444; margin-bottom: 30px; }}
            .details-box {{ background-color: #f8f8f8; border-left: 4px solid #BF9A33; padding: 20px; margin: 20px 0; border-radius: 0 4px 4px 0; }}
            .details-title {{ font-weight: bold; color: #1A1A1A; margin-bottom: 10px; text-transform: uppercase; font-size: 13px; letter-spacing: 1px; }}
            .button {{ display: inline-block; padding: 14px 30px; background-color: #BF9A33; color: #ffffff !important; text-decoration: none; border-radius: 4px; font-weight: bold; text-transform: uppercase; font-size: 14px; letter-spacing: 1px; margin-top: 10px; }}
            .footer {{ padding: 30px; text-align: center; font-size: 12px; color: #999; background-color: #f4f4f4; }}
            .footer a {{ color: #BF9A33; text-decoration: none; }}
            .highlight {{ color: #BF9A33; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="container">
                <div class="header">
                    <a href="https://www.share2inspire.pt" class="logo">Share2Inspire</a>
                </div>
                <div class="content">
                    <div class="title">{title}</div>
                    <div class="message">
                        {content}
                    </div>
                </div>
                <div class="footer">
                    <p>© 2026 Share2Inspire - Human Centred Career & Knowledge Platform</p>
                    <p><a href="https://www.share2inspire.pt">www.share2inspire.pt</a></p>
                    <p>Transformamos insights em decisões conscientes.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def get_email_confirmacao_pedido(nome, nome_do_servico, data_pedido):
    subject = "Confirmamos o seu pedido | Share2Inspire"
    content = f"""
    Olá <span class="highlight">{nome}</span>,<br><br>
    Obrigado por confiar na <strong>Share2Inspire</strong>.<br><br>
    Recebemos o teu pedido de <strong>{nome_do_servico}</strong> e estamos a preparar os próximos passos para avançarmos contigo de forma clara e estruturada.<br><br>
    <div class="details-box">
        <div class="details-title">Resumo do Pedido</div>
        <strong>Serviço:</strong> {nome_do_servico}<br>
        <strong>Data:</strong> {data_pedido}
    </div>
    Em breve vais receber um novo email com as instruções seguintes, incluindo os detalhes para o processamento do teu serviço.<br><br>
    Atenciosamente,<br>
    <strong>Equipa Share2Inspire</strong>
    """
    return subject, get_base_template(content, "Pedido Confirmado")

def get_email_pagamento_mbway(nome, nome_do_servico, valor, prazo_entrega, link_pagamento_mbway):
    subject = f"Pagamento MB Way | {nome_do_servico} | Share2Inspire"
    content = f"""
    Olá <span class="highlight">{nome}</span>,<br><br>
    Para avançarmos com o teu pedido de <strong>{nome_do_servico}</strong>, precisamos agora da confirmação do pagamento.<br><br>
    <div class="details-box">
        <div class="details-title">Detalhes do Serviço</div>
        <strong>Serviço:</strong> {nome_do_servico}<br>
        <strong>Valor:</strong> {valor}<br>
        <strong>Prazo de Entrega:</strong> {prazo_entrega}
    </div>
    <p>Utiliza o botão abaixo para efetuar o pagamento via MB Way de forma simples e segura:</p>
    <a href="{link_pagamento_mbway}" class="button">Pagar com MB Way</a><br><br>
    Assim que o pagamento for confirmado, receberás automaticamente o teu relatório.<br><br>
    Com estima,<br>
    <strong>Equipa Share2Inspire</strong>
    """
    return subject, get_base_template(content, "Pagamento Pendente")

def get_email_entrega_relatorio(nome, nome_do_servico):
    subject = "O teu relatório está pronto | Share2Inspire"
    content = f"""
    Olá <span class="highlight">{nome}</span>,<br><br>
    O teu pedido de <strong>{nome_do_servico}</strong> foi concluído com sucesso.<br><br>
    O teu relatório completo de análise está pronto para consulta. Este documento foi preparado para apoiar decisões conscientes sobre o teu percurso profissional, incluindo:<br><br>
    • Análise de posicionamento profissional<br>
    • Avaliação de maturidade e competências<br>
    • Pontos fortes diferenciadores e sugestões de evolução<br><br>
    Podes aceder ao teu relatório através do anexo deste e-mail.<br><br>
    Com estima,<br>
    <strong>Equipa Share2Inspire</strong>
    """
    return subject, get_base_template(content, "Relatório Disponível")

def get_email_followup_estrategico(nome):
    subject = "Próximo passo na tua evolução profissional"
    content = f"""
    Olá <span class="highlight">{nome}</span>,<br><br>
    Esperamos que o relatório tenha sido útil e esclarecedor para o teu percurso.<br><br>
    Muitos profissionais optam por complementar este diagnóstico com <strong>acompanhamento humano</strong>, transformando insights em decisões práticas e alinhadas com o mercado.<br><br>
    Se sentires que este é o momento certo para aprofundar a tua estratégia, estamos disponíveis para apoiar o próximo capítulo da tua carreira.<br><br>
    <a href="https://www.share2inspire.pt/servicos" class="button">Explorar Serviços</a><br><br>
    Com estima,<br>
    <strong>Equipa Share2Inspire</strong>
    """
    return subject, get_base_template(content, "Evolução Contínua")

def get_email_confirmacao_consulta(nome, assunto):
    subject = "Confirmação do seu Pedido de Consulta | Share2Inspire"
    content = f"""
    Olá <span class="highlight">{nome}</span>,<br><br>
    Recebemos o seu pedido de consulta sobre "<strong>{assunto}</strong>".<br><br>
    A nossa equipa irá analisar a sua mensagem e entrará em contacto o mais breve possível.<br><br>
    <div class="details-box">
        <div class="details-title">Próximos Passos</div>
        A nossa equipa de desenvolvimento irá rever o seu pedido e responder com uma proposta personalizada nas próximas 48 horas úteis.
    </div>
    Obrigado pelo seu interesse nos nossos serviços!<br><br>
    Atenciosamente,<br>
    <strong>Equipa Share2Inspire</strong>
    """
    return subject, get_base_template(content, "Pedido de Consulta Recebido")
