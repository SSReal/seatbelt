from abc import ABC, abstractmethod

from llm.llm import LLM
from openai.types.chat import ChatCompletion


class Exit(Exception):
    pass


class Harness(ABC):
    @abstractmethod
    def __init__(self, model_name: str, *args, **kwargs):
        self.model_name = model_name
        self.llm = LLM(self.model_name)
        self.messages = []

    @abstractmethod
    async def run(self):
        pass

    def log_messages(self):
        with open("messages_log.txt", "w") as f:
            for msg in self.messages:
                f.write(f"\n\n{msg['role']}: {msg['content']}\n")

    def take_user_input(self):
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            raise Exit
        elif user_input.lower() == "/show_messages":
            self.log_messages()
            return (
                self.take_user_input()
            )  # Prompt for input again after showing messages
        return user_input

    def display_output(self, message: ChatCompletion):
        if hasattr(message.choices[0].message, "reasoning_content"):
            print(f"LLM reasoning: {message.choices[0].message.reasoning_content}")  # type: ignore
        print(f"LLM: {message.choices[0].message.content}")
