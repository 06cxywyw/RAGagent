"""从 PostgreSQL vector_store 表生成 RAGAS 生成评测数据。

从数据库的 5275 个文档块中提取高质量 QA 对：
1. 质量过滤 — 排除无效问题、纯代码片段、广告内容
2. 答案提取 — 从 content 中提取 50-300 字的完整答案
3. 分类标注 — category / difficulty / type
4. 输出 JSON — 可直接被 ragas_eval.py 消费

用法:
    python generate_ragas_test_data.py

依赖:
    psycopg2-binary
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import psycopg2

# ── 数据库配置 ──────────────────────────────────────────────
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "ai_agent"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "123456"),
}

# ── 路径 ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "src" / "test" / "resources" / "rag_golden_ragas.json"

# ── 采样参数 ──────────────────────────────────────────────
MAX_TOTAL = 150
MAX_PER_CATEGORY = 20
MIN_CONTENT_LEN = 80
MIN_ANSWER_LEN = 50
MAX_ANSWER_LEN = 800
RANDOM_SEED = 42

# ── 停用问题 ──────────────────────────────────────────────
STOP_QUESTIONS = frozenset({
    "前言", "写在最后", "后记", "参考", "参考文献", "参考资料",
    "总结", "小结", "回顾", "简介", "介绍", "引言",
    "占用空间", "访问标志", "面试题",
    "参考链接", "课外阅读", "扩展阅读",
    "备注", "说明", "补充",
})

STOP_PREFIXES = ("请解释 前言", "请解释 写在最后", "请解释 参考", "荣誉奖项（可选）")


def connect_db():
    return psycopg2.connect(**DB_CONFIG)


def fetch_chunks(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id::text, content, metadata::text
            FROM vector_store
            WHERE content IS NOT NULL AND length(trim(content)) >= %s
        """, (MIN_CONTENT_LEN,))
        rows = cur.fetchall()
    result = []
    for row_id, content, meta_str in rows:
        try:
            meta = json.loads(meta_str)
        except json.JSONDecodeError:
            continue
        if not content or not content.strip():
            continue
        result.append({"id": row_id, "content": content, "metadata": meta})
    return result


# ── 问题提取 ──────────────────────────────────────────────

def get_question(meta: dict) -> str:
    """从 metadata 中提取问题。优先 question 字段，fallback 到标题。"""
    q = (meta.get("question") or "").strip()
    if q:
        return q
    for key in ("h4", "h3", "h2"):
        val = (meta.get(key) or "").strip()
        if val:
            return val
    return ""


# ── 质量过滤 ──────────────────────────────────────────────

def is_valid_question(q: str) -> bool:
    if not q or len(q) < 4:
        return False
    if q in STOP_QUESTIONS:
        return False
    if q.startswith(STOP_PREFIXES):
        return False
    # 纯数字/版本号
    if re.match(r"^[\d\.]+$", q):
        return False

    has_cjk = bool(re.search(r"[一-鿿]", q))
    if not has_cjk:
        return False

    # 必须有问句结构或者足够长
    has_mark = q.endswith("？") or q.endswith("?")
    has_natural = any(kw in q for kw in ("如何", "怎么", "为什么", "什么是", "是什么",
                                          "区别", "哪些", "多少", "何时", "能否",
                                          "是否", "有没有", "是不是", "可否"))
    if has_mark or has_natural or len(q) >= 10:
        return True
    return False


def passes_content_quality(content: str) -> bool:
    if len(content) < MIN_CONTENT_LEN:
        return False

    lines = content.split("\n")
    code_lines = sum(
        1 for line in lines
        if line.strip().startswith(("```", "public ", "private ", "int ",
                                     "String ", "class ", "void ", "function ",
                                     "def ", ">>> ", "    ", "\t"))
    )
    ratio_code = code_lines / max(len(lines), 1)
    chinese_chars = len(re.findall(r"[一-鿿]", content))

    if ratio_code > 0.7 and chinese_chars < 30:
        return False

    # 太多 URL 的短内容（广告/导航）
    urls = len(re.findall(r"https?://", content))
    if urls > 3 and len(content) < 200:
        return False

    return True


# ── 导航/引用段检测 ────────────────────────────────────────

NAVIGATION_PATTERNS = [
    r"可以看(我写|下面|上文|下文).*文章",
    r"更多.*?参考",
    r"详细.*?请参考",
    r"推荐阅读",
    r"相关文章",
    r"[↓↑]\s*",
]

