#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PythonAnywhere無料プラン用デモアプリ
外部サイトアクセス制限に対応したデモ版
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import os
import json
import csv
from datetime import datetime
import threading
import time

# Flaskアプリケーションの初期化
app = Flask(__name__)

# 設定
app.config['SECRET_KEY'] = 'pythonanywhere-demo-2024'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['DEBUG'] = False

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

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    """クロール開始（デモ版）"""
    global crawl_progress
    
    try:
        url = request.form.get('url', '').strip()
        max_pages = int(request.form.get('max_pages', 10))
        
        if not url:
            flash('URLを入力してください', 'error')
            return redirect(url_for('index'))
        
        # デモ用の制限
        if max_pages > 20:
            flash('デモ版では最大20ページまでです', 'warning')
            max_pages = 20
        
        # 進捗をリセット
        crawl_progress = {
            'is_running': True,
            'current_page': 0,
            'total_pages': max_pages,
            'percentage': 0,
            'status': 'デモデータ生成中...',
            'results': [],
            'start_time': datetime.now()
        }
        
        # バックグラウンドでデモデータ生成
        thread = threading.Thread(target=generate_demo_data, args=(url, max_pages))
        thread.daemon = True
        thread.start()
        
        return redirect(url_for('progress'))
        
    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('index'))

def generate_demo_data(url, max_pages):
    """デモデータを生成"""
    global crawl_progress
    
    try:
        # デモデータを生成
        demo_results = []
        
        for i in range(max_pages):
            # 進捗を更新
            crawl_progress['current_page'] = i + 1
            crawl_progress['total_pages'] = max_pages
            crawl_progress['percentage'] = int(((i + 1) / max_pages) * 100)
            crawl_progress['status'] = f'デモデータ生成中: {i + 1}/{max_pages}'
            
            # デモデータを作成
            demo_result = {
                'url': f"{url}/page{i+1}",
                'title': f'デモページ {i+1} - {url}',
                'h1': f'デモH1見出し {i+1}',
                'h2_1': f'デモH2-1見出し {i+1}',
                'h2_2': f'デモH2-2見出し {i+1}',
                'h2_3': f'デモH2-3見出し {i+1}',
                'description': f'これはデモデータです。PythonAnywhereの無料プランでは外部サイトへのアクセスが制限されているため、実際のクロールはできません。',
                'canonical_url': f"{url}/page{i+1}",
                'index_status': 'demo',
                'is_redirect': False,
                'redirect_chain': '',
                'final_url': f"{url}/page{i+1}",
                'status_code': 200
            }
            
            demo_results.append(demo_result)
            
            # デモ用の遅延
            time.sleep(0.5)
        
        crawl_progress['results'] = demo_results
        crawl_progress['is_running'] = False
        crawl_progress['status'] = f'デモ完了！ {len(demo_results)}件のデモデータを生成しました'
        
    except Exception as e:
        crawl_progress['is_running'] = False
        crawl_progress['status'] = f'エラー: {str(e)}'

@app.route('/progress')
def progress():
    """進捗表示ページ"""
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
    json_filename = f'demo_results_{timestamp}.json'
    csv_filename = f'demo_results_{timestamp}.csv'
    
    json_filepath = os.path.join(RESULTS_FOLDER, json_filename)
    csv_filepath = os.path.join(RESULTS_FOLDER, csv_filename)
    
    try:
        # JSONファイルに保存
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(crawl_progress['results'], f, ensure_ascii=False, indent=2)
        
        # CSVファイルに保存
        with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'Index Status', 'Title', 'H1', 'H2-1', 'H2-2', 'Description', 'Canonical URL', 'Status Code'])
            for result in crawl_progress['results']:
                writer.writerow([
                    result['url'],
                    result['index_status'],
                    result['title'],
                    result['h1'],
                    result['h2_1'],
                    result['h2_2'],
                    result['description'],
                    result['canonical_url'],
                    result['status_code']
                ])
        
    except Exception as e:
        print(f"ファイル保存エラー: {e}")
    
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
    app.run(debug=True)
