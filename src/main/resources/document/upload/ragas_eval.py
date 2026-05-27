"""RAGAS 生成质量评测（干净版）

做两件事：
1) 调用本地 RAG 服务（默认 `GET http://localhost:8123/rag/chat`）收集：question / answer / contexts
2) 用 RAGAS 计算生成质量指标（默认：faithfulness + answer_correctness）

为什么默认只做 LLM-only 指标：
- 你当前环境里 DashScope 的 OpenAI 兼容 embeddings 接口会报 400/403（会导致 answer_relevancy 等指标全是 NaN）
- RAGAS 在部分版本中即使只算 LLM-only 指标，也会尝试初始化 embeddings 客户端
- 因此这里默认注入一个“纯本地 dummy embeddings”（hash 向量，不发网络请求），保证“能稳定出分 + 速度可控”

关于你贴的最新文档（llm_factory / collections metrics）：
- `ragas.metrics.collections` 这套新指标需要 `llm_factory(...)` 创建的 InstructorLLM
- 你当前工程里更方便的是用 LangChain 的 `ChatOpenAI`（配合 base_url），所以这里使用兼容层 `ragas.metrics` 的指标对象（会有弃用提示，但脚本已静默）

关于 benchmark（很关键）：
- `expected_snippet` 更像“检索 Ground Truth”（用于命中率/排名类指标，如 hit@k、MRR、nDCG）
- `answer_correctness` 需要的是“QA Ground Truth”（标准答案），建议在测试集里新增 `expected_answer`
- 本脚本会优先用 `expected_answer` 做 correctness；同时基于 `expected_snippet` 输出一组简单检索指标，避免混用

依赖：
  pip install ragas datasets langchain-openai requests numpy

用法（PowerShell）：
  $env:RAGAS_EVAL_API_KEY = "<your-openai-compatible-key>"
  $env:RAGAS_EVAL_BASE_URL = "https://token.sensenova.cn/v1"   # 例：你本地 /rag/chat 用的同源服务
  $env:RAGAS_EVAL_MODEL = "deepseek-v4-flash"
  python ragas_eval.py --count 10
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import requests
from datasets import Dataset
from langchain_core.embeddings import Embeddings
from langchain_core.outputs import ChatResult
from langchain_openai import ChatOpenAI
from ragas import evaluate
warnings.filterwarnings(
    "ignore",
    message=r"Importing .* from 'ragas\.metrics' is deprecated.*",
    category=DeprecationWarning,
)
from ragas.metrics import answer_correctness, faithfulness
from ragas.run_config import RunConfig

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


class ForceN1ChatOpenAI(ChatOpenAI):
    """强制所有调用 n=1，避免部分厂商的 thinking 模式限制导致 400。"""

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:  # type: ignore[override]
        kwargs["n"] = 1
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:  # type: ignore[override]
        kwargs["n"] = 1
        return await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)


class DummyDeterministicEmbeddings(Embeddings):
    """纯本地 embeddings：不走网络，用于满足 ragas.evaluate 的 embeddings 初始化要求。

    注意：它不是语义 embedding，只是为了让 LLM-only 指标能稳定运行。
    """

    def __init__(self, dim: int = 128):
        self.dim = dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        import hashlib

        b = hashlib.sha256((text or "").encode("utf-8", errors="ignore")).digest()
        vec = []
        while len(vec) < self.dim:
            for x in b:
                vec.append((x - 128) / 128.0)
                if len(vec) >= self.dim:
                    break
        return vec


BASE_DIR = Path(__file__).parent


def load_cases(path: Path, count: int) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"测试集格式不对（应为 JSON array）：{path}")
    return data[:count]


def call_rag_chat(api_url: str, question: str, timeout_s: int) -> dict[str, Any]:
    try:
        r = requests.get(api_url, params={"question": question}, timeout=timeout_s)
        r.raise_for_status()
        payload = r.json()
        return {
            "question": payload.get("question", question),
            "answer": payload.get("answer", ""),
            "contexts": payload.get("contexts", []) or [],
        }
    except Exception as e:
        return {"question": question, "answer": "", "contexts": [], "error": str(e)}


def try_load_eval_from_spring() -> dict[str, str]:
    """仅本地兜底：从 RAG standalone 的 Spring 配置读取评测 LLM 配置。

    不会打印/输出 key，只用于本机跑评测。
    """
    if yaml is None:
        return {}
    p = BASE_DIR / "RAG" / "src" / "main" / "resources" / "application-dev.yml"
    if not p.exists():
        return {}
    try:
        cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        custom = (cfg.get("custom") or {}).get("llm") or {}
        api_key = custom.get("api-key")
        base_url = custom.get("url")
        model = custom.get("model")
        if api_key and base_url and model:
            return {"eval_key": str(api_key), "eval_base_url": str(base_url), "eval_model": str(model)}
    except Exception:
        return {}
    return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument(
        "--test-file",
        default=str(BASE_DIR / "RAG" / "src" / "test" / "resources" / "rag_golden_50.json"),
    )
    parser.add_argument("--api-url", default="http://localhost:8123/rag/chat")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--out", default=None, help="可选：输出完整明细 JSON 到文件")

    parser.add_argument(
        "--eval-workers",
        type=int,
        default=4,
        help="RAGAS 评测阶段并发（越大越快，但更容易触发限流/超时）",
    )
    parser.add_argument(
        "--eval-timeout",
        type=int,
        default=180,
        help="RAGAS 单个评测任务超时（秒），对应 RunConfig.timeout",
    )

    parser.add_argument("--eval-key", default=os.environ.get("RAGAS_EVAL_API_KEY"))
    parser.add_argument("--eval-base-url", default=os.environ.get("RAGAS_EVAL_BASE_URL"))
    parser.add_argument("--eval-model", default=os.environ.get("RAGAS_EVAL_MODEL"))
    args = parser.parse_args()

    test_file = Path(args.test_file)
    if not test_file.exists():
        raise SystemExit(f"test-file 不存在：{test_file}")

    if not args.eval_key or not args.eval_base_url or not args.eval_model:
        spring = try_load_eval_from_spring()
        args.eval_key = args.eval_key or spring.get("eval_key")
        args.eval_base_url = args.eval_base_url or spring.get("eval_base_url")
        args.eval_model = args.eval_model or spring.get("eval_model")

    if not args.eval_key or not args.eval_base_url or not args.eval_model:
        raise SystemExit(
            "缺少评测 LLM 配置。请设置环境变量：RAGAS_EVAL_API_KEY / RAGAS_EVAL_BASE_URL / RAGAS_EVAL_MODEL（或用命令行参数传入）。"
        )

    cases = load_cases(test_file, args.count)
    total = len(cases)
    if total == 0:
        raise SystemExit("测试集为空")

    print(f"cases={total} workers={args.workers}")
    print(f"rag_api={args.api_url}")
    print(f"eval_model={args.eval_model} eval_base_url={args.eval_base_url}")

    t0 = time.time()
    results: list[dict[str, Any]] = [None] * total  # type: ignore[assignment]

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut = {ex.submit(call_rag_chat, args.api_url, c["question"], args.timeout): i for i, c in enumerate(cases)}
        done = 0
        for f in as_completed(fut):
            idx = fut[f]
            results[idx] = f.result()
            done += 1
            sys.stdout.write(f"\rcollect: {done}/{total}")
            sys.stdout.flush()
    print("\ncollect done")

    expected_snippet = [c.get("expected_snippet", "") for c in cases]
    expected_answer = [c.get("expected_answer", "") for c in cases]

    # generation ground truth：优先 expected_answer；缺失则回退 expected_snippet（correctness 会偏低/不稳定）
    gt = [a if (a or "").strip() else s for a, s in zip(expected_answer, expected_snippet)]
    if any((not (a or "").strip()) and (s or "").strip() for a, s in zip(expected_answer, expected_snippet)):
        print("WARN: 测试集缺少 expected_answer，将回退使用 expected_snippet 作为 correctness 的 ground truth（分数可能偏低）。")

    dataset = Dataset.from_dict(
        {
            "question": [r["question"] for r in results],
            "answer": [r.get("answer", "") for r in results],
            "contexts": [r.get("contexts", []) for r in results],
            # 兼容不同 ragas 版本/指标对 ground truth 的字段名要求
            "reference": gt,
            "ground_truth": gt,
            "ground_truths": [[x] if (x or "").strip() else [] for x in gt],
            # 输出/诊断用（不会影响 ragas 指标计算）
            "expected_snippet": expected_snippet,
            "expected_answer": expected_answer,
        }
    )

    llm = ForceN1ChatOpenAI(
        model=args.eval_model,
        api_key=args.eval_key,
        base_url=args.eval_base_url,
        temperature=0,
        timeout=min(120, int(args.eval_timeout)),
        max_retries=1,
    )

    # 避免 ragas 在 embeddings=None 时尝试自动创建 OpenAIEmbeddings 并要求 OPENAI_API_KEY
    dummy_embeddings = DummyDeterministicEmbeddings()

    print("ragas evaluating...")
    res = evaluate(
        dataset,
        metrics=[faithfulness, answer_correctness],
        llm=llm,
        embeddings=dummy_embeddings,
        run_config=RunConfig(timeout=int(args.eval_timeout), max_workers=int(args.eval_workers)),
        raise_exceptions=False,
    )
    df = res.to_pandas()

    # 把测试集字段一并带到输出里，方便排查（顺序与输入一致）
    df["expected_snippet"] = expected_snippet
    df["expected_answer"] = expected_answer
    df["generation_ground_truth"] = gt

    # 检索评测（基于 expected_snippet 的近似）：hit / rank / MRR / nDCG
    # 说明：这里用“snippet 是否出现在 retrieved_contexts 文本中”当作 relevant judgement。
    import math

    retrieval_hit: list[int] = []
    retrieval_rank: list[float] = []
    retrieval_mrr: list[float] = []
    retrieval_ndcg: list[float] = []
    snippet_in_answer: list[int] = []

    for r, snippet in zip(results, expected_snippet):
        snippet = (snippet or "").strip()
        contexts = r.get("contexts", []) or []
        ans = r.get("answer", "") or ""

        if not snippet:
            retrieval_hit.append(0)
            retrieval_rank.append(float("nan"))
            retrieval_mrr.append(0.0)
            retrieval_ndcg.append(0.0)
            snippet_in_answer.append(0)
            continue

        found_rank = None
        for i, c in enumerate(contexts, start=1):
            if snippet in (c or ""):
                found_rank = i
                break

        if found_rank is None:
            retrieval_hit.append(0)
            retrieval_rank.append(float("nan"))
            retrieval_mrr.append(0.0)
            retrieval_ndcg.append(0.0)
        else:
            retrieval_hit.append(1)
            retrieval_rank.append(float(found_rank))
            retrieval_mrr.append(1.0 / float(found_rank))
            retrieval_ndcg.append(1.0 / math.log2(float(found_rank) + 1.0))

        snippet_in_answer.append(1 if snippet in ans else 0)

    df["retrieval_hit"] = retrieval_hit
    df["retrieval_rank"] = retrieval_rank
    df["retrieval_mrr"] = retrieval_mrr
    df["retrieval_ndcg"] = retrieval_ndcg
    df["snippet_in_answer"] = snippet_in_answer

    numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
    summary = {col: float(df[col].mean()) for col in numeric_cols}
    summary["total"] = total
    summary["elapsed_seconds"] = int(time.time() - t0)

    print("\n=== RAGAS mean ===")
    for k, v in summary.items():
        if k in ("total", "elapsed_seconds"):
            continue
        print(f"{k}: {v:.4f}")
    print(f"total: {summary['total']}")
    print(f"elapsed_seconds: {summary['elapsed_seconds']}")

    print(
        "retrieval_hit: "
        + str(int(sum(retrieval_hit)))
        + "/"
        + str(total)
        + "; snippet_in_answer: "
        + str(int(sum(snippet_in_answer)))
        + "/"
        + str(total)
    )

    if args.out:
        out_path = Path(args.out)
        payload = {
            "summary": summary,
            "rows": df.to_dict(orient="records"),
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"written: {out_path}")


if __name__ == "__main__":
    main()