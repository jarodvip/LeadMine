#!/bin/bash

# LeadMine HTTPS 配置验证脚本
# 无需 Docker，仅验证配置文件和证书

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== LeadMine HTTPS 配置验证 ===${NC}"
echo ""

ERRORS=0
WARNINGS=0

# 1. 检查必要文件
echo -e "${YELLOW}[1/7] 检查必要文件...${NC}"

REQUIRED_FILES=(
    "nginx/nginx.conf"
    "docker-compose.local-https.yml"
    "docker-compose.https.yml"
    "setup-ssl.sh"
    "deploy-https-local.sh"
    "web/dist/index.html"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - 文件不存在"
        ((ERRORS++))
    fi
done

# 2. 检查 SSL 证书
echo ""
echo -e "${YELLOW}[2/7] 检查 SSL 证书...${NC}"

if [ -f "nginx/ssl/localhost/fullchain.pem" ]; then
    echo "  ✅ SSL 证书文件存在"
    
    # 检查证书有效期
    CERT_END=$(openssl x509 -in nginx/ssl/localhost/fullchain.pem -noout -enddate 2>/dev/null | cut -d= -f2)
    if [ -n "$CERT_END" ]; then
        echo "  ✅ 证书有效期至: $CERT_END"
    fi
    
    # 检查证书域名
    CERT_SUBJECT=$(openssl x509 -in nginx/ssl/localhost/fullchain.pem -noout -subject 2>/dev/null)
    echo "  📋 $CERT_SUBJECT"
else
    echo "  ❌ SSL 证书不存在"
    ((ERRORS++))
fi

# 3. 检查 Nginx 配置语法 (如果安装了 nginx)
echo ""
echo -e "${YELLOW}[3/7] 检查 Nginx 配置...${NC}"

if command -v nginx &> /dev/null; then
    if nginx -t -c nginx/nginx.conf 2>&1 | grep -q "successful"; then
        echo "  ✅ Nginx 配置语法正确"
    else
        echo "  ❌ Nginx 配置有语法错误"
        nginx -t -c nginx/nginx.conf 2>&1 | sed 's/^/    /'
        ((ERRORS++))
    fi
else
    echo "  ⚠️  Nginx 未安装，跳过语法检查"
    ((WARNINGS++))
fi

# 4. 检查关键配置项
echo ""
echo -e "${YELLOW}[4/7] 检查关键配置项...${NC}"

# 检查 HTTPS 配置
if grep -q "listen 443 ssl" nginx/nginx.conf; then
    echo "  ✅ HTTPS (443) 端口配置"
else
    echo "  ❌ HTTPS 端口未配置"
    ((ERRORS++))
fi

# 检查 HTTP 重定向
if grep -q "return 301 https" nginx/nginx.conf; then
    echo "  ✅ HTTP 到 HTTPS 重定向"
else
    echo "  ⚠️  HTTP 重定向未配置"
    ((WARNINGS++))
fi

# 检查 SSL 证书路径
if grep -q "ssl_certificate" nginx/nginx.conf; then
    echo "  ✅ SSL 证书路径配置"
else
    echo "  ❌ SSL 证书路径未配置"
    ((ERRORS++))
fi

# 检查 API 代理
if grep -q "location /api" nginx/nginx.conf; then
    echo "  ✅ API 反向代理配置"
else
    echo "  ❌ API 代理未配置"
    ((ERRORS++))
fi

# 检查安全头
if grep -q "X-Frame-Options" nginx/nginx.conf; then
    echo "  ✅ 安全响应头配置"
else
    echo "  ⚠️  安全响应头未配置"
    ((WARNINGS++))
fi

# 5. 检查 Docker Compose 配置
echo ""
echo -e "${YELLOW}[5/7] 检查 Docker Compose 配置...${NC}"

if command -v docker &> /dev/null; then
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        echo "  ✅ Docker Compose 可用"
        
        # 验证 compose 文件
        if docker-compose -f docker-compose.local-https.yml config > /dev/null 2>&1; then
            echo "  ✅ docker-compose.local-https.yml 格式正确"
        else
            echo "  ❌ docker-compose.local-https.yml 格式错误"
            ((ERRORS++))
        fi
        
        if docker-compose -f docker-compose.https.yml config > /dev/null 2>&1; then
            echo "  ✅ docker-compose.https.yml 格式正确"
        else
            echo "  ❌ docker-compose.https.yml 格式错误"
            ((ERRORS++))
        fi
    else
        echo "  ⚠️  Docker Compose 未安装"
        ((WARNINGS++))
    fi
else
    echo "  ⚠️  Docker 未安装"
    echo "     请安装 Docker Desktop: https://www.docker.com/products/docker-desktop"
    ((WARNINGS++))
fi

# 6. 检查环境变量配置
echo ""
echo -e "${YELLOW}[6/7] 检查环境变量配置...${NC}"

if [ -f ".env.prod" ]; then
    echo "  ✅ .env.prod 存在"
    
    # 检查关键变量
    if grep -q "JWT_SECRET" .env.prod; then
        echo "  ✅ JWT_SECRET 已配置"
    else
        echo "  ⚠️  JWT_SECRET 未配置"
        ((WARNINGS++))
    fi
    
    if grep -q "MYSQL_PASSWORD" .env.prod; then
        echo "  ✅ MySQL 密码已配置"
    else
        echo "  ⚠️  MySQL 密码未配置"
        ((WARNINGS++))
    fi
else
    echo "  ⚠️  .env.prod 不存在，使用默认配置"
    ((WARNINGS++))
fi

# 7. 检查前端构建
echo ""
echo -e "${YELLOW}[7/7] 检查前端构建...${NC}"

if [ -f "web/dist/index.html" ]; then
    echo "  ✅ 前端已构建"
    
    # 检查关键文件
    if [ -d "web/dist/assets" ]; then
        echo "  ✅ 静态资源目录存在"
    else
        echo "  ⚠️  静态资源目录不存在"
        ((WARNINGS++))
    fi
else
    echo "  ❌ 前端未构建"
    echo "     请运行: cd web && npm run build"
    ((ERRORS++))
fi

# 总结
echo ""
echo -e "${GREEN}=== 验证结果 ===${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ 所有检查通过！配置正确。${NC}"
    echo ""
    echo "可以开始部署:"
    echo "  本地测试: ./deploy-https-local.sh"
    echo "  生产环境: docker-compose -f docker-compose.https.yml up -d"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  配置基本正确，但有 $WARNINGS 个警告${NC}"
    echo ""
    echo "可以部署，但建议处理警告项"
    exit 0
else
    echo -e "${RED}❌ 发现 $ERRORS 个错误，$WARNINGS 个警告${NC}"
    echo ""
    echo "请修复错误后再部署"
    exit 1
fi
