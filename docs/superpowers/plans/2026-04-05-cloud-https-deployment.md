# LeadMine Cloud HTTPS Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补齐 LeadMine 在 Debian 12 单机云服务器上的正式 HTTPS 部署链路，继续沿用现有“本地构建 + 脚本上传 + 远端 Docker Compose 启动”路径，让 `https://lbu.me` 成为主站，并让 `https://www.lbu.me` 永久 `301` 跳转到主站。

**Architecture:** 保留现有 `deploy.sh` 作为发布入口，不额外引入 CI/CD。新增一个生产专用 Nginx 配置和一个 Debian 12 初始化脚本；证书使用宿主机 `certbot` 申请到 `/etc/letsencrypt`，再由 `docker-compose.https.yml` 只读挂载进 Nginx 容器。部署实现用仓库内的文本级回归测试锁定，避免后续脚本或配置回退到 HTTP-only 状态。

**Tech Stack:** Bash, Docker Compose plugin, Nginx, Let's Encrypt certbot, pytest, Vite environment variables

---

## File Map

- `backend/tests/test_deployment_assets.py` — 读取仓库内部署脚本与配置文件，做文本级回归断言。
- `web/.env.production` — 生产前端 API 地址，必须切到正式 HTTPS 域名。
- `nginx/nginx.prod.conf` — 生产专用 Nginx 配置，处理 `lbu.me` HTTPS 入口和 `www` 跳转。
- `docker-compose.https.yml` — 生产 HTTPS 编排，挂载生产 Nginx 配置与宿主机证书目录。
- `setup-ssl.sh` — 本地自签名和生产双域名 Let's Encrypt 证书申请脚本。
- `init-server.sh` — Debian 12 首次初始化脚本，安装 Docker、Compose plugin、certbot 与 rsync。
- `deploy.sh` — 生产发布入口，上传 HTTPS 编排并执行公开域名健康检查。
- `verify-https.sh` — 静态检查生产部署资产是否满足 HTTPS 上线要求。
- `docs/HTTPS_DEPLOY.md` — 面向操作者的正式部署手册。

### Task 1: Lock The Production Deploy Contract

**Files:**
- Create: `backend/tests/test_deployment_assets.py`
- Modify: `web/.env.production`
- Modify: `deploy.sh`
- Test: `backend/tests/test_deployment_assets.py`

- [ ] **Step 1: Write the failing regression tests**

```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def read_repo_file(relative_path: str) -> str:
    """读取仓库内部署资产文本，供回归断言使用。"""
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_frontend_production_api_uses_https_domain():
    env_text = read_repo_file("web/.env.production")
    assert "VITE_API_URL=https://lbu.me/api/v1" in env_text


def test_deploy_script_uses_https_compose_and_public_healthcheck():
    script = read_repo_file("deploy.sh")
    assert 'COMPOSE_SOURCE="docker-compose.https.yml"' in script
    assert 'PUBLIC_HEALTHCHECK_URL="${PUBLIC_HEALTHCHECK_URL:-https://lbu.me/health}"' in script
    assert "docker compose" in script
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/test_deployment_assets.py -q
```

Expected: FAIL because `web/.env.production` still points at `http://152.32.189.185/api/v1`, and `deploy.sh` still uploads `docker-compose.prod.yml` with `docker-compose` commands.

- [ ] **Step 3: Implement the minimal production contract changes**

Update `web/.env.production` to the正式 HTTPS 域名：

```bash
VITE_API_URL=https://lbu.me/api/v1
```

Update the top of `deploy.sh` so production deploys the HTTPS compose file and knows the public health URL:

```bash
SERVER_IP="${SERVER_IP:-}"
SERVER_USER="${SERVER_USER:-root}"
APP_DIR="/opt/leadmine"
SSH_PORT="${SSH_PORT:-22}"
COMPOSE_SOURCE="docker-compose.https.yml"
PUBLIC_HEALTHCHECK_URL="${PUBLIC_HEALTHCHECK_URL:-https://lbu.me/health}"
```

