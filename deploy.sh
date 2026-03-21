#!/bin/bash
# =====================================================
# Deploy Financial Planning Suite to TerraMaster NAS
# Usage: bash deploy.sh
# =====================================================
set -e

NAS_IP="192.168.68.102"
NAS_USER="Gonzik"
NAS_SSH_PORT="9222"
NAS_APP_DIR="/Volume1/docker/financial-planner"
COMPOSE_FILE="docker-compose-local.yml"

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  💰 Deploying Financial Planning Suite to NAS         ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Files to deploy
FILES="FinancialApp_V14.py Dockerfile docker-compose.yml docker-compose-local.yml requirements.txt streamlit_config.toml"

echo "📦 Copying files to NAS..."
for f in $FILES; do
    if [ -f "$f" ]; then
        echo "   → $f"
        scp -P $NAS_SSH_PORT "$f" ${NAS_USER}@${NAS_IP}:${NAS_APP_DIR}/ 2>/dev/null || {
            echo "   ⚠️  SCP failed for $f, trying SSH pipe..."
            cat "$f" | ssh -p $NAS_SSH_PORT ${NAS_USER}@${NAS_IP} "cat > ${NAS_APP_DIR}/$f"
        }
    else
        echo "   ⚠️  MISSING: $f"
    fi
done

echo ""
echo "🔨 Building and starting on NAS..."
ssh -p $NAS_SSH_PORT ${NAS_USER}@${NAS_IP} << REMOTE
    cd ${NAS_APP_DIR}
    mkdir -p app-data/households
    docker-compose -f ${COMPOSE_FILE} build --no-cache
    docker-compose -f ${COMPOSE_FILE} up -d
    echo ""
    echo "Container status:"
    docker-compose -f ${COMPOSE_FILE} ps
REMOTE

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  ✅ Deployed! Open http://${NAS_IP}:8501              ║"
echo "╚═══════════════════════════════════════════════════════╝"
