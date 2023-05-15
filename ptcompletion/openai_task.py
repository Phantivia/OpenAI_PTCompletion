from collections.abc import Callable
from typing import Any

import openai

from .task import Task
from typing import Any
from abc import abstractmethod

class OpenAITask(Task):
    
    def __init__(self, id, messages, generation_config: dict, 
                 model:str, api_key:str, organization:str = None) -> None:
        super().__init__(id, messages, generation_config)

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
    
    @abstractmethod
    def validate(self, completion:str) -> bool: 
        raise NotImplementedError
    
    @abstractmethod
    def postprocess(self, completion:str) -> dict: 
        raise NotImplementedError
    
    