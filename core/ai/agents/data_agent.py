"""
Data Agent
==========
AI agent specialized in analyzing employee and business data.
Detects anomalies, generates insights, and provides recommendations.
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import threading

from ..ollama_client import get_ollama_client
from ..prompts import SYSTEM_PROMPTS
from core.logging import app_logger


class InsightType(Enum):
    """Types of insights."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class AnomalyType(Enum):
    """Types of data anomalies."""
    SALARY_HIGH = "salary_high"
    SALARY_LOW = "salary_low"
    MISSING_DATA = "missing_data"
    CONTRACT_EXPIRING = "contract_expiring"
    DUPLICATE = "duplicate"
    INVALID_DATA = "invalid_data"


@dataclass
class Insight:
    """Represents an AI-generated insight."""
    title: str
    description: str
    type: InsightType
    data: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Anomaly:
    """Represents a detected data anomaly."""
    type: AnomalyType
    severity: str  # "high", "medium", "low"
    description: str
    affected_records: List[int]
    details: Optional[Dict[str, Any]] = None


class DataAgent:
    """
    AI Agent for data analysis.

    Features:
    - Employee data analysis
    - Salary analysis and anomaly detection
    - Pattern recognition
    - Insight generation
    - Natural language queries on data

    Usage:
        agent = DataAgent()

        # Analyze employees
        insights = agent.analyze_employees(employees_data)

        # Find salary anomalies
        anomalies = agent.analyze_salaries(salaries_data)

        # Ask questions about data
        answer = agent.query("كم عدد الموظفين في قسم المبيعات؟", data)
    """

    _instance: Optional['DataAgent'] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._client = get_ollama_client()
        self._system_prompt = SYSTEM_PROMPTS.get("analyst")
        self._initialized = True

    @property
    def is_available(self) -> bool:
        """Check if agent is available."""
        return self._client.is_available()

    def _format_data_for_ai(self, data: List[Dict], max_records: int = 50) -> str:
        """Format data for AI analysis."""
        # Limit records to avoid token limits
        sample = data[:max_records]

        # Convert to readable format
        lines = []
        for i, record in enumerate(sample, 1):
            record_str = ", ".join(f"{k}: {v}" for k, v in record.items() if v is not None)
            lines.append(f"{i}. {record_str}")

        formatted = "\n".join(lines)

        if len(data) > max_records:
            formatted += f"\n\n... و {len(data) - max_records} سجل آخر"

        return formatted

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Try to parse structured data from AI response."""
        # Try to find JSON in response
        try:
            # Look for JSON block
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
            elif "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        return {"raw_response": response}

    def analyze_employees(
        self,
        employees: List[Dict],
        focus: Optional[str] = None
    ) -> List[Insight]:
        """
        Analyze employee data and generate insights.

        Args:
            employees: List of employee records
            focus: Specific area to focus on (optional)

        Returns:
            List of insights
        """
        if not self.is_available or not employees:
            return []

        insights = []

        # Prepare data summary
        formatted_data = self._format_data_for_ai(employees)

        prompt = f"""حلل بيانات الموظفين التالية وقدم رؤى مفيدة:

{formatted_data}

المطلوب:
1. ملخص عام للبيانات (عدد، توزيع، إلخ)
2. ملاحظات مهمة أو أنماط
3. توصيات للتحسين إن وجدت

{"ركز بشكل خاص على: " + focus if focus else ""}

