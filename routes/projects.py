from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import ProjectNode, Todo, Category
from services.progress import calc_node_progress, calc_forecast, build_progress_bar_segments

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


# ── プロジェクト一覧 ────────────────────────────────────
@projects_bp.route("/")
@login_required
def index():
    roots = (ProjectNode.query
             .filter_by(user_id=current_user.id, parent_id=None)
             .order_by(ProjectNode.sort_order, ProjectNode.title)
             .all())
    today = date.today()
    project_data = []
    for node in roots:
        progress = calc_node_progress(node)
        forecast = calc_forecast(node, today)
        segments = build_progress_bar_segments(forecast)
        project_data.append({
            "node": node,
            "progress": progress,
            "forecast": forecast,
            "segments": segments,
        })
    return render_template("projects.html", project_data=project_data)


# ── プロジェクト新規作成 ────────────────────────────────
@projects_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("タイトルを入力してください。", "danger")
            return render_template("project_form.html", node=None, parent=None)

        node = ProjectNode(
            user_id=current_user.id,
            parent_id=None,
            title=title,
            description=request.form.get("description", "").strip() or None,
            progress_mode=request.form.get("progress_mode", "percent"),
            target_value=_parse_float(request.form.get("target_value")),
            current_value=_parse_float(request.form.get("current_value")) or 0.0,
            unit=request.form.get("unit", "").strip() or None,
            start_date=_parse_date(request.form.get("start_date", "")),
            due_date=_parse_date(request.form.get("due_date", "")),
        )
        db.session.add(node)
        db.session.commit()
        flash(f"プロジェクト「{title}」を作成しました。", "success")
        return redirect(url_for("projects.index"))

    return render_template("project_form.html", node=None, parent=None)


# ── プロジェクト詳細（階層ツリー） ──────────────────────
@projects_bp.route("/<int:node_id>")
@login_required
def detail(node_id):
    root = ProjectNode.query.filter_by(
        id=node_id, user_id=current_user.id, parent_id=None
    ).first_or_404()

    today = date.today()
    tree = _build_tree(root, today)
    categories = (Category.query
                  .filter_by(user_id=current_user.id)
                  .order_by(Category.name).all())
    return render_template("project_detail.html",
                           root=root, tree=tree,
                           today=today, categories=categories)


# ── プロジェクト編集 ────────────────────────────────────
@projects_bp.route("/<int:node_id>/edit", methods=["POST"])
@login_required
def edit(node_id):
    node = ProjectNode.query.filter_by(
        id=node_id, user_id=current_user.id
    ).first_or_404()

    title = request.form.get("title", "").strip()
    if not title:
        flash("タイトルを入力してください。", "danger")
        return redirect(url_for("projects.detail", node_id=node.id if not node.is_root else node_id))

    node.title = title
    node.description = request.form.get("description", "").strip() or None
    node.progress_mode = request.form.get("progress_mode", node.progress_mode)
    node.target_value = _parse_float(request.form.get("target_value"))
    node.current_value = _parse_float(request.form.get("current_value")) or 0.0
    node.unit = request.form.get("unit", "").strip() or None
    node.start_date = _parse_date(request.form.get("start_date", ""))
    node.due_date = _parse_date(request.form.get("due_date", ""))
    db.session.commit()
    flash("更新しました。", "success")

    # ルートへリダイレクト
    root_id = _get_root_id(node)
    return redirect(url_for("projects.detail", node_id=root_id))


# ── プロジェクト削除 ────────────────────────────────────
@projects_bp.route("/<int:node_id>/delete", methods=["POST"])
@login_required
def delete(node_id):
    node = ProjectNode.query.filter_by(
        id=node_id, user_id=current_user.id, parent_id=None
    ).first_or_404()
    title = node.title
    _delete_node_recursive(node)
    db.session.commit()
    flash(f"プロジェクト「{title}」を削除しました。", "success")
    return redirect(url_for("projects.index"))


