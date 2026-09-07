from __future__ import annotations

import os
from typing import Any

from .base import ModelReply, ToolCall


class GeminiClient:
    """Thin adapter around the Google Gen AI SDK with manual tool execution."""

    def __init__(self, model: str, temperature: float = 0.0):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required for the Gemini provider")
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover - depends on optional live setup
            raise RuntimeError("Install requirements.txt before using Gemini") from exc
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._temperature = temperature

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system_prompt: str,
    ) -> ModelReply:
        from google.genai import types

        transcript = []
        for message in messages:
            transcript.append(f"[{message.get('role', 'user')}] {message.get('content', '')}")
        declarations = [
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters_json_schema=tool["parameters"],
            )
            for tool in tools
        ]
        response = self._client.models.generate_content(
            model=self._model,
            contents="\n".join(transcript),
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=self._temperature,
                tools=[types.Tool(function_declarations=declarations)],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )

        text_parts: list[str] = []
        calls: list[ToolCall] = []
        candidate = response.candidates[0] if response.candidates else None
        if candidate and candidate.content:
            for part in candidate.content.parts or []:
                if getattr(part, "text", None):
                    text_parts.append(part.text)
                function_call = getattr(part, "function_call", None)
                if function_call:
                    calls.append(
                        ToolCall(
                            name=function_call.name,
                            arguments=dict(function_call.args or {}),
                            call_id=getattr(function_call, "id", None),
                        )
                    )
        usage_metadata = getattr(response, "usage_metadata", None)
        usage = {}
        if usage_metadata:
            usage = {
                "input_tokens": int(getattr(usage_metadata, "prompt_token_count", 0) or 0),
                "output_tokens": int(getattr(usage_metadata, "candidates_token_count", 0) or 0),
            }
        return ModelReply(text="\n".join(text_parts), tool_calls=calls, usage=usage)
