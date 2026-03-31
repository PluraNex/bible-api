# RAG Optimization Plan - Bible API

## 📊 Estado Atual (Baseline - Nov 2025)

### Dados de Embeddings

| Tabela | Registros | Tamanho | Índice HNSW |
|--------|-----------|---------|-------------|
| `verse_embeddings` | 528,995 | 15 GB | 3.99 GB (small) |
| `unified_verse_embeddings` | 31,074 | 915 MB | 243 MB |

### Modelos de Embedding

| Modelo | Dimensão | Status |
|--------|----------|--------|
| `text-embedding-3-small` | 1536 | ✅ Ativo (recall) |
| `text-embedding-3-large` | 3072 | ✅ Populado (rerank) |

### Versões com Embeddings (17 versões)

```
Português: ACF, ARA, ARC, AS21, NAA, NTLH, NVI, NVT
Inglês: AKJV, ASV, BSB, DARBY, DRC, GENEVA1599, KJV, WEBSTER, YLT
```

### Configuração Atual

```env
RAG_ALLOWED_VERSIONS=ACF,ARA,ARC,AS21,NAA,NTLH,NVI,NVT,...
RAG_RERANK_LARGE=1  # Reranking com large ativado
RAG_HYBRID=0        # Busca híbrida desativada (usar endpoint /hybrid/)
```

---

## ✅ IMPLEMENTADO: Hybrid Search (Fase 1)

### Descrição
Combinação de BM25 (lexical) + Vetorial (semântica) usando Reciprocal Rank Fusion (RRF).

### Endpoint
```
GET /api/v1/ai/rag/hybrid/?q=odio&alpha=0.7&top_k=10
```

### Parâmetros
| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `q` | string | required | Query de busca |
| `alpha` | float | 0.5 | Peso BM25 (0=vetorial, 1=BM25) |
| `top_k` | int | 10 | Número de resultados |
| `version` | string | all | Versão específica |

### Performance (com índice GIN)

| Componente | Tempo | Observação |
|------------|-------|------------|
| BM25 | 16ms | Com índice GIN |
| Vetorial | ~2000ms | HNSW index |
| Fusion | <1ms | RRF merge |
| **Total** | ~2s | vs 10s sem índice |

### Resultados Comparativos: "ódio"

**Antes (só vetorial):**
- Atos 12:21 (42% match) - Irrelevante
- Números 26:16 (42% match) - Irrelevante

**Depois (híbrido alpha=0.7):**
- João 15:18 (70% match) - "Se o mundo odeia vocês..."
- Tito 3:3 (69% match) - "...odiando-nos uns aos outros"
- Gênesis 37:4-8 - História de José sendo odiado

### Arquivos Criados/Modificados
- `bible/ai/hybrid.py` (novo) - Módulo de busca híbrida
- `bible/ai/services.py` - Adicionado `search_hybrid()`
- `bible/ai/views.py` - Adicionado `RagHybridSearchView`
- `bible/ai/urls.py` - Rota `/rag/hybrid/`

### Índice Criado
```sql
CREATE INDEX idx_verses_text_pt_gin 
ON verses USING GIN (to_tsvector('portuguese', text));
```

---

## ✅ IMPLEMENTADO: Query Expansion (Fase 3)

### Descrição
Expansão de queries com sinônimos teológicos para aumentar o recall.

### Endpoint
```
GET /api/v1/ai/rag/hybrid/?q=odio&expand=true&top_k=10
```

### Parâmetros
| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `expand` | bool | false | Habilita expansão com sinônimos |

### Como Funciona

A query é expandida usando um dicionário de sinônimos teológicos curado:

```python
THEOLOGICAL_SYNONYMS = {
    "ódio": ["ira", "raiva", "aversão", "inimizade", "hostilidade"],
    "amor": ["caridade", "afeição", "ágape", "benevolência"],
    "perdão": ["remissão", "absolvição", "misericórdia"],
    "salvação": ["redenção", "libertação", "resgate"],
    "pecado": ["transgressão", "iniquidade", "culpa"],
    # + 50 grupos de sinônimos
}
```