Update the compose upload and the公开健康检查 in `deploy.sh`:

```bash
scp -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -P ${SSH_PORT} "${COMPOSE_SOURCE}" ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/docker-compose.yml

if curl --fail --silent --show-error "${PUBLIC_HEALTHCHECK_URL}" >/dev/null; then
    echo -e "${GREEN}✓ 公开 HTTPS 健康检查通过${NC}"
else
    echo -e "${RED}✗ 公开 HTTPS 健康检查失败: ${PUBLIC_HEALTHCHECK_URL}${NC}"
    exit 1
fi
```

Switch the remote compose commands to the plugin form so the script matches Debian 12 的 `docker-compose-plugin`：

```bash
docker compose down --remove-orphans 2>/dev/null || true
docker compose pull
docker compose up -d --build
docker compose ps
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/test_deployment_assets.py -q
```

Expected: PASS with `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_deployment_assets.py web/.env.production deploy.sh
git commit -m "$(cat <<'EOF'
test: lock https deployment contract
EOF
)"
```

### Task 2: Split Production Nginx And Dual-Domain Certificate Setup

**Files:**
- Modify: `backend/tests/test_deployment_assets.py`
- Create: `nginx/nginx.prod.conf`
- Modify: `docker-compose.https.yml`
- Modify: `setup-ssl.sh`
- Test: `backend/tests/test_deployment_assets.py`

- [ ] **Step 1: Extend the regression tests for the production HTTPS chain**

Append these tests to `backend/tests/test_deployment_assets.py`:

```python
def test_https_compose_mounts_prod_nginx_and_host_certificates():
    compose = read_repo_file("docker-compose.https.yml")
    assert "./nginx/nginx.prod.conf:/etc/nginx/conf.d/default.conf:ro" in compose
    assert "/etc/letsencrypt:/etc/letsencrypt:ro" in compose
    assert "./nginx/certbot-data:/var/www/certbot" in compose


def test_production_nginx_serves_apex_and_redirects_www():
    config = read_repo_file("nginx/nginx.prod.conf")
    assert "server_name lbu.me;" in config
    assert "server_name www.lbu.me;" in config
    assert "listen 443 ssl http2;" in config
    assert "ssl_certificate /etc/letsencrypt/live/lbu.me/fullchain.pem;" in config
    assert "ssl_certificate_key /etc/letsencrypt/live/lbu.me/privkey.pem;" in config
    assert "return 301 https://lbu.me$request_uri;" in config
    assert "location /.well-known/acme-challenge/" in config
    assert "location /api" in config
    assert "location /docs" in config
    assert "location /health" in config


def test_setup_ssl_requests_dual_domain_certificate():
    script = read_repo_file("setup-ssl.sh")
    assert 'PRIMARY_DOMAIN="${2:-localhost}"' in script
    assert 'WWW_DOMAIN="${3:-www.${PRIMARY_DOMAIN}}"' in script
    assert 'EMAIL="${4:-admin@example.com}"' in script
    assert "certbot certonly --standalone" in script
    assert '-d "$PRIMARY_DOMAIN"' in script
    assert '-d "$WWW_DOMAIN"' in script
```

- [ ] **Step 2: Run the HTTPS-chain tests to verify they fail**

Run:
```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/test_deployment_assets.py -k "compose or nginx or setup_ssl" -q
```

Expected: FAIL because `nginx/nginx.prod.conf` does not exist yet, `docker-compose.https.yml` still mounts `nginx/nginx.conf`, and `setup-ssl.sh` still accepts only one domain.

- [ ] **Step 3: Implement the production Nginx config, compose mount, and dual-domain cert flow**

Create `nginx/nginx.prod.conf` with separate apex and `www` handling:

