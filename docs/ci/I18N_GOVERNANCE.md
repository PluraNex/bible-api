# I18n Governance - CI/CD Integration

## Overview

This document describes how to integrate the i18n audit command into CI/CD pipelines to maintain continuous governance over internationalization data quality and coverage.

## Audit Command Usage

### Basic Command Structure

```bash
python manage.py audit_i18n [OPTIONS]
```

### Recommended CI/CD Configuration

```yaml
# .github/workflows/i18n-governance.yml
name: I18n Governance

on:
  pull_request:
    paths:
      - 'bible/models/**'
      - 'bible/management/commands/**'
      - 'data/**'
  schedule:
    # Run daily at 02:00 UTC
    - cron: '0 2 * * *'

jobs:
  i18n-audit:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run I18n Audit
        run: |
          python manage.py audit_i18n \
            --report-only \
            --fail-on-missing \
            --min-coverage=90 \
            --languages=pt,en \
            --include-deuterocanon \
            --report-file=reports/i18n_audit.json

      - name: Upload Audit Report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: i18n-audit-report
          path: reports/i18n_audit.json
          retention-days: 30
```

### Makefile Integration

Add to your `Makefile`:

```makefile
# I18n governance commands
.PHONY: i18n-audit i18n-audit-ci i18n-report

i18n-audit:
	@echo "Running I18n audit (read-only)..."
	docker exec bible-api-web-1 python manage.py audit_i18n --report-only

i18n-audit-ci:
	@echo "Running I18n audit for CI/CD..."
	docker exec bible-api-web-1 python manage.py audit_i18n \
		--report-only \
		--fail-on-missing \
		--min-coverage=90 \
		--languages=pt,en \
		--include-deuterocanon \
		--report-file=/tmp/i18n_audit.json

i18n-report:
	@echo "Generating detailed I18n coverage report..."
	docker exec bible-api-web-1 python manage.py audit_i18n \
		--report-file=reports/i18n_coverage_$(shell date +%Y%m%d).json \
		--languages=pt,en,es
```

## Command Options Reference

### Core Options

| Option | Description | Use Case |
|--------|-------------|----------|
| `--report-only` | Read-only mode, no changes | CI/CD validation |
| `--fail-on-missing` | Exit code ≠ 0 if missing data | CI gate |
| `--min-coverage=90` | Require minimum coverage % | Quality gate |

### Filtering Options

| Option | Description | Example |
|--------|-------------|---------|
| `--languages=pt,en` | Audit specific languages | `--languages=pt,en,es` |
| `--include-deuterocanon` | Include deuterocanonical books | For Catholic tradition |
| `--exclude-deuterocanon` | Exclude deuterocanonical books | For Protestant tradition |

### Output Options

| Option | Description | Use Case |
|--------|-------------|----------|
| `--report-file=path.json` | Export detailed JSON report | Artifact storage |

## Exit Codes

| Code | Meaning | Action Required |
|------|---------|-----------------|
| `0` | All checks passed | None |
| `1` | Missing i18n entries found | Add missing translations |
| `2` | Coverage below minimum | Improve coverage |

## Integration Patterns

### 1. PR Validation (Strict)

```bash
# Fail if any missing entries
python manage.py audit_i18n \
  --report-only \
  --fail-on-missing \
  --languages=pt,en
```

### 2. Nightly Reporting (Comprehensive)

```bash
# Generate full report with all languages
python manage.py audit_i18n \
  --report-file=reports/nightly_i18n_$(date +%Y%m%d).json \
  --languages=pt,en,es \
  --include-deuterocanon
```

### 3. Release Gating (Quality)

```bash
# Ensure 95% coverage before release
python manage.py audit_i18n \
  --report-only \
  --fail-on-missing \
  --min-coverage=95 \
  --languages=pt,en
```

## Monitoring and Alerting

### Slack Integration Example

```yaml
- name: Notify Slack on I18n Issues
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    text: "🌍 I18n audit failed: Missing translations detected"
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Metrics Collection

```bash
# Extract metrics from JSON report
jq '.totals.average_coverage' reports/i18n_audit.json
jq '.totals.total_missing' reports/i18n_audit.json
jq '.totals.languages_with_gaps' reports/i18n_audit.json
```

## Best Practices

### 1. Gradual Rollout

Start with low coverage requirements and gradually increase:

```bash
# Week 1: 70% coverage
--min-coverage=70

# Week 2: 80% coverage
--min-coverage=80

# Week 3+: 90% coverage
--min-coverage=90
```

### 2. Language Prioritization

Focus on primary languages first:

```bash
# Phase 1: Core languages
--languages=pt,en

# Phase 2: Add Spanish
--languages=pt,en,es

# Phase 3: Full coverage
# (no --languages filter)
```

### 3. Report Retention

```bash
# Keep reports for trend analysis
mkdir -p reports/i18n/$(date +%Y/%m)
python manage.py audit_i18n \
  --report-file=reports/i18n/$(date +%Y/%m)/audit_$(date +%Y%m%d_%H%M).json
```

## Troubleshooting

### Common Issues

1. **High missing count suddenly**: Check if new canonical books were added
2. **Coverage dropped**: Verify language data wasn't accidentally deleted
3. **Audit command fails**: Check database connectivity and model integrity

### Debug Commands

```bash
# Verbose output for debugging
python manage.py audit_i18n --report-only -v 2

# Check specific language
python manage.py audit_i18n --report-only --languages=pt

# Check specific book subset
python manage.py audit_i18n --report-only --exclude-deuterocanon
```
