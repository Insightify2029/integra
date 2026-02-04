-- =================================================================
-- INTEGRA - Tasks Module Database Schema
-- المحور H: موديول المهام
-- التاريخ: 4 فبراير 2026
-- =================================================================

-- ═══════════════════════════════════════════════════════════════
-- جدول المهام الرئيسي (tasks)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,

    -- البيانات الأساسية
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',      -- pending, in_progress, completed, cancelled
    priority VARCHAR(20) DEFAULT 'normal',     -- urgent, high, normal, low
    category VARCHAR(100),                     -- hr, finance, operations, general, etc.

    -- الربط بالكيانات الأخرى
    parent_task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,  -- للمهام الفرعية
    source_email_id VARCHAR(255),                                     -- مصدر الإيميل
    employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,  -- الموظف المرتبط
    assigned_to INTEGER,                                              -- المكلف بالمهمة

    -- التواريخ
    due_date TIMESTAMP,
    reminder_date TIMESTAMP,
    start_date TIMESTAMP,
    completed_at TIMESTAMP,

    -- التكرار
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern JSONB,  -- {"type": "daily|weekly|monthly", "interval": 1, ...}
    next_occurrence DATE,

    -- تحليل AI
    ai_analysis JSONB,         -- تحليل AI للمهمة
    ai_suggested_action TEXT,  -- الإجراء المقترح
    ai_priority_score DECIMAL(3,2),  -- درجة الأولوية 0-1

    -- البيانات الإضافية
    tags TEXT[],               -- وسوم المهمة
    metadata JSONB,            -- بيانات إضافية

    -- تتبع التغييرات
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- فهارس للبحث السريع
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_employee_id ON tasks(employee_id);
CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_is_recurring ON tasks(is_recurring) WHERE is_recurring = TRUE;

