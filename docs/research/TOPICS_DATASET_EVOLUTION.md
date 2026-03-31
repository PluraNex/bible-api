# Evolução do Dataset de Tópicos Bíblicos

> Documentação técnica do processo de construção e enriquecimento do dataset unificado de tópicos bíblicos (V3).

## 📊 Resumo Executivo

| Métrica | Valor Final |
|---------|-------------|
| **Total de Tópicos** | 7,873 |
| **Com Definições** | 5,955 (75.6%) |
| **Com Cross-refs** | 5,642 (71.7%) |
| **Tópicos Enriquecidos por IA** | 3,837 (48.7%) |
| **Conexões entre Tópicos** | 112,835 |
| **Referências de Definições Extraídas** | 17,715 |

---

## 🔄 Diagrama do Pipeline

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         FASE 1: FONTES ORIGINAIS                              ║
║                                                                               ║
║   Localização: data/dataset/dictionary/                                       ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ┌──────────────────┐  ┌──────────────────┐                                 ║
║   │  📚 Torrey (TOR) │  │  📚 Nave (NAV)   │                                 ║
║   │    618 tópicos   │  │   5,234 tópicos  │                                 ║
║   │                  │  │                  │                                 ║
║   │ Arquivo fonte:   │  │ Arquivo fonte:   │                                 ║
║   │ torrey.json      │  │ nave.json        │                                 ║
║   └────────┬─────────┘  └────────┬─────────┘                                 ║
║            │                     │                                            ║
║            └──────────┬──────────┘                                            ║
║                       ▼                                                       ║
║   ┌──────────────────────────────────────────────────────────────────────┐   ║
║   │  🔧 SCRIPT: scripts/topical_pipeline/parse_sources.py                │   ║
║   │     Converte fontes brutas → JSON estruturado                        │   ║
║   │     Saída: scripts/topical_pipeline/data/topics/                     │   ║
║   └──────────────────────────────────────────────────────────────────────┘   ║
║                       │                                                       ║
║                       ▼                                                       ║
║            ┌─────────────────────┐                                           ║
║            │  Dataset V2 Inicial │                                           ║
║            │    5,466 tópicos    │                                           ║
║            └─────────┬───────────┘                                           ║
║                      │                                                        ║
╚══════════════════════╪════════════════════════════════════════════════════════╝
                       │
                       ▼
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    FASE 2: INTEGRAÇÃO DE DICIONÁRIOS                          ║
║                                                                               ║
║   Adiciona definições de Easton e Smith ao dataset                           ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ┌──────────────────┐  ┌──────────────────┐                                 ║
║   │  📖 Easton (EAS) │  │  📖 Smith (SMI)  │                                 ║
║   │   3,956 tópicos  │  │   4,546 tópicos  │                                 ║
║   │                  │  │                  │                                 ║
║   │ data/dataset/    │  │ data/dataset/    │                                 ║
║   │ dictionary/      │  │ dictionary/      │                                 ║
║   │ easton/          │  │ smith/           │                                 ║
║   └────────┬─────────┘  └────────┬─────────┘                                 ║
║            │                     │                                            ║
║            └──────────┬──────────┘                                            ║
║                       ▼                                                       ║
║   ┌──────────────────────────────────────────────────────────────────────┐   ║
║   │  🔧 SCRIPT: scripts/create_v3_unified.py                             │   ║
║   │                                                                      │   ║
║   │  Comando:                                                            │   ║
║   │  python scripts/create_v3_unified.py                                 │   ║
║   │                                                                      │   ║
║   │  Função: Merge V2 + Easton + Smith → V3 unificado                    │   ║
║   │  Saída: data/dataset/topics_v3/                                      │   ║
║   └──────────────────────────────────────────────────────────────────────┘   ║
║                       │                                                       ║
║                       ▼                                                       ║
║            ┌─────────────────────┐                                           ║
║            │   Dataset V3.0      │                                           ║
║            │   7,873 tópicos     │                                           ║
║            │   5,955 c/ defs     │                                           ║
║            └─────────┬───────────┘                                           ║
║                      │                                                        ║
╚══════════════════════╪════════════════════════════════════════════════════════╝
                       │
                       ▼
