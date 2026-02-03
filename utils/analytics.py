# -*- coding: utf-8 -*-
"""
Módulo de Analytics para CV Analyzer - Share2Inspire
Versão 1.0 - Tracking e Estatísticas de Análises
"""

import os
import requests
from datetime import datetime, timedelta

# Configuração Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://cvlumvgrbuolrnwrtrgz.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN2bHVtdmdyYnVvbHJud3J0cmd6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2NDI3MywiZXhwIjoyMDgzOTQwMjczfQ.71rOpHDasxhT4QUn9rKVT-Nv0OlH3x9uBs7H2ZkFPGY")


class CVAnalytics:
    """Classe para gestão de analytics de análises de CV."""
    
    def __init__(self):
        self.headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
    
    def log_analysis(self, user_email, user_name, analysis_result, score=None, 
                     professional_area=None, analysis_type="free", 
                     payment_status="pending", payment_amount=None, transaction_id=None):
        """
        Regista uma análise de CV na base de dados.
        
        Args:
            user_email: Email do utilizador
            user_name: Nome do utilizador
            analysis_result: Resultado da análise (dict/JSON)
            score: Pontuação obtida (0-100)
            professional_area: Área profissional detectada
            analysis_type: Tipo de análise ('free' ou 'premium')
            payment_status: Estado do pagamento ('pending', 'paid', 'failed')
            payment_amount: Valor pago (se aplicável)
            transaction_id: ID da transação de pagamento
        
        Returns:
            dict: Resultado da operação com ID do registo
        """
        try:
            log_entry = {
                "user_email": user_email,
                "user_name": user_name,
                "analysis_result": analysis_result,
                "score": score,
                "professional_area": professional_area,
                "analysis_type": analysis_type,
                "payment_status": payment_status,
                "payment_amount": payment_amount,
                "transaction_id": transaction_id,
                "domain": "share2inspire.pt",
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/cv_analysis",
                json=log_entry,
                headers={**self.headers, "Prefer": "return=representation"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {"success": True, "id": data[0]["id"] if data else None}
            else:
                print(f"[ERRO] Falha ao registar análise: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"[ERRO] Exceção ao registar análise: {e}")
            return {"success": False, "error": str(e)}
    
    def update_payment_status(self, analysis_id=None, transaction_id=None, 
                               payment_status="paid", payment_amount=None):
        """
        Atualiza o estado de pagamento de uma análise.
        
        Args:
            analysis_id: ID do registo de análise
            transaction_id: ID da transação (alternativa ao analysis_id)
            payment_status: Novo estado ('paid', 'failed', 'refunded')
            payment_amount: Valor do pagamento
        
        Returns:
            dict: Resultado da operação
        """
        try:
            update_data = {
                "payment_status": payment_status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if payment_amount:
                update_data["payment_amount"] = payment_amount
            
            if transaction_id:
                update_data["transaction_id"] = transaction_id
            
            # Construir URL com filtro
            if analysis_id:
                url = f"{SUPABASE_URL}/rest/v1/cv_analysis?id=eq.{analysis_id}"
            elif transaction_id:
                url = f"{SUPABASE_URL}/rest/v1/cv_analysis?transaction_id=eq.{transaction_id}"
            else:
                return {"success": False, "error": "É necessário analysis_id ou transaction_id"}
            
            response = requests.patch(
                url,
                json=update_data,
                headers=self.headers
            )
            
            if response.status_code in [200, 204]:
                return {"success": True}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_payment_status_by_email(self, user_email, payment_status="paid", payment_amount=None):
        """
        Updates the payment status of the most recent analysis for a given email.
        Useful when we don't have the analysis_id but have the user's email.
        """
        try:
            # 1. Find the most recent analysis for this email
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/cv_analysis?user_email=eq.{user_email}&order=created_at.desc&limit=1",
                headers=self.headers
            )
            
            if response.status_code != 200:
                print(f"[ANALYTICS] Error finding analysis by email: {response.text}")
                return {"success": False, "error": response.text}
                
            data = response.json()
            if not data:
                print(f"[ANALYTICS] No analysis found for email: {user_email}")
                return {"success": False, "error": "Analysis not found"}
                
            analysis_id = data[0]['id']
            print(f"[ANALYTICS] Found analysis {analysis_id} for email {user_email}. Updating status...")
            
            # 2. Update status
            return self.update_payment_status(
                analysis_id=analysis_id, 
                payment_status=payment_status, 
                payment_amount=payment_amount
            )
            
        except Exception as e:
            print(f"[ANALYTICS] Exception updating by email: {e}")
            return {"success": False, "error": str(e)}
    
    def get_summary_stats(self):
        """
        Obtém estatísticas resumidas de todas as análises.
        
        Returns:
            dict: Estatísticas agregadas
        """
        try:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/cv_analytics_summary",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {"success": True, "stats": data[0]}
                return {"success": True, "stats": {
                    "total_analyses": 0,
                    "paid_analyses": 0,
                    "free_analyses": 0,
                    "total_revenue": 0,
                    "last_24h": 0,
                    "last_7_days": 0,
                    "last_30_days": 0,
                    "avg_score": None
                }}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_daily_stats(self, days_back=30):
        """
        Obtém estatísticas por dia.
        
        Args:
            days_back: Número de dias para trás (default: 30)
        
        Returns:
            dict: Lista de estatísticas diárias
        """
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/get_cv_stats_by_day",
                json={"days_back": days_back},
                headers=self.headers
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_area_stats(self):
        """
        Obtém estatísticas por área profissional.
        
        Returns:
            dict: Lista de estatísticas por área
        """
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/get_cv_stats_by_area",
                json={},
                headers=self.headers
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_recent_analyses(self, limit=10):
        """
        Obtém as análises mais recentes.
        
        Args:
            limit: Número máximo de registos (default: 10)
        
        Returns:
            dict: Lista de análises recentes
        """
        try:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/cv_analysis?select=id,user_email,user_name,score,professional_area,payment_status,created_at&order=created_at.desc&limit={limit}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_live_count(self):
        """
        Obtém contagem rápida para exibição em tempo real.
        
        Returns:
            dict: Contagens básicas
        """
        try:
            # Contagem total
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/cv_analysis?select=id",
                headers={**self.headers, "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"}
            )
            
            total = 0
            if "content-range" in response.headers:
                # Formato: "0-0/123" onde 123 é o total
                range_header = response.headers["content-range"]
                if "/" in range_header:
                    total = int(range_header.split("/")[1])
            
            return {
                "success": True,
                "total_analyses": total,
                "display_count": f"+{total}" if total > 0 else "0"
            }
                
        except Exception as e:
            return {"success": False, "error": str(e), "total_analyses": 0}

    def log_google_ads_lead(self, lead_data):
        """
        Regista um lead vindo do Google Ads.
        
        Args:
            lead_data: Dados do lead formatados
            
        Returns:
            dict: Resultado da operação
        """
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/google_ads_leads",
                json=lead_data,
                headers={**self.headers, "Prefer": "return=representation"}
            )
            
            if response.status_code in [200, 201]:
                return {"success": True}
            else:
                print(f"[ERRO] Falha ao registar lead Google Ads: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"[ERRO] Exceção ao registar lead Google Ads: {e}")
            return {"success": False, "error": str(e)}


# Instância global para uso fácil
analytics = CVAnalytics()


def log_cv_analysis(user_email, user_name, analysis_result, **kwargs):
    """Função de conveniência para registar análise."""
    return analytics.log_analysis(user_email, user_name, analysis_result, **kwargs)


def get_analytics_summary():
    """Função de conveniência para obter resumo."""
    return analytics.get_summary_stats()


def get_live_counter():
    """Função de conveniência para contador em tempo real."""
    return analytics.get_live_count()
