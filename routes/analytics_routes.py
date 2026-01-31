# -*- coding: utf-8 -*-
"""
Rotas de Analytics para CV Analyzer - Share2Inspire
API endpoints para consulta de estatísticas
"""

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


# CORS headers para todos os endpoints
@analytics_bp.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response
