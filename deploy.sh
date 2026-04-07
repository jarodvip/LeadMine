#!/bin/bash

set -euo pipefail

SERVER_IP="${SERVER_IP:-}"
SERVER_USER="${SERVER_USER:-root}"
APP_DIR="${APP_DIR:-/opt/leadmine}"
SSH_PORT="${SSH_PORT:-22}"
COMPOSE_SOURCE="${COMPOSE_SOURCE:-docker-compose.https.yml}"
PUBLIC_HEALTHCHECK_URL="${PUBLIC_HEALTHCHECK_URL:-https://lbu.me/health}"
PUBLIC_DOMAIN="${PUBLIC_DOMAIN:-lbu.me}"
CERTIFICATE_DOMAIN="${CERTIFICATE_DOMAIN:-lbu.me}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-false}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SSH_OPTS=(-o StrictHostKeyChecking=no -o ServerAliveInterval=60 -p "${SSH_PORT}")
SCP_OPTS=(-o StrictHostKeyChecking=no -o ServerAliveInterval=60 -P "${SSH_PORT}")
RSYNC_RSH="ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -p ${SSH_PORT}"
TEMP_ENV_FILE=""

# 检查本地依赖是否齐全，避免发布过程中才暴露缺命令问题。
ensure_local_requirements() {
    local command_name

    for command_name in ssh scp rsync curl python3; do
        if ! command -v "${command_name}" >/dev/null 2>&1; then
            echo -e "${RED}错误: 缺少本地依赖 ${command_name}${NC}"
            exit 1
        fi
    done
}

# 清理发布时生成的临时环境文件，避免凭据副本残留在本机。
cleanup_temp_files() {
    if [[ -n "${TEMP_ENV_FILE}" && -f "${TEMP_ENV_FILE}" ]]; then
        rm -f "${TEMP_ENV_FILE}"
    fi
}

# 生成远端专用 .env，把密码安全编码进连接串，避免特殊字符破坏 URL 解析。
build_remote_env_file() {
    TEMP_ENV_FILE="$(mktemp)"

    python3 - ".env.prod" "${TEMP_ENV_FILE}" <<'PY'
import sys
from pathlib import Path
from urllib.parse import quote

source_path = Path(sys.argv[1])
target_path = Path(sys.argv[2])
source_text = source_path.read_text(encoding="utf-8")
values = {}

for line in source_text.splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in line:
        continue

    key, value = line.split("=", 1)
    values[key] = value

values["DATABASE_URL"] = (
    f"mysql+pymysql://{values['MYSQL_USER']}:"
    f"{quote(values['MYSQL_PASSWORD'], safe='')}@mysql:3306/{values['MYSQL_DATABASE']}"
)
values["REDIS_URL"] = (
    f"redis://:{quote(values['REDIS_PASSWORD'], safe='')}@redis:6379/0"
)

rendered_lines = []
for line in source_text.splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in line:
        rendered_lines.append(line)
        continue

    key, _ = line.split("=", 1)
    rendered_lines.append(f"{key}={values[key]}")

target_path.write_text("\n".join(rendered_lines) + "\n", encoding="utf-8")
PY
}

trap cleanup_temp_files EXIT

# 检查发布输入是否完整，避免把不完整产物同步到服务器。
ensure_local_artifacts() {
    if [[ -z "${SERVER_IP}" ]]; then
        echo -e "${RED}错误: 请设置 SERVER_IP 环境变量${NC}"
        echo "示例: export SERVER_IP=152.32.189.185"
        exit 1
    fi

    if [[ ! -f "${COMPOSE_SOURCE}" ]]; then
        echo -e "${RED}错误: 未找到编排文件 ${COMPOSE_SOURCE}${NC}"
        exit 1
    fi

    if [[ ! -f ".env.prod" ]]; then
        echo -e "${RED}错误: 未找到 .env.prod 文件${NC}"
        exit 1
    fi

    if [[ ! -f "web/dist/index.html" ]]; then
        echo -e "${RED}错误: 未找到前端构建产物 web/dist/index.html${NC}"
        echo "请先执行: cd web && npm run build"
        exit 1
    fi
}

# 检查服务器运行时和证书前置条件，避免把发布失败归因到应用代码。
check_remote_runtime() {
    ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_IP}" "
        if ! command -v docker >/dev/null 2>&1; then
            echo '服务器未安装 Docker，请先在服务器执行 ./init-server.sh'
            exit 1
        fi
        if ! docker compose version >/dev/null 2>&1; then
            echo '服务器缺少 Docker Compose plugin，请先在服务器执行 ./init-server.sh'
            exit 1
        fi
        if [ ! -f /etc/letsencrypt/live/${CERTIFICATE_DOMAIN}/fullchain.pem ]; then
            echo '服务器未找到正式证书，请先执行 ./setup-ssl.sh letsencrypt lbu.me www.lbu.me admin@example.com'
            exit 1
        fi
    "
}

