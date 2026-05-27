# RAG 八股文面试知识库系统

![Java](https://img.shields.io/badge/Java-21-orange)
![Spring Boot](https://img.shields.io/badge/SpringBoot-3.4.4-green)
![Spring AI](https://img.shields.io/badge/Spring%20AI-1.0.0-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-PgVector-blue)
![Redis](https://img.shields.io/badge/Redis-Cache-red)
![License](https://img.shields.io/badge/license-MIT-brightgreen)

---

基于 **Spring Boot + Spring AI** 的 RAG 面试知识库系统，面向 Java、MySQL、Redis、操作系统、计算机网络、分布式等八股文场景，支持 **文档入库、向量检索、全文检索、混合召回、查询重写、重排序以及 AI 问答**。

系统通过 **PgVector 向量数据库 + PostgreSQL 全文检索 + Rerank 重排序** 构建高质量检索链路，并结合 **Markdown 文档切分、中文分词、关键词增强、HyDE / Multi-Query 查询改写** 提升复杂面试问题的召回效果。

系统内置 **RAG 问答接口与管理入口**，支持上传 Markdown 文档自动入库、检索结果调试、A/B 测试不同召回策略，适合作为个人面试知识库、RAG 学习项目或 AI 应用工程实践项目。

---

# 技术栈

## 后端框架
- **Spring Boot** 3.4.4
- **Spring AI** 1.0.0
- **Java** 21

## AI 能力
- **通义千问 / DashScope** — 查询重写、Embedding、Rerank
- **OpenAI 兼容接口** — 对话模型调用
- **PgVector** — 向量存储与相似度检索

## 数据与检索
- **PostgreSQL** — 文档元数据与全文检索
- **PgVector** — 向量索引与语义召回
- **Redis** — 缓存与运行时辅助能力
- **HNSW** — 向量索引加速

## 核心依赖
- **spring-ai-pgvector-store** — PgVector 向量库集成
- **spring-ai-markdown-document-reader** — Markdown 文档读取
- **spring-ai-advisors-vector-store** — Spring AI 向量检索增强
- **spring-ai-alibaba-starter-dashscope** — 阿里云 DashScope 模型接入
- **Lombok** — 简化 Java 代码

---

# 系统架构

```text
                  User
                   │
                   ▼
              Web / API Client
                   │
                   ▼
           Spring Boot Application
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   Query Rewrite  Hybrid     Document
   / HyDE         Retriever  Ingestion
        │          │          │
        │     ┌────┴────┐     │
        │     ▼         ▼     ▼
        │  Vector     Full-Text  Markdown Docs
        │  Search     Search     Splitter
        │     │         │
        └─────┼─────────┘
              ▼
            Reranker
              │
              ▼
        LLM Answer Generator
              │
              ▼
          RAG Response

         PostgreSQL + PgVector
                │
              Redis
```

系统采用 **RAG 检索增强生成架构**：

- **文档入库**：读取本地 Markdown 文档，按照标题与语义结构进行切分
- **关键词增强**：为文档块补充关键词，提高精确匹配能力
- **向量化存储**：调用 Embedding 模型生成向量，写入 PgVector
- **混合检索**：结合向量检索与全文检索，提高召回覆盖率
- **查询重写**：通过 Multi-Query / HyDE 扩展用户问题，提高复杂问题命中率
- **重排序**：使用 Rerank 模型对候选文档重新打分，提升上下文质量
- **AI 回答**：基于召回上下文调用大模型生成结构化中文面试回答

---

# 核心功能

## 文档知识库模块
- 支持 Markdown 文档作为知识来源
- 支持 JavaGuide、小林 Coding 等技术文档数据集
- 支持按目录批量加载文档
- 支持上传 Markdown 文档并自动入库

## 文档切分模块
- Markdown 标题结构切分
- Token 长度控制
- 语义分块处理
- 文档 Hash 去重

## 检索增强模块
- PgVector 向量语义检索
- PostgreSQL 全文检索
- Hybrid 混合召回
- 中文分词优化
- 关键词增强召回

## 查询优化模块
- Query Rewrite 查询重写
- Multi-Query 多查询扩展
- HyDE 假设答案生成
- 面试问题语义增强

## 重排序模块
- 调用 Rerank 模型对候选文档重新排序
- 降低无关文档进入上下文的概率
- 提升最终回答准确性

## RAG 问答模块
- 根据参考资料回答面试问题
- 支持不知道时拒绝编造
- 返回答案与召回上下文
- 支持检索接口独立调试
- 支持 A/B 测试开关：rewrite、fts、vector、rerank

## 运维与管理模块
- RAG 文档监控
- 文档数量检查
- 管理页访问控制
- API Key 访问控制
- 文档上传入口

---

# 项目结构

```text
RAG/
├── src/main/java/com/example/rag/
│   ├── RagApplication.java                 # Spring Boot 启动类
│   │
│   ├── config/                             # Web 与安全配置
│   │   ├── SecurityProperties.java
│   │   └── WebConfig.java
│   │
│   ├── controller/                         # 接口层
│   │   ├── AiController.java               # RAG 检索与问答接口
│   │   ├── UploadController.java           # 文档上传与入库接口
│   │   └── StaticPageController.java       # 静态页面转发
│   │
│   ├── filter/                             # 访问控制过滤器
│   │   ├── AdminAuthFilter.java
│   │   └── ApiKeyAuthFilter.java
│   │
│   ├── opagent/                            # 运行监控
│   │   └── RagMonitor.java
│   │
│   └── rag/                                # RAG 核心模块
│       ├── ChineseTokenizer.java           # 中文分词
│       ├── FullTextSearchRetriever.java    # 全文检索
│       ├── HybridRetriever.java            # 混合检索
│       ├── HybridVectorStoreAdapter.java   # 向量库适配
│       ├── IngestionService.java           # 文档入库服务
│       ├── LoveAppDocumentLoader.java      # 文档加载器
│       ├── MarkdownHeadingSplitter.java    # Markdown 标题切分
│       ├── MyKeywordEnricher.java          # 关键词增强
│       ├── MyTokenTextSplitter.java        # Token 文本切分
│       ├── PgVectorVectorStoreConfig.java  # PgVector 配置
│       ├── QueryRewriter.java              # 查询重写
│       ├── Reranker.java                   # 重排序
│       └── SemanticSplitter.java           # 语义切分
│
├── src/main/resources/
│   ├── application.yml                     # 主配置
│   ├── application-dev.yml                 # 开发环境配置
│   ├── application-prod.yml                # 生产环境配置
│   ├── application-security.yml            # 安全配置
│   └── document/                           # 本地知识库文档
│       ├── javaguide/
│       └── xiaolincoding/
│
├── cleanup_docs.py                         # 文档清洗脚本
├── crawl_javaguide.py                      # JavaGuide 文档采集脚本
├── crawl_xiaolin.py                        # 小林 Coding 文档采集脚本
├── generate_test_data.py                   # 测试数据生成脚本
├── rag_test_cases.json                     # RAG 测试问题集
├── pom.xml
└── README.md
```

---

# 快速开始

## 环境要求

- JDK 21+
- Maven 3.8+
- PostgreSQL 14+
- PgVector 扩展
- Redis
- DashScope API Key 或 OpenAI 兼容模型 API Key

---

## 数据库准备

PostgreSQL 需要启用 PgVector 扩展：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

建议创建独立数据库：

```sql
CREATE DATABASE ai_agent;
```

---

## 配置说明

编辑配置文件：

```text
src/main/resources/application-dev.yml
```

示例配置：

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/ai_agent
    username: your_username
    password: your_password

  ai:
    dashscope:
      api-key: your_dashscope_api_key
      chat:
        options:
          model: qwen-turbo
      embedding:
        options:
          model: text-embedding-v2

    vectorstore:
      pgvector:
        index-type: HNSW
        dimensions: 1536
        distance-type: COSINE_DISTANCE

  data:
    redis:
      host: localhost
      port: 6379
      password: your_redis_password
      database: 0

custom:
  llm:
    api-key: your_llm_api_key
    url: https://your-openai-compatible-endpoint/v1
    model: your_model_name
```

---

# 启动项目

```bash
mvn spring-boot:run
```

服务默认运行地址：

```text
http://localhost:8123
```

---

# 接口说明

## RAG 问答

```http
GET /rag/chat?question=MySQL索引为什么会失效
```

返回内容包含：

- question：原始问题
- answer：大模型基于知识库生成的回答
- contexts：召回的参考资料片段

---

## 仅检索上下文

```http
GET /rag/retrieve?question=Redis缓存击穿怎么解决
```

用于调试当前问题召回了哪些文档片段。

---

## A/B 测试检索链路

```http
GET /rag/abtest?question=Java线程池参数有哪些&rewrite=true&fts=true&vector=true&rerank=true
```

可独立开关：

- rewrite：查询重写
- fts：全文检索
- vector：向量检索
- rerank：重排序

---

## 上传文档并入库

```http
POST /ops/upload
Content-Type: multipart/form-data

file=@your-document.md
```

上传 Markdown 文档后，系统会保存到本地文档目录并触发入库流程。

---

# 核心技术亮点

## 1 混合检索架构

- **向量检索** 负责语义相似问题召回
- **全文检索** 负责关键词、专有名词、精确表达召回
- **Hybrid Retriever** 融合多路召回结果，提高复杂问题命中率

---

## 2 查询重写与 HyDE

- 将用户原始问题改写为更适合检索的查询
- 通过多查询扩展覆盖不同问法
- 使用 HyDE 生成假设答案，增强语义检索效果

---

## 3 Markdown 知识库入库

- 基于 Markdown 标题结构进行分块
- 结合 Token 长度控制，避免上下文过长
- 保留文档层级信息，提升回答可读性

---

## 4 Rerank 重排序

- 对初步召回文档进行二次排序
- 优先保留与问题强相关的片段
- 降低噪声上下文对回答质量的影响

---

## 5 面试场景回答优化

- 使用中文回答
- 结构化输出重点内容
- 基于资料回答，避免编造
- 适配 Java 后端面试八股文场景

---

# 注意事项

- 请不要将真实 API Key、数据库密码、Redis 密码提交到 GitHub
- 建议使用环境变量或本地配置文件管理敏感信息
- 上传 GitHub 前请确认 target/、.env、application-local.yml 等文件已被 .gitignore 忽略
- 如果配置文件中已经写入真实密钥，建议先替换为占位符再提交

---

# License

MIT License
