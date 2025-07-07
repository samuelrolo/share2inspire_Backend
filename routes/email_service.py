#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serviço de Email para Share2Inspire - VERSÃO CORRIGIDA
Integra as funcionalidades de envio de email através de rotas HTTP
E-MAIL CORRIGIDO: share2inspire@gmail.com
"""

import os
import json
import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Criar blueprint
email_bp = Blueprint('email', __name__)

# Configuração da API Brevo (Sendinblue)
configuration = sib_api_v3_sdk.Configuration()
api_key = os.getenv("BREVO_API_KEY")
configuration.api_key["api-key"] = api_key

# Verificar se a chave API foi carregada
if not api_key:
    logger.error("ALERTA: A variável de ambiente BREVO_API_KEY não está definida!")
else:
    logger.info("Chave API Brevo configurada com sucesso")

# Email do remetente verificado na Brevo - E-MAIL CORRIGIDO
VERIFIED_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "share2inspire@gmail.com")
VERIFIED_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "Share2Inspire")

# Email do destinatário (admin) - E-MAIL CORRIGIDO
ADMIN_EMAIL = "share2inspire@gmail.com"
ADMIN_NAME = "Share2Inspire Admin"

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

def send_booking_confirmation_email(data):
    """
    Função principal para envio de emails de confirmação de reservas