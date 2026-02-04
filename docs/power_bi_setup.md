# Power BI Desktop Integration Guide
# دليل تكامل Power BI Desktop مع INTEGRA

---

## Overview | نظرة عامة

INTEGRA provides seamless integration with **Power BI Desktop** (100% free) for advanced analytics and professional dashboards.

يوفر INTEGRA تكاملاً سلساً مع **Power BI Desktop** (مجاني 100%) للتحليلات المتقدمة ولوحات التحكم الاحترافية.

---

## Prerequisites | المتطلبات الأساسية

1. **Power BI Desktop** (Free download from Microsoft)
   - [Download Link](https://powerbi.microsoft.com/desktop)

2. **PostgreSQL** running with INTEGRA database
   - Default: `localhost:5432`
   - Database: `integra`

3. **BI Views** created in database
   - Use INTEGRA's BI Settings dialog to create views

---

## Step 1: Install Power BI Desktop | تثبيت Power BI Desktop

### Windows
1. Download from [powerbi.microsoft.com/desktop](https://powerbi.microsoft.com/desktop)
2. Run the installer
3. Sign in with a Microsoft account (free account works)

### Note
Power BI Desktop is **completely free** for local use. You only need a paid license for Power BI Service (cloud publishing).

---

## Step 2: Create BI Views | إنشاء BI Views

Before connecting Power BI, create the optimized views in your database:

### Option A: Using INTEGRA UI
1. Open INTEGRA
2. Go to **Settings** → **Power BI Settings**
3. Click **Views** tab
4. Click **Create Views** button

### Option B: Using Python
```python
from core.bi import get_bi_views_manager

manager = get_bi_views_manager()
success, failed = manager.create_all_views()
print(f"Created: {success}, Failed: {failed}")
```

### Available Views

| View Name | Description (EN) | الوصف (AR) |
|-----------|------------------|------------|
| `employees_summary` | Comprehensive employee data | بيانات الموظفين الشاملة |
| `department_stats` | Department statistics | إحصائيات الأقسام |
| `payroll_analysis` | Salary analytics | تحليل الرواتب |
| `monthly_trends` | Hiring/termination trends | اتجاهات التوظيف والإنهاء |
| `company_summary` | Company-level metrics | ملخص الشركة |
| `job_title_analysis` | Job title statistics | تحليل المسميات الوظيفية |
| `nationality_distribution` | Workforce nationality breakdown | توزيع الجنسيات |

---

## Step 3: Connect Power BI to PostgreSQL | ربط Power BI بـ PostgreSQL

1. **Open Power BI Desktop**

2. **Get Data**
   - Click **Get Data** in the Home ribbon
   - Or use shortcut: `Ctrl + G`

3. **Select PostgreSQL**
   - Search for "PostgreSQL"
   - Select **PostgreSQL database**
   - Click **Connect**

4. **Enter Connection Details**
   ```
   Server: localhost
   Database: integra
   ```
   - Data Connectivity mode: **DirectQuery** (recommended for live data)
   - Or **Import** (for faster performance, but data is cached)

5. **Authentication**
   - Select **Database** tab
   - Enter your PostgreSQL credentials:
     - Username: `postgres` (or your user)
     - Password: your password

6. **Select Tables/Views**
   - In the Navigator, expand `bi_views` schema
   - Check the views you want to use
   - Click **Load** or **Transform Data**

---

## Step 4: Build Visualizations | إنشاء التصورات

### Recommended Visualizations

#### Employee Dashboard
- **Card**: Total employees count
- **Pie Chart**: Distribution by department
- **Bar Chart**: Salary by job title
- **Table**: Employee details

#### Payroll Analysis
- **Stacked Bar**: Salary ranges distribution
- **Line Chart**: Monthly payroll trends
- **Matrix**: Department × Job Title salary breakdown

#### HR Trends
- **Line Chart**: Monthly hires vs terminations
- **Area Chart**: Headcount over time
- **KPI**: Net change indicator

### Arabic/RTL Support

For proper Arabic display:

1. Go to **File** → **Options and settings** → **Options**
2. Under **Current File** → **Regional Settings**
3. Set locale to **Arabic**
4. For RTL visuals, use the **Format** pane and look for alignment options

---

## Step 5: Export and Share | التصدير والمشاركة

### Save as .pbix
```
File → Save As → Choose location → Save
```

### Export to PDF
```
File → Export → Export to PDF
```

### Share (Optional - Requires License)
For sharing via Power BI Service, you'll need a Power BI Pro license. However, you can share `.pbix` files freely.

---

## Data Export from INTEGRA | تصدير البيانات من INTEGRA

If you prefer to work with exported data instead of DirectQuery:

### Using INTEGRA UI
1. Open **Power BI Settings** dialog
2. Go to **Export** tab
3. Click **Export to CSV** or **Export to Excel**
4. Import the files into Power BI

### Using Python
```python
from core.bi import get_bi_exporter

exporter = get_bi_exporter()

# Export single view to CSV
result = exporter.export_to_csv("employees_summary")
print(f"Exported to: {result.file_path}")

# Export all views to Excel
result = exporter.export_all_views_excel()
print(f"Excel file: {result.file_path}")
```

### Scheduled Export
```python
from core.bi import get_export_scheduler, ExportFrequency
from datetime import time

scheduler = get_export_scheduler()
scheduler.configure(
    enabled=True,
    frequency=ExportFrequency.DAILY,
    time_of_day=time(6, 0),  # 6:00 AM
    export_format="excel"
)
scheduler.start()
```

---

## Pre-built Templates | قوالب جاهزة

INTEGRA includes template placeholders for Power BI reports:

| Template | Purpose |
|----------|---------|
| `employees_dashboard.pbit` | Complete HR dashboard |
| `payroll_analysis.pbit` | Salary analytics |
| `department_overview.pbit` | Department metrics |
| `executive_summary.pbit` | C-level KPIs |

### Using Templates
1. Open INTEGRA → Power BI Settings → Templates
2. Click on a template to open it
3. Enter your database credentials when prompted

---

## Troubleshooting | استكشاف الأخطاء

### Connection Failed
- Verify PostgreSQL is running
- Check firewall settings for port 5432
- Confirm username/password

### Views Not Found
- Run `manager.create_all_views()` to create views
- Refresh the Navigator in Power BI

### Arabic Text Issues
- Ensure your system has Arabic fonts installed
- Use UTF-8 encoding for data exports

### Performance Issues
- Use **Import** mode instead of DirectQuery
- Limit data with filters/slicers
- Consider materialized views for large datasets

---

## Connection String Reference

```
Server=localhost;Port=5432;Database=integra
```

For advanced connection options:
```
Server=localhost;Port=5432;Database=integra;SSL Mode=Prefer;Timeout=30
```

---

## Support | الدعم

For issues with:
- **INTEGRA**: Check logs in `logs/` directory
- **Power BI**: Visit [Power BI Community](https://community.powerbi.com)
- **PostgreSQL**: Check `pg_log` for database errors

---

*Document Version: 1.0.0*
*Last Updated: February 2026*