╔═══════════════════════════════════════════════════════════════════════════════╗
║                FASE 3: EXTRAÇÃO DE REFS DAS DEFINIÇÕES                        ║
║                                                                               ║
║   Extrai referências bíblicas do texto das definições                        ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ┌──────────────────────────────────────────────────────────────────────┐   ║
║   │  🔧 SCRIPT: scripts/extract_definition_refs.py                       │   ║
║   │                                                                      │   ║
║   │  Comando:                                                            │   ║
║   │  python scripts/extract_definition_refs.py                           │   ║
║   │                                                                      │   ║
║   │  Função: Parse "(Luke 19:1-10)" → estrutura definition_refs          │   ║
║   │  Entrada: data/dataset/topics_v3/                                    │   ║
║   │  Saída: Atualiza os mesmos arquivos (in-place)                       │   ║
║   └──────────────────────────────────────────────────────────────────────┘   ║
║                       │                                                       ║
║                       ▼                                                       ║
║            ┌─────────────────────┐                                           ║
║            │   Dataset V3.1      │                                           ║
║            │   +17,715 refs      │                                           ║
║            │   extraídas         │                                           ║
║            └─────────┬───────────┘                                           ║
║                      │                                                        ║
╚══════════════════════╪════════════════════════════════════════════════════════╝
                       │
                       ▼
╔═══════════════════════════════════════════════════════════════════════════════╗
║              FASE 4: INTEGRAÇÃO DE CROSS-REFERENCES                           ║
║                                                                               ║
║   Conecta tópicos via rede de referências cruzadas                           ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ┌──────────────────────────────────────────────────────────────────────┐   ║
║   │  📂 Cross-refs Dataset                                               │   ║
║   │  Localização: data/dataset/cross_references/unified/verses/          │   ║
║   │  Arquivos: 31,060 (genesis_1_1.json, john_3_16.json, etc.)           │   ║
║   │  Total: 1,117,491 referências cruzadas                               │   ║
║   └──────────────────────────────────────────────────────────────────────┘   ║
║                       │                                                       ║
║                       ▼                                                       ║
║   ┌──────────────────────────────────────────────────────────────────────┐   ║
║   │  🔧 SCRIPT: scripts/integrate_crossrefs_v3.py                        │   ║
║   │                                                                      │   ║
║   │  Comando:                                                            │   ║
║   │  python scripts/integrate_crossrefs_v3.py                            │   ║
║   │                                                                      │   ║
║   │  Funções:                                                            │   ║
║   │  1. collect_topic_refs() - coleta refs de cada tópico                │   ║
║   │  2. process_topic() - busca cross-refs para cada ref                 │   ║
║   │  3. calculate_connected_topics() - calcula conexões entre tópicos    │   ║
║   │                                                                      │   ║
║   │  Entrada: data/dataset/topics_v3/ + cross_references/                │   ║
║   │  Saída: Atualiza topics_v3/ com cross_reference_network,             │   ║
║   │         cross_ref_stats, connected_topics                            │   ║
║   └──────────────────────────────────────────────────────────────────────┘   ║
║                       │                                                       ║
║                       ▼                                                       ║
║            ┌─────────────────────┐                                           ║
║            │   Dataset V3.2      │                                           ║
║            │   5,642 c/ crossref │                                           ║
║            │   112,835 conexões  │                                           ║
║            └─────────┬───────────┘                                           ║
║                      │                                                        ║
╚══════════════════════╪════════════════════════════════════════════════════════╝
                       │
                       ▼