### Exemplo de Expansão

**Query original:** `odio`

**Query expandida (tsquery):** `odio | ira | raiva | aversão`

### Resultados Comparativos: "odio"

**Sem expansão (`expand=false`):**
- João 15:18 - "Se o mundo odeia vocês..."
- Gênesis 37:4-8 - José odiado pelos irmãos
- Tito 3:3 - "odiando-nos uns aos outros"

**Com expansão (`expand=true`):**
- Jonas 4:9 - "raiva por causa dessa planta"
- Sofonias 1:18 - "ira de Deus"
- Sofonias 2:2 - "ira furiosa"
- + todos os resultados sem expansão

### Arquivos Criados/Modificados
- `bible/ai/query_expansion.py` (novo) - Módulo de expansão
- `bible/ai/hybrid.py` - Integrado `expand_query_flag`
- `bible/ai/services.py` - Parâmetro `expand_query`
- `bible/ai/views.py` - Parâmetro `expand` na API

### Features
- Normalização de acentos (busca "odio" encontra "ódio")
- Variações morfológicas (verbo/substantivo)
- 20+ grupos de sinônimos teológicos
- Resposta inclui `query_expansion` com detalhes

---

## ✅ IMPLEMENTADO: Two-Stage Reranking (Fase 2)

### Fundamentação Teórica

**Two-Stage Retrieval** é uma técnica consolidada em Information Retrieval:
- **Stage 1 (Recall)**: Busca rápida com modelo leve para encontrar candidatos
- **Stage 2 (Precision)**: Reordenação precisa com modelo mais pesado

Referências:
- Nogueira & Cho (2019) "Passage Re-ranking with BERT"
- Karpukhin et al. (2020) "Dense Passage Retrieval for Open-Domain QA"

### Implementação

**Pipeline:**
```
Query → Embed(small, 1536d) → 100 candidatos → Rerank(large, 3072d) → top_k final
```

### Endpoint
```
GET /api/v1/ai/rag/hybrid/?q=amor+de+Deus&rerank=true&top_k=5
```

### Parâmetros
| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `rerank` | bool | false | Habilita reranking com embedding large |

### Performance

| Componente | Tempo | Observação |
|------------|-------|------------|
| Query embedding (large) | ~530ms | Cache após primeira chamada |
| Batch fetch embeddings | ~100ms | 100 candidatos |
| Similarity calculation | <5ms | Numpy vectorizado |
| **Total reranking** | ~640ms | Primeira chamada |
| **Total (cached)** | ~100ms | Chamadas subsequentes |

### Resultados Experimentais: "amor de Deus"

**Sem Reranking (baseline):**
```
1. 1 João 4:16 (ACF) - "Deus é amor"
2. 1 João 4:16 (ARA) - "Deus é amor"
3. 1 João 4:16 (NVI) - "Deus é amor"
4. 1 João 4:16 (NAA) - "Deus é amor"
5. 1 João 4:16 (AS21) - "Deus é amor"
```
**Problema**: 5 versões do mesmo versículo (sem diversidade)

**Com Reranking (`rerank=true`):**
```
1. Judas 1:21 - "conservem-se no amor de Deus"
2. 1 João 4:7 - "o amor procede de Deus"
3. Romanos 8:39 - "nos separar do amor de Deus"
4. 1 João 4:16 - "Deus é amor"
5. Salmos 103:17 - "amor do SENHOR"
```
**Melhoria**: 5 passagens distintas sobre "amor de Deus"

### Métricas de Análise

| Métrica | Valor | Significado |
|---------|-------|-------------|
| `rank_changes` | 5 | Todos os top-5 mudaram de posição |
| `avg_rank_shift` | 42.2 | Média de 42 posições de mudança |
| `top_k_preserved` | 0% | Nenhum resultado original mantido |
| `kendall_tau` | 0.0 | Correlação com ranking original |

