from typing import List, Tuple
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

def extract_qa_pairs(messages: List[BaseMessage]) -> List[Tuple[HumanMessage, AIMessage]]:
    """
    Walks through the messages and pairs:
      - each HumanMessage with the *next* AIMessage that appears after it.

    This gives you a list of (question, answer) pairs in order.
    """
    pairs: List[Tuple[HumanMessage, AIMessage]] = []
    last_human: HumanMessage | None = None

    for m in messages:
        if isinstance(m, HumanMessage):
            last_human = m
        elif isinstance(m, AIMessage) and last_human is not None:
            pairs.append((last_human, m))
            last_human = None  # reset so you don’t pair the same human with multiple AIs

    return pairs