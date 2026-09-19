import httpx
from growixa_api.config import get_settings

class TwilioClientError(Exception):
    pass

async def send_sms(to_number: str, message: str) -> dict:
    """
    Sends an SMS message using the Twilio API.
    Uses the global platform credentials if defined in .env.
    """
    settings = get_settings()
    
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        raise TwilioClientError("Twilio credentials are not configured in the environment.")
        
    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    
    auth = (settings.twilio_account_sid, settings.twilio_auth_token)
    
    data = {
        "To": to_number,
        "From": settings.twilio_phone_number,
        "Body": message
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, auth=auth, data=data)
        
        if not response.is_success:
            raise TwilioClientError(f"Failed to send SMS: {response.text}")
            
        return response.json()
