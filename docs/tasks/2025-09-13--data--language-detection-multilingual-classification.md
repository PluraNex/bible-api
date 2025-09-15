# T-DATA-002: Language Detection - Multilingual Bible Classification System

**Created:** 2025-09-13
**Priority:** HIGH
**Complexity:** Medium
**Estimated Time:** 2-3 days
**Dependencies:** T-DATA-001
**Status:** Not Started

## Objective

Implement intelligent language detection system to automatically classify 100+ Bible translations by language for proper i18n organization.

## Context

Current `data/datasets/json/` contains 150+ Bible translations in multiple languages with inconsistent naming:
- `PorBLivre.json`, `GerSch.json`, `FreCrampon.json`, `KJV.json`
- Language information embedded in filenames but not standardized
- Need automatic classification for language-first directory structure
- Support for 25+ languages including Portuguese, English, German, French, Spanish, etc.

## Scope

### In Scope
- Automated language detection from filename patterns
- Text content analysis for validation/refinement
- Confidence scoring system for detection quality
- Language manifest generation for all existing files
- Support for 25+ languages with extensible pattern system
- Preview analysis tool before migration

### Out of Scope
- Actual data migration (T-DATA-004)
- Translation quality assessment
- Language learning/ML approaches (using rule-based detection)

## Technical Implementation

### LanguageDetector Class
```python
class LanguageDetector:
    FILENAME_PATTERNS = {
        r'^Por.*': 'pt',      # Portuguese
        r'^Ger.*': 'de',      # German
        r'^Fre.*': 'fr',      # French
        r'^KJV.*': 'en',      # English
        # ... 20+ more patterns
    }

    TEXT_PATTERNS = {
        'pt': [r'\bDeus\b', r'\bSenhor\b', r'\bJesus\b'],
        'en': [r'\bGod\b', r'\bLord\b', r'\bJesus\b'],
        'de': [r'\bGott\b', r'\bHerr\b', r'\bJesus\b'],
        # ... validation patterns
    }

    def detect_language(self, filename: str, sample_text: str = None) -> Tuple[str, float]
    def create_language_manifest(self, data_dir: Path) -> Dict
```

### Language Mapping Support
- Portuguese: 15+ versions (NVI, ARC, Biblia Livre, etc.)
- English: 30+ versions (KJV, ASV, BBE, WEB, etc.)
- German: 10+ versions (Luther, Elberfelder, Menge, etc.)
- French: 15+ versions (Crampon, JND, Stapfer, etc.)
- Spanish, Italian, Dutch, Czech, Finnish, Croatian, etc.

### Confidence Scoring
- **1.0**: Filename + text patterns both match
- **0.8**: Strong filename pattern match
- **0.5**: Weak filename or text-only detection
- **0.0**: No patterns matched (unknown)

## Files to Create/Modify

### New Files
```
common/data_pipeline/
  language_detection.py # LanguageDetector class

scripts/
  analyze_languages.py # Standalone analysis tool

tests/common/data_pipeline/
  test_language_detection.py

data/ingested/reports/
  language-analysis.json # Generated manifest (output)
```

### Modified Files
```
Makefile # Add language analysis targets
```

## Definition of Ready (DoR)

- [ ] Current multilingual dataset structure mapped
- [ ] Filename patterns for 25+ languages identified
- [ ] Sample text patterns for major languages collected
- [ ] Confidence scoring approach defined

## Definition of Done (DoD)

- [ ] `LanguageDetector` supports 25+ languages
- [ ] Filename pattern detection with 95%+ accuracy
- [ ] Text content validation for confirmation
- [ ] `scripts/analyze_languages.py` provides detailed analysis
- [ ] Complete manifest of 150+ files generated with languages
- [ ] Confidence scoring accurately reflects detection quality
- [ ] Unknown files clearly identified for manual review
- [ ] Unit tests cover all detection scenarios
- [ ] `make analyze-languages` target functional

## Expected Output

### Language Distribution (Estimated)
- **Portuguese:** ~15 versions (NVI, ARC, ARA, TB, etc.)
- **English:** ~30 versions (KJV, ASV, BBE, WEB, etc.)
- **German:** ~10 versions (Sch, Menge, Elb, etc.)
- **French:** ~15 versions (Crampon, JND, etc.)
- **Spanish:** ~5 versions
- **Other languages:** ~25 versions (Italian, Dutch, Czech, etc.)
- **Unknown:** <5 files requiring manual classification

### Analysis Report Format
```json
{
  "summary": {
    "total_files": 150,
    "languages_detected": 25,
    "unknown_files": 3
  },
  "languages": {
    "pt": {"count": 15, "files": [...], "confidence_avg": 0.92},
    "en": {"count": 30, "files": [...], "confidence_avg": 0.89},
    "de": {"count": 10, "files": [...], "confidence_avg": 0.85}
  }
}
```

## Testing Strategy

- Unit tests for filename pattern matching
- Text analysis validation tests
- Confidence scoring accuracy tests
- Full dataset analysis integration test
- Edge case handling (ambiguous files, corrupted data)

## Success Metrics

- 95%+ accuracy in language detection
- <5 files classified as "unknown"
- 80%+ files with confidence > 0.8
- Complete language manifest generated in <30 seconds

## Notes

### Design Decisions
1. **Rule-based over ML**: More predictable, debuggable, faster
2. **Confidence scoring**: Allows manual review of low-confidence detections
3. **Extensible patterns**: Easy to add new languages
4. **Text validation**: Catches filename false positives

### Manual Review Cases
Files with confidence < 0.5 should be manually reviewed:
- Unusual naming patterns
- Mixed language content
- Corrupted or incomplete data

## Related Tasks

- **Depends on:** T-DATA-001 (directory structure)
- **Blocks:** T-DATA-004 (migration needs language classification)
- **Integrates with:** T-DATA-003 (CLI will use detection results)
