#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Render用Webクローラー
Selenium + requests + BeautifulSoupで動作
外部サイトアクセス制限なし
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
import threading

class WebCrawlerRender:
    """Render用Webクローラー"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.visited_urls = set()
        self.results = []
    
    def extract_page_info(self, url, response):
        """ページ情報を抽出"""
        try:
            soup = BeautifulSoup(response.content, 'html5lib')
            
            # タイトル
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ''
            
            # H1タグ（imgタグが含まれる場合はaltテキストを取得）
            h1_tag = soup.find('h1')
            h1_text = ''
            if h1_tag:
                img_tag = h1_tag.find('img')
                if img_tag and img_tag.get('alt'):
                    h1_text = img_tag.get('alt').strip()
                else:
                    h1_text = h1_tag.get_text().strip()
            
            # H2タグ（最大3個まで）
            h2_tags = soup.find_all('h2')[:3]
            h2_1 = h2_tags[0].get_text().strip() if len(h2_tags) > 0 else ''
            h2_2 = h2_tags[1].get_text().strip() if len(h2_tags) > 1 else ''
            h2_3 = h2_tags[2].get_text().strip() if len(h2_tags) > 2 else ''
            
            # メタディスクリプション
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '').strip() if meta_desc else ''
            
            # カノニカルURL
            canonical_link = soup.find('link', attrs={'rel': 'canonical'})
            canonical_url = canonical_link.get('href', '') if canonical_link else ''
            
            # インデックスステータス
            robots_meta = soup.find('meta', attrs={'name': 'robots'})
            robots_content = robots_meta.get('content', '').lower() if robots_meta else ''
            index_status = 'indexable' if 'noindex' not in robots_content else 'noindex'
            
            return {
                'url': url,
                'title': title_text,
                'h1': h1_text,
                'h2_1': h2_1,
                'h2_2': h2_2,
                'h2_3': h2_3,
                'description': description,
                'canonical_url': canonical_url,
                'index_status': index_status,
                'is_redirect': False,
                'redirect_chain': '',
                'final_url': url,
                'status_code': response.status_code
            }
            
        except Exception as e:
            print(f"ページ情報抽出エラー {url}: {str(e)}")
            return {
                'url': url,
                'title': '',
                'h1': '',
                'h2_1': '',
                'h2_2': '',
                'h2_3': '',
                'description': '',
                'canonical_url': '',
                'index_status': 'error',
                'is_redirect': False,
                'redirect_chain': '',
                'final_url': url,
                'status_code': response.status_code
            }
    
    def get_redirect_info(self, response):
        """リダイレクト情報を取得"""
        redirect_chain = []
        final_url = response.url
        
        if response.history:
            for resp in response.history:
                redirect_chain.append(resp.url)
            redirect_chain.append(final_url)
        
        return {
            'is_redirect': len(response.history) > 0,
            'redirect_chain': ' -> '.join(redirect_chain),
            'final_url': final_url
        }
    
    def crawl_website_with_progress(self, start_url, max_pages=50, progress_callback=None):
        """ウェブサイトをクロール（進捗コールバック付き）"""
        try:
            # 高速化設定
            MAX_WORKERS = 3  # 並列処理数（無料プランでは控えめに）
            
            # 開始URLをキューに追加
            queue = [start_url]
            self.visited_urls = set()
            self.results = []
            self.lock = threading.Lock()
            
            # ドメインを取得
            parsed_start = urlparse(start_url)
            base_domain = f"{parsed_start.scheme}://{parsed_start.netloc}"
            
            progress_callback(0, max_pages, "高速クロール開始...")
            
            while queue and len(self.results) < max_pages:
                # 並列処理用のURLバッチを作成
                batch_size = min(MAX_WORKERS, len(queue), max_pages - len(self.results))
                batch_urls = []
                
                for _ in range(batch_size):
                    if queue:
                        batch_urls.append(queue.pop(0))
                
                if not batch_urls:
                    break
                
                # 並列処理でページを取得
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = [executor.submit(self._process_single_page, url, parsed_start) for url in batch_urls]
                    
                    for future in futures:
                        try:
                            result = future.result(timeout=15)  # タイムアウト短縮
                            if result:
                                with self.lock:
                                    self.results.append(result)
                                    
                                    # 進捗を更新
                                    current_count = len(self.results)
                                    progress_callback(current_count, max_pages, f"高速収集中: {current_count}/{max_pages}ページ完了")
                                    
                                    # 新しいリンクをキューに追加
                                    if result.get('new_links'):
                                        for link in result['new_links']:
                                            if (link not in self.visited_urls and 
                                                link not in queue and 
                                                len(queue) < 100):  # キューサイズ制限
                                                queue.append(link)
                        except Exception as e:
                            print(f"並列処理エラー: {str(e)}")
                            continue
                
                # 短い待機時間
                time.sleep(0.2)
            
            progress_callback(len(self.results), max_pages, f"高速完了！ {len(self.results)}件のページを収集しました")
            return self.results
            
        except Exception as e:
            print(f"クロールエラー: {str(e)}")
            progress_callback(0, max_pages, f"エラー: {str(e)}")
            return []
    
    def _process_single_page(self, url, parsed_start):
        """単一ページの処理（並列処理用）"""
        try:
            with self.lock:
                if url in self.visited_urls:
                    return None
                self.visited_urls.add(url)
            
            # リクエスト送信（タイムアウト短縮）
            response = self.session.get(url, timeout=8)
            
            # リダイレクト情報を取得
            redirect_info = self.get_redirect_info(response)
            
            # ページ情報を抽出
            page_info = self.extract_page_info(url, response)
            page_info.update(redirect_info)
            
            # 新しいリンクを収集
            new_links = []
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html5lib')
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href')
                    if href:
                        absolute_url = urljoin(url, href)
                        parsed_url = urlparse(absolute_url)
                        
                        if (parsed_url.netloc == parsed_start.netloc and 
                            not absolute_url.startswith('#')):
                            new_links.append(absolute_url)
            
            page_info['new_links'] = new_links
            return page_info
            
        except Exception as e:
            print(f"ページ処理エラー {url}: {str(e)}")
            return None
