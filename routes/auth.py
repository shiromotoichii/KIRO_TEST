from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("todos.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        # バリデーション
        error = None
        if not username or not email or not password:
            error = "すべての項目を入力してください。"
        elif len(username) > 80:
            error = "ユーザー名は80文字以内で入力してください。"
        elif password != password_confirm:
            error = "パスワードが一致しません。"
        elif len(password) < 6:
            error = "パスワードは6文字以上で入力してください。"
        elif User.query.filter_by(email=email).first():
            error = "このメールアドレスはすでに登録されています。"
        elif User.query.filter_by(username=username).first():
            error = "このユーザー名はすでに使用されています。"

        if error:
            flash(error, "danger")
            return render_template("auth/register.html",
                                   username=username, email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("アカウントを作成しました。ログインしてください。", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", username="", email="")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("todos.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("メールアドレスまたはパスワードが正しくありません。", "danger")
            return render_template("auth/login.html", email=email)

        login_user(user, remember=remember)
        # ログイン前にアクセスしようとしていたページにリダイレクト
        next_page = request.args.get("next")
        return redirect(next_page or url_for("todos.index"))

    return render_template("auth/login.html", email="")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("ログアウトしました。", "success")
    return redirect(url_for("auth.login"))
