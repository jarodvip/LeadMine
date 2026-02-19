# LeadMine P0 级别安全修复计划

## 修复执行清单

### ✅ 已创建备份
- 备份路径: `/Users/jarod/Dev/new.backup.{日期时间}/`

---

## 修复 1: 删除 scheduler.py 中的重复类定义

### 文件
`backend/app/services/scheduler.py`

### 问题
第 16-55 行存在两个重复的 `CrawlScheduler` 类定义，第二个会覆盖第一个

### 修复操作
**删除第 16-36 行**（第一个类定义），只保留第 37 行开始的完整类定义

### 修改前
```python
class CrawlScheduler:
    """爬虫定时任务调度器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.running = False

    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行")
            return

        # 从数据库加载数据源并添加任务
        self._load_tasks_from_db()

        self.scheduler.start()
        self.running = True
        logger.info("爬虫调度器已启动")


class CrawlScheduler:
    """爬虫定时任务调度器"""
    ...
```

### 修改后
```python
class CrawlScheduler:
    """爬虫定时任务调度器"""
    ...
```

---

## 修复 2: 更新 config.py 安全配置

### 文件
`backend/app/core/config.py`

### 问题
1. JWT_SECRET 使用弱默认密钥
2. CORS 允许所有来源 `*`
3. DEBUG 模式默认开启

### 修复操作
替换整个文件内容：

```python
"""
应用配置
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置类"""

    # 应用配置
    app_name: str = "LeadMine API"
    debug: bool = Field(default=False, env="DEBUG")
    version: str = "1.0.0"

    # 数据库配置
    database_url: str = Field(
        default="sqlite:///./leadmine.db",
        env="DATABASE_URL"
    )

    # Redis 配置
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )

    # Elasticsearch 配置
    elasticsearch_url: str = Field(
        default="http://localhost:9200",
        env="ELASTICSEARCH_URL"
    )

    # JWT 配置 - 强制从环境变量读取，无默认值
    jwt_secret: str = Field(..., env="JWT_SECRET")  # 必须设置
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration: int = Field(default=7, env="JWT_EXPIRATION_DAYS")  # 天数

    # CORS 配置 - 生产环境必须配置具体域名
    cors_origins: List[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"],
        env="CORS_ORIGINS"
    )

    # RSSHub 配置
    rsshub_url: str = Field(
        default="http://localhost:1200",
        env="RSSHUB_URL"
    )

    # 管理员初始密码
    admin_password: str = Field(
        default="",
        env="ADMIN_PASSWORD"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()


# 生成强密钥的辅助函数（用于首次设置）
def generate_secure_key(length: int = 64) -> str:
    """生成安全的随机密钥"""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# 验证配置
if not settings.jwt_secret or settings.jwt_secret == "your-secret-key-change-in-production":
    import warnings
    warnings.warn(
        "WARNING: JWT_SECRET 未设置或使用默认弱密钥！"
        "请设置强密钥: export JWT_SECRET=$(openssl rand -base64 64)",
        RuntimeWarning
    )
```

---

## 修复 3: 移除 main.py 中的硬编码密码

### 文件
`backend/app/main.py`

### 问题
第 53 行硬编码管理员密码 `"admin123"`

### 修复操作
修改 `init_db()` 函数中的密码设置部分：

### 修改前
```python
hashed_password = get_password_hash("admin123")
```

### 修改后
```python
import os
import secrets

# 从环境变量读取或使用随机生成的强密码
admin_password = os.getenv("ADMIN_PASSWORD")
if not admin_password:
    admin_password = secrets.token_urlsafe(16)
    print(f"WARNING: ADMIN_PASSWORD 未设置，已生成临时密码: {admin_password}")
    print("请立即登录并修改密码！")

hashed_password = get_password_hash(admin_password)
```

---

## 修复 4: 限制 auth.py 用户注册角色

### 文件
`backend/app/api/auth.py`

### 问题
用户注册时可指定任意角色，包括 admin

### 修复操作
在 `register` 函数开头强制设置 role：

### 修改前
```python
@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    ...
```

### 修改后
```python
@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # 强制 role 为 user，不允许注册其他角色
    user.role = "user"
    
    # 检查用户名是否已存在
    ...
```

