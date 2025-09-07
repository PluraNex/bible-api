# Repository Setup Guide

This guide helps configure the Bible API repository with proper branch protection, labels, and quality gates.

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
# Make script executable
chmod +x scripts/setup-repo.sh

# Run setup (requires GitHub CLI)
./scripts/setup-repo.sh
```

### Option 2: Manual Configuration

1. **Install GitHub CLI** (if not already installed):
   ```bash
   # macOS
   brew install gh
   
   # Windows
   winget install --id GitHub.cli
   
   # Linux
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   ```

2. **Authenticate GitHub CLI**:
   ```bash
   gh auth login
   ```

3. **Apply branch protection**:
   ```bash
   gh api repos/PluraNex/bible-api/branches/main/protection \
     --method PUT \
     --input .github/branch-protection.json
   ```

## 🔒 Branch Protection Rules

The following rules are automatically applied to the `main` branch:

### Required Status Checks
- ✅ `lint-and-format` - Code formatting with ruff + black
- ✅ `migrations-check` - Django migrations validation  
- ✅ `tests` - Test suite with 80% minimum coverage
- ✅ `openapi-schema-check` - API documentation validation
- ✅ `sonarqube` - Code quality analysis

### Pull Request Requirements
- 📝 **1 approval required** before merge
- 🔄 **Dismiss stale reviews** when new commits pushed
- 📏 **Linear history** enforced (squash merge only)
- 🚫 **No force pushes** to protected branch
- 🚫 **No direct pushes** to main branch

### Additional Protections
- 🛡️ **Admin enforcement** - Rules apply to admins too
- 🔄 **Up-to-date branches** - Must be current with main
- 📊 **Status checks** - All CI jobs must pass

## 🏷️ Repository Labels

Automatically creates standardized labels for issue/PR categorization:

### Area Labels
- `area/api` - API endpoints and business logic
- `area/auth` - Authentication and authorization  
- `area/ai` - AI agents and tools
- `area/audio` - Audio synthesis and management
- `area/resources` - External resources integration
- `area/infra` - Infrastructure and deployment
- `area/docs` - Documentation updates

### Type Labels
- `type/feat` - New feature implementation
- `type/fix` - Bug fix
- `type/chore` - Maintenance and cleanup
- `type/refactor` - Code refactoring
- `type/test` - Test additions or modifications

### Special Labels
- `needs-schema` - Requires OpenAPI schema update
- `breaking` - Contains breaking changes
- `security` - Security-related changes
- `performance` - Performance improvements
- `observability` - Monitoring and logging

## ⚙️ Repository Settings

### Merge Settings
- ✅ **Squash merge** enabled (recommended)
- ❌ **Merge commit** disabled
- ❌ **Rebase merge** disabled
- ✅ **Auto-delete branches** after merge
- ✅ **Auto-merge** when checks pass

### Security Settings
- ✅ **Vulnerability alerts** enabled
- ✅ **Automated security fixes** enabled
- ✅ **Private vulnerability reporting** enabled

## 🔍 Validation

After setup, verify configuration:

1. **Check branch protection**:
   ```bash
   gh api repos/PluraNex/bible-api/branches/main/protection
   ```

2. **View in GitHub UI**:
   - Go to: `Settings` → `Branches` → `main`
   - Verify all 5 status checks are listed
   - Confirm "Restrict pushes" is enabled

3. **Test with PR**:
   - Create a test PR
   - Should show: "Merging is blocked"
   - All 5 checks should be required

## 🆘 Troubleshooting

### GitHub CLI Issues
```bash
# Check authentication
gh auth status

# Re-authenticate if needed
gh auth login --scopes repo,admin:repo_hook

# Test API access
gh api user
```

### Permission Issues
- Ensure you have **admin access** to the repository
- Organization owners may need to enable branch protection enforcement

### Status Check Names
If checks don't match, verify job names in `.github/workflows/ci.yml`:
- Job names must match exactly in `branch-protection.json`
- Case sensitive matching

## 📚 References

- [GitHub Branch Protection API](https://docs.github.com/en/rest/branches/branch-protection)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [Repository Settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features)