╔═══════════════════════════════════════════════════════════════════════════════╗
║                   FASE 5: ENRIQUECIMENTO COM IA                               ║
║                                                                               ║
║   GPT-4 gera themes, questions, applications para cada tópico                ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ┌──────────────────────────────────────────────────────────────────────┐   ║
║   │  📄 PROMPTS: scripts/topical_pipeline/phase0/prompts.py              │   ║
║   │                                                                      │   ║
║   │  Funções:                                                            │   ║
║   │  • prepare_topic_for_enrichment() - monta contexto do tópico         │   ║
║   │  • get_enrichment_prompt() - gera prompt completo                    │   ║
║   │  • _build_outline_from_data() - outline híbrido programático         │   ║
║   │  • _build_connections() - inclui connected_topics                    │   ║
║   │  • _format_sources() - formata definições por fonte                  │   ║
║   │                                                                      │   ║
║   │  Estratégia de Outline:                                              │   ║
║   │  ┌────────────────────────────────────────────────────────────────┐  │   ║
║   │  │ 1. Extrai entry_labels do Torrey/Nave programaticamente       │  │   ║
║   │  │ 2. Passa como "Outline Sugerido" para a IA                    │  │   ║
║   │  │ 3. IA REFINA (não regenera) mantendo referências              │  │   ║
║   │  │ 4. IA descobre novos aspectos (discovered_aspects)            │  │   ║
║   │  │ 5. Discovered aspects são mesclados ao outline final          │  │   ║
║   │  └────────────────────────────────────────────────────────────────┘  │   ║
║   └──────────────────────────────────────────────────────────────────────┘   ║
║                       │                                                       ║
║                       ▼                                                       ║
║   ┌──────────────────────────────────────────────────────────────────────┐   ║
║   │  🔧 SCRIPT: scripts/topical_pipeline/run_phase0.py                   │   ║
║   │                                                                      │   ║
║   │  Comandos:                                                           │   ║
║   │  cd scripts/topical_pipeline                                         │   ║
║   │  python run_phase0.py --limit 100 --delay 0.3                        │   ║
║   │                                                                      │   ║
║   │  Parâmetros:                                                         │   ║
║   │  --limit N     : Processa N tópicos (útil para teste)                │   ║
║   │  --delay X     : Delay entre requests (evita rate limit)             │   ║
║   │  --resume      : Continua de onde parou                              │   ║
║   │                                                                      │   ║
║   │  Entrada: data/dataset/topics_v3/                                    │   ║
║   │  Saída: Atualiza cada tópico com:                                    │   ║
║   │    - ai_enrichment: {summary, outline, key_concepts, ...}            │   ║
║   │    - ai_discovered_aspects: [{label, references, rationale}]         │   ║
║   │  Logs: scripts/topical_pipeline/data/logs/phase0_current.json        │   ║
║   └──────────────────────────────────────────────────────────────────────┘   ║
║                       │                                                       ║
║                       ▼                                                       ║
║   ┌──────────────────────────────────────────────────────────────────────┐   ║
║   │  🧪 TESTE: scripts/test_enrichment_comparison.py                     │   ║
║   │                                                                      │   ║
║   │  Comando:                                                            │   ║
║   │  python scripts/test_enrichment_comparison.py --topic GRACE          │   ║
║   │                                                                      │   ║
║   │  Saída:                                                              │   ║
║   │  - data/dataset/test_comparison/GRACE_prompt.txt                     │   ║
║   │  - data/dataset/test_comparison/GRACE_enriched.json                  │   ║
║   │  - data/dataset/test_comparison/GRACE_comparison.md                  │   ║
║   └──────────────────────────────────────────────────────────────────────┘   ║
║                       │                                                       ║
║                       ▼                                                       ║
║            ┌─────────────────────┐                                           ║
║            │   Dataset V3 FINAL  │                                           ║
║            │   3,837 enriquecidos│                                           ║
║            │   + discovered      │                                           ║
║            │     aspects         │                                           ║
║            └─────────────────────┘                                           ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝


══════════════════════════════════════════════════════════════════════════════════
                              SCRIPTS AUXILIARES
══════════════════════════════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────────────────────────┐
│  🔧 scripts/merge_pipeline_to_v3.py                                          │
│                                                                              │
│  Comando: python scripts/merge_pipeline_to_v3.py                             │
│                                                                              │
│  Função: Migra ai_enrichment de arquivos antigos para V3                     │
│  Útil quando: Já tem enriquecimentos em outro local e quer migrar            │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  📊 Verificar Estatísticas do Dataset                                        │
│                                                                              │
│  Comando (PowerShell):                                                       │
│  python -c "                                                                 │
│  import json, os                                                             │
│  from collections import defaultdict                                         │
│  # ... código de estatísticas ...                                            │
│  "                                                                           │
│                                                                              │
│  Ou consulte: docs/TOPICS_DATASET_EVOLUTION.md (este arquivo)                │
└──────────────────────────────────────────────────────────────────────────────┘