قدم الإجابة بشكل منظم ومختصر."""

        try:
            response = self._client.chat(
                message=prompt,
                system=self._system_prompt,
                temperature=0.3
            )

            if response:
                insights.append(Insight(
                    title="تحليل بيانات الموظفين",
                    description=response,
                    type=InsightType.INFO,
                    data={"total_employees": len(employees)}
                ))

        except Exception as e:
            app_logger.error(f"Employee analysis error: {e}")

        return insights

    def analyze_salaries(
        self,
        salaries: List[Dict],
        threshold_high: float = 2.0,
        threshold_low: float = 0.5
    ) -> Tuple[List[Anomaly], List[Insight]]:
        """
        Analyze salary data for anomalies.

        Args:
            salaries: List of salary records with 'employee_id', 'salary', 'department', etc.
            threshold_high: Standard deviations above mean to flag as high
            threshold_low: Standard deviations below mean to flag as low

        Returns:
            Tuple of (anomalies, insights)
        """
        if not salaries:
            return [], []

        anomalies = []
        insights = []

        # Basic statistical analysis
        salary_values = [s.get('salary', 0) for s in salaries if s.get('salary')]
        if not salary_values:
            return [], []

        avg_salary = sum(salary_values) / len(salary_values)
        min_salary = min(salary_values)
        max_salary = max(salary_values)

        # Calculate standard deviation
        variance = sum((x - avg_salary) ** 2 for x in salary_values) / len(salary_values)
        std_dev = variance ** 0.5

        # Find anomalies
        high_threshold = avg_salary + (threshold_high * std_dev)
        low_threshold = avg_salary - (threshold_low * std_dev)

        high_salaries = []
        low_salaries = []

        for record in salaries:
            salary = record.get('salary', 0)
            emp_id = record.get('employee_id') or record.get('id')

            if salary and salary > high_threshold:
                high_salaries.append(emp_id)
            elif salary and salary < low_threshold and salary > 0:
                low_salaries.append(emp_id)

        if high_salaries:
            anomalies.append(Anomaly(
                type=AnomalyType.SALARY_HIGH,
                severity="medium",
                description=f"رواتب أعلى من المتوسط بشكل ملحوظ ({len(high_salaries)} موظف)",
                affected_records=high_salaries,
                details={"threshold": high_threshold, "average": avg_salary}
            ))

        if low_salaries:
            anomalies.append(Anomaly(
                type=AnomalyType.SALARY_LOW,
                severity="high",
                description=f"رواتب أقل من المتوسط بشكل ملحوظ ({len(low_salaries)} موظف)",
                affected_records=low_salaries,
                details={"threshold": low_threshold, "average": avg_salary}
            ))

        # Generate insight
        insights.append(Insight(
            title="تحليل الرواتب",
            description=f"متوسط الراتب: {avg_salary:,.0f} | أقل راتب: {min_salary:,.0f} | أعلى راتب: {max_salary:,.0f}",
            type=InsightType.INFO,
            data={
                "average": avg_salary,
                "min": min_salary,
                "max": max_salary,
                "std_dev": std_dev,
                "count": len(salary_values)
            }
        ))

        return anomalies, insights

    def find_missing_data(
        self,
        records: List[Dict],
        required_fields: List[str]
    ) -> List[Anomaly]:
        """
        Find records with missing required data.

        Args:
            records: Data records
            required_fields: List of required field names

        Returns:
            List of anomalies
        """
        anomalies = []
        missing_by_field = {field: [] for field in required_fields}

        for record in records:
            record_id = record.get('id') or record.get('employee_id')
            for field in required_fields:
                value = record.get(field)
                if value is None or value == "" or (isinstance(value, str) and not value.strip()):
                    missing_by_field[field].append(record_id)

        for field, affected in missing_by_field.items():
            if affected:
                anomalies.append(Anomaly(
                    type=AnomalyType.MISSING_DATA,
                    severity="medium" if len(affected) < 5 else "high",
                    description=f"حقل '{field}' فارغ في {len(affected)} سجل",
                    affected_records=affected,
                    details={"field": field}
                ))

        return anomalies

    def find_expiring_contracts(
        self,
        employees: List[Dict],
        days_threshold: int = 30
    ) -> List[Anomaly]:
        """
        Find employees with contracts expiring soon.

        Args:
            employees: Employee records with 'contract_end_date'
            days_threshold: Days before expiry to flag

        Returns:
            List of anomalies
        """
        anomalies = []
        expiring = []
        expired = []

        today = datetime.now().date()
        threshold_date = today + timedelta(days=days_threshold)

        for emp in employees:
            end_date = emp.get('contract_end_date')
            if not end_date:
                continue

            # Parse date if string
            if isinstance(end_date, str):
                try:
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                except ValueError:
                    continue

            emp_id = emp.get('id') or emp.get('employee_id')

            if end_date < today:
                expired.append(emp_id)
            elif end_date <= threshold_date:
                expiring.append(emp_id)

        if expired:
            anomalies.append(Anomaly(
                type=AnomalyType.CONTRACT_EXPIRING,
                severity="high",
                description=f"عقود منتهية الصلاحية ({len(expired)} موظف)",
                affected_records=expired
            ))

        if expiring:
            anomalies.append(Anomaly(
                type=AnomalyType.CONTRACT_EXPIRING,
                severity="medium",
                description=f"عقود ستنتهي خلال {days_threshold} يوم ({len(expiring)} موظف)",
                affected_records=expiring
            ))

        return anomalies

    def query(
        self,
        question: str,
        data: List[Dict],
        context: Optional[str] = None
    ) -> Optional[str]:
        """
        Answer a natural language question about data.

        Args:
            question: User question in natural language
            data: Data to query
            context: Additional context

        Returns:
            Answer string
        """
        if not self.is_available or not data:
            return None

        formatted_data = self._format_data_for_ai(data)

        prompt = f"""البيانات المتاحة:
{formatted_data}

