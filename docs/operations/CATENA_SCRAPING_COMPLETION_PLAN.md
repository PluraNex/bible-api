# Catena Scraping Completion Plan

## Objetivo
Completar o scraping do corpus Catena de forma controlada, documentando:
- cobertura real atual
- livros faltantes ou praticamente vazios
- capacidades atuais do scraper
- ordem recomendada de execucao

## Corpus principal
Fonte bruta principal identificada:
- `C:/Users/Iury Coelho/projetos/bible-api-old/data/scraped/commentaries/catena_bible`

Espelho operacional do TCC:
- `C:/Users/Iury Coelho/Desktop/TCC/Datasets/commentaries/01_original_commentaries`

## Diagnostico resumido
O corpus nao e apenas NT.
Existe cobertura substancial em partes do OT e do NT, mas a distribuicao e muito desigual.

## Cobertura atual observada

## Novo Testamento
Livros com cobertura relevante:
- `acts`: 1007
- `john`: 879
- `luke`: 1151
- `mark`: 678
- `matthew`: 1071
- `romans`: 433
- `1corinthians`: 437
- `2corinthians`: 198
- `galatians`: 149
- `ephesians`: 155
- `philippians`: 104
- `colossians`: 95
- `hebrews`: 303
- `james`: 108
- `1john`: 105
- `jude`: 25
- `2john`: 13
- `3john`: 14

Livros muito incompletos ou vazios:
- `revelation`: 0
- `1peter`: 0
- `2peter`: 0
- `1thes`: 0
- `1thessalonians`: 0
- `2thes`: 0
- `2thessalonians`: 0
- `1timothy`: 0
- `2timothy`: 0
- `titus`: 0

## Antigo Testamento
Livros com cobertura relevante:
- `gn`: 1533
- `ex`: 1213
- `ps`: 2461
- `prv`: 915
- `jb`: 1070
- `is`: 1290
- `jer`: 1364
- `ez`: 1273
- `dn`: 463

Livros quase vazios:
- `lv`: 0 ou praticamente nulo no estado atual

Grupos inteiros ainda zerados:
- `historical_books`
- `minor_prophets`
- `deuterocanonical_historical`
- `other_writings`

Livros importantes ainda zerados:
- `dt`
- `nm`
- `ru`
- `jo` (Joshua)
- `jgs`
- `1sm`
- `2sm`
- `1kgs`
- `2kgs`
- `1chr`
- `2chr`
- `ezr`
- `neh`
- `hos`
- `jl`
- `am`
- `ob`
- `jon`
- `mi`
- `na`
- `hb`
- `zep`
- `hg`
- `zec`
- `mal`
- `eccl`
- `sg`

## Estado do scraper
Comandos principais:
- `bible/management/commands/scrape_catena_bible.py`
- `bible/management/commands/scrape_catena_enhanced.py`

## Ajustes ja aplicados
Os comandos agora suportam:
- `all-nt`
- `all-ot`
- `all-bible`
- grupos:
  - `gospels`
  - `pauline`
  - `general`
  - `pentateuch`
  - `historical`
  - `deuterocanonical`
  - `wisdom`
  - `major-prophets`
  - `minor-prophets`

Tambem foi corrigido:
- roteamento por testamento
- normalizacao de abreviacoes
- argumentos operacionais no comando `enhanced`

## Limitacao atual
Os scrapers continuam dependendo de:
- ambiente Django funcional
- `requests`
- `beautifulsoup4`
- opcionalmente `firecrawl-py`

Mesmo com Firecrawl indisponivel, o scraper possui fallback HTTP/BeautifulSoup.

## O que sabemos sobre a origem do corpus
O corpus atual nao foi produzido apenas pela versao mais recente do scraper.

Motivo:
- os comandos atuais sao claramente `NT-first`
- mas o corpus ja contem varios livros do OT com volume alto

Interpretacao mais provavel:
- parte do OT foi obtida em rodadas anteriores ou em versoes anteriores do scraper
- a versao atual do comando precisa ser usada para completar e padronizar os faltantes

## Relacao com as cross-references
As cross-references nao foram geradas a partir dos topicos.

Fonte:
- `OpenBible`
- `SoulLiberty`

Fluxo correto:
- crossrefs sao construidas independentemente
- depois sao integradas ao V3

Consequencia metodologica:
- crossrefs continuam sendo fonte mais independente do que topicos/definicoes

## Estrategia recomendada para concluir o scraping
Nao rodar a Biblia inteira de uma vez.
Executar em blocos.

### Bloco 1 - Finalizar NT fraco
Prioridade:
- `revelation`
- `1peter`
- `2peter`
- `1thessalonians`
- `2thessalonians`
- `1timothy`
- `2timothy`
- `titus`

Exemplo:
```bash
python manage.py scrape_catena_enhanced --books "revelation,1peter,2peter,1thessalonians,2thessalonians,1timothy,2timothy,titus" --parallel-books 1 --conservative-mode --verbose --resume
```

### Bloco 2 - Fechar Pentateuco
Prioridade:
- `dt`
- `nm`
- revisar `lv`

Exemplo:
```bash
python manage.py scrape_catena_enhanced --books "pentateuch" --parallel-books 1 --conservative-mode --verbose --resume
```

### Bloco 3 - Fechar Historicos
Exemplo:
```bash
python manage.py scrape_catena_enhanced --books "historical" --parallel-books 1 --conservative-mode --verbose --resume
```

### Bloco 4 - Fechar Profetas Menores
Exemplo:
```bash
python manage.py scrape_catena_enhanced --books "minor-prophets" --parallel-books 1 --conservative-mode --verbose --resume
```

### Bloco 5 - Revisar Sabedoria e Deuterocanonicos
Exemplo:
```bash
python manage.py scrape_catena_enhanced --books "wisdom,deuterocanonical" --parallel-books 1 --conservative-mode --verbose --resume
```

## Criterios de pronto
Considerar uma rodada satisfatoria quando:
- o livro deixa de estar zerado
- o checkpoint e gerado sem falhas criticas
- os arquivos em `verses/` crescem de forma coerente
- o livro pode ser refletido depois no espelho do TCC

## Regras de seguranca operacional
1. rodar com `--resume`
2. usar `--parallel-books 1` no OT inicialmente
3. manter `--conservative-mode`
4. validar crescimento dos arquivos apos cada bloco
5. so depois considerar paralelismo maior

## O que fazer depois de concluir os blocos
1. sincronizar o corpus bruto atualizado com o espelho do TCC
2. recalcular cobertura por livro
3. atualizar o inventario de datasets
4. reavaliar em quais livros o corpus patrístico pode sustentar o gold set
