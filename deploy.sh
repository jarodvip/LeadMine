#!/bin/bash

# LeadMine 安全部署脚本
# 使用方法: export SERVER_IP=your_ip && ./deploy.sh

set -euo pipefail

# 配置（从环境变量读取）
SERVER_IP="${SERVER_IP:-}"
SERVER_USER="${SERVER_USER:-deploy}"
APP_DIR="/opt/leadmine"
SSH_PORT="${SSH_PORT:-22}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查必要的环境变量
if [[ -z "$SERVER_IP" ]]; then
    echo -e "${RED}错误: 请设置 SERVER_IP 环境变量${NC}"
    echo "示例: export SERVER_IP=180.76.184.204"
    exit 1
fi

# 检查SSH密钥
if [[ ! -f ~/.ssh/id_rsa ]]; then
    echo -e "${RED}错误: 未找到SSH密钥 ~/.ssh/id_rsa${NC}"
    echo "请配置SSH密钥认证:"
    echo "  1. 生成密钥: ssh-keygen -t rsa -b 4096"
    echo "  2. 复制到服务器: ssh-copy-id ${SERVER_USER}@${SERVER_IP}"
    exit 1
fi

echo -e "${GREEN}========== LeadMine 生产部署 ==========${NC}"
echo "目标服务器: ${SERVER_IP}"
echo "部署用户: ${SERVER_USER}"
echo "应用目录: ${APP_DIR}"

# 1. 备份现有数据
echo -e "\n${YELLOW}[1/6] 备份现有数据...${NC}"
ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "
    if [ -d ${APP_DIR} ] && [ -f ${APP_DIR}/.env ]; then
        BACKUP_DIR=/opt/backups/leadmine-\$(date +%Y%m%d-%H%M%S)
        mkdir -p \${BACKUP_DIR}
        cd ${APP_DIR}
        source .env 2>/dev/null || true
        docker compose exec -T mysql mysqldump -u root -p\${MYSQL_ROOT_PASSWORD} \${MYSQL_DATABASE} > \${BACKUP_DIR}/database.sql 2>/dev/null || echo '数据库备份跳过'
        cp .env \${BACKUP_DIR}/ 2>/dev/null || true
        echo \"备份完成: \${BACKUP_DIR}\"
    else
        echo '首次部署，跳过备份'
    fi
"

# 2. 创建部署目录
echo -e "\n${YELLOW}[2/6] 创建服务器目录...${NC}"
ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "mkdir -p ${APP_DIR}/logs ${APP_DIR}/backup"

# 3. 上传配置文件
echo -e "\n${YELLOW}[3/6] 上传配置文件...${NC}"
scp -P ${SSH_PORT} docker-compose.prod.yml ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/docker-compose.yml

if [[ ! -f .env.prod ]]; then
    echo -e "${RED}错误: 未找到 .env.prod 文件${NC}"
    exit 1
fi

scp -P ${SSH_PORT} .env.prod ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/.env

# 4. 上传代码
echo -e "\n${YELLOW}[4/6] 上传应用代码...${NC}"
rsync -avz --delete \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='.env' \
    --exclude='.venv' \
    backend/ ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/backend/

rsync -avz --delete \
    --exclude='node_modules' \
    --exclude='.git' \
    web/dist/ ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/web/dist/

# 5. 构建并启动服务
echo -e "\n${YELLOW}[5/6] 构建并启动服务...${NC}"
ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "
    cd ${APP_DIR}
    docker compose down --remove-orphans 2>/dev/null || true
    docker compose pull
    docker compose up -d --build
    sleep 10
    docker compose ps
"

# 6. 健康检查
echo -e "\n${YELLOW}[6/6] 执行健康检查...${NC}"
HEALTH_STATUS=$(ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "
    cd ${APP_DIR}
    docker compose exec -T backend wget -qO- http://localhost:8000/health 2>/dev/null || echo 'FAILED'
")

if [[ "$HEALTH_STATUS" == *"ok"* ]] || [[ "$HEALTH_STATUS" == *"\"status\":\"ok\""* ]]; then
    echo -e "${GREEN}✓ 健康检查通过${NC}"
else
    echo -e "${RED}✗ 健康检查失败${NC}"
    exit 1
fi

echo -e "\n${GREEN}========== 部署完成！==========${NC}"
echo "访问地址: http://${SERVER_IP}"
echo ""
echo -e "${YELLOW}重要提醒:${NC}"
echo "1. 查看服务器日志获取临时密码"
echo "2. 立即登录并修改默认密码"
