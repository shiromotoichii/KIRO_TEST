# TODO管理Webアプリ 設計書

## 技術スタック

| 区分 | 技術 |
|------|------|
| 言語 | Python 3.10+ |
| Webフレームワーク | Flask 3.x |
| ORM | SQLAlchemy 2.x |
| データベース | SQLite |
| 認証 | Flask-Login + Werkzeug |
| フロントエンド | Bootstrap 5.3、Jinja2テンプレート |
| フォームバリデーション | WTForms（Flask-WTF） |

---

## ディレクトリ構成

```
KIRO_TEST/
├── app.py                      # アプリエントリーポイント・初期化
├── requirements.txt            # 依存パッケージ
├── config.py                   # 設定ファイル
├── models.py                   # SQLAlchemyモデル定義
├── routes/
│   ├── __init__.py
│   ├── auth.py                 # 認証ルート（登録・ログイン・ログアウト）
│   ├── todos.py                # TODO CRUDルート
│   ├── categories.py           # カテゴリ管理ルート
│   ├── recurrence.py           # 繰り返しタスク管理ルート
│   └── projects.py             # プロジェクト・階層管理ルート
├── services/
│   ├── __init__.py
│   └── progress.py             # 進捗計算・予測ロジック（純粋関数）
├── templates/
│   ├── base.html               # ベーステンプレート（ナビバー・フラッシュ）
│   ├── auth/
│   │   ├── login.html          # ログイン画面
│   │   └── register.html       # ユーザー登録画面
│   ├── index.html              # TODOリスト（メイン画面）
│   ├── todo_form.html          # TODO追加・編集フォーム
│   ├── categories.html         # カテゴリ管理画面
│   ├── recurrence.html         # 繰り返しルール管理画面
│   ├── projects.html           # プロジェクト一覧画面
│   ├── project_detail.html     # プロジェクト詳細・階層ツリー表示
│   └── project_form.html       # プロジェクト・ノード追加・編集フォーム
├── static/
│   └── css/
│       └── custom.css          # カスタムスタイル
└── todos.db                    # SQLiteファイル（自動生成）
```

---

## データベース設計

### テーブル: `users`

| カラム | 型 | 制約 | 説明 |
|--------|----|------|------|
| id | INTEGER | PK, AUTO INCREMENT | ユーザーID |
| username | VARCHAR(80) | NOT NULL, UNIQUE | ユーザー名 |
| email | VARCHAR(120) | NOT NULL, UNIQUE | メールアドレス |
| password_hash | VARCHAR(256) | NOT NULL | ハッシュ化パスワード |
| created_at | DATETIME | NOT NULL | 登録日時 |

### テーブル: `categories`

| カラム | 型 | 制約 | 説明 |
|--------|----|------|------|
| id | INTEGER | PK, AUTO INCREMENT | カテゴリID |
| name | VARCHAR(50) | NOT NULL | カテゴリ名 |
| color | VARCHAR(7) | NOT NULL | カラーコード（例: #3498db） |
| user_id | INTEGER | FK(users.id), NOT NULL | 所有ユーザー |
| created_at | DATETIME | NOT NULL | 作成日時 |

### テーブル: `recurrence_rules`（繰り返しルール）

| カラム | 型 | 制約 | 説明 |
|--------|----|------|------|
| id | INTEGER | PK, AUTO INCREMENT | ルールID |
| user_id | INTEGER | FK(users.id), NOT NULL | 所有ユーザー |
| title | VARCHAR(200) | NOT NULL | 繰り返しタスクのテンプレートタイトル |
| description | TEXT | NULLABLE | 詳細説明テンプレート |
| pattern | VARCHAR(10) | NOT NULL | 繰り返しパターン（daily/weekly/monthly） |
| interval_value | INTEGER | NOT NULL, DEFAULT 1 | 間隔（例: 2週ごとなら2） |
| day_of_week | INTEGER | NULLABLE | 曜日（0=月〜6=日、weeklyの場合） |
| day_of_month | INTEGER | NULLABLE | 月の日付（1〜31、monthlyの場合） |
| end_type | VARCHAR(10) | NOT NULL | 終了条件（date/count/never） |
| end_date | DATE | NULLABLE | 終了日（end_type=dateの場合） |
| end_count | INTEGER | NULLABLE | 終了回数（end_type=countの場合） |
| priority | VARCHAR(10) | NOT NULL, DEFAULT 'medium' | 優先度テンプレート |
| category_id | INTEGER | FK(categories.id), NULLABLE | カテゴリテンプレート |
| created_at | DATETIME | NOT NULL | 作成日時 |

### テーブル: `project_nodes`（プロジェクト・サブタスク階層）

階層構造は**隣接リスト（Adjacency List）**で表現する。
ルートノード（`parent_id IS NULL`）がプロジェクト、子ノードがサブタスク。
階層の深さは無制限（再帰的に子を持てる）。

