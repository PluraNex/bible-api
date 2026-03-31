# 🔍 Análise de Qualidade de Busca - Bible API

**Data:** Novembro 2025  
**Autor:** Bible API Team  
**Script:** `analyze_search_quality.py`

## 📊 Resumo Executivo

Após análise detalhada de múltiplas queries e configurações, identificamos:

| Configuração | Melhor Para | Limitações |
|-------------|------------|------------|
| **Híbrido SEM expansão** | Frases exatas ("paz na terra") | Menos recall para conceitos abstratos |
| **Híbrido COM expansão** | Conceitos abstratos ("justiça") | Resultados mais diversos |
| **Vector puro** | Sinônimos e variações | Menos precisão textual |
| **BM25 puro** | Matches exatos de palavras | Não encontra sinônimos |
| **Híbrido COM NLP** ⭐ | **Todas as queries** | Ajuste automático por tipo |

---

## 🧠 NLP Query Tool Integration (NOVO!)

### O Problema

Antes, o `hybrid_search` usava **parâmetros fixos** para todas as queries:

```python
alpha = 0.5          # Sempre 50% BM25, 50% Vector
expand = True        # Sempre expandia com sinônimos
entity_boost = 1.0   # Sem boost especial
tsquery = "paz & terra"  # Operador simples (AND)
```

**Problema**: Uma busca por "Abraão" (nome próprio) era tratada igual a "justiça" (conceito abstrato), quando deveriam ter estratégias diferentes!

### A Solução: NLP Dinâmico

O **NLP Query Tool** (`bible/ai/agents/tools/nlp_query_tool.py`) analisa cada query e ajusta automaticamente:

#### 1. Classificação Semântica

| Query | Tipo Detectado | Descrição |
|-------|---------------|-----------|
| "paz na terra" | **PHRASE** | Frase exata, manter ordem |
| "Abraão" | **ENTITY** | Nome próprio do Gazetteer |
| "justiça" | **CONCEPT** | Conceito abstrato |
| "João 3:16" | **REFERENCE** | Referência bíblica |
| "o que é amor?" | **QUESTION** | Pergunta do usuário |
| "perdão" | **KEYWORD** | Palavra-chave única |

#### 2. Alpha Dinâmico (BM25 vs Vector)

```
Alpha = peso do BM25 (textual) vs Vector (semântico)
- Alpha 0.8 = 80% textual, 20% semântico
- Alpha 0.5 = 50/50 balanceado
- Alpha 0.3 = 30% textual, 70% semântico
```

| Tipo | Alpha | Por quê? |
|------|-------|----------|
| REFERENCE | **0.8** | "João 3:16" precisa match exato |
| ENTITY | **0.7** | "Abraão" é nome, match textual |
| PHRASE | **0.6** | Frase precisa estar no texto |
| KEYWORD | **0.5** | Balanceado |
| CONCEPT | **0.4** | "justiça" → buscar sinônimos |
| QUESTION | **0.3** | Semântica mais importante |

#### 3. Entity Boost (Gazetteer)

O Gazetteer (`data/NLP/nlp_gazetteer/canonical_entities_v4_unified.json`) contém **120 entidades bíblicas** com boosts pré-definidos:

| Entidade | Tipo | Boost |
|----------|------|-------|
| Jesus | PERSON | **4.0** |
| Espírito Santo | DEITY | **3.5** |
| Abraão | PERSON | **3.0** |
| Sermão do Monte | LITERARY_WORK | **2.8** |
| Jerusalém | PLACE | **2.5** |

Quando você busca "Jesus Cristo", o sistema:
1. Detecta entidade "Jesus" (PERSON, boost 4.0)
2. Multiplica o score de matches exatos por **4.0**

#### 4. TSQuery Otimizado (Distância Dinâmica)

O NLP calcula a distância ideal baseado nos stopwords removidos:

```python
# Detecta stopwords removidas
stopwords_removed = ["na"]  # 1 stopword

# Calcula distância
distance = len(stopwords_removed) + 1  # = 2

# Gera tsquery otimizado
"paz na terra" → (paz <2> terra)  → 49 resultados! ✅
```

#### 5. Expansão Inteligente

| Tipo | Expand | Motivo |
|------|--------|--------|
| PHRASE | **false** | Preservar frase exata |
| ENTITY | **false** | Nome próprio não expande |
| REFERENCE | **false** | Referência precisa |
| CONCEPT | **true** | Buscar sinônimos |
| QUESTION | **true** | Entender contexto |

