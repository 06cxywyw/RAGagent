"""
爬取 xiaolincoding.com 技术文章并保存为 markdown 文档
用于 RAG 系统的软件工程八股文知识库
"""
import os, sys, time, re
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("请安装依赖: pip install requests beautifulsoup4")
    sys.exit(1)

# 配置
DOC_DIR = Path("src/main/resources/document")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
BASE_URL = "https://xiaolincoding.com"

# === 要爬取的文章列表（已验证的 URL） ===
ARTICLES = [
    # === Redis (13篇，全部已验证) ===
    ("Redis-缓存问题", "/redis/cluster/cache_problem.html"),
    ("Redis-数据类型和应用场景", "/redis/data_struct/command.html"),
    ("Redis-数据结构实现", "/redis/data_struct/data_struct.html"),
    ("Redis-AOF持久化", "/redis/storage/aof.html"),
    ("Redis-RDB快照", "/redis/storage/rdb.html"),
    ("Redis-大Key对持久化的影响", "/redis/storage/bigkey_aof_rdb.html"),
    ("Redis-过期删除和内存淘汰", "/redis/module/strategy.html"),
    ("Redis-分布式锁", "/redis/module/setnx.html"),
    ("Redis-主从复制", "/redis/cluster/master_slave_replication.html"),
    ("Redis-哨兵机制", "/redis/cluster/sentinel.html"),
    ("Redis-Cluster集群", "/redis/cluster/cluster.html"),
    ("Redis-Redlock高可用", "/redis/cluster/redlock.html"),
    ("Redis-数据库和缓存一致性", "/redis/architecture/mysql_redis_consistency.html"),

    # === MySQL (20篇，已验证) ===
    ("MySQL-Select语句执行流程", "/mysql/base/how_select.html"),
    ("MySQL-一行记录的存储", "/mysql/base/row_format.html"),
    ("MySQL-索引面试题", "/mysql/index/index_interview.html"),
    ("MySQL-数据页与B+树", "/mysql/index/page.html"),
    ("MySQL-B+树索引选择", "/mysql/index/why_index_chose_bpuls_tree.html"),
    ("MySQL-单表2000W行", "/mysql/index/2000w.html"),
    ("MySQL-索引失效", "/mysql/index/index_lose.html"),
    ("MySQL-Count函数", "/mysql/index/count.html"),
    ("MySQL-分页优化", "/mysql/index/limit.html"),
    ("MySQL-事务隔离级别", "/mysql/transaction/mvcc.html"),
    ("MySQL-幻读问题", "/mysql/transaction/phantom.html"),
    ("MySQL-锁机制", "/mysql/lock/mysql_lock.html"),
    ("MySQL-加锁分析", "/mysql/lock/how_to_lock.html"),
    ("MySQL-Update无索引锁全表", "/mysql/lock/update_index.html"),
    ("MySQL-间隙锁防幻读", "/mysql/lock/lock_phantom.html"),
    ("MySQL-死锁分析", "/mysql/lock/deadlock.html"),
    ("MySQL-字节面试加锁", "/mysql/lock/show_lock.html"),
    ("MySQL-日志机制", "/mysql/log/how_update.html"),
    ("MySQL-BufferPool", "/mysql/buffer_pool/buffer_pool.html"),
    ("MySQL-架构总览", "/mysql/architecture/mysql_architecture.html"),

    # === 计算机网络 (42篇，已验证) ===
    ("网络-TCPIP网络模型", "/network/1_base/tcp_ip_model.html"),
    ("网络-键入网址的过程", "/network/1_base/what_happen_url.html"),
    ("网络-Linux收发网络包", "/network/1_base/how_os_deal_network_package.html"),
    ("网络-HTTP面试题", "/network/2_http/http_interview.html"),
    ("网络-HTTP1.1优化", "/network/2_http/http_optimize.html"),
    ("网络-HTTPS-RSA握手", "/network/2_http/https_rsa.html"),
    ("网络-HTTPS-ECDHE握手", "/network/2_http/https_ecdhe.html"),
    ("网络-HTTPS优化", "/network/2_http/https_optimize.html"),
    ("网络-HTTP2", "/network/2_http/http2.html"),
    ("网络-HTTP3", "/network/2_http/http3.html"),
    ("网络-HTTP与RPC", "/network/2_http/http_rpc.html"),
    ("网络-HTTP与WebSocket", "/network/2_http/http_websocket.html"),
    ("网络-TCP三次握手四次挥手", "/network/3_tcp/tcp_interview.html"),
    ("网络-TCP重传与流量控制", "/network/3_tcp/tcp_feature.html"),
    ("网络-TCP抓包分析", "/network/3_tcp/tcp_tcpdump.html"),
    ("网络-TCP半连接和全连接队列", "/network/3_tcp/tcp_queue.html"),
    ("网络-TCP优化", "/network/3_tcp/tcp_optimize.html"),
    ("网络-TCP字节流", "/network/3_tcp/tcp_stream.html"),
    ("网络-TCP初始化序列号", "/network/3_tcp/isn_deff.html"),
    ("网络-SYN报文丢弃", "/network/3_tcp/syn_drop.html"),
    ("网络-已连接TCP收到SYN", "/network/3_tcp/challenge_ack.html"),
    ("网络-乱序FIN包处理", "/network/3_tcp/out_of_order_fin.html"),
    ("网络-TIME_WAIT收到SYN", "/network/3_tcp/time_wait_recv_syn.html"),
    ("网络-TCP断电与进程崩溃", "/network/3_tcp/tcp_down_and_crash.html"),
    ("网络-拔网线TCP连接", "/network/3_tcp/tcp_unplug_the_network_cable.html"),
    ("网络-tcp_tw_reuse", "/network/3_tcp/tcp_tw_reuse_close.html"),
    ("网络-TLS与TCP同时握手", "/network/3_tcp/tcp_tls.html"),
    ("网络-TCP与HTTPKeepAlive", "/network/3_tcp/tcp_http_keepalive.html"),
    ("网络-TCP协议缺陷", "/network/3_tcp/tcp_problem.html"),
    ("网络-基于UDP的可靠传输", "/network/3_tcp/quic.html"),
    ("网络-TCP和UDP同端口", "/network/3_tcp/port.html"),
    ("网络-服务端无listen", "/network/3_tcp/tcp_no_listen.html"),
    ("网络-无accept建立连接", "/network/3_tcp/tcp_no_accpet.html"),
    ("网络-TCP数据不丢", "/network/3_tcp/tcp_drop.html"),
    ("网络-TCP三次挥手", "/network/3_tcp/tcp_three_fin.html"),
    ("网络-TCP序列号和确认号", "/network/3_tcp/tcp_seq_ack.html"),
    ("网络-IP基础知识", "/network/4_ip/ip_base.html"),
    ("网络-Ping工作原理", "/network/4_ip/ping.html"),
    ("网络-断网Ping127", "/network/4_ip/ping_lo.html"),

    # === 操作系统 (34篇，已验证) ===
    ("OS-CPU执行程序", "/os/1_hardware/how_cpu_run.html"),
    ("OS-磁盘比内存慢", "/os/1_hardware/storage.html"),
    ("OS-CPU代码优化", "/os/1_hardware/how_to_make_cpu_run_faster.html"),
    ("OS-CPU缓存一致性", "/os/1_hardware/cpu_mesi.html"),
    ("OS-CPU执行任务", "/os/1_hardware/how_cpu_deal_task.html"),
    ("OS-软中断", "/os/1_hardware/soft_interrupt.html"),
    ("OS-浮点精度", "/os/1_hardware/float.html"),
    ("OS-Linux内核vsWindows", "/os/2_os_structure/linux_vs_windows.html"),
    ("OS-虚拟内存", "/os/3_memory/vmem.html"),
    ("OS-malloc分配", "/os/3_memory/malloc.html"),
    ("OS-内存满了", "/os/3_memory/mem_reclaim.html"),
    ("OS-申请超大内存", "/os/3_memory/alloc_mem.html"),
    ("OS-缓存LRU", "/os/3_memory/cache_lru.html"),
    ("OS-Linux虚拟内存管理", "/os/3_memory/linux_mem.html"),
    ("OS-Linux物理内存管理", "/os/3_memory/linux_mem2.html"),
    ("OS-进程线程基础", "/os/4_process/process_base.html"),
    ("OS-进程间通信", "/os/4_process/process_commu.html"),
    ("OS-多线程同步", "/os/4_process/multithread_sync.html"),
    ("OS-死锁", "/os/4_process/deadlock.html"),
    ("OS-悲观锁乐观锁", "/os/4_process/pessim_and_optimi_lock.html"),
    ("OS-最大线程数", "/os/4_process/create_thread_max.html"),
    ("OS-线程崩溃进程崩溃", "/os/4_process/thread_crash.html"),
    ("OS-调度算法", "/os/5_schedule/schedule.html"),
    ("OS-文件系统", "/os/6_file_system/file_system.html"),
    ("OS-写文件崩溃", "/os/6_file_system/pagecache.html"),
    ("OS-键盘输入过程", "/os/7_device/device.html"),
    ("OS-零拷贝", "/os/8_network_system/zero_copy.html"),
    ("OS-IO多路复用", "/os/8_network_system/selete_poll_epoll.html"),
    ("OS-Reactor和Proactor", "/os/8_network_system/reactor.html"),
    ("OS-一致性哈希", "/os/8_network_system/hash.html"),
    ("OS-网络性能查看", "/os/9_linux_cmd/linux_network.html"),
    ("OS-日志分析PVUV", "/os/9_linux_cmd/pv_uv.html"),

    # === 面试 ===
    ("Java-面试题", "/interview/java.html"),
    ("Spring-面试题", "/interview/spring.html"),

    # === Java 专题（QA 格式，粒度细） ===
    ("Java集合面试题", "/interview/collections.html"),
    ("Java并发编程面试题", "/interview/juc.html"),
    ("Java虚拟机面试题", "/interview/jvm.html"),

    # === 其他面试题（QA 格式，粒度细） ===
    ("MySQL面试题", "/interview/mysql.html"),
    ("Redis面试题", "/interview/redis.html"),
    ("计算机网络面试题", "/interview/network.html"),
    ("操作系统面试题", "/interview/os.html"),
    ("数据结构与算法面试题", "/interview/data.html"),
    ("消息队列面试题", "/interview/mq.html"),
    ("分布式面试题", "/interview/cap.html"),
    ("系统设计面试题", "/interview/systemdesign.html"),
    ("Linux命令面试题", "/interview/linux.html"),
    ("Git面试题", "/interview/git.html"),
    ("Docker面试题", "/interview/docker.html"),
]

