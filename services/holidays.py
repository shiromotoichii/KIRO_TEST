"""
日本の祝日情報を管理するモジュール
キャッシュした祝日リストを使用
"""

from datetime import date
from typing import Dict, Optional

# キャッシュ用の祝日データ（フォールバック）
CACHED_HOLIDAYS = {
    # 2026年
    "2026-01-01": "元日",
    "2026-01-12": "成人の日",
    "2026-02-11": "建国記念の日",
    "2026-02-23": "天皇誕生日",
    "2026-03-20": "春分の日",
    "2026-04-29": "昭和の日",
    "2026-05-03": "憲法記念日",
    "2026-05-04": "みどりの日",
    "2026-05-05": "こどもの日",
    "2026-05-06": "振替休日",
    "2026-07-20": "海の日",
    "2026-08-10": "山の日",
    "2026-09-21": "敬老の日",
    "2026-09-22": "秋分の日",
    "2026-10-12": "スポーツの日",
    "2026-11-03": "文化の日",
    "2026-11-23": "勤労感謝の日",
    # 2027年
    "2027-01-01": "元日",
    "2027-01-11": "成人の日",
    "2027-02-11": "建国記念の日",
    "2027-02-23": "天皇誕生日",
    "2027-03-21": "春分の日",
    "2027-04-29": "昭和の日",
    "2027-05-03": "憲法記念日",
    "2027-05-04": "みどりの日",
    "2027-05-05": "こどもの日",
    "2027-07-19": "海の日",
    "2027-08-11": "山の日",
    "2027-09-20": "敬老の日",
    "2027-09-23": "秋分の日",
    "2027-10-11": "スポーツの日",
    "2027-11-03": "文化の日",
    "2027-11-23": "勤労感謝の日",
    # 2028年
    "2028-01-01": "元日",
    "2028-01-10": "成人の日",
    "2028-02-11": "建国記念の日",
    "2028-02-23": "天皇誕生日",
    "2028-03-20": "春分の日",
    "2028-04-29": "昭和の日",
    "2028-05-03": "憲法記念日",
    "2028-05-04": "みどりの日",
    "2028-05-05": "こどもの日",
    "2028-07-17": "海の日",
    "2028-08-11": "山の日",
    "2028-09-18": "敬老の日",
    "2028-09-22": "秋分の日",
    "2028-10-09": "スポーツの日",
    "2028-11-03": "文化の日",
    "2028-11-23": "勤労感謝の日",
}


def get_holidays_from_api() -> Optional[Dict[str, str]]:
    """
    外部APIから日本の祝日情報を取得
    Nager.Date API を使用
    現在は無効化してキャッシュのみを使用
    """
    return None
    # try:
    #     # 複数年分の祝日を取得（2024-2030年）
    #     all_holidays = {}
    #     for year in range(2024, 2031):
    #         try:
    #             response = requests.get(
    #                 f"https://date.nager.at/api/v3/PublicHolidays/{year}/JP",
    #                 timeout=5
    #             )
    #             if response.status_code == 200:
    #                 holidays_data = response.json()
    #                 for holiday in holidays_data:
    #                     date_str = holiday.get("date")
    #                     name = holiday.get("name", "祝日")
    #                     if date_str:
    #                         all_holidays[date_str] = name
    #         except Exception as e:
    #             print(f"Error fetching holidays for {year}: {e}")
    #             continue
    #     
    #     return all_holidays if all_holidays else None
    # except Exception as e:
    #     print(f"Error getting holidays from API: {e}")
    #     return None


def get_all_holidays() -> Dict[str, str]:
    """
    祝日情報を取得（API優先、失敗時はキャッシュ使用）
    """
    # まずAPIから取得を試みる
    api_holidays = get_holidays_from_api()
    if api_holidays:
        return api_holidays
    
    # APIが失敗した場合はキャッシュを使用
    print("Using cached holidays data")
    return CACHED_HOLIDAYS


def is_holiday(d: date) -> bool:
    """指定された日付が祝日か判定"""
    holidays = get_all_holidays()
    return d.isoformat() in holidays


def is_weekend(d: date) -> bool:
    """土曜日または日曜日か判定"""
    return d.weekday() >= 5  # 5=土, 6=日
