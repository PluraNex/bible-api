---
id: T-C01
title: "[data] Extrair comentários para JSON e ajustar consistência de documentos — Sem salvar no banco de dados"
status: completed
created: 2025-09-10
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/feat"]
priority: high
effort: L
risk: low
depends_on: []
related: []
epic: "Fase 3: Scraping Avançado de Comentários"
branch: "feat/extract-commentaries-to-json"
pr: ""
github_issue: ""
due: null
---

## Contexto

O projeto Bible API possui um sistema robusto de scraping de comentários dos Church Fathers através do Firecrawl MCP, mas atualmente os dados são salvos diretamente no banco de dados. Para fins de processamento em lote e análise externa, é necessário extrair esses comentários em formato JSON estruturado sem importá-los para o banco de dados.

Este trabalho se baseia nos comandos já existentes:
- `demo_firecrawl_scraping` - Demonstração funcional de scraping
- `catena_firecrawl_mcp` - Implementação completa com Firecrawl MCP

### Documentação de Referência
O agente deve consultar os seguintes documentos para entender o contexto completo:
- `FIRECRAWL_MCP_GUIDE.md` - Guia de integração do Firecrawl MCP
- `FIRECRAWL_WORKFLOW_GUIDE.md` - Workflow completo do Firecrawl
- `SCRAPING_CHECKLIST.md` - Checklist de versículos para scraping
- `firecrawl_sample_lk1_1.json` - Exemplo de JSON de saída esperado
- `test_single_commentary.json` - Outro exemplo de JSON de saída

### Comandos Disponíveis para Análise
O agente deve analisar os seguintes comandos existentes:
- `data/management/commands/demo_firecrawl_scraping.py`
- `data/management/commands/catena_firecrawl_mcp.py`
- `data/management/commands/firecrawl_book_scraper.py` (pode ter problemas de sintaxe que precisam ser corrigidos)
- `data/management/commands/import_firecrawl_json.py`

### Valor para o sistema
- Permite processamento em lote de comentários sem impactar o banco de dados
- Facilita análise externa e migração de dados
- Mantém a estrutura de dados já validada do projeto

### Notas Importantes para o Agente
1. **Verificação de Consistência**: O agente deve verificar a consistência entre os documentos existentes e ajustar quaisquer divergências antes de implementar
2. **Correção de Problemas**: Alguns comandos podem ter problemas de sintaxe ou erros que precisam ser corrigidos (ex: `firecrawl_book_scraper.py`)
3. **Fluxo Linear**: Certifique-se de que todos os documentos e comandos funcionem de forma linear e coerente antes de implementar novas funcionalidades
4. **Preservação de Estrutura**: Mantenha a estrutura de dados existente conforme demonstrada nos arquivos JSON de exemplo

## Objetivo e Critérios de Aceite
- [ ] CA1 — Modificar comando `catena_firecrawl_mcp` para suportar saída JSON
- [ ] CA2 — Adicionar opções `--output-json` e `--output-dir`
- [ ] CA3 — Salvar comentários em arquivos JSON estruturados
- [ ] CA4 — Manter validação de qualidade dos comentários existente
- [ ] CA5 — Não tentar conexão com banco de dados quando em modo JSON
- [ ] CA6 — Verificar e ajustar consistência entre documentos existentes de firecrawl
- [ ] CA7 — Corrigir possíveis problemas de sintaxe em comandos existentes
- [ ] CA8 — Garantir que todos os comandos funcionem de forma linear e coerente

## Escopo / Fora do Escopo
- Inclui: Modificação do comando `catena_firecrawl_mcp`
- Inclui: Criação de método para salvar em JSON
- Inclui: Adição de novas opções de linha de comando
- Inclui: Verificação e correção de consistência entre documentos existentes
- Inclui: Ajuste de possíveis problemas de sintaxe em comandos existentes
- Não inclui: Alterações no modelo de dados do banco
- Não inclui: Criação de novos comandos de scraping

## Impacto Técnico
**Contrato (OpenAPI)**: não muda
**DB/Migrations**: não afeta
**Throttle/Cache**: não afeta
**Performance**: mínimo impacto, apenas IO de arquivos
**Segurança**: não afeta

### Impacto nos Documentos Existentes
- Verificação e ajuste de consistência entre documentos de firecrawl
- Potenciais correções de problemas de sintaxe em comandos existentes
- Atualização da documentação para refletir mudanças

## Plano de Testes
**API**: Testar comando com diferentes opções
- `python manage.py catena_firecrawl_mcp --verse lk/1/1 --output-json --verbose`
- `python manage.py catena_firecrawl_mcp --chapter lk/1 --output-json --verbose`

**Dados**: Verificar estrutura dos arquivos JSON gerados
- Estrutura consistente com padrão definido
- Todos os campos necessários presentes
- Validação de qualidade dos comentários mantida

