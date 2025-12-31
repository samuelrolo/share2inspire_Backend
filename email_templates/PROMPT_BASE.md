# Share2Inspire Email Templates - Prompt Base

Guardar este contexto permanentemente para referência do agente.

## Emails Transacionais Persistentes

**EMAIL 1 - Confirmação de Pedido**
- Trigger: Após submissão, antes de pagamento
- Assunto: "Confirmámos o teu pedido | Share2Inspire"
- Variáveis: nome, nome_do_servico, data_pedido

**EMAIL 2 - Pagamento MB Way**
- Trigger: Link MB Way gerado
- Assunto: "Pagamento MB Way | {{nome_do_servico}} | Share2Inspire"
- Variáveis: nome, nome_do_servico, valor, prazo_entrega, link_pagamento_mbway

**EMAIL 3 - Entrega do Relatório**
- Trigger: Pagamento confirmado
- Assunto: "O teu relatório está pronto | Share2Inspire"
- Variáveis: nome, nome_do_servico
- Anexos: Relatório PDF + CV original

**EMAIL 4 - Follow up Estratégico**
- Trigger: 3-5 dias após entrega
- Assunto: "Próximo passo na tua evolução profissional"
- Variáveis: nome

**REGRAS CRÍTICAS**:
- Emails residem em `email_templates/transactional_emails.py`
- Independentes do frontend HTML
- Apenas 4 emails, sem duplicação
- Ordem específica conforme triggers
- Templates são fonte única de verdade

**LOCALIZAÇÃO**: `share2inspire_Backend/email_templates/transactional_emails.py`
