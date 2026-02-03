# -*- coding: utf-8 -*-

"""
Datastore Client para Share2Inspire Backend
Gestão de registos de pagamentos usando Google Cloud Datastore
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Tentar importar o cliente do Datastore
try:
    from google.cloud import datastore
    DATASTORE_AVAILABLE = True
except ImportError:
    DATASTORE_AVAILABLE = False
    logger.warning("Google Cloud Datastore não disponível. A usar armazenamento em memória.")


class DatastoreClient:
    """Cliente para interagir com o Google Cloud Datastore"""
    
    def __init__(self):
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'share2inspire-beckend')
        self._client = None
        self._memory_store = {}  # Fallback em memória
        
        if DATASTORE_AVAILABLE:
            try:
                self._client = datastore.Client(project=self.project_id)
                logger.info(f"Datastore client inicializado para projeto: {self.project_id}")
            except Exception as e:
                logger.error(f"Erro ao inicializar Datastore client: {e}")
                self._client = None
    
    def _get_key(self, order_id: str):
        """Criar chave do Datastore"""
        if self._client:
            return self._client.key('PaymentRecord', order_id)
        return order_id
    
    def save_payment_record(self, order_id: str, payment_data: dict, user_data: dict, analysis_data: dict = None) -> bool:
        """Guardar registo de pagamento"""
        try:
            record = {
                'order_id': order_id,
                'payment_data': payment_data,
                'user_data': user_data,
                'analysis_data': analysis_data,
                'created_at': datetime.now().isoformat(),
                'payment_status': 'pending',
                'delivered': False
            }
            
            if self._client:
                key = self._get_key(order_id)
                entity = datastore.Entity(key=key)
                entity.update(record)
                self._client.put(entity)
                logger.info(f"Registo guardado no Datastore: {order_id}")
            else:
                self._memory_store[order_id] = record
                logger.info(f"Registo guardado em memória: {order_id}")
            
            return True
        except Exception as e:
            logger.error(f"Erro ao guardar registo: {e}")
            return False
    
    def get_payment_record(self, order_id: str) -> dict:
        """Obter registo de pagamento"""
        try:
            if self._client:
                key = self._get_key(order_id)
                entity = self._client.get(key)
                if entity:
                    return dict(entity)
                return None
            else:
                return self._memory_store.get(order_id)
        except Exception as e:
            logger.error(f"Erro ao obter registo: {e}")
            return None
    
    def update_record(self, order_id: str, updates: dict) -> bool:
        """Atualizar registo de pagamento"""
        try:
            if self._client:
                key = self._get_key(order_id)
                entity = self._client.get(key)
                if entity:
                    entity.update(updates)
                    self._client.put(entity)
                    logger.info(f"Registo atualizado no Datastore: {order_id}")
                    return True
                return False
            else:
                if order_id in self._memory_store:
                    self._memory_store[order_id].update(updates)
                    logger.info(f"Registo atualizado em memória: {order_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Erro ao atualizar registo: {e}")
            return False
    
    def is_delivered(self, order_id: str) -> bool:
        """Verificar se o relatório já foi entregue"""
        try:
            record = self.get_payment_record(order_id)
            if record:
                return record.get('delivered', False)
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar entrega: {e}")
            return False
    
    def mark_as_delivered(self, order_id: str) -> bool:
        """Marcar registo como entregue"""
        return self.update_record(order_id, {
            'delivered': True,
            'delivered_at': datetime.now().isoformat()
        })


# Singleton instance
_datastore_client = None

def get_datastore_client() -> DatastoreClient:
    """Obter instância singleton do cliente Datastore"""
    global _datastore_client
    if _datastore_client is None:
        _datastore_client = DatastoreClient()
    return _datastore_client
