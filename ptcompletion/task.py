from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from abc import abstractmethod

class Task:
    
    messages:list[dict]
    input:Any = None
    completion:str = None
    result:dict = None
    
    completed:bool = False
        
    def __init__(self, id:str | int, messages:list[dict], generation_config:dict) -> None:
        
        self.id = id
        
        self.messages = messages
        self.input = self.preprocess(messages)
        self.generation_config = generation_config

    @abstractmethod
    def preprocess(self, messages:list[dict]) -> Any:
        raise NotImplementedError
    
    @abstractmethod
    def query(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def validate(self, completion:str) -> bool: 
        raise NotImplementedError
    
    @abstractmethod
    def postprocess(self, completion:str) -> dict: 
        raise NotImplementedError
    
    def run(self) -> None:
        
        try:
            completion = self.query()
        except Exception as error:
            print("Query Error: ", repr(error))
            return
        
        is_valid = self.validate(completion)
        
        if is_valid:
            self.completion = completion
            self.result = self.postprocess(completion)
            self.completed = True
            return
    
    def __str__(self) -> str:
        return '\n'.join([
            f'{self.__class__}',
            f'Result: {self.result}',
            f'Completion: {self.completion}',
            f'Input: {self.input}'
        ])







    
        

        