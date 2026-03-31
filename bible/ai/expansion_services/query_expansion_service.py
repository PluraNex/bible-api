"""
Query Expansion Service - Orquestra cache + LLM para expansão dinâmica.

Este serviço implementa o padrão Cache-Aside:
1. Verifica se a expansão já existe no cache (DB)
2. Se existe, retorna do cache e incrementa uso
3. Se não existe, chama o LLM Tool e salva no cache

Fluxo:
    User busca "perdão"
    → Service.expand("perdão")
    → Verifica QueryExpansionCache (DB)
    → MISS: Chama QueryExpansionTool (LLM)
    → Salva no cache
    → Retorna expansão
    
    Próxima busca "perdão"
    → HIT: Retorna do cache (sem chamar LLM)

Versão: 1.0.0
Data: Nov 2025
"""

from __future__ import annotations

import logging
import unicodedata
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

if TYPE_CHECKING:
    from bible.models import QueryExpansionCache

logger = logging.getLogger(__name__)


@dataclass
class DynamicExpansionResult:
    """Resultado da expansão dinâmica."""

    query: str
    query_normalized: str
    theological_synonyms: list[str]
    morphological_variants: list[str]
    related_concepts: list[str]
    from_cache: bool
    model_used: str | None
    expansion_type: str

    def get_all_terms(self) -> list[str]:
        """Retorna todos os termos expandidos."""
        return (
            self.theological_synonyms
            + self.morphological_variants
            + self.related_concepts
        )

    def to_tsquery(self) -> str:
        """
        Converte para formato tsquery do PostgreSQL.
        
        Prioriza a query original (frase completa) e adiciona sinônimos.
        Usa operador de distância <N> para matches de frases com gap.
        
        Exemplo:
            Query: "paz na terra"
            Resultado: "(paz <2> terra) | paz | terra | tranquilidade | serenidade"
            
        O operador <2> busca palavras com até 1 palavra entre elas.
        Isso permite encontrar "paz na terra" onde "na" é stopword.
        """
        import re
        
        # 1. Preparar query original como frase (palavras significativas)
        query_clean = re.sub(r"[^\w\s]", "", self.query_normalized.lower().strip())
        query_words = [w for w in query_clean.split() if len(w) > 2]
        
        # Criar frase com operador de distância <2> (permite 1 palavra entre)
        # Isso é melhor que <-> pois permite stopwords como "na", "de", "em"
        phrase_query = ""
        if len(query_words) >= 2:
            # Usa <2> para permitir 1 gap entre palavras
            # Exemplo: "paz <2> terra" encontra "paz na terra"
            phrase_query = " <2> ".join(query_words)
        elif len(query_words) == 1:
            phrase_query = query_words[0]
        
        # 2. Adicionar termos expandidos (sinônimos individuais)
        expanded_terms = []
        seen = set(query_words)  # Não duplicar palavras da query original
        
        for term in self.get_all_terms():
            # Sanitizar termo
            clean = re.sub(r"[^\w\s]", "", term.lower().strip())
            words = [w for w in clean.split() if len(w) > 2]
            
            for word in words:
                if word and word not in seen:
                    seen.add(word)
                    expanded_terms.append(word)
        
        # 3. Montar tsquery final: (frase) | termo1 | termo2 | ...
        all_parts = []
        
        # Frase original com alta prioridade (entre parênteses)
        if phrase_query:
            if " <2> " in phrase_query:
                all_parts.append(f"({phrase_query})")  # Frase entre parênteses
            else:
                all_parts.append(phrase_query)
        
        # Adicionar cada palavra da query original individualmente também
        # (para matches parciais quando a frase não está presente)
        for word in query_words:
            if word not in [p.strip("()") for p in all_parts]:
                all_parts.append(word)
        
        # Adicionar sinônimos (limitado para não diluir relevância)
        all_parts.extend(expanded_terms[:6])
        
        return " | ".join(all_parts)

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "query": self.query,
            "query_normalized": self.query_normalized,
            "theological_synonyms": self.theological_synonyms,
            "morphological_variants": self.morphological_variants,
            "related_concepts": self.related_concepts,
            "from_cache": self.from_cache,
            "model_used": self.model_used,
            "expansion_type": self.expansion_type,
            "all_terms": self.get_all_terms(),
        }