# ── 子ノード追加 ────────────────────────────────────────
@projects_bp.route("/<int:parent_id>/node/new", methods=["GET", "POST"])
@login_required
def node_new(parent_id):
    parent = ProjectNode.query.filter_by(
        id=parent_id, user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("タイトルを入力してください。", "danger")
            return render_template("project_form.html", node=None, parent=parent)

        # 同階層の sort_order
        sibling_count = ProjectNode.query.filter_by(parent_id=parent_id).count()
        node = ProjectNode(
            user_id=current_user.id,
            parent_id=parent_id,
            title=title,
            description=request.form.get("description", "").strip() or None,
            progress_mode=request.form.get("progress_mode", "percent"),
            target_value=_parse_float(request.form.get("target_value")),
            current_value=_parse_float(request.form.get("current_value")) or 0.0,
            unit=request.form.get("unit", "").strip() or None,
            start_date=_parse_date(request.form.get("start_date", "")),
            due_date=_parse_date(request.form.get("due_date", "")),
            sort_order=sibling_count,
        )
        db.session.add(node)
        db.session.commit()
        flash(f"サブタスク「{title}」を追加しました。", "success")
        root_id = _get_root_id(node)
        return redirect(url_for("projects.detail", node_id=root_id))

    return render_template("project_form.html", node=None, parent=parent)


# ── ノード編集 ──────────────────────────────────────────
@projects_bp.route("/node/<int:node_id>/edit", methods=["GET", "POST"])
@login_required
def node_edit(node_id):
    node = ProjectNode.query.filter_by(
        id=node_id, user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("タイトルを入力してください。", "danger")
            return render_template("project_form.html", node=node,
                                   parent=node.parent)

        node.title = title
        node.description = request.form.get("description", "").strip() or None
        node.progress_mode = request.form.get("progress_mode", node.progress_mode)
        node.target_value = _parse_float(request.form.get("target_value"))
        node.current_value = _parse_float(request.form.get("current_value")) or 0.0
        node.unit = request.form.get("unit", "").strip() or None
        node.start_date = _parse_date(request.form.get("start_date", ""))
        node.due_date = _parse_date(request.form.get("due_date", ""))
        db.session.commit()
        flash("更新しました。", "success")
        root_id = _get_root_id(node)
        return redirect(url_for("projects.detail", node_id=root_id))

    return render_template("project_form.html", node=node, parent=node.parent)


# ── ノード削除 ──────────────────────────────────────────
@projects_bp.route("/node/<int:node_id>/delete", methods=["POST"])
@login_required
def node_delete(node_id):
    node = ProjectNode.query.filter_by(
        id=node_id, user_id=current_user.id
    ).first_or_404()

    root_id = _get_root_id(node)
    title = node.title
    _delete_node_recursive(node)
    db.session.commit()
    flash(f"「{title}」を削除しました。", "success")
    return redirect(url_for("projects.detail", node_id=root_id))


# ── ユーティリティ ──────────────────────────────────────
def _build_tree(node: ProjectNode, today: date, depth: int = 0) -> dict:
    """ノードを再帰的にツリー辞書に変換する"""
    progress = calc_node_progress(node)
    forecast = calc_forecast(node, today)
    segments = build_progress_bar_segments(forecast)
    todos = node.todos.order_by(Todo.created_at.desc()).all()
    children = (node.children
                .order_by(ProjectNode.sort_order, ProjectNode.title)
                .all())
    return {
        "node": node,
        "depth": depth,
        "progress": round(progress, 1),
        "forecast": forecast,
        "segments": segments,
        "todos": todos,
        "children": [_build_tree(c, today, depth + 1) for c in children],
    }


def _get_root_id(node: ProjectNode) -> int:
    """ノードのルート（プロジェクト）IDを返す"""
    current = node
    while current.parent_id is not None:
        current = current.parent
    return current.id


def _delete_node_recursive(node: ProjectNode) -> None:
    """ノードとその子孫を再帰的に削除（コミットは呼び出し元で行う）"""
    for child in node.children.all():
        _delete_node_recursive(child)
    # 紐付くTODOのFK をNULLに
    Todo.query.filter_by(project_node_id=node.id).update({"project_node_id": None})
    db.session.delete(node)


def _parse_date(value: str):
    if value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return None


def _parse_float(value):
    if value and str(value).strip():
        try:
            return float(value)
        except ValueError:
            pass
    return None
