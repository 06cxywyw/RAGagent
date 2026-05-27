"""
清洗爬取的文档：去锚点链接、图片噪音、推广尾巴
"""
import re
from pathlib import Path

DOC_DIR = Path("src/main/resources/document")

# 需要去除的推广尾部特征行（从后往前扫描，匹配就删）
TAIL_MARKERS = [
    "最新的图解文章都在公众号首发",
    "如果你想加入百人技术交流群",
    "扫码下方二维码回复",
    "关注公众号",
    "加我微信",
    "求点赞、求收藏",
    "欢迎在评论区",
    "下面的是我的公众号",
    "如果觉得文章有用",
    "小林是专门为大家",
    "小林准备了一份",
    "你如果有什么困惑",
    "可以关注我的公众号",
    "本文已收录",
    "-----",
    "---",
    "推荐阅读",
    "历史好文",
    "*微信",
    "*公众号",
    "欢迎关注我的微信公众号",
    "最新的图解文章都在公众号",
    "可以加我",
    "欢迎添加",
    "往期回顾",
    "推荐好文",
    "红包封面",
    "抽奖",
    "送书",
    "福利活动",
    "面试手册",
    "面试资料",
    "学习资料免费",
    "免费领取",
]

def clean_content(text):
    """清洗单文件内容"""
    lines = text.split("\n")
    cleaned = []

    # 阶段1: 逐行清洗
    for line in lines:
        original = line

        # 去掉 > 原文地址 / > 来源 / > 作者 等标注行
        if re.match(r'^\s*>\s*(原文地址|来源|作者|本文)', line):
            continue

        # 去掉 来源/作者：公众号@xxx 行
        if re.match(r'^\s*(来源|作者)[：:]\s*公众号', line):
            continue

        # 去掉单独的图片行（行内容几乎全是图片标记）
        img_only = re.sub(r'!\[.*?\]\(.*?\)', '', line).strip()
        if img_only == '' and '![' in line:
            continue

        # 清洗标题中的锚点链接: ## [#](url)标题 → ## 标题
        line = re.sub(r'(^#{1,4}\s*)\[#\]\([^)]*\)\s*', r'\1', line)

        # 去掉行内多余的锚点: [#](url)
        line = re.sub(r'\[#\]\([^)]*\)', '', line)

        # 去掉普通图片标记（但保留行中其他文本）
        line = re.sub(r'!\[.*?\]\([^)]*\)', '', line).strip()
        if not line:
            continue

        # 去掉空的链接标记: [](url)
        line = re.sub(r'\[\]\([^)]*\)', '', line).strip()
        if not line:
            continue

        # 去掉 > 大家好 等开场白
        if re.match(r'^\s*>\s*(大家好|你好|你们好|hello|hi)', line, re.IGNORECASE):
            continue

        # 去掉原文链接: 原文地址：xxx (opens new window)
        line = re.sub(r'原文地址[：:].*?', '', line).strip()
        if not line:
            continue

        # 去掉 (opens new window)
        line = line.replace("(opens new window)", "")

        # 去掉结尾多余的 (opens new window) 残留
        line = line.replace("(opens new window)", "").strip()
        if not line:
            continue

        # 去掉 markdown 链接中残留的 (opens new window)
        line = re.sub(r'\(opens new window\)', '', line).strip()

        # 压缩多余空格
        line = re.sub(r' +', ' ', line)

        if line:
            cleaned.append(line)

    # 阶段2: 从后往前删推广尾巴
    # 找到第一个推广行出现的位置
    tail_start = len(cleaned)
    for i in range(len(cleaned) - 1, max(len(cleaned) - 30, 0) - 1, -1):
        line = cleaned[i].strip()
        for marker in TAIL_MARKERS:
            if marker in line:
                tail_start = i
                break
        if tail_start < len(cleaned):
            break

    if tail_start < len(cleaned):
        cleaned = cleaned[:tail_start]

    # 阶段3: H1 去重（保留第一个，后续的 H1 降级为 H2）
    final = []
    h1_found = False
    for line in cleaned:
        stripped = line.strip()
        if re.match(r'^# [^#]', stripped):  # 是 H1
            if not h1_found:
                h1_found = True
                final.append(line)
            else:
                final.append("##" + line[1:])
        else:
            final.append(line)
    cleaned = final

    # 阶段4: 清理多余空行
    final = []
    prev_empty = False
    for line in cleaned:
        is_empty = line.strip() == ''
        if is_empty and prev_empty:
            continue
        final.append(line)
        prev_empty = is_empty

    return "\n".join(final)

def dedup_hr(text):
    """清理多余的 ---：
    1. 连续的 --- 只保留第一个（含空白行间隔的情况）
    2. 文件开头就是 --- 的去掉"""
    lines = text.split("\n")
    result = []
    prev_hr = False
    for line in lines:
        stripped = line.strip()
        is_hr = stripped == "---"
        is_blank = stripped == ""
        if is_hr and prev_hr:
            continue  # 跳过连续的 ---
        result.append(line)
        if is_hr:
            prev_hr = True
        elif not is_blank:
            prev_hr = False
        # 空白行保持 prev_hr 不变，以捕获 ---\n\n--- 的模式
    text = "\n".join(result)
    # 去掉开头的 ---
    text = re.sub(r'^---\s*\n', '', text)
    return text

def apply_hr_split(text):
    """在 H2/H3/H4 标题前插入 ---，每个标题及其内容作为独立切片"""
    # H2: ## 标题（但非 ###）
    text = re.sub(r'^## (?!#)', '---\n## ', text, flags=re.MULTILINE)
    # H3: ### 标题（但非 ####）
    text = re.sub(r'^### (?![#])', '---\n### ', text, flags=re.MULTILINE)
    # H4: #### 标题（但非 #####）
    text = re.sub(r'^#### (?![#])', '---\n#### ', text, flags=re.MULTILINE)
    return text

def main():
    files = sorted(DOC_DIR.glob("*.md"))
    total_before = 0
    total_after = 0

    for fn in files:
        before = fn.read_text(encoding="utf-8")
        total_before += len(before)
        after = clean_content(before)
        after = dedup_hr(after)
        after = apply_hr_split(after)
        after = dedup_hr(after)
        total_after += len(after)
        fn.write_text(after, encoding="utf-8")

    print(f"清洗完成!")
    print(f"  文件数: {len(files)}")
    print(f"  清洗前: {total_before / 1024:.1f} KB")
    print(f"  清洗后: {total_after / 1024:.1f} KB")
    print(f"  减少:   {(total_before - total_after) / 1024:.1f} KB")

    # 抽样验证
    print("\n抽样验证:")
    for fn in list(files)[:3]:
        content = fn.read_text(encoding="utf-8")
        lines = content.split("\n")
        print(f"\n  {fn.name}:")
        for line in lines[:8]:
            if line.strip():
                print(f"    {line[:80]}")

if __name__ == "__main__":
    main()