def fetch_page(url):
    """获取页面内容"""
    full_url = BASE_URL + url if url.startswith("/") else url
    for attempt in range(3):
        try:
            resp = requests.get(full_url, headers=HEADERS, timeout=15)
            resp.encoding = "utf-8"
            if resp.status_code == 200:
                return resp.text
            print(f"  HTTP {resp.status_code}: {full_url}")
        except Exception as e:
            print(f"  错误 (尝试 {attempt+1}): {e}")
        time.sleep(2)
    return None

def extract_main_content(html):
    """提取文章主要内容，去除导航/侧边栏/页脚"""
    soup = BeautifulSoup(html, "html.parser")

    # 移除无关元素
    for tag in soup.select("nav, footer, .sidebar, .toc, script, style, aside, .ads, .comments"):
        tag.decompose()

    # 尝试多种选择器获取主内容
    main = None
    for selector in [
        "article", "main", ".post-content", ".article-content",
        ".content", "#content", ".markdown-body", ".theme-doc-markdown",
        "[class*='content']", "[class*='article']", "[class*='post']"
    ]:
        main = soup.select_one(selector)
        if main:
            break

    if not main:
        # fallback: 取 body 中的大部分内容
        body = soup.find("body")
        if body:
            main = body
        else:
            return ""

    return str(main)

