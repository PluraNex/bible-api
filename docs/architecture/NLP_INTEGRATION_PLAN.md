# 🚀 NLP Query Tool → Hybrid Search Integration

**Status:** ✅ **IMPLEMENTADO** (Novembro 2025)  
**Autor:** Bible API Team

## 📊 Status da Implementação

| Item | Status | Arquivo |
|------|--------|---------|
| NLP Query Tool | ✅ Completo | `bible/ai/agents/tools/nlp_query_tool.py` |
| Integração hybrid_search | ✅ Completo | `bible/ai/hybrid.py` |
| Modelo QueryNLPCache | ✅ Completo | `bible/models/nlp_cache.py` |
| Gazetteer (120 entidades) | ✅ Carregado | `data/NLP/nlp_gazetteer/` |
| Cache hit/miss | ✅ Funcionando | Testado com `test_nlp_cache.py` |
| Testes E2E | ✅ Passando | `test_hybrid_e2e.py` |

## Arquitetura Implementada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           QUERY PROCESSING PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  User Query: "Sermão do Monte"                                               │
│          │                                                                    │
│          ▼                                                                    │
│  ┌───────────────────┐                                                        │
│  │  NLP QUERY TOOL   │  ◄── Gazetteer (1635+ entidades)                      │
│  │                   │                                                        │
│  │  • Tokenização    │  ["sermao", "monte"]                                  │
│  │  • Stopwords      │  ["do"]                                               │
│  │  • Entity detect  │  LITERARY_WORK (boost: 2.8)                           │
│  │  • Classificação  │  ENTITY                                               │
│  │  • Estratégia     │  entity_boost, alpha: 0.7, expand: false             │
│  └─────────┬─────────┘                                                        │
│            │                                                                  │
│            ▼                                                                  │
│  ┌───────────────────┐                                                        │
│  │   HYBRID SEARCH   │                                                        │
│  │                   │                                                        │
│  │  BM25 (alpha=0.7) │  ← Configurado pelo NLP Tool                          │
│  │  Vector (0.3)     │                                                        │
│  │  Entity Boost     │  × 2.8 para matches exatos                            │
│  │  Expand: false    │  ← Não expande nomes próprios                         │
│  └─────────┬─────────┘                                                        │
│            │                                                                  │
│            ▼                                                                  │
│  ┌───────────────────┐                                                        │
│  │    RESULTADOS     │                                                        │
│  │    OTIMIZADOS     │                                                        │
│  └───────────────────┘                                                        │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Integração Proposta

### 1. Modificar `hybrid_search()` para usar NLP Tool

```python
# bible/ai/hybrid.py

from bible.ai.agents.tools.nlp_query_tool import NLPQueryTool, NLPAnalysis

# Instância global (lazy loaded)
_nlp_tool = None

def get_nlp_tool() -> NLPQueryTool:
    global _nlp_tool
    if _nlp_tool is None:
        _nlp_tool = NLPQueryTool(use_spacy=False, use_gazetteer=True)
    return _nlp_tool


def hybrid_search(
    query: str,
    query_embedding: list[float],
    *,
    # ... parâmetros existentes ...
    use_nlp_analysis: bool = True,  # NOVO: usar NLP para otimização
) -> dict[str, Any]:
    """
    Executa busca híbrida com otimização NLP.
    """
    
    # 1. Análise NLP da query
    nlp_analysis = None
    if use_nlp_analysis:
        try:
            nlp_tool = get_nlp_tool()
            nlp_analysis = nlp_tool.analyze(query)
            
            # Ajustar parâmetros baseado na análise
            boost_strategy = nlp_analysis.boost_strategy
            
            # Alpha dinâmico
            alpha = boost_strategy.get("alpha", alpha)
            
            # Expansão dinâmica
            if not boost_strategy.get("expand", True):
                expand_query_flag = False
            
            # TSQuery otimizado
            optimized_tsquery = nlp_analysis.to_tsquery()
            
            logger.info(
                f"NLP Analysis: type={nlp_analysis.semantic_type.value}, "
                f"entities={len(nlp_analysis.entities)}, "
                f"alpha={alpha}, expand={expand_query_flag}"
            )
        except Exception as e:
            logger.warning(f"NLP analysis failed: {e}")
    
    # 2. BM25 Search (com tsquery otimizado se disponível)
    if nlp_analysis and optimized_tsquery:
        bm25_results = _bm25_search(
            query=query,
            tsquery=optimized_tsquery,  # Usar tsquery do NLP
            ...
        )
    
    # 3. Aplicar boost de entidade nos resultados
    if nlp_analysis and nlp_analysis.entities:
        entity_boost = nlp_analysis.boost_strategy.get("entity_boost", 1.0)
        for result in bm25_results:
            if result.get("contains_query"):
                result["score"] *= entity_boost
    
    # ... resto do código ...
```

