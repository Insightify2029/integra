"""
Database Connection Configuration
=================================
Stores connection parameters.
"""

from core.config.database.db_host import DB_HOST
from core.config.database.db_port import DB_PORT
from core.config.database.db_name import DB_NAME
from core.config.database.db_user import DB_USER
from core.config.database.db_password import DB_PASSWORD


def get_connection_string():
    """Get PostgreSQL connection string."""
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_connection_params():
    """Get connection parameters as dictionary."""
    return {
        "host": DB_HOST,
        "port": DB_PORT,
        "database": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD
    }