# ── 低质量答案检测 ────────────────────────────────────────

LOW_QUALITY_ANSWERS = [
    r"这里(只是|仅仅).*(简单|粗略|大概).*(介绍|说明|概述).*(后面|日后|以后|后续)",
    r"本小节.*(简单介绍|粗略介绍|概述)",
    r"后面会.*(专门|单独).*(文章|篇幅|章节).*(介绍|讲解|说明)",
    r"暂时没有.*(内容|文章|文档)",
    r"敬请期待",
    r"待续",
    r"todo",
    r"TBD",
    r"在这里不做(深入|详细|展开)的(介绍|讨论)",
]


def is_low_quality_answer(text: str) -> bool:
    """检测答案是否只是占位/预告内容，无实质知识点。"""
    return bool(re.search("|".join(LOW_QUALITY_ANSWERS), text, re.IGNORECASE))


def is_reference_section(content: str) -> bool:
    """检测是否只是导航/参考/广告段落，没有实质内容。"""
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    if len(lines) <= 2:
        return True
    cjk = len(re.findall(r"[一-鿿]", content))
    if cjk < 30:
        return True
    nav_count = sum(1 for line in lines
                    if any(kw in line for kw in ["https://", "http://", "参考", "来源", "推荐阅读"]))
    if nav_count >= len(lines) * 0.5 and cjk < 80:
        return True
    nav_hits = sum(1 for pat in NAVIGATION_PATTERNS if re.search(pat, content))
    if nav_hits >= 2 and cjk < 100:
        return True
    return False


# ── 答案提取 ──────────────────────────────────────────────

def extract_answer(content: str, question: str) -> str:
    """从 content 中提取干净的答案文本。"""
    text = content

    # 1. 去掉第一行的 markdown 标题（如果它匹配问题）
    lines = text.split("\n")
    first = lines[0].strip().lstrip("#").strip()
    if first == question or question in first or first in question:
        text = "\n".join(lines[1:]).strip()
    else:
        # 去掉所有行首的 ### / ####
        text = re.sub(r"^#{1,4}\s+", "", text, flags=re.MULTILINE).strip()

    # 2. 去掉图片
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # 3. 去掉引用「下图」「上图」「如表」等图片/图表引用
    text = re.sub(r"[如下如上如](图|表)[^。\n]*", "", text)
    text = re.sub(r"图[片表]\s*\d*[：:].*", "", text)
    # 4. 去掉导航句
    for pat in NAVIGATION_PATTERNS:
        text = re.sub(pat, "", text)
    # 5. 去掉"可以看"、"详见"等引导到其他文章的句子
    text = re.sub(r"可以看[^。\n]{3,30}(文章|文档|链接|说明)", "", text)
    text = re.sub(r"详见[^。\n]{3,40}(文章|文档|链接|说明)", "", text)
    # 6. 去掉 markdown 链接但保留文本
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # 7. 去掉代码块
    text = re.sub(r"```[\s\S]*?```", "", text)
    # 8. 去掉 greeting
    text = re.sub(r"^大家好.*?[。，！]", "", text, flags=re.MULTILINE).strip()
    text = re.sub(r"^我是[^。\n]{2,10}。[^。\n]{2,30}", "", text, flags=re.MULTILINE)
    # 9. 去掉推广行
    ad_lines = {"关注公众号", "加我微信", "扫码", "求点赞", "转发", "在看", "打赏"}
    lines = [line for line in text.split("\n")
             if not any(ad in line for ad in ad_lines)]
    text = "\n".join(lines)

    # 10. 清理空白
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    text = re.sub(r" +", " ", text)

    if not text or len(text) < MIN_ANSWER_LEN:
        return ""
    if is_reference_section(text):
        return ""

    # 11. 截取完整句子（最多 MAX_ANSWER_LEN）
    if len(text) > MAX_ANSWER_LEN:
        truncated = text[:MAX_ANSWER_LEN]
        # 找最后一个句子边界
        for sep in ("。", "！", "？", "\n"):
            idx = truncated.rfind(sep)
            if idx > MIN_ANSWER_LEN:
                return truncated[: idx + 1]
        return truncated
    return text


def extract_snippet(content: str, min_len=25, max_len=120) -> str:
    """提取用于检索验证的短片段。"""
    head = content[:1500]
    parts = re.split(r"[。！？!?\n]", head)
    cands = [p.strip() for p in parts if min_len <= len(p.strip()) <= max_len]
    if cands:
        return cands[0]
    return content[:max_len].strip()


