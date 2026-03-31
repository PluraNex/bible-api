# 📊 Análise: Frontend (Word-Sanctuary) + API (Bible-API)

## Visão Geral da Arquitetura Frontend

### Estrutura de Camadas

```
src/
├── shared/api/
│   ├── clients/         → BibleApiClient (fetch wrapper)
│   ├── config/          → endpoints.ts (URL builder)
│   ├── types/           → api.types.ts (interfaces TypeScript)
│   ├── adapters/        → bibleAdapter.ts (normalização API→Frontend)
│   └── repositories/    → Abstração por domínio
├── entities/            → Modelos de domínio
├── features/            → Funcionalidades (ThemeExplorer, BibleSearch)
└── pages/               → Páginas da aplicação
```

### Padrão de Repositórios Existentes

| Repositório | Endpoints Consumidos | i18n |
|-------------|---------------------|------|
| `VerseRepository` | `/verses/by-chapter/`, `/verses/by-reference/`, `/verses/compare/` | ✅ `lang` + `Accept-Language` |
| `BookRepository` | `/books/`, `/books/search/`, `/books/{name}/chapters/` | ✅ `lang` + `Accept-Language` |
| `ThemeRepository` | `/themes/`, `/themes/search/`, `/themes/{id}/statistics/` | ✅ `lang` + `Accept-Language` |
| `SearchRepository` | `/verses/?word=`, `/ai/rag/hybrid/` | ❌ Não usa i18n |
| `CommentRepository` | `/comments/` | ✅ `langCode` |
| `VersionRepository` | `/versions/` | - |

---

## 🔍 Padrões Identificados

### 1. Cliente HTTP Centralizado

```typescript
// bibleApiClient.ts - Padrão usado
const response = await bibleApiClient.get<T>(url, {
  params: queryParams,
  langCode: params?.langCode  // Usado para Accept-Language header
});
```

### 2. Normalização de Dados (Adapter Pattern)

```typescript
// bibleAdapter.ts - Converte snake_case → camelCase
normalizeVerse(apiVerse: ApiVerse): Verse {
  return {
    id: apiVerse.id.toString(),
    book: apiVerse.book_name,     // API: book_name
    bookOsis: apiVerse.book_osis, // API: book_osis
    chapter: apiVerse.chapter,
    verse: apiVerse.verse,        // API renomeou number → verse ✅
    text: apiVerse.text,
    version: apiVerse.version_code,
    reference: apiVerse.reference,
  };
}
```

### 3. Tipos da API (api.types.ts)

```typescript
// Tipos bem definidos para cada entidade
interface ApiVerse {
  id: number;
  book: number;       // ⚠️ Ainda espera ID (legado)
  book_osis: string;  // ✅ OSIS code
  book_name: string;  // ✅ Nome localizado
  version: number;    // ⚠️ Ainda espera ID (legado)
  version_code: string;
  chapter: number;
  verse: number;
  text: string;
  reference: string;
}
```

### 4. Paginação (Dois Formatos)

```typescript
// DRF padrão
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Customizado (StandardResultsSetPagination)
interface StandardPaginatedResponse<T> {
  pagination: {
    count: number;
    num_pages: number;
    current_page: number;
    page_size: number;
    next: string | null;
    previous: string | null;
  };
  results: T[];
}
```

---

## 🎯 Pontos de Melhoria na API

### 1. Consistência de Resposta

**Problema**: API retorna formatos diferentes dependendo do endpoint

```typescript
// VerseRepository.ts - Precisa lidar com 3 formatos!
if (Array.isArray(response.data)) {
  verses = response.data;
} else if ('pagination' in response.data) {
  verses = (response.data as StandardPaginatedResponse<ApiVerse>).results;
} else {
  verses = (response.data as PaginatedResponse<ApiVerse>).results;
}
```

**Solução**: Padronizar TODOS os endpoints para `StandardPaginatedResponse`

### 2. Objetos Aninhados vs IDs

**Problema**: Alguns endpoints retornam IDs, outros retornam objetos

```typescript
interface ApiVerse {
  book: number;        // ID (legado) - requer request adicional
  book_osis: string;   // OSIS code (novo)
  book_name: string;   // Nome localizado (novo) ✅
}
```

**Atual no Backend (VerseSerializer)**:
```python
class VerseSerializer(serializers.ModelSerializer):
    book = BookNestedSerializer(read_only=True)      # ✅ Objeto aninhado
    version = VersionNestedSerializer(read_only=True) # ✅ Objeto aninhado
```

**Solução**: ✅ Já implementado no backend! Frontend precisa atualizar tipos.

### 3. Busca Semântica sem i18n

**Problema**: `SearchRepository` não passa idioma para busca RAG

```typescript
// SearchRepository.ts
async searchHybrid(params: HybridSearchParams): Promise<SemanticSearchResult> {
  const url = API_ENDPOINTS.search.hybrid(query.trim(), mergedParams);
  const response = await bibleApiClient.get<RagSearchResponse>(url);
  // ⚠️ Não passa langCode!
}
```

**Solução**: Adicionar `lang` ao endpoint híbrido

### 4. Endpoints de Temas Limitados

**Problema**: Frontend usa apenas:
- `/themes/` - Lista
- `/themes/search/?q=` - Busca
- `/themes/{id}/statistics/` - Estatísticas

