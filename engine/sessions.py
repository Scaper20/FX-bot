"""Trading sessions in local exchange time, so daylight saving is handled by the timezone database."""
from __future__ import annotations

import pandas as pd

LONDON = "Europe/London"
NEW_YORK = "America/New_York"


def in_killzone(t_utc: pd.Timestamp) -> str:
    """'london' for 07:00-10:00 London time, 'newyork' for 08:30-11:00 New York time, else ''."""
    ld = t_utc.tz_convert(LONDON)
    if 7 <= ld.hour < 10:
        return "london"
    ny = t_utc.tz_convert(NEW_YORK)
    minutes = ny.hour * 60 + ny.minute
    if 8 * 60 + 30 <= minutes < 11 * 60:
        return "newyork"
    return ""


def session_of(t_utc: pd.Timestamp) -> str:
    """Broad session label for reporting: asia / london / newyork / late."""
    ld = t_utc.tz_convert(LONDON)
    ny = t_utc.tz_convert(NEW_YORK)
    if 8 <= ny.hour < 17:
        return "newyork" if ld.hour >= 12 else "london"
    if 7 <= ld.hour < 12:
        return "london"
    if 0 <= ld.hour < 7:
        return "asia"
    return "late"


def session_flags(t_utc: pd.Timestamp) -> str:
    """'overlap' if inside both London (07:00-16:00 London) and New York (08:00-17:00 NY) sessions,
    else 'london' or 'newyork', else '' (Asia / late)."""
    ld = t_utc.tz_convert(LONDON)
    ny = t_utc.tz_convert(NEW_YORK)
    in_ld = 7 <= ld.hour < 16
    in_ny = 8 <= ny.hour < 17
    if in_ld and in_ny:
        return "overlap"
    return "london" if in_ld else ("newyork" if in_ny else "")


def friday_late(t_utc: pd.Timestamp) -> bool:
    """Friday from 15:00 New York time: too close to the weekend close."""
    ny = t_utc.tz_convert(NEW_YORK)
    return ny.weekday() == 4 and ny.hour >= 15
