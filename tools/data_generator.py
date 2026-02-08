#!/usr/bin/env python3
# tools/data_generator.py
"""
INTEGRA - Fake Data Generator
==============================
Generate realistic test data for development and demos.

Uses the `Faker` library with Arabic (Saudi) locale.

Usage:
    # From command line
    python tools/data_generator.py --employees 50
    python tools/data_generator.py --employees 100 --format csv --output test_data.csv
    python tools/data_generator.py --employees 20 --format json --output test_data.json
    python tools/data_generator.py --employees 10 --print

    # From code
    from tools.data_generator import DataGenerator

    gen = DataGenerator()
    employees = gen.generate_employees(50)
    gen.export_csv(employees, "test_employees.csv")
"""

import argparse
import csv
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from faker import Faker
    HAS_FAKER = True
except ImportError:
    HAS_FAKER = False


# ─── Constants ─────────────────────────────────────────────

COMPANIES = [
    {"id": 1, "name_ar": "شركة المراعي", "name_en": "Almarai"},
    {"id": 2, "name_ar": "شركة سابك", "name_en": "SABIC"},
    {"id": 3, "name_ar": "شركة أرامكو", "name_en": "Aramco"},
    {"id": 4, "name_ar": "مجموعة الراجحي", "name_en": "Al Rajhi Group"},
    {"id": 5, "name_ar": "شركة الاتصالات", "name_en": "STC"},
]

DEPARTMENTS = [
    {"id": 1, "name_ar": "الإدارة العامة", "name_en": "General Management"},
    {"id": 2, "name_ar": "المالية", "name_en": "Finance"},
    {"id": 3, "name_ar": "الموارد البشرية", "name_en": "Human Resources"},
    {"id": 4, "name_ar": "تقنية المعلومات", "name_en": "Information Technology"},
    {"id": 5, "name_ar": "المبيعات", "name_en": "Sales"},
    {"id": 6, "name_ar": "التسويق", "name_en": "Marketing"},
    {"id": 7, "name_ar": "الإنتاج", "name_en": "Production"},
    {"id": 8, "name_ar": "المشتريات", "name_en": "Procurement"},
    {"id": 9, "name_ar": "الجودة", "name_en": "Quality"},
    {"id": 10, "name_ar": "اللوجستيات", "name_en": "Logistics"},
]

JOB_TITLES = [
    {"id": 1, "name_ar": "مدير عام", "name_en": "General Manager"},
    {"id": 2, "name_ar": "مدير قسم", "name_en": "Department Manager"},
    {"id": 3, "name_ar": "رئيس فريق", "name_en": "Team Lead"},
    {"id": 4, "name_ar": "محاسب", "name_en": "Accountant"},
    {"id": 5, "name_ar": "مهندس برمجيات", "name_en": "Software Engineer"},
    {"id": 6, "name_ar": "محلل بيانات", "name_en": "Data Analyst"},
    {"id": 7, "name_ar": "أخصائي موارد بشرية", "name_en": "HR Specialist"},
    {"id": 8, "name_ar": "مندوب مبيعات", "name_en": "Sales Representative"},
    {"id": 9, "name_ar": "فني صيانة", "name_en": "Maintenance Technician"},
    {"id": 10, "name_ar": "سكرتير", "name_en": "Secretary"},
    {"id": 11, "name_ar": "مساعد إداري", "name_en": "Admin Assistant"},
    {"id": 12, "name_ar": "مراقب جودة", "name_en": "Quality Inspector"},
]

NATIONALITIES = [
    {"id": 1, "name_ar": "سعودي", "name_en": "Saudi"},
    {"id": 2, "name_ar": "مصري", "name_en": "Egyptian"},
    {"id": 3, "name_ar": "يمني", "name_en": "Yemeni"},
    {"id": 4, "name_ar": "باكستاني", "name_en": "Pakistani"},
    {"id": 5, "name_ar": "هندي", "name_en": "Indian"},
    {"id": 6, "name_ar": "بنغلاديشي", "name_en": "Bangladeshi"},
    {"id": 7, "name_ar": "فلبيني", "name_en": "Filipino"},
    {"id": 8, "name_ar": "سوداني", "name_en": "Sudanese"},
    {"id": 9, "name_ar": "سوري", "name_en": "Syrian"},
    {"id": 10, "name_ar": "أردني", "name_en": "Jordanian"},
]

