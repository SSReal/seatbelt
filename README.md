# Seatbelt

A collection of harness frameworks for building AI agents with Python. Seatbelt provides multiple agent architectures and utilities for creating, managing, and executing agents that interact with Language Models (LLMs) and external tools.

## Features

- **Multiple Harness Implementations**: Choose from different agent architectures:
    - **Simple Harness**: Lightweight baseline implementation for initial testing
    - **ReAct Harness**: Agentic Behavior (tool-use) in a Reason-Act loop.
    - **CodeAct Harness**: Code running framework on top of ReAct.
    - **Code Act Subagent Harness**: Code-Act loop augmented with subagents.
    - **RLM Harness**: Recursive Language Models implementation.

- **Tool Integration**: Easy-to-use tool system for extending agent capabilities
- **LLM Integration**: Built-in support for OpenAI models and extensible LLM interface
- **Message Logging**: Automatic conversation history tracking and logging
- **User Interaction**: Interactive user input handling with graceful exit mechanisms

## Project Structure

```
seatbelt/
├── harness/                    # Core harness frameworks
│   ├── harness.py             # Base Harness abstract class
│   ├── react_harness.py       # ReAct (Reasoning + Acting) implementation
│   ├── rlm_harness.py         # Recursive Language Model harness
│   ├── code_act_harness.py    # Code-Act loop
│   ├── code_act_subagent_harness.py  # Code-Act with Subagents
│   └── simple_harness.py      # Simple/baseline implementation
├── tools/                      # Tool framework for agents
│   ├── tool.py                # Base Tool class
│   └── user_tools/            # Custom user-defined tools (examples)
│       ├── greet.py           # Greeting utility
│       ├── math.py            # Mathematical operations
│       └── strings.py         # String manipulation
├── llm/                        # Language Model interface
│   └── llm.py                 # LLM abstraction and integration
├── prompts/                    # Prompt templates
│   └── rlm_prompt.py          # RLM-specific prompts
├── repl/                       # REPL interface
│   └── REPL.py                # Interactive REPL environment
├── pyproject.toml             # Project configuration and dependencies
└── main.py                     # Entry point
```

## Requirements

- Python >= 3.13
- Dependencies:
    - `numpy >= 2.4.5` - Numerical computing
    - `openai >= 2.37.0` - OpenAI API integration
    - `pandas >= 3.0.3` - Data manipulation

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd seatbelt
```

2. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -e .
```

Or install manually:

```bash
pip install numpy>=2.4.5 openai>=2.37.0 pandas>=3.0.3
```

## Usage

### Basic Agent Setup

```python
from harness.react_harness import ReactHarness

# Create an agent instance
agent = ReactHarness(model_name="gpt-4")

# Run the agent
import asyncio
asyncio.run(agent.run())
```

### Creating Custom Tools

```python
from tools.tool import Tool

def my_tool(input_text: str) -> str:
    """A custom tool that processes text."""
    return f"Processed: {input_text}"

tool = Tool(my_tool, name="my_tool", description="Processes text input")
```

### Available Tools

The project includes pre-built example utility tools:

- **math.py**: Mathematical operations
- **strings.py**: String manipulation utilities
- **greet.py**: Greeting functions

## Architecture

Each harness extends the base `Harness` class and implements:

- **LLM Integration**: Connects to language models for inference
- **Message Management**: Maintains conversation history
- **Tool Calling**: Executes tools based on LLM output
- **Async Execution**: Full async/await support for I/O operations

## Configuration

Edit `pyproject.toml` to configure:

- Project version
- Python version requirements
- Dependencies and their versions

## Message Logging

Agents automatically log message history:

```python
agent.log_messages()  # Saves conversation to messages_log.txt
```

## How to run

1. Change the OpenAI API configuration in `llm.py`. (Any OpenAI compatible API works, including Ollama, Llama-cpp, etc.)
2. Select the harness to run:
   a. Simple Harness (simple_harness.py)
   b. ReAct Harness (react_harness.py)
   c. Code-Act Harness (code_act_harness.py)
   d. Code-Act Subagent Harness (code_act_subagent_harness.py)
   e. Recursive Language Model Harness (rlm_harness.py)
3. Run the selected python file

    ```python
    python -m harness.<selected_file_name_without_extension>
    ```

    For eg -

    ```python
    python -m harness.react_harness
    ```

## Contributing

Contributions are welcome! Please ensure:

- Code follows Python best practices
- New harnesses extend the base `Harness` class
- Tools implement the `Tool` interface
- Async patterns are used for I/O operations

## Support

For issues or questions, please open an issue on the repository.
