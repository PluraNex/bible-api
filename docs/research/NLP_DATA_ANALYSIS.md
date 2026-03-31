# 📊 Análise dos Dados NLP Existentes

**Status:** ✅ **INTEGRADO** (Novembro 2025)

> **Nota:** Esta documentação descreve os dados NLP existentes que agora são usados pelo `NLPQueryTool` integrado ao `hybrid_search()`. Veja `NLP_INTEGRATION_PLAN.md` para detalhes da implementação.

## 🗂️ Estrutura Encontrada

```
data/NLP/
├── nlp_gazetteer/                    # Dicionário de entidades
│   ├── canonical_entities_v4_unified.json  # ⭐ PRINCIPAL (1635 linhas)
│   └── versões anteriores...
│
├── nlp_corpus/                       # Corpus processado por versão
│   └── NAA/
│       ├── Gênesis_NAA_nlp.json
│       └── Marcos_NAA_nlp.json     # ⭐ 396K linhas!
│
└── nlp_corpus_comparison_json/       # Comparações entre versões
```

## 🏷️ Gazetteer de Entidades (canonical_entities_v4_unified.json)

### Namespaces Disponíveis:
| Namespace | Descrição | Exemplos |
|-----------|-----------|----------|
| `PERSON` | Pessoas bíblicas | Abraão, Moisés, Paulo, Davi |
| `DEITY` | Nomes divinos | YHWH, Jesus Cristo, Espírito Santo |
| `PLACE` | Locais geográficos | Jerusalém, Judeia, Monte Sinai |
| `ANGEL` | Seres celestiais | Gabriel, Miguel |
| `CONCEPT` | Conceitos abstratos | Salvação, Graça, Fé |
| `OBJECT` | Objetos sagrados | Arca da Aliança, Tabernáculo |
| `EVENT` | Eventos bíblicos | Êxodo, Crucificação, Pentecostes |
| `LITERARY_WORK` | Obras literárias | Sermão do Monte, Salmo 23 |

### Estrutura de cada Entidade:
```json
{
  "Abraão": {
    "canonical_id": "PER:abraao",
    "aliases": ["Abraão", "Abrão", "Pai da Fé"],
    "type": "PATRIARCH",
    "description": "Pai da fé, patriarca de Israel",
    "priority": 85,
    "boost": 3.0,
    "categories": ["Patriarca", "Pessoa"]
  }
}
```

### 🎯 Uso para Busca:
- **`boost`**: Multiplicador de relevância (1.0-4.0)
- **`priority`**: Ordenação em resultados (0-100)
- **`aliases`**: Termos alternativos para matching

## 📖 Corpus NLP Processado (Marcos_NAA_nlp.json)

### Estrutura por Versículo:
```json
{
  "ref": "Marcos 1:1",
  "text": "Princípio do evangelho de Jesus Cristo, Filho de Deus.",
  "word_count": 9,
  "sentence_count": 1,
  
  "tokens": ["Princípio", "do", "evangelho", "de", "Jesus", ...],
  "lemmas": ["princípio", "de o", "evangelho", "de", "Jesus", ...],
  "stopwords": ["do", "de"],
  "keywords": ["Cristo", "evangelho", "Deus", "princípio", "Jesus"],
  
  "tfidf_scores": [
    ["Cristo", 2.88],
    ["evangelho", 1.85],
    ["Deus", 1.79]
  ],
  
  "pos": [
    {"text": "Jesus", "lemma": "Jesus", "pos": "PROPN", "ent": "BIBLICAL_PERSON"},
    {"text": "Filho", "lemma": "Filho", "pos": "PROPN", "ent": "BIBLICAL_DIVINE"}
  ]
}
```

### Keywords do Livro (Top 50):
```
Jesus, discípulo, homem, Deus, Filho, responder, perguntar, Senhor,
casa, dia, ouvir, João, coisa, multidão, mão, Espírito, sacerdote...
```

## 🚀 Como Integrar com NLP Query Tool

### 1. Carregar Gazetteer na Inicialização

```python
class NLPQueryTool:
    def __init__(self):
        self.gazetteer = self._load_gazetteer()
    
    def _load_gazetteer(self):
        with open("data/NLP/nlp_gazetteer/canonical_entities_v4_unified.json") as f:
            return json.load(f)
    
    def get_entity_boost(self, term: str) -> float:
        """Retorna boost se termo é entidade conhecida."""
        for namespace, entities in self.gazetteer.items():
            if namespace.startswith("_"):
                continue
            for name, data in entities.items():
                if term.lower() in [a.lower() for a in data.get("aliases", [name])]:
                    return data.get("boost", 1.0)
        return 1.0
```

### 2. Usar TF-IDF do Corpus para Keywords

```python
def get_verse_keywords(book: str, chapter: int, verse: int) -> list:
    """Retorna keywords pré-computadas do corpus NLP."""
    corpus = load_corpus(f"{book}_NAA_nlp.json")
    for item in corpus["items"]:
        if item["chapter"] == chapter and item["verse"] == verse:
            return item["keywords"]
    return []
```

### 3. Detecção de Entidades na Query

```python
def detect_entities(query: str) -> list:
    """Detecta entidades bíblicas na query usando gazetteer."""
    entities = []
    query_lower = query.lower()
    
    for namespace, items in gazetteer.items():
        for name, data in items.items():
            for alias in data.get("aliases", [name]):
                if alias.lower() in query_lower:
                    entities.append({
                        "text": alias,
                        "type": namespace,
                        "canonical_id": data["canonical_id"],
                        "boost": data.get("boost", 1.0)
                    })
    return entities
```

### 4. Boost Inteligente Baseado em Entidades

```python
def calculate_query_boost(query: str) -> dict:
    """Calcula boost baseado em entidades detectadas."""
    entities = detect_entities(query)
    
    if not entities:
        return {"boost": 1.0, "strategy": "default"}
    
    # Entidade de alta prioridade = boost textual
    max_boost = max(e["boost"] for e in entities)
    
    return {
        "boost": max_boost,
        "entities": entities,
        "strategy": "entity_boost",
        "alpha": 0.7 if max_boost > 2.5 else 0.5  # Mais textual para entidades
    }
```

## 📋 Status da Implementação

| Item | Status | Detalhes |
|------|--------|----------|
| Carregar Gazetteer | ✅ Completo | `NLPQueryTool.gazetteer` property |
| Detectar Entidades | ✅ Completo | `detect_entities()` método |
| Entity Boost | ✅ Completo | Boost 1.0-4.0 aplicado no BM25 |
| Cache de Queries | ✅ Completo | `QueryNLPCache` model |
| Indexar Keywords do Corpus | ⏳ Futuro | TF-IDF pré-computado disponível |

## 💡 Exemplos de Uso (Testados)

### Query: "Abraão"
```
Gazetteer: PERSON (boost: 3.0, type: PATRIARCH)
Alpha: 0.7 (textual forte)
Expand: false (nome próprio)
Cache: HIT após primeira busca
```

### Query: "paz na terra"
```
Tipo: PHRASE (frase)
TSQuery: (paz <2> terra)
Alpha: 0.6
Expand: false
```

### Query: "Sermão do Monte"
```
Gazetteer: LITERARY_WORK (boost: 2.8)
Alpha: 0.7
Expand: false
```

## 🧪 Testes

```bash
# Verificar carregamento do Gazetteer
docker exec -i bible-api-web-1 python test_nlp_tool.py

# Testar detecção de entidades
docker exec -i bible-api-web-1 python test_hybrid_nlp.py

# Verificar cache funcionando
docker exec -i bible-api-web-1 python test_nlp_cache.py
```