# ── 分类 ──────────────────────────────────────────────────

def classify_category(filename: str) -> str:
    stem = filename.replace(".md", "")
    if "javaguide" in stem.lower():
        parts = stem.split("-")
        if len(parts) >= 2:
            topic = parts[1]
            return f"javaguide/{topic}"
        return "javaguide/通用"
    if "八股文" in stem:
        name = re.sub(r"^八股文\s*[-—]\s*", "", stem).strip()
        segments = name.split("-")
        topic = segments[0].strip() if segments else "通用"
        return f"xiaolincoding/{topic}"
    return "其他"


CATEGORY_ALIAS = {
    "javaguide/计算机网络": "javaguide/网络",
    "javaguide/数据结构算法": "javaguide/数据结构",
    "xiaolincoding/Java并发编程": "xiaolincoding/Java并发",
    "xiaolincoding/Java虚拟机": "xiaolincoding/JVM",
    "xiaolincoding/网络": "xiaolincoding/计算机网络",
}


def normalize_category(cat: str) -> str:
    return CATEGORY_ALIAS.get(cat, cat)


def classify_difficulty(content: str, question: str) -> str:
    text = content.lower()
    q = question.lower()

    hard_kw = ["源码", "实现原理", "底层", "AQS", "CAS", "volatile",
               "红黑树", "B+树", "B-Tree", "MVCC", "GC", "类加载",
               "epoll", "零拷贝", "分布式", "一致性", "CAP", "raft",
               "netty", "NIO", "内存模型", "垃圾回收", "序列化"]
    easy_kw = ["什么是", "是什么", "基本", "简单", "概述", "特点",
               "优点", "缺点", "区别", "vs", "对比"]

    hard_score = sum(1 for kw in hard_kw if kw in text or kw in q)
    easy_score = sum(1 for kw in easy_kw if kw in q)

    if hard_score >= 2:
        return "hard"
    if easy_score >= 2 or len(content) < 150:
        return "easy"
    return "medium"


def classify_type(content: str, question: str) -> str:
    q = question.lower()
    if any(kw in q for kw in ["区别", "vs", "对比", "比较", "差异", "不同"]):
        return "comparison"
    if any(kw in q for kw in ["原理", "如何", "怎么", "过程", "机制", "流程", "步骤"]):
        return "mechanism"
    code_score = sum(1 for ind in ["```", "public ", "private ", "void ", "int ", "class "]
                     if ind in content)
    if code_score >= 3 and len(content) > 100:
        return "code"
    return "concept"


def improve_question(question: str, content: str = "") -> str:
    """让问题更自然。使用 content 中的线索推断更好的问法。"""
    q = question.strip()

    # 已经是完整问句
    if (q.endswith("？") or q.endswith("?") or q.endswith("吗？") or q.endswith("吗?")):
        if len(q) >= 5:
            return q
    if any(kw in q for kw in ("如何", "怎么", "为什么", "哪些", "多少", "何时", "是否", "能不能")):
        return q

    # 从 content 首段提取自然问题模式
    head = content[:300] if content else ""

    # 检查 content 是否有 "什么是 X"/"X 是什么" 模式
    m = re.search(r"什么是(.{2,20})[？?]?", head)
    if m and m.group(1).strip() in q:
        return f"什么是{m.group(1).strip()}？"

    # 场景化转换: 无问号的问题
    # 先用较具体的模板匹配
    templates = [
        (r"(.*)的(原理|工作流程|工作机制|流程)",                     r"\1的\2是什么？"),
        (r"(.*)(源码|实现|设计)(分析|解析|讲解)",                   r"\1的\2如何实现的？"),
        (r"(.*)常见(应用|场景|问题)",                              r"\1有哪些常见\2？"),
        (r"(.*)(应用|使用)场景",                                   r"\1有哪些\2？"),
        (r"(.*)和(.*)的(区别|比较|差异)",                          r"\1和\2有什么区别？"),
        (r"(.*)与(.*)的区别",                                      r"\1与\2的区别是什么？"),
        (r"(.*)(详解|概述|介绍|总结|入门|基础)",                   r"请详细解释\1"),
    ]

    for pattern, replacement in templates:
        m = re.match(pattern, q)
        if m:
            return re.sub(pattern, replacement, q)

    # 数字标题清理: "4.2 什么是X" → "什么是X"
    q_clean = re.sub(r"^[\d\.\s]+", "", q).strip()
    if q_clean and q_clean != q:
        return improve_question(q_clean, head)

    # 已经是动作/问题开头的直接保留
    if q.startswith(("说", "讲", "谈", "介绍", "列举", "比较", "对比", "分析", "解释")):
        if not q.endswith("？") and not q.endswith("?"):
            return q + "？"
        return q

    # 检查是否已含疑问词
    if any(kw in q for kw in ("什么是", "是什么", "怎么", "如何", "为什么", "区别")):
        if not q.endswith("？") and not q.endswith("?"):
            return q + "？"
        return q

    # 根据长度选择模板: 短标题用"什么是"，长标题用"请解释"
    if len(q) <= 15:
        return f"什么是{q}？"
    return f"请解释{q}"


