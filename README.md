# 🍽️ LangChain 智能餐厅助手

基于 **LangChain + LangGraph Agent** 架构的智能餐厅问答与预订系统。集成向量检索（Milvus + BGE-M3）、FAQ 匹配（Redis）、大语言模型（DeepSeek），提供菜品推荐、餐厅预订、FAQ 问答等智能化服务。前端基于 **Vue 3 + Element Plus**，后端基于 **FastAPI + SSE 流式响应**。

## 项目架构

```
langchain-smartMenu/
├── agent/                         # Agent 核心代码
│   ├── prompts/
│   │   └── system_prompt.txt      # Agent 系统提示词（角色、能力、注意事项）
│   ├── langchain_assistant.py     # Agent 主体：工具定义、LLM 配置、对话流程、流式输出
│   ├── milvus_data_sync.py        # 菜单数据向量化（BGE-M3）并同步至 Milvus
│   ├── redis_data_sync.py         # FAQ 数据同步至 Redis（Hash + Set）
│   └── redis_demo.py              # Redis 基础命令演示（String/Hash/Set/Pipeline）
├── api/
│   └── main.py                    # FastAPI 后端：聊天(/chat)、FAQ匹配(/faq/suggest)、
│                                  #   预约列表(/reservation/list)、菜单(/menu/list)
├── ui/                            # Vue 3 前端（Element Plus）
│   ├── src/
│   │   ├── App.vue                # 主页面：聊天面板 + 预订信息 + 菜品列表
│   │   ├── main.js                # 前端入口
│   │   └── api/index.js           # Axios 封装：chatAPI / faqAPI / menuAPI / reservationAPI
│   ├── index.html
│   ├── package.json
│   └── vite.config.js             # Vite 配置（端口 3000，API 代理至 8000）
├── postgres-menu.sql              # PostgreSQL 建表脚本（含 menu_items + reservation_order + 示例数据）
├── run.py                         # 后端启动入口：uvicorn api.main:app --port 8000
├── pyproject.toml                 # Python 项目依赖（uv 管理）
└── .env                           # 环境变量配置
```

## 核心功能

### 1. 🤖 智能对话（SSE 流式输出）

- 基于 **LangGraph `create_agent`** 构建 Agent，集成 DeepSeek 大语言模型
- 通过 **SSE（Server-Sent Events）** 实现流式输出，逐字返回响应
- 使用 **InMemorySaver** 实现对话记忆，支持多轮会话上下文保持
- Agent 启动时自动注入当前日期作为 system prompt
- 过滤 ToolMessage，只将文本内容推送给前端

### 2. 🍜 菜品查询

- **特色主菜查询**（`search_main_dishes`）：从 PostgreSQL 查询 `is_featured = true` 的特色菜品，使用 psycopg2 直连
- **口味偏好语义搜索**（`user_flavor_search`）：基于用户口味描述，使用 **BGE-M3 模型**（1024 维）向量化后，在 **Milvus** 中进行 ANN 检索，返回 Top 3 匹配菜品

### 3. 📅 餐厅预订

- 支持多参数预订：`num_people`（人数）、`num_children`（儿童数）、`arrival_time`（到达时间）、`seat_preference`（座位偏好）、`main_dish_preference`（主菜偏好）、`comment`（备注）
- Agent 根据系统提示词自动引导用户补充缺失信息
- 信息齐全后二次确认，确认后才通过 **SQLAlchemy 连接池**写入 PostgreSQL 的 `reservation_order` 表
- 使用 Pydantic `ReservationToolArgsInfo` 定义参数 Schema

### 4. ❓ FAQ 智能匹配

- FAQ 数据存储在 **Redis Hash Map**（每条 FAQ 一个 key）+ **Redis Set**（`faq:all_items` 维护所有 key 索引），采用 **Pipeline 批量操作**
- **双重相似度算法**：
  - **SequenceMatcher**（权重 0.6）：基于最长公共子序列（LCS），捕捉位置相关的字符级相似度
  - **Jaccard 相似度**（权重 0.4）：词袋模型，计算字符集合的交并比
- 前端输入时**实时触发** FAQ 匹配（debounce），展示「您可能想问」建议列表

### 5. 📋 数据管理 API

| 接口 | 说明 |
|------|------|
| `GET /reservation/list` | 查询全部预订列表，按 `created_at` 排序 |
| `GET /menu/list` | 查询全部可用菜品（`is_available = 1`），按分类+菜名排序，含辣度文字映射 |

## 前端功能概览

