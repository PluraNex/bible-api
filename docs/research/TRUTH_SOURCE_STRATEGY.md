# Estrategia de Fonte de Verdade

## Objetivo
Definir como as fontes do projeto serao usadas para validar a busca hibrida e a vinculacao semantica no TCC, separando:
- `gold`: verdade principal
- `silver`: verdade auxiliar
- `signal`: sinal experimental e interpretativo

Este documento existe para evitar circularidade metodologica e para tornar a validacao reproduzivel.

## Principio central
Embeddings, scores semanticos e heuristicas do proprio motor de busca nao devem ser usados como unica fonte de verdade principal.

Leitura correta:
- o sistema de retrieval produz candidatos e scores
- a fonte de verdade deve vir, preferencialmente, de camadas mais independentes
- o experimento compara configuracoes do metodo contra essas camadas

## Papel operacional dos embeddings
Embeddings podem e devem ser usados para `pesquisa exploratoria`, `candidate generation` e `priorizacao de revisao`.

Uso correto:
- encontrar versiculos candidatos
- encontrar comentarios semanticamente proximos
- encontrar topicos e temas relacionados
- reduzir o universo de leitura manual
- apoiar reranking e explicabilidade

Uso incorreto:
- declarar que o proprio score de embedding ja e a verdade final
- usar somente similaridade vetorial para validar um sistema vetorial

Regra metodologica:
- embeddings entram como `camada de descoberta`
- fontes independentes entram como `camada de validacao`

Formula simples:
- `embedding = detector`
- `crossrefs/comentarios/curadoria = juiz`

## Classificacao das fontes

## 1. Gold
Fontes mais fortes para validacao principal.

### A. Referencias cruzadas
Origem:
- dataset consolidado de cross-references
- integrado ao V3 por `scripts/integrate_crossrefs_v3.py`

Forca:
- alta independencia em relacao ao motor de embeddings
- boa para medir aderencia intertextual
- boa para queries tematicas e relacionais

Limitacoes:
- cross-reference nao equivale sempre a tema
- pode favorecer estruturas tradicionais ja canonizadas
- pode subrepresentar conexoes semanticas novas

Uso recomendado:
- concordancia com resultados recuperados
- cobertura de links tradicionais
- validacao principal em `Phase 2` e `Phase 3`

### B. CCEL Precision
Origem:
- corpus de comentarios estruturados em `E:/comentarios_pesquisa_ceel`
- subconjunto `PRECISION`

Forca:
- forte ancoragem exegética
- filtragem rigorosa
- util como referencia teologica de alta confianca

Limitacoes:
- cobertura desigual por livros, autores e obras
- nem toda consulta moderna tera cobertura equivalente

Uso recomendado:
- gold set auxiliar forte
- validacao teologica
- estudos de caso de alta confianca

### C. Curadoria manual
Origem:
- selecao e revisao humana das queries e referencias centrais

Forca:
- maior controle sobre casos importantes
- excelente para queries emblematicas do TCC

Limitacoes:
- pequena escala
- exige disciplina para nao introduzir vies excessivos

Uso recomendado:
- queries nucleares
- desempate entre fontes
- refinement de `gold_references` e `relevance_judgments`

## 2. Silver
Fontes fortes, mas auxiliares.

### A. CCEL Coverage
Origem:
- mesmo corpus CCEL, subconjunto `COVERAGE`

Forca:
- maior cobertura
- bom para encontrar passagens plausiveis e ampliar recall

Limitacoes:
- menor rigor do que `PRECISION`
- maior heterogeneidade semantica

Uso recomendado:
- ampliar candidatos
- corroboracao secundaria
- analise de abrangencia semantica

### B. Definition refs
Origem:
- `definition_refs` extraidas das definicoes do V3

Forca:
- independentes da busca hibrida
- ligadas ao escopo enciclopedico do topico
- uteis para contexto e weak supervision

Limitacoes:
- nao foram criadas para avaliar ranking
- descrevem o topico, nao necessariamente os melhores versos para retrieval

Uso recomendado:
- validacao fraca
- apoio a curadoria
- reforco em estudos de caso

### C. Temas promovidos e topicos enriquecidos
Origem:
- pipeline interno do projeto

Forca:
- alta aderencia ao dominio do sistema
- boa fonte para consistencia interna

Limitacoes:
- proximos demais do proprio metodo
- nao devem ser a unica verdade de referencia

Uso recomendado:
- consistencia interna
- analise de estabilidade
- apoio a `Phase 2`

## 3. Signal
Fontes que ajudam a explicar, ordenar ou gerar candidatos, mas nao devem ser tratadas como gold principal.

