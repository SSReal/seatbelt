import json
from typing import Dict, cast
from harness.harness import Exit, Harness
from tools.tool import Tool, discover_tools, generate_tool_prompt
from openai.types.chat import ChatCompletionMessageFunctionToolCall


class ReactHarness(Harness):
    def __init__(self, model_name, *args, **kwargs):
        super().__init__(model_name, *args, **kwargs)
        self.tools: Dict[str, Tool] = kwargs.get("tools", {})
        self.tool_defs = [tool.schema for tool in self.tools.values()]
        self.sys_prompt = kwargs.get("sys_prompt", "You are a helpful assistant.")
        self.messages = [
            {
                "role": "system",
                "content": self.sys_prompt,
            }
        ]

    async def run(self):
        print(f"Running ReAct Harness with model {self.model_name}")
        while True:
            try:
                user_input = self.take_user_input()
            except Exit:
                print("Exiting ReAct Harness.")
                break
            self.messages.append({"role": "user", "content": user_input})
            response = await self.llm(self.messages, tools=self.tool_defs)
            while (
                response.choices[0].message.tool_calls
                and response.choices[0].finish_reason != "stop"
            ):
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": response.choices[0].message.content,
                    }
                )
                for tool_call in response.choices[0].message.tool_calls:
                    tool_call = cast(ChatCompletionMessageFunctionToolCall, tool_call)
                    tool = self.tools.get(tool_call.function.name)
                    self.display_tool_call(tool_call)
                    if tool:
                        tool_response = tool(**json.loads(tool_call.function.arguments))
                        self.messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": tool_response,
                            }
                        )
                        print(f"Tool response: {tool_response}")
                    else:
                        print(f"Tool {tool_call.function.name} not found.")
                response = await self.llm(self.messages, tools=self.tool_defs)
            self.messages.append(
                {"role": "assistant", "content": response.choices[0].message.content}
            )
            self.display_output(response)

    def display_tool_call(self, tool_call):
        print(
            f"Tool call: {tool_call.function.name} with arguments {json.dumps(json.loads(tool_call.function.arguments), indent=2)}"
        )


if __name__ == "__main__":
    harness = ReactHarness(
        "qwen3.5-9B",
        tools=discover_tools("tools/user_tools"),
        sys_prompt="You are a helpful assistant that can use tools to answer user questions.",
    )
    try:
        import asyncio

        asyncio.run(harness.run())
    except KeyboardInterrupt:
        print("Exiting ReAct Harness.")
