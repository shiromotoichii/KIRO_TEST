# TODO管理Webアプリ 実装タスク

## タスク一覧

### Phase 1: プロジェクトのセットアップ

- [ ] **Task 1-1**: `requirements.txt` を作成する
  - Flask、SQLAlchemy、Flask-Login、Flask-WTF、Werkzeug を含める
- [ ] **Task 1-2**: `config.py` を作成する
  - SQLiteのDB接続パス、SECRET_KEY などを定義する
- [ ] **Task 1-3**: `app.py` を作成する
  - Flaskアプリの初期化、SQLAlchemy・Flask-Login の登録、Blueprint の登録、DB初期化処理
- [ ] **Task 1-4**: `models.py` を作成する
  - `User`、`Category`、`RecurrenceRule`、`Todo`、`ProjectNode` の5モデルを定義する
  - `User` に Flask-Login 用の `UserMixin` を継承させる
  - `Todo.progress`（0〜100）、`Todo.recurrence_rule_id`、`Todo.recurrence_index`、`Todo.project_node_id` を含める
  - `ProjectNode` は自己参照の隣接リスト（`parent_id` → `ProjectNode.id`）で定義する

---

### Phase 2: 認証機能

- [ ] **Task 2-1**: `routes/auth.py` を作成する
  - ユーザー登録（GET/POST `/auth/register`）を実装する
  - パスワードは `werkzeug.security.generate_password_hash` でハッシュ化する
- [ ] **Task 2-2**: ログイン（GET/POST `/auth/login`）を実装する
  - `flask_login.login_user` でセッション管理する
  - ログイン済みの場合はメイン画面にリダイレクト
- [ ] **Task 2-3**: ログアウト（GET `/auth/logout`）を実装する
- [ ] **Task 2-4**: 未ログイン時のリダイレクト設定を実装する
  - `login_manager.login_view` を設定し、`@login_required` デコレータをすべての保護ルートに適用する

---

### Phase 3: カテゴリ機能

- [ ] **Task 3-1**: `routes/categories.py` を作成する
  - カテゴリ一覧表示（GET `/categories`）を実装する（ログインユーザーのみ）
- [ ] **Task 3-2**: カテゴリの追加（POST `/categories/new`）を実装する
- [ ] **Task 3-3**: カテゴリの編集（POST `/categories/<id>/edit`）を実装する
- [ ] **Task 3-4**: カテゴリの削除（POST `/categories/<id>/delete`）を実装する
  - 紐付くTODOの `category_id` を NULL にする処理を含める

---

### Phase 4: TODO基本機能

- [ ] **Task 4-1**: `routes/todos.py` を作成する
  - TODOリスト表示（GET `/`）を実装する
  - ログインユーザーのTODOのみ取得するクエリを書く
- [ ] **Task 4-2**: 検索・フィルター・ソートのクエリロジックを実装する
  - キーワード検索、完了状態・優先度・カテゴリフィルター、締め切り日/優先度ソート
- [ ] **Task 4-3**: TODO追加（GET/POST `/todo/new`）を実装する
  - プロジェクトノードへの紐付け選択（任意）も含める
- [ ] **Task 4-4**: TODO編集（GET/POST `/todo/<id>/edit`）を実装する
  - 編集対象が自分のTODOかチェックする（他ユーザーのTODOは403）
- [ ] **Task 4-5**: 完了/未完了切り替え（POST `/todo/<id>/toggle`）を実装する
- [ ] **Task 4-6**: TODO削除（POST `/todo/<id>/delete`）を実装する

---

### Phase 5: 完成度機能

- [ ] **Task 5-1**: `Todo.progress` フィールドをTODO追加・編集フォームに組み込む
  - 0〜100のスライダー（`<input type="range">`）と数値表示を連動させる
- [ ] **Task 5-2**: `static/css/custom.css` に完成度プログレスバーのスタイルを定義する
  - `progress-level-1`〜`progress-level-5` のクラスを定義し色の濃さを段階的に変える
  - バー内に数値（例: `75%`）を中央表示するスタイルを実装する
- [ ] **Task 5-3**: TODOカードのプログレスバー表示を `index.html` に実装する
  - 完成度の値に応じてJinja2でクラスを切り替える
