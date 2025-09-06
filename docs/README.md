# Bible API Documentation

Welcome to the Bible API documentation. This directory contains all project documentation organized by category.

## 📁 Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
├── workflows/                   # Development processes and workflows
├── architecture/                # System design and architecture docs
├── tasks/                       # Task specifications and tracking
└── api/                        # API documentation and testing guides
```

## 🔄 Workflows
- **[Development Flow Playbook](workflows/DEV_FLOW_PLAYBOOK.md)** - Complete development workflow guide
- **[Project Orchestrator](workflows/BIBLE_API_ORCHESTRATOR.md)** - High-level project coordination

## 🏗️ Architecture  
- **[Base Project Overview](architecture/BIBLE_API_BASE_PROJECT.md)** - Complete system architecture and vision

## 📋 Tasks
- **[Task Index](tasks/INDEX.md)** - Active and completed tasks with status tracking
- **[T-000: Dev Environment Setup](tasks/2025-09-06--infra--dev-environment-setup.md)** - Infrastructure setup task
- **[T-001: Django Project Setup](tasks/2025-09-06--api--django-project-setup.md)** - Django application setup task

## 🚀 API Documentation
- **[API Testing Best Practices](api/API_TESTING_BEST_PRACTICES.md)** - Comprehensive API testing guidelines

## 📖 How to Use This Documentation

### For Developers
1. Start with [Development Flow Playbook](workflows/DEV_FLOW_PLAYBOOK.md) to understand the workflow
2. Review [Base Project Overview](architecture/BIBLE_API_BASE_PROJECT.md) for system context
3. Check [Task Index](tasks/INDEX.md) for current work items
4. Follow [API Testing Best Practices](api/API_TESTING_BEST_PRACTICES.md) when working with APIs

### For AI Agents (Claude)
- All documentation follows the established patterns from the main [CLAUDE.md](../CLAUDE.md)
- Task files in `docs/tasks/` use the standardized format with 8 acceptance criteria
- Workflow documentation provides step-by-step guidance for common operations
- Architecture documentation provides context for making informed technical decisions

## 🔄 Maintenance

This documentation structure should be maintained as the project evolves:

- **Workflows**: Update when development processes change
- **Architecture**: Keep synchronized with system design decisions  
- **Tasks**: Archive completed tasks, add new ones following the established format
- **API**: Update when API contracts or testing approaches change

---

For the main development setup and commands, see the root [README.md](../README.md) and [CLAUDE.md](../CLAUDE.md).