══════════════════════════════════════════════════════════════════════════════════
                           ORDEM DE EXECUÇÃO
══════════════════════════════════════════════════════════════════════════════════

  Para recriar o dataset do zero:

  1️⃣  python scripts/create_v3_unified.py
      → Cria V3 com Torrey + Nave + Easton + Smith

  2️⃣  python scripts/extract_definition_refs.py
      → Extrai refs das definições

  3️⃣  python scripts/integrate_crossrefs_v3.py
      → Adiciona cross-refs e calcula conexões

  4️⃣  cd scripts/topical_pipeline && python run_phase0.py
      → Enriquece com IA (pode rodar em batches)

══════════════════════════════════════════════════════════════════════════════════
```

---

## 🗂️ Fontes de Dados

### 1. Torrey's New Topical Textbook (TOR)
- **Origem**: Clássico de referência bíblica (1897)
- **Estrutura**: Tópicos hierárquicos com subtópicos
- **Foco**: Organização sistemática de versículos por tema
- **Identificador**: `source: "TOR"`

### 2. Nave's Topical Bible (NAV)
- **Origem**: Orville J. Nave (1896)
- **Estrutura**: 20,000+ tópicos e subtópicos
- **Foco**: Índice exaustivo de referências bíblicas
- **Identificador**: `source: "NAV"`

### 3. Easton's Bible Dictionary (EAS)
- **Origem**: Matthew George Easton (1897)
- **Estrutura**: Entradas de dicionário com definições
- **Foco**: Definições teológicas e históricas
- **Identificador**: `source: "EAS"`

### 4. Smith's Bible Dictionary (SMI)
- **Origem**: William Smith (1863)
- **Estrutura**: Enciclopédia bíblica
- **Foco**: Contexto histórico e arqueológico
- **Identificador**: `source: "SMI"`

### 5. Cross-References Dataset
- **Origem**: Treasury of Scripture Knowledge + outras fontes
- **Estrutura**: 31,060 arquivos de versículos
- **Total**: 1,117,491 referências cruzadas
- **Localização**: `data/dataset/cross_references/unified/verses/`

---

## 📈 Evolução por Versão

### V1 - Dataset Inicial (Torrey + Nave)

**Período**: Fase inicial do projeto

**Processo**:
1. Parsing dos arquivos fonte de Torrey e Nave
2. Normalização de referências bíblicas
3. Estruturação em formato JSON

**Estrutura**:
```json
{
  "topic_name": "FAITH",
  "source": "TOR",
  "content": "...",
  "references": ["Heb 11:1", "Rom 10:17", ...]
}
```

**Resultado**: ~5,466 tópicos únicos

---

### V2 - Unificação e Deduplicação

**Período**: Consolidação dos datasets

**Processo**:
1. Merge de tópicos duplicados entre Torrey e Nave
2. Unificação de aliases e variações de nomes
3. Consolidação de referências bíblicas

**Melhorias**:
- Tópicos com múltiplas fontes combinadas
- Aliases unificados (ex: "FAITH", "Faith", "Belief")
- Referências deduplicadas

**Estrutura**:
```json
{
  "topic_name": "FAITH",
  "aliases": ["Faith", "Belief", "Trust"],
  "sources": ["TOR", "NAV"],
  "references": [...],
  "content": "..."
}
```

**Resultado**: 5,466 tópicos consolidados

---

### V3 - Dataset Unificado com Dicionários

**Período**: Dezembro 2024

**Processo**:
1. Integração de Easton's Bible Dictionary (3,831 entradas)
2. Integração de Smith's Bible Dictionary (4,685 entradas)
3. Merge inteligente com tópicos existentes
4. Preservação de definições únicas

**Scripts**:
- `scripts/create_v3_unified.py` - Criação do dataset unificado
- `scripts/merge_pipeline_to_v3.py` - Merge de enriquecimentos existentes

**Ganhos**:
| Métrica | Antes | Depois | Ganho |
|---------|-------|--------|-------|
| Tópicos | 5,466 | 7,873 | +44% |
| Com definições | 0 | 4,438 | +4,438 |
| Fontes por tópico | 1-2 | 1-4 | +100% |

**Nova Estrutura**:
```json
{
  "topic_name": "ZACCHAEUS",
  "slug": "zacchaeus",
  "aliases": ["Zacchaeus", "Zacchæus"],
  "sources": ["EAS", "SMI"],
  "definitions": {
    "EAS": "A Jewish publican...",
    "SMI": "A tax-collector of Jericho..."
  },
  "references": ["Luke 19:1-10"],
  "created_at": "2024-12-01T...",
  "updated_at": "2024-12-01T..."
}
```

---

### V3.1 - Extração de Referências de Definições

**Período**: Dezembro 2024

**Problema Identificado**:
As definições dos dicionários continham referências bíblicas embutidas no texto (ex: "mentioned in (Luke 19:1-10)") que não estavam estruturadas.

**Processo**:
1. Parser de regex para extrair referências do texto
2. Normalização para formato canônico
3. Adição ao campo `references` do tópico

**Script**: `scripts/extract_definition_refs.py`

**Padrões Detectados**:
```
(Luke 19:1-10)           → Luke 19:1-10
see Gen. 1:1             → Genesis 1:1
Matt. 5:3-12             → Matthew 5:3-12
1 Cor. 13                → 1 Corinthians 13
```

**Ganhos**:
| Métrica | Valor |
|---------|-------|
| Referências extraídas | 17,715 |
| Tópicos beneficiados | 4,438 |
| Média por tópico | 4.0 refs |

**Nova Estrutura**:
```json
{
  "definition_refs": ["Luke 19:1-10"],
  "definition_refs_stats": {
    "extracted_refs": 1,
    "from_definitions": ["EAS", "SMI"]
  }
}
```

---

### V3.2 - Integração de Referências Cruzadas

**Período**: Dezembro 2024

**Objetivo**:
Conectar tópicos através da rede de 1.1M+ referências cruzadas existente no dataset.

**Processo**:
1. Coleta de todas as referências de cada tópico
2. Lookup nas 31,060 arquivos de cross-refs
3. Expansão da rede de versículos relacionados
4. Cálculo de conexões entre tópicos

**Script**: `scripts/integrate_crossrefs_v3.py`

**Algoritmo de Conexões**:
```python
# Para cada par de tópicos
for topic_a, topic_b in combinations(topics, 2):
    refs_a = set(topic_a.all_references)
    refs_b = set(topic_b.all_references)
    
    # Conexões diretas (mesma ref)
    direct = refs_a & refs_b
    
    # Conexões via cross-refs
    crossref_a = expand_via_crossrefs(refs_a)
    crossref_b = expand_via_crossrefs(refs_b)
    via_crossref = crossref_a & refs_b | refs_a & crossref_b
    
    shared = len(direct) + len(via_crossref)
    if shared > 0:
        connections.append((topic_a, topic_b, shared))
