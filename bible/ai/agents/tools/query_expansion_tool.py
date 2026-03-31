"""
Query Expansion Tool - LLM-based query expansion for Bible search.

Este tool usa GPT-4o para expandir queries de busca bíblica com:
1. Sinônimos teológicos - termos com significado similar no contexto bíblico
2. Variações morfológicas - diferentes formas da mesma palavra
3. Conceitos relacionados - termos que frequentemente aparecem juntos

Responsabilidade Única: Chamar LLM e retornar expansão estruturada.
O cache e orquestração são responsabilidade do QueryExpansionService.

Versão: 1.0.0
Data: Nov 2025
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from openai import OpenAI

logger = logging.getLogger(__name__)

# Prompt para expansão de query teológica
EXPANSION_PROMPT_V1 = """Você é um especialista em teologia bíblica e linguística portuguesa.

Dado o termo de busca "{query}", gere expansões para melhorar a busca semântica em uma base de versículos bíblicos.

Retorne um JSON com EXATAMENTE esta estrutura:
{{
    "theological_synonyms": ["termo1", "termo2", "termo3"],
    "morphological_variants": ["termo1", "termo2", "termo3"],
    "related_concepts": ["termo1", "termo2", "termo3"]
}}

Regras:
1. theological_synonyms: 3-5 sinônimos que têm MESMO significado no contexto bíblico
   - Ex: "perdão" → ["remissão", "absolvição", "misericórdia"]
   - Ex: "salvação" → ["redenção", "libertação", "resgate"]

2. morphological_variants: 2-4 formas diferentes da MESMA palavra (verbos, substantivos)
   - Ex: "perdão" → ["perdoar", "perdoado", "perdoando"]
   - Ex: "amor" → ["amar", "amou", "amado"]

3. related_concepts: 2-4 conceitos que FREQUENTEMENTE aparecem junto no contexto bíblico
   - Ex: "perdão" → ["arrependimento", "graça", "reconciliação"]
   - Ex: "fé" → ["obras", "justificação", "crença"]

Importante:
- Retorne APENAS o JSON, sem explicações
- Use português brasileiro
- Máximo 5 termos por categoria
- Foque em termos que aparecem na Bíblia
"""


@dataclass
class ExpansionResult:
    """Resultado da expansão de query pelo LLM."""

    query: str
    theological_synonyms: list[str]
    morphological_variants: list[str]
    related_concepts: list[str]
    model_used: str
    prompt_version: str
    success: bool
    error: str | None = None

    def get_all_terms(self) -> list[str]:
        """Retorna todos os termos expandidos."""
        return (
            self.theological_synonyms
            + self.morphological_variants
            + self.related_concepts
        )

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "query": self.query,
            "theological_synonyms": self.theological_synonyms,
            "morphological_variants": self.morphological_variants,
            "related_concepts": self.related_concepts,
            "model_used": self.model_used,
            "prompt_version": self.prompt_version,
            "success": self.success,
            "error": self.error,
        }


class QueryExpansionTool:
    """
    Tool de expansão de query usando LLM.

    Responsabilidade única: chamar o LLM e retornar expansão estruturada.

    Exemplo de uso:
        tool = QueryExpansionTool()
        result = tool.expand("perdão")
        print(result.theological_synonyms)  # ["remissão", "absolvição", ...]
    """

    DEFAULT_MODEL = "gpt-4o-mini"
    PROMPT_VERSION = "v1"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        """
        Inicializa o tool.

        Args:
            model: Modelo OpenAI a usar (default: gpt-4o-mini)
            api_key: API key OpenAI (default: usa env OPENAI_API_KEY)
            timeout: Timeout para chamada API
        """
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()

    def expand(self, query: str) -> ExpansionResult:
        """
        Expande uma query usando o LLM.

        Args:
            query: Termo ou frase para expandir

        Returns:
            ExpansionResult com os termos expandidos
        """
        query = query.strip().lower()

        if not query:
            return ExpansionResult(
                query=query,
                theological_synonyms=[],
                morphological_variants=[],
                related_concepts=[],
                model_used=self.model,
                prompt_version=self.PROMPT_VERSION,
                success=False,
                error="Query vazia",
            )

        try:
            response = self._call_llm(query)
            parsed = self._parse_response(response)

            return ExpansionResult(
                query=query,
                theological_synonyms=parsed.get("theological_synonyms", [])[:5],
                morphological_variants=parsed.get("morphological_variants", [])[:4],
                related_concepts=parsed.get("related_concepts", [])[:4],
                model_used=self.model,
                prompt_version=self.PROMPT_VERSION,
                success=True,
            )

        except Exception as e:
            logger.error(f"QueryExpansionTool error for '{query}': {e}")
            return ExpansionResult(
                query=query,
                theological_synonyms=[],
                morphological_variants=[],
                related_concepts=[],
                model_used=self.model,
                prompt_version=self.PROMPT_VERSION,
                success=False,
                error=str(e),
            )

    def _call_llm(self, query: str) -> str:
        """Chama o LLM com o prompt de expansão."""
        prompt = EXPANSION_PROMPT_V1.format(query=query)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente especializado em teologia bíblica. Responda apenas em JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Baixa temperatura para consistência
            max_tokens=500,
            timeout=self.timeout,
        )

        return response.choices[0].message.content or ""

    def _parse_response(self, response: str) -> dict:
        """Parse a resposta JSON do LLM."""
        # Remove possíveis marcadores de código
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        try:
            data = json.loads(response.strip())
        except json.JSONDecodeError:
            # Tenta extrair JSON de dentro do texto
            import re

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                raise ValueError(f"Não foi possível parsear resposta: {response[:200]}")

        # Validar estrutura
        result = {
            "theological_synonyms": [],
            "morphological_variants": [],
            "related_concepts": [],
        }

        for key in result.keys():
            if key in data and isinstance(data[key], list):
                # Filtra apenas strings válidas
                result[key] = [
                    str(item).strip().lower()
                    for item in data[key]
                    if item and isinstance(item, str)
                ]

        return result


# Função de conveniência para uso rápido
def expand_query_with_llm(query: str, model: str | None = None) -> ExpansionResult:
    """
    Função de conveniência para expandir query.

    Args:
        query: Termo para expandir
        model: Modelo a usar (default: gpt-4o-mini)

    Returns:
        ExpansionResult com expansões
    """
    tool = QueryExpansionTool(model=model)
    return tool.expand(query)
