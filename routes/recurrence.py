from datetime import date, timedelta
import calendar
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import RecurrenceRule, Todo, Category

recurrence_bp = Blueprint("recurrence", __name__, url_prefix="/recurrence")


@recurrence_bp.route("/")
@login_required
def index():
    rules = (RecurrenceRule.query
             .filter_by(user_id=current_user.id)
             .order_by(RecurrenceRule.created_at.desc())
             .all())
    rule_data = []
    for r in rules:
        count = Todo.query.filter_by(recurrence_rule_id=r.id).count()
        rule_data.append({"rule": r, "todo_count": count})
    return render_template("recurrence.html", rule_data=rule_data)


@recurrence_bp.route("/new", methods=["POST"])
@login_required
def new():
    title = request.form.get("title", "").strip()
    if not title:
        flash("タイトルを入力してください。", "danger")
        return redirect(url_for("recurrence.index"))

    pattern = request.form.get("pattern", "daily")
    interval_value = max(1, int(request.form.get("interval_value", 1) or 1))
    day_of_week = _parse_int(request.form.get("day_of_week"))
    day_of_month = _parse_int(request.form.get("day_of_month"))
    end_type = request.form.get("end_type", "never")
    end_date = _parse_date(request.form.get("end_date", ""))
    end_count = _parse_int(request.form.get("end_count"))
    priority = request.form.get("priority", "medium")
    category_id = _parse_int(request.form.get("category_id"))

    rule = RecurrenceRule(
        user_id=current_user.id,
        title=title,
        description=request.form.get("description", "").strip() or None,
        pattern=pattern,
        interval_value=interval_value,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
        end_type=end_type,
        end_date=end_date,
        end_count=end_count,
        priority=priority,
        category_id=category_id,
    )
    db.session.add(rule)
    db.session.flush()  # IDを確定させる

    # 最初の1件を生成（今日の日付で）
    first_todo = Todo(
        user_id=current_user.id,
        title=title,
        description=rule.description,
        priority=priority,
        category_id=category_id,
        recurrence_rule_id=rule.id,
        recurrence_index=0,
        due_date=date.today(),
    )
    db.session.add(first_todo)
    db.session.commit()
    flash(f"繰り返しルール「{title}」を作成しました。", "success")
    return redirect(url_for("recurrence.index"))


@recurrence_bp.route("/<int:rule_id>/generate", methods=["POST"])
@login_required
def generate(rule_id):
    """今月分のタスクを一括生成する"""
    rule = RecurrenceRule.query.filter_by(
        id=rule_id, user_id=current_user.id
    ).first_or_404()

    today = date.today()
    # 当月の開始・終了日
    month_start = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    month_end = today.replace(day=last_day)

    # 既存の due_date を取得してセット化（重複防止）
    existing_dates = set(
        row.due_date for row in
        Todo.query.filter_by(recurrence_rule_id=rule.id)
        .with_entities(Todo.due_date).all()
        if row.due_date
    )

    # 現在の最大 recurrence_index
    max_idx_row = db.session.query(
        db.func.max(Todo.recurrence_index)
    ).filter_by(recurrence_rule_id=rule.id).scalar()
    idx = (max_idx_row or 0) + 1

    target_dates = _calc_target_dates(rule, month_start, month_end)

    created = 0
    for d in target_dates:
        # 終了条件チェック
        if rule.end_type == "date" and rule.end_date and d > rule.end_date:
            break
        if rule.end_type == "count" and rule.end_count:
            total = Todo.query.filter_by(recurrence_rule_id=rule.id).count()
            if total >= rule.end_count:
                break

        if d in existing_dates:
            continue

        todo = Todo(
            user_id=current_user.id,
            title=rule.title,
            description=rule.description,
            priority=rule.priority,
            category_id=rule.category_id,
            recurrence_rule_id=rule.id,
            recurrence_index=idx,
            due_date=d,
        )
        db.session.add(todo)
        existing_dates.add(d)
        idx += 1
        created += 1

    db.session.commit()
    if created:
        flash(f"今月分 {created} 件のタスクを生成しました。", "success")
    else:
        flash("今月分はすでに生成済みか、終了条件に達しています。", "info")
    return redirect(url_for("recurrence.index"))


@recurrence_bp.route("/<int:rule_id>/delete", methods=["POST"])
@login_required
def delete(rule_id):
    rule = RecurrenceRule.query.filter_by(
        id=rule_id, user_id=current_user.id
    ).first_or_404()
    delete_future = request.form.get("delete_future") == "1"

    if delete_future:
        today = date.today()
        # 未来の未完了タスクを一括削除
        (Todo.query
         .filter_by(recurrence_rule_id=rule.id, is_completed=False)
         .filter(Todo.due_date >= today)
         .delete())

    # ルール自体を削除（残ったTODOのFK はNULLに）
    Todo.query.filter_by(recurrence_rule_id=rule.id).update(
        {"recurrence_rule_id": None}
    )
    db.session.delete(rule)
    db.session.commit()
    flash(f"繰り返しルール「{rule.title}」を削除しました。", "success")
    return redirect(url_for("recurrence.index"))


# ── ユーティリティ ──────────────────────────────────────
def _calc_target_dates(rule: RecurrenceRule,
                       start: date, end: date) -> list[date]:
    """ルールに従って start〜end 内の対象日付リストを返す"""
    dates = []
    current = start

    if rule.pattern == "daily":
        while current <= end:
            dates.append(current)
            current += timedelta(days=rule.interval_value)

    elif rule.pattern == "weekly":
        # day_of_week: 0=月〜6=日（Python の weekday() と一致）
        target_dow = rule.day_of_week if rule.day_of_week is not None else 0
        # start から最初の対象曜日を探す
        days_ahead = (target_dow - start.weekday()) % 7
        current = start + timedelta(days=days_ahead)
        while current <= end:
            dates.append(current)
            current += timedelta(weeks=rule.interval_value)

    elif rule.pattern == "monthly":
        target_dom = rule.day_of_month if rule.day_of_month else 1
        # 当月の対象日（月末を超える場合は月末）
        last_day = calendar.monthrange(start.year, start.month)[1]
        day = min(target_dom, last_day)
        candidate = start.replace(day=day)
        if candidate < start:
            # 翌月
            year = start.year + (start.month // 12)
            month = (start.month % 12) + 1
            last_day2 = calendar.monthrange(year, month)[1]
            candidate = date(year, month, min(target_dom, last_day2))
        if candidate <= end:
            dates.append(candidate)

    return dates


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
