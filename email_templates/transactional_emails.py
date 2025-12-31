"""
Share2Inspire Transactional Email Templates
Persistent email content independent of frontend HTML
"""

def get_email_confirmacao_pedido(nome, nome_do_servico, data_pedido):
    """
    EMAIL 1: Confirmação de Pedido
    Trigger: Submissão de pedido concluída com sucesso, antes de qualquer pagamento
    """
    subject = "Confirmámos o teu pedido | Share2Inspire"
    
    body = f"""
Olá {nome},

Obrigado por confiares na Share2Inspire.

Recebemos o teu pedido de {nome_do_servico} e estamos a preparar os próximos passos para avançarmos contigo de forma clara e estruturada.

Resumo do pedido
Serviço solicitado: {nome_do_servico}
Data do pedido: {data_pedido}

Em breve vais receber um novo email com as instruções seguintes, incluindo, quando aplicável, os detalhes para pagamento seguro via MB Way.

Até já,
Equipa Share2Inspire
Human Centred Career & Knowledge Platform
www.share2inspire.pt
"""
    return subject, body


def get_email_pagamento_mbway(nome, nome_do_servico, valor, prazo_entrega, link_pagamento_mbway):
    """
    EMAIL 2: Pagamento MB Way
    Trigger: Pedido validado e link MB Way gerado com sucesso via ifthenpay
    """
    subject = f"Pagamento MB Way | {nome_do_servico} | Share2Inspire"
    
    body = f"""
Olá {nome},

Para avançarmos com o teu pedido de {nome_do_servico}, precisamos agora da confirmação do pagamento.

Detalhes do serviço
Serviço: {nome_do_servico}
Valor: {valor}
Prazo estimado de entrega: {prazo_entrega}

Pagamento MB Way
Utiliza o link abaixo para pagar de forma simples e segura:

{link_pagamento_mbway}

Assim que o pagamento for confirmado, receberás automaticamente o email de entrega com os respetivos anexos.

Com estima,
Equipa Share2Inspire
www.share2inspire.pt
"""
    return subject, body


def get_email_entrega_relatorio(nome, nome_do_servico):
    """
    EMAIL 3: Entrega do Relatório
    Trigger: Confirmação de pagamento recebida com sucesso
    """
    subject = "O teu relatório está pronto | Share2Inspire"
    
    body = f"""
Olá {nome},

O teu pedido de {nome_do_servico} foi concluído com sucesso.

Em anexo encontras:

• O Relatório Completo de Análise de CV em PDF

• O CV original que carregaste no momento do pedido

O relatório inclui análise de posicionamento profissional, avaliação de maturidade e competências, pontos fortes diferenciadores, sugestões de evolução e próximos passos recomendados.

Este documento foi preparado para apoiar decisões conscientes sobre o teu percurso profissional.

Com estima,
Equipa Share2Inspire
www.share2inspire.pt
"""
    return subject, body


def get_email_followup_estrategico(nome):
    """
    EMAIL 4: Follow up Estratégico
    Trigger: 3 a 5 dias após envio do email de entrega do relatório
    """
    subject = "Próximo passo na tua evolução profissional"
    
    body = f"""
Olá {nome},

Esperamos que o relatório tenha sido útil e esclarecedor.

Muitos profissionais optam por complementar este diagnóstico com acompanhamento humano, transformando insights em decisões práticas e alinhadas com o mercado.

Se sentires que este é o momento certo para aprofundar, podes explorar os serviços disponíveis na Share2Inspire.

Estamos disponíveis para apoiar o próximo capítulo do teu percurso.

Com estima,
Equipa Share2Inspire
www.share2inspire.pt
"""
    return subject, body
