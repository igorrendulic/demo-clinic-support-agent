from dataclasses import dataclass

@dataclass
class ChatRequest:
    message: str
    thread_id: str

@dataclass
class ChatResponse:
    message: str
    thread_id: str