### A. Embeddings
Inclui:
- `small`
- `large`
- `unified/merge`
- embeddings de livros

Uso correto:
- retrieval
- reranking
- score semantico
- analise de alinhamento
- descoberta de candidatos em corpora grandes
- priorizacao do que merece revisao manual

Uso incorreto:
- gerar a propria verdade principal contra a qual o sistema sera avaliado

Risco metodologico:
- circularidade

### B. Gazetteers, entidades e simbolos
Forca:
- ajudam a interpretar consultas
- ajudam a explicar resultados

Limitacoes:
- ainda nao sao base primaria de validacao do ranking

Uso recomendado:
- classificacao de query
- explicabilidade
- auditoria semantica

## Distincao entre corpus bruto, corpus derivado e corpus de validacao
Nem toda fonte textual do projeto tem o mesmo papel metodologico.

Separacao recomendada:

### Corpus bruto de origem
Exemplos:
- Biblia em versiculos
- paragrafos teologicos de colecoes maiores
- livros completos e corpus amplos

Papel:
- materia-prima
- base de retrieval
- origem historica do dado

### Corpus derivado e estruturado
Exemplos:
- comentarios estruturados do TCC
- topicos enriquecidos
- definicoes e `definition_refs`
- temas promovidos

Papel:
- candidate generation
- contexto interpretativo
- validacao auxiliar
- estudos de caso

### Corpus de validacao mais forte
Exemplos:
- crossrefs manuais
- comentarios de alta precisao
- curadoria manual

Papel:
- referencia para avaliacao formal

## Riscos metodologicos
Quando varias camadas compartilham os mesmos versiculos, referencias e conceitos, surgem riscos que precisam ser controlados.

### 1. Vazamento semantico
Descricao:
- uma camada derivada pode repetir ou reformular o mesmo conteudo biblico em outra representacao

Exemplo:
- um topico carrega `definition_refs`
- um comentario menciona explicitamente o mesmo versiculo
- a busca recupera esse versiculo e ele parece confirmado por varias fontes

Risco:
- uma mesma evidencia parecer varias evidencias independentes

### 2. Circularidade
Descricao:
- o metodo e avaliado com sinais fortemente produzidos ou influenciados pelo proprio ecossistema do metodo

Exemplo:
- embeddings ajudam a gerar candidatos
- topicos, definicoes e comentarios derivam do mesmo universo de referencias
- essas mesmas camadas depois sao usadas como prova final

Risco:
- inflar artificialmente a qualidade percebida do sistema

### 3. Overlap entre camadas
Descricao:
- a mesma informacao pode existir ao mesmo tempo em:
  - versiculo
  - topico
  - definicao
  - comentario
  - embedding

Risco:
- contar corroboracoes internas como se fossem corroboracoes externas

## Regras para evitar contaminacao entre camadas
1. nao usar embeddings como unica verdade principal
2. nao tratar topicos, definicoes e comentarios derivados como se fossem todos independentes entre si
3. priorizar fontes mais externas e mais manuais como `gold`
4. tratar fontes derivadas como `silver` ou `signal`, salvo quando houver ancoragem forte e independente
5. registrar, query por query, de onde veio cada referencia de validacao

## Regra de ouro
Quanto mais uma fonte foi derivada do proprio corpus biblico e do proprio pipeline do projeto, menor deve ser seu peso como `verdade independente`.

## Como cada fonte entra nas fases

## Workflow de construcao da verdade de referencia
Este e o fluxo recomendado para montar a fonte de verdade sem circularidade:

1. usar embeddings e busca hibrida para levantar candidatos
2. cruzar esses candidatos com:
   - crossrefs
   - CCEL Precision
   - CCEL Coverage
   - definition_refs
   - curadoria manual
3. classificar cada candidato como:
   - `gold_core`
   - `gold_support`
   - `silver_support`
   - `exploratory_only`
4. usar apenas `gold` e parte de `silver` como base de avaliacao formal

Leitura correta do processo:
- embeddings ajudam a achar onde olhar
- as fontes independentes decidem o que vira evidencia

## Como lidar com embeddings de multiplas camadas
Se o projeto possui embeddings de:
- Biblia
- comentarios
- topicos
- definicoes
- livros

entao a regra recomendada e:

1. usar embeddings para discovery e pesquisa exploratoria
2. evitar usar a mesma familia de embeddings como prova final contra si propria
3. separar no experimento:
   - `retrieval corpus`
   - `validation corpus`
4. quando houver overlap entre duas fontes, marcar explicitamente que a corroboracao nao e totalmente independente

## Phase 2 - Theme Promotion
Pergunta:
- a configuracao de retrieval gera evidencia suficiente para promover o tema?

