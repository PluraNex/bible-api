# Inventario de Datasets e Gaps

## Objetivo
Este documento consolida os datasets relevantes para o TCC, indicando:
- localizacao
- funcao metodologica
- status real de materializacao
- recomendacao de uso
- gaps e riscos

A meta e distinguir claramente:
- o que ja pode ser tratado como fonte oficial
- o que e piloto parcial
- o que e corpus auxiliar
- o que ainda esta incompleto ou so documentado

## Resumo executivo
No estado atual, o projeto ja possui base suficiente para iniciar a construcao do gold set, mas os datasets nao estao igualmente prontos.

Leitura curta:
- `topics_v3`, `cross_references` e `dictionary` estao maduros
- o `piloto do topical pipeline` esta parcial, mas util
- o corpus principal de comentarios do TCC existe e esta bem organizado, mas sua cadeia `structured -> embeddings -> unified` ainda nao esta materializada
- os datasets externos do `E:` sao importantes, mas nao devem ser confundidos com as fontes principais do TCC sem uma decisao metodologica explicita

## Classificacao operacional

### Categoria A - Oficial agora
Datasets que ja podem entrar na fase inicial da pesquisa.

1. `data/dataset/topics_v3/`
2. `data/dataset/cross_references/`
3. `data/dataset/dictionary/`
4. `scripts/topical_pipeline/data/topics_v3/` como piloto oficial
5. `data/experiments/hybrid_search/`

### Categoria B - Oficial com restricao
Fontes que existem e sao importantes, mas precisam ser usadas com recorte e cautela.

1. `data/dataset/commentaries/`
2. `C:/Users/Iury Coelho/Desktop/TCC/Datasets/commentaries/`

### Categoria C - Auxiliar externo
Fontes relevantes para contexto, comparacao ou validacao complementar.

1. `E:/comentarios_pesquisa_ceel/`
2. `E:/embeding_data_openai_small_ceel/`
3. `E:/emdeding_data_openai_large_ceel/`
4. `E:/embeding_bibles/`

### Categoria D - Nao usar como base principal agora
Artefatos incompletos, antigos ou de reparo.

1. `C:/Users/Iury Coelho/processing_embedding_old/backup_old_files/ccel_missing/`
2. `scripts/topical_pipeline/data/topics_deprecated/`
3. `data/dataset/topics_v2_deprecated/`

## Inventario detalhado

## 1. Topics V3
### Localizacao
- `data/dataset/topics_v3/`

### Estado
- presente
- `7.874` arquivos totais
- `25` diretorios por letra + `_index.json`

### Papel metodologico
- corpus principal de topicos
- base para definicoes, refs, conectividade e enrichment

### Forca
- melhor dataset topical consolidado do projeto
- combina Nave, Torrey, Easton, Smith, refs extraidas e crossrefs integrados

### Gaps
- nao possui `README` local na propria pasta
- depende de documentacao externa para historia de construcao

### Recomendacao
- tratar como `fonte oficial`

## 2. Dicionario
### Localizacao
- `data/dataset/dictionary/`

### Estado
- presente
- `26` arquivos
- `_index.json` materializado
- `5.998` entradas
- `35.089` refs

### Papel metodologico
- definicoes enciclopedicas
- base para `definitions` e `definition_refs`

### Forca
- bem indexado
- pronto para uso

### Gaps
- deve entrar como `silver`, nao como gold principal

### Recomendacao
- tratar como `fonte oficial auxiliar`

## 3. Cross References
### Localizacao
- `data/dataset/cross_references/`

### Estado
- presente
- `31.101` arquivos totais
- estrutura `raw`, `processed`, `unified`
- `README.md` e `METHODOLOGY.md`
- `31.060` arquivos JSON em `unified/verses`

### Papel metodologico
- validacao estrutural forte
- principal fonte `gold` para links intertextuais

### Forca
- um dos datasets mais bem organizados do projeto

