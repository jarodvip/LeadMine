#!/bin/bash

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查当前用户是否为 root，避免安装阶段权限不足。
require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "${RED}错误: 请使用 root 运行此脚本${NC}"
        exit 1
    fi
}

# 安装系统基础依赖，供 Docker 仓库、证书申请和部署同步使用。
install_base_packages() {
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release rsync certbot
}

# 配置 Docker 官方 APT 仓库，确保 Debian 12 可以安装 Compose plugin。
configure_docker_repository() {
    install -m 0755 -d /etc/apt/keyrings
    install -m 0755 -d /etc/apt/sources.list.d

    if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
        curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg
    fi

    . /etc/os-release
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian ${VERSION_CODENAME} stable" \
        > /etc/apt/sources.list.d/docker.list
}

# 安装 Docker 运行时和 Compose plugin，作为后续发布的基础环境。
install_docker_runtime() {
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker --now
}

# 预创建应用目录，避免首次发布时 bind mount 目录缺失。
prepare_application_directories() {
    mkdir -p /opt/leadmine/backup
    mkdir -p /opt/leadmine/backend
    mkdir -p /opt/leadmine/web/dist
    mkdir -p /opt/leadmine/nginx/logs
    mkdir -p /opt/leadmine/nginx/certbot-data
}

echo -e "${GREEN}=== LeadMine Debian 12 初始化 ===${NC}"

require_root
install_base_packages
configure_docker_repository
install_docker_runtime
prepare_application_directories

echo -e "${GREEN}初始化完成${NC}"
echo "docker version: $(docker --version)"
echo "docker compose version: $(docker compose version --short)"
echo "certbot version: $(certbot --version)"