- [ ] **Task 5-4**: 完成度が100%になった際に完了確認ダイアログを表示するJavaScriptを実装する

---

### Phase 6: 繰り返しタスク機能

- [ ] **Task 6-1**: `routes/recurrence.py` を作成する
  - 繰り返しルール一覧（GET `/recurrence`）を実装する
- [ ] **Task 6-2**: TODO追加フォームに繰り返し設定セクションを追加する
  - パターン（なし/毎日/毎週/毎月）、間隔、終了条件（終了日/回数）の入力項目
  - パターン選択に応じてフォームの表示/非表示をJavaScriptで制御する
- [ ] **Task 6-3**: 繰り返しルールの保存ロジックを実装する
  - TODO作成時に `RecurrenceRule` を作成し、最初の1件のTODOを生成する
- [ ] **Task 6-4**: 「今月分を生成」ボタンの処理（POST `/recurrence/<id>/generate`）を実装する
  - 繰り返しパターン（daily/weekly/monthly）に基づいて当月の対象日を計算する
  - 終了条件（end_date/end_count）を考慮して生成件数を制限する
  - 既に生成済みの日付は重複生成しない
- [ ] **Task 6-5**: TODO編集時の繰り返し編集オプションを実装する
  - 「この1件のみ変更」：該当TODOの `recurrence_rule_id` を切り離して単独化する
  - 「以降すべてに変更」：同ルールの `recurrence_index` 以降のTODOを一括更新する
- [ ] **Task 6-6**: 繰り返しグループ削除（POST `/recurrence/<id>/delete`）を実装する
  - 未完了の将来タスクを一括削除するか、ルールのみ削除するかを選択できるようにする

---

### Phase 7: プロジェクト・階層機能

- [ ] **Task 7-1**: `services/progress.py` を作成する
  - `calc_node_progress(node)` を実装する（再帰的に子ノードの進捗を集計）
    - `percent` モード：紐付くTODOの `progress` の平均
    - `numeric` モード：`current_value / target_value * 100`
    - 子ノードが存在する場合：子ノードの進捗の平均（再帰）
- [ ] **Task 7-2**: `services/progress.py` に `calc_forecast(node, today)` を実装する
  - 1日あたりの進捗速度 = 現在進捗 / 経過日数
  - 完了予測日 = today + （残り進捗 / 速度）日
  - ステータス判定：`on_track` / `at_risk` / `overdue` / `no_progress`
  - 超過日数の計算（`at_risk`: 予測超過日数、`overdue`: 実超過日数）
- [ ] **Task 7-3**: `routes/projects.py` を作成する
  - プロジェクト一覧（GET `/projects`）を実装する
  - 各プロジェクトに `calc_node_progress` と `calc_forecast` を適用して渡す
- [ ] **Task 7-4**: プロジェクト新規作成（POST `/projects/new`）を実装する
  - ルートノード（`parent_id=None`）として `ProjectNode` を作成する
- [ ] **Task 7-5**: プロジェクト詳細画面（GET `/projects/<id>`）を実装する
  - ルートノードを起点に子ノードを再帰取得し、階層ツリーとしてテンプレートに渡す
- [ ] **Task 7-6**: 子ノード追加（POST `/projects/<id>/node/new`）を実装する
  - `parent_id` を指定してサブタスクノードを作成する
  - `progress_mode`・`target_value`・`unit` も保存する
- [ ] **Task 7-7**: ノード編集（POST `/projects/node/<id>/edit`）を実装する
- [ ] **Task 7-8**: ノード削除（POST `/projects/node/<id>/delete`）を実装する
  - 子ノードを再帰的に削除する（CASCADE設定またはアプリ側で処理）
- [ ] **Task 7-9**: プロジェクト削除（POST `/projects/<id>/delete`）を実装する

---

### Phase 8: フロントエンド実装

- [ ] **Task 8-1**: `templates/base.html` を作成する
  - Bootstrap 5 CDN読み込み、ナビバー（ログインユーザー名・ログアウト・各管理ページリンク）
  - フラッシュメッセージ（success/danger）の表示エリア
- [ ] **Task 8-2**: `templates/auth/login.html` と `templates/auth/register.html` を作成する
  - カード中央寄せのログイン・登録フォーム