BANKS = [
    {"id": 1, "name_ar": "البنك الأهلي", "name_en": "SNB"},
    {"id": 2, "name_ar": "بنك الراجحي", "name_en": "Al Rajhi Bank"},
    {"id": 3, "name_ar": "بنك الإنماء", "name_en": "Alinma Bank"},
    {"id": 4, "name_ar": "البنك السعودي الفرنسي", "name_en": "Banque Saudi Fransi"},
    {"id": 5, "name_ar": "بنك الرياض", "name_en": "Riyad Bank"},
]

STATUSES = [
    {"id": 1, "name_ar": "نشط", "name_en": "Active"},
    {"id": 2, "name_ar": "مُنهى خدمات", "name_en": "Terminated"},
    {"id": 3, "name_ar": "مستقيل", "name_en": "Resigned"},
    {"id": 4, "name_ar": "إجازة", "name_en": "On Leave"},
]

# Salary ranges by job title (approximate SAR)
SALARY_RANGES = {
    1: (15000, 40000),   # General Manager
    2: (10000, 25000),   # Department Manager
    3: (8000, 18000),    # Team Lead
    4: (5000, 12000),    # Accountant
    5: (8000, 20000),    # Software Engineer
    6: (6000, 15000),    # Data Analyst
    7: (5000, 12000),    # HR Specialist
    8: (4000, 10000),    # Sales Representative
    9: (3500, 8000),     # Maintenance Technician
    10: (3500, 7000),    # Secretary
    11: (3000, 6000),    # Admin Assistant
    12: (4000, 9000),    # Quality Inspector
}


