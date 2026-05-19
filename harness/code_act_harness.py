import os
from pathlib import Path

from harness.harness import Exit, Harness
from repl.REPL import REPL


class CodeActHarness(Harness):
    def __init__(self, model_name, *args, **kwargs):
        super().__init__(model_name, *args, **kwargs)
        self.allowed_modules = kwargs.get("allowed_modules", set())
        self.blocked_modules = kwargs.get("blocked_modules", set())
        self.sys_prompt = kwargs.get(
            "system_prompt",
            "You are a helpful assistant that executes Python code in a secure REPL environment. Only use the provided safe modules and file access methods. Do not attempt to import blocked modules or access unauthorized files.",
        )

        self.code_prompt = """
To run python code, wrap it in triple backticks with 'python' after the first three backticks, like this:
```python
# your code here
```
Only use this format for code you want to execute. Do not include any other text in the code block.
It behaves like a jupyter notebook cell, the last expression's value will be returned as the result. 
Don't use print statements, just write the expression you want the result of. 
You can have multiple lines of code, but only the last expression's value will be returned. 
If you don't want to return anything, end with a statement instead of an expression.

ONLY USE THIS FEATURE FOR ACTUAL CODE YOU WANT TO EXECUTE. DO NOT USE IT FOR ANYTHING ELSE. IF YOU JUST WANT TO RETURN TEXT, DO NOT WRAP IT IN A CODE BLOCK.
"""
        self.sys_prompt += self.code_prompt

        # Set allowed_dirs to project root's tmp folder (independent of cwd)
        project_root = Path(__file__).parent.parent
        self.tmp_dir = project_root / "repl_workspace"
        self.tmp_dir.mkdir(exist_ok=True)  # Ensure tmp folder exists
        self.allowed_dirs = [str(self.tmp_dir)]
        self.repl = REPL(
            allowed_dirs=self.allowed_dirs,
            allowed_modules=self.allowed_modules,
            blocked_modules=self.blocked_modules,
            cwd=str(self.tmp_dir),
        )
        self.messages = [
            {
                "role": "system",
                "content": self.sys_prompt,
            }
        ]

    async def run(self):
        print(f"Running CodeActHarness with model {self.model_name}")
        while True:
            try:
                user_input = self.take_user_input()
            except Exit:
                print("Exiting CodeActHarness.")
                break
            self.messages.append({"role": "user", "content": user_input})
            response = await self.llm(self.messages)
            self.messages.append(
                {"role": "assistant", "content": response.choices[0].message.content}
            )
            self.display_output(response)
            # Check for code blocks in the assistant's message
            code_blocks = self.extract_code_blocks(response.choices[0].message.content)
            if len(code_blocks) > 0:
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
                response = await self.llm(self.messages)
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": response.choices[0].message.content,
                    }
                )
                self.display_output(response)

    def extract_code_blocks(self, text):
        import re

        code_blocks = re.findall(r"```python\n(.*?)\n```", text, re.DOTALL)
        return code_blocks


if __name__ == "__main__":

    harness = CodeActHarness("qwen3.5-9B")
    print("REPL initialized with security controls enabled.")
    print(f"Working directory: {harness.repl.cwd}")
    print(f"Allowed directories: {harness.repl.file_access.allowed_dirs}")
    print(
        f"Allowed modules: {', '.join(sorted(harness.repl.import_interceptor.allowed_modules))}"
    )
    print(
        f"Blocked modules: {', '.join(sorted(harness.repl.import_interceptor.blocked_modules))}"
    )

    import asyncio

    asyncio.run(harness.run())
