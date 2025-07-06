# -*- coding: utf-8 -*-
"""
Pacote de rotas do Share2Inspire Backend
Este ficheiro torna a pasta 'routes' um pacote Python válido
"""

# Importações opcionais para facilitar o acesso aos blueprints
try:
    from .feedback import feedback_bp
except ImportError:
    feedback_bp = None

try:
    from .payment import payment_bp
except ImportError:
    payment_bp = None

try:
    from .ifthenpay import ifthenpay_bp
except ImportError:
    ifthenpay_bp = None

try:
    from .email import email_bp
except ImportError:
    email_bp = None

try:
    from .user import user_bp
except ImportError:
    user_bp = None

__all__ = ['feedback_bp', 'payment_bp', 'ifthenpay_bp', 'email_bp', 'user_bp']