-- ═══════════════════════════════════════════════════════════════
-- جدول قائمة التحقق (task_checklist)
-- للمهام الفرعية البسيطة / Checklist items
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS task_checklist (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(500) NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_checklist_task_id ON task_checklist(task_id);

-- ═══════════════════════════════════════════════════════════════
-- جدول مرفقات المهام (task_attachments)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS task_attachments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_attachments_task_id ON task_attachments(task_id);

-- ═══════════════════════════════════════════════════════════════
-- جدول تعليقات المهام (task_comments)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS task_comments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE NOT NULL,
    content TEXT NOT NULL,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_comments_task_id ON task_comments(task_id);

-- ═══════════════════════════════════════════════════════════════
-- جدول سجل حالة المهام (task_status_history)
-- لتتبع تغييرات الحالة
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS task_status_history (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by INTEGER,
    changed_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_task_status_history_task_id ON task_status_history(task_id);

-- ═══════════════════════════════════════════════════════════════
-- جدول أنماط التكرار المحفوظة (recurrence_templates)
-- قوالب جاهزة للمهام المتكررة
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS recurrence_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    name_ar VARCHAR(255),
    pattern_type VARCHAR(50) NOT NULL,  -- daily, weekly, monthly, yearly
    pattern_config JSONB NOT NULL,
    is_system BOOLEAN DEFAULT FALSE,    -- قوالب النظام
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- إدراج قوالب التكرار الافتراضية
-- ═══════════════════════════════════════════════════════════════
INSERT INTO recurrence_templates (name, name_ar, pattern_type, pattern_config, is_system) VALUES
('Daily', 'يومي', 'daily', '{"interval": 1}', TRUE),
('Weekdays', 'أيام العمل', 'weekly', '{"interval": 1, "days_of_week": ["sunday", "monday", "tuesday", "wednesday", "thursday"]}', TRUE),
('Weekly', 'أسبوعي', 'weekly', '{"interval": 1}', TRUE),
('Biweekly', 'كل أسبوعين', 'weekly', '{"interval": 2}', TRUE),
('Monthly', 'شهري', 'monthly', '{"interval": 1, "day_of_month": 1}', TRUE),
('Quarterly', 'ربع سنوي', 'monthly', '{"interval": 3, "day_of_month": 1}', TRUE),
('Yearly', 'سنوي', 'yearly', '{"interval": 1}', TRUE)
ON CONFLICT DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- جدول تصنيفات المهام (task_categories)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS task_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    name_ar VARCHAR(100),
    color VARCHAR(7) DEFAULT '#3498db',  -- Hex color
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- إدراج التصنيفات الافتراضية
INSERT INTO task_categories (name, name_ar, color, icon, sort_order) VALUES
('general', 'عام', '#6c757d', 'fa.tasks', 1),
('hr', 'الموارد البشرية', '#28a745', 'fa.users', 2),
('finance', 'المالية', '#ffc107', 'fa.money-bill', 3),
('operations', 'العمليات', '#17a2b8', 'fa.cogs', 4),
('it', 'تقنية المعلومات', '#6610f2', 'fa.laptop-code', 5),
('legal', 'الشؤون القانونية', '#dc3545', 'fa.gavel', 6),
('admin', 'الإدارة', '#fd7e14', 'fa.building', 7),
('personal', 'شخصي', '#20c997', 'fa.user', 8)
ON CONFLICT (name) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- Trigger: تحديث updated_at تلقائياً
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION update_task_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_tasks_updated_at ON tasks;
CREATE TRIGGER trigger_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_task_updated_at();

-- ═══════════════════════════════════════════════════════════════
-- Trigger: تسجيل تغييرات الحالة تلقائياً
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION log_task_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO task_status_history (task_id, old_status, new_status, changed_by)
        VALUES (NEW.id, OLD.status, NEW.status, NEW.updated_by);

        -- تحديث completed_at عند الإكمال
        IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
            NEW.completed_at = NOW();
        ELSIF NEW.status != 'completed' AND OLD.status = 'completed' THEN
            NEW.completed_at = NULL;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_task_status_change ON tasks;
CREATE TRIGGER trigger_task_status_change
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION log_task_status_change();

-- ═══════════════════════════════════════════════════════════════
-- View: نظرة عامة على المهام
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW task_overview AS
SELECT
    t.id,
    t.title,
    t.description,
    t.status,
    t.priority,
    t.category,
    tc.name_ar AS category_ar,
    tc.color AS category_color,
    t.due_date,
    t.is_recurring,
    t.created_at,
    t.updated_at,
    e.name_ar AS employee_name,
    pt.title AS parent_task_title,
    (SELECT COUNT(*) FROM task_checklist cl WHERE cl.task_id = t.id) AS checklist_count,
    (SELECT COUNT(*) FROM task_checklist cl WHERE cl.task_id = t.id AND cl.is_completed = TRUE) AS checklist_completed,
    (SELECT COUNT(*) FROM task_attachments a WHERE a.task_id = t.id) AS attachments_count,
    (SELECT COUNT(*) FROM task_comments c WHERE c.task_id = t.id) AS comments_count
FROM tasks t
LEFT JOIN employees e ON t.employee_id = e.id
LEFT JOIN tasks pt ON t.parent_task_id = pt.id
LEFT JOIN task_categories tc ON t.category = tc.name;

-- ═══════════════════════════════════════════════════════════════
-- View: المهام المستحقة اليوم
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW tasks_due_today AS
SELECT * FROM task_overview
WHERE DATE(due_date) = CURRENT_DATE
AND status NOT IN ('completed', 'cancelled')
ORDER BY
    CASE priority
        WHEN 'urgent' THEN 1
        WHEN 'high' THEN 2
        WHEN 'normal' THEN 3
        WHEN 'low' THEN 4
    END,
    due_date;

-- ═══════════════════════════════════════════════════════════════
-- View: المهام المتأخرة
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW tasks_overdue AS
SELECT * FROM task_overview
WHERE due_date < NOW()
AND status NOT IN ('completed', 'cancelled')
ORDER BY due_date;

-- ═══════════════════════════════════════════════════════════════
-- View: إحصائيات المهام
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW task_statistics AS
SELECT
    COUNT(*) FILTER (WHERE status = 'pending') AS pending_count,
    COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress_count,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_count,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled_count,
    COUNT(*) FILTER (WHERE due_date < NOW() AND status NOT IN ('completed', 'cancelled')) AS overdue_count,
    COUNT(*) FILTER (WHERE DATE(due_date) = CURRENT_DATE AND status NOT IN ('completed', 'cancelled')) AS due_today_count,
    COUNT(*) FILTER (WHERE priority = 'urgent' AND status NOT IN ('completed', 'cancelled')) AS urgent_count,
    COUNT(*) FILTER (WHERE is_recurring = TRUE) AS recurring_count,
    COUNT(*) AS total_count
FROM tasks;

-- ═══════════════════════════════════════════════════════════════
-- تعليقات للمبرمجين
-- ═══════════════════════════════════════════════════════════════
COMMENT ON TABLE tasks IS 'جدول المهام الرئيسي - يحتوي على كل المهام مع دعم المهام الفرعية والتكرار';
COMMENT ON TABLE task_checklist IS 'قائمة التحقق - عناصر بسيطة تابعة للمهمة';
COMMENT ON TABLE task_attachments IS 'مرفقات المهام - ملفات مرتبطة بالمهمة';
COMMENT ON TABLE task_comments IS 'تعليقات المهام - نقاشات حول المهمة';
COMMENT ON TABLE task_status_history IS 'سجل تغييرات الحالة - تتبع تاريخي للمهمة';
COMMENT ON TABLE recurrence_templates IS 'قوالب التكرار - أنماط جاهزة للمهام المتكررة';
COMMENT ON TABLE task_categories IS 'تصنيفات المهام - فئات لتنظيم المهام';
