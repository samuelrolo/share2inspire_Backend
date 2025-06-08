#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de tracking de downloads do relatório HR para Share2Inspire
Integração com o sistema existente
"""

import os
import json
import logging
import datetime
import sqlite3
from flask import Blueprint, request, jsonify
from main import handle_cors_preflight

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Criar blueprint
hr_downloads_bp = Blueprint('hr_downloads', __name__)

# Caminho da base de dados
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hr_downloads.db')

def init_database():
    """
    Inicializa a base de dados de downloads HR
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hr_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Base de dados HR downloads inicializada com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar base de dados: {str(e)}")

@hr_downloads_bp.route('/hr-downloads', methods=['POST', 'OPTIONS'])
def save_hr_download():
    """
    Endpoint para guardar registo de download do relatório HR
    """
    # Tratamento de CORS para preflight requests
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        # Log detalhado do request
        logger.info("=== NOVO DOWNLOAD HR ===")
        logger.info(f"Método: {request.method}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"IP: {request.remote_addr}")
        logger.info(f"User Agent: {request.user_agent}")
        
        # Obter dados do request
        data = request.get_json() if request.is_json else {}
        
        # Extrair dados com fallbacks
        email = data.get('email', '')
        ip_address = request.remote_addr
        user_agent = str(request.user_agent)
        timestamp = data.get('timestamp', datetime.datetime.now().isoformat())
        
        # Validar email
        if not email or '@' not in email:
            logger.warning(f"Email inválido recebido: {email}")
            return jsonify({
                'success': False,
                'error': 'Email é obrigatório e deve ser válido'
            }), 400
        
        # Inicializar base de dados se necessário
        init_database()
        
        # Guardar na base de dados
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO hr_downloads (email, ip_address, user_agent, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (email, ip_address, user_agent, timestamp))
        
        download_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Download HR registado com sucesso - ID: {download_id}, Email: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Download registado com sucesso',
            'download_id': download_id
        })
        
    except Exception as e:
        logger.error(f"Erro ao guardar download HR: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@hr_downloads_bp.route('/hr-downloads', methods=['GET', 'OPTIONS'])
def get_hr_downloads():
    """
    Endpoint para obter estatísticas de downloads do relatório HR
    """
    # Tratamento de CORS para preflight requests
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        # Inicializar base de dados se necessário
        init_database()
        
        # Verificar se a base de dados existe
        if not os.path.exists(DB_PATH):
            return jsonify({
                'total': 0,
                'today': 0,
                'thisWeek': 0,
                'thisMonth': 0,
                'downloads': [],
                'dailyStats': []
            })
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total downloads
        cursor.execute('SELECT COUNT(*) FROM hr_downloads')
        total = cursor.fetchone()[0]
        
        # Downloads hoje
        cursor.execute('''
            SELECT COUNT(*) FROM hr_downloads 
            WHERE DATE(created_at) = DATE('now')
        ''')
        today = cursor.fetchone()[0]
        
        # Downloads esta semana
        cursor.execute('''
            SELECT COUNT(*) FROM hr_downloads 
            WHERE DATE(created_at) >= DATE('now', '-7 days')
        ''')
        this_week = cursor.fetchone()[0]
        
        # Downloads este mês
        cursor.execute('''
            SELECT COUNT(*) FROM hr_downloads 
            WHERE DATE(created_at) >= DATE('now', 'start of month')
        ''')
        this_month = cursor.fetchone()[0]
        
        # Lista de downloads recentes
        cursor.execute('''
            SELECT email, ip_address, user_agent, timestamp, created_at 
            FROM hr_downloads 
            ORDER BY created_at DESC 
            LIMIT 50
        ''')
        downloads = []
        for row in cursor.fetchall():
            downloads.append({
                'email': row[0],
                'ip': row[1],
                'user_agent': row[2],
                'timestamp': row[3],
                'date': row[4]
            })
        
        # Dados para gráficos - downloads por dia (últimos 7 dias)
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM hr_downloads 
            WHERE DATE(created_at) >= DATE('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        ''')
        daily_stats = []
        for row in cursor.fetchall():
            daily_stats.append({
                'date': row[0],
                'count': row[1]
            })
        
        conn.close()
        
        result = {
            'total': total,
            'today': today,
            'thisWeek': this_week,
            'thisMonth': this_month,
            'downloads': downloads,
            'dailyStats': daily_stats
        }
        
        logger.info(f"Estatísticas HR enviadas: {total} downloads totais")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas HR: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@hr_downloads_bp.route('/hr-downloads/export', methods=['GET', 'OPTIONS'])
def export_hr_downloads():
    """
    Endpoint para exportar dados de downloads em CSV
    """
    # Tratamento de CORS para preflight requests
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        # Inicializar base de dados se necessário
        init_database()
        
        if not os.path.exists(DB_PATH):
            return jsonify({
                'success': False,
                'error': 'Nenhum dado disponível para exportação'
            }), 404
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email, ip_address, user_agent, timestamp, created_at 
            FROM hr_downloads 
            ORDER BY created_at DESC
        ''')
        
        downloads = cursor.fetchall()
        conn.close()
        
        # Criar CSV
        csv_content = "Email,IP Address,User Agent,Timestamp,Created At\n"
        for download in downloads:
            # Escapar vírgulas nos dados
            email = str(download[0]).replace(',', ';')
            ip = str(download[1]).replace(',', ';')
            user_agent = str(download[2]).replace(',', ';')
            timestamp = str(download[3]).replace(',', ';')
            created_at = str(download[4]).replace(',', ';')
            
            csv_content += f"{email},{ip},{user_agent},{timestamp},{created_at}\n"
        
        logger.info(f"Exportação CSV gerada com {len(downloads)} registos")
        
        return csv_content, 200, {
            'Content-Type': 'text/csv; charset=utf-8',
            'Content-Disposition': 'attachment; filename=hr_downloads.csv'
        }
        
    except Exception as e:
        logger.error(f"Erro ao exportar dados HR: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

# Inicializar base de dados ao importar o módulo
init_database()