### Fluxo Completo

```
Query: "Sermão do Monte"
         │
         ▼
┌─────────────────────────────────────────┐
│        NLP QUERY TOOL                   │
├─────────────────────────────────────────┤
│ 1. Tokeniza: ["sermao", "do", "monte"]  │
│ 2. Stopwords: ["do"] removido           │
│ 3. Gazetteer: LITERARY_WORK (boost 2.8) │
│ 4. Tipo: ENTITY                         │
│ 5. Estratégia:                          │
│    - alpha: 0.7 (mais textual)          │
│    - entity_boost: 2.8                  │
│    - expand: false                      │
│    - tsquery: "sermao | monte"          │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│        HYBRID SEARCH                    │
├─────────────────────────────────────────┤
│ BM25: alpha=0.7, boost=2.8×1.5=4.2      │
│ Vector: 1-alpha=0.3                     │
│ Não expande com sinônimos               │
└─────────────────────────────────────────┘
```

### Cache NLP

Para evitar recálculos, análises são cacheadas no banco:

```sql
-- Tabela: query_nlp_cache
| query_normalized | semantic_type | entities | boost_strategy | usage_count |
|------------------|---------------|----------|----------------|-------------|
| paz na terra     | phrase        | []       | {alpha:0.6}    | 42          |
| abraao           | entity        | [...]    | {boost:3.0}    | 15          |
```

| Momento | Processing Time |
|---------|-----------------|
| 1ª busca (MISS) | 2-12ms |
| 2ª busca (HIT) | **0ms** |

### Impacto nos Resultados

#### Query: "paz na terra"

| Config | Lev 26:6 | Luc 2:14 | Melhoria |
|--------|----------|----------|----------|
| Antes (alpha=0.5) | 91% | 89% | - |
| **Depois (NLP)** | **98%** | **94%** | +7% |

#### Query: "Abraão" (com Entity Boost)

| Config | Impacto |
|--------|---------|
| Antes | Score normal |
| **Depois** | Score × **3.0** |

### Uso no Código

```python
from bible.ai.hybrid import hybrid_search

result = hybrid_search(
    query="paz na terra",
    query_embedding=embedding,
    use_nlp_analysis=True,  # ← Habilita NLP dinâmico
)

# Resposta inclui análise NLP
result["nlp_analysis"] = {
    "semantic_type": "phrase",
    "entities": [],
    "boost_strategy": {
        "alpha": 0.6,
        "entity_boost": 1.0,
        "expand": False
    },
    "from_cache": True,  # Cache hit!
}
```

### Testes

```bash
# Testar NLP Tool isolado
docker exec -i bible-api-web-1 python test_nlp_tool.py

# Testar integração com Hybrid Search
docker exec -i bible-api-web-1 python test_hybrid_nlp.py

# Testar cache NLP
docker exec -i bible-api-web-1 python test_nlp_cache.py

# Teste end-to-end completo
docker exec -i bible-api-web-1 python test_hybrid_e2e.py
```

---

## 🎯 Descobertas Principais

### 1. Operador de Distância PostgreSQL

O problema original era que o operador `<->` (adjacente) não encontrava "paz na terra" porque "na" está entre as palavras:

```sql
-- ❌ NÃO FUNCIONA: 0 resultados
SELECT * FROM verses 
WHERE to_tsvector('portuguese', text) @@ to_tsquery('portuguese', 'paz <-> terra')

-- ✅ FUNCIONA: 49 resultados  
SELECT * FROM verses 
WHERE to_tsvector('portuguese', text) @@ to_tsquery('portuguese', 'paz <2> terra')
```

**Operadores tsquery:**
| Operador | Descrição | "paz na terra" |
|----------|-----------|----------------|
| `paz <-> terra` | Palavras adjacentes (0 gap) | ❌ 0 resultados |
| `paz <2> terra` | Até 1 palavra entre | ✅ 49 resultados |
| `paz <3> terra` | Até 2 palavras entre | 2 resultados |
| `paz & terra` | Ambas em qualquer posição | 225 resultados |

### 2. Resultados Após Correção

Com o operador `<2>`, a busca "paz na terra" agora funciona corretamente:

