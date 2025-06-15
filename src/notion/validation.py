"""
Schema validation and error handling for the abstract Notion tools system.

This module provides validation for database configurations and runtime
error handling to ensure robust operation.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
from .database_config import (
    DatabaseConfig, 
    ColumnConfig, 
    FilterConfig, 
    NotionColumnType, 
    PermissionType,
    NotionDatabaseManager
)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class DatabaseConfigValidator:
    """Validates database configurations for correctness and completeness."""
    
    @staticmethod
    def validate_database_id(database_id: str) -> bool:
        """Validate that a database ID looks like a valid Notion database ID."""
        if not database_id or database_id in ["", "YOUR_DATABASE_ID"]:
            return False
        
        # Notion database IDs are typically 32 character hex strings with optional dashes
        # Allow placeholder values during development
        if database_id.upper() in ["BOTTLE_INVENTORY_NOTION_DB", "SYRUPS_AND_JUICES_NOTION_DB", 
                                   "COCKTAIL_PROJECTS_NOTION_DB", "WINES_NOTION_DB"]:
            return True
        
        # Check for actual Notion ID format (32 chars, alphanumeric + dashes)
        clean_id = database_id.replace('-', '')
        return len(clean_id) == 32 and clean_id.isalnum()
    
    @staticmethod
    def validate_column_config(column: ColumnConfig) -> List[str]:
        """Validate a single column configuration."""
        errors = []
        
        # Check column name
        if not column.name or not column.name.strip():
            errors.append("Column name cannot be empty")
        
        # Check for valid Notion column type
        if column.notion_type not in NotionColumnType:
            errors.append(f"Invalid column type: {column.notion_type}")
        
        # Check permission type
        if column.permission not in PermissionType:
            errors.append(f"Invalid permission type: {column.permission}")
        
        # Type-specific validations
        if column.notion_type == NotionColumnType.MULTI_SELECT:
            if column.multi_select_options is not None and not isinstance(column.multi_select_options, list):
                errors.append("multi_select_options must be a list")
        
        if column.notion_type == NotionColumnType.SELECT:
            if column.select_options is not None and not isinstance(column.select_options, list):
                errors.append("select_options must be a list")
        
        return errors
    
    @staticmethod
    def validate_filter_config(filter_config: FilterConfig) -> List[str]:
        """Validate a filter configuration."""
        errors = []
        
        # Check column name
        if not filter_config.column_name or not filter_config.column_name.strip():
            errors.append("Filter column_name cannot be empty")
        
        # Check filter type
        valid_filter_types = [
            "equals", "does_not_equal", "contains", "does_not_contain",
            "starts_with", "ends_with", "is_empty", "is_not_empty",
            "greater_than", "greater_than_or_equal_to", "less_than", 
            "less_than_or_equal_to", "on_or_after", "on_or_before",
            "past_week", "past_month", "past_year", "next_week", 
            "next_month", "next_year"
        ]
        
        if filter_config.filter_type not in valid_filter_types:
            errors.append(f"Invalid filter type: {filter_config.filter_type}")
        
        # Check value is provided when needed
        value_required_types = [
            "equals", "does_not_equal", "contains", "does_not_contain",
            "starts_with", "ends_with", "greater_than", "greater_than_or_equal_to",
            "less_than", "less_than_or_equal_to", "on_or_after", "on_or_before"
        ]
        
        if filter_config.filter_type in value_required_types and filter_config.value is None:
            errors.append(f"Filter type '{filter_config.filter_type}' requires a value")
        
        return errors
    
    @staticmethod
    def validate_database_config(database_config: DatabaseConfig) -> List[str]:
        """Validate a complete database configuration."""
        errors = []
        
        # Check database name
        if not database_config.name or not database_config.name.strip():
            errors.append("Database name cannot be empty")
        
        # Validate database ID
        if not DatabaseConfigValidator.validate_database_id(database_config.database_id):
            errors.append(f"Invalid database ID: {database_config.database_id}")
        
        # Check primary key column exists
        if database_config.primary_key_column not in database_config.columns:
            errors.append(f"Primary key column '{database_config.primary_key_column}' not found in columns")
        
        # Validate all columns
        for column_name, column_config in database_config.columns.items():
            column_errors = DatabaseConfigValidator.validate_column_config(column_config)
            for error in column_errors:
                errors.append(f"Column '{column_name}': {error}")
        
        # Validate all filters
        for filter_name, filter_config in database_config.filters.items():
            filter_errors = DatabaseConfigValidator.validate_filter_config(filter_config)
            for error in filter_errors:
                errors.append(f"Filter '{filter_name}': {error}")
            
            # Check that filter references an existing column
            if filter_config.column_name not in database_config.columns:
                errors.append(f"Filter '{filter_name}' references non-existent column '{filter_config.column_name}'")
        
        # Check for required columns
        has_title_column = any(
            col.notion_type == NotionColumnType.TITLE 
            for col in database_config.columns.values()
        )
        if not has_title_column:
            errors.append("Database must have at least one title column")
        
        return errors
    
    @staticmethod
    def validate_database_manager(manager: NotionDatabaseManager) -> Dict[str, List[str]]:
        """Validate all databases in a manager."""
        validation_results = {}
        
        for db_name, db_config in manager.databases.items():
            errors = DatabaseConfigValidator.validate_database_config(db_config)
            if errors:
                validation_results[db_name] = errors
        
        return validation_results


class RuntimeValidator:
    """Validates runtime operations and data."""
    
    @staticmethod
    def validate_query_data(data: Dict[str, Any], database_config: DatabaseConfig) -> List[str]:
        """Validate data for querying operations."""
        errors = []
        
        # Check that referenced columns exist
        for column_name in data.keys():
            if column_name not in database_config.columns:
                errors.append(f"Column '{column_name}' not found in database schema")
        
        return errors
    
    @staticmethod
    def validate_write_data(data: Dict[str, Any], database_config: DatabaseConfig) -> List[str]:
        """Validate data for write operations."""
        errors = []
        
        # Check required columns
        required_columns = [
            col.name for col in database_config.columns.values() 
            if col.required and col.permission in [PermissionType.WRITE, PermissionType.READ_WRITE]
        ]
        
        for required_col in required_columns:
            if required_col not in data or data[required_col] is None:
                errors.append(f"Required column '{required_col}' is missing")
        
        # Validate data types and permissions for each column
        for column_name, value in data.items():
            if column_name not in database_config.columns:
                errors.append(f"Column '{column_name}' not found in database schema")
                continue
            
            column_config = database_config.columns[column_name]
            
            # Check write permissions
            if column_config.permission not in [PermissionType.WRITE, PermissionType.READ_WRITE]:
                errors.append(f"Column '{column_name}' is not writable")
                continue
            
            # Type-specific validation
            type_errors = RuntimeValidator._validate_column_value(column_name, value, column_config)
            errors.extend(type_errors)
        
        return errors
    
    @staticmethod
    def _validate_column_value(column_name: str, value: Any, column_config: ColumnConfig) -> List[str]:
        """Validate a value for a specific column type."""
        errors = []
        
        if value is None:
            return errors  # None values are generally acceptable
        
        column_type = column_config.notion_type
        
        try:
            if column_type in [NotionColumnType.TITLE, NotionColumnType.RICH_TEXT, 
                              NotionColumnType.URL, NotionColumnType.EMAIL, 
                              NotionColumnType.PHONE_NUMBER]:
                if not isinstance(value, str):
                    errors.append(f"Column '{column_name}' expects string value, got {type(value).__name__}")
            
            elif column_type == NotionColumnType.NUMBER:
                if not isinstance(value, (int, float)):
                    errors.append(f"Column '{column_name}' expects number value, got {type(value).__name__}")
            
            elif column_type == NotionColumnType.CHECKBOX:
                if not isinstance(value, bool):
                    errors.append(f"Column '{column_name}' expects boolean value, got {type(value).__name__}")
            
            elif column_type in [NotionColumnType.MULTI_SELECT, NotionColumnType.SELECT]:
                if column_type == NotionColumnType.MULTI_SELECT:
                    if not isinstance(value, list):
                        errors.append(f"Column '{column_name}' expects list value, got {type(value).__name__}")
                    elif not all(isinstance(v, str) for v in value):
                        errors.append(f"Column '{column_name}' expects list of strings")
                else:  # SELECT
                    if not isinstance(value, str):
                        errors.append(f"Column '{column_name}' expects string value, got {type(value).__name__}")
            
            elif column_type == NotionColumnType.DATE:
                if not isinstance(value, str):
                    errors.append(f"Column '{column_name}' expects date string, got {type(value).__name__}")
                else:
                    # Basic date format validation (ISO format)
                    date_pattern = r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?)?$'
                    if not re.match(date_pattern, value):
                        errors.append(f"Column '{column_name}' expects ISO date format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
        
        except Exception as e:
            errors.append(f"Error validating column '{column_name}': {e}")
        
        return errors


def validate_configuration_file(config_path: str) -> Tuple[bool, List[str]]:
    """
    Validate a configuration file and return validation results.
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    try:
        from .config_loader import ConfigLoader
        manager = ConfigLoader.load_from_toml(config_path)
        
        validator = DatabaseConfigValidator()
        validation_results = validator.validate_database_manager(manager)
        
        if not validation_results:
            return True, []
        
        # Flatten error messages
        all_errors = []
        for db_name, errors in validation_results.items():
            for error in errors:
                all_errors.append(f"Database '{db_name}': {error}")
        
        return False, all_errors
    
    except Exception as e:
        return False, [f"Failed to load configuration: {e}"]


def create_validation_report(config_path: str) -> str:
    """Create a detailed validation report for a configuration file."""
    is_valid, errors = validate_configuration_file(config_path)
    
    report = f"# Configuration Validation Report\n\n"
    report += f"**Configuration File**: {config_path}\n"
    report += f"**Status**: {'✅ Valid' if is_valid else '❌ Invalid'}\n\n"
    
    if errors:
        report += f"## Validation Errors ({len(errors)})\n\n"
        for i, error in enumerate(errors, 1):
            report += f"{i}. {error}\n"
    else:
        report += "## ✅ All validations passed!\n\n"
        report += "Your configuration is ready to use.\n"
    
    return report


if __name__ == "__main__":
    # Test validation with the example configuration
    config_path = "etc/databases_config.toml"
    report = create_validation_report(config_path)
    print(report)