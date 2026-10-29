"""College academic calendar and campus event generator for realistic canteen dynamics."""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd


class AcademicCalendar:
    """Generates synthetic college calendar days, academic events, and holiday markers."""

    def __init__(self, start_date: str = "2025-01-06", num_weeks: int = 52):
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.num_weeks = num_weeks
        self.num_days = num_weeks * 7

    def generate_calendar_days(self) -> pd.DataFrame:
        """Generate day-level schedule with academic events, holidays, and day-of-week info."""
        records: List[Dict[str, Any]] = []

        for day_idx in range(self.num_days):
            current_date = self.start_date + timedelta(days=day_idx)
            iso_date = current_date.strftime("%Y-%m-%d")
            day_name = current_date.strftime("%A")
            day_num = current_date.weekday()  # Monday is 0, Sunday is 6
            week_num = (day_idx // 7) + 1

            event, is_holiday, event_multipliers = self._resolve_event(current_date, week_num, day_num)

            records.append({
                "date": iso_date,
                "week_number": week_num,
                "day_of_week": day_name,
                "day_num": day_num,
                "is_weekend": int(day_num in (5, 6)),
                "is_holiday": is_holiday,
                "campus_event": event,
                "event_multipliers": event_multipliers,
            })

        return pd.DataFrame(records)

    def _resolve_event(
        self, date: datetime, week_num: int, day_num: int
    ) -> (str, int, Dict[str, float]):
        """Determine campus event, holiday status, and category demand multipliers."""
        month = date.month
        day = date.day

        # Default standard academic day
        event = "Normal Academic Day"
        is_holiday = 0
        multipliers: Dict[str, float] = {
            "Beverages": 1.0,
            "Rice Bowl": 1.0,
            "Sandwich": 1.0,
            "Pizza": 1.0,
            "Salad": 1.0,
            "Biryani": 1.0,
            "Pasta": 1.0,
            "Starters": 1.0,
            "Other Snacks": 1.0,
            "Soup": 1.0,
            "Desert": 1.0,
            "Extras": 1.0,
            "Fish": 1.0,
            "Seafood": 1.0,
        }

        # 1. National / Public Holidays (Canteen runs on skeleton crew)
        if (month == 1 and day == 26) or (month == 8 and day == 15) or (month == 10 and day == 2):
            event = "National Holiday"
            is_holiday = 1
            for k in multipliers:
                multipliers[k] = 0.20
            return event, is_holiday, multipliers

        # 2. Annual Cultural Fest (Week 7: Feb 20-23)
        if week_num == 7 and day_num in (3, 4, 5, 6):
            event = "Annual Cultural Fest"
            is_holiday = 0
            for k in multipliers:
                multipliers[k] = 1.45
            multipliers["Pizza"] = 1.60
            multipliers["Beverages"] = 1.55
            multipliers["Other Snacks"] = 1.50
            return event, is_holiday, multipliers

        # 3. Spring Midterm Exam Week (Week 10: Mar 10-15)
        if week_num == 10 and day_num <= 5:
            event = "Midterm Exam Week"
            is_holiday = 0
            for k in multipliers:
                multipliers[k] = 0.90
            multipliers["Beverages"] = 1.35
            multipliers["Sandwich"] = 1.20
            multipliers["Other Snacks"] = 1.25
            return event, is_holiday, multipliers

        # 4. Inter-College Sports Championship (Week 13: Apr 4-6)
        if week_num == 13 and day_num in (4, 5, 6):
            event = "Inter-College Sports Fest"
            is_holiday = 0
            for k in multipliers:
                multipliers[k] = 1.30
            multipliers["Beverages"] = 1.50
            multipliers["Sandwich"] = 1.35
            return event, is_holiday, multipliers

        # 5. Spring Final Semester Exams (Weeks 16-17: Late April)
        if week_num in (16, 17) and day_num <= 5:
            event = "Final Exam Season"
            is_holiday = 0
            for k in multipliers:
                multipliers[k] = 0.85
            multipliers["Beverages"] = 1.40
            multipliers["Other Snacks"] = 1.25
            return event, is_holiday, multipliers

        # 6. Summer Vacation Break (Weeks 18 to 25: May to June)
        if 18 <= week_num <= 25:
            event = "Summer Vacation Break"
            is_holiday = 1
            for k in multipliers:
                multipliers[k] = 0.25
            return event, is_holiday, multipliers

        # 7. Monsoon Freshers Welcome Week (Week 27: Mid July)
        if week_num == 27:
            event = "Freshers Induction Week"
            is_holiday = 0
            for k in multipliers:
                multipliers[k] = 1.25
            multipliers["Pizza"] = 1.35
            multipliers["Beverages"] = 1.30
            return event, is_holiday, multipliers

        # 8. Fall Midterms (Week 37: Mid September)
        if week_num == 37 and day_num <= 5:
            event = "Fall Midterms"
            is_holiday = 0
            for k in multipliers:
                multipliers[k] = 0.90
            multipliers["Beverages"] = 1.30
            multipliers["Sandwich"] = 1.20
            return event, is_holiday, multipliers

        # 9. 48-Hour National Hackathon (Week 41: Oct 10-12)
        if week_num == 41 and day_num in (4, 5, 6):
            event = "National Hackathon Weekend"
            is_holiday = 0
            for k in multipliers:
                multipliers[k] = 1.20
            multipliers["Pizza"] = 1.65
            multipliers["Beverages"] = 1.60
            multipliers["Other Snacks"] = 1.45
            return event, is_holiday, multipliers

        # 10. Diwali & Autumn Break (Week 43: Late October)
        if week_num == 43:
            event = "Diwali Festive Break"
            is_holiday = 1
            for k in multipliers:
                multipliers[k] = 0.20
            return event, is_holiday, multipliers

        # 11. Winter Final Exams (Weeks 47-48: Late November)
        if week_num in (47, 48) and day_num <= 5:
            event = "Winter End-Semester Exams"
            is_holiday = 0
            for k in multipliers:
                multipliers[k] = 0.85
            multipliers["Beverages"] = 1.40
            multipliers["Other Snacks"] = 1.25
            return event, is_holiday, multipliers

        # 12. Winter Break (Weeks 50-52: Late December)
        if week_num >= 50:
            event = "Winter Holiday Break"
            is_holiday = 1
            for k in multipliers:
                multipliers[k] = 0.25
            return event, is_holiday, multipliers

        return event, is_holiday, multipliers
