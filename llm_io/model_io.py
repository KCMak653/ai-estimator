import logging
from typing import List, Optional, Union

from langchain_core.messages import BaseMessage
from openai import OpenAI

logger = logging.getLogger(__name__)


# TODO (design): This class is a single abstraction for "get one completion" so parsers/generators
# (WindowDescriptionParser, ValidConfigGenerator, etc.) take a ModelIO instance and stay agnostic to
# backend. Pros: one interface (get_response), retry/validation stay in consumers, easy to test with
# a fake. If we add more backends (Anthropic, LiteLLM) or want llm_io to stay free of LangChain,
# refactor to a protocol (e.g. get_response(user_content) -> str | None) plus per-backend
# implementations (LegacyModelIO, LangChainModelIO).


class ModelIO:
    """
    Unified interface for LLM calls. Use either:
    - Legacy: ModelIO(company_name, model, prompt) → uses OpenAI client (responses API).
    - LangChain: ModelIO(prompt=system_prompt, llm=chat_llm) → uses llm.invoke([system, user]).
    get_response(user_content) works the same in both cases.
    """

    def __init__(self, company_name=None, model=None, prompt=None, *, llm=None):
        self.prompt = prompt
        self.llm = llm
        if llm is not None:
            self.client = None
            self.model = None
            self.company_name = None
        else:
            if company_name is None or model is None:
                raise TypeError("company_name and model are required when llm is not provided")
            self.company_name = company_name
            self.model = model
            self.client = self._authenticate()

    def _authenticate(self):
        try:
            return OpenAI()
        except Exception as e:
            logger.error(f"Error initializing OpenAI client. Is OPENAI_API_KEY set? Error: {e}")
            exit()

    def get_response(self, message: str = None, messages_lc: List[BaseMessage] = None) -> Optional[Union[str, BaseMessage]]:
        """
        Send a chat completion request.
        Legacy: returns assistant text (str).
        LangChain: returns the AIMessage from the model.
        """
        if self.llm is not None:
            return self._get_response_via_llm(message, messages_lc)
        if messages_lc is not None and message is None:
            raise ValueError("messages_lc (list of messages) is not supported with the legacy backend; use message (str) only.")
        legacy_input = message or ""
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=self.prompt,
                input=legacy_input,
            )
            return response.output_text
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return None

    def _get_response_via_llm(self, message: str = None, messages_lc: List[BaseMessage] = None) -> Optional[BaseMessage]:
        from langchain_core.messages import HumanMessage, SystemMessage
        if messages_lc is None:
            to_invoke = [HumanMessage(content=message or "")]
        else:
            to_invoke = messages_lc
        if self.prompt:
            to_invoke = [SystemMessage(content=self.prompt)] + to_invoke
        print(to_invoke)
        try:
            return self.llm.invoke(to_invoke)
        except Exception as e:
            logger.error(f"Error in LLM invoke: {e}")
            return None