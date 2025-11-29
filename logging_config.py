import sys
import json
from loguru import logger


# 1. Define the formatter
def custom_formatter(record):
    # Pretty handling only for LLM logs
    if record["extra"].get("type") == "llm":
        msg = record["message"]

        # LangChain AIMessage/SystemMessage/etc -> use .content
        if hasattr(msg, "content"):
            msg = msg.content

        # dict / list -> pretty JSON
        elif isinstance(msg, (dict, list)):
            msg = json.dumps(msg, indent=2, ensure_ascii=False)

        # Fallback to string
        else:
            msg = str(msg)

        # Override the message in the record so {message} uses the pretty version
        record["message"] = msg

        return (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<bold><magenta>🤖 AI GENERATION:</magenta></bold>\n"  # Header
            "<cyan>{message}</cyan>\n"                             # Content on new line
            "<magenta>--------------------------------------------------</magenta>\n"  # Separator
        )

    # Default logging format
    return (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>\n"
    )


# 2. Configure the global logger (Runs once when this module is imported)
logger.remove()
logger.add(sys.stderr, format=custom_formatter, colorize=True)

# 3. Create and export the bound logger
llm_logger = logger.bind(type="llm")

__all__ = ["logger", "llm_logger"]