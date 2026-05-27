"""\
从本地语料(javaguide + xiaolincoding)中抽取 50 条“黄金”检索评测集。

输出格式：
[
  {
    "category": "javaguide/Java并发",
    "question": "...",
    "expected_snippet": "..."
  }
]

设计目标：
- expected_snippet 必须真实存在于语料中
- 尽量选择在全量语料中“唯一出现”的 snippet，减少误判
- 覆盖 javaguide 与 xiaolincoding 两套语料
"""

from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DOC_DIR = BASE_DIR / "src" / "main" / "resources" / "document"
OUTPUT = BASE_DIR / "src" / "test" / "resources" / "rag_golden_50.json"

RANDOM_SEED = 42
TOTAL = 50


@dataclass(frozen=True)
class Section:
    corpus: str  # javaguide / xiaolincoding
    category: str
    heading: str
    content: str


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n")


def parse_sections(filepath: Path) -> list[tuple[str, str]]:
    """按 --- 分割，返回 (heading, content) 列表。"""
    text = normalize_text(filepath.read_text(encoding="utf-8"))
    blocks = re.split(r"\n---\n", text)
    sections: list[tuple[str, str]] = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split("\n")

        # 提取标题：优先 H4(更像问答) -> H3 -> H2
        heading = ""
        for prefix in ("#### ", "### ", "## "):
            for line in lines:
                if line.startswith(prefix):
                    clean = re.sub(r"^#{2,4}\s*\[#\]\([^)]*\)\s*", "", line)
                    clean = re.sub(r"^#{2,4}\s+", "", clean)
                    heading = clean.strip()
                    break
            if heading:
                break

        # 提取内容（跳过图片、空行、标题）
        content_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("!["):
                continue
            if stripped.startswith(">"):
                stripped = stripped[1:].strip()
            content_lines.append(stripped)

        content = "\n".join(content_lines).strip()
        if content and len(content) > 80:
            sections.append((heading, content))

    return sections


def iter_sections() -> list[Section]:
    all_sections: list[Section] = []

    for md in sorted(DOC_DIR.glob("**/*.md")):
        rel = md.relative_to(DOC_DIR)
        corpus = rel.parts[0] if rel.parts else "document"

        stem = md.stem

        # category：尽量从文件名中抽取主题（避免全是“javaguide/八股文”）
        if corpus == "javaguide":
            parts = stem.split("-")
            topic = parts[1] if len(parts) >= 2 and parts[0].lower() == "javaguide" else parts[0]
            category = f"{corpus}/{topic}".strip("/")
        elif corpus == "xiaolincoding":
            name = re.sub(r"^\s*八股文\s*[-—]\s*", "", stem).strip()
            topic = name.split("-")[0].strip() if "-" in name else name
            topic = re.sub(r"面试题$", "", topic).strip() or "综合"
            category = f"{corpus}/{topic}".strip("/")
        else:
            category = f"{corpus}".strip("/")

        for heading, content in parse_sections(md):
            effective_heading = heading or stem
            all_sections.append(Section(corpus=corpus, category=category, heading=effective_heading, content=content))

    return all_sections


def sentence_candidates(content: str) -> list[str]:
    # 入库链路会截断超长内容（当前 MAX_CONTENT_CHARS=2000），
    # 为了避免 expected_snippet 选到“被截掉的后半段”，只从前 1500 字取样。
    head = content[:1500]

    # 按常见中文/英文句末符切分，过滤过短句
    parts = re.split(r"[。！？!?\n]", head)
    cands: list[str] = []
    for p in parts:
        s = p.strip()
        if 25 <= len(s) <= 120:
            cands.append(s)
    # fallback：取前 80 字
    if not cands:
        s = content.strip()
        if len(s) > 120:
            s = s[:120]
        cands.append(s)
    return cands


def question_from_heading(heading: str) -> str:
    h = heading.replace("（上）", "").replace("（下）", "").replace("（必问）", "").strip()

    # 尽量保持自然、直接命中标题词
    if any(x in h for x in ("如何", "怎么", "为什么", "是什么", "区别")):
        return h.rstrip("？") + "？"

    templates = [
        lambda x: f"请解释 {x}",
        lambda x: f"{x} 的原理是什么？",
        lambda x: f"面试中如何回答 {x}？",
        lambda x: f"请简述 {x}",
    ]
    return random.choice(templates)(h)


def build_corpus_text(files: list[Path]) -> str:
    buf: list[str] = []
    for fn in files:
        try:
            buf.append(fn.read_text(encoding="utf-8"))
        except Exception:
            continue
    return "\n".join(buf)


def main() -> None:
    random.seed(RANDOM_SEED)

    all_sections = iter_sections()
    if not all_sections:
        raise SystemExit(f"未找到语料: {DOC_DIR}")

    all_md_files = list(DOC_DIR.glob("**/*.md"))
    corpus_text = build_corpus_text(all_md_files)

    # 分 corpus 平衡抽样
    by_corpus: dict[str, list[Section]] = defaultdict(list)
    for s in all_sections:
        by_corpus[s.corpus].append(s)

    corpora = sorted(by_corpus.keys())
    if not corpora:
        raise SystemExit("语料为空")

    # 目标：至少每个 corpus 拿到一半（若 corpus 数>2，则均分）
    per = TOTAL // len(corpora)
    target_counts = {c: per for c in corpora}
    # 把余数补到前几个
    for i in range(TOTAL - per * len(corpora)):
        target_counts[corpora[i]] += 1

    picked: list[dict] = []
    used_questions: set[str] = set()

    for corpus in corpora:
        pool = by_corpus[corpus][:]
        random.shuffle(pool)

        need = target_counts[corpus]
        for sec in pool:
            if need <= 0:
                break

            q = question_from_heading(sec.heading)
            if q in used_questions:
                continue

            # 选尽量“唯一”的 snippet
            cands = sentence_candidates(sec.content)
            snippet = None
            for cand in cands:
                if corpus_text.count(cand) == 1:
                    snippet = cand
                    break
            if snippet is None:
                snippet = cands[0]

            if snippet not in corpus_text:
                # 极端情况：fallback 也不在（一般不会发生）
                continue

            picked.append({
                "category": sec.category,
                "question": q,
                "expected_snippet": snippet,
            })
            used_questions.add(q)
            need -= 1

    # 兜底：不足则全量补齐
    if len(picked) < TOTAL:
        remain = TOTAL - len(picked)
        pool = all_sections[:]
        random.shuffle(pool)
        for sec in pool:
            if remain <= 0:
                break
            q = question_from_heading(sec.heading)
            if q in used_questions:
                continue
            cands = sentence_candidates(sec.content)
            snippet = cands[0]
            if snippet not in corpus_text:
                continue
            picked.append({
                "category": sec.category,
                "question": q,
                "expected_snippet": snippet,
            })
            used_questions.add(q)
            remain -= 1

    picked = picked[:TOTAL]

    # 写文件
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(picked, ensure_ascii=False, indent=2), encoding="utf-8")

    # 校验
    missing = [tc for tc in picked if tc["expected_snippet"] not in corpus_text]
    if missing:
        raise SystemExit(f"生成失败：{len(missing)} 条 snippet 未在语料中命中")

    # 输出简单统计
    by_src = defaultdict(int)
    for tc in picked:
        by_src[tc["category"].split("/")[0]] += 1
    print(f"写入 {OUTPUT}，共 {len(picked)} 条")
    print("语料分布:")
    for k, v in sorted(by_src.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
