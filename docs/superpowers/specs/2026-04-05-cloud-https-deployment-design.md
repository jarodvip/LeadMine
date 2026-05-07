# LeadMine 云服务器 HTTPS 部署设计

## 文档定位

本文档定义 LeadMine 在 Debian 12 单机云服务器上的最小生产部署方案，目标是基于仓库现有部署脚本与 Docker Compose 编排，完成 `lbu.me` 主站 HTTPS 上线，并将 `www.lbu.me` 永久重定向到主站。

## 当前状态说明

仓库当前已经具备基于 Docker Compose 的部署基础，包括 [`deploy.sh`](../../../deploy.sh)、[`docker-compose.prod.yml`](../../../docker-compose.prod.yml)、[`docker-compose.https.yml`](../../../docker-compose.https.yml) 与 [`nginx/nginx.conf`](../../../nginx/nginx.conf)。

但当前生产 HTTPS 链路尚未真正闭合，主要差异如下：

- `deploy.sh` 默认上传并启动的是 `docker-compose.prod.yml`，未切换到 HTTPS 生产编排。
- `nginx/nginx.conf` 当前只监听 `80`，未声明 `443 ssl`、证书路径或域名跳转规则。
- `setup-ssl.sh` 当前只按单域名 `certbot` 申请证书，不满足 `lbu.me` + `www.lbu.me` 双域名证书需求。
- `web/.env.production` 当前仍写死 `http://152.32.189.185/api/v1`，与正式 HTTPS 域名不一致。

本文档描述的是本轮要落地的部署目标与所需补齐项，不代表这些项已经在仓库中全部实现。

## 最后校准时间

2026-04-05

## 1. 目标与约束

### 1.1 部署目标

- 目标服务器：`152.32.189.185`
- 操作系统：Debian 12
- SSH 用户：`root`
- 主站域名：`https://lbu.me`
- 别名域名：`https://www.lbu.me`，返回 `301` 到 `https://lbu.me`
- 部署方式：保留“本地构建 + 脚本上传 + 远端 Docker Compose 启动”主路径

### 1.2 设计约束

- 不引入 CI/CD、镜像仓库或多机编排，保持单机最小可行上线。
- 不改变现有应用架构，只补齐云服务器初始化、HTTPS 配置与部署脚本缺口。
- 证书使用 Let's Encrypt，避免长期维护自签名或手工复制证书。
- 上线前必须显式设置强 `JWT_SECRET` 与 `ADMIN_PASSWORD`，不接受随机临时密码作为正式环境口径。

## 2. 推荐方案

### 2.1 方案概述

采用“本地构建 + 远端运行”的单机 Docker Compose 方案：

1. 本地构建前端产物 `web/dist`
2. 本地准备 `.env.prod`
3. 初始化 Debian 12 服务器基础环境
4. 申请 `lbu.me` 与 `www.lbu.me` 双域名证书
5. 使用部署脚本上传后端、前端产物、Nginx 配置、Compose 文件与环境变量
6. 在服务器 `/opt/leadmine` 下执行 `docker compose up -d --build`
7. 用 HTTPS 域名与容器健康状态做验收

### 2.2 方案理由

该方案与仓库现有结构最一致，能最大程度复用当前的部署脚本、Compose 文件与 Nginx 静态资源分发方式，避免在首次正式上线前引入额外基础设施复杂度。

## 3. 部署架构

### 3.1 运行拓扑

生产服务器采用单机容器编排，最小必需组件如下：

- `mysql`：主数据库
- `redis`：缓存与内部依赖服务
- `backend`：FastAPI 应用
- `nginx`：前端静态资源服务与反向代理终结 HTTPS

可选组件如下：

- `elasticsearch`：当前代码可连接，但不作为本轮上线必需项
- `rsshub`：用于特定微信来源场景，不作为站点主入口运行必需项
- `certbot`：用于证书续期，可作为独立容器或宿主机任务补充

### 3.2 请求流

```
Browser
  -> 80/tcp  -> nginx (仅用于 ACME challenge 或 HTTP -> HTTPS 跳转)
  -> 443/tcp -> nginx (TLS 终结)
                 -> /            返回 web/dist 静态页面
                 -> /api/*       反向代理到 backend:8000
                 -> /docs        反向代理到 backend:8000/docs
                 -> /health      反向代理到 backend:8000/health
```

### 3.3 域名策略

- `server_name lbu.me`：作为唯一主站
- `server_name www.lbu.me`：返回 `301 https://lbu.me$request_uri`
- HTTP 入口保留用于证书申请与统一跳转，不对外提供明文业务访问

## 4. 配置边界

### 4.1 服务器初始化要求

Debian 12 首次部署前需完成以下准备：

- 安装 Docker Engine
- 安装 Docker Compose plugin
- 安装 `rsync`
- 安装 `certbot`
- 开放 `22`、`80`、`443` 端口
- 配置 SSH 公钥认证

出于最小可行原则，本轮不强制引入 `ufw`/`fail2ban` 自动化脚本，但防火墙与 SSH 加固应作为上线后第一批补强项。

### 4.2 环境变量基线

生产 `.env.prod` 至少包含以下项：

- `DATABASE_URL`
- `REDIS_URL`
- `ELASTICSEARCH_URL`
- `JWT_SECRET`
- `ADMIN_PASSWORD`
- `CORS_ORIGINS`

建议值要求如下：