```

**Ganhos**:
| Métrica | Valor |
|---------|-------|
| Cross-refs adicionadas | 1,922,869 |
| Tópicos com cross-refs | 5,642 (72%) |
| Conexões descobertas | 112,835 |
| Média conexões/tópico | 20 |

**Nova Estrutura**:
```json
{
  "cross_reference_network": {
    "Genesis 1:1": ["John 1:1", "Psalm 33:6", ...],
    "John 3:16": ["Romans 5:8", "1 John 4:9", ...]
  },
  "cross_ref_stats": {
    "total_connections": 5829,
    "unique_verses_reached": 3320,
    "source_refs_with_crossrefs": 245
  },
  "connected_topics": [
    {"topic": "FAITH", "shared_refs": 3206},
    {"topic": "SALVATION", "shared_refs": 2891}
  ]
}
```

---

### V3.3 - Atualização dos Prompts de IA

**Período**: Dezembro 2024

**Objetivo**:
Aproveitar todos os novos dados no prompt enviado ao GPT para enriquecimento.

**Arquivo**: `scripts/topical_pipeline/phase0/prompts.py`

**Melhorias no Prompt**:

1. **Definições dos Dicionários**:
```
## Definições (Dicionários Bíblicos)

**Easton's Bible Dictionary**:
A chief tax-gatherer at Jericho...

