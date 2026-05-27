"""
爬取 javaguide.cn 所有技术文章，按分类保存为 markdown 文档
用于 RAG 系统的软件工程八股文知识库
"""
import os, sys, re, time, json
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("请安装依赖: pip install requests beautifulsoup4")
    sys.exit(1)

DOC_DIR = Path("src/main/resources/document/javaguide")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
BASE = "https://javaguide.cn"

# 已知分类页面（手动整理，确保覆盖核心主题）
CATEGORY_PAGES = [
    ("Java基础", "/java/basis/"),
    ("Java集合", "/java/collection/"),
    ("Java并发", "/java/concurrent/"),
    ("JVM", "/java/jvm/"),
    ("Java新特性", "/java/new-features/"),
    ("Spring", "/java/spring/"),
    ("MySQL", "/database/mysql/"),
    ("Redis", "/database/redis/"),
    ("消息队列", "/database/message-queue/"),
    ("计算机网络", "/cs-basics/network/"),
    ("操作系统", "/cs-basics/operating-system/"),
    ("数据结构算法", "/cs-basics/data-structure/"),
    ("系统设计", "/system-design/"),
    ("分布式", "/system-design/distributed/"),
    ("设计模式", "/system-design/design-pattern/"),
    ("Linux", "/tools/linux/"),
    ("Git", "/tools/git/"),
    ("Docker", "/tools/docker/"),
    ("Maven", "/tools/maven/"),
    ("面试准备", "/interview-preparation/"),
    ("AI面试题", "/ai/interview-questions/"),
    ("AI大模型基础", "/ai/llm-basis/"),
    ("AI Agent", "/ai/agent/"),
    ("AI RAG", "/ai/rag/"),
    ("AI系统设计", "/ai/system-design/"),
    ("AI编程", "/ai-coding/"),
]

def fetch(url):
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.encoding = "utf-8"
            if resp.status_code == 200:
                return resp.text
            print(f"  HTTP {resp.status_code}: {url}")
        except Exception as e:
            print(f"  错误 (尝试 {attempt+1}): {e}")
        time.sleep(2)
    return None

