import asyncio
from agents.llms import get_llm_large_model
from logging_config import qa_evaluator_logger
from langchain_core.callbacks.base import AsyncCallbackHandler
from typing import Any
from langchain_core.outputs import LLMResult
from uuid import UUID
from langchain_core.messages import BaseMessage
from langchain_core.messages import AIMessage, HumanMessage
import hashlib
from pydantic import BaseModel, Field
from typing import Tuple

from agents.hooks.prompts.evaluator_prompts import conversation_evaluator_prompt

class AnswerQuality(BaseModel):
    """
    Evaluation of a single QA pair.
    All subscores are 0-10.
    """
    answer_relevance_accuracy: int = Field(
        description="0-10: Is the answer on-topic and factually correct for the question?"
    )
    user_need_relevance: int = Field(
        description="0-10: Does the answer actually help the user achieve what they wanted?"
    )
    groundedness: int = Field(
        description="0-10: Is the answer grounded in provided data/context, avoiding hallucinations?"
    )
    overall_score: float = Field(
        description="Weighted overall score in [0,10] using 50/30/20 weighting."
    )
    explanation: str = Field(
        description="Short explanation of why the scores were assigned."
    )

class EvaluatorCallbackHandler(AsyncCallbackHandler):
    def __init__(self) -> None:
        super().__init__()
        # Messages seen by this LLM call (per run_id)
        self._history_by_run: dict[UUID, list[BaseMessage]] = {}
        # QA pairs we've already evaluated, so we don't re-evaluate
        self._evaluated_pairs: set[tuple[str, str]] = set()
        eval_llm = get_llm_large_model()
        self._eval_chain = conversation_evaluator_prompt | eval_llm.with_structured_output(AnswerQuality)

    def _pair_key(self, human: HumanMessage, ai: AIMessage) -> tuple[str, str]:
        def msg_key(m: BaseMessage) -> str:
            if getattr(m, "id", None):
                return str(m.id)
            h = hashlib.sha256()
            h.update(m.type.encode("utf-8"))
            h.update(str(m.content).encode("utf-8"))
            return h.hexdigest()

        return msg_key(human), msg_key(ai)

    def _get_last_human(self, messages: list[BaseMessage]) -> HumanMessage | None:
        for m in reversed(messages):
            if isinstance(m, HumanMessage):
                return m
        return None

    def _get_ai_from_result(self, response: LLMResult) -> AIMessage | None:
        # Assuming chat model: generations is List[List[ChatGeneration]]
        if not response.generations:
            return None
        first_batch = response.generations[0]
        if not first_batch:
            return None

        gen = first_batch[0]

        # Newer LangChain: ChatGeneration has .message; older has .text only
        msg = getattr(gen, "message", None)
        if isinstance(msg, AIMessage):
            # Skip tool-only responses with empty content
            if msg.content is None or str(msg.content).strip() == "":
                return None
            return msg

        # Fallback for plain text LLM
        text = getattr(gen, "text", None)
        if text:
            return AIMessage(content=text)

        return None


    async def on_chat_model_start(self, serialized: dict[str, Any], messages: list[list[BaseMessage]], *, run_id: UUID, parent_run_id: UUID | None = None, tags: list[str] | None = None, metadata: dict[str, Any] | None = None, **kwargs: Any) -> None:
       # Usually there is only one batch
        if messages:
            batch = messages[0]
            self._history_by_run[run_id] = batch
            
    async def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: UUID | None = None, tags: list[str] | None = None, **kwargs: Any) -> None:
        messages = self._history_by_run.pop(run_id, [])
        
        human = self._get_last_human(messages)
        ai = self._get_ai_from_result(response)

        if human is None or ai is None:
            return

        # skip already evaluated pair
        pair_key = self._pair_key(human, ai)
        if pair_key in self._evaluated_pairs:
            # Already evaluated this Human–AI pair in a previous run
            return
        
        self._evaluated_pairs.add(pair_key)
        asyncio.create_task(self._run_evaluator(human, ai))
    

    async def _run_evaluator(self, human: HumanMessage, ai: AIMessage) -> None:
        try:
            if not human or not ai:
                return
            eval_input = {
                "question": human.content,
                "answer": ai.content,
                "context": "",
            }
            qa_evaluator_logger.info(f"QA_EVAL: eval_input={eval_input}")
            # result: AnswerQuality = await self._eval_chain.ainvoke(eval_input)
            # qa_evaluator_logger.info(
            #     f"QA_EVAL: "
            #     f"overall={result.overall_score:.2f}, "
            #     f"rel_acc={result.answer_relevance_accuracy}, "
            #     f"user_need={result.user_need_relevance}, "
            #     f"grounded={result.groundedness}, "
            #     f"human={human.content!r}, "
            #     f"ai={ai.content!r}, "
            #     f"explanation={result.explanation}"
            # )
        except Exception as e:
            qa_evaluator_logger.error(f"QA_EVAL: error={e}")
        