Fontes principais:
- crossrefs
- CCEL Precision
- curadoria manual

Fontes auxiliares:
- CCEL Coverage
- definition_refs
- temas relacionados do V3

Sinais:
- embeddings
- scores de cobertura
- quality score

## Phase 3 - Verse Linking
Pergunta:
- a configuracao de retrieval entrega o melhor ranking final para representar o tema?

Fontes principais:
- crossrefs
- CCEL Precision
- curadoria manual

Fontes auxiliares:
- CCEL Coverage
- definition_refs
- topicos e comentarios correlatos

Sinais:
- embeddings
- score semantico
- reranking
- diversidade

## Matriz de confianca
| Fonte | Categoria | Independencia | Cobertura | Uso principal |
|-------|-----------|---------------|-----------|---------------|
| Crossrefs | Gold | Alta | Alta | validacao estrutural |
| CCEL Precision | Gold | Alta | Media | validacao teologica forte |
| Curadoria manual | Gold | Alta | Baixa | queries nucleares |
| CCEL Coverage | Silver | Media | Alta | recall e corroboracao |
| Definition refs | Silver | Media | Media | contexto e weak supervision |
| Temas/topicos internos | Silver | Baixa | Alta | consistencia interna |
| Embeddings | Signal | Baixa | Alta | retrieval e score |
| Gazetteers/simbolos | Signal | Media | Media | interpretacao |

## Regras de decisao
Para chamar uma evidencia de `forte`, priorizar:
1. concordancia entre crossrefs e CCEL Precision
2. concordancia entre crossrefs e curadoria manual
3. concordancia entre mais de uma fonte independente

Para chamar uma evidencia de `plausivel`, aceitar:
- uma fonte gold + uma silver
- ou duas silvers convergentes

Para chamar uma evidencia de `exploratoria`, aceitar:
- apenas sinais semanticos
- ou apenas uma silver sem corroboracao

## Como procurar em corpora grandes sem perder rigor
Em bases muito grandes, como comentarios, crossrefs e corpus biblico completo, a busca manual pura e inviavel.
Por isso, a estrategia recomendada e:

1. usar embedding ou busca hibrida para recuperar um conjunto de candidatos
2. limitar a inspecao humana aos melhores candidatos
3. confirmar esses candidatos com fontes independentes
4. transformar apenas os itens corroborados em referencia oficial

Isso evita dois extremos ruins:
- depender so de leitura manual, que nao escala
- depender so de embedding, que gera circularidade

## Formula pratica para o TCC
Na redacao metodologica, a formulacao recomendada e:
- embeddings foram usados para descoberta, busca exploratoria e priorizacao de candidatos
- camadas derivadas do corpus biblico foram usadas como apoio contextual e validacao auxiliar
- a validacao principal priorizou fontes com maior independencia estrutural, como referencias cruzadas, comentarios de alta precisao e curadoria manual

## Regras para o query set
Cada query deve ter:
- `gold_references`: referencias centrais de maior confianca
- `relevance_judgments`: pesos de relevancia
- `validation_sources`: quais fontes sustentam a query

Categorias sugeridas:
- `gold_core`
- `gold_support`
- `silver_support`
- `exploratory_only`

## Primeiras queries prioritarias
Estas queries sao boas para abrir a trilha de validacao:

### q003 - amor ao proximo
Boa porque:
- possui base biblica clara
- tem forte estrutura em crossrefs
- deve aparecer em comentarios e topicos

### q004 - agua viva
Boa porque:
- testa semantica e metafora
- pode distinguir melhor configuracoes com expansao e rerank

### q006 - Abraao
Boa porque:
- une entidade, topico, definicoes e referencias centrais
- permite comparar comportamento lexical versus semantico

### q010 - perdao
Boa porque:
- e conceitual
- permite testar recall de sinonimos
- deve conversar com topicos e comentarios

## Como isso entra na escrita do TCC
Na metodologia, a redacao ideal e:
- o sistema foi avaliado contra uma fonte de verdade em camadas
- fontes independentes, como referencias cruzadas e comentarios de alta precisao, foram tratadas como gold
- fontes enciclopedicas e de cobertura ampla foram tratadas como silver
- embeddings foram tratados como mecanismo de retrieval e nao como verdade principal
- embeddings tambem foram usados para descoberta de candidatos e priorizacao de revisao em corpora extensos

## Proximo passo operacional
1. escolher 3 queries do piloto
2. revisar suas `gold_references` contra crossrefs e CCEL Precision
3. marcar, query por query, quais referencias sao `gold_core` e `gold_support`
4. so depois rodar a primeira bateria oficial de benchmark
