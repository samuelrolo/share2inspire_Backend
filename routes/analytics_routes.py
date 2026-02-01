# -*- coding: utf-8 -*-
"""
Rotas de Analytics para CV Analyzer - Share2Inspire
API endpoints para consulta de estatísticas
"""

from datetime import datetime
from flask import Blueprint, jsonify, request
from utils.analytics import analytics

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/api/analytics/summary', methods=['GET'])
def get_summary():
    """
    Endpoint para obter estatísticas resumidas.
    
    Returns:
        JSON com estatísticas agregadas:
        - total_analyses: Total de análises
        - paid_analyses: Análises pagas
        - free_analyses: Análises gratuitas
        - total_revenue: Receita total
        - last_24h: Análises nas últimas 24h
        - last_7_days: Análises nos últimos 7 dias
        - last_30_days: Análises nos últimos 30 dias
        - avg_score: Pontuação média
    """
    result = analytics.get_summary_stats()
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": result["stats"]
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "Erro desconhecido")
        }), 500


@analytics_bp.route('/api/analytics/daily', methods=['GET'])
def get_daily():
    """
    Endpoint para obter estatísticas diárias.
    
    Query params:
        days: Número de dias para trás (default: 30)
    
    Returns:
        JSON com lista de estatísticas por dia
    """
    days = request.args.get('days', 30, type=int)
    result = analytics.get_daily_stats(days_back=days)
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": result["data"]
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "Erro desconhecido")
        }), 500


@analytics_bp.route('/api/analytics/areas', methods=['GET'])
def get_areas():
    """
    Endpoint para obter estatísticas por área profissional.
    
    Returns:
        JSON com lista de áreas e contagens
    """
    result = analytics.get_area_stats()
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": result["data"]
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "Erro desconhecido")
        }), 500


@analytics_bp.route('/api/analytics/recent', methods=['GET'])
def get_recent():
    """
    Endpoint para obter análises recentes.
    
    Query params:
        limit: Número máximo de registos (default: 10)
    
    Returns:
        JSON com lista de análises recentes
    """
    limit = request.args.get('limit', 10, type=int)
    result = analytics.get_recent_analyses(limit=limit)
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": result["data"]
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "Erro desconhecido")
        }), 500


@analytics_bp.route('/api/analytics/count', methods=['GET'])
def get_count():
    """
    Endpoint para contador em tempo real (para landing page).
    
    Returns:
        JSON com contagem total formatada
    """
    result = analytics.get_live_count()
    
    return jsonify({
        "success": True,
        "total": result.get("total_analyses", 0),
        "display": result.get("display_count", "0")
    }), 200


@analytics_bp.route('/api/analytics/webhook-leads', methods=['POST'])
def google_ads_webhook():
    """
    Webhook para receber leads do Google Ads.
    """
    # Verificar chave de segurança (opcional mas recomendado)
    google_key = request.args.get('key')
    expected_key = "s2i_google_ads_2026_secure"
    
    if google_key != expected_key:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data received"}), 400
        
    # Mapear campos do Google Ads (exemplo baseado na estrutura padrão)
    # O Google envia uma lista de user_column_data
    user_data = {}
    for column in data.get('user_column_data', []):
        column_id = column.get('column_id')
        column_value = column.get('string_value')
        
        if column_id == 'EMAIL':
            user_data['user_email'] = column_value
        elif column_id == 'FULL_NAME':
            user_data['user_name'] = column_value
        elif column_id == 'PHONE_NUMBER':
            user_data['user_phone'] = column_value
            
    lead_entry = {
        "lead_id": data.get('lead_id'),
        "user_email": user_data.get('user_email'),
        "user_name": user_data.get('user_name'),
        "user_phone": user_data.get('user_phone'),
        "campaign_id": data.get('campaign_id'),
        "adgroup_id": data.get('adgroup_id'),
        "creative_id": data.get('creative_id'),
        "raw_data": data,
        "created_at": datetime.utcnow().isoformat()
    }
    
    result = analytics.log_google_ads_lead(lead_entry)
    
    if result["success"]:
        return jsonify({"success": True, "message": "Lead registered"}), 200
    else:
        return jsonify({"success": False, "error": result.get("error")}), 500


# CORS headers para todos os endpoints
@analytics_bp.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response
