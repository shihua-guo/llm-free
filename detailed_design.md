# LLM-Free 项目详细设计文档

## 1. 项目概述
**LLM-Free** 是一个基于 LiteLLM 构建的智能路由后端，旨在整合各大主流 LLM 平台的免费额度。通过自动化的错误监测、优先级路由和持久化状态管理，为外部工具提供一个稳定、高可用且“白嫖”到底的统一 OpenAI 兼容接口。

## 2. 核心目标
1. **统一接口**：提供完全兼容 OpenAI API 格式的 REST 接口。
2. **自动切换**：当当前模型返回“额度耗尽”错误时，自动按预设优先级切换到下一个可用模型。
3. **分流分层**：根据任务类型（文本、向量、视觉）自动路由到不同的模型池。
4. **持久化监控**：使用 PostgreSQL 记录每个模型的可用状态，并在额度耗尽后进入冷却期。

## 3. 技术栈
- **语言**: Python 3.10+
- **核心框架**: [LiteLLM](https://github.com/BerriAI/litellm) (处理多模型兼容与路由)
- **API 框架**: FastAPI (高性能异步 API)
- **数据库**: PostgreSQL (存储模型状态、冷却标记)
- **数据库驱动**: SQLAlchemy (Async) + asyncpg
- **任务队列/重试**: LiteLLM 内置 Router 机制

## 4. 详细设计

### 4.1 优先级模型列表 (Priority Model Pools)
系统预置三大模型池，严格按照提供的顺序进行轮询切换。

#### A. 文本/对话模型池 (`TEXT_MODELS`)
顺序（部分展示）：`qwen3.5-plus` -> `qwen3.5-plus-2026-02-15` -> ... -> `opennlu-v1`

#### B. 向量模型池 (`EMBEDDING_MODELS`)
顺序：`tongyi-embedding-vision-flash` -> `text-embedding-v4` -> ... -> `text-embedding-v2`

#### C. 视觉模型池 (`VISION_MODELS`)
顺序：`qwen-image-plus-2026-01-09` -> `wan2.6-i2v-flash` -> ... -> `wanx-style-repaint-v1`

### 4.2 路由与异常逻辑
1. **请求分发**：API 接收到请求后，根据请求路径（`/v1/chat/completions`, `/v1/embeddings`, `/v1/images/generations`）定位到对应的模型池。
2. **故障转移 (Failover)**：
   - 使用 LiteLLM `Router` 模式。
   - 配置 `enable_pre_call_checks=True`，在调用前过滤掉数据库中标记为“已耗尽”的模型。
   - 捕获 `QuotaExceededError` (429/403 等)。
3. **状态标记**：
   - 一旦捕获到额度耗尽错误，立即向 PostgreSQL 写入一条冷却记录。
   - 冷却策略：默认冷却 24 小时或直到次日 0 点（根据平台重置规则）。

### 4.3 数据库 Schema (`PostgreSQL`)
```sql
CREATE TABLE model_status (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50),      -- 例如 'dashscope'
    model_name VARCHAR(100),   -- 例如 'qwen-plus'
    is_available BOOLEAN DEFAULT TRUE,
    last_error_type VARCHAR(50),
    cool_down_until TIMESTAMP, -- 冷却结束时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.4 接口定义
- **POST `/v1/chat/completions`**: 转发至文本池。
- **POST `/v1/embeddings`**: 转发至向量池。
- **POST `/v1/images/generations`**: 转发至视觉池。
- **GET `/status`**: 查看当前各个模型的额度存活状态。

## 5. 部署说明
- **环境**: Windows/Linux (Python 环境)
- **数据库连接**: `postgresql+asyncpg://admin:password@192.168.2.200:5432/llm_free`
- **配置文件**: `config.py` 存放所有 API_KEY。

## 6. 待确认细节 (Q&A)
1. **API Key 来源**：目前列表基本属于阿里千问（DashScope），是否所有模型共享同一个 API Key？如果是，一旦 API Key 层面被限流，是否需要支持多个 Key 的轮询？
2. **视觉模型接口标准**：视觉模型池中包含视频生成（Wan2.6等）和图像编辑，这些在 OpenAI 标准接口中并没有完全对应的定义。是否统一映射到 `/v1/images/generations`？
3. **冷却重置规则**：大部分免费额度是按天重置的。我们是否需要在每天凌晨 0 点自动清空数据库中的 `is_available=FALSE` 记录？

---
**设计文档已生成。请确认上述细节，如果无误，我将开始准备环境并编写核心代码。**