```nginx
server {
    listen 80;
    server_name lbu.me;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    return 301 https://lbu.me$request_uri;
}

server {
    listen 80;
    server_name www.lbu.me;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    return 301 https://lbu.me$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.lbu.me;

    ssl_certificate /etc/letsencrypt/live/lbu.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lbu.me/privkey.pem;

    return 301 https://lbu.me$request_uri;
}

server {
    listen 443 ssl http2;
    server_name lbu.me;

    ssl_certificate /etc/letsencrypt/live/lbu.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lbu.me/privkey.pem;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript font/opentype font/ttf font/eot font/woff font/woff2;

    client_max_body_size 10M;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /docs {
        proxy_pass http://backend:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /openapi.json {
        proxy_pass http://backend:8000/openapi.json;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /health {
        proxy_pass http://backend:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        access_log off;
    }

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate" always;
        add_header Pragma "no-cache" always;
        add_header Expires "0" always;
    }
}
```

Update the `nginx` service in `docker-compose.https.yml` so production mounts the new config and host-side certificates:

```yaml
  nginx:
    image: nginx:alpine
    container_name: leadmine_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./web/dist:/usr/share/nginx/html:ro
      - ./nginx/nginx.prod.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - ./nginx/certbot-data:/var/www/certbot
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - backend
    networks:
      - leadmine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Update `setup-ssl.sh` argument parsing and production certificate request flow:

```bash
MODE=${1:-"self-signed"}
PRIMARY_DOMAIN="${2:-localhost}"
WWW_DOMAIN="${3:-www.${PRIMARY_DOMAIN}}"
EMAIL="${4:-admin@example.com}"

request_letsencrypt_certificate() {
    certbot certonly --standalone \
        -d "$PRIMARY_DOMAIN" \
        -d "$WWW_DOMAIN" \
        --agree-tos \
        -m "$EMAIL" \
        --no-eff-email \
        --force-renewal
}
```

Keep `self-signed` mode writing to `nginx/ssl/localhost`, and update the production usage text to this exact command:

```bash
./setup-ssl.sh letsencrypt lbu.me www.lbu.me admin@example.com
```

- [ ] **Step 4: Run the HTTPS-chain tests to verify they pass**

Run:
```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/test_deployment_assets.py -k "compose or nginx or setup_ssl" -q
```

Expected: PASS with `5 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_deployment_assets.py nginx/nginx.prod.conf docker-compose.https.yml setup-ssl.sh
git commit -m "$(cat <<'EOF'
feat: add production https nginx chain
EOF
)"
```

### Task 3: Bootstrap Debian 12 And Harden The Remote Deploy Script

**Files:**
- Modify: `backend/tests/test_deployment_assets.py`
- Create: `init-server.sh`
- Modify: `deploy.sh`
- Test: `backend/tests/test_deployment_assets.py`

- [ ] **Step 1: Extend the regression tests for server bootstrap and deploy prerequisites**

Append these tests to `backend/tests/test_deployment_assets.py`:

```python
def test_init_server_installs_runtime_dependencies():
    script = read_repo_file("init-server.sh")
    assert "docker-ce" in script
    assert "docker-compose-plugin" in script
    assert "certbot" in script
    assert "rsync" in script
    assert "systemctl enable docker --now" in script


def test_deploy_script_checks_remote_runtime_before_sync():
    script = read_repo_file("deploy.sh")
    assert "command -v docker >/dev/null 2>&1" in script
    assert "docker compose version >/dev/null 2>&1" in script
    assert "请先在服务器执行 ./init-server.sh" in script
    assert "docker compose up -d --build" in script
```

- [ ] **Step 2: Run the bootstrap tests to verify they fail**

Run:
```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/test_deployment_assets.py -k "init_server or remote_runtime" -q
```

Expected: FAIL because `init-server.sh` does not exist and `deploy.sh` does not yet stop early when Docker or Compose plugin is missing on the server.

- [ ] **Step 3: Implement the Debian 12 initialization script and remote prerequisite checks**

Create `init-server.sh`:

```bash
#!/bin/bash

