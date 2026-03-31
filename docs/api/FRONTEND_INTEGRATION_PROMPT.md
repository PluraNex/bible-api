# Task: Integrar Bible API no Word-Sanctuary Frontend

## Contexto

A Bible API (localhost:8000) tem 4 novos domínios prontos para integração no frontend React:

| Domínio | Dados | Endpoint chave |
|---------|-------|----------------|
| **People** | 242 pessoas (hub identidade) | `GET /people/{slug}/` |
| **Commentary Authors** | 242 autores com avatar, hermenêutica, ortodoxia | `GET /comments/authors/` |
| **Commentary Entries** | 38.101 comentários patrísticos | `GET /comments/entries/?book__osis_code=X&chapter=Y&verse=Z` |
| **Biblical Images** | 16.914 pinturas + 9.649 verse links | `GET /images/by-verse/{book}/{ch}/{vs}/` |
| **Themes** | 50 temas com 1.000 verse links | `GET /themes/{id}/detail/` |
| **Artists** | 1.892 artistas (Doré: 301, Rubens: 235) | `GET /images/artists/{slug}/` |

## LEIA ANTES DE COMEÇAR

A documentação completa da API está em:
```
C:\Users\Iury Coelho\Desktop\bible-api\docs\api\ENDPOINTS_GUIDE.md
```

**Leia esse arquivo INTEIRO.** Ele contém:
- Todos os endpoints com exemplos de request/response reais
- Interfaces TypeScript prontas para copiar
- Tabelas de filtros disponíveis
- Fluxos de uso (ArtsTab, galeria, perfil de autor)

## Stack do Frontend
- **Framework:** React 18 + TypeScript + Vite (porta 8080)
- **UI:** shadcn/ui (Radix) + Tailwind CSS
- **Data Fetching:** TanStack React Query v5
- **State:** Zustand
- **Routing:** React Router v6
- **Grafos:** XYFlow | **Charts:** Recharts
- **Ícones:** Lucide React

## Padrão existente a seguir

### API Client
`src/shared/api/clients/bibleApiClient.ts` — Singleton com fetch, auth via `Authorization: Api-Key {key}`

### Repository Pattern
`src/shared/api/repositories/` — Um por domínio:
- `VerseRepository.ts`, `BookRepository.ts`, `ThemeRepository.ts`, `CommentRepository.ts`, `SearchRepository.ts`

### Types
`src/shared/api/types/api.types.ts` — Interfaces TypeScript

### Design Rules (`src/shared/rules/product-principles.md`)
- Fonte Bible: Crimson Text (serif) | UI: Inter (sans)
- Cores via CSS tokens, nunca hardcoded
- Ícones: Lucide h-4 w-4
- Texto bíblico é protagonista visual
- Tom ecumênico (sem viés denominacional)

## O que implementar

### 1. Types (`src/shared/api/types/api.types.ts`)

Adicionar as interfaces do ENDPOINTS_GUIDE.md:
- `Person`, `PersonDetail`, `AuthorProfile`
- `Author`, `AuthorDetail`
- `CommentaryEntry` (atualizar o existente)
- `Artist`, `ArtistDetail`
- `BiblicalImage`, `BiblicalImageDetail`, `ImageTag`, `BiblicalImageByVerse`
- `Theme`, `ThemeDetail`, `ThemeVerse`

### 2. Repositories (`src/shared/api/repositories/`)

**PersonRepository.ts** (NOVO):
```typescript
getAll(params?: { person_type?: string; search?: string; page?: number })
getBySlug(slug: string): PersonDetail
```

**AuthorRepository.ts** (NOVO):
```typescript
getAll(params?: { author_type?: string; tradition?: string; search?: string; ... })
getById(id: number): AuthorDetail
getEntries(id: number): CommentaryEntry[]
```

**ImageRepository.ts** (NOVO):
```typescript
getAll(params?: { is_tagged?: boolean; artist?: string; style?: string; search?: string })
getById(id: number): BiblicalImageDetail
getByVerse(book: string, chapter: number, verse: number): BiblicalImageByVerse[]
search(query: string): BiblicalImage[]
```

