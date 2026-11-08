# TODO Manager

PythonとFlaskで構築したマルチユーザー対応のTODO管理Webアプリケーション。

## 主な機能

| 機能 | 概要 |
|------|------|
| ユーザー認証 | 登録・ログイン・ログアウト、ユーザーごとにデータ分離 |
| TODO管理 | 追加・編集・完了切替・削除、優先度・締め切り日・カテゴリ設定 |
| 完成度 | 0〜100%のスライダー入力、色の濃さが段階的に変化するプログレスバー |
| 繰り返しタスク | 毎日・毎週・毎月パターン、終了日/回数指定、今月分一括生成 |
| プロジェクト管理 | 無制限階層（プロジェクト→サブタスク→...）、percent/numericモード |
| 進捗予測 | 現在ペースから完了予測日を計算、遅延見込み（橙）/超過（赤）バー表示 |
| 検索・フィルター | キーワード、完了状態、優先度、カテゴリ、日付ソート |

## 技術スタック

- **Python 3.10+**
- **Flask 3.x** - Webフレームワーク
- **SQLAlchemy 2.x** - ORM
- **SQLite** - データベース（ファイルベース）
- **Flask-Login** - 認証セッション管理
- **Bootstrap 5.3** - UIフレームワーク

## セットアップ手順

### 1. 仮想環境の作成（推奨）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. アプリの起動

```bash
python app.py
```

ブラウザで [http://127.0.0.1:5000](http://127.0.0.1:5000) にアクセスしてください。

初回起動時に `todos.db`（SQLiteファイル）が自動作成されます。

## ディレクトリ構成

```
KIRO_TEST/
├── app.py                  # アプリエントリーポイント
├── config.py               # 設定ファイル
├── models.py               # データベースモデル
├── requirements.txt        # 依存パッケージ
├── routes/
│   ├── auth.py             # 認証（登録・ログイン・ログアウト）
│   ├── todos.py            # TODO CRUD・検索・フィルター
│   ├── categories.py       # カテゴリ管理
│   ├── recurrence.py       # 繰り返しタスク管理
│   └── projects.py         # プロジェクト・階層管理
├── services/
│   └── progress.py         # 進捗計算・予測ロジック
├── templates/
│   ├── base.html           # ベーステンプレート
│   ├── auth/               # ログイン・登録画面
│   ├── index.html          # TODOリスト（メイン）
│   ├── todo_form.html      # TODO追加・編集フォーム
│   ├── categories.html     # カテゴリ管理
│   ├── recurrence.html     # 繰り返しルール管理
│   ├── projects.html       # プロジェクト一覧
│   ├── project_detail.html # プロジェクト詳細・階層ツリー
│   └── project_form.html   # プロジェクト・ノード追加・編集
├── static/
│   └── css/custom.css      # カスタムスタイル
└── todos.db                # SQLiteファイル（自動生成）
```

## 環境変数

本番環境では以下の環境変数を設定してください。

| 変数名 | 説明 | デフォルト |
|--------|------|----------|
| `SECRET_KEY` | セッション暗号化キー | `dev-secret-key-change-in-production` |
| `DATABASE_URL` | DBの接続URL | `sqlite:///todos.db` |

```bash
# 例（Windows PowerShell）
$env:SECRET_KEY = "your-strong-secret-key"
python app.py
```

## プログレスバーの仕様

### 個別TODOの完成度バー

| 完成度 | バーの色 |
|--------|----------|
| 0% | グレー |
| 1〜24% | 薄い青 |
| 25〜49% | やや薄い青 |
| 50〜74% | 中程度の青 |
| 75〜99% | 濃い青 |
| 100% | 最も濃い青 |

### プロジェクト進捗バー（3色合成）

- 🔵 **青**: 達成済み進捗
- ⬜ **グレー**: 残り（予定通り）
- 🟠 **橙**: 遅延見込み分（完了予測日 > 期限日）
- 🔴 **赤**: 期限超過分（今日 > 期限日）