---

## 修复 5: 修复 LeadDetail.vue XSS 漏洞

### 文件
`web/src/views/LeadDetail.vue`

### 问题
第 113 行使用 `v-html` 渲染未过滤的用户内容，存在 XSS 攻击风险

### 修复操作

### 修改前
```vue
<div class="source-summary" v-html="article.content?.slice(0, 500) + '...'"></div>
```

### 修改后
```vue
<div class="source-summary">{{ article.content?.slice(0, 500) }}...</div>
```

或者如果需要渲染 HTML，使用 DOMPurify：

```vue
<template>
  <div class="source-summary" v-html="sanitizedContent"></div>
</template>

<script setup>
import { computed } from 'vue'
// 需要先安装: npm install dompurify
import DOMPurify from 'dompurify'

const sanitizedContent = computed(() => {
  const content = article.value?.content?.slice(0, 500) || ''
  return DOMPurify.sanitize(content + '...')
})
</script>
```

---

## 修复 6: 重写 deploy.sh 移除硬编码密码

### 文件
`deploy.sh`

### 修复操作
替换整个文件：

```bash
#!/bin/bash

# LeadMine 安全部署脚本
# 使用方法:
#   export SERVER_IP=your_server_ip
#   export SERVER_USER=deploy
#   ./deploy.sh

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
echo -e "\n${YELLOW}[1/8] 备份现有数据...${NC}"
ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "
    if [ -d ${APP_DIR} ] && [ -f ${APP_DIR}/.env ]; then
        BACKUP_DIR=/opt/backups/leadmine-\$(date +%Y%m%d-%H%M%S)
        mkdir -p \${BACKUP_DIR}
        cd ${APP_DIR}
        # 备份数据库
        source .env
        docker compose exec -T mysql mysqldump -u root -p\${MYSQL_ROOT_PASSWORD} \${MYSQL_DATABASE} > \${BACKUP_DIR}/database.sql 2>/dev/null || echo '数据库备份跳过'
        # 备份配置文件
        cp .env \${BACKUP_DIR}/
        cp docker-compose.yml \${BACKUP_DIR}/ 2>/dev/null || true
        echo \"备份完成: \${BACKUP_DIR}\"
    else
        echo '首次部署，跳过备份'
    fi
"

# 2. 创建部署目录
echo -e "\n${YELLOW}[2/8] 创建服务器目录...${NC}"
ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "mkdir -p ${APP_DIR}/logs ${APP_DIR}/backup"

# 3. 上传配置文件
echo -e "\n${YELLOW}[3/8] 上传配置文件...${NC}"
scp -P ${SSH_PORT} docker-compose.prod.yml ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/docker-compose.yml

# 检查是否存在 .env.prod，如果不存在则提示创建
if [[ ! -f .env.prod ]]; then
    echo -e "${RED}错误: 未找到 .env.prod 文件${NC}"
    echo "请先创建生产环境配置文件:"
    echo "  cp .env.example .env.prod"
    echo "  # 编辑 .env.prod，设置强密码"
    exit 1
fi

scp -P ${SSH_PORT} .env.prod ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/.env

# 4. 上传代码
echo -e "\n${YELLOW}[4/8] 上传应用代码...${NC}"
rsync -avz --delete \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='.env' \
    --exclude='.venv' \
    --exclude='tests/' \
    backend/ ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/backend/

rsync -avz --delete \
    --exclude='node_modules' \
    --exclude='.git' \
    web/dist/ ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/web/dist/

# 5. 构建并启动服务
echo -e "\n${YELLOW}[5/8] 构建并启动服务...${NC}"
ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "
    cd ${APP_DIR}
    echo '停止旧服务...'
    docker compose down --remove-orphans 2>/dev/null || true
    
    echo '拉取镜像...'
    docker compose pull
    
    echo '构建并启动...'
    docker compose up -d --build
    
    echo '等待服务启动...'
    sleep 10
    
    echo '服务状态:'
    docker compose ps
"

# 6. 健康检查
echo -e "\n${YELLOW}[6/8] 执行健康检查...${NC}"
HEALTH_STATUS=$(ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "
    cd ${APP_DIR}
    docker compose exec -T backend wget -qO- http://localhost:8000/health 2>/dev/null || echo 'FAILED'
")

if [[ "$HEALTH_STATUS" == *"ok"* ]] || [[ "$HEALTH_STATUS" == *"\"status\":\"ok\""* ]]; then
    echo -e "${GREEN}✓ 健康检查通过${NC}"
else
    echo -e "${RED}✗ 健康检查失败${NC}"
    echo "请检查日志: ssh ${SERVER_USER}@${SERVER_IP} 'cd ${APP_DIR} && docker compose logs backend'"
    exit 1
fi

# 7. 清理旧资源
echo -e "\n${YELLOW}[7/8] 清理旧镜像和容器...${NC}"
ssh -p ${SSH_PORT} ${SERVER_USER}@${SERVER_IP} "docker system prune -f --volumes 2>/dev/null || true"

echo -e "\n${GREEN}[8/8] 部署完成！${NC}"
echo "访问地址: http://${SERVER_IP}"
echo ""
echo -e "${YELLOW}重要提醒:${NC}"
echo "1. 如果是首次部署，请立即修改默认密码"
echo "2. 配置 SSL 证书: certbot --nginx"
echo "3. 查看日志: ssh ${SERVER_USER}@${SERVER_IP} 'cd ${APP_DIR} && docker compose logs -f'"
```