| カラム | 型 | 制約 | 説明 |
|--------|----|------|------|
| id | INTEGER | PK, AUTO INCREMENT | ノードID |
| user_id | INTEGER | FK(users.id), NOT NULL | 所有ユーザー |
| parent_id | INTEGER | FK(project_nodes.id), NULLABLE | 親ノードID（NULLはルート=プロジェクト） |
| title | VARCHAR(200) | NOT NULL | タイトル（例: TOEIC 850点取得） |
| description | TEXT | NULLABLE | 説明 |
| progress_mode | VARCHAR(10) | NOT NULL, DEFAULT 'percent' | 進捗モード（percent / numeric） |
| target_value | FLOAT | NULLABLE | 目標値（numericモード、例: 6000） |
| current_value | FLOAT | NULLABLE | 現在値（numericモード、例: 3500） |
| unit | VARCHAR(20) | NULLABLE | 単位（例: 単語、点） |
| start_date | DATE | NULLABLE | 開始日 |
| due_date | DATE | NULLABLE | 期限日 |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 | 同階層内の表示順 |
| created_at | DATETIME | NOT NULL | 作成日時 |
| updated_at | DATETIME | NOT NULL | 更新日時 |

### テーブル: `todos`

| カラム | 型 | 制約 | 説明 |
|--------|----|------|------|
| id | INTEGER | PK, AUTO INCREMENT | TODO ID |
| user_id | INTEGER | FK(users.id), NOT NULL | 所有ユーザー |
| title | VARCHAR(200) | NOT NULL | タイトル |
| description | TEXT | NULLABLE | 詳細説明 |
| is_completed | BOOLEAN | NOT NULL, DEFAULT FALSE | 完了フラグ |
| priority | VARCHAR(10) | NOT NULL, DEFAULT 'medium' | 優先度（high/medium/low） |
| due_date | DATE | NULLABLE | 締め切り日 |
| progress | INTEGER | NOT NULL, DEFAULT 0 | 完成度（0〜100） |
| category_id | INTEGER | FK(categories.id), NULLABLE | カテゴリID |
| recurrence_rule_id | INTEGER | FK(recurrence_rules.id), NULLABLE | 繰り返しルールID |
| recurrence_index | INTEGER | NULLABLE | 繰り返し内の連番（何回目か） |
| project_node_id | INTEGER | FK(project_nodes.id), NULLABLE | 紐付くプロジェクトノードID |
| created_at | DATETIME | NOT NULL | 作成日時 |
| updated_at | DATETIME | NOT NULL | 更新日時 |

---

## 進捗計算ロジック（`services/progress.py`）

### ノード進捗の計算（再帰）

```python
def calc_node_progress(node) -> float:
    """
    子ノードが存在する場合 → 子ノードの進捗の平均を返す（再帰）
    子ノードがない場合 → progress_mode に応じて計算
      - percent: node に紐付く todos の progress の平均
      - numeric: current_value / target_value * 100
    """
```

### 進捗速度・完了予測日の計算

```python
def calc_forecast(node, today) -> dict:
    """
    戻り値:
      {
        "speed_per_day": float,      # 1日あたりの進捗速度（%/日）
        "forecast_date": date|None,  # 完了予測日（速度0の場合None）
        "overrun_days": int,         # 超過日数（予測超過: 橙、実超過: 赤）
        "status": "on_track" | "at_risk" | "overdue" | "no_progress"
      }

    計算式:
      経過日数 = today - node.start_date
      速度 = current_progress / 経過日数  （経過日数=0なら速度=0）
      残り進捗 = 100 - current_progress
      完了予測日 = today + (残り進捗 / 速度) 日後  （速度=0ならNone）

    ステータス判定:
      overdue    : today > due_date
      at_risk    : forecast_date > due_date（期限内だが遅延見込み）
      on_track   : forecast_date <= due_date
      no_progress: speed = 0
    """
```

---

## 画面構成

### 1. ログイン画面（`/auth/login`）
- メールアドレス・パスワード入力フォーム
- ユーザー登録画面へのリンク

### 2. ユーザー登録画面（`/auth/register`）
- ユーザー名・メールアドレス・パスワード入力フォーム

### 3. メイン画面（`/`）
- ナビゲーションバー（アプリ名、ログインユーザー名、ログアウト、各管理ページリンク）
- フィルターエリア（検索・完了状態・優先度・カテゴリ・ソート）
- TODOカード一覧（完成度プログレスバー付き、繰り返しアイコン）
- 右下フローティングボタン（新規TODO追加）

### 4. TODO追加・編集画面（`/todo/new`、`/todo/<id>/edit`）
- タイトル・説明・優先度・締め切り日・カテゴリ・完成度スライダー
- 繰り返し設定セクション（新規のみ）
- プロジェクトノードへの紐付け選択（任意）

### 5. カテゴリ管理画面（`/categories`）

