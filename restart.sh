#!/bin/bash
# Quiz App 重启脚本（N150 生产环境，随 CI 产物分发）
# venv/models 放 $HOME 下，避免被 deploy-agent 的 rsync --delete 清除（与 deploy-agent.sh 同策略）

PORT=9200
LOG=/tmp/quiz-app.log
DIR="$HOME/quiz-app"
VENV="$HOME/quiz-app-venv"
MODELS="$HOME/quiz-app-models"

# 服务专属配置（.env 受 rsync --exclude 保护，跨版本持久）
[ -f "$DIR/.env" ] && set -a && . "$DIR/.env" && set +a

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

# 防并发：同一时间只允许一个 restart 实例
# （deploy-agent cron 健康检查与 webhook 部署可能重叠触发，并发 pip install 会损坏 venv）
LOCK_FILE=/tmp/quiz-app-restart.lock
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  log "另一个 restart 正在运行，跳过"
  exit 0
fi

# 杀旧进程
PID=$(lsof -ti:$PORT 2>/dev/null)
if [ -n "$PID" ]; then
  kill $PID 2>/dev/null
  sleep 1
  kill -9 $PID 2>/dev/null
  log "已停止旧进程 PID $PID"
fi

cd "$DIR" || exit 1

# 首次部署：创建 venv + 安装依赖（一次性，需几分钟）
if [ ! -x "$VENV/bin/uvicorn" ]; then
  log "创建 venv 并安装依赖（首次部署，需几分钟）..."
  rm -rf "$VENV"
  python3 -m venv "$VENV" || { echo "venv 创建失败" >> "$LOG"; exit 1; }
  "$VENV/bin/pip" install -q --upgrade pip >> "$LOG" 2>&1
  for idx in "https://pypi.org/simple" "https://pypi.tuna.tsinghua.edu.cn/simple" "https://mirrors.aliyun.com/pypi/simple/"; do
    log "pip install -i $idx"
    if "$VENV/bin/pip" install -q -r "$DIR/requirements.txt" -i "$idx" >> "$LOG" 2>&1; then
      break
    fi
  done
  if [ ! -x "$VENV/bin/uvicorn" ]; then
    echo "依赖安装失败，查看 $LOG" >> "$LOG"
    exit 1
  fi
  "$VENV/bin/pip" freeze > "$VENV/.installed.txt" 2>/dev/null || true
  log "依赖安装完成"
fi

# 环境变量（与 start_backend.sh 对齐）
export DATABASE_URL="sqlite+aiosqlite:///$DIR/data/quiz.db"
export LIGHTRAG_DIR="$DIR/data/lightrag"
export CHROMA_PERSIST_DIR="$DIR/data/chroma"
export UPLOAD_DIR="$DIR/data/uploads"
export VAULT_DIR="${VAULT_DIR:-$DIR/../vault}"
export STATIC_DIR="$DIR/static"
export HF_HOME="$MODELS"
export HF_ENDPOINT="https://hf-mirror.com"

# 用 systemd-run 起独立 scope，脱离 cron cgroup（复用 WeMusic 经验）
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
if command -v systemd-run >/dev/null 2>&1; then
  if ! loginctl show-user "$(id -un)" --property=Linger 2>/dev/null | grep -q 'Linger=yes'; then
    loginctl enable-linger "$(id -un)" >/dev/null 2>&1
    sleep 1
  fi
  systemctl --user stop quiz-app.scope >/dev/null 2>&1
  systemctl --user reset-failed quiz-app.scope >/dev/null 2>&1
  nohup systemd-run --user --scope --collect --unit="quiz-app" -- "$VENV/bin/uvicorn" backend.main:app --host 0.0.0.0 --port "$PORT" > "$LOG" 2>&1 &
else
  nohup "$VENV/bin/uvicorn" backend.main:app --host 0.0.0.0 --port "$PORT" > "$LOG" 2>&1 &
fi

sleep 3
NEWPID=$(lsof -ti:$PORT 2>/dev/null)
if [ -n "$NEWPID" ]; then
  log "启动成功 PID $NEWPID port $PORT"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] started PID $NEWPID port $PORT"
else
  log "启动失败"
  echo "启动失败，查看 $LOG"
  tail -20 "$LOG"
fi
