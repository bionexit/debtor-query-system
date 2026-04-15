import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base import SMSProviderBase


class MockSMSProvider(SMSProviderBase):
    """
    Mock SMS provider for testing and development.
    
    Simulates SMS sending without actually sending messages.
    """
    
    name = "mock"
    support_international = True
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.sent_messages: Dict[str, Dict[str, Any]] = {}
        self.failure_rate = self.config.get('failure_rate', 0.0)
        self.delay_seconds = self.config.get('delay_seconds', 0)
    
    def send(self, phone: str, message: str, **kwargs) -> Dict[str, Any]:
        """
        Simulate sending an SMS message.
        
        Returns a random success/failure based on failure_rate setting.
        """
        import time
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
        
        message_id = f"MOCK_{uuid.uuid4().hex[:16].upper()}"
        
        if random.random() < self.failure_rate:
            return {
                'success': False,
                'message_id': message_id,
                'error_code': 'MOCK_FAILURE',
                'error_message': 'Simulated failure for testing',
            }
        
        self.sent_messages[message_id] = {
            'phone': phone,
            'message': message,
            'status': 'sent',
            'sent_at': datetime.utcnow(),
            'delivered_at': None,
        }
        
        self.logger.info(f"[MOCK] SMS sent to {phone}: {message[:50]}... (ID: {message_id})")
        
        return {
            'success': True,
            'message_id': message_id,
            'status': 'sent',
        }
    
    def query_status(self, message_id: str) -> Dict[str, Any]:
        """
        Query the status of a sent message.
        
        Simulates delivery status progression:
        - 0-5 seconds: sent
        - 5-30 seconds: delivered
        - After 30 seconds: always delivered
        """
        if message_id not in self.sent_messages:
            return {
                'status': 'unknown',
                'error_code': 'NOT_FOUND',
                'error_message': f'Message {message_id} not found',
            }
        
        msg = self.sent_messages[message_id]
        elapsed = (datetime.utcnow() - msg['sent_at']).total_seconds()
        
        if elapsed < 5:
            current_status = 'sent'
        else:
            current_status = 'delivered'
            if msg['delivered_at'] is None:
                msg['delivered_at'] = datetime.utcnow()
                msg['status'] = 'delivered'
        
        return {
            'status': current_status,
            'delivered_at': msg.get('delivered_at'),
            'error_code': None,
            'error_message': None,
        }
    
    def handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mock callback data.
        """
        message_id = callback_data.get('message_id')
        
        if message_id and message_id in self.sent_messages:
            status = callback_data.get('status', 'unknown')
            self.sent_messages[message_id]['status'] = status
            
            if status == 'delivered':
                self.sent_messages[message_id]['delivered_at'] = datetime.utcnow()
        
        return {
            'received': True,
            'message_id': message_id,
            'status': callback_data.get('status'),
        }
    
    def get_sent_messages(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all sent messages (for testing purposes).
        """
        return self.sent_messages.copy()
    
    def clear_messages(self):
        """
        Clear all sent messages (for testing purposes).
        """
        self.sent_messages.clear()


class MockSMSProviderFactory:
    """
    Factory for creating MockSMSProvider instances.
    """
    
    @staticmethod
    def create(config: Optional[Dict[str, Any]] = None) -> MockSMSProvider:
        """
        Create a MockSMSProvider instance.
        """
        return MockSMSProvider(config)
