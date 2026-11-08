"""
進捗計算・予測ロジック
  calc_node_progress(node)  → float（0〜100）
  calc_forecast(node, today) → dict
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import ProjectNode


def calc_node_progress(node: "ProjectNode") -> float:
    """
    ノードの進捗（0〜100）を再帰的に計算する。

    - 子ノードが存在する場合: 子ノードの進捗の平均
    - 子ノードがない場合:
        percent モード → 紐付く Todo の progress の平均
        numeric モード → current_value / target_value * 100
    """
    children = node.children.all()

    if children:
        child_progresses = [calc_node_progress(c) for c in children]
        return sum(child_progresses) / len(child_progresses)

    # 末端ノード
    if node.progress_mode == "numeric":
        if node.target_value and node.target_value > 0:
            cv = node.current_value or 0.0
            return min(100.0, cv / node.target_value * 100)
        return 0.0

    # percent モード: 紐付く Todo の progress 平均
    todos = node.todos.all()
    if not todos:
        return 0.0
    return sum(t.progress for t in todos) / len(todos)


def calc_forecast(node: "ProjectNode", today: date) -> dict:
    """
    進捗速度と完了予測日を計算する。

    戻り値:
      {
        "progress":       float,         # 現在の進捗%
        "speed_per_day":  float,         # 1日あたりの進捗速度
        "forecast_date":  date | None,   # 完了予測日
        "overrun_days":   int,           # 超過日数（正=超過）
        "status":         str,           # on_track / at_risk / overdue / no_progress
        "label":          str,           # 表示用テキスト
      }
    """
    progress = calc_node_progress(node)
    result = {
        "progress": progress,
        "speed_per_day": 0.0,
        "forecast_date": None,
        "overrun_days": 0,
        "status": "no_progress",
        "label": "進捗なし",
    }

    # 開始日・期限日がない場合は予測不能
    if not node.start_date or not node.due_date:
        result["status"] = "no_progress"
        result["label"] = "期限未設定"
        return result

    # 経過日数（最低1日）
    elapsed = max(1, (today - node.start_date).days)
    speed = progress / elapsed  # %/日
    result["speed_per_day"] = round(speed, 4)

    # 既に完了（100%）
    if progress >= 100:
        result["status"] = "on_track"
        result["label"] = "完了"
        return result

    # 進捗が0
    if speed == 0:
        # 期限超過かどうかだけ判定
        if today > node.due_date:
            overrun = (today - node.due_date).days
            result["overrun_days"] = overrun
            result["status"] = "overdue"
            result["label"] = f"+{overrun}日超過"
        else:
            result["status"] = "no_progress"
            result["label"] = "進捗なし"
        return result

    # 完了予測日
    remaining = 100.0 - progress
    days_needed = remaining / speed
    forecast_date = today + timedelta(days=int(days_needed))
    result["forecast_date"] = forecast_date

    # ステータス判定
    if today > node.due_date:
        # すでに期限超過
        overrun = (today - node.due_date).days
        result["overrun_days"] = overrun
        result["status"] = "overdue"
        result["label"] = f"+{overrun}日超過"
    elif forecast_date > node.due_date:
        # 期限内だが完了予測日がオーバー
        overrun = (forecast_date - node.due_date).days
        result["overrun_days"] = overrun
        result["status"] = "at_risk"
        result["label"] = f"予測 +{overrun}日"
    else:
        result["status"] = "on_track"
        result["label"] = f"予測完了: {forecast_date.strftime('%m/%d')}"

    return result


def build_progress_bar_segments(forecast: dict) -> list[dict]:
    """
    3色合成プログレスバー用のセグメントリストを返す。

    各セグメント: {"width": float（%）, "color_class": str, "label": str}
    """
    progress = forecast["progress"]
    status = forecast["status"]

    if status == "overdue":
        # 青（達成分）+ 赤（超過表示: デュー日超過分を比率で表現）
        overrun_days = forecast["overrun_days"]
        # 超過割合: 超過日数 / (経過日数 + 超過日数) ※ 最大20%に制限して見やすくする
        overrun_ratio = min(20.0, overrun_days * 1.5)
        blue_width = max(0, 100 - overrun_ratio)
        return [
            {"width": blue_width * progress / 100,
             "color_class": "progress-bar-blue", "label": f"{progress:.0f}%"},
            {"width": overrun_ratio,
             "color_class": "progress-bar-overdue", "label": f"+{overrun_days}日"},
        ]

    elif status == "at_risk":
        overrun_days = forecast["overrun_days"]
        overrun_ratio = min(20.0, overrun_days * 1.5)
        blue_width = 100 - overrun_ratio
        remaining_width = blue_width * (100 - progress) / 100
        achieved_width = blue_width * progress / 100
        return [
            {"width": achieved_width,
             "color_class": "progress-bar-blue", "label": f"{progress:.0f}%"},
            {"width": remaining_width,
             "color_class": "progress-bar-remaining", "label": ""},
            {"width": overrun_ratio,
             "color_class": "progress-bar-atrisk", "label": f"予測+{overrun_days}日"},
        ]

    elif status == "on_track":
        return [
            {"width": progress,
             "color_class": "progress-bar-blue", "label": f"{progress:.0f}%"},
            {"width": 100 - progress,
             "color_class": "progress-bar-remaining", "label": ""},
        ]

    else:  # no_progress
        return [
            {"width": 100,
             "color_class": "progress-bar-remaining", "label": "進捗なし"},
        ]