- [ ] **Task 8-3**: `templates/index.html` を作成する
  - フィルターエリア（検索・ドロップダウン・ソート）
  - TODOカード（優先度バッジ・カテゴリバッジ・締め切り・完成度バー・繰り返しアイコン）
  - 新規追加フローティングボタン（右下）
- [ ] **Task 8-4**: `templates/todo_form.html` を作成する（追加・編集共用）
  - 完成度スライダー、繰り返し設定セクション（JavaScriptで動的表示）
  - 編集時は繰り返し編集オプション（この1件のみ/以降すべて）を表示
  - プロジェクトノードへの紐付けセレクトボックス
- [ ] **Task 8-5**: `templates/categories.html` を作成する
- [ ] **Task 8-6**: `templates/recurrence.html` を作成する
  - 繰り返しルール一覧、「今月分を生成」ボタン、グループ削除ボタン
- [ ] **Task 8-7**: `templates/projects.html` を作成する
  - プロジェクトカード一覧
  - 各カードに3色合成プログレスバー（on_track/at_risk/overdue/no_progress）
  - 完了予測日・超過日数テキストを表示
- [ ] **Task 8-8**: `templates/project_detail.html` を作成する
  - Bootstrap `collapse` を使った折りたたみ可能な階層ツリー
  - 各ノードに進捗バー・予測テキスト・子ノード追加ボタン
  - numericモードのノードは「現在値 / 目標値（単位）」をバー下に表示
- [ ] **Task 8-9**: `templates/project_form.html` を作成する（プロジェクト・ノード追加・編集共用）
  - `progress_mode` 選択に応じて `target_value`・`current_value`・`unit` 入力欄をJavaScriptで表示切替
- [ ] **Task 8-10**: `static/css/custom.css` を作成する
  - 個別TODO完成度バースタイル（`progress-level-1`〜`5`）
  - 3色合成プロジェクト進捗バースタイル（青/橙/赤）
  - 期限切れ・本日締め切りのカード強調スタイル
  - 完了済みTODOの取り消し線・グレーアウトスタイル
  - 階層ツリーのインデントスタイル

---

### Phase 9: 動作確認・仕上げ

- [ ] **Task 9-1**: ユーザー登録・ログイン・ログアウト・認証ガードの動作確認
- [ ] **Task 9-2**: TODO基本操作（追加・編集・完了・削除）の動作確認
- [ ] **Task 9-3**: 完成度スライダー・プログレスバーの色階調の動作確認
- [ ] **Task 9-4**: 繰り返しタスクの生成・編集・削除の動作確認
- [ ] **Task 9-5**: プロジェクト作成・階層ノード追加・進捗計算の動作確認
- [ ] **Task 9-6**: 進捗予測・オーバーバー（橙/赤）の表示確認
- [ ] **Task 9-7**: 検索・フィルター・ソートの動作確認
- [ ] **Task 9-8**: `README.md` を作成する（セットアップ手順・起動方法）

---

## 実装順序の依存関係

```
Phase 1（セットアップ）
  └─ Phase 2（認証）
       └─ Phase 3（カテゴリ）
            └─ Phase 4（TODO基本）
                 ├─ Phase 5（完成度）
                 ├─ Phase 6（繰り返し）
                 └─ Phase 7（プロジェクト・階層）← services/progress.py が先
                      └─ Phase 8（フロントエンド）
                           └─ Phase 9（動作確認）
```

- Phase 7-1・7-2（`services/progress.py`）は Phase 7-3 以降より先に完了させること
- Phase 8（テンプレート）は Phase 4〜7 のルート実装と並行して進めることができる
- Phase 9 は Phase 1〜8 がすべて完了してから実施すること

---

## タスク数サマリー

| Phase | 内容 | タスク数 |
|-------|------|---------|
| Phase 1 | プロジェクトセットアップ | 4 |
| Phase 2 | 認証機能 | 4 |
| Phase 3 | カテゴリ機能 | 4 |
| Phase 4 | TODO基本機能 | 6 |
| Phase 5 | 完成度機能 | 4 |
| Phase 6 | 繰り返しタスク機能 | 6 |
| Phase 7 | プロジェクト・階層機能 | 9 |
| Phase 8 | フロントエンド実装 | 10 |
| Phase 9 | 動作確認・仕上げ | 8 |
| **合計** | | **55** |