def html_to_markdown(html):
    """将 HTML 转换为 Markdown"""
    from urllib.parse import urljoin

    soup = BeautifulSoup(html, "html.parser")

    # 处理代码块
    for pre in soup.find_all("pre"):
        code = pre.find("code")
        lang = ""
        if code and code.get("class"):
            classes = code.get("class")
            for c in classes:
                if c.startswith("language-") or c.startswith("lang-"):
                    lang = c.split("-", 1)[1]
        text = code.get_text() if code else pre.get_text()
        # 缩进处理
        lines = text.strip().split("\n")
        # 计算公共缩进
        indent = float("inf")
        for line in lines:
            stripped = line.lstrip()
            if stripped:
                i = len(line) - len(stripped)
                indent = min(indent, i)
        if indent == float("inf"):
            indent = 0
        # 构建代码块
        code_text = "\n".join(line[indent:] for line in lines)
        replacement = f"\n```{lang}\n{code_text}\n```\n"
        pre.replace_with(BeautifulSoup(replacement, "html.parser"))

    # 处理图片 - 用 alt 文本代替
    for img in soup.find_all("img"):
        alt = img.get("alt", "").strip()
        src = img.get("src", "")
        if src and not src.startswith("http"):
            src = urljoin(BASE_URL, src)
        replacement = f"\n![{alt}]({src})\n"
        img.replace_with(BeautifulSoup(replacement, "html.parser"))

    # 处理链接
    for a in soup.find_all("a"):
        text = a.get_text(strip=True)
        href = a.get("href", "")
        if href and not href.startswith("http"):
            href = urljoin(BASE_URL, href)
        if text and href and not href.startswith("#"):
            replacement = f"[{text}]({href})"
            a.replace_with(BeautifulSoup(replacement, "html.parser"))

    # 处理标题
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = tag.get_text(strip=True)
        level = int(tag.name[1])
        marker = "#" * level
        tag.replace_with(f"\n{marker} {text}\n\n")

    # 处理段落
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text:
            # 检查是否只包含图片/链接（已处理过）
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

    # 处理强调
    for strong in soup.find_all(["strong", "b"]):
        text = strong.get_text(strip=True)
        if text:
            strong.replace_with(f"**{text}**")

    for em in soup.find_all(["em", "i"]):
        text = em.get_text(strip=True)
        if text:
            em.replace_with(f"*{text}*")

    # 处理表格
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            rows.append("| " + " | ".join(cells) + " |")
        if rows:
            # 添加表头分隔
            if len(rows) >= 1 and "---" not in rows[0]:
                cols = rows[0].count("|") - 1
                sep = "| " + " | ".join(["---"] * cols) + " |"
                rows.insert(1, sep)
            table.replace_with("\n" + "\n".join(rows) + "\n\n")

    # 获取文本
    text = soup.get_text()
    # 清理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +\n', '\n', text)
    text = text.strip()

    # 在 H2 标题前插入 ---，确保每个独立章节被 MarkdownDocumentReader 单独切分
    # 仅匹配 "## " 但不匹配 "### " 和 "#### "
    text = re.sub(r'^## (?!#)', '---\n\n## ', text, flags=re.MULTILINE)

    return text