# 备份线上数据库和环境变量，给失败回滚留出最小恢复点。
backup_remote_data() {
    if [[ "${BACKUP_BEFORE_DEPLOY}" != "true" ]]; then
        echo "跳过数据库备份（设置 BACKUP_BEFORE_DEPLOY=true 可启用）"
        return
    fi

    ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_IP}" "
        if [ -d ${APP_DIR} ] && [ -f ${APP_DIR}/.env ]; then
            BACKUP_DIR=/opt/backups/leadmine-\$(date +%Y%m%d-%H%M%S)
            mkdir -p \${BACKUP_DIR}
            MYSQL_DATABASE=\$(grep '^MYSQL_DATABASE=' ${APP_DIR}/.env | cut -d'=' -f2-)
            MYSQL_ROOT_PASSWORD=\$(grep '^MYSQL_ROOT_PASSWORD=' ${APP_DIR}/.env | cut -d'=' -f2-)

            if docker ps --format '{{.Names}}' | grep -qx leadmine_mysql; then
                docker exec leadmine_mysql mysqldump -u root -p\"\${MYSQL_ROOT_PASSWORD}\" \"\${MYSQL_DATABASE}\" > \${BACKUP_DIR}/database.sql 2>/dev/null || echo '数据库备份跳过'
            else
                echo '数据库容器不存在，跳过数据库备份'
            fi

            cp ${APP_DIR}/.env \${BACKUP_DIR}/ 2>/dev/null || true
            echo \"备份完成: \${BACKUP_DIR}\"
        else
            echo '首次部署，跳过备份'
        fi
    "
}

# 创建远端目录，确保 bind mount 和代码同步路径存在。
prepare_remote_directories() {
    ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_IP}" "
        mkdir -p ${APP_DIR} \
                 ${APP_DIR}/backend \
                 ${APP_DIR}/web \
                 ${APP_DIR}/nginx
    "
}

# 上传编排、环境变量、后端代码、前端产物和 Nginx 配置。
sync_release_files() {
    scp "${SCP_OPTS[@]}" "${COMPOSE_SOURCE}" "${SERVER_USER}@${SERVER_IP}:${APP_DIR}/docker-compose.yml"
    scp "${SCP_OPTS[@]}" "${TEMP_ENV_FILE}" "${SERVER_USER}@${SERVER_IP}:${APP_DIR}/.env"

    rsync -avz --delete -e "${RSYNC_RSH}" \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.git' \
        --exclude='.env' \
        --exclude='.venv' \
        --exclude='.pytest_cache' \
        --exclude='tests' \
        --exclude='logs' \
        --exclude='*.db' \
        backend/ "${SERVER_USER}@${SERVER_IP}:${APP_DIR}/backend/"

    rsync -avz --delete -e "${RSYNC_RSH}" \
        --exclude='node_modules' \
        --exclude='.git' \
        web/dist/ "${SERVER_USER}@${SERVER_IP}:${APP_DIR}/web/dist/"

    rsync -avz --delete -e "${RSYNC_RSH}" \
        --exclude='.git' \
        nginx/ "${SERVER_USER}@${SERVER_IP}:${APP_DIR}/nginx/"
}

# 启动远端容器栈并输出服务状态，便于快速确认启动结果。
start_remote_services() {
    ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_IP}" "
        cd ${APP_DIR}
        docker compose up -d --build --remove-orphans
        docker compose up -d --no-deps --force-recreate nginx
        docker compose exec -T nginx sh -lc 'mkdir -p /var/log/nginx && touch /var/log/nginx/error.log /var/log/nginx/access.log && nginx -t' || { docker compose logs nginx --tail=50; exit 1; }
        docker compose ps
    "
}

# 轮询公开 HTTPS 健康检查，确认域名入口已经可用。
verify_public_healthcheck() {
    local attempt

    for attempt in {1..20}; do
        if curl --fail --silent --show-error "${PUBLIC_HEALTHCHECK_URL}" >/dev/null; then
            echo -e "${GREEN}✓ 公开 HTTPS 健康检查通过${NC}"
            return 0
        fi

        echo "等待公开 HTTPS 健康检查就绪... (${attempt}/20)"
        sleep 3
    done

    echo -e "${RED}✗ 公开 HTTPS 健康检查失败: ${PUBLIC_HEALTHCHECK_URL}${NC}"
    exit 1
}

echo -e "${GREEN}========== LeadMine 生产部署 ==========${NC}"
echo "目标服务器: ${SERVER_IP}"
echo "部署用户: ${SERVER_USER}"
echo "应用目录: ${APP_DIR}"
echo "健康检查: ${PUBLIC_HEALTHCHECK_URL}"

ensure_local_requirements
ensure_local_artifacts
build_remote_env_file
check_remote_runtime
backup_remote_data
prepare_remote_directories
sync_release_files
start_remote_services
verify_public_healthcheck

echo -e "${GREEN}========== 部署完成 ==========${NC}"
echo "访问地址: https://${PUBLIC_DOMAIN}"
