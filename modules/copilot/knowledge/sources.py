"""
Knowledge Sources
=================
Different types of knowledge sources that can be indexed.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json
import os

from core.logging import app_logger


class SourceType(Enum):
    """Types of knowledge sources."""
    DOCUMENT = "document"
    DATABASE = "database"
    MODULE = "module"
    HELP = "help"
    SCHEMA = "schema"
    CONFIG = "config"
    USER_ACTION = "user_action"


@dataclass
class KnowledgeItem:
    """A single piece of indexed knowledge."""
    id: str
    source_type: SourceType
    title: str
    content: str
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    indexed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source_type": self.source_type.value,
            "title": self.title,
            "content": self.content,
            "keywords": self.keywords,
            "metadata": self.metadata,
            "indexed_at": self.indexed_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeItem':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            source_type=SourceType(data["source_type"]),
            title=data["title"],
            content=data["content"],
            keywords=data.get("keywords", []),
            metadata=data.get("metadata", {}),
            indexed_at=datetime.fromisoformat(data["indexed_at"]) if "indexed_at" in data else datetime.now()
        )


class KnowledgeSource(ABC):
    """Abstract base class for knowledge sources."""

    def __init__(self, source_id: str, name: str):
        self.source_id = source_id
        self.name = name
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    @abstractmethod
    def extract(self) -> List[KnowledgeItem]:
        """Extract knowledge items from the source."""
        pass

    @abstractmethod
    def get_source_type(self) -> SourceType:
        """Get the type of this source."""
        pass


class DocumentSource(KnowledgeSource):
    """Knowledge source from documents (markdown, text files)."""

    def __init__(self, source_id: str, name: str, base_path: str, extensions: List[str] = None):
        super().__init__(source_id, name)
        self.base_path = base_path
        self.extensions = extensions or [".md", ".txt"]

    def get_source_type(self) -> SourceType:
        return SourceType.DOCUMENT

    def extract(self) -> List[KnowledgeItem]:
        """Extract knowledge from document files."""
        items = []

        if not os.path.exists(self.base_path):
            return items

        for root, _, files in os.walk(self.base_path):
            for file in files:
                if any(file.endswith(ext) for ext in self.extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Extract title from first heading or filename
                        title = self._extract_title(content, file)
                        keywords = self._extract_keywords(content)

                        items.append(KnowledgeItem(
                            id=f"doc_{self.source_id}_{file}",
                            source_type=self.get_source_type(),
                            title=title,
                            content=content[:5000],  # Limit content size
                            keywords=keywords,
                            metadata={
                                "file_path": file_path,
                                "file_name": file,
                                "source": self.name
                            }
                        ))
                    except Exception as e:
                        app_logger.error(f"Failed to read document {file_path}: {e}")

        return items

    def _extract_title(self, content: str, filename: str) -> str:
        """Extract title from content or use filename."""
        lines = content.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            if line.startswith('## '):
                return line[3:].strip()
        return filename.replace('.md', '').replace('_', ' ').title()

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content."""
        keywords = []
        # Extract from headings
        for line in content.split('\n'):
            if line.startswith('#'):
                heading = line.lstrip('#').strip()
                keywords.extend(heading.lower().split())
        return list(set(keywords[:20]))


