import asyncio
from typing import override

from harness.harness import Exit, Harness


class SimpleHarness(Harness):
    # The simplest harness possible - just runs a chat loop with the LLM and prints the output
    def __init__(self, model_name: str, *args, **kwargs):
        super().__init__(model_name)
        self.sys_prompt = kwargs.get("system_prompt", "You are a helpful assistant.")

    async def run(self):
        self.messages = [
            {
                "role": "system",
                "content": self.sys_prompt,
            }
        ]
        print(f"Running SimpleHarness with model {self.model_name}")
        while True:
            try:
                user_input = self.take_user_input()
            except Exit:
                print("Exiting SimpleHarness.")
                break
            self.messages.append({"role": "user", "content": user_input})
            response = await self.llm(self.messages)
            self.messages.append(
                {"role": "assistant", "content": response.choices[0].message.content}
            )
            self.display_output(response)


if __name__ == "__main__":
    harness = SimpleHarness("qwen3.5-9B")
    asyncio.run(harness.run())