class QueryExpansionService:
    """
    Serviço de expansão de query com cache.

    Orquestra o cache (DB) e o LLM Tool para fornecer expansões
    de forma eficiente e econômica.

    Exemplo:
        service = QueryExpansionService()
        result = service.expand("perdão")
        print(result.theological_synonyms)  # ["remissão", "absolvição", ...]
        print(result.from_cache)  # True se veio do cache
    """

    def __init__(
        self,
        use_cache: bool = True,
        use_llm: bool = True,
        use_static_fallback: bool = True,
        llm_model: str | None = None,
    ):
        """
        Inicializa o serviço.

        Args:
            use_cache: Usar cache do banco de dados
            use_llm: Usar LLM para expansões não-cacheadas
            use_static_fallback: Usar dicionário estático como fallback
            llm_model: Modelo LLM a usar (default: gpt-4o-mini)
        """
        self.use_cache = use_cache
        self.use_llm = use_llm
        self.use_static_fallback = use_static_fallback
        self.llm_model = llm_model

    def expand(self, query: str) -> DynamicExpansionResult:
        """
        Expande uma query com cache inteligente.

        Args:
            query: Termo ou frase para expandir

        Returns:
            DynamicExpansionResult com expansões
        """
        query = query.strip()
        query_normalized = self._normalize_query(query)

        if not query_normalized:
            return self._empty_result(query, query_normalized)

        # 1. Tenta cache
        if self.use_cache:
            cached = self._get_from_cache(query_normalized)
            if cached:
                logger.info(f"QueryExpansion CACHE HIT: '{query_normalized}'")
                return self._result_from_cache(query, query_normalized, cached)

        logger.info(f"QueryExpansion CACHE MISS: '{query_normalized}'")

        # 2. Tenta LLM
        if self.use_llm:
            llm_result = self._expand_with_llm(query_normalized)
            if llm_result and llm_result.success:
                # Salva no cache para próximas buscas
                self._save_to_cache(query, query_normalized, llm_result)
                return DynamicExpansionResult(
                    query=query,
                    query_normalized=query_normalized,
                    theological_synonyms=llm_result.theological_synonyms,
                    morphological_variants=llm_result.morphological_variants,
                    related_concepts=llm_result.related_concepts,
                    from_cache=False,
                    model_used=llm_result.model_used,
                    expansion_type="llm_dynamic",
                )

        # 3. Fallback para dicionário estático
        if self.use_static_fallback:
            static_result = self._expand_with_static(query_normalized)
            if static_result:
                return static_result

        # 4. Retorna vazio se nada funcionou
        return self._empty_result(query, query_normalized)

    def _normalize_query(self, query: str) -> str:
        """
        Normaliza query para lookup no cache.
        
        - Lowercase
        - Remove acentos (perdão → perdao)
        - Remove espaços extras
        """
        query = query.lower().strip()
        # Remove acentos para normalização consistente
        nfkd = unicodedata.normalize("NFKD", query)
        return "".join(c for c in nfkd if not unicodedata.combining(c))

    def _get_from_cache(self, query_normalized: str) -> "QueryExpansionCache | None":
        """Busca expansão no cache do banco."""
        from bible.models import QueryExpansionCache

        try:
            # Busca direta com query normalizada (já sem acentos)
            cached = QueryExpansionCache.objects.filter(
                query_normalized=query_normalized
            ).first()

            if cached:
                # Incrementa contador de uso
                cached.increment_usage()
                return cached

            return None

        except Exception as e:
            logger.warning(f"Error getting from cache: {e}")
            return None

    def _save_to_cache(self, query: str, query_normalized: str, llm_result) -> None:
        """Salva expansão no cache do banco."""
        from bible.models import QueryExpansionCache

        try:
            with transaction.atomic():
                QueryExpansionCache.objects.update_or_create(
                    query_normalized=query_normalized,
                    defaults={
                        "query_original": query,
                        "theological_synonyms": llm_result.theological_synonyms,
                        "morphological_variants": llm_result.morphological_variants,
                        "related_concepts": llm_result.related_concepts,
                        "model_used": llm_result.model_used,
                        "prompt_version": llm_result.prompt_version,
                        "confidence_score": 1.0,
                        "usage_count": 1,
                        "last_used_at": timezone.now(),
                    },
                )
            logger.info(f"QueryExpansion saved to cache: '{query_normalized}'")

        except Exception as e:
            logger.error(f"Error saving to cache: {e}")

    def _expand_with_llm(self, query: str):
        """Expande usando LLM Tool."""
        try:
            from bible.ai.agents.tools import QueryExpansionTool

            tool = QueryExpansionTool(model=self.llm_model)
            return tool.expand(query)

        except Exception as e:
            logger.error(f"LLM expansion failed: {e}")
            return None

    def _expand_with_static(self, query: str) -> DynamicExpansionResult | None:
        """Fallback para dicionário estático."""
        try:
            from bible.ai.query_expansion import expand_query

            static = expand_query(query)

            if static.synonyms_used:
                all_synonyms = []
                for syns in static.synonyms_used.values():
                    all_synonyms.extend(syns)

                return DynamicExpansionResult(
                    query=query,
                    query_normalized=query,
                    theological_synonyms=all_synonyms[:5],
                    morphological_variants=[],
                    related_concepts=[],
                    from_cache=False,
                    model_used=None,
                    expansion_type="static_dictionary",
                )

            return None

        except Exception as e:
            logger.error(f"Static expansion failed: {e}")
            return None

    def _result_from_cache(
        self, query: str, query_normalized: str, cached: "QueryExpansionCache"
    ) -> DynamicExpansionResult:
        """Converte cache para resultado."""
        return DynamicExpansionResult(
            query=query,
            query_normalized=query_normalized,
            theological_synonyms=list(cached.theological_synonyms or []),
            morphological_variants=list(cached.morphological_variants or []),
            related_concepts=list(cached.related_concepts or []),
            from_cache=True,
            model_used=cached.model_used,
            expansion_type="cached",
        )

    def _empty_result(self, query: str, query_normalized: str) -> DynamicExpansionResult:
        """Retorna resultado vazio."""
        return DynamicExpansionResult(
            query=query,
            query_normalized=query_normalized,
            theological_synonyms=[],
            morphological_variants=[],
            related_concepts=[],
            from_cache=False,
            model_used=None,
            expansion_type="none",
        )


# Função de conveniência global
def expand_query_dynamic(
    query: str,
    *,
    use_cache: bool = True,
    use_llm: bool = True,
    use_static_fallback: bool = True,
) -> DynamicExpansionResult:
    """
    Expande query de forma dinâmica com cache + LLM.

    Esta é a função principal para usar no hybrid search.

    Args:
        query: Termo para expandir
        use_cache: Usar cache do banco
        use_llm: Usar LLM se não estiver em cache
        use_static_fallback: Usar dicionário estático como fallback

    Returns:
        DynamicExpansionResult com expansões

    Exemplo:
        result = expand_query_dynamic("perdão")
        print(result.to_tsquery())  # "perdão | remissão | absolvição | ..."
    """
    service = QueryExpansionService(
        use_cache=use_cache,
        use_llm=use_llm,
        use_static_fallback=use_static_fallback,
    )
    return service.expand(query)
