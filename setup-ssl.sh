#!/bin/bash

# LeadMine SSL 证书配置脚本
# 支持 Let's Encrypt 自动证书和自签名证书

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== LeadMine SSL 证书配置 ===${NC}"
echo ""

# 检查参数
MODE=${1:-"self-signed"}
DOMAIN=${2:-"localhost"}
EMAIL=${3:-"admin@example.com"}

if [ "$MODE" == "help" ] || [ "$MODE" == "-h" ]; then
    echo "用法: $0 [模式] [域名] [邮箱]"
    echo ""
    echo "模式:"
    echo "  self-signed     使用自签名证书 (默认，用于本地测试)"
    echo "  letsencrypt     使用 Let's Encrypt 证书 (用于生产环境)"
    echo ""
    echo "示例:"
    echo "  $0 self-signed                              # 生成本地自签名证书"
    echo "  $0 letsencrypt example.com admin@example.com # 生成 Let's Encrypt 证书"
    exit 0
fi

# 创建 SSL 目录
mkdir -p nginx/ssl/localhost
mkdir -p nginx/logs

case "$MODE" in
    "self-signed")
        echo -e "${YELLOW}生成自签名证书...${NC}"
        
        # 生成自签名证书
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/localhost.key \
            -out nginx/ssl/localhost.crt \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=LeadMine/OU=Dev/CN=$DOMAIN"
        
        # 复制到 nginx 期望的位置
        cp nginx/ssl/localhost.crt nginx/ssl/localhost/fullchain.pem
        cp nginx/ssl/localhost.key nginx/ssl/localhost/privkey.pem
        
        echo -e "${GREEN}✅ 自签名证书已生成${NC}"
        echo ""
        echo "证书信息:"
        echo "  域名: $DOMAIN"
        echo "  有效期: 365 天"
        echo "  位置: nginx/ssl/"
        echo ""
        echo -e "${YELLOW}⚠️  注意: 浏览器会显示安全警告，这是正常的${NC}"
        ;;
        
    "letsencrypt")
        echo -e "${YELLOW}配置 Let's Encrypt 证书...${NC}"
        
        # 检查 certbot
        if ! command -v certbot &> /dev/null; then
            echo -e "${RED}❌ 请先安装 certbot${NC}"
            echo "  Ubuntu/Debian: sudo apt-get install certbot"
            echo "  CentOS/RHEL: sudo yum install certbot"
            echo "  macOS: brew install certbot"
            exit 1
        fi
        
        # 检查域名
        if [ "$DOMAIN" == "localhost" ]; then
            echo -e "${RED}❌ Let's Encrypt 不支持 localhost${NC}"
            echo "请使用真实域名"
            exit 1
        fi
        
        echo "域名: $DOMAIN"
        echo "邮箱: $EMAIL"
        echo ""
        
        # 申请证书
        echo -e "${YELLOW}正在申请证书...${NC}"
        certbot certonly --standalone \
            -d "$DOMAIN" \
            --agree-tos \
            -m "$EMAIL" \
            --no-eff-email \
            --force-renewal
        
        # 创建符号链接
        CERT_PATH="/etc/letsencrypt/live/$DOMAIN"
        if [ -d "$CERT_PATH" ]; then
            ln -sf "$CERT_PATH/fullchain.pem" nginx/ssl/localhost/fullchain.pem
            ln -sf "$CERT_PATH/privkey.pem" nginx/ssl/localhost/privkey.pem
            echo -e "${GREEN}✅ Let's Encrypt 证书已配置${NC}"
        else
            echo -e "${RED}❌ 证书申请失败${NC}"
            exit 1
        fi
        
        echo ""
        echo -e "${GREEN}证书信息:${NC}"
        openssl x509 -in nginx/ssl/localhost/fullchain.pem -noout -subject -dates
        echo ""
        echo -e "${YELLOW}提示: 证书将自动续期${NC}"
        ;;
        
    "renew")
        echo -e "${YELLOW}续期 Let's Encrypt 证书...${NC}"
        
        if command -v certbot &> /dev/null; then
            certbot renew
            echo -e "${GREEN}✅ 证书续期完成${NC}"
        else
            echo -e "${RED}❌ certbot 未安装${NC}"
            exit 1
        fi
        ;;
        
    *)
        echo -e "${RED}❌ 未知模式: $MODE${NC}"
        echo "使用 'self-signed' 或 'letsencrypt'"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}SSL 配置完成!${NC}"
echo ""
echo "下一步:"
echo "  1. 使用 docker-compose.https.yml 启动服务"
echo "     docker compose -f docker-compose.https.yml up -d"
echo ""
echo "  2. 访问 https://$DOMAIN"
echo ""
