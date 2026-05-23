from operator import length_hint
from random import choices
import re
import asyncio
import threading
from typing import Any

from harness.code_act_subagent_harness import CodeActSubagentHarness
from openai.types.chat import ChatCompletion

from harness.harness import Exit, Harness
from prompts.rlm_prompt import RLM_PROMPT
from repl.REPL import REPL


class RLMHarness(Harness):
    def __init__(self, model_name: str, *args, **kwargs):
        super().__init__(model_name, *args, **kwargs)
        self.repl = REPL()
        self.max_chunk_length = kwargs.get("chunk_length", 100)
        self.sys_prompt = kwargs.get("sys_prompt", RLM_PROMPT)
        self.is_subagent = kwargs.get("is_subagent", False)
        if self.is_subagent:
            print("\n\n\n --------- SUBAGENT --------- \n\n\n")
        self.setup_messages()

    def spawn_subagent(self, query: Any, id: str):
        async def _spawn():
            subagent = RLMHarness(self.model_name, is_subagent=True)
            result = await subagent.process_query(query)
            print(result.choices[0].message.content)
            self.repl.namespace[f"_subagent_{id}"] = subagent.repl.namespace.get(
                "_content", ""
            )
            self.messages.append(
                {
                    "role": "tool",
                    "content": f"Subagent with id {id} completed the query",
                }
            )
            print(f"Subagent {id} completed. Result stored in _subagent_{id}")

        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_spawn())
            finally:
                loop.close()

        thread = threading.Thread(target=run_in_thread, daemon=False)
        thread.start()
        thread.join()  # Block until subagent completes

    def setup_messages(self):
        self.repl.namespace["spawn_subagent"] = self.spawn_subagent
        self.messages = [
            {
                "role": "system",
                "content": self.sys_prompt,
            }
        ]

    async def process_code_blocks(self, response: ChatCompletion) -> ChatCompletion:
        content = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": content})
        self.display_output(response)
        if not content:
            return response

        code_blocks = re.findall(r"```python\n(.*?)\n```", content, re.DOTALL)

        if len(code_blocks) == 0:
            return response

        for code in code_blocks:
            print(f"Executing code block:\n{code}")
            repl_result = self.repl.run(code)
            print(f"REPL result: {repl_result}")
            self.messages.append(
                {
                    "role": "tool",
                    "content": f"Code Output: {repl_result}",
                }
            )
        return await self.process_code_blocks(await self.llm(self.messages))

    async def process_query(self, query: Any) -> ChatCompletion:
        self.repl.namespace["_query"] = query
        self.messages.append(
            {
                "role": "user",
                "content": f"The user query is a {type(query)} with length {len(query)}. Here's a snapshot of the query: {query[:50]}",
            }
        )
        return await self.process_code_blocks(await self.llm(self.messages))

    async def run(self):
        print("Running RLMHarness. Type 'exit', 'quit', or 'bye' to stop.")
        while True:
            try:
                query = self.take_user_input()
            except Exit:
                break
            response = await self.process_query(query)
            self.messages.append(
                {
                    "role": "assistent",
                    "content": (
                        response.choices[0].message.content
                        if response
                        else "No response from assistant."
                    ),
                }
            )
            self.display_output(response)
            print(
                f"Final response in REPL:\n{self.repl.namespace.get('_content', 'No content returned by the assistant.')}"
            )
            self.log_messages()
            self.setup_messages()
        print("Exiting RLMHarness")


if __name__ == "__main__":
    import asyncio

    harness = RLMHarness("qwen3.5-9B", chunk_length=100)
    asyncio.run(harness.run())
