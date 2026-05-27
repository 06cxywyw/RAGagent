"""
从爬取的 xiaolincoding 文档中提取 QA 对，生成 rag_recall_100.json
确保每个 expected_snippet 都真实存在于文档中
"""
import json, re, random
from pathlib import Path

DOC_DIR = Path("src/main/resources/document")
OUTPUT = Path("src/test/resources/rag_recall_100.json")
random.seed(42)

def parse_sections(filepath):
    """解析 markdown 文件，按 --- 分割，返回 list of (heading, content)"""
    text = filepath.read_text(encoding="utf-8")
    blocks = re.split(r'\n---\n', text)
    sections = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        # 提取 H2 标题（第一个 ## 开头的行）
        heading = ""
        for line in lines:
            if line.startswith("## "):
                # 清理 anchor 链接：## [#](url)标题 → 标题
                clean = re.sub(r'^##\s*\[#\]\([^)]*\)\s*', '', line)
                clean = re.sub(r'^##\s+', '', clean)
                heading = clean.strip()
                break
        # 提取有意义的内容（跳过图片、空行、标题）
        content_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("!["):
                continue
            if stripped.startswith(">"):
                stripped = stripped[1:].strip()
            content_lines.append(stripped)
        content = "\n".join(content_lines)
        if content and len(content) > 50:
            stem_clean = re.sub(r'^(八股文|软件工程)\s*[-—]\s*', '', filepath.stem)
            sections.append((heading or stem_clean, content))
    return sections

def extract_snippet(content, min_len=20, max_len=80):
    """从内容中提取一段适合作为 expected_snippet 的文本"""
    # 按句号、问号、感叹号、换行分割
    sentences = re.split(r'[。！？\n]', content)
    # 找第一个长度合适的句子
    for s in sentences:
        s = s.strip()
        if len(s) >= min_len:
            if len(s) > max_len:
                return s[:max_len]
            return s
    # fallback: 取前 max_len 字
    return content[:max_len].strip()

def question_from_heading(heading, category):
    """根据 H2 标题生成一个面试问题"""
    # 清理标题中的特殊标记
    heading = heading.replace("（上）", "").replace("（下）", "").replace("（必问）", "").strip()

    # 常见标题 -> 问题的映射规则
    question_templates = [
        lambda h: f"请详细解释{h}",
        lambda h: f"什么是{h}？",
        lambda h: f"{h}的原理是什么？",
        lambda h: f"面试中常问的{h}有哪些？",
        lambda h: f"如何理解{h}？",
        lambda h: f"谈谈你对{h}的理解",
        lambda h: f"{h}是怎么工作的？",
        lambda h: f"请简述{h}",
    ]

    # 更自然的问题
    if "如何" in heading or "怎么" in heading:
        return heading.rstrip("？") + "？"
    if "为什么" in heading:
        return heading.rstrip("？") + "？"
    if "是什么" in heading:
        return heading
    if "区别" in heading:
        return heading.rstrip("？") + "？"

    # 特定标题的定制问题
    specific = {
        "缓存雪崩": "什么是缓存雪崩？如何解决？",
        "缓存击穿": "什么是缓存击穿？和缓存雪崩有什么区别？",
        "缓存穿透": "什么是缓存穿透？如何预防？",
        "TCP 三次握手": "请描述 TCP 三次握手的过程",
        "TCP 四次挥手": "请描述 TCP 四次挥手的过程",
        "TCP 重传": "TCP 的重传机制有哪些？",
        "滑动窗口": "TCP 滑动窗口机制是怎么工作的？",
        "流量控制": "TCP 的流量控制是如何实现的？",
        "拥塞控制": "TCP 拥塞控制的算法有哪些？",
        "HTTP/2": "HTTP/2 相比 HTTP/1.1 有哪些改进？",
        "HTTP/3": "HTTP/3 是基于什么协议的？",
        "HTTPS": "HTTPS 的工作原理是什么？",
        "虚拟内存": "什么是虚拟内存？为什么需要虚拟内存？",
        "零拷贝": "什么是零拷贝技术？",
        "I/O 多路复用": "什么是 I/O 多路复用？select/poll/epoll 有什么区别？",
        "进程间通信": "进程间通信的方式有哪些？",
        "死锁": "死锁产生的四个必要条件是什么？",
        "B+ 树": "为什么 MySQL 用 B+ 树作为索引结构？",
        "事务隔离级别": "MySQL 的事务隔离级别有哪些？分别解决了什么问题？",
        "MVCC": "MVCC 是怎么实现的？",
        "索引失效": "哪些情况下会导致 MySQL 索引失效？",
        "Redis 数据结构": "Redis 有哪些常用的数据结构？",
        "缓存一致性": "数据库和缓存如何保证数据一致性？",
        "分布式锁": "Redis 分布式锁是怎么实现的？",
        "哨兵机制": "Redis 哨兵机制的工作原理是什么？",
    }
    for key, q in specific.items():
        if key in heading:
            return q

    # fallback: 随机选一个模板
    return random.choice(question_templates)(heading)