set -euo pipefail

# 检查当前用户是否为 root，避免安装阶段权限不足。
require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "错误: 请使用 root 用户执行 init-server.sh"
        exit 1
    fi
}

# 安装 Docker 官方源以及部署链路需要的运行时依赖。
install_runtime_packages() {
    apt-get update
    apt-get install -y ca-certificates curl gnupg rsync certbot

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" \
        > /etc/apt/sources.list.d/docker.list

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

# 启动 Docker，并输出关键二进制版本方便人工确认。
verify_runtime_packages() {
    systemctl enable docker --now
    docker --version
    docker compose version
    certbot --version
    rsync --version | head -n 1
}

main() {
    require_root
    install_runtime_packages
    verify_runtime_packages
}

main "$@"
```

Add a remote runtime check near the top of `deploy.sh`:

```bash
check_remote_runtime() {
    ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "
        if ! command -v docker >/dev/null 2>&1; then
            echo '错误: 服务器未安装 Docker，请先在服务器执行 ./init-server.sh'
            exit 1
        fi
        if ! docker compose version >/dev/null 2>&1; then
            echo '错误: 服务器未安装 Docker Compose plugin，请先在服务器执行 ./init-server.sh'
            exit 1
        fi
    "
}
```

Call that check before backup/sync, and keep all remote compose operations on `docker compose`:

```bash
echo -e "\n${YELLOW}[0/6] 检查服务器运行时...${NC}"
check_remote_runtime

ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "
    cd ${APP_DIR}
    docker compose down --remove-orphans 2>/dev/null || true
    docker compose pull
    docker compose up -d --build
    docker compose ps
"
```

- [ ] **Step 4: Run the bootstrap tests to verify they pass**

Run:
```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/test_deployment_assets.py -k "init_server or remote_runtime" -q
```

Expected: PASS with `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_deployment_assets.py init-server.sh deploy.sh
git commit -m "$(cat <<'EOF'
feat: add server bootstrap for https deploy
EOF
)"
```

### Task 4: Refresh Verification And The Operator Runbook

**Files:**
- Modify: `backend/tests/test_deployment_assets.py`
- Modify: `verify-https.sh`
- Modify: `docs/HTTPS_DEPLOY.md`
- Test: `backend/tests/test_deployment_assets.py`

- [ ] **Step 1: Extend the regression tests for verification and docs**

Append these tests to `backend/tests/test_deployment_assets.py`:

```python
def test_verify_script_points_to_production_https_assets():
    script = read_repo_file("verify-https.sh")
    assert 'NGINX_CONFIG="nginx/nginx.prod.conf"' in script
    assert 'COMPOSE_FILE="docker-compose.https.yml"' in script
    assert "www.lbu.me" in script
    assert "VITE_API_URL=https://lbu.me/api/v1" in script


def test_https_deploy_doc_uses_the_new_runbook():
    doc = read_repo_file("docs/HTTPS_DEPLOY.md")
    assert "./init-server.sh" in doc
    assert "./setup-ssl.sh letsencrypt lbu.me www.lbu.me admin@example.com" in doc
    assert "export SERVER_IP=152.32.189.185" in doc
    assert "https://www.lbu.me" in doc
```

- [ ] **Step 2: Run the verification/docs tests to verify they fail**

Run:
```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/test_deployment_assets.py -k "verify_script or runbook" -q
```

Expected: FAIL because `verify-https.sh` still checks `nginx/nginx.conf`, and `docs/HTTPS_DEPLOY.md` still describes the old single-domain/manual compose flow.

- [ ] **Step 3: Implement the production verifier and operator runbook**

Update the top of `verify-https.sh` so it validates the production asset set instead of the local default config:

```bash
NGINX_CONFIG="nginx/nginx.prod.conf"
COMPOSE_FILE="docker-compose.https.yml"

