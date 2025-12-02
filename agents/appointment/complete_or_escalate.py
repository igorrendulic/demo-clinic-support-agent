from pydantic import BaseModel, Field
from typing import Optional

class CompleteOrEscalate(BaseModel):
    """
    A tool to mark the current task as completed and/or to escalate control of the dialog to the main assistant,
    who can re-route the dialog based on the user's needs.
    """
    cancel: bool = Field(default=True, description=
        "Whether to cancel/end the current task. "
        "Set this to true when:\n"
        "- The user explicitly cancels the current task, OR\n"
        "- You have fully completed the current task.\n"
        "Set this to false when:\n"
        "- You want to keep the current task active and need to take more actions "
        "(for example, searching the user's appointments for more information).")
    reason: Optional[str] = Field(default=None, description=
     "Short natural-language explanation of why you chose this value for `cancel`.\n"
     "Examples:\n"
     "- \"User changed their mind about the current task.\"\n"
     "- \"I have fully completed the task.\"\n"
     "- \"I need to search the user's appointments for more information.\"",
     examples=[
        {"cancel": True, "reason": "User changed their mind about the current task."},
        {"cancel": True, "reason": "I have fully completed the task."},
        {"cancel": False, "reason": "I need to search the user's appointments for more information."},
     ]
    )

    # class Config:
    #     json_schema_extra = {
    #         "example": {
    #             "cancel": True,
    #             "reason": "User changed their mind about the current task.",
    #         },
    #         "example 2": {
    #             "cancel": True,
    #             "reason": "I have fully completed the task.",
    #         },
    #         "example 3": {
    #             "cancel": False,
    #             "reason": "I need to search the user's appointments for more information.",
    #         },
    #     }