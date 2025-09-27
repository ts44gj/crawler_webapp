#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PythonAnywhere用Flaskアプリケーション（デバッグ版）
エラーハンドリングとログ出力を強化
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import os
import json
import csv
from datetime import datetime
import threading
import traceback

# デバッグ用のインポート
try:
    from crawler_web import WebCrawlerPythonAnywhere
    print("✅ crawler_web インポート成功")
except ImportError as e:
    print(f"❌ crawler_web インポートエラー: {e}")
    WebCrawlerPythonAnywhere = None

# Flaskアプリケーションの初期化
app = Flask(__name__)

# PythonAnywhere用設定
app.config['SECRET_KEY'] = 'pythonanywhere-crawler-2024-secure-key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['DEBUG'] = False  # 本番環境ではFalse

# PythonAnywhereの制限に対応
MAX_PAGES_LIMIT = 10  # デバッグ用にさらに制限

# 結果保存フォルダ
RESULTS_FOLDER = 'results'
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)
    print(f"✅ {RESULTS_FOLDER} フォルダを作成しました")

# グローバル変数（進捗管理）
crawl_progress = {
    'is_running': False,
    'current_page': 0,
    'total_pages': 0,
    'percentage': 0,
    'status': '待機中',
    'results': [],
    'start_time': None
}

@app.route('/')
def index():
    """メインページ"""
    print("✅ メインページにアクセス")
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    """クロール開始"""
    global crawl_progress
    
    try:
        print("🚀 クロール開始リクエスト受信")
        
        url = request.form.get('url', '').strip()
        max_pages = int(request.form.get('max_pages', 10))
        
        print(f"📝 URL: {url}")
        print(f"📝 最大ページ数: {max_pages}")
        
        if not url:
            flash('URLを入力してください', 'error')
            return redirect(url_for('index'))
        
        # PythonAnywhereの制限チェック
        if max_pages > MAX_PAGES_LIMIT:
            flash(f'PythonAnywhereの制限により、最大{MAX_PAGES_LIMIT}ページまでです', 'warning')
            max_pages = MAX_PAGES_LIMIT
        
        # 進捗をリセット
        crawl_progress = {
            'is_running': True,
            'current_page': 0,
            'total_pages': max_pages,
            'percentage': 0,
            'status': 'クロール開始中...',
            'results': [],
            'start_time': datetime.now()
        }
        
        print("🔄 バックグラウンドスレッドを開始")
        
        # バックグラウンドでクロール実行
        thread = threading.Thread(target=crawl_background, args=(url, max_pages))
        thread.daemon = True
        thread.start()
        
        return redirect(url_for('progress'))
        
    except Exception as e:
        error_msg = f'エラーが発生しました: {str(e)}'
        print(f"❌ クロール開始エラー: {error_msg}")
        print(f"❌ トレースバック: {traceback.format_exc()}")
        flash(error_msg, 'error')
        return redirect(url_for('index'))

def crawl_background(url, max_pages):
    """バックグラウンドでクロール実行"""
    global crawl_progress
    
    try:
        print(f"🔄 バックグラウンドクロール開始: {url}")
        
        if WebCrawlerPythonAnywhere is None:
            raise Exception("WebCrawlerPythonAnywhereクラスがインポートできません")
        
        crawler = WebCrawlerPythonAnywhere()
        print("✅ クローラーインスタンス作成成功")
        
        def update_progress(current, total, status):
            crawl_progress['current_page'] = current
            crawl_progress['total_pages'] = total
            crawl_progress['percentage'] = int((current / total) * 100) if total > 0 else 0
            crawl_progress['status'] = status
            print(f"📊 進捗更新: {current}/{total} - {status}")
        
        print("🔄 クロール実行開始")
        results = crawler.crawl_website_with_progress(url, max_pages, update_progress)
        
        crawl_progress['results'] = results
        crawl_progress['is_running'] = False
        crawl_progress['status'] = f'完了！ {len(results)}件のページを収集しました'
        
        print(f"✅ クロール完了: {len(results)}件のページを収集")
        
    except Exception as e:
        error_msg = f'エラー: {str(e)}'
        print(f"❌ クロールエラー: {error_msg}")
        print(f"❌ トレースバック: {traceback.format_exc()}")
        crawl_progress['is_running'] = False
        crawl_progress['status'] = error_msg

@app.route('/progress')
def progress():
    """進捗表示ページ"""
    print("📊 進捗ページにアクセス")
    return render_template('progress.html')

@app.route('/api/progress')
def api_progress():
    """進捗API"""
    print(f"📡 進捗API呼び出し: {crawl_progress}")
    return jsonify(crawl_progress)

@app.route('/results')
def show_results():
    """結果表示ページ"""
    global crawl_progress
    
    print("📋 結果ページにアクセス")
    
    if not crawl_progress['results']:
        flash('結果がありません', 'warning')
        return redirect(url_for('index'))
    
    # 結果をファイルに保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_filename = f'crawl_results_{timestamp}.json'
    csv_filename = f'crawl_results_{timestamp}.csv'
    
    json_filepath = os.path.join(RESULTS_FOLDER, json_filename)
    csv_filepath = os.path.join(RESULTS_FOLDER, csv_filename)
    
    try:
        # JSONファイルに保存
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(crawl_progress['results'], f, ensure_ascii=False, indent=2)
        
        # CSVファイルに保存
        with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'Index Status', 'Title', 'H1', 'H2-1', 'H2-2', 'H2-3', 'Description', 'Canonical URL', 'Is Redirect', 'Redirect Chain', 'Final URL', 'Status Code'])
            for result in crawl_progress['results']:
                writer.writerow([
                    result['url'],
                    result['index_status'],
                    result['title'],
                    result['h1'],
                    result['h2_1'],
                    result['h2_2'],
                    result['h2_3'],
                    result['description'],
                    result['canonical_url'],
                    result['is_redirect'],
                    result['redirect_chain'],
                    result['final_url'],
                    result['status_code']
                ])
        
        print(f"✅ ファイル保存完了: {json_filename}, {csv_filename}")
        
    except Exception as e:
        print(f"❌ ファイル保存エラー: {e}")
    
    return render_template('results.html', 
                         results=crawl_progress['results'], 
                         json_filename=json_filename,
                         csv_filename=csv_filename,
                         total_count=len(crawl_progress['results']))

@app.route('/download/<filename>')
def download_file(filename):
    """結果ファイルのダウンロード"""
    try:
        file_path = os.path.join(RESULTS_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash('ファイルが見つかりません', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'ダウンロードエラー: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    print("🚀 Flaskアプリケーション開始")
    app.run(debug=True)