---

## 修复 7: 创建生产环境 docker-compose.prod.yml

### 文件
`docker-compose.prod.yml`（新建）

### 内容
```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: leadmine_mysql
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-leadmine}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./backup:/backup
    networks:
      - leadmine
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  redis:
    image: redis:7-alpine
    container_name: leadmine_redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - leadmine
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: leadmine_backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - ELASTICSEARCH_URL=${ELASTICSEARCH_URL}
      - JWT_SECRET=${JWT_SECRET}
      - DEBUG=false
      - LOG_LEVEL=INFO
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - leadmine
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M

  nginx:
    image: nginx:alpine
    container_name: leadmine_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./web/dist:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
    networks:
      - leadmine
    restart: unless-stopped

volumes:
  mysql_data:
  redis_data:

networks:
  leadmine:
    name: leadmine_network
```

---

## 修复 8: 创建生产环境 .env.prod 模板

### 文件
`.env.prod`（新建）

### 内容
```bash
# LeadMine 生产环境配置
# 生成强密码命令: openssl rand -base64 32

# ========================================
# 数据库配置（必须修改）
# ========================================
MYSQL_ROOT_PASSWORD=CHANGE_THIS_TO_32_CHAR_RANDOM_STRING
MYSQL_DATABASE=leadmine
MYSQL_USER=leadmine
MYSQL_PASSWORD=CHANGE_THIS_TO_32_CHAR_RANDOM_STRING

# 数据库连接URL（自动填充，无需修改）
DATABASE_URL=mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/${MYSQL_DATABASE}

# ========================================
# Redis 配置（必须修改）
# ========================================
REDIS_PASSWORD=CHANGE_THIS_TO_32_CHAR_RANDOM_STRING
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379

# ========================================
# JWT 配置（必须修改）
# 生成命令: openssl rand -base64 64
# ========================================
JWT_SECRET=CHANGE_THIS_TO_64_CHAR_RANDOM_STRING_MINIMUM
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7

# ========================================
# Elasticsearch 配置
# ========================================
ELASTICSEARCH_URL=http://elasticsearch:9200

# ========================================
# 管理员初始密码（必须修改）
# ========================================
ADMIN_PASSWORD=CHANGE_THIS_TO_STRONG_PASSWORD

# ========================================
# 应用配置
# ========================================
DEBUG=false
LOG_LEVEL=INFO

# ========================================
# CORS 配置（生产环境设置具体域名）
# 多个域名用逗号分隔
# ========================================
CORS_ORIGINS=http://localhost:8501,http://localhost:3000

# ========================================
# RSSHub 配置
# ========================================
RSSHUB_URL=http://rsshub:1200
```

---

## 修复 9: 更新 Dockerfile 生产配置

### 文件
`backend/Dockerfile`

### 修改内容

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# 复制依赖文件并安装
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY --chown=appuser:appuser . .

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:8000/health || exit 1

