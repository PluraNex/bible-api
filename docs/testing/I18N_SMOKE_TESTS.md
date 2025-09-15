# I18n Smoke Tests Guide

## Overview

The i18n smoke tests (`tests/integration/test_i18n_smoke.py`) validate internationalization functionality across the Bible API. These tests ensure consistent language resolution, fallback behavior, and performance across Books, Verses, and Versions endpoints.

## Test Structure

### Test Classes

1. **`BooksI18nSmokeTest`** - Books endpoint i18n functionality
2. **`VersesI18nSmokeTest`** - Verses endpoint i18n functionality
3. **`VersionsI18nSmokeTest`** - Versions endpoint i18n functionality
4. **`I18nPerformanceSmokeTest`** - Performance validation (N+1 queries, response times)
5. **`I18nEdgeCasesSmokeTest`** - Edge cases and error handling

### Test Scenarios

#### Books Tests
- ✅ `lang=pt` returns Portuguese names (`João` for John)
- ✅ `lang=en` returns English names
- ✅ Regional fallback (`pt-PT` → `pt` → `en`)
- ✅ Unknown language fallback to English
- ✅ `Accept-Language` header support
- ✅ Book detail i18n
- ✅ 404 handling for unknown books
- ✅ Payload structure validation

#### Verses Tests
- ✅ Portuguese book names with `lang=pt`
- ✅ Default version selection by language
- ✅ Explicit version parameter with i18n book names
- ✅ 404 for unknown books
- ✅ Payload structure validation

#### Versions Tests
- ✅ Default endpoint language resolution (`pt` → NVI, `en` → KJV)
- ✅ Fallback logic (base ↔ regional)
- ✅ English fallback for unknown languages
- ✅ 404 when no active versions
- ✅ Language filtering in versions list
- ✅ Payload structure validation

#### Performance Tests
- ✅ No N+1 queries (< 10 queries per request)
- ✅ Reasonable response times (< 1s books, < 0.5s versions)
- ✅ Query count validation

#### Edge Cases
- ✅ Malformed language parameters
- ✅ Consistency across endpoints
- ✅ Case sensitivity handling

## Test Data Setup

The tests create comprehensive multilingual data:

```python
# Languages: en, pt, pt-BR, es
# Books: John (João/João Brasil), Genesis (Gênesis)
# Versions: KJV (en), NVI (pt), NVI-BR (pt-BR)
# Verses: John 3:16 in English and Portuguese
```

## Running Tests

### All Smoke Tests
```bash
# Via Docker
docker exec bible-api-web-1 python manage.py test tests.integration.test_i18n_smoke -v 2

# Via script
python scripts/run_i18n_smoke_tests.py
```

### Specific Test Class
```bash
# Books only
python scripts/run_i18n_smoke_tests.py BooksI18nSmokeTest

# Performance only
python scripts/run_i18n_smoke_tests.py I18nPerformanceSmokeTest
```

### Individual Test Method
```bash
docker exec bible-api-web-1 python manage.py test tests.integration.test_i18n_smoke.BooksI18nSmokeTest.test_books_list_with_lang_pt -v 2
```

## Expected Results

### Success Indicators
- ✅ All tests pass with expected language names
- ✅ Fallback logic works consistently
- ✅ No N+1 query issues
- ✅ Response times within thresholds
- ✅ Proper 404 handling

### Common Failures and Solutions

#### Language Resolution Issues
```
AssertionError: Expected 'João' but got 'John'
```
**Solution**: Check BookName data exists for language, verify `request.lang_code` usage in serializers

#### Fallback Not Working
```
AssertionError: Expected 'pt' fallback but got 'en'
```
**Solution**: Verify language resolution middleware and fallback logic in `bible.utils.i18n`

#### Performance Issues
```
AssertionError: Expected < 10 queries but got 15
```
**Solution**: Add `select_related`/`prefetch_related` optimizations in views/serializers

#### Missing Vary Headers (if implemented)
```
AssertionError: Expected Vary header not found
```
**Solution**: Ensure `mark_response_language_sensitive()` is called for Accept-Language dependent endpoints

## Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Run I18n Smoke Tests
  run: |
    docker exec bible-api-web-1 python manage.py test tests.integration.test_i18n_smoke -v 2

- name: Performance Check
  run: |
    python scripts/run_i18n_smoke_tests.py I18nPerformanceSmokeTest
```

## Extending Tests

### Adding New Language Support
```python
# In test setUp()
self.es_lang = Language.objects.create(code="es", name="Spanish")
BookName.objects.create(
    canonical_book=self.john,
    language=self.es_lang,
    name="Juan",
    abbreviation="Jn",
    version=None
)

# Add test case
def test_books_list_with_lang_es(self):
    """Books list with lang=es should return Spanish names."""
    # ... test implementation
```

### Adding New Endpoint Coverage
```python
class ThemesI18nSmokeTest(I18nSmokeTestCase):
    """Smoke tests for Themes i18n functionality."""

    def test_themes_list_with_lang_pt(self):
        # ... implementation
```

## Monitoring and Alerting

Set up monitoring for:
- 🚨 Test execution time > 30s (performance regression)
- 🚨 Any smoke test failures in production deployment
- 📊 Language resolution accuracy metrics
- 📊 API response time trends for i18n endpoints

## Related Documentation

- [API Standards - I18n Section](../API_STANDARDS.md#6-internacionalizacao-i18n)
- [I18n Utilities](../../bible/utils/i18n.py)
- [Language Resolution Middleware](../../bible/utils/i18n.py)