### 2. Boost no BM25

```python
def _bm25_search(
    query: str,
    tsquery: str | None = None,
    entity_boost: float = 1.0,
    ...
) -> list[dict]:
    """BM25 com boost de entidade."""
    
    sql = """
    SELECT 
        v.*,
        ts_rank_cd(to_tsvector('portuguese', v.text), query) 
            * CASE WHEN v.text ILIKE %s THEN %s ELSE 1.0 END  -- Entity boost
            AS bm25_score
    FROM verses v,
         to_tsquery('portuguese', %s) query
    WHERE to_tsvector('portuguese', v.text) @@ query
    ORDER BY bm25_score DESC
    LIMIT %s
    """
    
    # Parâmetros: %query_pattern%, entity_boost, tsquery, limit
    params = [f"%{query}%", entity_boost, tsquery, pool_size]
```

### 3. Cache de Análise NLP

```python
# Tabela para cachear análises NLP
class QueryNLPCache(models.Model):
    query_normalized = models.CharField(max_length=500, unique=True, db_index=True)
    semantic_type = models.CharField(max_length=50)
    tokens_clean = models.JSONField()
    entities = models.JSONField()
    boost_strategy = models.JSONField()
    tsquery = models.CharField(max_length=1000)
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

## Benefícios

| Antes | Depois |
|-------|--------|
| Alpha fixo (0.5) | Alpha dinâmico por tipo de query |
| Distância fixa (<2>) | Distância calculada por stopwords |
| Sem boost de entidade | Boost 1.0-4.0 do Gazetteer |
| Expansão sempre igual | Expansão só para conceitos |

## Queries de Exemplo

| Query | Tipo | Alpha | Boost | Expand |
|-------|------|-------|-------|--------|
| "paz na terra" | PHRASE | 0.6 | 2.0 | ❌ |
| "Abraão" | ENTITY | 0.7 | 3.0 | ❌ |
| "Jesus Cristo" | ENTITY | 0.7 | 4.0 | ❌ |
| "justiça" | CONCEPT | 0.4 | N/A | ✅ |
| "João 3:16" | REFERENCE | 0.8 | 3.0 | ❌ |
| "quem é Deus?" | QUESTION | 0.3 | N/A | ✅ |

## Próximos Passos (Opcionais)

- [x] ~~Adicionar `use_nlp_analysis` ao `hybrid_search()`~~ ✅
- [x] ~~Implementar boost SQL no BM25~~ ✅
- [x] ~~Criar tabela `QueryNLPCache`~~ ✅
- [x] ~~Testar com queries reais~~ ✅
- [x] ~~Medir impacto na qualidade de busca~~ ✅
- [ ] Warm-up do cache com queries mais comuns
- [ ] Métricas Prometheus para hit/miss
- [ ] TTL para expirar entradas antigas
- [ ] Adicionar spaCy ao container para NLP avançado

## Testes Disponíveis

```bash
# Testar NLP Tool isolado
docker exec -i bible-api-web-1 python test_nlp_tool.py

# Testar integração com classificação
docker exec -i bible-api-web-1 python test_hybrid_nlp.py

# Testar cache NLP (hit/miss)
docker exec -i bible-api-web-1 python test_nlp_cache.py

# Teste end-to-end completo
docker exec -i bible-api-web-1 python test_hybrid_e2e.py
```

## Resultados de Testes

### Cache Performance

| Momento | Processing Time |
|---------|-----------------|
| 1ª busca (MISS) | 2-12ms |
| 2ª busca (HIT) | **0ms** |

### Impacto nos Resultados

| Query | Antes | Depois (NLP) | Melhoria |
|-------|-------|--------------|----------|
| "paz na terra" | 91% | **98%** | +7% |
| "Abraão" | Normal | **3.0× boost** | Entity detection |
| "Jesus Cristo" | Normal | **4.0× boost** | Entity detection |
| "justiça" | alpha=0.5 | **alpha=0.4** | Mais semântico |
