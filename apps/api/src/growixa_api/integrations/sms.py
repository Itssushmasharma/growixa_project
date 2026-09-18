import httpx
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SmsAdapter:
    """
    Adapter for Twilio SMS API.
    """
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        
    async def send_message(self, to_phone: str, body: str) -> Dict[str, Any]:
        """
        Send an SMS message via Twilio.
        """
        # Basic E.164 normalization check (assume pre-validated, just ensure + is there)
        if not to_phone.startswith("+"):
            to_phone = "+" + to_phone
            
        payload = {
            "To": to_phone,
            "From": self.from_number,
            "Body": body
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                data=payload,
                auth=(self.account_sid, self.auth_token)
            )
            
            if response.status_code >= 400:
                logger.error(f"Twilio API Error: {response.text}")
                response.raise_for_status()
                
            return response.json()
