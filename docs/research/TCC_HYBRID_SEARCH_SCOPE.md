# Recorte Oficial do TCC

## Titulo de trabalho
Impacto de estrategias de recuperacao hibrida na descoberta e vinculacao semantica de conteudo biblico.

## Problema
Sistemas de busca biblica baseados apenas em correspondencia lexical recuperam bem termos exatos, mas falham quando a descoberta depende de sinonimia, tematizacao ou conexoes semanticas indiretas. Sistemas apenas semanticos melhoram cobertura conceitual, mas podem perder precisao textual e interpretabilidade. O problema central deste trabalho e medir como diferentes configuracoes de recuperacao hibrida alteram a qualidade da descoberta e da vinculacao semantica biblica.

## Pergunta de pesquisa
Como diferentes estrategias de busca hibrida, combinando componentes lexicais e semanticos, impactam a qualidade da recuperacao de versiculos e da vinculacao de temas biblicos em um corpus enriquecido por referencias cruzadas, comentarios e topicos?

## Hipotese
Uma estrategia hibrida com combinacao controlada de BM25, embeddings semanticos, expansao de consulta, reranking e diversificacao produz melhor equilibrio entre precisao, cobertura e utilidade interpretativa do que abordagens puramente lexicais ou puramente semanticas.

## Objetivo geral
Comparar configuracoes de recuperacao hibrida para identificar o setup que oferece a melhor relacao entre qualidade de ranking, diversidade, latencia e concordancia com fontes biblicas auxiliares.

## Objetivos especificos
- Medir o efeito de `alpha` na fusao lexical-semantica.
- Medir o efeito de expansao de consulta.
- Medir o efeito de reranking de segundo estagio.
- Medir o efeito de `mmr_lambda` sobre relevancia e diversidade.
- Comparar `embedding_source=verse` e `embedding_source=unified`.
- Verificar concordancia dos resultados com referencias cruzadas, comentarios e temas promovidos.

## Variavel independente principal
Configuracao da busca hibrida, definida por `alpha`, `expand`, `rerank`, `mmr_lambda` e `embedding_source`.

## Variaveis dependentes
- Precision@K
- Recall@K
- MAP
- NDCG
- Latencia
- Diversidade dos resultados
- Taxa de concordancia com crossrefs
- Taxa de concordancia com comentarios
- Taxa de descobertas novas plausiveis

## Fontes de validacao
- Referencias cruzadas
- Comentarios e CCEL
- Temas promovidos e topicos enriquecidos
- Casos manuais curados

## Delimitacao
O foco experimental primario sera busca hibrida, busca semantica e vinculacao de temas. Gazetteers, simbolos e entidades permanecem como eixos auxiliares de interpretacao e auditoria, nao como frentes paralelas do TCC.

## O que fica fora desta sprint
- Interface
- Expansao de todos os dominios ao mesmo tempo
- Tratamento do corpus parcial como se fosse corpus final
- Novas features sem evidencia experimental
