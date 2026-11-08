from datetime import date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Todo, Category, ProjectNode
from services.holidays import get_all_holidays, is_weekend, is_holiday

todos_bp = Blueprint("todos", __name__)


@todos_bp.route("/")
@login_required
def index():
    # 表示モード: list / calendar
    view_mode = request.args.get("view", "calendar")

    # ── フィルター・検索・ソートパラメータ取得 ──
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "all")
    priority = request.args.get("priority", "all")
    cat_id = request.args.get("category", "all")
    sort = request.args.get("sort", "created_desc")

    query = Todo.query.filter_by(user_id=current_user.id)

    # キーワード検索
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Todo.title.ilike(like), Todo.description.ilike(like))
        )

    # 完了状態フィルター
    if status == "active":
        query = query.filter_by(is_completed=False)
    elif status == "completed":
        query = query.filter_by(is_completed=True)

    # 優先度フィルター
    if priority != "all":
        query = query.filter_by(priority=priority)

    # カテゴリフィルター
    if cat_id != "all":
        if cat_id == "none":
            query = query.filter(Todo.category_id.is_(None))
        else:
            query = query.filter_by(category_id=int(cat_id))

    # ソート
    if sort == "due_asc":
        query = query.order_by(Todo.due_date.asc().nulls_last())
    elif sort == "due_desc":
        query = query.order_by(Todo.due_date.desc().nulls_first())
    elif sort == "priority":
        # high→medium→low の順（SQLAlchemy 2.x の whens 辞書構文）
        from sqlalchemy import case as sa_case
        priority_order = sa_case(
            {
                "high": 1,
                "medium": 2,
                "low": 3,
            },
            value=Todo.priority,
            else_=4,
        )
        query = query.order_by(priority_order)
    else:  # created_desc（デフォルト）
        query = query.order_by(Todo.created_at.desc())

    todos = query.all()
    categories = (Category.query
                  .filter_by(user_id=current_user.id)
                  .order_by(Category.name)
                  .all())

    # カレンダー表示用：如果截止日期，则返回该日期的事件
    # FullCalendar expects: { title, start, end, color, url }
    calendar_events = []
    for t in todos:
        if t.due_date:
            event = {
                "id": t.id,
                "title": t.title,
                "start": t.due_date.isoformat(),
                "allDay": True,
                "url": url_for("todos.edit", todo_id=t.id, _external=True),
            }
            # 颜色基于优先级和完成状态
            if t.is_completed:
                event["color"] = "#6c757d"  # 灰色
                event["title"] = "✅ " + t.title
            elif t.priority == "high":
                event["color"] = "#dc3545"  # 红色
            elif t.priority == "medium":
                event["color"] = "#fd7e14"  # 橙色
            else:
                event["color"] = "#198754"  # 绿色
            
            calendar_events.append(event)

    # 祝日の日付リストを作成（services.holidaysから取得）
    all_holidays = get_all_holidays()
    holidays = list(all_holidays.keys())

    return render_template(
        "index.html",
        todos=todos,
        categories=categories,
        today=date.today(),
        q=q, status=status, priority=priority,
        cat_id=cat_id, sort=sort,
        view_mode=view_mode,
        calendar_events=calendar_events,
        holidays=holidays,
    )


@todos_bp.route("/api/events")
@login_required
def api_events():
    """返回FullCalendar的事件数据（JSON）"""
    start = request.args.get("start")
    end = request.args.get("end")
    
    query = Todo.query.filter_by(user_id=current_user.id)
    
    # 按日期范围过滤
    if start:
        query = query.filter(Todo.due_date >= start)
    if end:
        query = query.filter(Todo.due_date <= end)
    
    todos = query.all()
    
    events = []
    for t in todos:
        if t.due_date:
            event = {
                "id": t.id,
                "title": t.title,
                "start": t.due_date.isoformat(),
                "allDay": True,
                "url": url_for("todos.edit", todo_id=t.id, _external=True),
            }
            if t.is_completed:
                event["color"] = "#6c757d"
            elif t.priority == "high":
                event["color"] = "#dc3545"
            elif t.priority == "medium":
                event["color"] = "#fd7e14"
            else:
                event["color"] = "#198754"
            events.append(event)
    
    return jsonify(events)


