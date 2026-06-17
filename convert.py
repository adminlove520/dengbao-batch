#!/usr/bin/env python3
"""
等保测评命令 - 微信公众号文章批量转Markdown
用法:
  1. 把微信文章链接写入 urls.txt (格式: 分类|标题|URL)
  2. 运行 python convert.py
  3. 等待完成，Markdown文件输出到 output/ 目录
"""

import os
import sys
import json
import time
import re
import requests
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

API_URL = "https://wechat-to-markdown-nmf6n02ut-adminlove520s-projects.vercel.app/api/convert"
TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY = 5
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
OUTPUT_DIR = "output"

def load_urls(filepath):
    """读取urls.txt，每行格式: 分类|标题|URL"""
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        print("请创建 urls.txt，格式: 分类|标题|URL")
        sys.exit(1)
    
    urls = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('|')
            if len(parts) >= 3:
                category = parts[0].strip()
                title = parts[1].strip()
                url = parts[2].strip()
                urls.append((category, title, url))
            elif len(parts) == 1 and line.startswith('http'):
                # 只有URL，没有分类标题，用标题作为URL
                urls.append(('未分类', line, line))
    return urls

def convert_one(category, title, url):
    """调用API转换单个URL"""
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                API_URL,
                json={"url": url},
                headers=HEADERS,
                timeout=TIMEOUT
            )
            if resp.status_code == 200:
                data = resp.json()
                if 'markdown' in data and data['markdown']:
                    return {
                        'category': category,
                        'title': title,
                        'url': url,
                        'status': 'success',
                        'markdown': data['markdown'],
                        'author': data.get('author', ''),
                        'publish_time': data.get('publish_time', '')
                    }
                else:
                    return {
                        'category': category,
                        'title': title,
                        'url': url,
                        'status': 'api_error',
                        'error': 'no markdown in response',
                        'response': data
                    }
            elif resp.status_code == 500:
                # 服务端解析错误，重试
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return {
                    'category': category,
                    'title': title,
                    'url': url,
                    'status': 'api_error',
                    'error': f"HTTP {resp.status_code}: {resp.text[:200]}"
                }
            else:
                return {
                    'category': category,
                    'title': title,
                    'url': url,
                    'status': 'http_error',
                    'error': f"HTTP {resp.status_code}: {resp.text[:200]}"
                }
        except RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            return {
                'category': category,
                'title': title,
                'url': url,
                'status': 'network_error',
                'error': str(e)
            }
    
    return {
        'category': category,
        'title': title,
        'url': url,
        'status': 'max_retries',
        'error': 'max retries exceeded'
    }

def sanitize_filename(name):
    """sanitize文件名"""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    name = name.strip('. ')
    return name[:100] or 'untitled'

def save_markdown(result):
    """保存Markdown文件"""
    if result['status'] != 'success':
        return None
    
    category = sanitize_filename(result['category'])
    title = sanitize_filename(result['title'])
    
    # 创建分类目录
    cat_dir = os.path.join(OUTPUT_DIR, category)
    os.makedirs(cat_dir, exist_ok=True)
    
    # 文件名
    filepath = os.path.join(cat_dir, f"{title}.md")
    
    # 处理文件名冲突
    if os.path.exists(filepath):
        base = title
        counter = 1
        while os.path.exists(filepath):
            title = f"{base}_{counter}"
            filepath = os.path.join(cat_dir, f"{title}.md")
            counter += 1
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(result['markdown'])
    
    return filepath

def main():
    print("=" * 60)
    print("等保测评命令 - 微信文章批量转Markdown")
    print("=" * 60)
    
    urls_file = "urls.txt"
    urls = load_urls(urls_file)
    
    if not urls:
        print("urls.txt 为空或没有有效链接")
        sys.exit(1)
    
    print(f"📋 共 {len(urls)} 篇文章待转换\n")
    
    # 统计
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    results = []
    success_count = 0
    fail_count = 0
    
    print("🚀 开始转换...\n")
    
    for i, (category, title, url) in enumerate(tqdm(urls, desc="转换进度", unit="篇"), 1):
        result = convert_one(category, title, url)
        results.append(result)
        
        if result['status'] == 'success':
            filepath = save_markdown(result)
            if filepath:
                tqdm.write(f"  ✅ {category}/{title}.md")
                success_count += 1
        else:
            tqdm.write(f"  ❌ {title}: {result['error'][:60]}")
            fail_count += 1
        
        # 避免请求过快
        time.sleep(1)
    
    # 保存转换日志
    log_file = "conversion_log.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 打印统计
    print("\n" + "=" * 60)
    print(f"✅ 成功: {success_count}/{len(urls)}")
    print(f"❌ 失败: {fail_count}/{len(urls)}")
    print(f"📁 输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print(f"📋 日志文件: {os.path.abspath(log_file)}")
    print("=" * 60)
    
    if fail_count > 0:
        print(f"\n⚠️  失败的链接已记录在 {log_file}，可稍后重试")

if __name__ == "__main__":
    main()