- `JWT_SECRET` 使用 `openssl rand -base64 64` 生成强密钥
- `ADMIN_PASSWORD` 使用高强度初始密码，禁止留空
- `CORS_ORIGINS` 至少包含 `https://lbu.me,https://www.lbu.me`
- 前端 `VITE_API_URL` 改为 `https://lbu.me/api/v1`

### 4.3 前端 API 基址

当前 [`web/.env.production`](../../../web/.env.production) 指向 `http://152.32.189.185/api/v1`。生产部署必须改为正式域名 HTTPS 地址，否则浏览器会出现混合内容或跨域问题。

## 5. 需要补齐的实现项

### 5.1 Nginx 生产 HTTPS 配置

需要新增或拆分生产 Nginx 配置，满足以下行为：

- `listen 80` 为 `lbu.me` 和 `www.lbu.me` 提供 ACME challenge 与 301 跳转
- `listen 443 ssl http2` 为 `lbu.me` 提供正式站点入口
- `listen 443 ssl http2` 为 `www.lbu.me` 提供 301 跳转
- 显式声明 `ssl_certificate` 与 `ssl_certificate_key`
- 保留 `/api`、`/docs`、`/openapi.json`、`/health` 的后端代理
- 保留 SPA `try_files` 行为用于 Vue Router history 模式

### 5.2 证书申请脚本

现有 [`setup-ssl.sh`](../../../setup-ssl.sh) 需要补强为双域名模式，至少支持：

- `certbot certonly --standalone -d lbu.me -d www.lbu.me`
- 证书输出路径与 Nginx 挂载路径解耦，不再硬编码为 `localhost`
- 续期命令可复用同一目录结构

### 5.3 部署脚本

现有 [`deploy.sh`](../../../deploy.sh) 需要补齐以下能力：

- 首次部署前检测服务器是否已安装 Docker/Compose，并给出明确失败原因
- 上传 HTTPS 版 Compose 文件与对应 Nginx 配置
- 兼容证书目录同步或宿主机证书挂载方式
- 继续保留数据库备份、代码同步与健康检查逻辑
- 发布完成后使用 `https://lbu.me/health` 或容器内健康检查做最终验收

### 5.4 服务器初始化脚本

新增宿主机初始化脚本，负责 Debian 12 基础软件安装与启动 Docker 服务。该脚本只覆盖首次准备，不负责业务发布。

## 6. 发布流程

### 6.1 首次上线

1. 在本地修正生产配置：前端 API 地址、Nginx HTTPS 配置、部署脚本目标编排。
2. 在本地生成 `.env.prod` 并填入正式强密钥。
3. 执行服务器初始化脚本，安装 Docker、Compose plugin、certbot、rsync。
4. 确认 DNS：`lbu.me` 与 `www.lbu.me` 都解析到 `152.32.189.185`。
5. 申请双域名 Let's Encrypt 证书。
6. 在本地构建 `web/dist`。
7. 执行部署脚本，将应用内容同步到 `/opt/leadmine`。
8. 在服务器启动容器并执行健康检查。

### 6.2 后续发布

1. 本地更新代码
2. 本地重新构建 `web/dist`
3. 重新执行部署脚本
4. 验证健康检查、首页访问和域名跳转

## 7. 回滚与恢复

### 7.1 回滚原则

本轮回滚采用“保留上一次可运行目录与环境备份”的简单策略，不引入镜像版本或数据库迁移框架。

### 7.2 回滚动作

- 部署前备份现有 `.env` 与数据库 dump
- 新版本启动失败时停止新容器
- 恢复上一个可用的 Compose 文件与环境变量
- 使用备份数据恢复数据库，仅在确认新版本对数据库造成破坏时执行

### 7.3 不在本轮范围内的恢复能力

- 自动化蓝绿发布
- 多版本镜像回滚
- 零停机数据库迁移框架

## 8. 验证与验收

### 8.1 自动化检查

- `docker compose ps`
- `docker compose logs backend --tail=100`
- `docker compose logs nginx --tail=100`
- 容器内 `/health` 检查

### 8.2 人工验收标准

- `https://lbu.me` 可打开前端首页
- `https://www.lbu.me` 返回 `301` 到 `https://lbu.me`
- `https://lbu.me/health` 返回健康状态
- `https://lbu.me/docs` 可访问
- 首次登录可使用显式设置的管理员密码，不依赖日志中的临时密码

## 9. 风险与取舍

### 9.1 已知风险

- 若 DNS 未完全生效，Let's Encrypt 证书申请会失败。
- 若仍沿用当前 HTTP `VITE_API_URL`，浏览器会出现 HTTPS 页面调用 HTTP API 的混合内容问题。
- 若保留当前仅 `listen 80` 的 Nginx 配置，部署完成后只能提供 HTTP，无法满足正式上线要求。
- 若 `ADMIN_PASSWORD` 留空，后端会在首次启动时生成临时密码并写日志，不符合正式环境可控交付要求。

### 9.2 本轮取舍

- 接受单机部署，优先完成可用 HTTPS 正式环境。
- 接受手工触发部署脚本，不引入 CI/CD。
- 接受简单备份回滚，不扩展到复杂发布平台。

## 10. 实施边界

本设计只覆盖以下内容：

- Debian 12 单机初始化
- `lbu.me` / `www.lbu.me` HTTPS 正式上线
- 现有部署脚本与 Nginx/Compose 生产配置补齐

本设计不覆盖以下内容：

- GitHub Actions 或其他 CI/CD
- 镜像仓库发布流
- 多环境分层（staging/prod）
- 多机高可用、监控告警系统、自动扩缩容
