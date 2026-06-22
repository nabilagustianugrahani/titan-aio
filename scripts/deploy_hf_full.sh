#!/usr/bin/env bash
# TITAN AIO — Full HF Deployment (no VPS needed)
#
# Deploys:
# 1. HF Space (main app)
# 2. Modal workers (GPU)
# 3. KeepAlive (systemd)
#
# Usage:
#   ./scripts/deploy_hf_full.sh
#
# Requirements:
#   - hf CLI authenticated (hf auth login)
#   - modal CLI authenticated (modal token set)
set -euo pipefail

echo "🚀 TITAN AIO — Full HF Deployment"
echo "=================================="

# Step 1: Deploy HF Space
echo ""
echo "📦 Step 1: Deploy HF Space..."
if command -v hf &>/dev/null; then
    cd /tmp && rm -rf titan-hf-deploy && mkdir titan-hf-deploy && cd titan-hf-deploy
    cp /home/Aa/ugc/Dockerfile.hf Dockerfile
    cp /home/Aa/ugc/requirements.hf.txt .
    cp -r /home/Aa/ugc/titan .
    cp -r /home/Aa/ugc/MCP .
    cp -r /home/Aa/ugc/Services .
    cp -r /home/Aa/ugc/Database .
    cp -r /home/Aa/ugc/Workers .
    cp /home/Aa/ugc/pyproject.toml .
    hf upload Badjals/hehehe . --repo-type space
    cd /home/Aa/ugc
    rm -rf /tmp/titan-hf-deploy
    echo "✅ HF Space deployed!"
else
    echo "❌ hf CLI not found. Run: hf auth login"
    exit 1
fi

# Step 2: Deploy Modal workers
echo ""
echo "📦 Step 2: Deploy Modal workers..."
if command -v modal &>/dev/null; then
    modal deploy /home/Aa/ugc/Workers/modal_a100.py
    modal deploy /home/Aa/ugc/Workers/modal_image.py
    echo "✅ Modal workers deployed!"
else
    echo "⚠️  modal CLI not found. Deploy manually:"
    echo "   modal deploy Workers/modal_a100.py"
    echo "   modal deploy Workers/modal_image.py"
fi

# Step 3: Setup KeepAlive
echo ""
echo "📦 Step 3: Setup KeepAlive..."
if [ -f /etc/systemd/system/titan-keepalive.service ]; then
    sudo systemctl restart titan-keepalive
    echo "✅ KeepAlive restarted!"
else
    sudo cp /home/Aa/ugc/scripts/titan-keepalive.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable titan-keepalive
    sudo systemctl start titan-keepalive
    echo "✅ KeepAlive installed and started!"
fi

echo ""
echo "=================================="
echo "✅ Deployment complete!"
echo ""
echo "HF Space: https://badjals-hehehe.hf.space"
echo "Dashboard: https://badjals-hehehe.hf.space/dashboard"
echo "Health: https://badjals-hehehe.hf.space/health"
echo ""
echo "Modal workers: Deployed"
echo "KeepAlive: Running (systemd)"