EXPOSE 8000

# 生产环境启动命令（移除 --reload，添加 workers）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## 修复 10: 创建 .dockerignore

### 文件
`backend/.dockerignore`（新建）

### 内容
```
__pycache__/
*.py[cod]
*$py.class
*.so
.env
.env.*
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.git
.gitignore
.pytest_cache/
.coverage
htmlcov/
.DS_Store
*.log
*.db
leadmine.db
```

---

## 修复执行步骤

按顺序执行以下命令：

```bash
# 1. 进入项目目录
cd /Users/jarod/Dev/new

# 2. 修复 scheduler.py - 删除第 16-36 行
sed -i '16,36d' backend/app/services/scheduler.py

# 3. 替换 config.py
cat > backend/app/core/config.py << 'EOF'
[上面修复 2 的内容]
EOF

# 4. 修改 main.py - 替换密码生成逻辑
sed -i 's/hashed_password = get_password_hash("admin123")/import os, secrets\nadmin_password = os.getenv("ADMIN_PASSWORD") or secrets.token_urlsafe(16)\nif not os.getenv("ADMIN_PASSWORD"):\n    print(f"WARNING: 使用临时密码: {admin_password}")\nhashed_password = get_password_hash(admin_password)/' backend/app/main.py

# 5. 修改 auth.py - 强制 role
sed -i '/async def register/a\    # 强制 role 为 user\n    user.role = "user"' backend/app/api/auth.py

# 6. 修复 LeadDetail.vue - 替换 v-html
sed -i 's/v-html="article.content?.slice(0, 500) + '"'"'...'"'"'"/{{ article.content?.slice(0, 500) }}.../' web/src/views/LeadDetail.vue

# 7. 创建 docker-compose.prod.yml
cat > docker-compose.prod.yml << 'EOF'
[上面修复 7 的内容]
EOF

# 8. 创建 .env.prod
cat > .env.prod << 'EOF'
[上面修复 8 的内容]
EOF

# 9. 更新 Dockerfile
cat > backend/Dockerfile << 'EOF'
[上面修复 9 的内容]
EOF

# 10. 创建 .dockerignore
cat > backend/.dockerignore << 'EOF'
[上面修复 10 的内容]
EOF

# 11. 更新 deploy.sh
cat > deploy.sh << 'EOF'
[上面修复 6 的内容]
EOF
chmod +x deploy.sh

# 12. 提交更改
git add -A
git commit -m "security: 修复 P0 级别安全漏洞

- 删除 scheduler.py 中重复的类定义
- 强制 JWT_SECRET 从环境变量读取
- 移除硬编码管理员密码，改为环境变量或随机生成
- 限制用户注册只能为 user 角色
- 修复 LeadDetail.vue XSS 漏洞（v-html -> 文本渲染）
- 重写 deploy.sh 使用 SSH 密钥而非密码
- 添加 docker-compose.prod.yml 生产配置
- 添加 .env.prod 环境变量模板
- 更新 Dockerfile 移除 --reload，添加 workers
- 添加 .dockerignore"
```

---

## 验证检查清单

修复完成后，请验证：

- [ ] `scheduler.py` 只有一个 `CrawlScheduler` 类定义
- [ ] `config.py` 中 JWT_SECRET 没有默认值
- [ ] `main.py` 没有硬编码 `"admin123"`
- [ ] `auth.py` 中 `user.role = "user"` 在 register 函数开头
- [ ] `LeadDetail.vue` 使用 `{{ }}` 而非 `v-html`
- [ ] `deploy.sh` 没有明文密码
- [ ] `docker-compose.prod.yml` 存在且 DEBUG=false
- [ ] `.env.prod` 存在且所有密码为 `CHANGE_THIS...`
- [ ] `Dockerfile` 没有 `--reload` 参数
- [ ] `.dockerignore` 存在

---

## 生成强密钥

```bash
# MySQL/Redis 密码（32字符）
openssl rand -base64 32

# JWT 密钥（64字符）
openssl rand -base64 64

# 管理员密码（随机）
openssl rand -base64 16
```

---

**创建日期**: 2026-02-19  
**计划版本**: 1.0