### Gaps
- crossref nao equivale automaticamente a relacao tematica

### Recomendacao
- tratar como `fonte oficial gold`

## 4. Piloto do topical pipeline
### Localizacao
- `scripts/topical_pipeline/data/topics_v3/`
- `scripts/topical_pipeline/data/themes/`

### Estado
- presente
- topicos do piloto: `336`
- letras materializadas: `A`, `C`, `D`
- themes materializados: catalogo, promoted, proposals, alias suggestions

### Papel metodologico
- piloto operacional do TCC
- base real para as primeiras rodadas experimentais

### Forca
- parcial, mas ja enriquecido e diagnosticado

### Gaps
- sem `README` local
- sem `_index.json`
- corpus parcial

### Recomendacao
- tratar como `piloto oficial`

## 5. Experimentos
### Localizacao
- `data/experiments/hybrid_search/`

### Estado
- presente
- `pilot_queries_v1.json`
- `README.md`
- `runs/`

### Papel metodologico
- query set
- artefatos de benchmark

### Forca
- estrutura correta ja criada

### Gaps
- query set ainda em curadoria
- runs existentes ainda nao representam rodada valida online

### Recomendacao
- tratar como `base oficial de experimento`

## 6. Corpus principal de comentarios do TCC
### Localizacao
- `data/dataset/commentaries/`
- espelho: `C:/Users/Iury Coelho/Desktop/TCC/Datasets/commentaries/`

### Estado
- presente
- `19.456` arquivos totais na arvore
- estrutura numerada de pipeline
- `PIPELINE_README.md` materializado

### Estrutura real observada
- `01_original_commentaries`: `18.569` arquivos
  - `new_testament`: `6.977`
  - `old_testament`: `11.592`
- `02_translated_enriched_commentaries`: `881` arquivos
  - atualmente concentrado em `John`
- `03_structured`: vazio
- `04_embeddings`: diretorios existem, mas sem arquivos materializados
- `05_unified_data`: vazio
- `06_analysis_results`: vazio
- `indexes`: vazio

### Papel metodologico
- corpus principal de comentarios patristicos / Catena para o TCC
- fonte importante para validacao teologica

### Forca
- corpus bruto principal ja existe
- pipeline documentado
- melhor candidato a comentario oficial da pesquisa

### Gaps
- traducao/enriquecimento apenas parcial
- embeddings dos comentarios nao materializados
- unificacao ainda nao materializada
- indices ainda nao materializados

### Recomendacao
- tratar como `fonte oficial com restricao`
- usar o que ja existe de forma explicita
- nao assumir que embeddings/unified estao prontos

## 7. CCEL comentarios extraidos
### Localizacao
- `E:/comentarios_pesquisa_ceel/`
- `E:/comentarios_pesquisa_ceel/biblical_commentaries_ceel/`

### Estado
- presente
- `PRECISION` e `COVERAGE` materializados
- relatorios e indices presentes

### Papel metodologico
- corpus auxiliar externo
- validacao complementar

### Forca
- ja possui cortes `precision` e `coverage`
- muito util para construir camada `gold/silver`

### Gaps
- esta fora do repositorio principal
- deve ser explicitamente tratado como corpus auxiliar externo
- nao deve ser confundido com o corpus principal de comentarios do TCC

### Recomendacao
- tratar como `fonte auxiliar externa`

## 8. Embeddings do CCEL bruto
### Localizacao
- `E:/embeding_data_openai_small_ceel/`
- `E:/emdeding_data_openai_large_ceel/`

### Estado
- `small`: `224` arquivos, com `222` shards principais + backups observados
- `large`: `104` arquivos

### Papel metodologico
- embeddings de corpus bruto de paragrafos do CCEL
- discovery exploratorio e comparacao externa

### Forca
- grande escala
- potencial para candidate generation

### Gaps
- nao e o corpus principal de comentarios do TCC
- `large` parece incompleto ou ao menos nao alinhado ao particionamento total esperado
- sem documentacao integrada ao repositorio principal

