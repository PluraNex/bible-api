# Documento-Mestre de Evidencias e Experimentos

## 1. Objetivo operacional
Transformar os datasets do projeto em instrumentos de experimento para avaliar recuperacao hibrida e vinculacao semantica biblica com trilha reproduzivel.

## 2. Estado auditado do repositório
Data da auditoria: 2026-03-12.

### Fonte de verdade
- Corpus completo: `data/dataset/topics_v3/`
- Evidencia documental do corpus: `docs/TOPICS_DATASET_EVOLUTION.md`
- Escala documentada do corpus V3: 7.873 topicos

### Piloto operacional
- Subconjunto enriquecido: `scripts/topical_pipeline/data/topics_v3/`
- Escala observada no repositório: 336 arquivos JSON
- Cobertura Phase 0 observada: 326/336 com `ai_enrichment`
- Cobertura `ai_themes_normalized`: 333/336
- Cobertura Phase 1 observada: 231/336 com `phase1_discovery`
- Distribuicao atual: `A=334`, `C=1`, `D=1`

### Outros fatos-base
- Endpoint experimental: `bible/ai/views.py`
- Engine hibrida: `bible/ai/hybrid.py`
- Servico de busca: `bible/ai/services.py`
- Configuracoes de promocao e busca: `scripts/topical_pipeline/phase2/config.py`
- Diagnostico atual do piloto: `2474` entidades e `347` simbolos
- Snapshot recente de gazetteers: `scripts/topical_pipeline/data/test_snapshot.json`
- Evidencia historica do snapshot: `2447` entidades e `345` simbolos em `2025-12-06`

### Falha estrutural corrigida nesta sprint
- `run_phase0.py` ja operava com `data/dataset/topics_v3 -> scripts/topical_pipeline/data/topics_v3`
- `run_phase1.py` e `diagnose_pipeline.py` ainda apontavam para `scripts/topical_pipeline/data/topics`
- Consequencia: a continuidade `phase0 -> phase1` e o diagnostico salvo ficavam incorretos

## 3. Decisao do piloto oficial
- Piloto oficial: `scripts/topical_pipeline/data/topics_v3/`
- Slice principal de reporte: letra `A`
- Letras `C` e `D`: smoke cases apenas
- Decisao de escopo: rodar o primeiro benchmark no subset atual antes de expandir novas letras

Justificativa:
- Ja existe material enriquecido suficiente para estabilizar protocolo e evidencias
- O subset atual expõe as quebras reais do pipeline sem diluir o esforço em expansao precoce
- A letra `A` concentra a maior parte da cobertura e serve como piloto coerente para auditoria e repetibilidade

## 4. Protocolo experimental
Comparacoes centrais da primeira rodada:

| Grupo | Controle | Variacoes |
|-------|----------|-----------|
| `alpha` | `0.5` | `1.0`, `0.0` |
| `expand` | `false` | `true` |
| `rerank` | `false` | `true` |
| `mmr_lambda` | `0.8` | `0.5`, `0.2` |
| `embedding_source` | `verse` | `unified` |

Estratificacao de analise:
- tipo de consulta: entidade, frase, conceito, referencia, pergunta
- livro
- versao
- configuracao

## 5. Metricas oficiais
- Precision@K
- Recall@K
- MAP
- NDCG
- Latencia total
- Diversidade por livros e referencias unicas
- Taxa de concordancia com crossrefs
- Taxa de concordancia com comentarios
- Taxa de descobertas novas plausiveis

Observacao:
- O runner novo calcula proxies de latencia, diversidade e cobertura por sinais esperados desde ja
- MAP e NDCG passam a ficar disponiveis quando o arquivo de queries receber julgamentos de relevancia

## 6. Base de avaliacao
Arquivo inicial:
- `data/experiments/hybrid_search/pilot_queries_v1.json`

Status da base:
- Seed inicial de queries e sinais esperados
- Ainda requer preenchimento manual de `gold_references` e `relevance_judgments`

Documento de apoio metodologico:
- `docs/research/TRUTH_SOURCE_STRATEGY.md`
- define quais fontes entram como `gold`, `silver` e `signal`

Fontes para completar a verdade de referencia:
- referencias cruzadas
- comentarios / CCEL / patrística
- temas promovidos
- topicos enriquecidos
- casos manuais curados

## 7. Comandos reproduziveis
Auditoria do piloto:

```bash
python scripts/topical_pipeline/diagnose_pipeline.py
```

Verificacao da continuidade Phase 1:

```bash
python scripts/topical_pipeline/run_phase1.py --dry-run --letter A --limit 20
```

Primeira rodada de benchmark:

```bash
python scripts/run_hybrid_benchmark.py --dry-run
python scripts/run_hybrid_benchmark.py
```

Recorte de benchmark por experimento:

```bash
python scripts/run_hybrid_benchmark.py --experiment baseline_hybrid --experiment alpha_lexical --experiment alpha_semantic
```

Recorte por query:

```bash
python scripts/run_hybrid_benchmark.py --query-id q001 --query-id q006
```

## 8. Artefatos esperados
Diretorio de saida:
- `data/experiments/hybrid_search/runs/<timestamp>/`

Arquivos gerados por rodada:
- `plan.json`
- `summary.json`
- `summary.csv`
- `aggregate.csv`
- `raw/<experimento>/<query>.json`

## 9. Criterio de saida desta sprint
- Recorte do TCC fechado
- Diagnostico do piloto confiavel
- Continuidade `phase0 -> phase1` estabilizada
- Runner de benchmark compatível com a API atual
- Estrutura de evidencias criada para repeticao e escrita