**Smith's Bible Dictionary**:
A wealthy publican who became a follower...
```

2. **Tópicos Conectados**:
```
## Conexões com Outros Tópicos
Tópicos conectados (via refs cruzadas): FAITH (3206 refs), SALVATION (2891 refs)...
```

3. **Estatísticas da Rede**:
```
Rede de referências: 5829 conexões para 3320 versículos únicos
```

**Impacto no Enriquecimento**:
| Aspecto | Antes | Depois |
|---------|-------|--------|
| Contexto para IA | Básico | Rico |
| Definições | ❌ | ✅ |
| Conexões | ❌ | ✅ |
| Rede de refs | ❌ | ✅ |

---

### V3.4 - Estratégia de Outline Híbrido + Discovered Aspects

**Período**: Dezembro 2024

**Problema Identificado**:
1. Os outlines gerados pela IA eram genéricos ("Definição de X", "Referências sobre Y")
2. A IA estava regenerando dados que já existiam no Torrey/Nave
3. Aspectos importantes não cobertos pelo Torrey/Nave não eram descobertos

**Solução Implementada**:

#### 1. Outline Híbrido (usa dados existentes programaticamente)

**Arquivo**: `scripts/topical_pipeline/phase0/prompts.py`

**Função**: `_build_outline_from_data(topic_data)`

**Estratégia**:
```
┌─────────────────────────────────────────────────────────────────┐
│  SE tem reference_groups (Nave/Torrey)                          │
│    → Extrai entry_labels + referências programaticamente        │
│    → Instrução: "REFINE o outline sugerido"                     │
│    → IA melhora o texto mantendo as refs                        │
├─────────────────────────────────────────────────────────────────┤
│  SE só tem dictionary_refs (apenas dicionários)                 │
│    → Extrai referências citadas nas definições                  │
│    → Instrução: "REFINE o outline sugerido"                     │
│    → IA infere contexto das refs                                │
├─────────────────────────────────────────────────────────────────┤
│  SE não tem dados                                               │
│    → Instrução: "GERE novo outline"                             │
│    → IA cria do zero (com exemplos de bom/ruim)                 │
└─────────────────────────────────────────────────────────────────┘
```

**Exemplo de Transformação (GRACE)**:

| Input (Torrey/Nave) | Output (IA Refinado) |
|---------------------|----------------------|
| God is the God of all (1 Peter 5:10) | A natureza da graça: favor imerecido de Deus (Efésios 2:5; Romanos 11:6) |
| God is the Giver of (Psalms 84:11) | A graça como dom espiritual: capacitação para a vida cristã (1 Coríntios 15:10) |
| Was upon Christ (Luke 2:40) | A graça revelada em Cristo: a plenitude da graça (João 1:14; Lucas 2:40) |

#### 2. Discovered Aspects (novos aspectos não cobertos)

**Modelo**: `DiscoveredAspect` em `scripts/topical_pipeline/phase0/models.py`

**Objetivo**: Identificar aspectos do tópico que Nave/Torrey não cobriram

**Estrutura**:
```json
{
  "label": "Grace as a transformative power in believers' lives",
  "references": ["2 Corinthians 12:9", "Titus 2:11-12"],
  "rationale": "A graça não apenas perdoa, mas também transforma a vida do crente...",
  "source": "ai_discovery"
}
```

**Foco da Descoberta**:
- ✅ Perspectivas do NT para temas do AT
- ✅ Aplicações práticas não cobertas
- ✅ Conexões tipológicas (tipos e sombras de Cristo)
- ✅ Aspectos teológicos sistemáticos

#### 3. Fusão Automática no Outline

**Os discovered_aspects são automaticamente mesclados no outline final**:

```python
# service.py - após processar discovered_aspects
if discovered_aspects and content:
    for aspect in discovered_aspects:
        refs_str = "; ".join(aspect.references[:3])
        outline_point = f"{aspect.label} ({refs_str})"
        if outline_point not in content.outline:
            content.outline.append(outline_point)
