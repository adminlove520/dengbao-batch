#!/usr/bin/env python3
"""
从微信公众号目录页提取所有子文章链接
用法: python extract_urls.py [目录页URL]
"""

import sys
import json
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ 请先安装 playwright:")
    print("   pip install playwright")
    print("   playwright install chromium")
    sys.exit(1)


def extract_wechat_urls(url: str, timeout: int = 60000) -> list[tuple[str, str]]:
    """
    打开微信目录页，提取所有子文章链接
    返回: [(标题, url), ...]
    """
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
        ])
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 390, 'height': 844},  # iPhone 14 Pro 尺寸
        )
        page = context.new_page()

        print(f"🌐 打开目录页: {url}")
        page.goto(url, timeout=timeout, wait_until='domcontentloaded')

        # 等待页面完全渲染
        print("⏳ 等待页面渲染...")
        page.wait_for_timeout(8000)  # 等 8 秒让 JS 加载

        # 尝试多种方式提取链接
        all_links = page.query_selector_all('a')
        print(f"   找到 {len(all_links)} 个链接")

        seen = set()
        for a in all_links:
            href = a.get_attribute('href') or ''
            text = (a.text_content() or '').strip()

            # 匹配微信文章链接格式
            if 'mp.weixin.qq.com/s' in href and href not in seen:
                # 跳过锚点和空标题
                if text and not text.startswith('#'):
                    seen.add(href)
                    results.append((text, href))

        browser.close()

    return results


def detect_category(url: str, title: str) -> str:
    """根据 URL 或标题判断分类"""
    title_lower = title.lower()

    keywords_map = {
        '网络设备': ['华为', '华三', 'h3c', '锐捷', '信锐', '思科', 'cisco', 'tp-link', '中兴', 'zte', '瑞斯康达', '网络设备'],
        '数据库': ['mysql', 'oracle', 'postgresql', 'sql server', 'redis', 'mongodb', '数据库', 'sqlserver'],
        '服务器操作系统': ['windows', 'linux', 'centos', 'ubuntu', 'debian', '操作系统', '服务器'],
        '中间件': ['tomcat', 'apache', 'nginx', 'jboss', 'weblogic', '东方通', '中间件', 'websphere', 'iis'],
    }

    for cat, keywords in keywords_map.items():
        if any(kw in title_lower for kw in keywords):
            return cat

    return '其他'


def save_to_urls(urls: list[tuple[str, str]], output: str = "urls.txt"):
    """保存到 urls.txt，格式: 分类|标题|URL"""
    lines = [
        "# 等保测评命令 - 微信文章链接清单",
        "# 自动从目录页提取",
        "# 格式: 分类|标题|URL",
        "# ==================",
        "",
    ]

    for title, url in urls:
        cat = detect_category(url, title)
        lines.append(f"{cat}|{title}|{url}")

    Path(output).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f"\n✅ 已保存 {len(urls)} 个链接到 {output}")


def main():
    # 默认目录页（等保测评命令总结合集）
    default_url = "https://mp.weixin.qq.com/s/eKegm-ZL3tGbU4WjyztMdA"

    url = sys.argv[1] if len(sys.argv) > 1 else default_url

    print(f"=" * 50)
    print(f"  微信文章链接提取器")
    print(f"=" * 50)
    print()

    urls = extract_wechat_urls(url)

    if not urls:
        print("❌ 未找到任何子文章链接，可能需要:")
        print("   1. 确认目录页能正常访问")
        print("   2. 等待时间不够，增加 wait_for_timeout 值")
        print("   3. 手动在浏览器中打开页面，确认能看到文章列表")
        sys.exit(1)

    print(f"\n📋 提取到 {len(urls)} 篇文章:")
    for i, (title, url) in enumerate(urls, 1):
        print(f"  {i:2d}. [{detect_category(url, title)}] {title}")

    save_to_urls(urls)


if __name__ == "__main__":
    main()
