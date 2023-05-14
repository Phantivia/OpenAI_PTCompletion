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
        
    def __init__(self, id:str | int, messages:list[dict], validate:Callable[[str], bool], postprocess:Callable[[str], Any], generation_config:dict) -> None:
        
        self.id = id
        
        self.messages = messages
        self.input = self.preprocess(messages)
        
        self.validate = validate
        self.postprocess = postprocess
        self.generation_config = generation_config

    @abstractmethod
    def preprocess(self, messages) -> Any:
        raise NotImplementedError
    
    @abstractmethod
    def query(self) -> str:
        raise NotImplementedError

    def validate(completion) -> bool: 
        raise NotImplementedError
    
    def postprocess(completion) -> dict: 
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







    
        

        