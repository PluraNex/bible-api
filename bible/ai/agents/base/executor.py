"""
Tool Executor Base - Classe base para execução de tools.

Fornece interface padrão para mapear function calls para execuções reais.

Autor: Bible API Team
Data: Dezembro 2025
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

logger = logging.getLogger(__name__)


class BaseToolExecutor(ABC):
    """
    Classe base abstrata para executores de tools.
    
    Subclasses devem implementar o método `_get_handlers` para
    retornar o mapeamento de funções.
    
    Exemplo:
        class MyToolExecutor(BaseToolExecutor):
            def _get_handlers(self) -> dict[str, Callable]:
                return {
                    "my_function": self._my_function,
                }
            
            def _my_function(self, arg1: str) -> dict:
                return {"result": arg1}
    """
    
    def __init__(self):
        """Inicializa o executor."""
        self._handlers: dict[str, Callable] = self._get_handlers()
    
    @abstractmethod
    def _get_handlers(self) -> dict[str, Callable]:
        """
        Retorna mapeamento de nomes de função para handlers.
        
        Returns:
            Dict {function_name: handler_callable}
        """
        pass
    
    def execute(self, tool_call: dict) -> dict:
        """
        Executa uma tool call.
        
        Args:
            tool_call: {id, name, arguments}
            
        Returns:
            {tool_call_id, output}
        """
        call_id = tool_call.get("id", "unknown")
        name = tool_call["name"]
        args = tool_call.get("arguments", {})
        
        # Parse arguments se for string JSON
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        
        handler = self._handlers.get(name)
        if not handler:
            logger.warning(f"Unknown tool: {name}")
            return {
                "tool_call_id": call_id,
                "output": {"error": f"Unknown tool: {name}"},
            }
        
        try:
            result = handler(**args)
            return {
                "tool_call_id": call_id,
                "output": result,
            }
        except TypeError as e:
            # Erro de argumentos
            logger.error(f"Tool argument error for {name}: {e}")
            return {
                "tool_call_id": call_id,
                "output": {"error": f"Invalid arguments: {e}"},
            }
        except Exception as e:
            logger.error(f"Tool execution error for {name}: {e}")
            return {
                "tool_call_id": call_id,
                "output": {"error": str(e)},
            }
    
    def execute_all(self, tool_calls: list[dict]) -> list[dict]:
        """
        Executa múltiplas tool calls.
        
        Args:
            tool_calls: Lista de tool calls
            
        Returns:
            Lista de resultados
        """
        return [self.execute(call) for call in tool_calls]
    
    def get_available_tools(self) -> list[str]:
        """Retorna lista de tools disponíveis."""
        return list(self._handlers.keys())


class ToolExecutor(BaseToolExecutor):
    """
    Executor genérico que aceita handlers no construtor.
    
    Exemplo:
        executor = ToolExecutor(handlers={
            "validate": lambda key: {"valid": True},
        })
    """
    
    def __init__(self, handlers: dict[str, Callable] | None = None):
        """
        Inicializa com handlers customizados.
        
        Args:
            handlers: Mapeamento de funções
        """
        self._custom_handlers = handlers or {}
        super().__init__()
    
    def _get_handlers(self) -> dict[str, Callable]:
        return self._custom_handlers
    
    def register(self, name: str, handler: Callable) -> None:
        """
        Registra um novo handler.
        
        Args:
            name: Nome da função
            handler: Callable que implementa a função
        """
        self._handlers[name] = handler
    
    def unregister(self, name: str) -> bool:
        """
        Remove um handler.
        
        Args:
            name: Nome da função
            
        Returns:
            True se removido, False se não existia
        """
        if name in self._handlers:
            del self._handlers[name]
            return True
        return False
