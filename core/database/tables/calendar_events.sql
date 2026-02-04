-- =================================================================
-- INTEGRA - Calendar Module Database Schema
-- المحور I: موديول التقويم
-- التاريخ: 4 فبراير 2026
-- =================================================================

-- ═══════════════════════════════════════════════════════════════
-- جدول الأحداث الرئيسي (calendar_events)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS calendar_events (
    id SERIAL PRIMARY KEY,

    -- البيانات الأساسية
    title VARCHAR(500) NOT NULL,
    description TEXT,
    event_type VARCHAR(50) DEFAULT 'event',  -- event, task, reminder, meeting, holiday

    -- التوقيت
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP,
    is_all_day BOOLEAN DEFAULT FALSE,
    timezone VARCHAR(50) DEFAULT 'Asia/Riyadh',

    -- الربط بالكيانات الأخرى
    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,

    -- التذكيرات (JSON array)
    -- [{"type": "notification", "minutes_before": 30}, {"type": "email", "minutes_before": 1440}]
    reminders JSONB DEFAULT '[]',

    -- التكرار
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern JSONB,  -- {"type": "daily|weekly|monthly|yearly", "interval": 1, ...}
    recurrence_end_date DATE,
    parent_event_id INTEGER REFERENCES calendar_events(id) ON DELETE CASCADE,  -- للأحداث المولدة من التكرار

    -- اللون والتصنيف
    color VARCHAR(20) DEFAULT '#3498db',
    category VARCHAR(100),

    -- المشاركون
    -- [{"email": "user@example.com", "name": "أحمد", "status": "accepted|pending|declined"}]
    attendees JSONB DEFAULT '[]',

    -- الموقع
    location VARCHAR(500),
    location_url TEXT,  -- رابط خارجي (Zoom, Teams, etc.)

    -- المصدر والمزامنة
    source VARCHAR(50) DEFAULT 'integra',  -- integra, outlook, google, manual
    external_id VARCHAR(255),  -- معرف خارجي للمزامنة
    external_link TEXT,  -- رابط للحدث الخارجي
    sync_status VARCHAR(50) DEFAULT 'synced',  -- synced, pending, error
    last_synced_at TIMESTAMP,

    -- الحالة
    status VARCHAR(50) DEFAULT 'confirmed',  -- confirmed, tentative, cancelled
    is_private BOOLEAN DEFAULT FALSE,

    -- البيانات الإضافية
    metadata JSONB DEFAULT '{}',

    -- تتبع التغييرات
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- فهارس للبحث السريع
CREATE INDEX IF NOT EXISTS idx_calendar_events_start ON calendar_events(start_datetime);
CREATE INDEX IF NOT EXISTS idx_calendar_events_end ON calendar_events(end_datetime);
CREATE INDEX IF NOT EXISTS idx_calendar_events_type ON calendar_events(event_type);
CREATE INDEX IF NOT EXISTS idx_calendar_events_category ON calendar_events(category);
CREATE INDEX IF NOT EXISTS idx_calendar_events_task_id ON calendar_events(task_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_employee_id ON calendar_events(employee_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_source ON calendar_events(source);
CREATE INDEX IF NOT EXISTS idx_calendar_events_external_id ON calendar_events(external_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_parent_id ON calendar_events(parent_event_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_date_range ON calendar_events(start_datetime, end_datetime);
CREATE INDEX IF NOT EXISTS idx_calendar_events_recurring ON calendar_events(is_recurring) WHERE is_recurring = TRUE;

-- فهرس للبحث في نطاق تاريخ معين
CREATE INDEX IF NOT EXISTS idx_calendar_events_month ON calendar_events(DATE_TRUNC('month', start_datetime));

-- ═══════════════════════════════════════════════════════════════
-- جدول تصنيفات التقويم (calendar_categories)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS calendar_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    name_ar VARCHAR(100),
    color VARCHAR(7) DEFAULT '#3498db',  -- Hex color
    icon VARCHAR(50),
    is_visible BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- إدراج التصنيفات الافتراضية
INSERT INTO calendar_categories (name, name_ar, color, icon, sort_order, is_system) VALUES
('work', 'العمل', '#3498db', 'fa.briefcase', 1, TRUE),
('meeting', 'اجتماع', '#9b59b6', 'fa.users', 2, TRUE),
('task', 'مهمة', '#2ecc71', 'fa.tasks', 3, TRUE),
('reminder', 'تذكير', '#f39c12', 'fa.bell', 4, TRUE),
('holiday', 'إجازة', '#e74c3c', 'fa.umbrella-beach', 5, TRUE),
('personal', 'شخصي', '#1abc9c', 'fa.user', 6, TRUE),
('hr', 'الموارد البشرية', '#27ae60', 'fa.id-card', 7, TRUE),
('finance', 'المالية', '#f1c40f', 'fa.money-bill', 8, TRUE)
ON CONFLICT (name) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- جدول العطلات الرسمية (public_holidays)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public_holidays (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    name_ar VARCHAR(255),
    holiday_date DATE NOT NULL,
    holiday_type VARCHAR(50) DEFAULT 'official',  -- official, company, optional
    country_code VARCHAR(5) DEFAULT 'SA',
    is_recurring_yearly BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_public_holidays_date ON public_holidays(holiday_date);
CREATE INDEX IF NOT EXISTS idx_public_holidays_country ON public_holidays(country_code);

-- إدراج العطلات السعودية الرسمية (2026)
INSERT INTO public_holidays (name, name_ar, holiday_date, holiday_type, country_code, is_recurring_yearly) VALUES
('Saudi National Day', 'اليوم الوطني السعودي', '2026-09-23', 'official', 'SA', TRUE),
('Founding Day', 'يوم التأسيس', '2026-02-22', 'official', 'SA', TRUE)
ON CONFLICT DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- جدول تذكيرات الأحداث (event_reminders)
-- لتخزين التذكيرات المجدولة
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS event_reminders (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES calendar_events(id) ON DELETE CASCADE NOT NULL,
    reminder_datetime TIMESTAMP NOT NULL,
    reminder_type VARCHAR(50) DEFAULT 'notification',  -- notification, email, sms
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_event_reminders_event_id ON event_reminders(event_id);
CREATE INDEX IF NOT EXISTS idx_event_reminders_datetime ON event_reminders(reminder_datetime);
CREATE INDEX IF NOT EXISTS idx_event_reminders_pending ON event_reminders(reminder_datetime, is_sent) WHERE is_sent = FALSE;

-- ═══════════════════════════════════════════════════════════════
-- جدول حضور الاجتماعات (event_attendees)
-- نسخة مفصلة من attendees
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS event_attendees (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES calendar_events(id) ON DELETE CASCADE NOT NULL,
    employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    email VARCHAR(255),
    name VARCHAR(255),
    response_status VARCHAR(50) DEFAULT 'pending',  -- pending, accepted, declined, tentative
    is_organizer BOOLEAN DEFAULT FALSE,
    is_optional BOOLEAN DEFAULT FALSE,
    responded_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_event_attendees_event_id ON event_attendees(event_id);
CREATE INDEX IF NOT EXISTS idx_event_attendees_employee_id ON event_attendees(employee_id);
CREATE INDEX IF NOT EXISTS idx_event_attendees_email ON event_attendees(email);

-- ═══════════════════════════════════════════════════════════════
-- جدول إعدادات التقويم (calendar_settings)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS calendar_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE,

    -- إعدادات العرض
    default_view VARCHAR(20) DEFAULT 'month',  -- day, week, month, agenda
    week_starts_on INTEGER DEFAULT 0,  -- 0 = Sunday, 1 = Monday, 6 = Saturday
    show_weekends BOOLEAN DEFAULT TRUE,
    show_week_numbers BOOLEAN DEFAULT FALSE,

    -- ساعات العمل
    work_hours_start TIME DEFAULT '08:00',
    work_hours_end TIME DEFAULT '17:00',
    work_days INTEGER[] DEFAULT '{0,1,2,3,4}',  -- Sunday to Thursday

    -- المزامنة
    sync_outlook BOOLEAN DEFAULT FALSE,
    outlook_calendar_id VARCHAR(255),
    sync_google BOOLEAN DEFAULT FALSE,
    google_calendar_id VARCHAR(255),

    -- التنبيهات
    default_reminder_minutes INTEGER DEFAULT 30,
    enable_desktop_notifications BOOLEAN DEFAULT TRUE,
    enable_email_notifications BOOLEAN DEFAULT FALSE,

    -- البيانات الإضافية
    preferences JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- Trigger: تحديث updated_at تلقائياً
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION update_calendar_event_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_calendar_events_updated_at ON calendar_events;
CREATE TRIGGER trigger_calendar_events_updated_at
    BEFORE UPDATE ON calendar_events
    FOR EACH ROW
    EXECUTE FUNCTION update_calendar_event_updated_at();

DROP TRIGGER IF EXISTS trigger_calendar_settings_updated_at ON calendar_settings;
CREATE TRIGGER trigger_calendar_settings_updated_at
    BEFORE UPDATE ON calendar_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_calendar_event_updated_at();

-- ═══════════════════════════════════════════════════════════════
-- View: الأحداث مع التفاصيل
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW calendar_events_view AS
SELECT
    ce.id,
    ce.title,
    ce.description,
    ce.event_type,
    ce.start_datetime,
    ce.end_datetime,
    ce.is_all_day,
    ce.timezone,
    ce.task_id,
    t.title AS task_title,
    ce.employee_id,
    e.name_ar AS employee_name,
    ce.reminders,
    ce.is_recurring,
    ce.recurrence_pattern,
    ce.parent_event_id,
    ce.color,
    ce.category,
    cc.name_ar AS category_ar,
    ce.attendees,
    ce.location,
    ce.location_url,
    ce.source,
    ce.external_id,
    ce.status,
    ce.is_private,
    ce.created_at,
    ce.updated_at,
    -- حساب المدة بالدقائق
    EXTRACT(EPOCH FROM (ce.end_datetime - ce.start_datetime)) / 60 AS duration_minutes,
    -- عدد المشاركين
    COALESCE(jsonb_array_length(ce.attendees), 0) AS attendees_count
FROM calendar_events ce
LEFT JOIN tasks t ON ce.task_id = t.id
LEFT JOIN employees e ON ce.employee_id = e.id
LEFT JOIN calendar_categories cc ON ce.category = cc.name;

-- ═══════════════════════════════════════════════════════════════
-- View: أحداث اليوم
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW calendar_events_today AS
SELECT * FROM calendar_events_view
WHERE DATE(start_datetime) = CURRENT_DATE
   OR (is_all_day = TRUE AND DATE(start_datetime) <= CURRENT_DATE AND DATE(end_datetime) >= CURRENT_DATE)
ORDER BY start_datetime;

-- ═══════════════════════════════════════════════════════════════
-- View: أحداث الأسبوع الحالي
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW calendar_events_this_week AS
SELECT * FROM calendar_events_view
WHERE DATE(start_datetime) >= DATE_TRUNC('week', CURRENT_DATE)
  AND DATE(start_datetime) < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '7 days'
ORDER BY start_datetime;

-- ═══════════════════════════════════════════════════════════════
-- View: الأحداث القادمة (7 أيام)
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW calendar_events_upcoming AS
SELECT * FROM calendar_events_view
WHERE start_datetime >= NOW()
  AND start_datetime < NOW() + INTERVAL '7 days'
  AND status != 'cancelled'
ORDER BY start_datetime
LIMIT 20;

-- ═══════════════════════════════════════════════════════════════
-- Function: جلب أحداث نطاق تاريخ معين
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION get_events_in_range(
    p_start_date TIMESTAMP,
    p_end_date TIMESTAMP,
    p_category VARCHAR DEFAULT NULL,
    p_event_type VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    id INTEGER,
    title VARCHAR,
    description TEXT,
    event_type VARCHAR,
    start_datetime TIMESTAMP,
    end_datetime TIMESTAMP,
    is_all_day BOOLEAN,
    color VARCHAR,
    category VARCHAR,
    category_ar VARCHAR,
    task_id INTEGER,
    task_title VARCHAR,
    employee_id INTEGER,
    employee_name VARCHAR,
    location VARCHAR,
    status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cev.id,
        cev.title,
        cev.description,
        cev.event_type,
        cev.start_datetime,
        cev.end_datetime,
        cev.is_all_day,
        cev.color,
        cev.category,
        cev.category_ar,
        cev.task_id,
        cev.task_title,
        cev.employee_id,
        cev.employee_name,
        cev.location,
        cev.status
    FROM calendar_events_view cev
    WHERE (cev.start_datetime >= p_start_date AND cev.start_datetime < p_end_date)
       OR (cev.end_datetime > p_start_date AND cev.end_datetime <= p_end_date)
       OR (cev.start_datetime <= p_start_date AND cev.end_datetime >= p_end_date)
       AND (p_category IS NULL OR cev.category = p_category)
       AND (p_event_type IS NULL OR cev.event_type = p_event_type)
    ORDER BY cev.start_datetime;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════
-- Function: التحقق من التعارضات
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION check_event_conflicts(
    p_start_datetime TIMESTAMP,
    p_end_datetime TIMESTAMP,
    p_exclude_event_id INTEGER DEFAULT NULL
)
RETURNS TABLE (
    event_id INTEGER,
    event_title VARCHAR,
    event_start TIMESTAMP,
    event_end TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ce.id,
        ce.title,
        ce.start_datetime,
        ce.end_datetime
    FROM calendar_events ce
    WHERE ce.status != 'cancelled'
      AND ce.is_all_day = FALSE
      AND (p_exclude_event_id IS NULL OR ce.id != p_exclude_event_id)
      AND (
          (ce.start_datetime >= p_start_datetime AND ce.start_datetime < p_end_datetime)
          OR (ce.end_datetime > p_start_datetime AND ce.end_datetime <= p_end_datetime)
          OR (ce.start_datetime <= p_start_datetime AND ce.end_datetime >= p_end_datetime)
      )
    ORDER BY ce.start_datetime;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════
-- تعليقات للمبرمجين
-- ═══════════════════════════════════════════════════════════════
COMMENT ON TABLE calendar_events IS 'جدول الأحداث الرئيسي - يحتوي على كل الأحداث والمواعيد';
COMMENT ON TABLE calendar_categories IS 'تصنيفات التقويم - ألوان وتصنيفات الأحداث';
COMMENT ON TABLE public_holidays IS 'العطلات الرسمية - أيام الإجازات الرسمية';
COMMENT ON TABLE event_reminders IS 'تذكيرات الأحداث - التذكيرات المجدولة';
COMMENT ON TABLE event_attendees IS 'حضور الاجتماعات - المشاركون في الأحداث';
COMMENT ON TABLE calendar_settings IS 'إعدادات التقويم - تفضيلات المستخدم';
