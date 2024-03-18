#!/bin/bash
set -euo pipefail

WORKERS=${WORKERS:-1}
WORKER_CLASS=${WORKER_CLASS:-gevent}
ACCESS_LOG=${ACCESS_LOG:--}
ERROR_LOG=${ERROR_LOG:--}
WORKER_TEMP_DIR=${WORKER_TEMP_DIR:-/dev/shm}
SECRET_KEY=${SECRET_KEY:-}

# Check that a .ctfd_secret_key file or SECRET_KEY envvar is set
if [ ! -f .ctfd_secret_key ] && [ -z "$SECRET_KEY" ]; then
    if [ $WORKERS -gt 1 ]; then
        echo "[ ERROR ] 您配置为使用超过 1 个工作线程。"
        echo "[ ERROR ] 为此，您必须定义 SECRET_KEY 环境变量或创建 .ctfd_secret_key 文件。"
        echo "[ ERROR ] 正在退出..."
        exit 1
    fi
fi

# Ensures that the database is available
python ping.py

# Initialize database
python manage.py db upgrade

# Start CTFd
echo "[CTFd] 正在启动CTFd"
exec gunicorn 'CTFd:create_app()' \
    --bind '0.0.0.0:8000' \
    --workers $WORKERS \
    --worker-tmp-dir "$WORKER_TEMP_DIR" \
    --worker-class "$WORKER_CLASS" \
    --access-logfile "$ACCESS_LOG" \
    --error-logfile "$ERROR_LOG" \
    --timeout 600 \
    --access-logformat '%(t)s (IP:%(h)s) 访问:"%(r)s" 响应状态:%(s)s Referer:"%(f)s"'
