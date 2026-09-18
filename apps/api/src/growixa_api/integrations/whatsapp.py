import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class WhatsAppAdapter:
    """
    Adapter for Meta Cloud API for WhatsApp Business.
    """
    
    def __init__(self, phone_number_id: str, access_token: str):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v19.0"
        
    async def send_template_message(
        self, 
        to_phone: str, 
        template_name: str, 
        language_code: str = "en_US",
        components: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Send an approved WhatsApp template message.
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
            
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code >= 400:
                logger.error(f"WhatsApp API Error: {response.text}")
                response.raise_for_status()
                
            return response.json()
            
    async def send_text_message(self, to_phone: str, text: str) -> Dict[str, Any]:
        """
        Send a free-form text message (only allowed within 24hr service window).
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code >= 400:
                logger.error(f"WhatsApp API Error: {response.text}")
                response.raise_for_status()
                
            return response.json()
