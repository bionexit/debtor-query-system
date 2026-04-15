from typing import Dict, Optional, Any, List
import logging
from .base import SMSProviderBase
from .mock import MockSMSProvider

logger = logging.getLogger(__name__)


class SMSProviderManager:
    """
    Manager for SMS providers.
    
    Handles provider registration, selection, and message routing.
    """
    
    def __init__(self):
        self._providers: Dict[str, SMSProviderBase] = {}
        self._default_provider: Optional[str] = None
        self._initialize_default_providers()
    
    def _initialize_default_providers(self):
        """
        Initialize default providers.
        """
        mock_provider = MockSMSProvider({'failure_rate': 0.0})
        self.register_provider('mock', mock_provider, set_default=True)
    
    def register_provider(self, name: str, provider: SMSProviderBase, set_default: bool = False):
        """
        Register a new SMS provider.
        
        Args:
            name: Provider name/identifier
            provider: SMSProviderBase instance
            set_default: Whether to set this as the default provider
        """
        if not isinstance(provider, SMSProviderBase):
            raise ValueError(f"Provider must be an instance of SMSProviderBase")
        
        self._providers[name] = provider
        
        if set_default or self._default_provider is None:
            self._default_provider = name
        
        logger.info(f"Registered SMS provider: {name}")
    
    def unregister_provider(self, name: str) -> bool:
        """
        Unregister an SMS provider.
        
        Args:
            name: Provider name to remove
            
        Returns:
            True if removed, False if not found
        """
        if name in self._providers:
            del self._providers[name]
            
            if self._default_provider == name:
                self._default_provider = next(iter(self._providers), None)
            
            logger.info(f"Unregistered SMS provider: {name}")
            return True
        
        return False
    
    def get_provider(self, name: Optional[str] = None) -> Optional[SMSProviderBase]:
        """
        Get a provider by name or get the default provider.
        
        Args:
            name: Provider name, or None for default
            
        Returns:
            SMSProviderBase instance or None
        """
        if name:
            return self._providers.get(name)
        
        if self._default_provider:
            return self._providers[self._default_provider]
        
        return None
    
    def get_provider_names(self) -> List[str]:
        """
        Get list of registered provider names.
        """
        return list(self._providers.keys())
    
    def set_default_provider(self, name: str) -> bool:
        """
        Set the default SMS provider.
        
        Args:
            name: Provider name to set as default
            
        Returns:
            True if successful, False if provider not found
        """
        if name in self._providers:
            self._default_provider = name
            logger.info(f"Set default SMS provider: {name}")
            return True
        return False
    
    def get_default_provider_name(self) -> Optional[str]:
        """
        Get the name of the default provider.
        """
        return self._default_provider
    
    def send(self, phone: str, message: str, provider_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Send an SMS message using the specified or default provider.
        
        Args:
            phone: Recipient phone number
            message: SMS message content
            provider_name: Specific provider to use, or None for default
            **kwargs: Additional arguments to pass to the provider
            
        Returns:
            Dictionary containing send result
        """
        provider = self.get_provider(provider_name)
        
        if not provider:
            return {
                'success': False,
                'error_code': 'PROVIDER_NOT_FOUND',
                'error_message': f'SMS provider not found: {provider_name or "default"}',
            }
        
        try:
            return provider.send(phone, message, **kwargs)
        except Exception as e:
            logger.error(f"Error sending SMS via {provider.name}: {str(e)}")
            return {
                'success': False,
                'error_code': 'SEND_ERROR',
                'error_message': str(e),
            }
    
    def query_status(self, message_id: str, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the status of an SMS message.
        
        Args:
            message_id: The message ID to query
            provider_name: Specific provider to query, or None for default
            
        Returns:
            Dictionary containing status result
        """
        provider = self.get_provider(provider_name)
        
        if not provider:
            return {
                'status': 'unknown',
                'error_code': 'PROVIDER_NOT_FOUND',
                'error_message': f'SMS provider not found: {provider_name or "default"}',
            }
        
        try:
            return provider.query_status(message_id)
        except Exception as e:
            logger.error(f"Error querying SMS status via {provider.name}: {str(e)}")
            return {
                'status': 'unknown',
                'error_code': 'QUERY_ERROR',
                'error_message': str(e),
            }


sms_manager = SMSProviderManager()