```

**Exemplo de Outline Final (GRACE)**:
```
1. A natureza da graça: favor imerecido de Deus (Efésios 2:5; Romanos 11:6)
2. A graça como dom espiritual: capacitação para a vida cristã (1 Coríntios 15:10)
3. A graça revelada em Cristo: a plenitude da graça (João 1:14; Lucas 2:40)
4. A graça e o papel do Espírito Santo (Zacarias 12:10; Hebreus 10:29)
5. A graça como distinção do evangelho em relação à lei (João 1:17; Romanos 6:14)
6. A esperança da glória futura (1 Pedro 1:13)
7. Grace as a transformative power in believers' lives (2 Cor 12:9; Titus 2:11-12)  ← DESCOBERTO
8. Typology of grace in the Old Testament sacrifices (Lev 4:20; Heb 9:22)          ← DESCOBERTO
```

**Ganhos**:
| Métrica | Antes | Depois |
|---------|-------|--------|
| Pontos de outline | 3-6 genéricos | 6-10 específicos |
| Referências por ponto | 0-1 | 2-3 |
| Aspectos descobertos | 0 | 2-5 por tópico |
| Qualidade do estudo | Básica | Rica |

**Script de Teste**: `scripts/test_enrichment_comparison.py`
```bash
# Testar enriquecimento de um tópico específico
python scripts/test_enrichment_comparison.py --topic GRACE

# Saída:
# - GRACE_prompt.txt (prompt enviado à IA)
# - GRACE_enriched.json (resultado completo)
# - GRACE_comparison.md (comparação antes/depois)
```

---

## 🔬 Exemplos de Tópicos Enriquecidos

### Exemplo 1: SIN (Pecado)

```json
{
  "topic_name": "SIN",
  "sources": ["TOR", "NAV", "EAS", "SMI"],
  "definitions": {
    "EAS": "Sin is any want of conformity unto, or transgression of...",
    "SMI": "The Hebrew and Greek words translated sin..."
  },
  "references": ["Rom 3:23", "1 John 3:4", ...],
  "cross_ref_stats": {
    "total_connections": 5829,
    "unique_verses_reached": 3320
  },
  "connected_topics": [
    {"topic": "FAITH", "shared_refs": 3206},
    {"topic": "IDOLATRY", "shared_refs": 2795},
    {"topic": "SALVATION", "shared_refs": 2891}
  ]
}
```

### Exemplo 2: ABRAHAM

```json
{
  "topic_name": "ABRAHAM",
  "sources": ["TOR", "NAV", "EAS", "SMI"],
  "definitions": {
    "EAS": "Father of a multitude, originally Abram...",
    "SMI": "The son of Terah, and founder of the Hebrew nation..."
  },
  "cross_ref_stats": {
    "total_connections": 2109,
    "unique_verses_reached": 1245
  },
  "connected_topics": [
    {"topic": "FAITH", "shared_refs": 2332},
    {"topic": "COVENANT", "shared_refs": 1876}
  ]
}
```

---

## 📁 Estrutura de Arquivos

```
data/dataset/
├── topics_v3/                    # Dataset unificado V3
│   ├── A/
│   │   ├── aaron.json
│   │   ├── abraham.json
│   │   └── ...
│   ├── B/
│   ├── ...
│   └── Z/
├── cross_references/
│   └── unified/
│       └── verses/               # 31,060 arquivos de cross-refs
│           ├── genesis_1_1.json
│           ├── john_3_16.json
│           └── ...
└── dictionary/
    ├── easton/                   # Easton's Bible Dictionary
    └── smith/                    # Smith's Bible Dictionary

