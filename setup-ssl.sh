#!/bin/bash

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

MODE=${1:-"self-signed"}
PRIMARY_DOMAIN="${2:-localhost}"
WWW_DOMAIN="${3:-www.${PRIMARY_DOMAIN}}"
EMAIL="${4:-admin@example.com}"
LEADMINE_DEPLOY_DIR="${LEADMINE_DEPLOY_DIR:-/opt/leadmine}"

# 输出脚本帮助，避免证书模式和参数顺序使用错误。
print_help() {
    echo "用法: $0 [模式] [主域名] [www域名] [邮箱]"
    echo ""
    echo "模式:"
    echo "  self-signed                                   生成本地自签名证书"
    echo "  letsencrypt lbu.me www.lbu.me admin@example.com 申请生产证书"
    echo "  renew                                         续期宿主机证书"
}

# 生成本地自签名证书，供本机 HTTPS 联调使用。
create_self_signed_certificate() {
    local cert_dir="nginx/ssl/localhost"

    mkdir -p "${cert_dir}" nginx/logs nginx/certbot-data

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "${cert_dir}/privkey.pem" \
        -out "${cert_dir}/fullchain.pem" \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=LeadMine/OU=Dev/CN=${PRIMARY_DOMAIN}"

    cp "${cert_dir}/fullchain.pem" nginx/ssl/localhost.crt
    cp "${cert_dir}/privkey.pem" nginx/ssl/localhost.key

    echo -e "${GREEN}✅ 自签名证书已生成${NC}"
    echo "证书目录: ${cert_dir}"
}

# 检查 certbot 是否可用，避免证书申请和续期重复散落同一前置判断。
ensure_certbot_available() {
    if ! command -v certbot >/dev/null 2>&1; then
        echo -e "${RED}❌ 未检测到 certbot，请先安装 certbot${NC}"
        exit 1
    fi
}

# 安装 certbot deploy hook，确保续期后容器内 Nginx 重新加载新证书。
install_certbot_reload_hook() {
    local hook_dir="/etc/letsencrypt/renewal-hooks/deploy"
    local hook_file="${hook_dir}/leadmine-nginx-reload.sh"

    mkdir -p "${hook_dir}"

    cat > "${hook_file}" <<EOF
#!/bin/bash
set -euo pipefail
LEADMINE_DEPLOY_DIR="${LEADMINE_DEPLOY_DIR}"

if ! command -v docker >/dev/null 2>&1; then
    exit 0
fi

if [ ! -f "4{LEADMINE_DEPLOY_DIR}/docker-compose.yml" ]; then
    exit 0
fi

docker compose -f "4{LEADMINE_DEPLOY_DIR}/docker-compose.yml" exec -T nginx sh -lc 'mkdir -p /var/log/nginx && touch /var/log/nginx/error.log /var/log/nginx/access.log && nginx -t && nginx -s reload' >/dev/null 2>&1 || true
EOF

    chmod +x "${hook_file}"
}

# 证书变更后刷新线上 Nginx，避免容器继续持有旧 TLS 证书。
reload_nginx_if_running() {
    if ! command -v docker >/dev/null 2>&1; then
        return
    fi

    if [ ! -f "${LEADMINE_DEPLOY_DIR}/docker-compose.yml" ]; then
        return
    fi

    docker compose -f "${LEADMINE_DEPLOY_DIR}/docker-compose.yml" exec -T nginx \
        sh -lc 'mkdir -p /var/log/nginx && touch /var/log/nginx/error.log /var/log/nginx/access.log && nginx -t && nginx -s reload' || true
}

# 申请正式双域名 Let's Encrypt 证书，供生产 Nginx 直接挂载宿主机证书。
request_letsencrypt_certificate() {
    ensure_certbot_available

    if [ "${PRIMARY_DOMAIN}" = "localhost" ]; then
        echo -e "${RED}❌ Let's Encrypt 不支持 localhost，请提供真实域名${NC}"
        exit 1
    fi

    install_certbot_reload_hook

    certbot certonly --standalone \
        -d "$PRIMARY_DOMAIN" \
        -d "$WWW_DOMAIN" \
        --agree-tos \
        -m "$EMAIL" \
        --no-eff-email

    reload_nginx_if_running

    echo -e "${GREEN}✅ Let's Encrypt 证书申请完成${NC}"
    echo "证书路径: /etc/letsencrypt/live/${PRIMARY_DOMAIN}"
}

# 续期宿主机上的 Let's Encrypt 证书，保持生产 HTTPS 可用。
renew_letsencrypt_certificate() {
    ensure_certbot_available
    install_certbot_reload_hook

    certbot renew
    reload_nginx_if_running
    echo -e "${GREEN}✅ 证书续期完成${NC}"
}

echo -e "${GREEN}=== LeadMine SSL 证书配置 ===${NC}"

action="${MODE}"
case "${action}" in
    help|-h|--help)
        print_help
        ;;
    self-signed)
        create_self_signed_certificate
        ;;
    letsencrypt)
        request_letsencrypt_certificate
        ;;
    renew)
        renew_letsencrypt_certificate
        ;;
    *)
        echo -e "${RED}❌ 未知模式: ${action}${NC}"
        print_help
        exit 1
        ;;
esac

echo ""
echo "下一步:"
echo "  本地联调: docker compose -f docker-compose.local-https.yml up -d --build"
echo "  生产申请: ./setup-ssl.sh letsencrypt lbu.me www.lbu.me admin@example.com"