{f"السياق: {context}" if context else ""}

السؤال: {question}

أجب بناءً على البيانات المتاحة فقط. إذا لم تجد الإجابة في البيانات، قل ذلك."""

        try:
            return self._client.chat(
                message=prompt,
                system=self._system_prompt,
                temperature=0.3
            )
        except Exception as e:
            app_logger.error(f"Data query error: {e}")
            return None

    def generate_report(
        self,
        data: List[Dict],
        report_type: str = "summary"
    ) -> Optional[str]:
        """
        Generate a text report from data.

        Args:
            data: Data to report on
            report_type: Type of report (summary, detailed, comparison)

        Returns:
            Report text
        """
        if not self.is_available or not data:
            return None

        formatted_data = self._format_data_for_ai(data)

        prompts = {
            "summary": "اكتب ملخصاً تنفيذياً مختصراً للبيانات التالية:",
            "detailed": "اكتب تقريراً مفصلاً يشمل الإحصائيات والتحليل:",
            "comparison": "قارن بين السجلات المختلفة واستخرج الفروقات:"
        }

        prompt = f"""{prompts.get(report_type, prompts['summary'])}

{formatted_data}

قدم التقرير بتنسيق واضح ومنظم."""

        try:
            return self._client.chat(
                message=prompt,
                system=self._system_prompt,
                temperature=0.4
            )
        except Exception as e:
            app_logger.error(f"Report generation error: {e}")
            return None

    def suggest_improvements(
        self,
        data: List[Dict],
        area: Optional[str] = None
    ) -> List[str]:
        """
        Get AI suggestions for data improvements.

        Args:
            data: Data to analyze
            area: Specific area to focus on

        Returns:
            List of suggestions
        """
        if not self.is_available or not data:
            return []

        formatted_data = self._format_data_for_ai(data)

        prompt = f"""حلل البيانات التالية واقترح تحسينات:

{formatted_data}

{"ركز على: " + area if area else ""}

قدم 3-5 اقتراحات عملية وقابلة للتنفيذ. رقّم الاقتراحات."""

        try:
            response = self._client.chat(
                message=prompt,
                system=self._system_prompt,
                temperature=0.5
            )

            if response:
                # Parse numbered suggestions
                suggestions = []
                lines = response.split("\n")
                for line in lines:
                    line = line.strip()
                    # Look for numbered items
                    if line and (line[0].isdigit() or line.startswith("-")):
                        # Clean up the suggestion
                        suggestion = line.lstrip("0123456789.-) ").strip()
                        if suggestion:
                            suggestions.append(suggestion)

                return suggestions if suggestions else [response]

        except Exception as e:
            app_logger.error(f"Suggestions error: {e}")

        return []


# Singleton instance
_agent: Optional[DataAgent] = None


def get_data_agent() -> DataAgent:
    """Get the singleton data agent instance."""
    global _agent
    if _agent is None:
        _agent = DataAgent()
    return _agent


def analyze_employees(employees: List[Dict], **kwargs) -> List[Insight]:
    """Quick function to analyze employees."""
    return get_data_agent().analyze_employees(employees, **kwargs)


def analyze_salaries(salaries: List[Dict], **kwargs) -> Tuple[List[Anomaly], List[Insight]]:
    """Quick function to analyze salaries."""
    return get_data_agent().analyze_salaries(salaries, **kwargs)


def find_anomalies(
    data: List[Dict],
    required_fields: Optional[List[str]] = None,
    check_contracts: bool = True
) -> List[Anomaly]:
    """
    Find all anomalies in data.

    Args:
        data: Data records
        required_fields: Fields to check for missing data
        check_contracts: Whether to check contract expiry

    Returns:
        List of all anomalies
    """
    agent = get_data_agent()
    anomalies = []

    if required_fields:
        anomalies.extend(agent.find_missing_data(data, required_fields))

    if check_contracts:
        anomalies.extend(agent.find_expiring_contracts(data))

    return anomalies


def generate_insights(data: List[Dict], **kwargs) -> List[Insight]:
    """Generate insights from data."""
    return get_data_agent().analyze_employees(data, **kwargs)
