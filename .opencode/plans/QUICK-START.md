# LeadMine P0 级别安全修复 - 快速执行指南

## 📋 修复总览

本次修复解决以下 **10 个 P0 级别**的安全和代码问题：

| 序号 | 文件 | 问题 | 严重程度 |
|------|------|------|----------|
| 1 | scheduler.py | 类重复定义 | 🔴 高 |
| 2 | config.py | 弱 JWT 密钥 + CORS 允许所有 | 🔴 高 |
| 3 | main.py | 硬编码管理员密码 | 🔴 高 |
| 4 | auth.py | 允许注册任意角色 | 🔴 高 |
| 5 | LeadDetail.vue | XSS 漏洞 (v-html) | 🔴 高 |
| 6 | deploy.sh | 明文服务器密码 | 🔴 高 |
| 7 | docker-compose.yml | DEBUG=true | 🟠 中 |
| 8 | Dockerfile | --reload 参数 | 🟠 中 |
| 9 | .env.example | 不安全示例 | 🟠 中 |
| 10 | 缺少 | .dockerignore | 🟡 低 |

---

## 🚀 快速执行（3 种方式）

### 方式一：一键脚本（推荐）

复制以下内容保存为 `apply-fixes.sh`，然后执行：

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== LeadMine P0 安全修复 ==="

# 1. 备份
cp -r . ../leadmine-backup-$(date +%Y%m%d_%H%M%S)
echo "✓ 备份完成"

# 2. 修复 scheduler.py (删除第 16-36 行)
sed -i '16,36d' backend/app/services/scheduler.py
echo "✓ scheduler.py 修复完成"

