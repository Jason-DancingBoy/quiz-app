# RAGAS 评估集成 — 设计文档

## 概述

为 quiz-app 的 RAG 管线（ChromaDB 检索 + DeepSeek 出题）集成 RAGAS 评估框架，实现全自动 LLM-as-judge 评估，无需人工标注 ground truth。

## 架构

```
backend/
├── tests/
│   ├── test_ragas_eval.py         ← pytest 入口（只验证脚本跑通 + 输出文件存在）
│   └── ragas_eval/
│       ├── __init__.py
│       ├── runner.py              ← 核心：采样 → 跑管线 → 评分 → 输出
│       ├── metrics.py             ← 指标：RAGAS 标准 + 自定义质量评分 + JSON 预处理
│       └── reporter.py            ← 输出：JSON + history + 人类可读报告
├── services/
│   ├── rag_service.py             ← 复用：query_for_quiz()
│   └── generator.py               ← 复用：generate_quiz()
└── requirements-dev.txt           ← 新增：ragas, langchain-openai
```

### 数据流

```
可用 doc_id（ChromaDB 中有 chunks 的）
  │
  ├─→ 按 difficulty 分层：easy / medium / hard
  │
  ├─→ 对每个 (doc_id, difficulty) 组合：
  │     ├─ [1] 取文档原始 chunks → _build_query_from_chunks(chunks, difficulty) → 检索 query
  │     ├─ [2] query_for_quiz(doc_id, difficulty, chunks) → retrieved_contexts
  │     ├─ [3] generate_quiz(contexts, difficulty, count=3, temperature=0) → JSON 题目
  │     ├─ [4] 预处理：content + options + explanation → 自然语言段落文本
  │     ├─ [5] RAGAS 标准指标评分（ContextRelevancy, ContextPrecision, Faithfulness）
  │     └─ [6] 自定义指标：格式合规率 + 题目质量评分
  │
  └─→ 输出：
        ragas_results_latest.json     ← 当前运行完整结果
        ragas_results_history.jsonl   ← 追加历史记录（含 commit hash）
        ragas_report.txt              ← 人类可读摘要
```

## 指标设计

### RAGAS 标准指标

| 指标 | 测量目标 | 映射 |
|------|---------|------|
| Context Relevancy | 检索是否相关 | query=`_build_query_from_chunks()` 检索词, contexts=`query_for_quiz()` 返回 |
| Context Precision | 相关 chunks 是否排前面 | 同上，ChromaDB 返回顺序即相似度排序 |
| Faithfulness | 生成是否忠于上下文 | response=预处理后的自然语言文本（非原始 JSON） |

### Faithfulness 预处理

原始 JSON 会使 RAGAS claim extraction 抽取 `correct_index: 2` 等格式主张。送入 Faithfulness 前，将题目转为自然语言段落：

```
题目：什么是 Agent Loop？
选项：A. xxx  B. xxx  C. xxx  D. xxx
正确答案：C
解析：Agent Loop 是...（原文依据）
```

### 自定义指标

| 指标 | 评估方式 | 原因 |
|------|---------|------|
| 格式合规率 | 正则校验：合法 JSON、4 选项、correct_index∈[0,3] | 非 RAGAS 领域 |
| 题目质量 | LLM 逐题评分 1-5：正确选项唯一性、干扰项是否来自文档、解析是否有原文依据 | RAGAS 无此指标 |

### 输出聚合

```json
{
  "commit": "abc123",
  "timestamp": "2026-07-29T10:00:00Z",
  "config": {"seed": 42, "temperature": 0, "difficulties": ["easy","medium","hard"]},
  "aggregate": {
    "context_relevancy": {"mean": 0.85, "std": 0.08},
    "context_precision": {"mean": 0.82, "std": 0.10},
    "faithfulness": {"mean": 0.78, "std": 0.12},
    "format_compliance": {"rate": 1.0},
    "question_quality": {"mean": 4.2, "std": 0.6}
  },
  "by_difficulty": { "easy": {...}, "medium": {...}, "hard": {...} },
  "by_doc_length": { "short": {...}, "medium_len": {...}, "long": {...} },
  "samples": [{"doc_id": 3, "difficulty": "easy", "faithfulness": 0.85, ...}]
}
```

## 样本策略

- **全量覆盖**：所有 ChromaDB 中有 chunks 的 doc_id（当前 16 个），不做随机采样
- **分层**：easy / medium / hard 三个难度各自跑一轮
- **单样本参数**：每个 (doc_id, difficulty) 生成 3 道题（count=3）
- **预计样本量**：≥ 48（16 docs × 3 difficulties，部分短文档可能不足 3 题）
- **分组**：按难度 + 按文档长度（<6000 / 6000-15000 / >15000 字符）两组维度汇报

## 可复现性

| 随机源 | 措施 |
|--------|-----|
| generate_quiz() temperature | 0（生产用 0.7，评估专用 0） |
| RAGAS judge LLM temperature | 0 |
| Python random | seed=42 |
| 输出追踪 | 每条记录含 commit_hash + timestamp + 完整 config |

## 技术实现

### 依赖

```
# requirements-dev.txt（新增文件）
ragas==0.2.10
langchain-openai==0.3.0
```

### DeepSeek 适配

```python
from langchain_openai import ChatOpenAI
from ragas.llms import LangchainLLMWrapper

evaluator_llm = LangchainLLMWrapper(ChatOpenAI(
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    temperature=0,
))
```

### 文件职责

| 文件 | 行数 | 职责 |
|------|------|------|
| tests/ragas_eval/runner.py | ~120 | 采样、调 pipeline、收集样本、计算 metric、聚合 |
| tests/ragas_eval/metrics.py | ~60 | 初始化 RAGAS metric + 自定义 quality metric + JSON 预处理 |
| tests/ragas_eval/reporter.py | ~40 | JSON/history/report 三种格式输出 |
| tests/test_ragas_eval.py | ~15 | pytest 入口，检查脚本成功 + 输出文件存在 |

### CI 支持

- 环境变量 `RAGAS_CI=1`：启用分数阈值断言（faithfulness < 0.6 fail），跳过耗时步骤
- 默认（手工）：不设阈值，输出完整报告

### 错误处理

- ChromaDB 无数据 → warning，跳过
- DeepSeek API 不可用 → 记录 error，跳过该样本，继续下一条
- 单条生成失败 → 记录到 errors 列表，不中断整体评估