**Oportunidade**: API tem mais endpoints não consumidos:
- `/themes/{id}/progression/` - Progressão cronológica
- `/themes/analysis/by-book/{book}/` - Análise por livro
- `/themes/{concept}/concept-map/` - Mapa conceitual

---

## 📋 Checklist para Topics Domain

Baseado nos padrões do frontend, o **Topics Domain** deve:

### ✅ Seguir Padrões Existentes

1. **Nomenclatura de campos**:
   - API: `snake_case` → Frontend: `camelCase`
   - Ex: `topic_name` → `topicName`

2. **Objetos aninhados** (não IDs):
```json
{
  "slug": "abraham",
  "name": "Abraão",           // Localizado
  "entities": [
    {
      "canonical_id": "PERSON:abraham",
      "display_name": "Abraão",   // Localizado
      "entity_type": "PERSON"
    }
  ]
}
```

3. **Paginação padronizada**:
```json
{
  "pagination": {
    "count": 4057,
    "num_pages": 41,
    "current_page": 1,
    "page_size": 100
  },
  "results": [...]
}
```

4. **i18n via query param e header**:
```
GET /api/v1/topics/abraham/?lang=pt
Accept-Language: pt-BR,pt;q=0.9,en;q=0.8
```

### 📝 Tipos TypeScript Sugeridos

```typescript
// api.types.ts - Adicionar
interface ApiTopic {
  slug: string;
  canonical_id: string;
  name: string;              // Localizado
  aliases: string[];         // Localizados
  summary: string;           // Localizado
  outline: string[];         // Localizado
  key_concepts: string[];    // Localizados
  
  // Estatísticas
  total_verses: number;
  ot_refs: number;
  nt_refs: number;
  books_count: number;
  aspects_count: number;
  
  // AI
  ai_enriched: boolean;
  ai_confidence: number;
  
  // Meta
  primary_source: string;
  available_sources: string[];
  language_code: string;     // Idioma da resposta
}

interface ApiTopicAspect {
  id: number;
  label: string;             // Localizado
  order: number;
  verse_count: number;
  books: string[];           // OSIS codes
}

interface ApiCanonicalEntity {
  canonical_id: string;      // "PERSON:abraham"
  entity_type: string;
  display_name: string;      // Localizado
  aliases: string[];         // Localizados
  frequency: number;
}

interface ApiCanonicalSymbol {
  canonical_id: string;      // "NATURAL:water"
  symbol_type: string;
  display_name: string;      // Localizado
  literal_meaning: string;   // Localizado
  symbolic_meanings: string[];  // Localizados
  frequency: number;
}
```

### 📁 TopicRepository Sugerido

```typescript
// TopicRepository.ts
export class TopicRepository {
  async list(params?: {
    page?: number;
    page_size?: number;
    letter?: string;
    langCode?: string;
  }): Promise<StandardPaginatedResponse<ApiTopic>> { ... }

  async getBySlug(slug: string, langCode?: string): Promise<ApiTopic> { ... }

  async search(query: string, langCode?: string): Promise<ApiTopic[]> { ... }

  async getAspects(slug: string, langCode?: string): Promise<ApiTopicAspect[]> { ... }

  async getVerses(slug: string, version?: string): Promise<ApiVerse[]> { ... }

  async getEntities(slug: string, langCode?: string): Promise<ApiCanonicalEntity[]> { ... }

  async getSymbols(slug: string, langCode?: string): Promise<ApiCanonicalSymbol[]> { ... }

  async getStatistics(slug: string): Promise<ApiTopicStatistics> { ... }

  async getBibleCoverage(slug: string, langCode?: string): Promise<ApiBibleCoverage> { ... }

  // Global lists
  async listEntities(type?: string, langCode?: string): Promise<ApiCanonicalEntity[]> { ... }
  
  async listSymbols(type?: string, langCode?: string): Promise<ApiCanonicalSymbol[]> { ... }
}
```

---

## 🔧 Melhorias Imediatas na API

### 1. Padronizar Resposta de Lista

**Antes** (inconsistente):
```python
# Alguns endpoints retornam array, outros paginado
return Response(serializer.data)  # Array direto
```

**Depois** (sempre paginado):
```python
# Usar StandardResultsSetPagination em TODOS os ListAPIView
class TopicListView(generics.ListAPIView):
    pagination_class = StandardResultsSetPagination
```

### 2. Adicionar language_code à Resposta

```python
class TopicSerializer(serializers.ModelSerializer):
    language_code = serializers.SerializerMethodField()
    
    def get_language_code(self, obj):
        from bible.utils.i18n import get_language_from_context
        return get_language_from_context(self.context)
```

### 3. Expandir RAG com i18n

```python
# /ai/rag/hybrid/ - Adicionar parâmetro lang
class HybridSearchView(APIView):
    def get(self, request):
        lang_code = request.query_params.get('lang', 'pt')
        # Usar lang_code para localizar nomes de livros nos resultados
```

---

## 📊 Resumo

| Aspecto | Status Atual | Recomendação |
|---------|-------------|--------------|
| Paginação | ⚠️ Inconsistente | Usar `StandardPaginatedResponse` sempre |
| i18n | ✅ Bom | Adicionar `language_code` às respostas |
| Objetos Aninhados | ✅ Já implementado | Frontend precisa atualizar tipos |
| Normalização (Adapter) | ✅ Bom padrão | Manter para Topics |
| Busca RAG | ⚠️ Sem i18n | Adicionar `lang` param |
| Topics Domain | 🆕 Novo | Seguir padrões documentados |

