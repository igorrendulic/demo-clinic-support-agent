import sys
import json
from loguru import logger

# 1. Define the formatter
def custom_formatter(record):
    # Pretty handling only for LLM logs
    if record["extra"].get("type") == "llm":
        msg = record["message"]

        # --- NEW LOGIC START ---
        
        # 1. Try to convert Pydantic/LangChain objects to a dict
        # Pydantic V2 uses model_dump(), V1 uses dict()
        if hasattr(msg, "model_dump"):
            msg = msg.model_dump()
        elif hasattr(msg, "dict"):
            msg = msg.dict()

        # 2. If it is (or has become) a dict/list, JSON dump it
        if isinstance(msg, (dict, list)):
            try:
                # default=str handles non-serializable objects (like UUIDs or custom classes)
                msg = json.dumps(msg, indent=2, ensure_ascii=False, default=str)
            except TypeError:
                msg = str(msg) # Fallback if JSON fails
        
        # 3. If it wasn't a dict/model but has content (e.g. simple string wrapper)
        elif hasattr(msg, "content"):
            msg = msg.content
            
        # 4. Fallback
        else:
            msg = str(msg)

        # --- NEW LOGIC END ---

        # Override the message in the record so {message} uses the pretty version
        record["message"] = msg

        return (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<bold><magenta>🤖 AI GENERATION:</magenta></bold>\n"
            "<cyan>{message}</cyan>\n"
            "<magenta>--------------------------------------------------</magenta>\n"
        )

    # Default logging format
    return (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>\n"
    )

# 2. Remove default handler and add custom one
logger.remove()
logger.add(sys.stderr, format=custom_formatter, colorize=True)

# 3. Create and export the bound logger
llm_logger = logger.bind(type="llm")

__all__ = ["logger", "llm_logger"]