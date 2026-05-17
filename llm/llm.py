import asyncio
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI, Omit
from openai.types.chat import ChatCompletionToolParam


class LLM:

    def __init__(self, model_name):
        self.model_name = model_name
        self.client = AsyncOpenAI(api_key="dummy", base_url="http://localhost:10000/v1")

    async def __call__(
        self, messages, tools: Optional[List[ChatCompletionToolParam]] = None
    ):
        return await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools or [],
        )


async def main():
    llm = LLM("qwen3.5-9B")
    response = await llm(
        [{"role": "user", "content": "What is the capital of France?"}]
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