前端基于 **Vue 3 Composition API + Element Plus**，采用左右双栏布局：

| 区域 | 功能 |
|------|------|
| **左侧：智能对话面板** | 聊天历史展示、流式消息接收、FAQ 自动建议、快捷提问入口、打字动画 |
| **右侧上：预订信息卡片** | 预订列表展示、定时/手动刷新 |
| **右侧下：菜品列表卡片** | 菜品网格展示（名称、价格、分类、辣度、素食标签）、高亮推荐、加入购物车 |

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **LLM** | DeepSeek（通过 OpenAI 兼容 API） | `langchain-openai` 的 `ChatOpenAI` 适配 |
| **Agent 框架** | LangChain + LangGraph | `create_agent` + `InMemorySaver` checkpointer |
| **向量模型** | BGE-M3（HuggingFace 本地加载） | `langchain-huggingface` 的 `HuggingFaceEmbeddings`，1024 维向量 |
| **向量数据库** | Milvus | HNSW 索引 + L2 距离度量，`pymilvus` 客户端 |
| **关系数据库** | PostgreSQL | `psycopg2`（直连查询）+ `SQLAlchemy`（连接池，pool_size=15） |
| **缓存** | Redis | `redis-py` 异步客户端，FAQ 存储 + Pipeline 批量操作 |
| **后端框架** | FastAPI | Pydantic 模型校验 + SSE 流式响应（`text/event-stream`） |
| **前端框架** | Vue 3 + Vite + Element Plus | Composition API + Axios 封装 |
| **异步** | asyncio | `agent.astream()` / `agent.ainvoke()` 异步调用 |
| **包管理** | uv（Python）/ npm（Node.js） | — |

## 环境变量配置

在项目根目录创建 `.env` 文件：

```env
# ========== LLM 模型配置 ==========
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-your-deepseek-api-key
MODEL_NAME=deepseek-v3-flash

# ========== PostgreSQL 数据库配置 ==========
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DATABASE=menu

# ========== Redis 配置 ==========
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# ========== Milvus 向量数据库配置 ==========
MILVUS_URI=http://localhost:19530
MILVUS_TOKEN=your-milvus-token
```

## 数据库 Schema

### menu_items（菜品表）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | SERIAL PK | 菜品 ID |
| `dish_name` | VARCHAR(100) | 菜品名称 |
| `price` | DECIMAL(8,2) | 价格（元） |
| `description` | TEXT | 菜品描述 |
| `category` | VARCHAR(50) | 分类（川菜/鲁菜/素食等） |
| `spice_level` | SMALLINT | 辣度：0-不辣 1-微辣 2-中辣 3-重辣 |
| `flavor` | VARCHAR(100) | 口味特点 |
| `main_ingredients` | TEXT | 主要食材（逗号分隔） |
| `cooking_method` | VARCHAR(50) | 烹饪方法 |
| `is_vegetarian` | BOOLEAN | 是否素食 |
| `allergens` | VARCHAR(200) | 过敏原信息 |
| `is_available` | BOOLEAN | 是否可供应 |
| `is_featured` | BOOLEAN | 是否特色主菜 |

### reservation_order（预订表）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | SERIAL PK | 预订 ID |
| `num_people` | INT | 就餐人数 |
| `num_children` | INT | 0-2 岁儿童人数 |
| `arrival_time` | TIMESTAMP | 到达时间 |
| `seat_preference` | VARCHAR(100) | 座位偏好 |
| `main_dish_preference` | VARCHAR(100) | 主菜偏好 |
| `other_comments` | TEXT | 备注 |
| `created_at` | TIMESTAMP | 创建时间（自动） |
| `updated_at` | TIMESTAMP | 更新时间（触发器自动更新） |

## 快速开始

### 1. 环境要求

- Python >= 3.13
- Node.js >= 18
- PostgreSQL（需创建 `menu` 数据库）
- Redis（需开启密码认证）
- Milvus 向量数据库（需创建 `menu_items` collection）

### 2. 初始化数据库

```bash
# 连接 PostgreSQL 并执行建表脚本（含示例数据）
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USERNAME -d menu -f postgres-menu.sql
```

### 3. 同步数据

```bash
# 将菜品数据向量化并同步到 Milvus（先执行建表脚本）
python agent/milvus_data_sync.py

# 将 FAQ 数据同步到 Redis
python agent/redis_data_sync.py
```

### 4. 安装依赖

```bash
# Python 依赖（使用 uv）
uv sync

# 前端依赖
cd ui && npm install
```

