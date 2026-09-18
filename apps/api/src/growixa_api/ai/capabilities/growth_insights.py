import json
from growixa_api.ai.providers.base import AIModelProvider

async def generate(generator: AIModelProvider, brief: str, **kwargs) -> dict[str, object]:
    system_prompt = (
        "You are an expert AI Marketing Strategist for a business. "
        "Analyze the provided historical analytics data (reach, engagement, followers) over the last 30 days. "
        "Return a JSON object with exactly three keys:\n"
        "- 'insights': an array of 2-3 strings describing key trends.\n"
        "- 'recommendations': an array of 2-3 strings of actionable marketing optimization steps.\n"
        "- 'topics': an array of 3 string content ideas to boost engagement."
    )
    
    response = await generator.generate(
        system_prompt=system_prompt,
        user_prompt=f"Here is the analytics data for the last 30 days:\n{brief}",
        json_mode=True,
    )
    
    # Provider returns parsed JSON if json_mode=True, but we ensure it's a dict
    if isinstance(response, str):
        try:
            return json.loads(response)
        except:
            return {"insights": [response], "recommendations": [], "topics": []}
    return response

module = {"generate": generate}
