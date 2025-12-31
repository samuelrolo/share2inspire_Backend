# Email Templates Module

This module contains persistent transactional email templates for Share2Inspire platform.

## Structure

- `transactional_emails.py` - Core email template functions
- `PROMPT_BASE.md` - Quick reference for AI agents

## Usage

```python
from email_templates.transactional_emails import (
    get_email_confirmacao_pedido,
    get_email_pagamento_mbway,
    get_email_entrega_relatorio,
    get_email_followup_estrategico
)

# Example: Email 1
subject, body = get_email_confirmacao_pedido(
    nome="João Silva",
    nome_do_servico="CV Analyzer",
    data_pedido="27/12/2025"
)
```

## Important Rules

- Templates are independent of frontend HTML
- Only dynamic variables can be interpolated
- Do not modify content without approval
- These are the single source of truth for user communication
