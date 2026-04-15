from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SMSProviderBase(ABC):
    """
    Abstract base class for SMS providers.
    
    All SMS provider implementations must inherit from this class
    and implement the required methods.
    """
    
    name: str = "base"
    support_international: bool = False
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the SMS provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"sms.{self.name}")
    
    @abstractmethod
    def send(self, phone: str, message: str, **kwargs) -> Dict[str, Any]:
        """
        Send an SMS message.
        
        Args:
            phone: Recipient phone number
            message: SMS message content
            
        Returns:
            Dictionary containing:
                - success: bool
                - message_id: str (provider's message ID)
                - error_code: str (optional)
                - error_message: str (optional)
        """
        pass
    
    @abstractmethod
    def query_status(self, message_id: str) -> Dict[str, Any]:
        """
        Query the delivery status of an SMS message.
        
        Args:
            message_id: The message ID returned from send()
            
        Returns:
            Dictionary containing:
                - status: str (pending/sent/delivered/failed/unknown)
                - delivered_at: datetime (optional)
                - error_code: str (optional)
                - error_message: str (optional)
        """
        pass
    
    def validate_phone(self, phone: str) -> bool:
        """
        Validate phone number format for this provider.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        import re
        pattern = re.compile(r'^1[3-9]\d{9}$')
        return bool(pattern.match(phone))
    
    def format_phone(self, phone: str) -> str:
        """
        Format phone number for this provider.
        
        Args:
            phone: Raw phone number
            
        Returns:
            Formatted phone number
        """
        return phone.strip()
    
    def handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle SMS status callback from provider.
        
        Args:
            callback_data: Callback data from provider
            
        Returns:
            Normalized callback response
        """
        return callback_data