### 5. 下载 Embedding 模型

```bash
# 下载 BGE-M3 embedding 模型到 models/ 目录（约 2.2GB）
# 来源：https://huggingface.co/BAAI/bge-m3
mkdir -p models/bge-m3
```

### 6. 启动服务

```bash
# 启动后端（端口 8000，使用 uvicorn）
python run.py

# 启动前端（端口 3000，Vite 自动代理 /api → localhost:8000）
cd ui && npm run dev
```

访问 **http://localhost:3000** 即可使用智能餐厅助手。

## API 接口

| 方法 | 路径 | 说明 | 请求参数 |
|------|------|------|----------|
| POST | `/chat` | 聊天接口（SSE 流式响应） | `{"query": "..."}` |
| GET | `/faq/suggest` | FAQ 智能匹配建议 | `?query=xxx&limit=5` |
| GET | `/reservation/list` | 查询预订列表 | — |
| GET | `/menu/list` | 查询可用菜品列表 | — |

### SSE 响应数据格式

```json
data: {"content": "\u4f60\u597d", "type": "token"}
data: {"content": "\uff01", "type": "token"}
```

## Agent 工具链

| 工具名称 | 功能 | 数据源 | 说明 |
|----------|------|--------|------|
| `search_main_dishes` | 查询特色主菜 | PostgreSQL（psycopg2 直连） | 返回 `is_featured=true` 的菜品，字段名映射为中文 |
| `user_flavor_search` | 基于口味的语义搜索 | Milvus + BGE-M3 | 用户口味描述 → 向量化 → ANN 检索 → Top 3 菜品 |
| `make_reservation` | 餐厅预订 | PostgreSQL（SQLAlchemy 连接池） | 参数校验通过 Pydantic Schema，使用 `text()` 参数化查询 |

## 数据同步流程

```
┌─────────────────┐     BGE-M3 向量化     ┌──────────────┐
│  PostgreSQL      │ ──────────────────→  │  Milvus       │
│  menu_items 表    │   milvus_data_sync   │  menu_items    │
│                  │                      │  collection   │
└─────────────────┘                      └──────────────┘

┌─────────────────┐     Pipeline 批量写入  ┌──────────────┐
│  FAQ_ITEMS 常量   │ ──────────────────→  │  Redis         │
│  (redis_data_sync)│                      │  Hash + Set    │
└─────────────────┘                      └──────────────┘
```

## FAQ 相似度算法

当用户输入 query 时，系统从 Redis 加载所有 FAQ，对每条 FAQ 计算双重相似度：

```
final_score = 0.6 × SequenceMatcher.ratio(query, question)
            + 0.4 × Jaccard(query, question)
```

| 算法 | 原理 | 特点 |
|------|------|------|
| **SequenceMatcher** | 递归比较最长公共子序列（LCS），`2 × LCS长度 / (len(a) + len(b))` | 捕捉字符位置信息，对语序敏感 |
| **Jaccard 相似度** | `|A ∩ B| / |A ∪ B|`，将字符串转为字符集合 | 只关心字符共现，对语序不敏感 |

两者加权互补，兼顾语序和关键词匹配。

## 常见问题

### Q1: `ModuleNotFoundError: No module named 'sqlalchemy'`

```bash
uv add sqlalchemy
```

### Q2: `relation "reservation_order" does not exist`

数据库表未创建，请执行步骤 2 初始化数据库。

### Q3: `Checkpointer requires one or more of the following 'configurable' keys`

`agent.invoke()` 的 config 参数必须包含 `{"configurable": {"thread_id": "xxx"}}`。

### Q4: 前端 `vite: command not found`

```bash
cd ui && npm install
```

### Q5: Redis 连接认证失败

`.env` 中设置 `REDIS_PASSWORD`，代码中 URL 格式为 `redis://:密码@host:port`。

## 开发说明

- 项目使用 **uv** 管理 Python 依赖，依赖列表见 `pyproject.toml`
- 前端使用 **pnpm** 作为包管理器（`pnpm-lock.yaml`），也兼容 npm
- Agent 的 system prompt 位于 `agent/prompts/system_prompt.txt`，可在此文件中调整 Agent 的行为
- MCP（Model Context Protocol）工具集成代码已预留（`langchain-mcp-adapters`），当前为注释状态，可按需启用
- 生产环境中建议将 `InMemorySaver` 替换为持久化方案（如 `AsyncSqliteSaver` 或 PostgreSQL checkpointer）