```
📝 HÍBRIDO SEM EXPANSÃO:
#1: Levítico 26:6 ⭐ "Também darei paz na terra..."
#2: Levítico 26:6 ⭐ (outra versão)
#3: Lucas 12:51: "Cuidais vós que vim trazer paz à terra?"
#4: Lucas 2:14 ⭐ "Glória a Deus... paz na terra..."

🔗 HÍBRIDO COM EXPANSÃO:
#1-6: Levítico 26:6 ⭐ (várias versões)
#10: Lucas 2:14 ⭐
#12: Lucas 2:14 ⭐
```

### 3. Expansão Funciona Para Conceitos

Para queries de **conceitos abstratos** como "justiça":

```
COM EXPANSÃO:
#1: Gálatas 2:16: "...pessoa é declarada justa..." (justificação)
#2: Gálatas 2:16: "...homem não é justificado..." (justificação)
```

A expansão encontra versículos sobre "justificação" que são semanticamente relacionados.

### 4. Valor da Busca Semântica

A busca vetorial encontra **variações e sinônimos automaticamente**:

```
Busca: "paz na terra"
Vector encontra:
- Levítico 26:6 (múltiplas versões: NVI, ARA, NAA, NTLH)
- Lucas 2:14 (múltiplas versões)
- Isaías 14:7 (relacionado semanticamente)
```

## 📌 Configuração Recomendada

### Para o Frontend (Presets)

```typescript
// Preset BALANCEADO (default) - para a maioria das buscas
{
  expand: false,        // Desabilitado para preservar frases exatas
  alpha: 0.55,          // Leve preferência para textual
  topK: 30,             // Bom recall
  showSourceFlags: true // Mostrar origem (textual/semântico)
}

// Preset DESCOBERTA - para conceitos abstratos
{
  expand: true,         // Habilitado para sinônimos
  alpha: 0.45,          // Mais semântico
  rerank: true,         // Melhor precisão
  topK: 30
}
```

### Parâmetros de API Recomendados

| Parâmetro | Valor Recomendado | Motivo |
|-----------|-------------------|--------|
| `expand` | `false` (default) | Preserva frases exatas |
| `mode` | `auto` | Deixa o híbrido decidir |
| `top_k` | `30-50` | Bom equilíbrio recall/performance |
| `alpha` | `0.5-0.6` | Leve preferência textual |

## 🔧 Correções Implementadas

### 1. Operador de Distância no tsquery (✅ FEITO)

No `query_expansion_service.py`, mudamos de `<->` para `<2>`:

```python
# ANTES (não funcionava para frases com stopwords):
phrase_query = " <-> ".join(query_words)  # "paz <-> terra"

# DEPOIS (funciona para "paz na terra"):
phrase_query = " <2> ".join(query_words)  # "paz <2> terra"
```

### 2. TSQuery Gerado

A expansão agora gera:
```
(paz <2> terra) | paz | terra | tranquilidade | harmonia | serenidade
```

A frase `(paz <2> terra)` prioriza versículos com a frase exata.

## 📈 Métricas de Qualidade

### Query: "paz na terra"

| Método | Levítico 26:6 | Lucas 2:14 | Lucas 12:51 |
|--------|---------------|------------|-------------|
| BM25 puro | #1 ✅ | - | #3 ✅ |
| Vector puro | #1-4 ✅ | #5 ✅ | - |
| Híbrido sem exp | #1 ✅ | #4 ✅ | #3 ✅ |
| Híbrido com exp | #1-6 ✅ | #10-14 ✅ | #16 ✅ |

### Query: "justiça"

| Método | Deut 16:20 | Prov 21:21 | Gal 2:16 |
|--------|------------|------------|----------|
| BM25 puro | #1 ✅ | #3 ✅ | - |
| Híbrido com exp | - | - | #1-5 ✅ |

## 🚀 Como Usar o Script de Análise

```bash
# Análise rápida de uma query
docker compose exec web python analyze_search_quality.py "sua query"

# Teste de ranking específico
docker compose exec web python test_search_ranking.py

# Teste de operadores tsquery
docker compose exec web python test_tsquery.py
```

## 📝 Conclusão

1. ✅ **Operador `<2>` corrige busca de frases** com stopwords no meio
2. ✅ **Manter `expand: false` como padrão** - a maioria das buscas são frases específicas
3. ✅ **Oferecer modo "Descoberta"** com expansão para conceitos abstratos
4. ✅ **Badges de origem** implementados para transparência
5. **Levítico 26:6 e Lucas 2:14** agora aparecem corretamente nos primeiros resultados