# ── 主流程 ──────────────────────────────────────────────────

def main():
    random.seed(RANDOM_SEED)

    print("连接数据库...")
    conn = connect_db()

    print("获取文档块...")
    chunks = fetch_chunks(conn)
    conn.close()
    print(f"  共 {len(chunks)} 个文档块")

    # 提取问题
    for c in chunks:
        c["question"] = get_question(c["metadata"])

    # 质量过滤
    valid = []
    skipped_stats: dict[str, int] = Counter()
    for c in chunks:
        q = c["question"]
        content = c["content"]
        if not is_valid_question(q):
            skipped_stats["无效问题"] += 1
            continue
        if not passes_content_quality(content):
            skipped_stats["内容质量不足"] += 1
            continue
        valid.append(c)
    print(f"\n质量过滤: {len(valid)} 通过 / {len(chunks)} 总")
    for reason, n in skipped_stats.most_common():
        print(f"  - 跳过 {reason}: {n}")

    # 构建条目
    entries = []
    for c in valid:
        question = c["question"]
        content = c["content"]
        meta = c["metadata"]

        question = improve_question(question, content)
        answer = extract_answer(content, question)

        if len(answer) < MIN_ANSWER_LEN:
            skipped_stats["答案过短"] += 1
            continue
        if is_low_quality_answer(answer):
            skipped_stats["低质量答案(预告/占位)"] += 1
            continue

        snippet = extract_snippet(content)
        category = normalize_category(classify_category(meta.get("filename", "")))

        # 过滤非技术分类
        if any(nt in category for nt in ["面试准备", "Git面试", "Docker面试"]):
            continue

        difficulty = classify_difficulty(answer, question)
        qtype = classify_type(content, question)

        entries.append({
            "category": category,
            "question": question,
            "expected_answer": answer,
            "expected_snippet": snippet,
            "difficulty": difficulty,
            "type": qtype,
        })

    print(f"\n答案提取后: {len(entries)} 条")

    # 去重
    seen = set()
    deduped = []
    for e in entries:
        key = e["question"].strip().rstrip("？?").lower()
        if key not in seen:
            seen.add(key)
            deduped.append(e)
    entries = deduped
    print(f"去重后: {len(entries)} 条")

    # 按分类均衡采样
    by_cat: dict[str, list] = defaultdict(list)
    for e in entries:
        by_cat[e["category"]].append(e)

    sampled = []
    for cat in sorted(by_cat.keys()):
        items = by_cat[cat]
        random.shuffle(items)
        sampled.extend(items[:MAX_PER_CATEGORY])

    # 打乱并限制总数
    random.shuffle(sampled)
    sampled = sampled[:MAX_TOTAL]
    print(f"\n均衡采样后: {len(sampled)} 条")

    # 写入
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(sampled, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n输出: {OUTPUT_FILE}")

    # 统计
    print("\n=== 分类分布 ===")
    for cat, n in sorted(Counter(e["category"] for e in sampled).items()):
        print(f"  {cat}: {n}")
    print(f"\n=== 难度分布 ===")
    for d, n in sorted(Counter(e["difficulty"] for e in sampled).items()):
        print(f"  {d}: {n}")
    print(f"\n=== 类型分布 ===")
    for t, n in sorted(Counter(e["type"] for e in sampled).items()):
        print(f"  {t}: {n}")

    # 抽样展示
    print(f"\n=== 抽样展示 (前5条) ===")
    for e in sampled[:5]:
        try:
            desc = f"\n  [{e['category']}][{e['difficulty']}][{e['type']}]"
            desc += f"\n  Q: {e['question']}"
            desc += f"\n  A: {e['expected_answer'][:100]}..."
            print(desc)
        except Exception:
            pass


if __name__ == "__main__":
    main()