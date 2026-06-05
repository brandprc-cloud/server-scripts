#!/bin/bash
# backup-to-github.sh
# Бэкапит конфиг Claude и память в этот же репо (server-scripts → GitHub)
set -e

REPO_DIR="/home/claudeuser/projects/server-scripts"
CLAUDE_DIR="/home/claudeuser/.claude"
MEMORY_DIR="$CLAUDE_DIR/projects/-home-claudeuser/memory"

cd "$REPO_DIR"

# --- Claude config ---
mkdir -p claude-config
cp "$CLAUDE_DIR/settings.json" ./claude-config/settings.json 2>/dev/null || true
cp "$CLAUDE_DIR/statusline-command.sh" ./claude-config/statusline-command.sh 2>/dev/null || true

# --- Claude memory ---
mkdir -p claude-memory
cp "$MEMORY_DIR"/*.md ./claude-memory/ 2>/dev/null || true

# --- Главный CLAUDE.md сервера ---
cp /home/claudeuser/CLAUDE.md ./CLAUDE.md 2>/dev/null || true

# --- Пуш ---
git add \
  claude-config/settings.json \
  claude-config/statusline-command.sh \
  claude-memory/ \
  CLAUDE.md

if git diff --cached --quiet; then
    echo "$(date): nothing changed, skip"
    exit 0
fi

git commit -m "backup $(date '+%Y-%m-%d %H:%M')"
GIT_SSH_COMMAND="ssh -i /home/claudeuser/.ssh/github_brandprc" git push origin main
echo "$(date): backup pushed to brandprc-cloud/server-scripts"
