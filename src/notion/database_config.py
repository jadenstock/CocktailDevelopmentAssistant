"""
Database configuration system for abstract Notion database management.

This module provides the core configuration classes and types for defining
Notion databases in a generic, reusable way.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from enum import Enum


class NotionColumnType(Enum):
    """Supported Notion column types."""
    TITLE = "title"
    RICH_TEXT = "rich_text"
    MULTI_SELECT = "multi_select"
    SELECT = "select"
    CHECKBOX = "checkbox"
    NUMBER = "number"
    DATE = "date"
    FORMULA = "formula"
    RELATION = "relation"
    ROLLUP = "rollup"
    PEOPLE = "people"
    FILES = "files"
    URL = "url"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"


class PermissionType(Enum):
    """Permission types for database operations."""
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"


@dataclass
class FilterConfig:
    """Configuration for database filters."""
    column_name: str
    filter_type: str  # e.g., "equals", "contains", "greater_than", etc.
    value: Any
    description: Optional[str] = None


@dataclass
class ColumnConfig:
    """Configuration for a single database column."""
    name: str
    notion_type: NotionColumnType
    permission: PermissionType = PermissionType.READ
    description: Optional[str] = None
    required: bool = False
    
    # Type-specific configurations
    multi_select_options: Optional[List[str]] = None
    select_options: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate column configuration."""
        if self.notion_type == NotionColumnType.MULTI_SELECT and not self.multi_select_options:
            # Multi-select options can be discovered dynamically
            pass
        if self.notion_type == NotionColumnType.SELECT and not self.select_options:
            # Select options can be discovered dynamically
            pass


@dataclass
class DatabaseConfig:
    """Configuration for a complete Notion database."""
    name: str
    database_id: str
    description: Optional[str] = None
    columns: Dict[str, ColumnConfig] = field(default_factory=dict)
    filters: Dict[str, FilterConfig] = field(default_factory=dict)
    
    # Parsing configuration
    primary_key_column: str = "Name"  # Usually the title column
    
    def add_column(self, column: ColumnConfig) -> None:
        """Add a column configuration to the database."""
        self.columns[column.name] = column
    
    def add_filter(self, name: str, filter_config: FilterConfig) -> None:
        """Add a predefined filter configuration."""
        self.filters[name] = filter_config
    
    def get_readable_columns(self) -> List[ColumnConfig]:
        """Get all columns with read permissions."""
        return [
            col for col in self.columns.values()
            if col.permission in [PermissionType.READ, PermissionType.READ_WRITE]
        ]
    
    def get_writable_columns(self) -> List[ColumnConfig]:
        """Get all columns with write permissions."""
        return [
            col for col in self.columns.values()
            if col.permission in [PermissionType.WRITE, PermissionType.READ_WRITE]
        ]
    
    def get_column_by_name(self, name: str) -> Optional[ColumnConfig]:
        """Get a column configuration by name."""
        return self.columns.get(name)


@dataclass
class NotionDatabaseManager:
    """Manager for multiple Notion database configurations."""
    databases: Dict[str, DatabaseConfig] = field(default_factory=dict)
    
    def add_database(self, database: DatabaseConfig) -> None:
        """Add a database configuration."""
        self.databases[database.name] = database
    
    def get_database(self, name: str) -> Optional[DatabaseConfig]:
        """Get a database configuration by name."""
        return self.databases.get(name)
    
    def list_databases(self) -> List[str]:
        """List all configured database names."""
        return list(self.databases.keys())
    
    def get_database_by_id(self, database_id: str) -> Optional[DatabaseConfig]:
        """Get a database configuration by Notion database ID."""
        for db in self.databases.values():
            if db.database_id == database_id:
                return db
        return None