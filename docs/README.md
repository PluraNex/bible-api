# Bible API Documentation

Welcome to the Bible API documentation. This directory contains all project documentation organized by category.

## Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
├── openapi-v1.yaml              # OpenAPI schema (source of truth)
├── api/                         # API standards and testing
├── architecture/                # System design, domain proposals, implemented features
├── ci/                          # CI/CD and governance docs
├── data/                        # Data pipeline documentation
├── operations/                  # Runbooks and operational guides
├── research/                    # Analysis, benchmarks, research findings
├── tasks/                       # Task specifications and tracking
├── templates/                   # Code templates
├── testing/                     # Test strategy and smoke tests
└── workflows/                   # Development processes and playbooks
```

## API

- **[API Standards](api/API_STANDARDS.md)** - Versioning, auth, throttling, errors, i18n, pagination, cache
- **[API Testing Best Practices](api/API_TESTING_BEST_PRACTICES.md)** - Comprehensive testing guidelines
- **[Frontend API Analysis](api/FRONTEND_API_ANALYSIS.md)** - Frontend consumption patterns and contract analysis

## Architecture

- **[Base Project Overview](architecture/BIBLE_API_BASE_PROJECT.md)** - Complete system architecture (master reference)
- **[RAG Optimization](architecture/RAG_OPTIMIZATION_PLAN.md)** - Hybrid search, reranking, query expansion, MMR (implemented)
- **[NLP Integration](architecture/NLP_INTEGRATION_PLAN.md)** - NLP query tool and dynamic alpha (implemented)
- **[Topical Pipeline](architecture/TOPICAL_PIPELINE_ARCHITECTURE.md)** - 6-phase topic processing pipeline
- **[Topics Architecture Review](architecture/TOPICS_ARCHITECTURE_REVIEW.md)** - Gap analysis and model proposals
- **[Topics Domain Proposal](architecture/TOPICS_DOMAIN_PROPOSAL.md)** - Topics domain design
- **[Comments Review](architecture/COMMENTS_REVIEW.md)** - Commentary models code review

## Data

- **[Unified Data System](data/UNIFIED_DATA_SYSTEM.md)** - Current data pipeline (3 files instead of 26)

## Operations

- **[Observability](operations/OBSERVABILITY.md)** - Prometheus, Grafana, health checks, metrics
- **[RAG Runbook](operations/RAG_RUNBOOK.md)** - RAG operational guide
- **[Local Postgres Restore](operations/LOCAL_POSTGRES_RESTORE.md)** - Database restoration
- **[Hybrid Benchmark Checklist](operations/HYBRID_BENCHMARK_CHECKLIST.md)** - Search benchmark validation
- **[Catena Scraping](operations/CATENA_SCRAPING_COMPLETION_PLAN.md)** - Commentary scraping completion

## Research

- **[Hybrid Search Evidence](research/HYBRID_SEARCH_EVIDENCE_MASTER.md)** - Evidence consolidation
- **[Search Quality Analysis](research/SEARCH_QUALITY_ANALYSIS.md)** - Hybrid search performance analysis
- **[NLP Data Analysis](research/NLP_DATA_ANALYSIS.md)** - NLP query processing analysis
- **[Dataset Inventory](research/DATASET_INVENTORY_AND_GAPS.md)** - Available datasets and gaps
- **[Topics Dataset Evolution](research/TOPICS_DATASET_EVOLUTION.md)** - Topic dataset status
- **[Pipeline & Embedding Strategy](research/PIPELINE_PHASES_AND_EMBEDDING_STRATEGY.md)** - Embedding approach
- **[TCC Hybrid Search Scope](research/TCC_HYBRID_SEARCH_SCOPE.md)** - Thesis scope definition
- **[Truth Source Strategy](research/TRUTH_SOURCE_STRATEGY.md)** - Authoritative data sources

## Workflows

- **[Development Flow Playbook](workflows/DEV_FLOW_PLAYBOOK.md)** - Complete development workflow
- **[Project Orchestrator](workflows/BIBLE_API_ORCHESTRATOR.md)** - High-level project coordination
- **[GitHub Integration](workflows/GITHUB_INTEGRATION.md)** - Task-to-issue sync workflow
- **[Repository Setup](workflows/REPOSITORY_SETUP.md)** - Branch protection, labels, CI setup

## CI / Testing

- **[i18n Governance](ci/I18N_GOVERNANCE.md)** - Internationalization standards
- **[i18n Smoke Tests](testing/I18N_SMOKE_TESTS.md)** - Multilingual test specifications

## Tasks

- **[Task Index](tasks/INDEX.md)** - Active and completed tasks with status tracking
- **[Task README](tasks/README.md)** - Task creation conventions and workflow

---

For development setup and commands, see [CLAUDE.md](../CLAUDE.md) and [README.md](../README.md).