**ArtistRepository.ts** (NOVO):
```typescript
getAll(params?: { search?: string })
getBySlug(slug: string): ArtistDetail
getImages(slug: string): BiblicalImage[]
```

**CommentRepository.ts** (ATUALIZAR):
```typescript
// Novo: GET /comments/entries/?book__osis_code={book}&chapter={ch}&verse={v}
getByVerse(book: string, chapter: number, verse: number): CommentaryEntry[]
getSources(): CommentarySource[]
```

**ThemeRepository.ts** (ATUALIZAR):
```typescript
getDetail(id: number): ThemeDetail  // GET /themes/{id}/detail/
search(query: string): Theme[]      // GET /themes/search/?q={query}
```

### 3. StudyRail — ArtsTab (PRIORIDADE MÁXIMA)

Arquivo: `src/features/bible-reading/ui/StudyRail/tabs/ArtsTab.tsx`

Atualmente é um **placeholder vazio**. Implementar:

```
Quando versículo selecionado:
  GET /images/by-verse/{book}/{ch}/{vs}/

Para cada imagem retornada:
  - Thumbnail/image_url em card
  - title (bold)
  - artist_name + completion_year
  - relevance_type como badge (primary|typological|allusion)
  - description (se existir, colapsível)

Se sem imagens: manter placeholder atual
Click na imagem → modal/drawer com detalhe (tag, characters, symbols, verse_links)
```

### 4. StudyRail — CommentsTab (ATUALIZAR)

Arquivo: `src/features/bible-reading/ui/StudyRail/tabs/CommentsTab.tsx`

```
GET /comments/entries/?book__osis_code={osis}&chapter={ch}&verse={v}

Para cada comentário:
  - author.portrait_image (avatar circular 32px)
  - author.short_name (negrito)
  - author.tradition (badge sutil, texto muted)
  - body_text (texto do comentário, colapsível se longo)
  - Link: author.person_slug → /people/{slug}/
```

### 5. Author Profile Page (NOVO)

Rota sugerida: `/author/:personSlug`

```
GET /people/{slug}/ → Person + author_profile
GET /comments/authors/{author_profile.id}/ → dados completos
GET /comments/authors/{id}/entries/ → comentários recentes

Mostrar:
  - Avatar grande (portrait_image)
  - Nome, lifespan (ex: "354-430"), tradition
  - Badges: Doctor of the Church, Saint, hermeneutic method, orthodoxy_status
  - recognized_by como badges (catholic, orthodox, protestant, etc.)
  - biography_summary
  - theological_contributions
  - major_works (lista)
  - Link Wikipedia (externo)
  - Lista de comentários recentes
```

### 6. Theme Explorer (ATUALIZAR)

```
GET /themes/ → lista de temas (clean mode: id, slug, name, name_en, verse_count)
GET /themes/{id}/detail/ → tema com versos (ref, book, chapter, verse, text)
GET /themes/search/?q=fé → busca por nome PT/EN

No detalhe:
  - Nome PT + EN
  - anchor_verses destacados
  - Lista de versículos com texto completo
  - Click num verso → navega para BibleReader naquele verso
```

### 7. Art Gallery Page (NOVO, OPCIONAL)

Rota sugerida: `/gallery`

```
GET /images/?is_tagged=true → galeria com filtros
GET /images/search/?q=crucifixion → busca
GET /images/artists/ → lista de artistas por obra count

Layout: grid de cards com image_url, title, artist_name
Filtros: style, genre, is_tagged, artist
Click → modal com detalhe completo (tag, verse_links, symbols)
```

## NÃO fazer
- Não criar páginas desnecessárias — integrar nos componentes existentes primeiro
- Não mudar a estrutura de pastas
- Não instalar libs novas — usar shadcn/ui + Tailwind
- Não hardcodar cores — usar tokens CSS
- Não duplicar fetching — usar React Query hooks com cache
- Não mostrar viés denominacional na UI (ecumênico)
- Não exibir `evidence_score`, `grade`, `priority` na UI produto (são dados de pesquisa)