def save_markdown(filename, content):
    """保存 markdown 文件"""
    filepath = DOC_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    print(f"  [保存] {filepath.name} ({len(content)} 字)")

def process_article(name, url):
    """爬取一篇文章并保存"""
    print(f"\n[{articles_done+1}/{len(ARTICLES)}] {name}")
    print(f"  获取: {url}")
    html = fetch_page(url)
    if not html:
        print(f"  [跳过] 获取失败")
        return False

    main_html = extract_main_content(html)
    if not main_html or len(main_html) < 200:
        print(f"  [跳过] 内容太少 ({len(main_html) if main_html else 0} 字符)")
        return False

    # 第一段作为简介
    soup = BeautifulSoup(main_html, "html.parser")
    first_p = soup.find("p")
    intro = first_p.get_text(strip=True)[:100] if first_p else ""

    markdown = html_to_markdown(main_html)
    if len(markdown) < 100:
        print(f"  [跳过] Markdown 内容太少 ({len(markdown)} 字符)")
        return False

    # 文件名
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', name)
    filename = f"软件工程 - {safe_name}.md"

    # 添加文件头
    content = f"# 小林coding - {name}\n\n"
    if intro:
        content += f"> {intro}\n\n"
    content += markdown

    save_markdown(filename, content)
    return True

# === 主流程 ===
if __name__ == "__main__":
    DOC_DIR.mkdir(parents=True, exist_ok=True)

    print(f"小林coding 技术文章爬取工具")
    print(f"{'='*60}")
    print(f"目标目录: {DOC_DIR}")
    print(f"文章数量: {len(ARTICLES)}")
    print(f"{'='*60}")

    articles_done = 0
    success_count = 0

    for name, url in ARTICLES:
        articles_done += 1
        try:
            if process_article(name, url):
                success_count += 1
            time.sleep(1)  # 礼貌延迟
        except KeyboardInterrupt:
            print("\n[中断] 用户终止")
            break
        except Exception as e:
            print(f"  [错误] {e}")

    print(f"\n{'='*60}")
    print(f"完成! 成功: {success_count}/{articles_done}")
    print(f"文档目录: {DOC_DIR.resolve()}")

    # 统计
    total_size = sum(f.stat().st_size for f in DOC_DIR.glob("*.md"))
    print(f"总大小: {total_size / 1024:.1f} KB")
    print(f"文件数: {len(list(DOC_DIR.glob('*.md')))}")
    print(f"{'='*60}")