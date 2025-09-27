# PythonAnywhere 用ファイル確認

## ✅ 必要なファイル一覧

### 必須ファイル

- [x] `app.py` - メイン Flask アプリケーション
- [x] `crawler_web.py` - クローラー機能（Selenium なし）
- [x] `requirements.txt` - 依存関係（軽量版）

### フォルダ

- [x] `templates/` - HTML テンプレート
  - [x] `base.html`
  - [x] `index.html`
  - [x] `progress.html`
  - [x] `results.html`
- [x] `static/` - CSS/JS ファイル
  - [x] `css/style.css`
  - [x] `js/main.js`
- [x] `results/` - 結果保存フォルダ（空）

## 🚀 PythonAnywhere でのデプロイ手順

### Step 1: ファイルアップロード

1. PythonAnywhere の Files タブにアクセス
2. `/home/username/mysite/`フォルダを作成
3. 上記のファイル・フォルダをアップロード

### Step 2: 依存関係のインストール

```bash
cd /home/username/mysite
pip3.10 install --user -r requirements.txt
```

### Step 3: Web アプリの設定

1. Web タブで Flask アプリを作成
2. WSGI 設定ファイルを編集：

```python
import sys
path = '/home/username/mysite'
if path not in sys.path:
    sys.path.append(path)

from app import app as application
```

### Step 4: アプリの起動

1. Web タブで Reload ボタンをクリック
2. `https://username.pythonanywhere.com/`でアクセス

## ⚠️ 注意事項

- 無料プランでは外部サイトへのアクセス制限あり
- 最大 50 ページまでの制限
- Selenium は使用不可（requests + BeautifulSoup のみ）

## 🔧 トラブルシューティング

### よくあるエラー

1. **ImportError**: 依存関係の再インストール
2. **Template not found**: ファイルパスの確認
3. **Static files not loading**: フォルダ構造の確認
