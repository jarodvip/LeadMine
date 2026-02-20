# LeadMine HTTPS 部署指南

本指南介绍如何配置 Nginx + HTTPS 部署 LeadMine。

## 🚀 快速开始

### 方式 1: 本地 HTTPS 测试 (自签名证书)

```bash
# 1. 确保已安装 Docker 和 Docker Compose

# 2. 运行部署脚本
./deploy-https-local.sh

# 3. 访问 https://localhost
# 注意: 浏览器会显示安全警告，点击"继续访问"
```

### 方式 2: 生产环境 (Let's Encrypt 证书)

```bash
# 1. 配置域名解析到服务器

# 2. 申请 Let's Encrypt 证书
./setup-ssl.sh letsencrypt your-domain.com admin@your-domain.com

# 3. 使用生产配置启动
docker compose -f docker-compose.https.yml up -d
```

---

## 📁 配置文件说明

### 1. Nginx 配置 (`nginx/nginx.conf`)

主要功能:
- ✅ HTTPS 强制 (HTTP 自动重定向到 HTTPS)
- ✅ TLS 1.2/1.3 支持
- ✅ 安全响应头 (CSP, HSTS, XSS Protection)
- ✅ Gzip 压缩
- ✅ 静态文件缓存
- ✅ API 反向代理
- ✅ WebSocket 支持

### 2. Docker Compose 配置

- **`docker-compose.local-https.yml`**: 本地测试 (自签名证书)
- **`docker-compose.https.yml`**: 生产环境 (Let's Encrypt)

### 3. SSL 证书脚本 (`setup-ssl.sh`)

支持三种模式:
- `self-signed`: 生成自签名证书 (测试用)
- `letsencrypt`: 申请 Let's Encrypt 证书 (生产用)
- `renew`: 续期证书

---

## 🔒 SSL 证书配置

### 自签名证书 (本地测试)

```bash
./setup-ssl.sh self-signed localhost
```

生成的文件:
```
nginx/ssl/
├── localhost.crt          # 证书
├── localhost.key          # 私钥
└── localhost/
    ├── fullchain.pem      # Nginx 使用的完整证书链
    └── privkey.pem        # Nginx 使用的私钥
```

### Let's Encrypt 证书 (生产环境)

```bash
# 1. 安装 certbot
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install certbot

# 2. 申请证书
./setup-ssl.sh letsencrypt your-domain.com your-email@example.com

# 3. 自动续期
certbot renew --dry-run  # 测试续期
```

---

## 🔧 Nginx 配置详解

### 安全头配置

```nginx
# 防止点击劫持
add_header X-Frame-Options "SAMEORIGIN" always;

# 防止 MIME 类型嗅探
add_header X-Content-Type-Options "nosniff" always;

# XSS 保护
add_header X-XSS-Protection "1; mode=block" always;

# Referrer 策略
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# 内容安全策略
add_header Content-Security-Policy "default-src 'self'; ..." always;
```

### 反向代理配置

```nginx
location /api {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

---

## 📊 性能优化

### Gzip 压缩

```nginx
gzip on;
gzip_vary on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json ...;
```

### 静态文件缓存

```nginx
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 6M;
    add_header Cache-Control "public, immutable";
}
```

### 客户端缓存控制

```nginx
# 不缓存 HTML (SPA 应用)
location / {
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

---

## 🛡️ 安全建议

1. **使用强密码**
   ```bash
   # 生成随机密钥
   openssl rand -base64 64
   ```

2. **定期更新证书**
   ```bash
   # Let's Encrypt 证书有效期 90 天
   ./setup-ssl.sh renew
   ```

3. **限制访问**
   - 防火墙只开放 80/443 端口
   - 禁用 root 登录
   - 使用 SSH 密钥认证

4. **日志监控**
   ```bash
   # 查看访问日志
   docker compose logs -f nginx
   
   # 查看 API 错误
   tail -f nginx/logs/api_error.log
   ```

---

## 🐛 故障排除

### 问题 1: 证书错误

**现象**: 浏览器显示 "NET::ERR_CERT_AUTHORITY_INVALID"

**解决**:
- 本地测试: 点击"高级" -> "继续访问 localhost"
- 生产环境: 确保证书已正确配置

### 问题 2: 502 Bad Gateway

**现象**: Nginx 返回 502 错误

**解决**:
```bash
# 检查后端服务是否运行
docker compose ps

# 查看后端日志
docker compose logs backend
```

### 问题 3: 混合内容警告

**现象**: 浏览器控制台显示 Mixed Content 警告

**解决**:
- 确保所有资源使用 HTTPS
- 检查 API 响应中的 HTTP 链接

---

## 📈 监控指标

### 健康检查端点

```bash
# Nginx 健康检查
curl https://localhost/nginx-health

# 后端健康检查
curl https://localhost/health

# API 文档
curl https://localhost/docs
```

### 日志位置

```
nginx/logs/
├── api_access.log      # API 访问日志
├── api_error.log       # API 错误日志
└── error.log           # Nginx 错误日志
```

---

## 📝 常用命令

```bash
# 启动服务
docker compose -f docker-compose.https.yml up -d

# 查看日志
docker compose -f docker-compose.https.yml logs -f

# 重启服务
docker compose -f docker-compose.https.yml restart

# 停止服务
docker compose -f docker-compose.https.yml down

# 查看证书信息
openssl x509 -in nginx/ssl/localhost/fullchain.pem -noout -text
```

---

## 🎯 生产环境检查清单

- [ ] 使用真实域名
- [ ] 配置正确的 SSL 证书
- [ ] 设置强密码 (JWT_SECRET, MySQL, Redis)
- [ ] 启用防火墙 (只开放 80/443)
- [ ] 配置自动备份
- [ ] 设置监控告警
- [ ] 配置日志轮转
- [ ] 测试故障恢复

---

## 📞 支持

如有问题，请检查:
1. Nginx 错误日志: `nginx/logs/error.log`
2. 后端服务日志: `docker compose logs backend`
3. SSL 证书配置: `nginx/ssl/`

---

**文档版本**: 1.0  
**更新日期**: 2026-02-20
