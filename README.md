
## 核心功能

### 1. 🤖 智能对话
- 基于 LangChain Agent 架构，集成 DeepSeek 大语言模型
- 支持流式输出（SSE），逐字返回响应给前端
- 使用 InMemorySaver 实现对话记忆，支持多轮会话上下文保持

### 2. 🍜 菜品查询
- **特色主菜查询**：从 PostgreSQL 查询 `is_featured = true` 的特色菜品
- **口味偏好搜索**：基于用户口味描述，使用 BGE-M3 模型向量化后，在 Milvus 向量数据库中进行语义检索，返回最匹配的 Top 3 菜品

### 3. 📅 餐厅预订
- 支持多参数预订（人数、儿童数、到达时间、座位偏好、主菜偏好、备注）
- Agent 自动引导用户补充缺失信息，二次确认后写入 PostgreSQL 数据库

### 4. ❓ FAQ 智能匹配
- FAQ 数据存储在 Redis Hash Map 中
- 采用双重相似度算法：SequenceMatcher（序列匹配）+ Jaccard（词袋相似度）加权计算
- 根据用户 query 自动匹配最相关的 FAQ 并返回

### 5. 📋 数据管理 API
- `/reservation/list`：查询预订列表
- `/menu/list`：查询全部可用菜品

## 技术栈

| 层级 | 技术 |
|------|------|
| **LLM** | DeepSeek V3/V4（通过 OpenAI 兼容 API） |
| **Agent 框架** | LangChain + LangGraph |
| **向量模型** | BGE-M3（HuggingFace 本地加载） |
| **向量数据库** | Milvus |
| **关系数据库** | PostgreSQL（psycopg2 + SQLAlchemy 连接池） |
| **缓存** | Redis（FAQ 存储 + 快速匹配） |
| **后端** | FastAPI + SSE 流式响应 |
| **前端** | Vue 3 + Vite |
| **包管理** | uv（Python）/ pnpm（Node.js） |

## 环境变量配置

在项目根目录创建 `.env` 文件：

```env
# LLM 模型配置
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-your-deepseek-api-key
MODEL_NAME=deepseek-v3-flash

# PostgreSQL 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DATABASE=menu

# Redis 配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# Milvus 向量数据库配置
MILVUS_URI=http://localhost:19530
MILVUS_TOKEN=your-milvus-token
```

## 快速开始

### 1. 环境要求

- Python >= 3.13
- Node.js >= 18
- PostgreSQL（需创建 `menu` 数据库）
- Redis（需开启密码认证）
- Milvus 向量数据库

### 2. 初始化数据库

```bash
# 连接 PostgreSQL 并执行建表脚本
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USERNAME -d menu -f postgres-menu.sql
```

### 3. 同步数据

```bash
# 同步菜品数据到 Milvus 向量数据库
python agent/milvus_data_sync.py

# 同步 FAQ 数据到 Redis
python agent/redis_data_sync.py
```

### 4. 安装依赖

```bash
# Python 依赖（使用 uv）
uv sync

# 前端依赖
cd ui && npm install
```

### 5. 下载 BGE-M3 模型

```bash
# 下载 BGE-M3 embedding 模型到 models/ 目录
# 模型文件约 2.2GB，可从 HuggingFace 下载
# https://huggingface.co/BAAI/bge-m3
mkdir -p models/bge-m3
```

### 6. 启动服务

```bash
# 启动后端（端口 8000）
python run.py

# 启动前端（端口 3000，API 自动代理到后端）
cd ui && npm run dev
```

访问 `http://localhost:3000` 即可使用智能餐厅助手。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat` | 聊天接口（SSE 流式响应） |
| GET | `/faq/suggest` | FAQ 智能匹配建议 |
| GET | `/reservation/list` | 查询预订列表 |
| GET | `/menu/list` | 查询可用菜品列表 |

## Agent 工具链

| 工具 | 说明 |
|------|------|
| `search_main_dishes` | 查询特色主菜（PostgreSQL） |
| `user_flavor_search` | 基于用户口味的语义搜索（Milvus + BGE-M3） |
| `make_reservation` | 餐厅预订（写入 PostgreSQL） |

## 数据流
