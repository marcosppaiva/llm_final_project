from typing import Any, Union, TypeVar

from groq import Groq
from jinja2 import Template
from openai import OpenAI
from pydantic import BaseModel
from groq.types.chat.chat_completion import ChatCompletion as GroqChatCompletion
from openai.types.chat.chat_completion import ChatCompletion as OpenAIChatCompletion

M = TypeVar('M', bound=BaseModel)


class QuestionAnswering:
    def __init__(
        self,
        model: Union[OpenAI, Groq],
        prompt_assistant_path: str,
        prompt_evaluate_path: str,
        model_name: str,
    ) -> None:
        self.prompt_assistant_path = prompt_assistant_path
        self.prompt_evaluate_path = prompt_evaluate_path
        self._model = model
        self._model_name = model_name

    def get_prompt(self, prompt_path: str, **kwargs: Any) -> str:
        with open(prompt_path, 'r', encoding='utf-8') as f_in:
            template = Template(f_in.read())
        return template.render(**kwargs)

    def evaluate_relevance(
        self, question: str, answer: str
    ) -> Union[GroqChatCompletion, OpenAIChatCompletion]:
        prompt = self.get_prompt(
            prompt_path=self.prompt_evaluate_path, question=question, answer=answer
        )

        response = self._model.chat.completions.create(
            messages=[{'role': 'user', 'content': prompt}],
            model=self._model_name,
        )

        print('Evaluate:', response)

        return response

    def generate_answer(
        self, question: str, context
    ) -> Union[GroqChatCompletion, OpenAIChatCompletion]:
        prompt = self.get_prompt(
            prompt_path=self.prompt_assistant_path, question=question, context=context
        )
        response = self._model.chat.completions.create(
            messages=[{'role': 'user', 'content': prompt}],
            model=self._model_name,
        )

        print('Answser:', response)

        return response

    @property
    def model_name(self) -> str:
        return self._model_name
