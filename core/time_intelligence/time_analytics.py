"""
Time Intelligence Analytics
===========================
Professional time-based analytics like Power BI Time Intelligence.
YoY, MoM, QoQ, YTD comparisons and trend analysis.
"""

from datetime import date, timedelta
from typing import Optional


class TimeAnalytics:
    """Time-based analytics - comparisons and trend calculations."""

    def year_over_year(self, current_value: float, last_year_value: float) -> dict:
        """Year-over-Year (YoY) comparison."""
        diff = current_value - last_year_value
        pct = (diff / last_year_value * 100) if last_year_value else 0
        return {
            "current": current_value,
            "previous": last_year_value,
            "difference": diff,
            "percentage": round(pct, 2),
            "trend": self._get_trend(diff),
            "label": "مقارنة سنوية (YoY)",
        }

    def month_over_month(self, current_value: float, last_month_value: float) -> dict:
        """Month-over-Month (MoM) comparison."""
        diff = current_value - last_month_value
        pct = (diff / last_month_value * 100) if last_month_value else 0
        return {
            "current": current_value,
            "previous": last_month_value,
            "difference": diff,
            "percentage": round(pct, 2),
            "trend": self._get_trend(diff),
            "label": "مقارنة شهرية (MoM)",
        }

    def quarter_over_quarter(self, current_value: float, last_quarter_value: float) -> dict:
        """Quarter-over-Quarter (QoQ) comparison."""
        diff = current_value - last_quarter_value
        pct = (diff / last_quarter_value * 100) if last_quarter_value else 0
        return {
            "current": current_value,
            "previous": last_quarter_value,
            "difference": diff,
            "percentage": round(pct, 2),
            "trend": self._get_trend(diff),
            "label": "مقارنة ربع سنوية (QoQ)",
        }

    def year_to_date(self, values_by_month: list) -> dict:
        """Year-to-Date (YTD) aggregation."""
        current_month = date.today().month
        ytd_values = values_by_month[:current_month]
        total = sum(ytd_values)
        avg = total / len(ytd_values) if ytd_values else 0
        return {
            "total": total,
            "average": round(avg, 2),
            "months_included": len(ytd_values),
            "by_month": ytd_values,
            "label": f"من أول السنة حتى الآن (YTD - {current_month} أشهر)",
        }

    def same_period_last_year(self, current_date: Optional[date] = None) -> dict:
        """Get the same period from last year for comparison."""
        if current_date is None:
            current_date = date.today()

        last_year = date(
            current_date.year - 1,
            current_date.month,
            min(current_date.day, 28)
        )

        return {
            "current_period": current_date.isoformat(),
            "last_year_period": last_year.isoformat(),
            "label": f"نفس الفترة {last_year.year}",
        }

    def rolling_period(self, months: int = 12) -> dict:
        """Rolling N months period."""
        today = date.today()
        start = today - timedelta(days=months * 30)
        return {
            "start": start.isoformat(),
            "end": today.isoformat(),
            "months": months,
            "label": f"آخر {months} شهر",
        }

    def growth_rate(self, values: list) -> dict:
        """Calculate growth rate from a series of values."""
        if len(values) < 2:
            return {"rate": 0, "trend": "flat", "label": "لا توجد بيانات كافية"}

        first = values[0]
        last = values[-1]

        if first == 0:
            rate = 100.0 if last > 0 else 0
        else:
            rate = ((last - first) / abs(first)) * 100

        return {
            "rate": round(rate, 2),
            "first_value": first,
            "last_value": last,
            "periods": len(values),
            "trend": self._get_trend(last - first),
            "label": f"معدل النمو ({len(values)} فترات)",
        }

    def moving_average(self, values: list, window: int = 3) -> list:
        """Calculate moving average for a series."""
        if len(values) < window:
            return values

        result = []
        for i in range(len(values)):
            if i < window - 1:
                result.append(round(sum(values[:i + 1]) / (i + 1), 2))
            else:
                window_values = values[i - window + 1:i + 1]
                result.append(round(sum(window_values) / window, 2))

        return result

    def compare_periods(
        self,
        current_values: list,
        previous_values: list,
        period_labels: Optional[list] = None,
    ) -> list:
        """Compare two periods element by element."""
        comparisons = []
        max_len = max(len(current_values), len(previous_values))

        for i in range(max_len):
            current = current_values[i] if i < len(current_values) else 0
            previous = previous_values[i] if i < len(previous_values) else 0
            diff = current - previous
            pct = (diff / previous * 100) if previous else 0

            label = period_labels[i] if period_labels and i < len(period_labels) else f"فترة {i + 1}"

            comparisons.append({
                "label": label,
                "current": current,
                "previous": previous,
                "difference": diff,
                "percentage": round(pct, 2),
                "trend": self._get_trend(diff),
            })

        return comparisons

    def format_comparison(self, comparison: dict) -> str:
        """Format a comparison result as Arabic text."""
        trend_icon = {
            "up": "📈",
            "down": "📉",
            "flat": "➡️",
        }

        icon = trend_icon.get(comparison.get("trend", "flat"), "➡️")
        pct = comparison.get("percentage", 0)

        if pct > 0:
            return f"{icon} ارتفاع بنسبة {abs(pct):.1f}%"
        elif pct < 0:
            return f"{icon} انخفاض بنسبة {abs(pct):.1f}%"
        else:
            return f"{icon} لا تغيير"

    @staticmethod
    def _get_trend(diff: float) -> str:
        """Determine trend direction."""
        if diff > 0:
            return "up"
        elif diff < 0:
            return "down"
        return "flat"


# Singleton
_analytics: Optional[TimeAnalytics] = None


def get_time_analytics() -> TimeAnalytics:
    """Get singleton TimeAnalytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = TimeAnalytics()
    return _analytics