scripts/
├── create_v3_unified.py          # Cria V3 a partir de V2 + dicionários
├── merge_pipeline_to_v3.py       # Merge enriquecimentos para V3
├── extract_definition_refs.py    # Extrai refs das definições
├── integrate_crossrefs_v3.py     # Integra cross-refs ao V3
└── topical_pipeline/
    └── phase0/
        └── prompts.py            # Prompts atualizados para IA
```

---

## 📊 Métricas Comparativas

### Evolução do Dataset

| Versão | Tópicos | Fontes | Definições | Cross-refs | Conexões | IA | Discovered |
|--------|---------|--------|------------|------------|----------|-----|------------|
| V1 | ~5,000 | 2 | ❌ | ❌ | ❌ | ❌ | ❌ |
| V2 | 5,466 | 2 | ❌ | ❌ | ❌ | ❌ | ❌ |
| V3.0 | 7,873 | 4 | 5,955 | ❌ | ❌ | ❌ | ❌ |
| V3.1 | 7,873 | 4 | 5,955 | ❌ | ❌ | 3,837 | ❌ |
| V3.2 | 7,873 | 4 | 5,955 | 5,642 | 112,835 | 3,837 | ❌ |
| V3.4 | 7,873 | 4 | 5,955 | 5,642 | 112,835 | ✅ | ✅ |

### Cobertura por Fonte

| Fonte | Tópicos | % do Total |
|-------|---------|------------|
| Nave (NAV) | 5,234 | 66.5% |
| Smith (SMI) | 4,546 | 57.7% |
| Easton (EAS) | 3,956 | 50.2% |
| Torrey (TOR) | 618 | 7.8% |

### Combinações de Fontes (Top 5)

| Combinação | Tópicos |
|------------|---------|
| EAS + NAV + SMI | 2,010 |
| NAV apenas | 1,422 |
| SMI apenas | 1,133 |
| NAV + SMI | 863 |
| EAS apenas | 840 |

### Qualidade do Enriquecimento IA

| Status | Tópicos | % |
|--------|---------|---|
| Enriquecidos | 3,837 | 48.7% |
| Pendentes | 4,036 | 51.3% |

---

## 🚀 Próximos Passos

1. **Completar Enriquecimento IA**
   - 4,036 tópicos pendentes (51.3%)
   - Prompts agora incluem definições, conexões e outline híbrido
   - Discovered aspects expandindo dados além do Nave/Torrey
   - Qualidade esperada: muito superior

2. **Integração com API**
   - Expor tópicos via endpoint REST
   - Busca semântica por tópicos (RAG)
   - Navegação por conexões

3. **Visualização**
   - Grafo de conexões entre tópicos
   - Mapa de referências cruzadas
   - Timeline de personagens bíblicos

---

## 📝 Changelog

### 2024-12-02 (V3.4)
- Implementação de Outline Híbrido (usa dados existentes programaticamente)
- Implementação de Discovered Aspects (IA descobre novos aspectos)
- Fusão automática de discovered_aspects no outline final
- Script de teste: `scripts/test_enrichment_comparison.py`
- Modelo `DiscoveredAspect` adicionado aos models

### 2024-12-02 (V3.2)
- Documentação completa do processo de evolução
- Integração de 1.9M cross-refs ao V3
- Cálculo de 112,835 conexões entre tópicos
- Atualização dos prompts com definições e conexões

### 2024-12-01
- Criação do V3 unificado (7,873 tópicos)
- Extração de 17,715 refs das definições
- Merge de enriquecimentos existentes

---

## 🔗 Referências

- [Torrey's New Topical Textbook](https://www.ccel.org/ccel/torrey/topical.html)
- [Nave's Topical Bible](https://www.ccel.org/ccel/nave/topical.html)
- [Easton's Bible Dictionary](https://www.ccel.org/ccel/easton/ebd2.html)
- [Smith's Bible Dictionary](https://www.ccel.org/ccel/smith_w/bibledict.html)
- [Treasury of Scripture Knowledge](https://www.ccel.org/ccel/treasury/treasury.html)
