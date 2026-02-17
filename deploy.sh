#!/bin/bash

# LeadMine 云服务器部署脚本

set -e

# 服务器配置
SERVER_IP="180.76.184.204"
SSH_PORT="22"
SERVER_USER="root"
SERVER_PASSWORD="asd456JKL!"

# 应用配置
APP_NAME="leadmine"
APP_DIR="/opt/leadmine"
DOMAIN="${SERVER_IP}"

echo "========== LeadMine 部署开始 =========="
echo "目标服务器: ${SERVER_IP}:${SSH_PORT}"
echo "应用目录: ${APP_DIR}"

# 1. 安装Docker（如未安装）
echo "[1/7] 检查并安装Docker..."
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "
    if ! command -v docker &> /dev/null; then
        echo '安装Docker...'
        apt-get update
        apt-get install -y ca-certificates curl gnupg lsb-release
        
        # 添加Docker GPG key
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        
        # 添加Docker仓库
        echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bullseye stable' > /etc/apt/sources.list.d/docker.list
        
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        
        # 启动Docker
        systemctl start docker
        systemctl enable docker
        
        echo 'Docker安装完成'
    else
        echo 'Docker已安装'
    fi
    
    docker --version
    docker-compose --version
"

# 2. 创建部署目录
echo "[2/7] 创建服务器目录..."
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "
    mkdir -p ${APP_DIR}
    mkdir -p ${APP_DIR}/logs
    echo '目录创建完成'
"

# 3. 上传 docker-compose.yml
echo "[3/7] 上传配置文件..."
sshpass -p "${SERVER_PASSWORD}" scp -o StrictHostKeyChecking=no -P ${SSH_PORT} docker-compose.yml ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/

# 4. 上传后端代码
echo "[4/7] 上传后端代码..."
sshpass -p "${SERVER_PASSWORD}" scp -o StrictHostKeyChecking=no -P ${SSH_PORT} -r backend ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/

# 5. 上传前端原型
echo "[5/7] 上传前端文件..."
sshpass -p "${SERVER_PASSWORD}" scp -o StrictHostKeyChecking=no -P ${SSH_PORT} -r web ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/

# 6. 启动Docker服务
echo "[6/7] 启动Docker服务..."
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "
    cd ${APP_DIR}
    
    # 拉取镜像
    echo '拉取MySQL镜像...'
    docker pull mysql:8.0 || true
    
    echo '拉取Redis镜像...'
    docker pull redis:7-alpine || true
    
    echo '启动服务...'
    docker-compose up -d
    
    echo '等待服务启动...'
    sleep 40
    
    # 检查容器状态
    docker-compose ps
"

# 7. 验证部署
echo "[7/7] 验证部署..."
sleep 15

# 检查服务状态
echo ""
echo "========== 检查服务状态 =========="
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "
    docker-compose ps
    echo ''
    echo '检查后端API...'
    curl -s http://localhost:8000/ || echo '后端可能需要更多时间启动'
"

echo ""
echo "========== 部署完成 =========="
echo "后端API: http://${DOMAIN}:8000"
echo "API文档: http://${DOMAIN}:8000/docs"
echo "MySQL:   ${DOMAIN}:3306"
echo ""
echo "默认账户: admin / admin123"
echo ""
echo "查看日志: cd ${APP_DIR} && docker-compose logs -f"
echo "停止服务: cd ${APP_DIR} && docker-compose down"