### Recomendacao
- tratar como `signal auxiliar`
- nao usar como base principal do experimento agora

## 9. Embeddings biblicos
### Localizacao
- `E:/embeding_bibles/`

### Estado
- presente
- backup dump e SQL
- evidencia historica de `1M+ embeddings`

### Papel metodologico
- evidencia de escala do sistema biblico
- apoio a narrativa da infraestrutura

### Forca
- importante para descrever cobertura biblica PT/EN

### Gaps
- corpus nao esta materializado localmente em forma navegavel no repo
- `data/processed/bibles` nao esta populado no workspace atual

### Recomendacao
- tratar como `fonte externa de infraestrutura`
- nao tratar como dataset operacional local ja pronto

## 10. ccel_missing
### Localizacao
- `C:/Users/Iury Coelho/processing_embedding_old/backup_old_files/ccel_missing/`

### Estado
- presente
- estrutura residual
- nao parece conter a base completa utilizavel no estado atual

### Papel metodologico
- artefato de reparo / processamento antigo

### Gaps
- sem clareza de completude
- nao e uma base principal confiavel no estado atual

### Recomendacao
- nao usar agora

## Questao de idioma

## Biblia
- a documentacao e os backups externos indicam versiculos em portugues e ingles
- porem essa base nao esta materializada de forma navegavel no workspace atual
- para o TCC, isso significa:
  - a cobertura PT/EN existe como capacidade do sistema
  - mas a evidência local imediata depende de corpus externo e/ou banco restaurado

## Comentarios do TCC
- corpus bruto principal esta em ingles
- traducao/enriquecimento em portugues esta parcial
- embeddings em `pt` ainda nao estao materializados

## Consequencia metodologica
- a pesquisa inicial deve assumir que a camada de comentarios esta mais madura em `EN` do que em `PT`
- qualquer afirmacao forte sobre validacao PT de comentarios deve ser condicionada ao estado parcial da traducao

## Principais gaps que podem influenciar o gold set
1. O corpus de topicos usado no piloto e parcial.
2. O corpus principal de comentarios do TCC existe, mas so parte dele foi traduzida/enriquecida.
3. A camada de embeddings dos comentarios do TCC ainda nao esta materializada.
4. O corpus biblico PT/EN embedado esta documentado e respaldado por backups externos, mas nao esta completamente acessivel no workspace como dataset navegavel.
5. O `CCEL` bruto e seus embeddings nao devem ser confundidos com o corpus principal de comentarios do TCC.
6. Existem espelhos e duplicatas de datasets entre repo, `Desktop/TCC` e `E:`, o que exige governanca explicita.

## Decisoes recomendadas
### Usar agora
- `data/dataset/topics_v3/`
- `data/dataset/cross_references/`
- `data/dataset/dictionary/`
- `scripts/topical_pipeline/data/topics_v3/`
- `data/experiments/hybrid_search/`
- `data/dataset/commentaries/01_original_commentaries/`
- `data/dataset/commentaries/02_translated_enriched_commentaries/` com escopo explicitamente parcial
- `E:/comentarios_pesquisa_ceel/biblical_commentaries_ceel/` como auxiliar externo

### Nao assumir como pronto agora
- `data/dataset/commentaries/03_structured/`
- `data/dataset/commentaries/04_embeddings/`
- `data/dataset/commentaries/05_unified_data/`
- `data/dataset/commentaries/06_analysis_results/`
- `E:/emdeding_data_openai_large_ceel/` como base completa validada

### Tratar como externo/infraestrutura
- `E:/embeding_bibles/`

## Proximo passo recomendado
Antes de construir o gold set final:
1. congelar este inventario como referencia metodologica
2. declarar oficialmente quais fontes serao usadas na primeira rodada
3. marcar cada uma como `gold`, `silver`, `signal` ou `infra`
4. so depois iniciar a validacao query por query
