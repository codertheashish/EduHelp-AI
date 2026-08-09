"""
planner.py
Builds a day-by-day study timetable given an exam date, a list of
subjects (optionally weighted by difficulty/priority), and daily
available hours.
"""

from datetime import date, timedelta


def build_plan(exam_date_str, subjects, hours_per_day):
    """
    exam_date_str: 'YYYY-MM-DD'
    subjects: list of dicts like {"name": "DSA", "priority": 3}
              higher priority = more hours allocated
    hours_per_day: float, hours available per study day

    Returns: list of {"day": 1, "date": "YYYY-MM-DD", "sessions": [{"subject": .., "hours": ..}]}
    """
    exam_date = date.fromisoformat(exam_date_str)
    today = date.today()
    days_left = (exam_date - today).days

    if days_left <= 0:
        raise ValueError("Exam date must be in the future.")

    total_priority = sum(s.get("priority", 1) for s in subjects) or 1
    plan = []

    for day_offset in range(days_left):
        current_day = today + timedelta(days=day_offset + 1)
        sessions = []
        remaining_hours = hours_per_day

        for i, subj in enumerate(subjects):
            share = subj.get("priority", 1) / total_priority
            hours = round(hours_per_day * share, 1)
            if i == len(subjects) - 1:
                hours = round(remaining_hours, 1)  # avoid rounding drift on last subject
            remaining_hours -= hours
            if hours > 0:
                sessions.append({"subject": subj["name"], "hours": hours})

        plan.append({
            "day": day_offset + 1,
            "date": current_day.isoformat(),
            "sessions": sessions,
        })

    return plan
