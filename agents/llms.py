from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

flash_light_latest_model = None

def get_llm_gemini_flash_light_latest(temperature: float = 0.0, max_tokens: int = 1000, top_p: float = 1, max_retries: int = 3, timeout: int = 10):
    global flash_light_latest_model
    
    if flash_light_latest_model is not None:
        return flash_light_latest_model

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        max_retries=max_retries,
        timeout=timeout
    )
    
    flash_light_latest_model = model
    return flash_light_latest_model