### Arquivos Criados/Modificados
- `bible/ai/reranking.py` (novo) - Módulo de reranking com:
  - `rerank_with_large_embeddings()` - Função principal
  - `compare_rankings()` - Análise de mudanças
  - `RerankingMetrics` - Dataclass de métricas
  - `get_large_embeddings_batch()` - Fetch otimizado
- `bible/ai/hybrid.py` - Parâmetro `rerank_with_large`
- `bible/ai/services.py` - Parâmetro `rerank`
- `bible/ai/views.py` - Parâmetro `rerank` na API

### Observações Científicas

1. **Diversificação Natural**: O embedding large (3072 dim) captura nuances semânticas que o small (1536 dim) não consegue, promovendo diversidade nos resultados.

2. **Trade-off Recall vs Precision**: O small é otimizado para recall (encontrar candidatos), enquanto o large é otimizado para precision (ordenar corretamente).

3. **Efeito Observado**: Em queries conceituais como "amor de Deus", o reranking promove diversidade ao capturar diferentes contextos do conceito.

---

## 🎯 Problemas Identificados

### 1. Busca por termos específicos (ex: "ódio")
- **Problema**: Embeddings não capturam bem termos negativos/específicos
- **Causa**: Modelo otimizado para conceitos, não palavras exatas
- **Impacto**: 42% match para "ódio" (deveria ser ~70%+)

### 2. Busca híbrida desativada
- **Problema**: `RAG_HYBRID=0` - só busca vetorial
- **Causa**: Não implementado
- **Impacto**: Perda de recall para termos exatos

### 3. Unified embeddings subutilizados
- **Problema**: 31k unified vs 528k individuais
- **Causa**: Apenas versões PT fundidas
- **Impacto**: Deduplicação de resultados

---

## 🚀 Plano de Otimização

### ~~Fase 1: Hybrid Search~~ ✅ IMPLEMENTADO

> Veja seção "✅ IMPLEMENTADO: Hybrid Search" acima

---

### ~~Fase 2: Two-Stage Retrieval~~ ✅ IMPLEMENTADO

> Veja seção "✅ IMPLEMENTADO: Two-Stage Reranking" acima

---

### ~~Fase 3: Query Expansion~~ ✅ IMPLEMENTADO

> Veja seção "✅ IMPLEMENTADO: Query Expansion" acima

---

### Fase 4: MMR Diversification

**Objetivo**: Evitar resultados redundantes (mesmo versículo em várias versões)

**Técnica**: Maximal Marginal Relevance

```python
def mmr_score(relevance, similarity_to_selected, lambda_=0.7):
    return lambda_ * relevance - (1 - lambda_) * similarity_to_selected
```

**Configuração**:
```env
RAG_MMR_ENABLED=1
RAG_MMR_LAMBDA=0.7  # 1=só relevância, 0=só diversidade
```

---

### ✅ IMPLEMENTADO: MMR Diversification (Fase 4)

### Fundamentação Teórica

**Maximal Marginal Relevance (MMR)** foi proposto por Carbonell & Goldstein (1998) para balancear relevância e diversidade em sistemas de retrieval.

**Fórmula:**
```
MMR(d) = λ × Sim(d, Q) − (1−λ) × max[Sim(d, S)]
```

Onde:
- `Sim(d, Q)` = similaridade do documento d com a query Q
- `Sim(d, S)` = similaridade de d com documentos já selecionados S
- `λ` = trade-off (0.7 recomendado para contexto bíblico)

**Referências:**
- Carbonell & Goldstein (1998) "The Use of MMR, Diversity-Based Reranking"
- https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf

### O Problema Específico

Na Bíblia, o mesmo versículo aparece em 8+ versões diferentes (NVI, ARA, ACF, etc.). Sem MMR, uma busca por "amor de Deus" retornava:

```
1. 1 João 4:16 (NVI)
2. 1 João 4:16 (NTLH)
3. 1 João 4:16 (AS21)
4. 1 João 4:16 (NVT)
5. 1 João 4:16 (NAA)
6. 1 João 4:16 (ACF)
7. 1 João 4:16 (ARA)
8. 1 João 4:16 (ARC)
9. Salmos 52:8 (NVI)
10. Salmos 52:8 (NVT)
```

**Problema:** 8 de 10 resultados são o MESMO versículo!

### Solução Implementada

Implementamos MMR com identificação de versículo canônico:

```python
def get_canonical_verse_id(hit: dict) -> str:
    """Gera ID independente de versão: 'Book:Chapter:Verse'"""
    return f"{hit['book_osis']}:{hit['chapter']}:{hit['verse']}"
    # Ex: "1John:4:16"
```

O algoritmo agrupa por ID canônico e mantém apenas a versão de maior score.

### Endpoint
```
GET /api/v1/ai/rag/hybrid/?q=amor+de+Deus&mmr_lambda=0.7&top_k=10
```

### Parâmetros

| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `mmr_lambda` | float | null | λ do MMR (0=diversidade, 1=relevância) |
| `dedupe` | bool | false | Deduplica versões antes do MMR |

### Resultados Experimentais: "amor de Deus"

**Sem MMR (baseline):**
```
1. 1 João 4:16 NVI
2. 1 João 4:16 NTLH
3. 1 João 4:16 AS21
4. 1 João 4:16 NVT
5. 1 João 4:16 NAA
6. 1 João 4:16 ACF
7. 1 João 4:16 ARA
8. 1 João 4:16 ARC
9. Salmos 52:8 NVI
10. Salmos 52:8 NVT
```
- **8 duplicatas** (80% redundância)
- **Diversity score: 0.2**

**Com MMR (λ=0.7):**
```
1. 1 João 4:16 NVI - "Deus é amor"
2. Salmos 52:8 NVI - "confio no amor de Deus"
3. Deuteronômio 29:26 NTLH - sobre abandonar o amor de Deus
4. Salmos 59:10 AS21 - "O Deus que me ama"
5. 2 Coríntios 5:13 NVI - "é o amor de Cristo"
6. 2 Crônicas 9:8 NVI - "o amor de Deus por Israel"
7. Jeremias 3:13 NTLH - sobre ser infiel ao amor
8. Lucas 11:42 NVI - "negligenciaram o amor de Deus"
9. Isaías 63:7 NTLH - "lembrar o amor do SENHOR"
10. Apocalipse 6:9 ARC - sobre a palavra de Deus
```
- **0 duplicatas** (100% único)
- **Diversity score: 1.0**
- **90 duplicatas removidas** dos 100 candidatos

### Métricas de Performance

| Métrica | Valor | Observação |
|---------|-------|------------|
| Candidatos processados | 100 | Pool inicial |
| Resultados após MMR | 10 | top_k solicitado |
| Duplicatas removidas | 90 | 90% eram redundantes |
| Diversity score | 1.0 | Máximo possível |
| Tempo MMR | 0.31ms | Muito rápido |

### Arquivos Criados/Modificados
- `bible/ai/mmr.py` (novo) - Módulo MMR com:
  - `mmr_diversify()` - Função principal
  - `MMRResult` - Dataclass com métricas
  - `MMRConfig` - Configuração do algoritmo
  - `get_canonical_verse_id()` - Identificação canônica
  - `deduplicate_by_version()` - Deduplicação por versão preferida
  - `cosine_similarity_vectors()` - Cálculo de similaridade
- `bible/ai/hybrid.py` - Integração no pipeline
- `bible/ai/services.py` - Parâmetros `mmr_lambda`, `deduplicate_versions`
- `bible/ai/views.py` - Parâmetros na API

