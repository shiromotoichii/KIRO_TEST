from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


# ─────────────────────────────────────────
# User
# ─────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # リレーション
    categories = db.relationship("Category", backref="owner", lazy="dynamic",
                                 cascade="all, delete-orphan")
    todos = db.relationship("Todo", backref="owner", lazy="dynamic",
                            cascade="all, delete-orphan")
    recurrence_rules = db.relationship("RecurrenceRule", backref="owner",
                                       lazy="dynamic", cascade="all, delete-orphan")
    project_nodes = db.relationship("ProjectNode", backref="owner",
                                    lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


# ─────────────────────────────────────────
# Category
# ─────────────────────────────────────────
class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), nullable=False, default="#3498db")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    todos = db.relationship("Todo", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"


# ─────────────────────────────────────────
# RecurrenceRule（繰り返しルール）
# ─────────────────────────────────────────
class RecurrenceRule(db.Model):
    __tablename__ = "recurrence_rules"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # 繰り返しパターン: daily / weekly / monthly
    pattern = db.Column(db.String(10), nullable=False)
    interval_value = db.Column(db.Integer, nullable=False, default=1)

    # weekly の場合: 0=月〜6=日
    day_of_week = db.Column(db.Integer, nullable=True)
    # monthly の場合: 1〜31
    day_of_month = db.Column(db.Integer, nullable=True)

    # 終了条件: date / count / never
    end_type = db.Column(db.String(10), nullable=False, default="never")
    end_date = db.Column(db.Date, nullable=True)
    end_count = db.Column(db.Integer, nullable=True)

    priority = db.Column(db.String(10), nullable=False, default="medium")
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    todos = db.relationship("Todo", backref="recurrence_rule", lazy="dynamic")

    def __repr__(self):
        return f"<RecurrenceRule {self.title} ({self.pattern})>"


# ─────────────────────────────────────────
# ProjectNode（プロジェクト・サブタスク階層）
# 隣接リスト: parent_id=None がルート（プロジェクト）
# ─────────────────────────────────────────
class ProjectNode(db.Model):
    __tablename__ = "project_nodes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # 自己参照（隣接リスト）
    parent_id = db.Column(db.Integer, db.ForeignKey("project_nodes.id"), nullable=True)
    children = db.relationship(
        "ProjectNode",
        backref=db.backref("parent", remote_side="ProjectNode.id"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # 進捗モード: percent（完成度平均） / numeric（数値目標）
    progress_mode = db.Column(db.String(10), nullable=False, default="percent")
    target_value = db.Column(db.Float, nullable=True)
    current_value = db.Column(db.Float, nullable=True, default=0.0)
    unit = db.Column(db.String(20), nullable=True)

    start_date = db.Column(db.Date, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    todos = db.relationship("Todo", backref="project_node", lazy="dynamic")

    @property
    def is_root(self) -> bool:
        """ルートノード（＝プロジェクト）かどうか"""
        return self.parent_id is None

    def __repr__(self):
        return f"<ProjectNode {self.title}>"


# ─────────────────────────────────────────
# Todo
# ─────────────────────────────────────────
class Todo(db.Model):
    __tablename__ = "todos"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_completed = db.Column(db.Boolean, nullable=False, default=False)

    # 優先度: high / medium / low
    priority = db.Column(db.String(10), nullable=False, default="medium")
    due_date = db.Column(db.Date, nullable=True)

    # 完成度: 0〜100
    progress = db.Column(db.Integer, nullable=False, default=0)

    # 外部キー
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    recurrence_rule_id = db.Column(db.Integer,
                                   db.ForeignKey("recurrence_rules.id"), nullable=True)
    recurrence_index = db.Column(db.Integer, nullable=True)
    project_node_id = db.Column(db.Integer,
                                db.ForeignKey("project_nodes.id"), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    @property
    def is_overdue(self) -> bool:
        """締め切りを過ぎているか（未完了のみ）"""
        if self.due_date and not self.is_completed:
            return self.due_date < date.today()
        return False

    @property
    def is_due_today(self) -> bool:
        """本日が締め切りか（未完了のみ）"""
        if self.due_date and not self.is_completed:
            return self.due_date == date.today()
        return False

    @property
    def progress_level(self) -> int:
        """完成度に応じたレベル（1〜5）をCSSクラス用に返す"""
        if self.progress == 0:
            return 0
        elif self.progress < 25:
            return 1
        elif self.progress < 50:
            return 2
        elif self.progress < 75:
            return 3
        elif self.progress < 100:
            return 4
        else:
            return 5

    def __repr__(self):
        return f"<Todo {self.title}>"
