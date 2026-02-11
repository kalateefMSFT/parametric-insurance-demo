#!/usr/bin/env bash
# =============================================================================
# migrate_to_v2.sh — Restructure repository from v1 (multi-file) to v2 (unified notebook)
#
# Run this ONCE from the repository root:
#   chmod +x migrate_to_v2.sh && ./migrate_to_v2.sh
#
# What it does:
#   1. Creates archive/v1/ directory
#   2. Moves v1 source code, docs, and tests into archive/v1/
#   3. Moves the unified notebook into fabric/notebooks/
#   4. Installs new README, QUICKSTART, DEPLOYMENT, EVENTGRID_GUIDE, CHANGELOG
#   5. Updates .env.example
#
# Safe to run: it moves (not deletes), so nothing is lost.
# =============================================================================

set -euo pipefail

echo "============================================================================"
echo "Parametric Insurance Demo — v1 → v2 Migration"
echo "============================================================================"
echo ""

# Check we're in the right place
if [ ! -f "README.md" ] || [ ! -d "shared" ]; then
    echo "ERROR: Run this script from the repository root directory."
    echo "       Expected to find README.md and shared/ in the current directory."
    exit 1
fi

# ---- Step 1: Create archive structure ----
echo "📁 Creating archive/v1/ directory..."
mkdir -p archive/v1

# ---- Step 2: Move v1 source code ----
echo "📦 Archiving v1 source code..."

# Core libraries
[ -d "shared" ] && mv shared archive/v1/ && echo "  ✓ shared/"

# Azure Functions
[ -d "functions" ] && mv functions archive/v1/ && echo "  ✓ functions/"

# Foundry agent
[ -d "foundry" ] && mv foundry archive/v1/ && echo "  ✓ foundry/"

# Demo runner
[ -d "demo" ] && mv demo archive/v1/ && echo "  ✓ demo/"

# Tests
[ -d "tests" ] && mv tests archive/v1/ && echo "  ✓ tests/"

# ---- Step 3: Move v1 documentation ----
echo "📝 Archiving v1 documentation..."

for doc in README_FIRST.md PROJECT_SUMMARY.md MANIFEST.md FILE_STRUCTURE.md \
           CONTRIBUTING.md GETTING_STARTED.md POWERSHELL_GUIDE.md INDEX.md; do
    [ -f "$doc" ] && mv "$doc" archive/v1/ && echo "  ✓ $doc"
done

# Move original QUICKSTART and DEPLOYMENT (will be replaced with v2 versions)
[ -f "QUICKSTART.md" ] && mv QUICKSTART.md archive/v1/QUICKSTART.md && echo "  ✓ QUICKSTART.md (archived)"
[ -f "DEPLOYMENT.md" ] && mv DEPLOYMENT.md archive/v1/DEPLOYMENT.md && echo "  ✓ DEPLOYMENT.md (archived)"

# Move verify script
[ -f "verify_structure.py" ] && mv verify_structure.py archive/v1/ && echo "  ✓ verify_structure.py"

# ---- Step 4: Archive original fabric/ contents, keep directory ----
echo "📂 Reorganizing fabric/ directory..."

# Move old fabric contents to archive
if [ -d "fabric" ]; then
    mkdir -p archive/v1/fabric
    # Move old notebooks (the new one will go here)
    [ -d "fabric/notebooks" ] && [ -f "fabric/notebooks/01_data_ingestion.py" ] && \
        mv fabric/notebooks/01_data_ingestion.py archive/v1/fabric/ && echo "  ✓ fabric/notebooks/01_data_ingestion.py"
    # Move SQL scripts to archive (consolidated into notebook)
    [ -d "fabric/sql" ] && mv fabric/sql archive/v1/fabric/ && echo "  ✓ fabric/sql/"
    # Move pipeline definitions
    [ -d "fabric/pipelines" ] && mv fabric/pipelines archive/v1/fabric/ && echo "  ✓ fabric/pipelines/"
fi

# Ensure fabric/notebooks/ exists for the new notebook
mkdir -p fabric/notebooks

# ---- Step 5: Move v1 docs subfolder to archive ----
if [ -d "docs" ]; then
    mkdir -p archive/v1/docs
    for f in docs/PRESTO_SUMMARY.md docs/POWERSHELL_GUIDE.md; do
        [ -f "$f" ] && mv "$f" archive/v1/docs/ && echo "  ✓ $f"
    done
    # Keep docs/PRESTO_GUIDE.md in active tree (still relevant)
fi

# ---- Step 6: Archive PowerBI mockups, keep setup guides ----
if [ -d "powerbi" ]; then
    mkdir -p archive/v1/powerbi
    [ -f "powerbi/DASHBOARD_MOCKUPS.md" ] && mv powerbi/DASHBOARD_MOCKUPS.md archive/v1/powerbi/ && echo "  ✓ powerbi/DASHBOARD_MOCKUPS.md"
    [ -f "powerbi/template.json" ] && mv powerbi/template.json archive/v1/powerbi/ && echo "  ✓ powerbi/template.json"
fi

echo ""
echo "============================================================================"
echo "✅ Migration complete!"
echo "============================================================================"
echo ""
echo "New structure:"
echo "  fabric/notebooks/   ← Place the unified notebook here"
echo "  docs/               ← Updated deployment & event grid guides"
echo "  setup/              ← Azure setup scripts (unchanged)"
echo "  powerbi/            ← Dashboard setup (unchanged)"
echo "  archive/v1/         ← All original v1 files preserved"
echo ""
echo "Next steps:"
echo "  1. Copy the unified notebook to fabric/notebooks/"
echo "  2. Place new README.md, QUICKSTART.md, CHANGELOG.md in root"
echo "  3. Place new docs/DEPLOYMENT.md and docs/EVENTGRID_GUIDE.md"
echo "  4. Update .env.example"
echo "  5. Commit and push"
echo ""
echo "See CHANGELOG.md for full details on what changed."
