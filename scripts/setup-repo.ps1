# Setup Repository - Bible API (PowerShell version)
# Configura branch protection, labels, e outras configurações do repositório

param(
    [string]$Owner = "PluraNex",
    [string]$Repo = "bible-api"
)

Write-Host "🔧 Setting up Bible API repository..." -ForegroundColor Green

# Check if gh CLI is available
try {
    gh --version | Out-Null
    Write-Host "✅ GitHub CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ GitHub CLI (gh) não encontrado. Instale: https://cli.github.com/" -ForegroundColor Red
    exit 1
}

# Check authentication
try {
    gh auth status 2>$null | Out-Null
    Write-Host "✅ GitHub CLI authenticated" -ForegroundColor Green
} catch {
    Write-Host "❌ GitHub CLI não autenticado. Execute: gh auth login" -ForegroundColor Red
    exit 1
}

# 1. Configure branch protection
Write-Host "🔒 Configuring branch protection for main..." -ForegroundColor Yellow
try {
    gh api "repos/$Owner/$Repo/branches/main/protection" `
        --method PUT `
        --input .github/branch-protection.json
    Write-Host "✅ Branch protection configured" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to configure branch protection: $_" -ForegroundColor Red
}

# 2. Create labels
Write-Host "🏷️ Creating repository labels..." -ForegroundColor Yellow

$labels = @(
    @{name="area/api"; color="0052CC"; description="API endpoints and business logic"},
    @{name="area/auth"; color="0052CC"; description="Authentication and authorization"},
    @{name="area/ai"; color="7B68EE"; description="AI agents and tools"},
    @{name="area/audio"; color="FF6B6B"; description="Audio synthesis and management"},
    @{name="area/resources"; color="4ECDC4"; description="External resources integration"},
    @{name="area/infra"; color="95A5A6"; description="Infrastructure and deployment"},
    @{name="area/docs"; color="F39C12"; description="Documentation updates"},
    @{name="type/feat"; color="00D084"; description="New feature implementation"},
    @{name="type/fix"; color="E74C3C"; description="Bug fix"},
    @{name="type/chore"; color="95A5A6"; description="Maintenance and cleanup"},
    @{name="type/refactor"; color="9B59B6"; description="Code refactoring"},
    @{name="type/test"; color="F1C40F"; description="Test additions or modifications"},
    @{name="needs-schema"; color="E67E22"; description="Requires OpenAPI schema update"},
    @{name="breaking"; color="E74C3C"; description="Contains breaking changes"},
    @{name="security"; color="C0392B"; description="Security-related changes"},
    @{name="performance"; color="3498DB"; description="Performance improvements"},
    @{name="observability"; color="2ECC71"; description="Monitoring and logging"}
)

foreach ($label in $labels) {
    try {
        gh api "repos/$Owner/$Repo/labels" `
            --method POST `
            --field name="$($label.name)" `
            --field color="$($label.color)" `
            --field description="$($label.description)" | Out-Null
        Write-Host "  ✅ Created label: $($label.name)" -ForegroundColor Green
    } catch {
        Write-Host "  ℹ️  Label exists: $($label.name)" -ForegroundColor Gray
    }
}

# 3. Configure repository settings
Write-Host "⚙️ Configuring repository settings..." -ForegroundColor Yellow
try {
    gh api "repos/$Owner/$Repo" `
        --method PATCH `
        --field allow_squash_merge=true `
        --field allow_merge_commit=false `
        --field allow_rebase_merge=false `
        --field delete_branch_on_merge=true `
        --field allow_auto_merge=true | Out-Null
    Write-Host "✅ Repository settings updated" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to update repository settings: $_" -ForegroundColor Red
}

# 4. Enable security features
Write-Host "🛡️ Enabling security features..." -ForegroundColor Yellow
try {
    gh api "repos/$Owner/$Repo/vulnerability-alerts" --method PUT | Out-Null
    Write-Host "✅ Vulnerability alerts enabled" -ForegroundColor Green
} catch {
    Write-Host "ℹ️  Vulnerability alerts already enabled" -ForegroundColor Gray
}

try {
    gh api "repos/$Owner/$Repo/automated-security-fixes" --method PUT | Out-Null
    Write-Host "✅ Automated security fixes enabled" -ForegroundColor Green
} catch {
    Write-Host "ℹ️  Automated security fixes already enabled" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🎉 Repository setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "  🔒 Branch protection: main branch protected"
Write-Host "  🏷️  Labels: Created standard project labels"
Write-Host "  ⚙️  Settings: Squash merge only, auto-delete branches"
Write-Host "  🛡️  Security: Vulnerability alerts enabled"
Write-Host ""
Write-Host "🔗 Repository: https://github.com/$Owner/$Repo" -ForegroundColor Blue
Write-Host "⚙️  Settings: https://github.com/$Owner/$Repo/settings" -ForegroundColor Blue