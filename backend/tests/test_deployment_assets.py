from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def read_repo_file(relative_path: str) -> str:
    """读取仓库内部署资产文本，供回归断言使用。"""
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_frontend_production_api_uses_https_domain():
    env_text = read_repo_file("web/.env.production")
    assert "VITE_API_URL=https://lbu.me/api/v1" in env_text


def test_production_env_leaves_connection_urls_for_deploy_time_generation():
    env_text = read_repo_file(".env.prod")
    assert "DATABASE_URL=" in env_text
    assert "REDIS_URL=" in env_text
    assert "DATABASE_URL=mysql+pymysql://" not in env_text
    assert "REDIS_URL=redis://:" not in env_text


def test_deploy_script_targets_https_stack_and_remote_runtime():
    script = read_repo_file("deploy.sh")
    assert 'COMPOSE_SOURCE="${COMPOSE_SOURCE:-docker-compose.https.yml}"' in script
    assert 'PUBLIC_HEALTHCHECK_URL="${PUBLIC_HEALTHCHECK_URL:-https://lbu.me/health}"' in script
    assert 'CERTIFICATE_DOMAIN="${CERTIFICATE_DOMAIN:-lbu.me}"' in script
    assert 'BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-false}"' in script
    assert "command -v docker >/dev/null 2>&1" in script
    assert "docker compose version >/dev/null 2>&1" in script
    assert "请先在服务器执行 ./init-server.sh" in script
    assert "docker compose up -d --build --remove-orphans" in script
    assert "docker compose up -d --no-deps --force-recreate nginx" in script
    assert "docker compose logs nginx --tail=50; exit 1; }" in script
    assert "docker compose down --remove-orphans" not in script
    assert "id_ed25519" not in script
    assert "id_rsa" not in script


def test_deploy_script_generates_runtime_env_and_skips_backend_artifacts():
    script = read_repo_file("deploy.sh")
    assert "build_remote_env_file()" in script
    assert "from urllib.parse import quote" in script
    assert "mktemp" in script
    assert "跳过数据库备份（设置 BACKUP_BEFORE_DEPLOY=true 可启用）" in script
    assert "--exclude='tests'" in script
    assert "--exclude='logs'" in script
    assert "--exclude='*.db'" in script
    assert "--exclude='.pytest_cache'" in script


def test_https_compose_mounts_prod_nginx_and_host_certificates():
    compose = read_repo_file("docker-compose.https.yml")
    assert "./nginx/nginx.prod.conf:/etc/nginx/conf.d/default.conf:ro" in compose
    assert "/etc/letsencrypt:/etc/letsencrypt:ro" in compose
    assert "./nginx/certbot-data:/var/www/certbot" in compose
    assert "env_file:" in compose
    assert "- .env" in compose
    assert '"http://127.0.0.1/nginx-health"' in compose
    assert "version:" not in compose


def test_production_nginx_serves_apex_and_redirects_www():
    config = read_repo_file("nginx/nginx.prod.conf")
    assert "server_name lbu.me;" in config
    assert "server_name www.lbu.me;" in config
    assert "listen 443 ssl;" in config
    assert "http2 on;" in config
    assert "ssl_certificate /etc/letsencrypt/live/lbu.me/fullchain.pem;" in config
    assert "ssl_certificate_key /etc/letsencrypt/live/lbu.me/privkey.pem;" in config
    assert 'add_header Cache-Control "public, immutable";' in config
    assert 'add_header Cache-Control "no-cache, no-store, must-revalidate" always;' in config
    assert "return 301 https://lbu.me$request_uri;" in config
    assert "location /.well-known/acme-challenge/" in config
    assert "location /api" in config
    assert "location /docs" in config
    assert "location /health" in config


def test_setup_ssl_requests_dual_domain_certificate_without_forced_renewal():
    script = read_repo_file("setup-ssl.sh")
    assert 'PRIMARY_DOMAIN="${2:-localhost}"' in script
    assert 'WWW_DOMAIN="${3:-www.${PRIMARY_DOMAIN}}"' in script
    assert 'EMAIL="${4:-admin@example.com}"' in script
    assert 'LEADMINE_DEPLOY_DIR="${LEADMINE_DEPLOY_DIR:-/opt/leadmine}"' in script
    assert "ensure_certbot_available()" in script
    assert "install_certbot_reload_hook()" in script
    assert "reload_nginx_if_running()" in script
    assert "renewal-hooks/deploy" in script
    assert "certbot certonly --standalone" in script
    assert '-d "$PRIMARY_DOMAIN"' in script
    assert '-d "$WWW_DOMAIN"' in script
    assert "--force-renewal" not in script
    assert "certbot renew" in script
    assert "nginx -s reload" in script


def test_init_server_installs_runtime_dependencies():
    script = read_repo_file("init-server.sh")
    assert "install -m 0755 -d /etc/apt/sources.list.d" in script
    assert "docker-ce" in script
    assert "docker-compose-plugin" in script
    assert "certbot" in script
    assert "rsync" in script
    assert "systemctl enable docker --now" in script
