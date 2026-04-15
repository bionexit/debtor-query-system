"""
SMS Provider Plugins Directory

This directory is volume-mounted from the host machine to allow dynamic
loading of SMS provider plugins without rebuilding the Docker image.

To add a custom SMS provider:
1. Create a Python file in this directory
2. Implement the SMSProviderBase interface
3. The plugin will be auto-discovered on startup

Example:
    from backend.app.plugins.sms.base import SMSProviderBase
    
    class MyCustomProvider(SMSProviderBase):
        name = "custom"
        ...
"""
