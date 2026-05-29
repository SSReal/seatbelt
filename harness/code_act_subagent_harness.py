from harness.code_act_harness import CodeActHarness
from openai.types.chat import ChatCompletion
import re

from harness.harness import Exit


class CodeActSubagentHarness(CodeActHarness):
    def __init__(self, model_name: str, *args, **kwargs):
        super().__init__(model_name, *args, **kwargs)
        self.is_subagent = kwargs.get("is_subagent", False)
        if self.is_subagent and "query" not in kwargs:
            raise ValueError("Subagent must have an 'query' specified.")
        self.query = kwargs.get("query", None)
        self.setup()

    def setup(self):
        if self.is_subagent:
            self.sys_prompt = (
                f"\nYou are an agent whose aim is fixed and given by the main agent. Use the tools at your disposal and run code to achieve this objective. "
                "Just complete the task without any extra commentary and return the final result. Do not explain your reasoning or thought process."
            )

        self.subagent_prompt = (
            "\nIf your task can be split into multiple independent units, spawn subagents for doing those tasks. To spawn a subagent, use the following format in your response:\n\n"
            f"```subagent:<id_for_subagent>\n<query for the subagent> \n```\n\n"
            "The query should be a clear and concise description of the task you want the subagent to accomplish."
            "The subagent will be created with the same capabilities as you, but with a different system prompt and a fresh context, and will return the answer to the query you specified."
            "CRITICAL: THE SUBAGENTS WILL NOT HAVE ACCESS TO THE MAIN AGENT'S CONTEXT OR MEMORY, SO MAKE SURE TO SPECIFY THE QUERY FOR THE SUBAGENT CLEARLY AND IN FULL, AS IF YOU WERE ASKING AN INDEPENDENT AGENT WITHOUT ANY PRIOR KNOWLEDGE OF THE PROBLEM."
            "Then you can combine the results from different subagents and return the final answer to the main agent. Remember, the subagent's goal is to complete the query you give it, so make sure to specify it clearly."
        )

    def setup_messages(self):
        self.messages = [
            {
                "role": "system",
                "content": self.sys_prompt + self.code_prompt + self.subagent_prompt,
            }
        ]
        if self.is_subagent:
            self.messages.append(
                {"role": "user", "content": f"The query is: {self.query}"}
            )

    async def process_subagents(self, response: ChatCompletion):
        content = response.choices[0].message.content or ""
        subagent_matches = re.findall(
            r"```subagent:(.*?)\n(.*?)\n```", content, re.DOTALL
        )
        if len(subagent_matches) == 0:
            return response
        for id, query in subagent_matches:
            print(
                f"\n--------\nSpawning subagent with id: {id}, query: {query}\n--------\n"
            )
            subagent = CodeActSubagentHarness(
                self.model_name, is_subagent=True, query=query
            )
            subagent_res = await subagent.run_agent()
            print(f"Subagent result for query '{query}': {subagent_res}")
            self.messages.append(
                {
                    "role": "tool",
                    "content": f"Subagent with id {id} completed query '{query}' with result:\n{subagent_res}",
                }
            )
        return await self.process_response()

    async def process_code_blocks(self, response: ChatCompletion):
        content = response.choices[0].message.content or ""
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
                    "content": f"Executed code block with result:\n{repl_result}",
                }
            )
        return await self.process_response()

    async def process_response(self):
        response = await self.process_subagents(
            await self.process_code_blocks(await self.llm(self.messages))
        )
        if response.choices[0].finish_reason == "stop":
            return response
        else:
            return await self.process_response()

    async def run_agent(self):
        self.setup_messages()
        print(f"Running CodeActSubagentHarness with model {self.model_name}")
        final_res = await self.process_response()
        print("\n--------\n")
        return (
            final_res.choices[0].message.content
            if final_res
            else "Subagent did not return a response."
        )

    async def run(self):
        self.setup_messages()
        print(f"Running CodeActHarness with model {self.model_name}")
        while True:
            try:
                user_input = self.take_user_input()
            except Exit:
                print("Exiting CodeActHarness.")
                break
            self.messages.append({"role": "user", "content": user_input})
            response = await self.process_response()
            self.messages.append(
                {"role": "assistant", "content": response.choices[0].message.content}
            )
            print(
                f"Assistant response in REPL:\n{self.repl.namespace['final_content']}"
            )
            self.display_output(response)


if __name__ == "__main__":
    harness = CodeActSubagentHarness("qwen3.5-9B", is_subagent=False)
    import asyncio

    asyncio.run(harness.run())
