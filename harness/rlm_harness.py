import re

from harness.code_act_subagent_harness import CodeActSubagentHarness
from openai.types.chat import ChatCompletion

from harness.harness import Exit


class RLMHarness(CodeActSubagentHarness):
    def __init__(self, model_name, *args, **kwargs):
        super().__init__(model_name, *args, **kwargs)
        self.sys_prompt = kwargs.get("system_prompt", "")
        self.sys_prompt += (
            "The query is accessible via the get_query(start, stop, step) function. You can call it to retrieve the query. You also have the function get_query_len which returns the length of the query. "
            "It accepts the standard parameters for slicing, so you can do get_query(0, 10) to get the first 10 characters of the query, or get_query(stop=-10) to get the last 10 characters of the query. "
            "Calling get_query() with no parameters or with the default parameters will return an error message to prevent infinite recursion, so always use slicing parameters when calling get_query()."
            "Try to piece the query together using multiple calls to get_query with different slicing parameters if the query is long and you can't fit the whole thing in your context at once."
            "Remember, the goal is to complete the query as effectively as possible, so make sure to retrieve and use the relevant parts of the query in your response."
            "Divide the query into manageable parts and use the get_query function to access those parts as needed to construct your response. "
            "Don't forget to consider the entire query and not just the part you can see in the current context window, since you can retrieve any part of the query using get_query."
        )
        self.setup_messages()

    def setup_messages(self):
        self.messages = [
            {
                "role": "system",
                "content": self.sys_prompt + self.code_prompt + self.subagent_prompt,
            }
        ]
        if self.is_subagent:
            self.repl.namespace["get_query"] = self.create_getter(self.query)
            self.repl.namespace["get_query_len"] = lambda: len(self.query)
            self.messages.append(
                {
                    "role": "user",
                    "content": "user has provided a new query in the 'query' variable.",
                }
            )

    @staticmethod
    def create_getter(s: str):
        def getter(start=0, stop=-1, step=1):
            if start == 0 and stop == -1 and step == 1:
                return "ERROR: the full query has been redacted to prevent infinite recursion. Please use slicing parameters to access a portion of the query."
            return s[start:stop:step]

        return getter

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
            subagent = RLMHarness(self.model_name, is_subagent=True, query=query)
            subagent_res = await subagent.run_agent()
            print(f"Subagent result for query '{query}': {subagent_res}")
            self.repl.namespace[f"__subagent_{id}"] = subagent_res
            self.messages.append(
                {
                    "role": "tool",
                    "content": f"Subagent with id {id} completed the query and stored it in the variable in the environment as subagent_{id}.",
                }
            )
        return await self.process_response()

    async def run(self):
        self.setup_messages()
        print(f"Running Recursive Language Model Harness with model {self.model_name}")
        while True:
            try:
                user_input = self.take_user_input()
            except Exit:
                print("Exiting Recursive Language Model Harness.")
                break
            self.query = user_input
            self.repl.namespace["get_query"] = self.create_getter(self.query)
            self.repl.namespace["get_query_len"] = lambda: len(self.query)
            self.messages.append(
                {
                    "role": "user",
                    "content": "user has provided a new query. Call get_query() to retrieve it.",
                }
            )
            response = await self.process_response()
            self.messages.append(
                {"role": "assistant", "content": response.choices[0].message.content}
            )
            self.display_output(response)


if __name__ == "__main__":
    harness = RLMHarness("qwen3.5-9B", is_subagent=False, temperature=0.1, top_p=0.9)
    import asyncio

    asyncio.run(harness.run())
