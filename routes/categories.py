from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Category, Todo

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")


@categories_bp.route("/")
@login_required
def index():
    cats = (Category.query
            .filter_by(user_id=current_user.id)
            .order_by(Category.name)
            .all())
    # 各カテゴリのTODO件数を付加
    cat_data = []
    for c in cats:
        count = Todo.query.filter_by(category_id=c.id).count()
        cat_data.append({"category": c, "todo_count": count})
    return render_template("categories.html", cat_data=cat_data)


@categories_bp.route("/new", methods=["POST"])
@login_required
def new():
    name = request.form.get("name", "").strip()
    color = request.form.get("color", "#3498db")

    if not name:
        flash("カテゴリ名を入力してください。", "danger")
        return redirect(url_for("categories.index"))
    if len(name) > 50:
        flash("カテゴリ名は50文字以内で入力してください。", "danger")
        return redirect(url_for("categories.index"))

    cat = Category(name=name, color=color, user_id=current_user.id)
    db.session.add(cat)
    db.session.commit()
    flash(f"カテゴリ「{name}」を作成しました。", "success")
    return redirect(url_for("categories.index"))


@categories_bp.route("/<int:cat_id>/edit", methods=["POST"])
@login_required
def edit(cat_id):
    cat = Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404()
    name = request.form.get("name", "").strip()
    color = request.form.get("color", cat.color)

    if not name:
        flash("カテゴリ名を入力してください。", "danger")
        return redirect(url_for("categories.index"))

    cat.name = name
    cat.color = color
    db.session.commit()
    flash("カテゴリを更新しました。", "success")
    return redirect(url_for("categories.index"))


@categories_bp.route("/<int:cat_id>/delete", methods=["POST"])
@login_required
def delete(cat_id):
    cat = Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404()
    name = cat.name

    # 紐付くTODOのカテゴリをNULLに
    Todo.query.filter_by(category_id=cat_id).update({"category_id": None})
    db.session.delete(cat)
    db.session.commit()
    flash(f"カテゴリ「{name}」を削除しました。", "success")
    return redirect(url_for("categories.index"))
