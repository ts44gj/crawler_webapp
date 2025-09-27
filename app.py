#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PythonAnywhere用Flaskアプリケーション
PythonAnywhere環境に最適化された設定
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
import os
import json
import csv
from datetime import datetime
import threading
import uuid
from crawler_web import WebCrawlerRender

# Flaskアプリケーションの初期化
app = Flask(__name__)

# Render用設定
app.config['SECRET_KEY'] = 'render-crawler-2024-secure-key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['DEBUG'] = False  # 本番環境ではFalse
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # セッション有効期限: 1時間

# Renderでは制限なし
MAX_PAGES_LIMIT = 1000  # Renderでは制限なし

# 結果保存フォルダ
RESULTS_FOLDER = 'results'
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

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

# アクティブなクロールの管理（セッションID別）
active_crawls = {}

@app.route('/')
def index():
    """メインページ"""
    # 既存のクロールを停止
    if 'crawl_session_id' in session:
        session_id = session['crawl_session_id']
        if session_id in active_crawls:
            active_crawls[session_id]['stop_flag'] = True
            del active_crawls[session_id]
        session.pop('crawl_session_id', None)
    
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    """クロール開始"""
    global crawl_progress, active_crawls
    
    try:
        url = request.form.get('url', '').strip()
        max_pages = int(request.form.get('max_pages', 50))
        
        if not url:
            flash('URLを入力してください', 'error')
            return redirect(url_for('index'))
        
        # Renderでは制限なし（警告のみ）
        if max_pages > MAX_PAGES_LIMIT:
            flash(f'大量のページクロールは時間がかかります。最大{MAX_PAGES_LIMIT}ページまで推奨', 'info')
            max_pages = MAX_PAGES_LIMIT
        
        # セッションIDを生成（既存のクロールを停止）
        session_id = str(uuid.uuid4())
        session['crawl_session_id'] = session_id
        
        # 既存のクロールを停止
        if session_id in active_crawls:
            active_crawls[session_id]['stop_flag'] = True
        
        # 新しいクロールの進捗を初期化
        crawl_progress = {
            'is_running': True,
            'current_page': 0,
            'total_pages': max_pages,
            'percentage': 0,
            'status': 'クロール開始中...',
            'results': [],
            'start_time': datetime.now(),
            'session_id': session_id
        }
        
        # アクティブクロールに追加
        active_crawls[session_id] = {
            'progress': crawl_progress,
            'stop_flag': False,
            'thread': None
        }
        
        # バックグラウンドでクロール実行
        thread = threading.Thread(target=crawl_background, args=(url, max_pages, session_id))
        thread.daemon = True
        thread.start()
        
        # スレッドを保存
        active_crawls[session_id]['thread'] = thread
        
        return redirect(url_for('progress'))
        
    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('index'))

def crawl_background(url, max_pages, session_id):
    """バックグラウンドでクロール実行"""
    global crawl_progress, active_crawls
    
    try:
        crawler = WebCrawlerRender()
        
        def update_progress(current, total, status):
            # セッションが有効かチェック
            if session_id not in active_crawls or active_crawls[session_id]['stop_flag']:
                return False  # クロール停止
            
            crawl_progress['current_page'] = current
            crawl_progress['total_pages'] = total
            crawl_progress['percentage'] = int((current / total) * 100) if total > 0 else 0
            crawl_progress['status'] = status
            return True
        
        results = crawler.crawl_website_with_progress(url, max_pages, update_progress)
        
        # セッションが有効な場合のみ結果を保存
        if session_id in active_crawls and not active_crawls[session_id]['stop_flag']:
            crawl_progress['results'] = results
            crawl_progress['is_running'] = False
            crawl_progress['status'] = f'完了！ {len(results)}件のページを収集しました'
        else:
            crawl_progress['is_running'] = False
            crawl_progress['status'] = 'クロールが中断されました'
        
        # アクティブクロールから削除
        if session_id in active_crawls:
            del active_crawls[session_id]
        
    except Exception as e:
        crawl_progress['is_running'] = False
        crawl_progress['status'] = f'エラー: {str(e)}'
        print(f"クロールエラー: {str(e)}")  # Renderのログに出力
        
        # アクティブクロールから削除
        if session_id in active_crawls:
            del active_crawls[session_id]

@app.route('/progress')
def progress():
    """進捗表示ページ"""
    # セッションが無効な場合はトップページにリダイレクト
    if 'crawl_session_id' not in session:
        flash('セッションが無効です。新しいクロールを開始してください。', 'warning')
        return redirect(url_for('index'))
    
    return render_template('progress.html')

@app.route('/api/progress')
def api_progress():
    """進捗API"""
    return jsonify(crawl_progress)

@app.route('/results')
def show_results():
    """結果表示ページ"""
    global crawl_progress
    
    if not crawl_progress['results']:
        flash('結果がありません', 'warning')
        return redirect(url_for('index'))
    
    # 結果をファイルに保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_filename = f'crawl_results_{timestamp}.json'
    csv_filename = f'crawl_results_{timestamp}.csv'
    
    json_filepath = os.path.join(RESULTS_FOLDER, json_filename)
    csv_filepath = os.path.join(RESULTS_FOLDER, csv_filename)
    
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
    import os
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