def main():
    all_sections = []

    # 解析所有文档
    for fn in sorted(DOC_DIR.glob("*.md")):
        # 从文件名提取分类
        name = fn.stem.replace("软件工程 - ", "")
        category = name.split("-")[0] if "-" in name else name

        sections = parse_sections(fn)
        for heading, content in sections:
            if not heading:
                heading = name
            all_sections.append((category, heading, content))

    print(f"找到 {len(all_sections)} 个文档小节")

    # 按分类分组，每类最多取 N 条
    from collections import defaultdict
    by_category = defaultdict(list)
    for cat, heading, content in all_sections:
        by_category[cat].append((heading, content))

    # 选择测试用例：尽量均匀覆盖各类
    test_cases = []
    categories = sorted(by_category.keys())

    # 优先每类取 2-3 条，凑够 100 条
    per_category = max(2, 100 // len(categories))
    extra_needed = 100

    for cat in categories:
        items = by_category[cat]
        random.shuffle(items)
        take = min(per_category, len(items), extra_needed)
        for heading, content in items[:take]:
            snippet = extract_snippet(content)
            question = question_from_heading(heading, cat)
            test_cases.append({
                "category": cat,
                "question": question,
                "expected_snippet": snippet
            })
        extra_needed = 100 - len(test_cases)
        if extra_needed <= 0:
            break

    # 如果还不够 100 条，继续加
    if len(test_cases) < 100:
        remaining = 100 - len(test_cases)
        extras = []
        for cat in categories:
            items = by_category[cat][per_category:]
            for heading, content in items:
                snippet = extract_snippet(content)
                question = question_from_heading(heading, cat)
                extras.append({
                    "category": cat,
                    "question": question,
                    "expected_snippet": snippet
                })
        random.shuffle(extras)
        test_cases.extend(extras[:remaining])

    # 截断到 100 条
    test_cases = test_cases[:100]
    print(f"生成 {len(test_cases)} 条测试用例")

    # 输出统计
    from collections import Counter
    cat_counts = Counter(tc["category"] for tc in test_cases)
    print("\n各类分布:")
    for cat, count in sorted(cat_counts.items()):
        print(f"  {cat}: {count} 条")

    # 写入 JSON
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)
    print(f"\n写入 {OUTPUT}")

    # 验证 expected_snippet 是否在文档中真实存在
    print("\n验证 expected_snippet...")
    doc_text = ""
    for fn in DOC_DIR.glob("*.md"):
        doc_text += fn.read_text(encoding="utf-8")

    missing = 0
    for tc in test_cases:
        if tc["expected_snippet"] not in doc_text:
            missing += 1
            print(f"  [缺失] {tc['category']}: {tc['expected_snippet'][:30]}...")
    if missing == 0:
        print("  [OK] 所有 expected_snippet 均存在于文档中！")
    else:
        print(f"  [警告] {missing} 条 expected_snippet 未找到")

if __name__ == "__main__":
    main()