### 6. 繰り返しルール管理画面（`/recurrence`）

### 7. プロジェクト一覧画面（`/projects`）
- プロジェクトカード一覧（全体進捗バー・予測情報・オーバー表示）
- 新規プロジェクト追加ボタン

### 8. プロジェクト詳細画面（`/projects/<id>`）
- 階層ツリー表示（インデントで深さを表現）
- 各ノードに進捗バー（通常/遅延見込み/超過で色変化）
- 子ノード追加ボタン・編集・削除ボタン
- 紐付きTODOリスト表示

---

## URLルーティング

| メソッド | URL | 認証 | 説明 |
|----------|-----|------|------|
| GET | `/auth/login` | 不要 | ログイン画面 |
| POST | `/auth/login` | 不要 | ログイン処理 |
| GET | `/auth/register` | 不要 | ユーザー登録画面 |
| POST | `/auth/register` | 不要 | ユーザー登録処理 |
| GET | `/auth/logout` | 必要 | ログアウト処理 |
| GET | `/` | 必要 | TODOリスト（検索・フィルター・ソート） |
| GET | `/todo/new` | 必要 | TODO追加フォーム |
| POST | `/todo/new` | 必要 | TODO新規作成 |
| GET | `/todo/<id>/edit` | 必要 | TODO編集フォーム |
| POST | `/todo/<id>/edit` | 必要 | TODO更新 |
| POST | `/todo/<id>/toggle` | 必要 | 完了/未完了切り替え |
| POST | `/todo/<id>/delete` | 必要 | TODO削除 |
| GET | `/categories` | 必要 | カテゴリ管理画面 |
| POST | `/categories/new` | 必要 | カテゴリ新規作成 |
| POST | `/categories/<id>/edit` | 必要 | カテゴリ更新 |
| POST | `/categories/<id>/delete` | 必要 | カテゴリ削除 |
| GET | `/recurrence` | 必要 | 繰り返しルール一覧 |
| POST | `/recurrence/new` | 必要 | 繰り返しルール新規作成 |
| POST | `/recurrence/<id>/generate` | 必要 | 今月分を一括生成 |
| POST | `/recurrence/<id>/delete` | 必要 | 繰り返しグループ削除 |
| GET | `/projects` | 必要 | プロジェクト一覧 |
| POST | `/projects/new` | 必要 | プロジェクト新規作成 |
| GET | `/projects/<id>` | 必要 | プロジェクト詳細・階層ツリー |
| POST | `/projects/<id>/edit` | 必要 | プロジェクト更新 |
| POST | `/projects/<id>/delete` | 必要 | プロジェクト削除 |
| POST | `/projects/<id>/node/new` | 必要 | 子ノード追加 |
| POST | `/projects/node/<id>/edit` | 必要 | ノード更新 |
| POST | `/projects/node/<id>/delete` | 必要 | ノード削除 |

---

## UIデザイン方針

### 優先度バッジ
- 高: `badge bg-danger`（赤）
- 中: `badge bg-warning text-dark`（橙）
- 低: `badge bg-success`（緑）

### 締め切り強調
- 期限切れ: `border-danger`、日付テキストを赤
- 本日締め切り: `border-warning`、日付テキストを橙

### 完了済みTODO
- タイトルに取り消し線 + カードをグレーアウト（`opacity: 0.6`）

### 個別TODO完成度プログレスバー

| 完成度 | バーの色 |
|--------|----------|
| 0% | グレー |
| 1〜24% | 薄い青（`#a8d1f5`） |
| 25〜49% | やや薄い青（`#5aaee8`） |
| 50〜74% | 中程度の青（`#1e7fc4`） |
| 75〜99% | 濃い青（`#0d4f8a`） |
| 100% | 最も濃い青/深緑（`#0a3660`） |

数値（例: `75%`）をバー内中央に常時表示。

### プロジェクト進捗バー（3色合成バー）

```
通常時（on_track）:
|████████████░░░░░░░░|
 青（達成分）  グレー（残り）

遅延見込み時（at_risk）:
|████████░░░░░░|🟧🟧🟧|
 青（達成）  残り  橙（予測オーバー分）
 ※「予測: +N日」テキストを右に表示

期限超過時（overdue）:
|████████████████|🟥🟥🟥|
 青（達成分）      赤（超過日数分）
 ※「+N日超過」テキストを赤色で表示

進捗なし時（no_progress）:
|░░░░░░░░░░░░░░░░░░░░|
 グレー全体 ※「進捗なし」テキスト
```

実装はBootstrap `progress` の `d-flex` 複数バーで実現する。
数値モードの場合は `現在値 / 目標値（単位）` もバー下に表示する。

### 繰り返しタスクの識別
- カードに🔁アイコン + 「繰り返し」バッジを表示

### プロジェクト階層ツリー
- インデント（`ms-3` per 階層）でネストを表現
- 折りたたみ/展開はBootstrap `collapse` で実装