### Configuração Recomendada

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| `mmr_lambda` | 0.7 | Balanceia relevância e diversidade |
| `dedupe` | false | MMR já faz deduplicação inteligente |

### Resposta da API

```json
{
  "hits": [...],
  "total": 10,
  "mmr_diversification": {
    "enabled": true,
    "lambda": 0.7,
    "deduplicate_versions": false,
    "duplicates_removed": 90,
    "candidates_processed": 100,
    "results_selected": 10,
    "diversity_score": 1.0,
    "timing_ms": 0.31
  }
}
```

---

### Fase 5: Unified Embeddings Expansion

**Objetivo**: Usar embeddings unificados para deduplicação inteligente

**Atual**: 31k versículos canônicos (PT apenas)
**Proposta**: Expandir para incluir EN e cross-lingual

**Benefício**: 
- Menos duplicatas nos resultados
- Busca cross-lingual (query PT → resultados EN)

---

## 📈 Métricas de Sucesso

### Métricas Científicas

| Métrica | Baseline | Target | Descrição |
|---------|----------|--------|-----------|
| nDCG@10 | ~0.65 | ≥0.75 | Qualidade do ranking |
| Recall@20 | ~0.70 | ≥0.85 | Cobertura |
| MRR | ~0.55 | ≥0.70 | Posição do primeiro resultado relevante |
| Latency P95 | 3s | <1s | Performance |

### Queries de Teste

```yaml
exact_match:
  - "ódio"
  - "Eva"
  - "Melquisedeque"
  
conceptual:
  - "amor de Deus"
  - "perdão dos pecados"
  - "salvação pela fé"
  
theological:
  - "trindade"
  - "justificação"
  - "santificação"
  
cross_version:
  - "João 3:16"
  - "Salmos 23"
```

---

## 🔧 Implementação Técnica

### Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────────┐
│                       RAG Pipeline v2.0                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Query ──┬──► Query Expansion ──► Embed(small)                  │
│          │                            │                         │
│          │                            ▼                         │
│          │   ┌────────────────────────────────────────┐         │
│          │   │         Hybrid Search                  │         │
│          │   │  ┌──────────┐    ┌──────────────┐     │         │
│          └──►│  │  BM25    │    │ Vector(HNSW) │     │         │
│              │  │ (tsvector)│    │ (small)      │     │         │
│              │  └────┬─────┘    └──────┬───────┘     │         │
│              │       │                  │            │         │
│              │       └────────┬─────────┘            │         │
│              │                │                      │         │
│              │         RRF Fusion (α=0.5)            │         │
│              └────────────────┼──────────────────────┘         │
│                               │                                 │
│                               ▼                                 │
│              ┌────────────────────────────────────────┐         │
│              │         Two-Stage Reranking            │         │
│              │  TopK*3 candidates                     │         │
│              │         │                              │         │
│              │         ▼                              │         │
│              │  Cross-Encoder / Large Embed           │         │
│              │         │                              │         │
│              │         ▼                              │         │
│              │  MMR Diversification                   │         │
│              └────────────────┼───────────────────────┘         │
│                               │                                 │
│                               ▼                                 │
│                         Final TopK                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Arquivos a Modificar

1. **`bible/ai/retrieval.py`** - Pipeline principal
2. **`bible/ai/hybrid.py`** ✅ - BM25 + RRF
3. **`bible/ai/reranking.py`** ✅ - Two-stage reranking
4. **`bible/ai/query_expansion.py`** ✅ - Sinônimos teológicos
5. **`bible/ai/mmr.py`** (pendente) - Diversificação

### Migrações Necessárias

```sql
-- ✅ Índice GIN para BM25 (CRIADO)
CREATE INDEX idx_verses_text_pt_gin 
ON verses USING GIN (to_tsvector('portuguese', text));
```

---

## 📊 Benchmark Comparativo

### Metodologia

Testamos 3 queries representativas com diferentes configurações:

