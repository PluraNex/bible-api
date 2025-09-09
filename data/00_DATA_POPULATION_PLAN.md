# Plano de Ação: População da Base de Dados da API Bíblica

**Status:** Definido
**Versão:** 1.0
**Data:** 2025-09-07

## 1. Objetivo

Este documento descreve o plano estratégico e a sequência de execução para popular a base de dados da API Bíblica de forma completa, íntegra e eficiente. O objetivo é construir uma base de dados definitiva, aproveitando múltiplas fontes de dados e garantindo a consistência através de uma ordem de execução lógica.

## 2. Pré-requisito Crítico: Alinhamento dos Modelos

Antes da execução de qualquer script de população, é **mandatório** que todos os modelos do Django (`Language`, `Testament`, `CanonicalBook`, `BookName`, `Version`, `Verse`, `CrossReference`) estejam completamente refatorados para o padrão definido no blueprint da arquitetura (`docs/architecture/BIBLE_API_BASE_PROJECT.md`). As migrações correspondentes devem ser geradas e aplicadas.

---

## 3. Fases de Execução

O plano é dividido em três fases distintas, que devem ser executadas na ordem apresentada para garantir a integridade referencial dos dados.

### Fase 1: A Fundação (Metadados Universais)

**Objetivo:** Criar a estrutura universal e agnóstica a idiomas da Bíblia. Ao final desta fase, teremos o "esqueleto" completo da Bíblia, mas sem nenhum texto de versículo.

*   **Script:** `python manage.py seed_metadata`
*   **Propósito:** Popular as tabelas de base que raramente mudam e servem como alicerce para todos os outros dados.
*   **Lógica:**
    1.  **Popular `Language`:** Cria os registros para os idiomas que serão suportados (ex: 'pt-BR', 'en-US', 'la').
    2.  **Popular `Testament`:** Cria os registros para 'Antigo Testamento', 'Novo Testamento' e 'Apócrifo/Deuterocanônico'.
    3.  **Popular `CanonicalBook`:** Cria os registros para os 66 livros canônicos e também para os livros deuterocanônicos, definindo o testamento e a flag `is_deuterocanonical` para cada um.
    4.  **Popular `BookName`:** Para cada `CanonicalBook`, cria seus respectivos nomes e abreviações em múltiplos idiomas (Português, Inglês, etc.), garantindo a correta associação entre o conceito do livro e suas traduções.

### Fase 2: O Conteúdo (Textos das Versões)

**Objetivo:** Popular a tabela `Verse` com o texto de cada tradução da Bíblia, conectando-os à estrutura de metadados criada na Fase 1.

*   **Script 1:** `python manage.py populate_pt_versions`
    *   **Fonte:** Diretório `inst/json/`.
    *   **Propósito:** Processar todas as versões da Bíblia em português. O script cria os registros `Version` associados ao idioma 'pt-BR' e popula os `Verse` correspondentes.

*   **Script 2:** `python manage.py populate_foreign_versions`
    *   **Fonte:** Diretório `bible_databases-2024/`.
    *   **Propósito:** Processar versões em outros idiomas (primariamente Inglês). A lógica é similar, mas adaptada aos formatos de dados encontrados neste diretório e associada aos idiomas corretos.

*   **Script 3:** `python manage.py populate_deuterocanon`
    *   **Fonte:** Diretório `bible_databases_deuterocanonical/`.
    *   **Propósito:** Processar os livros deuterocanônicos. O script cria uma `Version` específica para este conjunto (ex: 'EN_APOCRYPHA') e popula os versículos dos livros marcados como `is_deuterocanonical=True`.

### Fase 3: As Conexões (Referências Cruzadas)

**Objetivo:** Popular a tabela `CrossReference` com os dados que ligam os versículos de forma canônica e agnóstica à versão.

*   **Script:** `python manage.py populate_cross_references`
*   **Fonte:** Arquivo `bible_databases-2024/cross_references.txt`.
*   **Propósito:** Ler o arquivo de referências, processar as strings de versículos (ex: `Gen.1.1`) para encontrar os `CanonicalBook` correspondentes, e criar os registros `CrossReference`.
*   **Nota:** Este script roda por último, pois depende que todos os `CanonicalBook` já existam na base.

---

## 4. Ordem de Execução Final

Para popular a base de dados do zero, os comandos de gerenciamento devem ser executados na seguinte ordem estrita:

1.  `python manage.py seed_metadata`
2.  `python manage.py populate_pt_versions`
3.  `python manage.py populate_foreign_versions`
4.  `python manage.py populate_deuterocanon`
5.  `python manage.py populate_cross_references`

A execução nesta sequência garante a integridade referencial e a construção correta e completa da base de dados.
