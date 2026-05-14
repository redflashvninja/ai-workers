from __future__ import annotations

import json
from typing import Any, Callable
import anthropic
from config import CLAUDE_MODEL


class ToolError(Exception):
    pass


class BaseAgent:
    """
    Runs a tool-use loop against Claude until the model returns end_turn.
    Subclasses register tools via self._tools and self._handlers.
    """

    def __init__(self, client: anthropic.Anthropic, system_prompt: str):
        self.client = client
        self.model = CLAUDE_MODEL
        self.system_prompt = system_prompt
        self._tools: list[dict] = []
        self._handlers: dict[str, Callable] = {}

    def _register_tool(self, name: str, description: str, input_schema: dict, handler: Callable):
        self._tools.append({
            "name": name,
            "description": description,
            "input_schema": input_schema,
        })
        self._handlers[name] = handler

    def _dispatch(self, tool_name: str, tool_input: dict) -> Any:
        handler = self._handlers.get(tool_name)
        if handler is None:
            raise ToolError(f"Unknown tool: {tool_name}")
        return handler(**tool_input)

    def run(self, user_message: str, context: str = "") -> str:
        system = self.system_prompt
        if context:
            system += f"\n\nAdditional context:\n{context}"

        messages = [{"role": "user", "content": user_message}]

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8096,
                system=system,
                tools=self._tools,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        try:
                            result = self._dispatch(block.name, block.input)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result, default=str),
                            })
                        except Exception as e:
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Error: {e}",
                                "is_error": True,
                            })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                return self._extract_text(response)

    def _extract_text(self, response) -> str:
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)