# 3. 修复 config.py
cat > backend/app/core/config.py << 'EOF'
"""应用配置"""
import warnings
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = "LeadMine API"
    debug: bool = Field(default=False, env="DEBUG")
    version: str = "1.0.0"
    database_url: str = Field(default="sqlite:///./leadmine.db", env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    elasticsearch_url: str = Field(default="http://localhost:9200", env="ELASTICSEARCH_URL")
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration: int = Field(default=7, env="JWT_EXPIRATION_DAYS")
    cors_origins: List[str] = Field(default=["http://localhost:8501"], env="CORS_ORIGINS")
    rsshub_url: str = Field(default="http://localhost:1200", env="RSSHUB_URL")
    admin_password: str = Field(default="", env="ADMIN_PASSWORD")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

if not settings.jwt_secret or settings.jwt_secret == "your-secret-key-change-in-production":
    warnings.warn("JWT_SECRET 未设置或使用默认弱密钥！", RuntimeWarning)
EOF
echo "✓ config.py 修复完成"

# 4. 修复 main.py
sed -i 's/hashed_password = get_password_hash("admin123")/import secrets\nadmin_password = os.getenv("ADMIN_PASSWORD") or secrets.token_urlsafe(16)\nif not os.getenv("ADMIN_PASSWORD"):\n    print(f"WARNING: 使用临时密码: {admin_password}")\nhashed_password = get_password_hash(admin_password)/' backend/app/main.py
echo "✓ main.py 修复完成"

# 5. 修复 auth.py
sed -i '/async def register(user: UserCreate, db: Session = Depends(get_db)):/a\    # 强制 role 为 user\n    user.role = "user"' backend/app/api/auth.py
echo "✓ auth.py 修复完成"

# 6. 修复 LeadDetail.vue
sed -i 's/v-html="article.content?.slice(0, 500) + '"'"'...'"'"'"/{{ article.content?.slice(0, 500) }}.../' web/src/views/LeadDetail.vue
echo "✓ LeadDetail.vue 修复完成"

echo "=== 核心修复完成 ==="
echo ""
echo "📋 手动检查清单："
echo "  ☐ scheduler.py 只有一个 CrawlScheduler 类"
echo "  ☐ config.py 中 JWT_SECRET 无默认值"
echo "  ☐ main.py 无硬编码 admin123"
echo "  ☐ auth.py 中 user.role = 'user'"
echo "  ☐ LeadDetail.vue 使用 {{ }} 而非 v-html"
echo ""
echo "📝 下一步：创建生产配置文件"
echo "  cp .env.example .env.prod"
echo "  # 编辑 .env.prod 设置强密码"
```

执行：
```bash
chmod +x apply-fixes.sh
./apply-fixes.sh
```

---

### 方式二：手动修复（逐个文件）

#### 1. 修复 scheduler.py
```bash
# 删除第 16-36 行（第一个重复类）
sed -i '16,36d' backend/app/services/scheduler.py
```

#### 2. 修复 config.py
直接复制 `p0-security-fixes.md` 中"修复 2"的完整代码替换原文件。

#### 3. 修复 main.py
将：
```python
hashed_password = get_password_hash("admin123")
```
替换为：
```python
import secrets
admin_password = os.getenv("ADMIN_PASSWORD") or secrets.token_urlsafe(16)
if not os.getenv("ADMIN_PASSWORD"):
    print(f"WARNING: 使用临时密码: {admin_password}")
hashed_password = get_password_hash(admin_password)
```

#### 4. 修复 auth.py
在 `register` 函数开头添加：
```python
user.role = "user"
```

#### 5. 修复 LeadDetail.vue
将：
```vue
<div class="source-summary" v-html="article.content?.slice(0, 500) + '...'"></div>
```
替换为：
```vue
<div class="source-summary">{{ article.content?.slice(0, 500) }}...</div>
```

---

### 方式三：使用 IDE

1. 打开项目文件夹 `/Users/jarod/Dev/new`
2. 按照 `p0-security-fixes.md` 中的详细说明逐个修改文件
3. 参考每个修复的"修改前"和"修改后"代码片段

---

## 📁 创建生产配置文件

修复完成后，创建以下文件：

### 1. .env.prod（环境变量模板）

```bash
# 生成强密码
# MySQL/Redis: openssl rand -base64 32
# JWT: openssl rand -base64 64

MYSQL_ROOT_PASSWORD=YOUR_STRONG_PASSWORD_HERE
MYSQL_DATABASE=leadmine
MYSQL_USER=leadmine
MYSQL_PASSWORD=YOUR_STRONG_PASSWORD_HERE
DATABASE_URL=mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/${MYSQL_DATABASE}

REDIS_PASSWORD=YOUR_STRONG_PASSWORD_HERE
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379

JWT_SECRET=YOUR_64_CHAR_JWT_SECRET_HERE
ADMIN_PASSWORD=YOUR_ADMIN_PASSWORD_HERE

DEBUG=false
CORS_ORIGINS=http://localhost:8501
```

### 2. docker-compose.prod.yml

参考 `p0-security-fixes.md` 中"修复 7"的完整配置。

### 3. 更新 Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev pkg-config wget \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser . .
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:8000/health || exit 1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 4. 创建 .dockerignore

```
__pycache__/
*.pyc
.env
.venv
.git
.pytest_cache/
.DS_Store
*.log
*.db
```

---

## ✅ 验证检查清单

修复完成后，请验证以下项目：

### 代码修复验证
- [ ] `scheduler.py` 只有一个 `CrawlScheduler` 类定义
- [ ] `config.py` 中 `JWT_SECRET` 没有默认值（`Field(...)`）
- [ ] `main.py` 中没有 `"admin123"` 字符串
- [ ] `auth.py` 中 `register` 函数有 `user.role = "user"`
- [ ] `LeadDetail.vue` 使用 `{{ }}` 而非 `v-html`

### 配置文件验证
- [ ] `.env.prod` 存在且所有密码为 `CHANGE_THIS...` 或已修改
- [ ] `docker-compose.prod.yml` 中 `DEBUG=false`
- [ ] `Dockerfile` 没有 `--reload` 参数
- [ ] `.dockerignore` 存在

---

## 🔐 生成强密码

```bash
# MySQL/Redis 密码（32字符）
openssl rand -base64 32

# JWT 密钥（64字符）
openssl rand -base64 64

# 随机密码
openssl rand -base64 16
```

---

## 💾 提交更改

```bash
# 添加所有更改
git add -A

# 提交
git commit -m "security: 修复 P0 级别安全漏洞

- 删除 scheduler.py 中重复的类定义
- 强制 JWT_SECRET 从环境变量读取
- 移除硬编码管理员密码
- 限制用户注册只能为 user 角色
- 修复 XSS 漏洞（v-html -> 文本渲染）
- 重写 deploy.sh 使用 SSH 密钥
- 添加生产环境配置文件"

# 推送（可选）
git push origin main
```

---

## 📚 参考文档

- 详细修复说明：`/Users/jarod/Dev/new/.opencode/plans/p0-security-fixes.md`
- 备份目录：`/Users/jarod/Dev/new.backup.{日期时间}/`

---

## ⚠️ 重要提醒

1. **修改 .env.prod 中的默认密码**后再部署
2. 生产环境必须使用强 JWT 密钥（64字符以上）
3. 首次启动后，如果未设置 `ADMIN_PASSWORD`，请查看日志获取临时密码
4. 配置 SSH 密钥后再使用新的 `deploy.sh`

---

**创建日期**: 2026-02-19  
**修复版本**: 1.0