class DataGenerator:
    """Generate realistic fake data for INTEGRA testing."""

    def __init__(self, locale: str = "ar_SA", seed: Optional[int] = None):
        """
        Initialize the data generator.

        Args:
            locale: Faker locale (default: Arabic Saudi).
            seed: Optional seed for reproducible data.
        """
        if not HAS_FAKER:
            raise ImportError(
                "Faker is required for data generation. "
                "Install it with: pip install Faker"
            )
        self._fake = Faker(locale)
        self._fake_en = Faker("en_US")
        if seed is not None:
            Faker.seed(seed)

    def generate_employee(self, employee_id: int) -> Dict[str, Any]:
        """
        Generate a single employee record.

        Args:
            employee_id: Employee ID number.

        Returns:
            Dictionary with employee data matching the database schema.
        """
        job_title = self._fake.random_element(JOB_TITLES)
        company = self._fake.random_element(COMPANIES)
        department = self._fake.random_element(DEPARTMENTS)
        nationality = self._fake.random_element(NATIONALITIES)
        bank = self._fake.random_element(BANKS)

        # Weight status: 80% active, 10% terminated, 5% resigned, 5% on leave
        status = self._fake.random_element(
            [STATUSES[0]] * 80 + [STATUSES[1]] * 10 +
            [STATUSES[2]] * 5 + [STATUSES[3]] * 5
        )

        salary_min, salary_max = SALARY_RANGES.get(
            job_title["id"], (3000, 10000)
        )
        basic_salary = self._fake.random_int(
            min=salary_min, max=salary_max, step=500
        )

        hire_date = self._fake.date_between(
            start_date=date.today() + timedelta(days=-3650),
            end_date=date.today() + timedelta(days=-30),
        )

        # Generate name in Arabic
        name_ar = self._fake.name()
        # Generate English name using en locale
        name_en = self._fake_en.name()

        emp_number = f"EMP-{employee_id:05d}"

        return {
            "id": employee_id,
            "employee_number": emp_number,
            "name_ar": name_ar,
            "name_en": name_en,
            "company_id": company["id"],
            "company_name": company["name_ar"],
            "department_id": department["id"],
            "department_name": department["name_ar"],
            "job_title_id": job_title["id"],
            "job_title_name": job_title["name_ar"],
            "nationality_id": nationality["id"],
            "nationality_name": nationality["name_ar"],
            "bank_id": bank["id"],
            "bank_name": bank["name_ar"],
            "status_id": status["id"],
            "status_name": status["name_ar"],
            "basic_salary": basic_salary,
            "housing_allowance": int(basic_salary * 0.25),
            "transport_allowance": int(basic_salary * 0.10),
            "phone": self._fake.phone_number(),
            "email": self._fake_en.email(),
            "hire_date": hire_date.isoformat(),
            "iqama_number": self._fake.numerify("##########"),
            "iban": f"SA{self._fake.numerify('############################')}",
        }

    def generate_employees(self, count: int = 50) -> List[Dict[str, Any]]:
        """
        Generate multiple employee records.

        Args:
            count: Number of employees to generate.

        Returns:
            List of employee dictionaries.
        """
        return [
            self.generate_employee(i + 1)
            for i in range(count)
        ]

    def export_csv(self, employees: List[Dict[str, Any]], filepath: str) -> str:
        """
        Export employees to CSV file.

        Args:
            employees: List of employee dicts.
            filepath: Output file path.

        Returns:
            Absolute path of the created file.
        """
        if not employees:
            return ""

        out_path = Path(filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = list(employees[0].keys())
        with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(employees)

        return str(out_path.resolve())

    def export_json(self, employees: List[Dict[str, Any]], filepath: str) -> str:
        """
        Export employees to JSON file.

        Args:
            employees: List of employee dicts.
            filepath: Output file path.

        Returns:
            Absolute path of the created file.
        """
        out_path = Path(filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(employees, f, ensure_ascii=False, indent=2)

        return str(out_path.resolve())

    def print_summary(self, employees: List[Dict[str, Any]]) -> None:
        """Print a summary of generated data to stdout."""
        total = len(employees)
        active = sum(1 for e in employees if e["status_id"] == 1)
        avg_salary = (
            sum(e["basic_salary"] for e in employees) // total
            if total > 0
            else 0
        )

        # Department distribution
        dept_counts: Dict[str, int] = {}
        for emp in employees:
            dept = emp["department_name"]
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        print(f"\n{'═' * 50}")
        print(f"  INTEGRA - Test Data Summary")
        print(f"{'═' * 50}")
        print(f"  Total Employees : {total}")
        print(f"  Active          : {active}")
        print(f"  Avg Salary (SAR): {avg_salary:,}")
        print(f"\n  Department Distribution:")
        for dept, count in sorted(dept_counts.items(), key=lambda x: -x[1]):
            bar = "█" * count
            print(f"    {dept:.<25} {count:>3}  {bar}")
        print(f"{'═' * 50}\n")


def _print_employees(employees: List[Dict[str, Any]], limit: int = 10) -> None:
    """Print employee records in readable format."""
    for emp in employees[:limit]:
        print(f"\n  ── {emp['employee_number']} ──")
        print(f"  الاسم     : {emp['name_ar']}")
        print(f"  Name      : {emp['name_en']}")
        print(f"  الشركة    : {emp['company_name']}")
        print(f"  القسم     : {emp['department_name']}")
        print(f"  الوظيفة   : {emp['job_title_name']}")
        print(f"  الراتب    : {emp['basic_salary']:,} ر.س")
        print(f"  الحالة    : {emp['status_name']}")
        print(f"  تاريخ التعيين: {emp['hire_date']}")

    if len(employees) > limit:
        print(f"\n  ... and {len(employees) - limit} more employees")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="INTEGRA - Fake Data Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python tools/data_generator.py --employees 50\n"
            "  python tools/data_generator.py --employees 100 --format csv --output data.csv\n"
            "  python tools/data_generator.py --employees 20 --format json --output data.json\n"
            "  python tools/data_generator.py --employees 10 --print\n"
            "  python tools/data_generator.py --employees 50 --seed 42  # reproducible\n"
        ),
    )

    parser.add_argument(
        "--employees", "-n",
        type=int,
        default=50,
        help="Number of employees to generate (default: 50)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["csv", "json"],
        default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path (default: auto-named in current directory)",
    )
    parser.add_argument(
        "--print", "-p",
        action="store_true",
        dest="print_data",
        help="Print generated data to console",
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed for reproducible data",
    )

    args = parser.parse_args()

    if not HAS_FAKER:
        print("Error: Faker is not installed.")
        print("Install with: pip install Faker")
        sys.exit(1)

    gen = DataGenerator(seed=args.seed)
    employees = gen.generate_employees(args.employees)

    gen.print_summary(employees)

    if args.print_data:
        _print_employees(employees)

    # Export
    output_path = args.output
    if output_path is None:
        ext = "csv" if args.format == "csv" else "json"
        output_path = f"test_employees_{args.employees}.{ext}"

    if args.format == "csv":
        path = gen.export_csv(employees, output_path)
    else:
        path = gen.export_json(employees, output_path)

    print(f"  Data exported to: {path}")


if __name__ == "__main__":
    main()
