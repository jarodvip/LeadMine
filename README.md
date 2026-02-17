# LeadMine 线索矿工

热点新闻采集与销售线索挖掘系统

## 技术栈

- **后端**: Python 3.11 + FastAPI
- **数据库**: MySQL 8.0 + Redis
- **搜索引擎**: Elasticsearch
- **前端**: Vue 3 + Element Plus
- **部署**: Docker + Docker Compose

## 快速开始

### 1. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 2. 访问服务

| 服务 | 地址 |
|------|------|
| 后端API | http://localhost:8000 |
| API文档 | http://localhost:8000/docs |
| Elasticsearch | http://localhost:9200 |
| RSSHub | http://localhost:1200 |

### 3. 默认账户

- 用户名: admin
- 密码: admin123

## 项目结构

```
backend/
├── app/
│   ├── api/           # API路由
│   ├── core/          # 核心配置
│   ├── models/        # 数据库模型
│   ├── schemas/       # Pydantic模型
│   ├── services/      # 业务逻辑
│   └── main.py        # 应用入口
├── scrapers/          # 爬虫模块
├── processors/        # 数据处理器
└── requirements.txt   # Python依赖
```

## API接口

### 认证

- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `GET /api/v1/auth/me` - 获取当前用户

### 线索管理

- `GET /api/v1/leads` - 获取线索列表
- `GET /api/v1/leads/{id}` - 获取线索详情
- `POST /api/v1/leads` - 创建线索
- `PATCH /api/v1/leads/{id}` - 更新线索
- `DELETE /api/v1/leads/{id}` - 删除线索
- `GET /api/v1/leads/stats/dashboard` - 仪表盘统计

### 文章管理

- `GET /api/v1/articles` - 获取文章列表
- `GET /api/v1/articles/{id}` - 获取文章详情

### 数据源管理

- `GET /api/v1/sources` - 获取数据源列表
- `POST /api/v1/sources` - 创建数据源
- `PATCH /api/v1/sources/{id}` - 更新数据源
- `DELETE /api/v1/sources/{id}` - 删除数据源
- `POST /api/v1/sources/{id}/crawl` - 手动触发抓取

## 开发

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload
```

## License

MIT
