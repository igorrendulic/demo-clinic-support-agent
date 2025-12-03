import pytest
import asyncio
from helpers import print_messages, run_graph_turn, BLUE, GREEN

@pytest.mark.anyio
async def test_cancel_appointment():
    thread_id = "4"

    conversation = [
        "My identity is John Doe, 01-01-1960, 1111",
        "show me my upcoming appointments",
        f"After December 15th, i'm out of town. Cancel my appointment after that date",
        "yes. Please cancel it",
        "show me my upcoming appointments",
    ]

    for message in conversation:
        print_messages(f"🧑 user message: {message}", BLUE)
        reply, tid = await run_graph_turn(message, thread_id)
        print_messages(f"🤖 assistant message: {reply}", GREEN)

    

if __name__ == "__main__":
    asyncio.run(test_cancel_appointment())
