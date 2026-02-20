#!/bin/bash

# LeadMine HTTPS 本地部署脚本
# 用于本地测试 Nginx + HTTPS 配置

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== LeadMine HTTPS 本地部署 ===${NC}"
echo ""

# 检查目录
cd "$(dirname "$0")"

# 1. 检查必要文件
echo -e "${YELLOW}[1/5] 检查必要文件...${NC}"

if [ ! -f "nginx/ssl/localhost/fullchain.pem" ]; then
    echo -e "${YELLOW}生成自签名 SSL 证书...${NC}"
    ./setup-ssl.sh self-signed
fi

if [ ! -f "web/dist/index.html" ]; then
    echo -e "${YELLOW}构建前端...${NC}"
    cd web
    npm run build
    cd ..
fi

echo -e "${GREEN}✅ 文件检查完成${NC}"

# 2. 设置环境变量
echo -e "${YELLOW}[2/5] 设置环境变量...${NC}"

export JWT_SECRET="local-https-test-secret-key-$(openssl rand -base64 32)"
export MYSQL_ROOT_PASSWORD="leadmine_root_$(openssl rand -base64 12)"
export MYSQL_PASSWORD="leadmine_$(openssl rand -base64 12)"
export REDIS_PASSWORD="redis_$(openssl rand -base64 12)"

echo "JWT_SECRET=${JWT_SECRET:0:20}..."
echo "MySQL Root Password: ${MYSQL_ROOT_PASSWORD:0:20}..."

# 3. 启动服务
echo -e "${YELLOW}[3/5] 启动服务...${NC}"

docker compose -f docker-compose.local-https.yml down 2>/dev/null || true

docker compose -f docker-compose.local-https.yml up -d --build

echo -e "${GREEN}✅ 服务已启动${NC}"

# 4. 等待服务就绪
echo -e "${YELLOW}[4/5] 等待服务就绪...${NC}"

sleep 5

# 检查服务状态
for i in {1..30}; do
    if curl -s -k https://localhost/nginx-health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Nginx 运行正常${NC}"
        break
    fi
    echo "  等待 Nginx 启动... ($i/30)"
    sleep 2
done

# 5. 测试 HTTPS
echo -e "${YELLOW}[5/5] 测试 HTTPS 连接...${NC}"

echo ""
echo "测试 HTTPS 健康检查:"
if curl -s -k https://localhost/nginx-health; then
    echo -e "${GREEN}✅ Nginx HTTPS 正常${NC}"
else
    echo -e "${RED}❌ Nginx HTTPS 测试失败${NC}"
fi

echo ""
echo "测试后端 API:"
if curl -s -k https://localhost/health 2>/dev/null | grep -q "healthy"; then
    echo -e "${GREEN}✅ 后端 API HTTPS 正常${NC}"
else
    echo -e "${YELLOW}⚠️  后端 API 可能需要更多时间启动${NC}"
fi

echo ""
echo -e "${GREEN}=== 部署完成 ===${NC}"
echo ""
echo "访问地址:"
echo "  HTTPS: https://localhost"
echo "  HTTP:  http://localhost (自动重定向到 HTTPS)"
echo ""
echo -e "${YELLOW}⚠️  注意: 由于是自签名证书，浏览器会显示安全警告${NC}"
echo "    请点击"高级" -> "继续访问" (这是正常的)"
echo ""
echo "常用命令:"
echo "  查看日志: docker compose -f docker-compose.local-https.yml logs -f"
echo "  停止服务: docker compose -f docker-compose.local-https.yml down"
echo "  重启服务: docker compose -f docker-compose.local-https.yml restart"
echo ""
