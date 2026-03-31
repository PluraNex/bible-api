"""
OpenAI Responses API Client - Cliente base para agentes.

Usa a nova API /v1/responses com:
- Function calling para tools
- Structured Outputs para respostas tipadas
- Conversation state para multi-turn
- Background mode para operações longas

Autor: Bible API Team
Data: Dezembro 2025
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Flag para verificar disponibilidade
RESPONSES_API_AVAILABLE = True


class ResponsesAPIClient:
    """
    Cliente para a nova OpenAI Responses API.
    
    Exemplo:
        client = ResponsesAPIClient()
        
        # Criar resposta com function calling
        response = client.create_response(
            input="Valide o tópico adoption",
            tools=MY_TOOLS,
        )
        
        # Processar tool calls
        if response["tool_calls"]:
            for call in response["tool_calls"]:
                result = execute_tool(call)
                response = client.continue_with_tool_results(
                    previous_response_id=response["id"],
                    tool_results=[result],
                )
    """
    
    DEFAULT_INSTRUCTIONS = """Você é um assistente especializado em dados bíblicos.
Use as ferramentas disponíveis para executar tarefas e fornecer respostas precisas."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1",
        instructions: str | None = None,
    ):
        """
        Inicializa o cliente.
        
        Args:
            api_key: Chave da API OpenAI
            model: Modelo a usar
            base_url: URL base da API
            instructions: System instructions padrão
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url
        self.instructions = instructions or self.DEFAULT_INSTRUCTIONS
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        self._client = None
    
    @property
    def client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai>=1.40.0")
        return self._client
    
    def create_response(
        self,
        input: str | list[dict],
        tools: list[dict] | None = None,
        text_format: dict | None = None,
        instructions: str | None = None,
        previous_response_id: str | None = None,
        store: bool = True,
        temperature: float = 0.3,
        max_output_tokens: int | None = None,
    ) -> dict:
        """
        Cria uma resposta usando a Responses API.
        
        Args:
            input: Texto ou lista de items de input
            tools: Lista de tools disponíveis
            text_format: Schema para Structured Output
            instructions: System instructions (opcional)
            previous_response_id: ID de resposta anterior (multi-turn)
            store: Se deve armazenar a resposta
            temperature: Temperatura de sampling
            max_output_tokens: Limite de tokens de saída
            
        Returns:
            Response object normalizado
        """
        request_body = {
            "model": self.model,
            "input": input,
            "temperature": temperature,
            "store": store,
        }
        
        if instructions:
            request_body["instructions"] = instructions
        elif not previous_response_id:
            request_body["instructions"] = self.instructions
        
        if tools:
            request_body["tools"] = tools
            request_body["tool_choice"] = "auto"
        
        if text_format:
            request_body["text"] = {"format": text_format}
        
        if previous_response_id:
            request_body["previous_response_id"] = previous_response_id
        
        if max_output_tokens:
            request_body["max_output_tokens"] = max_output_tokens
        
        try:
            # Usar a nova API de responses
            response = self.client.responses.create(**request_body)
            return self._parse_response(response)
        except AttributeError:
            # Fallback para chat completions se responses não disponível
            logger.warning("Responses API not available, falling back to chat completions")
            return self._fallback_chat_completions(request_body)
    
    def _parse_response(self, response) -> dict:
        """Parse response object para dict normalizado."""
        result = {
            "id": response.id,
            "status": response.status,
            "model": response.model,
            "output": [],
            "tool_calls": [],
            "text": None,
            "usage": None,
        }
        
        # Parse output items
        for item in response.output:
            if item.type == "message":
                for content in item.content:
                    if content.type == "output_text":
                        result["text"] = content.text
                        result["output"].append({
                            "type": "text",
                            "content": content.text,
                        })
            elif item.type == "function_call":
                result["tool_calls"].append({
                    "id": item.id,
                    "name": item.name,
                    "arguments": json.loads(item.arguments) if isinstance(item.arguments, str) else item.arguments,
                })
        
        if response.usage:
            result["usage"] = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        return result
    
    def _fallback_chat_completions(self, request_body: dict) -> dict:
        """Fallback para chat completions API."""
        messages = []
        
        # System message
        if request_body.get("instructions"):
            messages.append({
                "role": "system",
                "content": request_body["instructions"],
            })
        
        # User message
        input_content = request_body.get("input")
        if isinstance(input_content, str):
            messages.append({"role": "user", "content": input_content})
        elif isinstance(input_content, list):
            for item in input_content:
                if isinstance(item, dict):
                    messages.append(item)
                else:
                    messages.append({"role": "user", "content": str(item)})
        
        # Preparar request
        chat_request = {
            "model": request_body["model"],
            "messages": messages,
            "temperature": request_body.get("temperature", 0.3),
        }
        
        if request_body.get("tools"):
            chat_request["tools"] = request_body["tools"]
            chat_request["tool_choice"] = "auto"
        
        if request_body.get("text", {}).get("format"):
            chat_request["response_format"] = request_body["text"]["format"]
        
        if request_body.get("max_output_tokens"):
            chat_request["max_tokens"] = request_body["max_output_tokens"]
        
        response = self.client.chat.completions.create(**chat_request)
        
        # Parse para formato normalizado
        result = {
            "id": response.id,
            "status": "completed",
            "model": response.model,
            "output": [],
            "tool_calls": [],
            "text": None,
            "usage": None,
        }
        
        message = response.choices[0].message
        
        if message.content:
            result["text"] = message.content
            result["output"].append({
                "type": "text",
                "content": message.content,
            })
        
        if message.tool_calls:
            for tc in message.tool_calls:
                result["tool_calls"].append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments,
                })
        
        if response.usage:
            result["usage"] = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        return result
    
    def continue_with_tool_results(
        self,
        previous_response_id: str,
        tool_results: list[dict],
    ) -> dict:
        """
        Continua uma conversa com resultados de tool calls.
        
        Args:
            previous_response_id: ID da resposta anterior
            tool_results: Lista de resultados [{tool_call_id, output}]
            
        Returns:
            Nova response
        """
        # Formatar tool results como input items
        input_items = []
        for result in tool_results:
            input_items.append({
                "type": "function_call_output",
                "call_id": result["tool_call_id"],
                "output": json.dumps(result["output"], ensure_ascii=False) if isinstance(result["output"], dict) else str(result["output"]),
            })
        
        return self.create_response(
            input=input_items,
            previous_response_id=previous_response_id,
        )
