from collections.abc import Callable
from typing import Any

import openai

from .task import Task


class OpenAITask(Task):
    
    def __init__(self, id, messages, validate: Callable[[str], bool], postprocess: Callable[[str], Any], generation_config: dict, 
                 model:str, api_key:str, organization:str = None) -> None:
        super().__init__(id, messages, validate, postprocess, generation_config)

        self.api_key = api_key
        self.model = model
        self.organization = organization
    
    def preprocess(self, messages) -> Any:
        return messages
    
    def query(self) -> str:

        openai.api_key = self.api_key
        if self.organization is not None:
            openai.organization = self.organization
        
        completion = openai.ChatCompletion.create(
            model=self.model,
            messages=self.input,
            **self.generation_config
            )

        return completion.choices[0].message['content']
    
    
    