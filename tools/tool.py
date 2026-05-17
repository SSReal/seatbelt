from typing import Dict, Annotated, List, get_origin, get_args

from openai.types.chat.chat_completion_tool_param import (
    ChatCompletionToolParam,
    FunctionDefinition,
)


class Tool:
    def __init__(self, fn, name=None, description=None, schema=None):
        self.fn = fn
        self.name = name or fn.__name__
        self.description = description or fn.__doc__
        self.schema: ChatCompletionToolParam = schema or self.generate_schema()

    def _get_type_string(self, type_obj):
        """Convert a type object to its string representation."""
        if type_obj is str:
            return "string"
        elif type_obj is int:
            return "integer"
        elif type_obj is float:
            return "number"
        elif type_obj is bool:
            return "boolean"
        elif hasattr(type_obj, "__name__"):
            return type_obj.__name__.lower()
        else:
            return str(type_obj)

    def generate_schema(self):
        # examine the parameters of the function and generate a schema
        import inspect

        sig = inspect.signature(self.fn)

        defs = {}
        req = []
        for name, param in sig.parameters.items():
            annotation = param.annotation
            param_type = "string"
            param_description = ""

            if annotation != inspect.Parameter.empty:
                # Check if it's an Annotated type
                if get_origin(annotation) is Annotated:
                    args = get_args(annotation)
                    actual_type = args[0]  # The actual type
                    # The rest of args are metadata
                    if len(args) > 1:
                        param_description = args[1] if isinstance(args[1], str) else ""
                    param_type = self._get_type_string(actual_type)
                else:
                    param_type = self._get_type_string(annotation)
                    param_description = (
                        annotation.__doc__ if hasattr(annotation, "__doc__") else ""
                    )

            defs[name] = {
                "type": param_type,
                "description": param_description,
            }
            if param.default == inspect.Parameter.empty:
                req.append(name)

        return ChatCompletionToolParam(
            function=FunctionDefinition(
                name=self.name,
                description=self.description,
                parameters={"type": "object", "properties": defs, "required": req},
            ),
            type="function",
        )

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


def generate_tool_prompt(tools: Dict[str, Tool]):
    tool_defs = [tool.schema for tool in tools.values()]
    return tool_defs


def discover_tools(folder_path: str) -> Dict[str, Tool]:
    import os
    import importlib.util

    tools = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            module_path = os.path.join(folder_path, filename)
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if not spec or not spec.loader:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for attr_name in dir(module):
                if attr_name.startswith("_"):
                    continue
                attr = getattr(module, attr_name)
                # Only include user-defined functions from this module
                if (
                    callable(attr)
                    and hasattr(attr, "__module__")
                    and attr.__module__ == module_name
                ):
                    tool = Tool(attr)
                    tools[tool.name] = tool

    return tools


if __name__ == "__main__":
    import asyncio

    async def main():
        tools = discover_tools("./user_tools")
        for name, tool in tools.items():
            print(f"Discovered tool: {name}")
            print(f"Schema: {tool.schema}")

    asyncio.run(main())
