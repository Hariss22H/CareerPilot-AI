import json
import logging
from typing import Any

import httpx

from .config import Settings
from .rag import CareerRetriever

logger = logging.getLogger(__name__)

COACH_SYSTEM = """You are CareerPilot AI Career Coach. You are a focused career mentor, resume reviewer,
technical interview coach, and learning advisor. Answer only questions about resumes, job descriptions,
skills, career planning, learning roadmaps, interview preparation, or educational guidance.
If the user asks for unrelated help, politely refuse and redirect them to career topics.
Use the supplied personal context and retrieved job context. Never invent resume experience or claim certainty
about hiring outcomes. Be practical, concise, and specific."""


def _fallback_answer(message: str, context: str) -> str:
    return f"Based on your current career context, start by connecting your next action to the target role. Your question was: '{message}'. Review the report gaps, choose one priority skill, and turn it into a small project or interview exercise."


class CareerCoach:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.retriever = CareerRetriever()

    async def answer(self, message: str, personal_context: dict[str, Any], job_documents: list[str], history: list[dict[str, str]]) -> str:
        retrieved = self.retriever.retrieve(message, job_documents)
        context = json.dumps({"personal": personal_context, "retrieved_job_context": retrieved})
        if not (self.settings.openai_api_key or self.settings.gemini_api_key):
            return _fallback_answer(message, context)
        try:
            from langchain_core.output_parsers import StrOutputParser
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

            prompt = ChatPromptTemplate.from_messages([
                ("system", COACH_SYSTEM + "\nPersonal context and retrieved context:\n{context}"),
                MessagesPlaceholder("history"),
                ("human", "{message}"),
            ])
            if self.settings.ai_provider == "openai":
                from langchain_openai import ChatOpenAI

                model = ChatOpenAI(api_key=self.settings.openai_api_key, model=self.settings.openai_model, temperature=0.25, max_tokens=self.settings.chat_max_tokens)
            else:
                return _fallback_answer(message, context)
            chain = prompt | model | StrOutputParser()
            return await chain.ainvoke({"context": context, "history": history[-8:], "message": message})
        except Exception as exc:
            logger.exception("Career Coach failed: %s", type(exc).__name__)
            return _fallback_answer(message, context)

