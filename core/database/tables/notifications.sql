-- ============================================================
-- INTEGRA - Notifications Table
-- المحور J: نظام الإشعارات الذكي
-- تاريخ الإنشاء: 4 فبراير 2026
-- ============================================================

-- جدول الإشعارات الرئيسي
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,

    -- المحتوى
    title VARCHAR(500) NOT NULL,
    body TEXT,

    -- التصنيف
    notification_type VARCHAR(50) NOT NULL DEFAULT 'system',
    -- أنواع الإشعارات: email, task, calendar, system, ai, alert

    -- الأولوية
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    -- الأولويات: urgent, high, normal, low

    -- المصدر
    source_module VARCHAR(100),  -- الموديول المصدر (mostahaqat, email, tasks, etc.)
    source_id INTEGER,           -- معرف السجل المصدر
    source_type VARCHAR(100),    -- نوع السجل (employee, email, task, etc.)

    -- الحالة
    is_read BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    is_pinned BOOLEAN DEFAULT FALSE,

    -- الإجراءات المتاحة (JSON array)
    -- مثال: [{"id": "open", "label": "فتح", "action": "navigate", "params": {"module": "email", "id": 123}}]
    actions JSONB DEFAULT '[]'::jsonb,

    -- البيانات الإضافية (JSON)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- AI Analysis
    ai_priority_score DECIMAL(3,2),  -- 0.00 - 1.00
    ai_category VARCHAR(100),
    ai_suggested_action VARCHAR(255),

    -- المستخدم المستهدف
    user_id INTEGER,

    -- التواريخ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,

    -- للحذف الناعم
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- فهارس للأداء
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_priority ON notifications(priority);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_source ON notifications(source_module, source_id);

-- فهرس مركب للاستعلامات الشائعة
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread
    ON notifications(user_id, is_read, created_at DESC)
    WHERE deleted_at IS NULL AND is_archived = FALSE;

-- ============================================================
-- جدول إعدادات الإشعارات للمستخدمين
-- ============================================================

CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE,

    -- إعدادات عامة
    notifications_enabled BOOLEAN DEFAULT TRUE,
    sound_enabled BOOLEAN DEFAULT TRUE,
    desktop_notifications BOOLEAN DEFAULT TRUE,

    -- فلترة حسب النوع
    email_notifications BOOLEAN DEFAULT TRUE,
    task_notifications BOOLEAN DEFAULT TRUE,
    calendar_notifications BOOLEAN DEFAULT TRUE,
    system_notifications BOOLEAN DEFAULT TRUE,
    ai_notifications BOOLEAN DEFAULT TRUE,

    -- فلترة حسب الأولوية
    show_low_priority BOOLEAN DEFAULT TRUE,
    show_normal_priority BOOLEAN DEFAULT TRUE,
    show_high_priority BOOLEAN DEFAULT TRUE,
    show_urgent_priority BOOLEAN DEFAULT TRUE,

    -- وضع التركيز (Do Not Disturb)
    focus_mode_enabled BOOLEAN DEFAULT FALSE,
    focus_mode_start TIME,
    focus_mode_end TIME,
    focus_mode_allow_urgent BOOLEAN DEFAULT TRUE,

    -- الأصوات
    sound_file VARCHAR(255) DEFAULT 'default',

    -- التنظيف التلقائي
    auto_archive_days INTEGER DEFAULT 30,
    auto_delete_days INTEGER DEFAULT 90,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- جدول سجل الإجراءات على الإشعارات
-- ============================================================

CREATE TABLE IF NOT EXISTS notification_actions_log (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER REFERENCES notifications(id) ON DELETE CASCADE,
    user_id INTEGER,
    action_type VARCHAR(50) NOT NULL,  -- read, archive, delete, action_click, dismiss
    action_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notification_actions_notification_id
    ON notification_actions_log(notification_id);

-- ============================================================
-- دوال مساعدة
-- ============================================================

-- دالة لحساب عدد الإشعارات غير المقروءة
CREATE OR REPLACE FUNCTION get_unread_notification_count(p_user_id INTEGER DEFAULT NULL)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM notifications
        WHERE is_read = FALSE
          AND is_archived = FALSE
          AND deleted_at IS NULL
          AND (p_user_id IS NULL OR user_id = p_user_id OR user_id IS NULL)
    );
END;
$$ LANGUAGE plpgsql;

-- دالة لتحديد كل الإشعارات كمقروءة
CREATE OR REPLACE FUNCTION mark_all_notifications_read(p_user_id INTEGER DEFAULT NULL)
RETURNS INTEGER AS $$
DECLARE
    affected_count INTEGER;
BEGIN
    UPDATE notifications
    SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
    WHERE is_read = FALSE
      AND deleted_at IS NULL
      AND (p_user_id IS NULL OR user_id = p_user_id OR user_id IS NULL);

    GET DIAGNOSTICS affected_count = ROW_COUNT;
    RETURN affected_count;
END;
$$ LANGUAGE plpgsql;

-- دالة لأرشفة الإشعارات القديمة
CREATE OR REPLACE FUNCTION archive_old_notifications(days_old INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    affected_count INTEGER;
BEGIN
    UPDATE notifications
    SET is_archived = TRUE
    WHERE is_archived = FALSE
      AND is_read = TRUE
      AND created_at < (CURRENT_TIMESTAMP - (days_old || ' days')::INTERVAL)
      AND deleted_at IS NULL;

    GET DIAGNOSTICS affected_count = ROW_COUNT;
    RETURN affected_count;
END;
$$ LANGUAGE plpgsql;

-- دالة لحذف الإشعارات المنتهية الصلاحية
CREATE OR REPLACE FUNCTION cleanup_expired_notifications()
RETURNS INTEGER AS $$
DECLARE
    affected_count INTEGER;
BEGIN
    UPDATE notifications
    SET deleted_at = CURRENT_TIMESTAMP
    WHERE deleted_at IS NULL
      AND expires_at IS NOT NULL
      AND expires_at < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS affected_count = ROW_COUNT;
    RETURN affected_count;
END;
$$ LANGUAGE plpgsql;
