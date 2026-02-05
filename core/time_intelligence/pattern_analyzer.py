"""
Pattern Analyzer
================
Analyzes time-based patterns from historical data.
"""

from datetime import date, datetime, timedelta
from typing import Optional


class PatternAnalyzer:
    """Analyzes patterns in time-series data for insights."""

    def detect_seasonality(self, values_by_month: list) -> dict:
        """Detect seasonal patterns in monthly data."""
        if len(values_by_month) < 12:
            return {"has_seasonality": False, "message": "بيانات غير كافية (أقل من سنة)"}

        avg = sum(values_by_month) / len(values_by_month)
        if avg == 0:
            return {"has_seasonality": False, "message": "القيم صفرية"}

        # Find months significantly above/below average
        from .system_time import MONTHS_AR

        high_months = []
        low_months = []
        threshold = 0.2  # 20% deviation

        for i, val in enumerate(values_by_month[:12]):
            deviation = (val - avg) / avg if avg else 0
            month_name = MONTHS_AR[i] if i < 12 else f"شهر {i + 1}"

            if deviation > threshold:
                high_months.append({"month": i + 1, "name": month_name, "deviation": round(deviation * 100, 1)})
            elif deviation < -threshold:
                low_months.append({"month": i + 1, "name": month_name, "deviation": round(deviation * 100, 1)})

        has_seasonality = len(high_months) > 0 or len(low_months) > 0

        return {
            "has_seasonality": has_seasonality,
            "average": round(avg, 2),
            "high_months": high_months,
            "low_months": low_months,
            "message": self._format_seasonality_message(high_months, low_months) if has_seasonality else "لا توجد أنماط موسمية واضحة",
        }

    def detect_trend(self, values: list) -> dict:
        """Detect overall trend direction in a series."""
        if len(values) < 3:
            return {"trend": "unknown", "message": "بيانات غير كافية"}

        # Simple linear trend detection
        n = len(values)
        x_sum = n * (n - 1) / 2
        y_sum = sum(values)
        xy_sum = sum(i * v for i, v in enumerate(values))
        x2_sum = n * (n - 1) * (2 * n - 1) / 6

        denominator = n * x2_sum - x_sum ** 2
        if denominator == 0:
            slope = 0
        else:
            slope = (n * xy_sum - x_sum * y_sum) / denominator

        avg_value = y_sum / n if n else 0
        slope_pct = (slope / avg_value * 100) if avg_value else 0

        if slope_pct > 5:
            trend = "increasing"
            message = f"اتجاه صاعد بمعدل {abs(slope_pct):.1f}% لكل فترة"
        elif slope_pct < -5:
            trend = "decreasing"
            message = f"اتجاه هابط بمعدل {abs(slope_pct):.1f}% لكل فترة"
        else:
            trend = "stable"
            message = "مستقر - لا تغيير ملحوظ"

        return {
            "trend": trend,
            "slope": round(slope, 4),
            "slope_percentage": round(slope_pct, 2),
            "message": message,
        }

    def find_anomalies(self, values: list, threshold: float = 2.0) -> list:
        """Find anomalous values using standard deviation."""
        if len(values) < 5:
            return []

        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return []

        anomalies = []
        for i, val in enumerate(values):
            z_score = abs(val - avg) / std_dev
            if z_score > threshold:
                anomalies.append({
                    "index": i,
                    "value": val,
                    "z_score": round(z_score, 2),
                    "direction": "high" if val > avg else "low",
                    "deviation_pct": round((val - avg) / avg * 100, 1) if avg else 0,
                })

        return anomalies

    def weekly_pattern(self, data_by_day: dict) -> dict:
        """Analyze weekly patterns from daily data."""
        from .system_time import DAYS_AR

        day_averages = {}
        for day_num in range(7):
            day_data = data_by_day.get(day_num, [])
            if day_data:
                day_averages[day_num] = {
                    "day_name": DAYS_AR[day_num],
                    "average": round(sum(day_data) / len(day_data), 2),
                    "count": len(day_data),
                }

        if not day_averages:
            return {"pattern": "none", "message": "لا توجد بيانات"}

        best_day = max(day_averages.items(), key=lambda x: x[1]["average"])
        worst_day = min(day_averages.items(), key=lambda x: x[1]["average"])

        return {
            "pattern": "weekly",
            "by_day": day_averages,
            "best_day": {"day": best_day[0], "name": best_day[1]["day_name"], "average": best_day[1]["average"]},
            "worst_day": {"day": worst_day[0], "name": worst_day[1]["day_name"], "average": worst_day[1]["average"]},
        }

    @staticmethod
    def _format_seasonality_message(high_months: list, low_months: list) -> str:
        """Format seasonality findings as Arabic message."""
        parts = []
        if high_months:
            names = "، ".join(m["name"] for m in high_months[:3])
            parts.append(f"أعلى في: {names}")
        if low_months:
            names = "، ".join(m["name"] for m in low_months[:3])
            parts.append(f"أقل في: {names}")
        return " | ".join(parts)


# Singleton
_analyzer: Optional[PatternAnalyzer] = None


def get_pattern_analyzer() -> PatternAnalyzer:
    """Get singleton PatternAnalyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = PatternAnalyzer()
    return _analyzer
