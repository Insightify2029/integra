# INTEGRA Web Migration - Architecture Blueprint

> **Document Purpose:** Complete reverse-engineering of the current INTEGRA Desktop (PyQt5) system
> to serve as the foundation for rebuilding with Django Web.
>
> **Priority:** HR Module FIRST - everything else comes later.
>
> **Date:** 2026-02-11

---

## Table of Contents

1. [Current System Summary](#1-current-system-summary)
2. [Database Schema (Complete)](#2-database-schema-complete)
3. [HR Module - Screens & Features](#3-hr-module---screens--features)
4. [HR Module - Planned Features (Not Yet Built)](#4-hr-module---planned-features)
5. [Lookup Data (Seed Data)](#5-lookup-data-seed-data)
6. [Business Rules & Validations](#6-business-rules--validations)
7. [New Django Architecture](#7-new-django-architecture)
8. [Form Configuration System (YAML)](#8-form-configuration-system-yaml)
9. [Prerequisites - What You Need to Prepare](#9-prerequisites---what-you-need-to-prepare)
10. [Implementation Phases](#10-implementation-phases)

---

## 1. Current System Summary

| Item | Value |
|------|-------|
| **Current Tech** | PyQt5 Desktop + PostgreSQL |
| **New Tech** | Django Web + PostgreSQL + HTMX + Tailwind CSS |
| **Total Tables** | 24 |
| **HR Tables** | 8 (employees + 7 lookup) |
| **Employees** | 180 records (in backup) |
| **Departments** | 20 |
| **Job Titles** | 88 |
| **Nationalities** | 12 |
| **Banks** | 7 |
| **Companies** | 1 |
| **Statuses** | 2 (Active/Inactive) |

---

## 2. Database Schema (Complete)

### 2.1 Core HR Tables

#### `employees` - Main Employee Table
```sql
CREATE TABLE employees (
    id              SERIAL PRIMARY KEY,
    employee_code   VARCHAR(20) UNIQUE NOT NULL,
    name_ar         VARCHAR(200),
    name_en         VARCHAR(200),
    national_id     VARCHAR(20),
    nationality_id  INTEGER REFERENCES nationalities(id),
    hire_date       DATE,
    department_id   INTEGER REFERENCES departments(id),
    job_title_id    INTEGER REFERENCES job_titles(id),
    bank_id         INTEGER REFERENCES banks(id),
    iban            VARCHAR(50),
    company_id      INTEGER REFERENCES companies(id),
    status_id       INTEGER REFERENCES employee_statuses(id),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `companies`
```sql
CREATE TABLE companies (
    id       SERIAL PRIMARY KEY,
    code     VARCHAR(20),
    name_ar  VARCHAR(200),
    name_en  VARCHAR(200)
);
```

#### `departments`
```sql
CREATE TABLE departments (
    id       SERIAL PRIMARY KEY,
    name_ar  VARCHAR(200),
    name_en  VARCHAR(200)
);
```

#### `job_titles`
```sql
CREATE TABLE job_titles (
    id       SERIAL PRIMARY KEY,
    name_ar  VARCHAR(200),
    name_en  VARCHAR(200)
);
```

#### `nationalities`
```sql
CREATE TABLE nationalities (
    id       SERIAL PRIMARY KEY,
    name_ar  VARCHAR(100),
    name_en  VARCHAR(100)
);
```

#### `banks`
```sql
CREATE TABLE banks (
    id       SERIAL PRIMARY KEY,
    name_ar  VARCHAR(100),
    name_en  VARCHAR(100)
);
```

#### `employee_statuses`
```sql
CREATE TABLE employee_statuses (
    id       SERIAL PRIMARY KEY,
    name_ar  VARCHAR(50),
    name_en  VARCHAR(50)
);
```

### 2.2 Audit Trail
```sql
CREATE TABLE audit.logged_actions (
    id               BIGSERIAL PRIMARY KEY,
    schema_name      TEXT NOT NULL,
    table_name       TEXT NOT NULL,
    record_id        INTEGER,
    action_type      TEXT CHECK (action_type IN ('INSERT','UPDATE','DELETE')),
    old_data         JSONB,
    new_data         JSONB,
    changed_fields   TEXT[],
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    db_user          TEXT DEFAULT current_user,
    app_user         TEXT,
    app_user_id      INTEGER,
    client_ip        INET,
    session_id       TEXT,
    notes            TEXT
);
```

### 2.3 Tasks Module (Future)
```
tasks, task_checklist, task_attachments, task_comments,
task_status_history, task_categories, recurrence_templates
```

### 2.4 Calendar Module (Future)
```
calendar_events, calendar_categories, public_holidays,
event_reminders, event_attendees, calendar_settings
```

### 2.5 Notifications Module (Future)
```
notifications, notification_settings, notification_actions_log
```

---

## 3. HR Module - Screens & Features

### 3.1 Employees List Screen
**What it does:** Shows all employees in a table with 11 columns

| Column | Arabic | Source |
|--------|--------|--------|
| employee_code | كود | employees.employee_code |
| name_ar | الاسم بالعربي | employees.name_ar |
| name_en | الاسم بالإنجليزي | employees.name_en |
| nationality | الجنسية | nationalities.name_ar |
| department | القسم | departments.name_ar |
| job_title | الوظيفة | job_titles.name_ar |
| bank | البنك | banks.name_ar |
| iban | IBAN | employees.iban |
| hire_date | تاريخ التعيين | employees.hire_date |
| company | الشركة | companies.name_ar |
| status | الحالة | employee_statuses.name_ar |

**Features:**
- Search/filter across all columns
- Double-click to open employee profile
- Add employee button
- Export to Excel

### 3.2 Employee Profile Screen (Read-Only)
**3 sections:**

**Section 1: البيانات الأساسية (Basic Info)**
- Employee Code, Status, Name Arabic, Name English
- Nationality, National ID, Hire Date

**Section 2: البيانات الوظيفية (Work Info)**
- Company, Department, Job Title

**Section 3: البيانات البنكية (Bank Info)**
- Bank, IBAN

**Action Buttons on Profile:**
- Edit Employee
- Leave Settlement (planned)
- Calculate Overtime (planned)
- End of Service (planned)
- Deactivate Employee (planned)

### 3.3 Edit Employee Screen
- Same 3 sections as profile but editable
- Dropdown selects for all foreign keys (dynamic from DB)
- Validations (see section 6)
- Save/Cancel buttons

### 3.4 Master Data Management
**Reusable CRUD screen for 5 entities:**
- Nationalities
- Departments
- Job Titles
- Banks
- Companies

**Features per entity:**
- Table view (all records)
- Add new (dialog)
- Edit (double-click)
- Delete (with FK protection)
- Excel import/export
- Search/filter

### 3.5 Statistics Dashboard
**5 stat cards:**
- Total employees count
- Active employees count
- Distinct nationalities count
- Distinct departments count
- Distinct job titles count

---

## 4. HR Module - Planned Features

### Menu Structure (designed but NOT yet built):

```
Employees (الموظفين)
├── View: All / Active / Terminated / By Department / By Nationality / By Job
├── Add New Employee
├── Search Employee
└── Import/Export (Excel, PDF)

Benefits (المستحقات)
├── Salaries: View / Edit / History
├── Allowances: Housing / Transport / Other
└── Deductions: Absence / Late / Other

Leaves (الإجازات)
├── Leave Balances
├── Add Leave Record
├── Leave History
└── Leave Settlement: Single / Bulk / Report

Overtime (الإضافي)
├── Monthly Summary
├── Add Overtime Hours
├── History
└── Settings

End of Service (نهاية الخدمة)
├── Calculator
├── Resigned List
├── Report
└── Settings

Reports (التقارير)
├── Employee: List / Nationality Dist. / Dept Dist. / Job Dist.
├── Financial: Payroll / WPS Bank File / Allowances / Deductions
└── Custom Report Builder
```

---

## 5. Lookup Data (Seed Data)

### 5.1 Companies
| id | name_en |
|----|---------|
| 1 | Pioneers Vegetable Oils Industry - PVO |

### 5.2 Departments (20)
| id | name_en |
|----|---------|
| 1 | COO Office : Operation : LIA Production |
| 2 | COO Office : Operation : Tin Can Factory |
| 3 | COO Office : Operation : QC/QA |
| 4 | COO Office : HR & Administration : Administration |
| 5 | COO Office : Operation |
| 6 | COO Office : Finance & Accounts |
| 7 | COO Office : Marketing & Sales |
| 8 | COO Office : HR & Administration : Administration : Security Dept. |
| 9 | COO Office : Operation : Maintenance |
| 10 | COO Office : HR & Administration : HR |
| 11 | COO Office : Operation : Stores COO |
| 12 | COO Office : Operation : Stores COO : AMOP Khamis Mushait Warehouse |
| 13 | COO Office : Operation : Plastic Factory |
| 14 | COO Office : Operation : KFIP Site |
| 15 | COO Office : Supply Chain : Procurement Supply Chain |
| 16 | COO Office : Supply Chain : Stores Supply Chain |
| 17 | COO Office : Construction & General Maintenance |
| 18 | COO Office : Supply Chain : Logistics |
| 19 | COO Office : Operation : Corrugated Carton Box & Printed Stickers Factory |
| 20 | COO Office |

### 5.3 Nationalities (12)
| id | name_ar | name_en |
|----|---------|---------|
| 1 | مصر | Egypt |
| 2 | الجمهورية العربية السورية | Syria |
| 3 | اليمن | Yemen |
| 4 | باكستان | Pakistan |
| 5 | المملكة العربية السعودية | Saudi Arabia |
| 6 | بنغلاديش | Bangladesh |
| 7 | الهند | India |
| 8 | نيجيريا | Nigeria |
| 9 | تركيا | Turkey |
| 10 | فلسطين | Palestine |
| 11 | السودان | Sudan |
| 12 | إندونيسيا | Indonesia |

### 5.4 Banks (7)
| id | name_en |
|----|---------|
| 1 | Arab National Bank |
| 2 | National Commercial Bank |
| 3 | Al Rajhi Bank |
| 4 | Alinma Bank |
| 5 | The Saudi British Bank |
| 6 | Bank AlJazira |
| 7 | Cash |

### 5.5 Employee Statuses (2)
| id | name_ar | name_en |
|----|---------|---------|
| 1 | نشط | Active |
| 2 | غير نشط | Inactive |

### 5.6 Job Titles (88 total - samples)
| id | name_ar |
|----|---------|
| 1 | مدير عام التشغيل |
| 6 | محاسب |
| 15 | عامل |
| 55 | مدير عام المالية |
| ... | (88 total) |

---

## 6. Business Rules & Validations

### Employee Validations
| Field | Rule |
|-------|------|
| employee_code | Unique, required |
| national_id | Exactly 14 digits |
| iban | Valid Saudi IBAN format (starts with SA) |
| status_id | Required |
| name_ar OR name_en | At least one required |

### Master Data Rules
| Rule | Description |
|------|-------------|
| FK Protection | Cannot delete a record if referenced by employees |
| Unique Names | Department/Job title names should be unique |

---

## 7. New Django Architecture

### Tech Stack
```
Backend:   Django 5.x + Python 3.11+
Database:  PostgreSQL 16+
Frontend:  Django Templates + HTMX + Tailwind CSS + Alpine.js
Forms:     YAML Config-Driven (see section 8)
Reports:   YAML Config-Driven
RTL:       Tailwind CSS RTL plugin
Arabic:    Cairo font (Google Fonts)
Icons:     Heroicons + custom SVG
Export:    openpyxl (Excel) + weasyprint (PDF)
```

### Project Structure
```
integra_web/
├── manage.py
├── config/                    # Django project settings
│   ├── settings/
│   │   ├── base.py           # Common settings
│   │   ├── development.py    # Dev settings
│   │   └── production.py     # Prod settings
│   ├── urls.py               # Root URL config
│   └── wsgi.py
│
├── core/                      # Shared infrastructure
│   ├── models.py             # Base models (TimeStamped, Auditable)
│   ├── views.py              # Base views (CRUD mixins)
│   ├── forms.py              # Base form classes
│   ├── middleware/            # Custom middleware
│   │   ├── audit.py          # Audit trail middleware
│   │   └── locale.py         # Arabic/English locale
│   ├── templatetags/         # Custom template tags
│   │   ├── form_renderer.py  # YAML form rendering
│   │   └── rtl_helpers.py    # RTL utilities
│   └── utils/                # Shared utilities
│       ├── export.py         # Excel/PDF export
│       └── validators.py     # Saudi ID, IBAN validators
│
├── apps/                      # Business modules
│   ├── hr/                   # HR Module (PRIORITY)
│   │   ├── models.py         # Employee, Department, etc.
│   │   ├── views.py          # List, Detail, Create, Update
│   │   ├── urls.py           # URL patterns
│   │   ├── admin.py          # Django admin config
│   │   ├── forms/            # YAML form configs
│   │   │   ├── employee_form.yaml
│   │   │   ├── employee_list.yaml
│   │   │   └── master_data.yaml
│   │   ├── reports/          # YAML report configs
│   │   │   ├── employee_list.yaml
│   │   │   └── department_distribution.yaml
│   │   ├── services/         # Business logic
│   │   │   ├── employee_service.py
│   │   │   └── report_service.py
│   │   └── tests/            # Unit tests
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_services.py
│   │
│   ├── payroll/              # Payroll (Phase 2)
│   ├── leaves/               # Leave Management (Phase 2)
│   ├── overtime/             # Overtime (Phase 2)
│   └── eos/                  # End of Service (Phase 2)
│
├── templates/                 # HTML templates
│   ├── base.html             # Master layout
│   ├── components/           # Reusable components
│   │   ├── navbar.html
│   │   ├── sidebar.html
│   │   ├── stat_card.html
│   │   ├── data_table.html
│   │   └── form_renderer.html
│   └── hr/                   # HR templates
│       ├── employee_list.html
│       ├── employee_detail.html
│       ├── employee_form.html
│       └── master_data.html
│
├── static/                    # Static files
│   ├── css/
│   ├── js/
│   └── fonts/                # Cairo font
│
├── forms/                     # YAML form definitions
│   └── hr/
│       ├── employee.yaml
│       └── department.yaml
│
├── reports/                   # YAML report definitions
│   └── hr/
│       ├── employee_list.yaml
│       └── stats.yaml
│
└── locale/                    # Translations
    └── ar/                   # Arabic translations
```

---

## 8. Form Configuration System (YAML)

### Example: Employee Form
```yaml
# forms/hr/employee.yaml
form:
  id: employee_form
  title_ar: "بيانات الموظف"
  title_en: "Employee Data"
  model: hr.Employee
  layout: "2-column"

  sections:
    - id: basic_info
      title_ar: "البيانات الأساسية"
      title_en: "Basic Information"
      icon: "user"
      fields:
        - name: employee_code
          label_ar: "رقم الموظف"
          label_en: "Employee Code"
          type: text
          width: 6          # out of 12 (Bootstrap grid)
          required: true
          readonly_on_edit: true

        - name: status
          label_ar: "الحالة"
          label_en: "Status"
          type: select
          source: employee_statuses
          width: 6
          required: true

        - name: name_ar
          label_ar: "الاسم بالعربي"
          label_en: "Name (Arabic)"
          type: text
          width: 6
          direction: rtl

        - name: name_en
          label_ar: "الاسم بالإنجليزي"
          label_en: "Name (English)"
          type: text
          width: 6
          direction: ltr

        - name: nationality
          label_ar: "الجنسية"
          label_en: "Nationality"
          type: select
          source: nationalities
          width: 6

        - name: national_id
          label_ar: "رقم الهوية"
          label_en: "National ID"
          type: text
          width: 6
          validation: national_id

        - name: hire_date
          label_ar: "تاريخ التعيين"
          label_en: "Hire Date"
          type: date
          width: 6

    - id: work_info
      title_ar: "البيانات الوظيفية"
      title_en: "Work Information"
      icon: "briefcase"
      fields:
        - name: company
          label_ar: "الشركة"
          label_en: "Company"
          type: select
          source: companies
          width: 4

        - name: department
          label_ar: "القسم"
          label_en: "Department"
          type: select
          source: departments
          width: 4

        - name: job_title
          label_ar: "المسمى الوظيفي"
          label_en: "Job Title"
          type: select
          source: job_titles
          width: 4

    - id: bank_info
      title_ar: "البيانات البنكية"
      title_en: "Bank Information"
      icon: "credit-card"
      fields:
        - name: bank
          label_ar: "البنك"
          label_en: "Bank"
          type: select
          source: banks
          width: 6

        - name: iban
          label_ar: "رقم الآيبان"
          label_en: "IBAN"
          type: text
          width: 6
          validation: iban
          placeholder: "SA..."
```

### How to Customize (User Guide)

**Change field order:** Move the field block up/down in the YAML

**Change field width:** Modify `width` value (1-12)

**Hide a field:** Add `visible: false`

**Make field required:** Add `required: true`

**Change label:** Modify `label_ar` / `label_en`

**Add new section:** Copy a section block and modify

**Change layout:** Modify `layout` to "1-column", "2-column", or "3-column"

---

## 9. Prerequisites - What You Need to Prepare

### Required Software

| # | Software | Version | Purpose | How to Install |
|---|----------|---------|---------|----------------|
| 1 | **Python** | 3.11+ | Backend runtime | python.org or `winget install Python.Python.3.11` |
| 2 | **PostgreSQL** | 16+ | Database | postgresql.org or `winget install PostgreSQL.PostgreSQL` |
| 3 | **Git** | Latest | Version control | Already installed |
| 4 | **Node.js** | 20+ | Tailwind CSS build | nodejs.org or `winget install OpenJS.NodeJS.LTS` |
| 5 | **VS Code** | Latest | Edit YAML files | Optional but recommended |

### Steps After Installation

```bash
# 1. Create PostgreSQL database
createdb integra_web

# 2. Clone the repo (already done)
# 3. Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac

# 4. Install Python packages (I will create requirements.txt)
pip install -r requirements.txt

# 5. Install Tailwind
npm install

# 6. Run migrations
python manage.py migrate

# 7. Load seed data
python manage.py loaddata seed_data

# 8. Start server
python manage.py runserver
```

### What I Need From You (Decisions)

| # | Question | Options |
|---|----------|---------|
| 1 | Operating System? | Windows / Linux / Mac |
| 2 | Start local first? | Yes (recommended) / Deploy to server |
| 3 | Want user authentication (login)? | Yes / No (single user) |
| 4 | Arabic-only or bilingual? | Arabic-only / Arabic + English |
| 5 | Any additional employee fields? | The current 12 fields enough? |

---

## 10. Implementation Phases

### Phase 1: Foundation + HR Core (PRIORITY)

**Step 1: Django Project Setup**
- Project structure, settings, database config
- Tailwind CSS + HTMX setup
- Base templates (layout, navbar, RTL)
- Cairo font integration

**Step 2: Form Engine (YAML → HTML)**
- YAML parser
- Field type renderers (text, select, date)
- Validation engine
- Section/tab layout system

**Step 3: Employee CRUD**
- Employee model + migrations
- Lookup models (Department, JobTitle, etc.)
- Employee list page (with search, filter, export)
- Employee detail page (read-only)
- Employee create/edit form (from YAML)
- Statistics dashboard cards

**Step 4: Master Data Management**
- Generic CRUD for all lookup tables
- FK protection on delete
- Excel import/export

**Step 5: Seed Data + Testing**
- Load all lookup data
- Unit tests for models, views, services
- Manual testing

### Phase 2: HR Advanced (After Phase 1)
- Salary management
- Leave management & settlement
- Overtime tracking
- End of service calculator
- Reports (employee list, distributions, payroll)
- WPS bank file export

### Phase 3: Other Modules (Later)
- Costing, Logistics, Custody, Insurance
- Dashboard, Calendar, Tasks
- AI integration

---

## Summary

> **Building from scratch with Django gives us:**
> - Clean, tested code from day one
> - Config-driven forms (YAML) - easy to customize
> - Web-based (browser access from any device)
> - Same PostgreSQL database
> - Same Python language
> - Arabic RTL support built-in
> - Proper testing framework
> - No PyQt5 complexity (no widget lifecycle, no thread safety issues)