def extract_article_links(category, url):
    """从分类页面提取文章链接"""
    full_url = BASE + url if url.startswith("/") else url
    html = fetch(full_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = set()
    # 查找所有指向 .html 的链接
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # 只取 javaguide.cn 主站的 .html 链接
        if href.startswith("/") and href.endswith(".html") and not href.startswith("//"):
            # 排除非文章页面
            if any(x in href for x in ["zhuanlan", "about-the-author", "javaguide", "timeline"]):
                continue
            links.add((category, href))
        elif href.startswith(BASE) and href.endswith(".html"):
            path = href.replace(BASE, "")
            links.add((category, path))
    return list(links)

def extract_main_content(html):
    """提取 JavaGuide 文章主要内容"""
    soup = BeautifulSoup(html, "html.parser")
    # 移除无关元素
    for tag in soup.select("nav, footer, .sidebar, .toc, script, style, aside, .ads, .comments, header, .header, .breadcrumb, .page-edit, .page-nav, .navbar, .sidebar-group, .sidebar-links"):
        tag.decompose()

    # 尝试多种选择器（VuePress 主题常用）
    main = None
    for selector in [
        ".theme-default-content", ".content__default", ".page .content",
        "main", "article", ".post-content", ".article-content",
        ".markdown-section", ".content", "#main-content",
    ]:
        main = soup.select_one(selector)
        if main:
            break
    if not main:
        body = soup.find("body")
        if body:
            main = body
        else:
            return ""
    return str(main)

def html_to_markdown(html, source_url=""):
    """将 HTML 转换为 Markdown（简化版）"""
    soup = BeautifulSoup(html, "html.parser")

    # 处理代码块
    for pre in soup.find_all("pre"):
        code = pre.find("code")
        lang = ""
        if code and code.get("class"):
            for c in code.get("class"):
                if c.startswith("language-") or c.startswith("lang-"):
                    lang = c.split("-", 1)[1]
        text = code.get_text() if code else pre.get_text()
        code_text = text.strip()
        replacement = f"\n```{lang}\n{code_text}\n```\n"
        pre.replace_with(BeautifulSoup(replacement, "html.parser"))

    # 处理图片
    for img in soup.find_all("img"):
        alt = img.get("alt", "").strip()
        src = img.get("src", "")
        if src and not src.startswith("http"):
            src = BASE + src if src.startswith("/") else src
        replacement = f"\n![{alt}]({src})\n"
        img.replace_with(BeautifulSoup(replacement, "html.parser"))

    # 处理链接
    for a in soup.find_all("a"):
        text = a.get_text(strip=True)
        href = a.get("href", "")
        if href and not href.startswith("http"):
            href = BASE + href if href.startswith("/") else href
        if text and href and not href.startswith("#"):
            replacement = f"[{text}]({href})"
            a.replace_with(BeautifulSoup(replacement, "html.parser"))

    # 处理标题
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = tag.get_text(strip=True)
        level = int(tag.name[1])
        marker = "#" * level
        tag.replace_with(f"\n{marker} {text}\n")

    # 处理段落
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text:
            if not p.find(["img", "a"]):
                p.replace_with(f"{text}\n\n")

    # 处理列表
    for ul in soup.find_all(["ul", "ol"]):
        items = []
        for li in ul.find_all("li"):
            text = li.get_text(strip=True)
            if text:
                items.append(f"- {text}")
        ul.replace_with("\n" + "\n".join(items) + "\n\n")

    # 处理表格
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            rows.append("| " + " | ".join(cells) + " |")
        if rows:
            if len(rows) >= 1:
                cols = rows[0].count("|") - 1
                rows.insert(1, "| " + " | ".join(["---"] * cols) + " |")
            table.replace_with("\n" + "\n".join(rows) + "\n\n")

    text = soup.get_text()
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +\n', '\n', text)
    text = text.strip()
    return text

def process_article(category, url_path):
    """爬取一篇文章并保存"""
    full_url = BASE + url_path
    print(f"\n  [{category}] {url_path}")
    html = fetch(full_url)
    if not html:
        print(f"    [跳过] 获取失败")
        return False

    main_html = extract_main_content(html)
    if not main_html or len(main_html) < 200:
        print(f"    [跳过] 内容太少")
        return False

    markdown = html_to_markdown(main_html, full_url)
    if len(markdown) < 100:
        print(f"    [跳过] Markdown 内容太少 ({len(markdown)} 字符)")
        return False

    # 从 URL 路径生成文件名
    path_clean = url_path.replace("/", "-").replace(".html", "").strip("-")
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', f"javaguide-{category}-{path_clean}")
    filename = f"{safe_name}.md"

    content = f"# JavaGuide - {category}\n\n> 来源: {full_url}\n\n{markdown}"

    filepath = DOC_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    print(f"    [保存] {filename} ({len(content)} 字符)")
    return True

def main():
    DOC_DIR.mkdir(parents=True, exist_ok=True)

    print("JavaGuide 技术文章爬取工具")
    print(f"{'='*60}")
    print(f"目标目录: {DOC_DIR}")
    print(f"分类数量: {len(CATEGORY_PAGES)}")
    print(f"{'='*60}")

    # 1. 收集所有文章链接
    print("\n收集文章链接...")
    all_articles = []  # (category, url_path)
    visited = set()

    for cat, page_url in CATEGORY_PAGES:
        links = extract_article_links(cat, page_url)
        print(f"  {cat}: {len(links)} 篇")
        for c, path in links:
            if path not in visited:
                visited.add(path)
                all_articles.append((c, path))
        time.sleep(1)

    print(f"\n共发现 {len(all_articles)} 篇独立文章")

    # 2. 爬取每篇文章
    print(f"\n{'='*60}")
    print("开始爬取...")
    success = 0
    for i, (cat, url_path) in enumerate(all_articles):
        try:
            if process_article(cat, url_path):
                success += 1
            time.sleep(1.5)
        except KeyboardInterrupt:
            print("\n[中断] 用户终止")
            break
        except Exception as e:
            print(f"    [错误] {e}")

    # 3. 统计
    print(f"\n{'='*60}")
    print(f"完成! 成功: {success}/{len(all_articles)}")
    print(f"文档目录: {DOC_DIR.resolve()}")

    total_size = sum(f.stat().st_size for f in DOC_DIR.glob("*.md"))
    print(f"总大小: {total_size / 1024:.1f} KB")
    print(f"文件数: {len(list(DOC_DIR.glob('*.md')))}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()