#!/bin/bash

# Setup Repository - Bible API
# Configura branch protection, labels, e outras configurações do repositório

set -e

REPO_OWNER="PluraNex"
REPO_NAME="bible-api"

echo "🔧 Setting up Bible API repository..."

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) não encontrado. Instale: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI não autenticado. Execute: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI authenticated"

# 1. Configure branch protection for main
echo "🔒 Configuring branch protection for main..."
gh api "repos/$REPO_OWNER/$REPO_NAME/branches/main/protection" \
    --method PUT \
    --input .github/branch-protection.json \
    && echo "✅ Branch protection configured" \
    || echo "❌ Failed to configure branch protection"

# 2. Create repository labels
echo "🏷️ Creating repository labels..."

declare -a labels=(
    "area/api:0052CC:API endpoints and business logic"
    "area/auth:0052CC:Authentication and authorization"
    "area/ai:7B68EE:AI agents and tools"
    "area/audio:FF6B6B:Audio synthesis and management"
    "area/resources:4ECDC4:External resources integration"
    "area/infra:95A5A6:Infrastructure and deployment"
    "area/docs:F39C12:Documentation updates"
    "type/feat:00D084:New feature implementation"
    "type/fix:E74C3C:Bug fix"
    "type/chore:95A5A6:Maintenance and cleanup"
    "type/refactor:9B59B6:Code refactoring"
    "type/test:F1C40F:Test additions or modifications"
    "needs-schema:E67E22:Requires OpenAPI schema update"
    "breaking:E74C3C:Contains breaking changes"
    "security:C0392B:Security-related changes"
    "performance:3498DB:Performance improvements"
    "observability:2ECC71:Monitoring and logging"
)

for label in "${labels[@]}"; do
    IFS=':' read -r name color description <<< "$label"
    gh api "repos/$REPO_OWNER/$REPO_NAME/labels" \
        --method POST \
        --field name="$name" \
        --field color="$color" \
        --field description="$description" \
        > /dev/null 2>&1 \
        && echo "  ✅ Created label: $name" \
        || echo "  ℹ️  Label exists: $name"
done

# 3. Set repository settings
echo "⚙️ Configuring repository settings..."
gh api "repos/$REPO_OWNER/$REPO_NAME" \
    --method PATCH \
    --field allow_squash_merge=true \
    --field allow_merge_commit=false \
    --field allow_rebase_merge=false \
    --field delete_branch_on_merge=true \
    --field allow_auto_merge=true \
    && echo "✅ Repository settings updated" \
    || echo "❌ Failed to update repository settings"

# 4. Enable security features
echo "🛡️ Enabling security features..."
gh api "repos/$REPO_OWNER/$REPO_NAME/vulnerability-alerts" \
    --method PUT \
    && echo "✅ Vulnerability alerts enabled" \
    || echo "ℹ️  Vulnerability alerts already enabled"

gh api "repos/$REPO_OWNER/$REPO_NAME/automated-security-fixes" \
    --method PUT \
    && echo "✅ Automated security fixes enabled" \
    || echo "ℹ️  Automated security fixes already enabled"

echo ""
echo "🎉 Repository setup completed!"
echo ""
echo "📋 Summary:"
echo "  🔒 Branch protection: main branch protected"
echo "  🏷️  Labels: Created standard project labels"
echo "  ⚙️  Settings: Squash merge only, auto-delete branches"
echo "  🛡️  Security: Vulnerability alerts enabled"
echo ""
echo "🔗 Repository: https://github.com/$REPO_OWNER/$REPO_NAME"
echo "⚙️  Settings: https://github.com/$REPO_OWNER/$REPO_NAME/settings"
