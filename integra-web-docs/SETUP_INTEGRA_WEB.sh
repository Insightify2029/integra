#!/bin/bash
# ============================================
# INTEGRA Web - One-Click Setup Script
# ============================================
# Run this on your local machine:
#   chmod +x SETUP_INTEGRA_WEB.sh && ./SETUP_INTEGRA_WEB.sh
# ============================================

set -e

echo "🚀 Setting up integra-web repository..."

# 1. Clone the empty integra-web repo
git clone https://github.com/Insightify2029/integra-web.git
cd integra-web

# 2. Download docs from integra repo (specific branch)
git clone --depth 1 -b claude/integra-frappe-migration-o9NoR https://github.com/Insightify2029/integra.git _temp

# 3. Copy files to the right places
cp _temp/integra-web-docs/CLAUDE.md .
cp -r _temp/integra-web-docs/docs .

# 4. Clean up temp folder
rm -rf _temp

# 5. Commit and push
git add .
git commit -m "docs: initialize INTEGRA Web project documentation"
git push origin main

echo ""
echo "✅ Done! integra-web is ready at: https://github.com/Insightify2029/integra-web"
echo ""
