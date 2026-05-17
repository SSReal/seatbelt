from abc import ABC, abstractmethod

from llm.llm import LLM


class Exit(Exception):
    pass


class Harness(ABC):
    @abstractmethod
    def __init__(self, model_name: str, *args, **kwargs):
        self.model_name = model_name
        self.llm = LLM(self.model_name)

    @abstractmethod
    async def run(self):
        pass

    def take_user_input(self):
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            raise Exit
        return user_input

    def display_output(self, message):
        print(f"LLM: {message.choices[0].message.content}")