@todos_bp.route("/todo/new", methods=["GET", "POST"])
@login_required
def new():
    categories = (Category.query
                  .filter_by(user_id=current_user.id)
                  .order_by(Category.name).all())
    # プロジェクトノード（ルートのみ）を選択肢に
    project_nodes = (ProjectNode.query
                     .filter_by(user_id=current_user.id)
                     .order_by(ProjectNode.title).all())

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("タイトルを入力してください。", "danger")
            return render_template("todo_form.html", categories=categories,
                                   project_nodes=project_nodes, todo=None)

        description = request.form.get("description", "").strip() or None
        priority = request.form.get("priority", "medium")
        due_date_str = request.form.get("due_date", "")
        due_date = _parse_date(due_date_str)
        progress = _clamp_progress(request.form.get("progress", 0))
        category_id = _parse_int(request.form.get("category_id"))
        project_node_id = _parse_int(request.form.get("project_node_id"))

        todo = Todo(
            user_id=current_user.id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            progress=progress,
            category_id=category_id,
            project_node_id=project_node_id,
        )
        db.session.add(todo)

        # 繰り返し設定がある場合は RecurrenceRule を作成
        recur_pattern = request.form.get("recur_pattern", "")
        if recur_pattern:
            from models import RecurrenceRule
            from routes.recurrence import _parse_date as rd_parse
            rule = RecurrenceRule(
                user_id=current_user.id,
                title=title,
                description=description,
                pattern=recur_pattern,
                interval_value=max(1, int(request.form.get("recur_interval", 1) or 1)),
                day_of_week=_parse_int(request.form.get("recur_day_of_week")),
                day_of_month=_parse_int(request.form.get("recur_day_of_month")),
                end_type=request.form.get("recur_end_type", "never"),
                end_date=_parse_date(request.form.get("recur_end_date", "")),
                end_count=_parse_int(request.form.get("recur_end_count")),
                priority=priority,
                category_id=category_id,
            )
            db.session.add(rule)
            db.session.flush()
            todo.recurrence_rule_id = rule.id
            todo.recurrence_index = 0

        db.session.commit()
        flash(f"「{title}」を追加しました。", "success")
        return redirect(url_for("todos.index"))

    return render_template("todo_form.html", categories=categories,
                           project_nodes=project_nodes, todo=None)


@todos_bp.route("/todo/<int:todo_id>/edit", methods=["GET", "POST"])
@login_required
def edit(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    categories = (Category.query
                  .filter_by(user_id=current_user.id)
                  .order_by(Category.name).all())
    project_nodes = (ProjectNode.query
                     .filter_by(user_id=current_user.id)
                     .order_by(ProjectNode.title).all())

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("タイトルを入力してください。", "danger")
            return render_template("todo_form.html", todo=todo,
                                   categories=categories, project_nodes=project_nodes)

        todo.title = title
        todo.description = request.form.get("description", "").strip() or None
        todo.priority = request.form.get("priority", todo.priority)
        todo.due_date = _parse_date(request.form.get("due_date", ""))
        todo.progress = _clamp_progress(request.form.get("progress", todo.progress))
        todo.category_id = _parse_int(request.form.get("category_id"))
        todo.project_node_id = _parse_int(request.form.get("project_node_id"))

        # 繰り返しタスクの編集スコープ処理
        scope = request.form.get("recur_edit_scope", "single")
        if todo.recurrence_rule_id and scope == "future":
            # 以降すべてのTODO（同ルール・同index以降）を一括更新
            future_todos = (Todo.query
                            .filter_by(recurrence_rule_id=todo.recurrence_rule_id)
                            .filter(Todo.recurrence_index >= todo.recurrence_index)
                            .all())
            for ft in future_todos:
                ft.title = title
                ft.description = todo.description
                ft.priority = todo.priority
                ft.category_id = todo.category_id
        elif todo.recurrence_rule_id and scope == "single":
            # この1件のみ: 繰り返しルールから切り離す
            todo.recurrence_rule_id = None
            todo.recurrence_index = None

        # 完成度100%で自動完了フラグ
        if todo.progress == 100:
            todo.is_completed = True

        db.session.commit()
        flash(f"「{todo.title}」を更新しました。", "success")
        return redirect(url_for("todos.index"))

    return render_template("todo_form.html", todo=todo,
                           categories=categories, project_nodes=project_nodes)


@todos_bp.route("/todo/<int:todo_id>/toggle", methods=["POST"])
@login_required
def toggle(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    todo.is_completed = not todo.is_completed
    db.session.commit()
    return redirect(url_for("todos.index"))


@todos_bp.route("/todo/<int:todo_id>/delete", methods=["POST"])
@login_required
def delete(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    title = todo.title
    db.session.delete(todo)
    db.session.commit()
    flash(f"「{title}」を削除しました。", "success")
    return redirect(url_for("todos.index"))


# ── ユーティリティ ──────────────────────────────────────
def _parse_date(value: str):
    if value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return None


def _parse_int(value):
    if value and str(value).strip():
        try:
            return int(value)
        except ValueError:
            pass
    return None


def _clamp_progress(value) -> int:
    try:
        return max(0, min(100, int(value)))
    except (ValueError, TypeError):
        return 0
