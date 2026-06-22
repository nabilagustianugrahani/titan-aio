#!/usr/bin/env bash
# TITAN AIO — Deploy to HF Spaces
# Usage: ./setup_hf.sh <hf-username> <space-name>
set -euo pipefail
cd "$(dirname "$0")"

HF_USER="${1:?Usage: ./setup_hf.sh <hf-username> <space-name>}"
SPACE_NAME="${2:?Usage: ./setup_hf.sh <hf-username> <space-name>}"
SPACE_URL="https://huggingface.co/spaces/${HF_USER}/${SPACE_NAME}"

echo "TITAN AIO — Deploying to HF Spaces"
echo "  Space: ${SPACE_URL}"

# Check HF CLI
if ! command -v huggingface-cli &>/dev/null; then
    echo "Installing HuggingFace CLI..."
    pip install --quiet huggingface-hub
fi

# Login (will prompt if not already logged in)
huggingface-cli login

# Create the Space if it doesn't exist
echo "Creating/updating Space..."
huggingface-cli repo create "${SPACE_NAME}" --type space --sdk docker 2>/dev/null || true

# Clone the Space repo
WORK_DIR=$(mktemp -d)
git clone "https://huggingface.co/spaces/${HF_USER}/${SPACE_NAME}" "${WORK_DIR}" 2>/dev/null || {
    echo "Cloning failed, initializing fresh..."
    mkdir -p "${WORK_DIR}"
    cd "${WORK_DIR}"
    git init
    git remote add origin "https://huggingface.co/spaces/${HF_USER}/${SPACE_NAME}"
}
cd "${WORK_DIR}"

# Copy required files
cp "${OLDPWD}/Dockerfile.hf" "${WORK_DIR}/Dockerfile"
cp "${OLDPWD}/requirements.hf.txt" "${WORK_DIR}/"
cp -r "${OLDPWD}/titan" "${WORK_DIR}/"
cp -r "${OLDPWD}/MCP" "${WORK_DIR}/"
cp -r "${OLDPWD}/Services" "${WORK_DIR}/"
cp -r "${OLDPWD}/Database" "${WORK_DIR}/"
cp -r "${OLDPWD}/Workers" "${WORK_DIR}/"
cp "${OLDPWD}/pyproject.toml" "${WORK_DIR}/"

# Create .gitignore
cat > "${WORK_DIR}/.gitignore" << 'EOF'
__pycache__/
*.pyc
.env
data/
*.egg-info/
.mypy_cache/
.pytest_cache/
.ruff_cache/
EOF

# Create README.md with HF Space metadata
cat > "${WORK_DIR}/README.md" << EOF
---
title: TITAN AIO
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# TITAN AIO — Autonomous Affiliate Intelligence

FastMCP server with 48 tools. GPU work runs on Modal (A100/T4).
EOF

# Push to HF
git add -A
git commit -m "Deploy TITAN AIO to HF Spaces" || echo "No changes to commit"
git push origin main

# Cleanup
cd "${OLDPWD}"
rm -rf "${WORK_DIR}"

echo ""
echo "Deploy complete!"
echo "  Space URL: ${SPACE_URL}"
echo "  MCP endpoint: ${SPACE_URL}/mcp"
echo "  Dashboard: ${SPACE_URL}/dashboard"
echo ""
echo "Set these env vars in HF Space settings:"
echo "  DATABASE_URL, NOTION_TOKEN, NOTION_CAMPAIGN_DB,"
echo "  NOTION_KNOWLEDGE_DB, NOTION_TASKS_DB, MONGODB_URI,"
echo "  GDRIVE_CREDENTIALS_FILE, GDRIVE_FOLDER_ID, HF_TOKEN,"
echo "  GOOGLE_AI_API_KEY, SCRAPINGBEE_API_KEY"
echo ""
echo "Set up keep-alive cron at cron-job.org:"
echo "  URL: ${SPACE_URL}/keepalive"
echo "  Interval: 5 minutes"
