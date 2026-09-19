import httpx
from growixa_api.config import get_settings

class MetaClientError(Exception):
    pass

async def send_whatsapp_message(to_number: str, message: str) -> dict:
    """
    Sends a WhatsApp message using the Meta Cloud API.
    Uses the global platform credentials if defined in .env.
    """
    settings = get_settings()
    
    if not settings.meta_whatsapp_token or not settings.meta_whatsapp_phone_id:
        raise MetaClientError("Meta WhatsApp credentials are not configured in the environment.")
        
    url = f"https://graph.facebook.com/v19.0/{settings.meta_whatsapp_phone_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {settings.meta_whatsapp_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message
        }
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, headers=headers, json=data)
        
        if not response.is_success:
            raise MetaClientError(f"Failed to send WhatsApp message: {response.text}")
            
        return response.json()