**Consistência**: Verificar que todos os documentos e comandos funcionam corretamente
- Todos os comandos de scraping existentes devem continuar funcionando
- Documentos de referência devem estar consistentes entre si
- Estrutura dos arquivos JSON gerados deve corresponder aos exemplos existentes

## Observabilidade
- Logs de salvamento em JSON
- Contagem de comentários extraídos
- Erros de parsing ou validação
- Logs de verificação de consistência de documentos

## Rollout & Rollback
- Plano de ativação: Modificação do comando existente
- Critérios de sucesso: Arquivos JSON gerados corretamente e todos os comandos funcionando
- Estratégia de reversão: Reverter modificações no comando e restaurar consistência de documentos

## Implementação Detalhada

### 0. Verificação e Ajuste de Consistência (Pré-requisito)
Antes de implementar a nova funcionalidade, o agente deve:
1. Verificar a consistência entre todos os documentos de firecrawl mencionados
2. Identificar e corrigir quaisquer divergências ou problemas de sintaxe
3. Garantir que todos os comandos existentes funcionem corretamente
4. Validar a estrutura dos arquivos JSON de exemplo existentes

### 1. Adicionar Opções de Linha de Comando

### 1. Adicionar Opções de Linha de Comando
No método `add_arguments` do comando `catena_firecrawl_mcp`:
```python
parser.add_argument(
    '--output-json',
    action='store_true',
    help='Save extracted data to JSON files instead of database'
)
parser.add_argument(
    '--output-dir',
    type=str,
    default='data/scraped/json',
    help='Directory to save JSON files'
)
```

### 2. Criar Método para Salvar em JSON
```python
def save_commentaries_to_json(self, commentaries: List[ParsedCommentary],
                             book: str, chapter: int, verse: int):
    """Save commentaries to JSON file"""
    if not commentaries:
        return

    # Create output directory
    output_dir = Path(self.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare data structure
    data = {
        'verse_reference': f"{book} {chapter}:{verse}",
        'verse_text': f"Texto do versículo {book} {chapter}:{verse}",
        'commentaries': [
            {
                'author': comm.author,
                'period': comm.period,
                'content': comm.content,
                'quality_score': comm.quality_score,
                'is_valid': comm.is_valid()
            }
            for comm in commentaries
        ]
    }

    # Save to JSON file
    filename = f"{book.lower()}_{chapter}_{verse}.json"
    filepath = output_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    if self.verbose:
        self.stdout.write(f"   💾 Saved JSON: {filename}")
```

### 3. Atualizar Método de Salvamento
No método `save_commentaries_to_db`, adicionar condição para usar JSON:
```python
def save_commentaries_to_db(self, commentaries: List[ParsedCommentary],
                           book: str, chapter: int, verse: int):
    """Save commentaries to database or JSON"""
    if getattr(self, 'output_json', False):
        self.save_commentaries_to_json(commentaries, book, chapter, verse)
        return

    # ... restante do código original para salvar no DB
```

### 4. Estrutura do JSON de Saída
Seguir a estrutura demonstrada nos arquivos de exemplo existentes:

`firecrawl_sample_lk1_1.json`:
```json
{
  "verse_reference": "Luke 1:1",
  "verse_text": "Since many have taken in hand to set forth in order a declaration of those things which are most surely believed among us,",
  "commentaries": [
    {
      "author": "Ambrose",
      "period": "AD 340-397",
      "content": "Highlights the variety of gospel attempts and the importance of divine inspiration. Notes that many tried to write gospels, but not all were successful.",
      "theological_themes": ["Divine inspiration", "Gospel authenticity"],
      "cross_references": []
    }
    // ... mais comentários
  ]
}
```

A estrutura deve incluir campos adicionais como `theological_themes` e `cross_references` que são parte do modelo existente.

### 5. Estrutura de Diretórios de Saída
```
data/
└── scraped/
    └── json/
        ├── luke_1_1.json
        ├── luke_1_2.json
        ├── luke_1_3.json
        └── ...
```

## Checklist Operacional (Autor)
- [ ] OpenAPI gerado/commitado em `docs/` (se houve mudança)
- [ ] `make fmt lint test` ok local
- [ ] CI verde (lint, migrations-check, tests, schema-diff)
- [ ] PR descreve impacto e rollback
- [ ] Todos os comandos de scraping existentes funcionam corretamente após as modificações
- [ ] Documentação atualizada e consistente

## Checklist Operacional (Revisor)
- [ ] Contrato estável ou depreciação formal
- [ ] Testes suficientes (felizes + erros + auth + throttle + paginação/ordenação/filtros)
- [ ] Sem N+1; p95 dentro do orçamento
- [ ] Migrations pequenas e reversíveis
- [ ] Segurança: sem PII em logs; escopos e rate adequados
- [ ] Cache/invalidação documentados
- [ ] Todos os documentos de referência estão consistentes
- [ ] Comandos existentes continuam funcionando após as modificações