REQUIRED_FILES=(
    "$NGINX_CONFIG"
    "$COMPOSE_FILE"
    "setup-ssl.sh"
    "init-server.sh"
    "deploy.sh"
    "web/.env.production"
)
```

Update the key checks in `verify-https.sh`:

```bash
if grep -q "server_name lbu.me;" "$NGINX_CONFIG"; then
    echo "  ✅ 主站域名配置"
else
    echo "  ❌ 主站域名未配置"
    ((ERRORS++))
fi

if grep -q "server_name www.lbu.me;" "$NGINX_CONFIG"; then
    echo "  ✅ www 域名配置"
else
    echo "  ❌ www 域名未配置"
    ((ERRORS++))
fi

if grep -q "return 301 https://lbu.me\\$request_uri;" "$NGINX_CONFIG"; then
    echo "  ✅ www 跳转到主站"
else
    echo "  ❌ www 跳转未配置"
    ((ERRORS++))
fi

if grep -q "VITE_API_URL=https://lbu.me/api/v1" web/.env.production; then
    echo "  ✅ 前端 API 地址已切到正式 HTTPS 域名"
else
    echo "  ❌ 前端 API 地址仍不是正式 HTTPS 域名"
    ((ERRORS++))
fi

if docker compose -f "$COMPOSE_FILE" config > /dev/null 2>&1; then
    echo "  ✅ ${COMPOSE_FILE} 格式正确"
else
    echo "  ❌ ${COMPOSE_FILE} 格式错误"
    ((ERRORS++))
fi
```

Rewrite the production section of `docs/HTTPS_DEPLOY.md` around the actual Debian 12 operator flow:

~~~md
## Debian 12 服务器初始化

```bash
scp init-server.sh root@152.32.189.185:/root/init-server.sh
ssh root@152.32.189.185 "bash /root/init-server.sh"
```

## 首次上线

```bash
ssh root@152.32.189.185 "mkdir -p /opt/leadmine"
scp setup-ssl.sh root@152.32.189.185:/opt/leadmine/setup-ssl.sh
ssh root@152.32.189.185 "cd /opt/leadmine && bash setup-ssl.sh letsencrypt lbu.me www.lbu.me admin@example.com"

cd /Users/jarod/Dev/LeadMine/web && npm run build
cd /Users/jarod/Dev/LeadMine
export SERVER_IP=152.32.189.185
export SERVER_USER=root
./deploy.sh
```

## 验收

- `https://lbu.me` 可以打开首页
- `https://www.lbu.me` 返回 `301` 到 `https://lbu.me`
- `https://lbu.me/health` 返回健康状态
- `https://lbu.me/docs` 可访问
~~~

- [ ] **Step 4: Run the full regression file to verify everything passes**

Run:
```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/test_deployment_assets.py -q
```

Expected: PASS with `9 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_deployment_assets.py verify-https.sh docs/HTTPS_DEPLOY.md
git commit -m "$(cat <<'EOF'
docs: refresh https deployment runbook
EOF
)"
```

## Final Validation Commands

Run these after Task 4 is complete:

```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/test_deployment_assets.py -q
bash /Users/jarod/Dev/LeadMine/verify-https.sh
cd /Users/jarod/Dev/LeadMine/web && npm run build
```

On the server, run these after `./deploy.sh` finishes:

```bash
ssh root@152.32.189.185 "cd /opt/leadmine && docker compose ps"
ssh root@152.32.189.185 "cd /opt/leadmine && docker compose logs backend --tail=100"
ssh root@152.32.189.185 "cd /opt/leadmine && docker compose logs nginx --tail=100"
```

Manual acceptance:

- `https://lbu.me` loads the Vue frontend.
- `https://www.lbu.me` returns `301` to `https://lbu.me`.
- `https://lbu.me/health` returns a healthy payload.
- `https://lbu.me/docs` loads FastAPI Swagger UI.
- The server no longer relies on a temporary admin password emitted to logs.