| Query | Tipo | Dificuldade |
|-------|------|-------------|
| "ódio" | Termo específico | Alta |
| "amor de Deus" | Conceito teológico | Média |
| "perdão" | Conceito com sinônimos | Média |

### Resultados: "ódio"

| Configuração | Resultado Principal | Qualidade |
|--------------|---------------------|-----------|
| Baseline (só vetorial) | Atos 12:21 (42%) | ❌ Irrelevante |
| Hybrid (alpha=0.7) | João 15:18 "odeia vocês" | ✅ Relevante |
| Hybrid + Expand | Jonas 4:9 "raiva" | ✅ Sinônimo |
| Hybrid + Expand + Rerank | Salmos 139:22 "ódio perfeito" | ✅✅ Muito relevante |

### Resultados: "amor de Deus"

| Configuração | Diversidade | Qualidade |
|--------------|-------------|-----------|
| Baseline | 5x 1 João 4:16 | ❌ Sem diversidade |
| Hybrid + Rerank | 5 passagens distintas | ✅ Diversificado |

**Com reranking:**
1. Judas 1:21 - "conservem-se no amor de Deus"
2. 1 João 4:7 - "o amor procede de Deus"
3. Romanos 8:39 - "nos separar do amor de Deus"
4. 1 João 4:16 - "Deus é amor"
5. Salmos 103:17 - "amor do SENHOR"

### Métricas de Performance

| Componente | Tempo (cold) | Tempo (cached) |
|------------|--------------|----------------|
| BM25 | ~80ms | ~30ms |
| Vector Search | ~2000ms | ~700ms |
| Query Expansion | <5ms | <1ms |
| Reranking | ~1400ms | ~100ms |
| **Total** | ~3500ms | ~900ms |

### Observações Científicas

1. **Hybrid Search** resolveu o problema de termos específicos ("ódio")
2. **Query Expansion** aumentou recall para conceitos relacionados
3. **Two-Stage Reranking** melhorou precision e diversidade
4. **Cache de embeddings** reduziu latência em 4x após primeira chamada

---

## ✅ Status do Projeto

| Fase | Status | Data |
|------|--------|------|
| 1. Hybrid Search | ✅ Completo | Nov 2025 |
| 2. Two-Stage Rerank | ✅ Completo | Nov 2025 |
| 3. Query Expansion | ✅ Completo | Nov 2025 |
| 4. MMR Diversity | ✅ Completo | Nov 2025 |
| 5. Unified Expansion | ⏳ Pendente | - |

---

## 📝 Uso da API

### Endpoint Principal
```
GET /api/v1/ai/rag/hybrid/
```

### Parâmetros

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `q` | string | required | Query de busca |
| `top_k` | int | 10 | Número de resultados (1-50) |
| `alpha` | float | 0.5 | Peso BM25 (0=vetorial, 1=lexical) |
| `version` | string | all | Versão bíblica específica |
| `expand` | bool | false | Expandir com sinônimos teológicos |
| `rerank` | bool | false | Reordenar com embedding large |
| `mmr_lambda` | float | null | MMR diversification (0=diversidade, 1=relevância) |
| `dedupe` | bool | false | Deduplica versões antes do MMR |

### Exemplos

```bash
# Busca básica
GET /api/v1/ai/rag/hybrid/?q=amor

# Busca otimizada para termos específicos
GET /api/v1/ai/rag/hybrid/?q=ódio&alpha=0.7

# Busca com todas as melhorias
GET /api/v1/ai/rag/hybrid/?q=perdão&expand=true&rerank=true&top_k=10

# Busca com MMR diversification (recomendado para produção)
GET /api/v1/ai/rag/hybrid/?q=amor+de+Deus&mmr_lambda=0.7&expand=true&top_k=10
```

---

*Documento criado em: Nov 2025*
*Última atualização: Nov 2025*
*Versão: 3.0.0 (Hybrid + Expansion + Reranking + MMR implementados)*
