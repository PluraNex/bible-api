# Bible API Data Directory

Este diretório centraliza todos os recursos de dados, comandos e documentação relacionados ao povoamento e gerenciamento de dados bíblicos.

## Structure

```
data/
├── datasets/              # Datasets bíblicos (excluído do Git)
│   ├── bibles-2024/      # Versões bíblicas em inglês
│   │   ├── json/         # Arquivos JSON das versões (KJV, ASV, etc)
│   │   └── cross_references.txt # Referências cruzadas
│   ├── deuterocanonical/ # Livros deuterocanônicos
│   │   └── sources/en/   # Fontes em inglês
│   └── inst/            # Versões em português
│       └── json/        # ARA, NVI, etc.
├── management/           # Django management commands
│   └── commands/        # Scripts de povoamento de dados
└── docs/               # Documentação específica de dados
```

## Management Commands

Os comandos de gerenciamento foram movidos para `data/management/commands/` e incluem:

### Comandos de Povoamento (Ordem recomendada):

1. **`seed_01_metadata.py`** - 🏗️ Semeia estrutura básica (idiomas, testamentos, livros canônicos)
2. **`populate_bible_data.py`** - 📖 Popula versões bíblicas em português (ARA, NVI, etc.)
3. **`populate_foreign_versions.py`** - 🌍 Popula versões estrangeiras (KJV, ASV, BBE, WEB, YLT)
4. **`populate_deuterocanon.py`** - 📜 Popula livros deuterocanônicos/apócrifos
5. **`populate_cross_references.py`** - 🔗 Popula referências cruzadas OpenBible.info

### Comandos Utilitários:

- **`clear_crossrefs.py`** - 🧹 Limpa referências cruzadas de forma segura

## Usage

Para executar os comandos, use o Django management:

```bash
# Via Docker (recomendado) - Sequência completa:
docker-compose exec web python manage.py seed_01_metadata
docker-compose exec web python manage.py populate_bible_data --bible-version ARA
docker-compose exec web python manage.py populate_foreign_versions --version KJV
docker-compose exec web python manage.py populate_deuterocanon
docker-compose exec web python manage.py populate_cross_references --min-votes 3

# Comandos individuais com opções:
docker-compose exec web python manage.py populate_bible_data --data-dir data/datasets/inst/json
docker-compose exec web python manage.py populate_foreign_versions --dry-run
docker-compose exec web python manage.py clear_crossrefs
```

## Git Configuration

- `data/datasets/` está excluído do controle de versão (.gitignore)
- `data/management/` e `data/docs/` são incluídos no Git
- Coverage exclui todo o diretório `data/` da análise

## Data Sources

- **Bíblias em português**: arquivos JSON com estrutura hierárquica
- **Bíblias estrangeiras**: formato de resultset com mapeamento de livros
- **Deuterocanônicos**: estrutura JSON com capítulos e versículos
- **Referências cruzadas**: arquivo texto com votes da OpenBible.info