class DatabaseSource(KnowledgeSource):
    """Knowledge source from database schema and data patterns."""

    def __init__(self, source_id: str, name: str):
        super().__init__(source_id, name)

    def get_source_type(self) -> SourceType:
        return SourceType.DATABASE

    def extract(self) -> List[KnowledgeItem]:
        """Extract knowledge from database schema."""
        items = []

        try:
            from core.database import select_all

            # Extract table information
            tables_info = self._get_tables_info()

            for table_name, columns in tables_info.items():
                content = self._format_table_doc(table_name, columns)
                items.append(KnowledgeItem(
                    id=f"db_table_{table_name}",
                    source_type=self.get_source_type(),
                    title=f"جدول {table_name}",
                    content=content,
                    keywords=[table_name, "جدول", "قاعدة بيانات", "database"] + [c["name"] for c in columns],
                    metadata={
                        "table_name": table_name,
                        "column_count": len(columns),
                        "source": "database_schema"
                    }
                ))
        except Exception as e:
            app_logger.error(f"Failed to extract database schema knowledge: {e}")

        return items

    def _get_tables_info(self) -> Dict[str, List[Dict]]:
        """Get information about database tables."""
        from core.database import select_all

        tables = {}

        # Get table names
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """
        try:
            _, rows = select_all(query)

            for row in rows:
                table_name = row[0]
                # Get columns for each table
                col_query = """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """
                _, col_rows = select_all(col_query, (table_name,))

                tables[table_name] = [
                    {"name": r[0], "type": r[1], "nullable": r[2]}
                    for r in col_rows
                ]
        except Exception as e:
            app_logger.error(f"Failed to get tables info: {e}")

        return tables

    def _format_table_doc(self, table_name: str, columns: List[Dict]) -> str:
        """Format table documentation."""
        doc = f"# جدول {table_name}\n\n"
        doc += "## الأعمدة:\n"
        for col in columns:
            nullable = "اختياري" if col["nullable"] == "YES" else "مطلوب"
            doc += f"- **{col['name']}**: {col['type']} ({nullable})\n"
        return doc


class ModuleSource(KnowledgeSource):
    """Knowledge source from application modules."""

    def __init__(self, source_id: str, name: str):
        super().__init__(source_id, name)

    def get_source_type(self) -> SourceType:
        return SourceType.MODULE

    def extract(self) -> List[KnowledgeItem]:
        """Extract knowledge from application modules."""
        items = []

        try:
            from core.config.modules.modules_list import get_all_modules

            for module in get_all_modules():
                content = self._format_module_doc(module)
                items.append(KnowledgeItem(
                    id=f"module_{module['id']}",
                    source_type=self.get_source_type(),
                    title=f"موديول {module['name_ar']}",
                    content=content,
                    keywords=[
                        module['id'],
                        module['name_ar'],
                        module['name_en'],
                        "موديول",
                        "module"
                    ],
                    metadata={
                        "module_id": module['id'],
                        "color": module['color'],
                        "enabled": module['enabled'],
                        "source": "modules"
                    }
                ))
        except Exception as e:
            app_logger.error(f"Failed to extract module knowledge: {e}")

        return items

    def _format_module_doc(self, module: Dict) -> str:
        """Format module documentation."""
        status = "مفعل" if module['enabled'] else "معطل"
        doc = f"# {module['name_ar']} ({module['name_en']})\n\n"
        doc += f"- **المعرف**: {module['id']}\n"
        doc += f"- **الحالة**: {status}\n"
        doc += f"- **اللون**: {module['color']}\n"
        return doc


class HelpSource(KnowledgeSource):
    """Knowledge source from help documentation."""

    HELP_CONTENT = {
        "employees": {
            "title": "إدارة الموظفين",
            "content": """
# إدارة الموظفين

## الوظائف المتاحة:
- **عرض الموظفين**: عرض قائمة بجميع الموظفين مع إمكانية البحث والفلترة
- **إضافة موظف**: إضافة موظف جديد مع كافة البيانات
- **تعديل موظف**: تعديل بيانات موظف موجود
- **حذف موظف**: حذف موظف من النظام

## البيانات المطلوبة:
- الاسم الكامل
- رقم الهوية
- الشركة والقسم
- المسمى الوظيفي
- الراتب والبدلات
- تاريخ التعيين

## نصائح:
- استخدم البحث السريع للوصول للموظف المطلوب
- يمكنك تصدير البيانات إلى Excel
- احرص على تحديث البيانات بشكل دوري
            """,
            "keywords": ["موظف", "موظفين", "إضافة", "تعديل", "حذف", "employee"]
        },
        "reports": {
            "title": "التقارير",
            "content": """
# التقارير

## أنواع التقارير:
- **تقرير الموظفين**: قائمة شاملة بجميع الموظفين
- **تقرير الرواتب**: ملخص الرواتب والبدلات
- **تقرير الحضور**: سجل الحضور والانصراف
- **تقرير الإجازات**: ملخص الإجازات المستخدمة

## التصدير:
- PDF: للطباعة والأرشفة
- Excel: للتحليل والتعديل
- Word: للتقارير الرسمية
            """,
            "keywords": ["تقرير", "تقارير", "طباعة", "تصدير", "report"]
        },
        "ai_assistant": {
            "title": "المساعد الذكي",
            "content": """
# المساعد الذكي

## الإمكانيات:
- **الأسئلة والأجوبة**: اسأل عن أي شيء في النظام
- **تحليل البيانات**: تحليل ذكي للبيانات واكتشاف الأنماط
- **اقتراحات**: اقتراحات لتحسين العمل
- **تنفيذ المهام**: تنفيذ مهام بأوامر طبيعية

## أمثلة:
- "أظهر لي الموظفين في قسم المبيعات"
- "ما هو متوسط الرواتب؟"
- "أضف موظف جديد اسمه أحمد"
- "أرسل تقرير الشهر للمدير"
            """,
            "keywords": ["مساعد", "ذكي", "AI", "سؤال", "تحليل", "copilot"]
        }
    }

    def __init__(self, source_id: str, name: str):
        super().__init__(source_id, name)

    def get_source_type(self) -> SourceType:
        return SourceType.HELP

    def extract(self) -> List[KnowledgeItem]:
        """Extract knowledge from help content."""
        items = []

        for help_id, help_data in self.HELP_CONTENT.items():
            items.append(KnowledgeItem(
                id=f"help_{help_id}",
                source_type=self.get_source_type(),
                title=help_data["title"],
                content=help_data["content"],
                keywords=help_data["keywords"],
                metadata={
                    "help_id": help_id,
                    "source": "help"
                }
            ))

        return items
