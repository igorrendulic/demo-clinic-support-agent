from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

mini_model = None

def get_llm_mini_model(temperature: float = 0.0, max_tokens: int = 1000, top_p: float = 1, max_retries: int = 3, timeout: int = 10):
    global mini_model
    
    if mini_model is not None:
        return mini_model

    # model = ChatGoogleGenerativeAI(
    #     model="gemini-2.5-flash",
    #     api_key=os.getenv("GEMINI_API_KEY"),
    #     temperature=temperature,
    #     max_tokens=max_tokens,
    #     top_p=top_p,
    #     max_retries=max_retries,
    #     timeout=timeout
    # )
    model = ChatOpenAI(
        model="gpt-4.1-mini", # gpt-5-mini (super slow)
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        max_retries=max_retries,
        timeout=timeout
    )
    
    mini_model = model
    return mini_model