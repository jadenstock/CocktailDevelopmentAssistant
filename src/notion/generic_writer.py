"""
Generic writer for Notion databases using configurable schemas.

This module provides generic write functionality that works with any
configured Notion database based on the database configuration.
"""

from typing import Dict, List, Any, Optional
from notion_client import Client
from .database_config import (
    DatabaseConfig, 
    ColumnConfig, 
    NotionColumnType,
    NotionDatabaseManager,
    PermissionType
)


class NotionPropertyBuilder:
    """Builds Notion API property objects based on column configuration."""
    
    @staticmethod
    def build_title_property(value: str) -> Dict[str, Any]:
        """Build a title property."""
        return {"title": [{"text": {"content": str(value)}}]}
    
    @staticmethod
    def build_rich_text_property(value: str) -> Dict[str, Any]:
        """Build a rich text property."""
        return {"rich_text": [{"text": {"content": str(value)}}]}
    
    @staticmethod
    def build_multi_select_property(values: List[str]) -> Dict[str, Any]:
        """Build a multi-select property."""
        if isinstance(values, str):
            values = [values]
        return {"multi_select": [{"name": str(value)} for value in values]}
    
    @staticmethod
    def build_select_property(value: str) -> Dict[str, Any]:
        """Build a select property."""
        return {"select": {"name": str(value)}}
    
    @staticmethod
    def build_checkbox_property(value: bool) -> Dict[str, Any]:
        """Build a checkbox property."""
        return {"checkbox": bool(value)}
    
    @staticmethod
    def build_number_property(value: float) -> Dict[str, Any]:
        """Build a number property."""
        return {"number": float(value)}
    
    @staticmethod
    def build_date_property(value: str) -> Dict[str, Any]:
        """Build a date property."""
        return {"date": {"start": str(value)}}
    
    @staticmethod
    def build_people_property(values: List[Dict[str, str]]) -> Dict[str, Any]:
        """Build a people property."""
        return {"people": values}
    
    @staticmethod
    def build_url_property(value: str) -> Dict[str, Any]:
        """Build a URL property."""
        return {"url": str(value)}
    
    @staticmethod
    def build_email_property(value: str) -> Dict[str, Any]:
        """Build an email property."""
        return {"email": str(value)}
    
    @staticmethod
    def build_phone_property(value: str) -> Dict[str, Any]:
        """Build a phone number property."""
        return {"phone_number": str(value)}


class GenericNotionWriter:
    """Generic Notion database writer engine."""
    
    def __init__(self, notion_client: Client, database_manager: NotionDatabaseManager):
        self.notion_client = notion_client
        self.database_manager = database_manager
        self.property_builder = NotionPropertyBuilder()
    
    def build_properties(self, database_config: DatabaseConfig, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion properties object from data based on database configuration."""
        properties = {}
        
        for column_name, value in data.items():
            if value is None:
                continue
                
            column_config = database_config.get_column_by_name(column_name)
            if not column_config:
                print(f"Warning: Column '{column_name}' not found in database config")
                continue
            
            # Check if column is writable
            if column_config.permission not in [PermissionType.WRITE, PermissionType.READ_WRITE]:
                print(f"Warning: Column '{column_name}' is not writable")
                continue
            
            try:
                if column_config.notion_type == NotionColumnType.TITLE:
                    properties[column_name] = self.property_builder.build_title_property(value)
                elif column_config.notion_type == NotionColumnType.RICH_TEXT:
                    properties[column_name] = self.property_builder.build_rich_text_property(value)
                elif column_config.notion_type == NotionColumnType.MULTI_SELECT:
                    properties[column_name] = self.property_builder.build_multi_select_property(value)
                elif column_config.notion_type == NotionColumnType.SELECT:
                    properties[column_name] = self.property_builder.build_select_property(value)
                elif column_config.notion_type == NotionColumnType.CHECKBOX:
                    properties[column_name] = self.property_builder.build_checkbox_property(value)
                elif column_config.notion_type == NotionColumnType.NUMBER:
                    properties[column_name] = self.property_builder.build_number_property(value)
                elif column_config.notion_type == NotionColumnType.DATE:
                    properties[column_name] = self.property_builder.build_date_property(value)
                elif column_config.notion_type == NotionColumnType.PEOPLE:
                    properties[column_name] = self.property_builder.build_people_property(value)
                elif column_config.notion_type == NotionColumnType.URL:
                    properties[column_name] = self.property_builder.build_url_property(value)
                elif column_config.notion_type == NotionColumnType.EMAIL:
                    properties[column_name] = self.property_builder.build_email_property(value)
                elif column_config.notion_type == NotionColumnType.PHONE_NUMBER:
                    properties[column_name] = self.property_builder.build_phone_property(value)
                else:
                    print(f"Warning: Unsupported column type '{column_config.notion_type}' for column '{column_name}'")
                    
            except Exception as e:
                print(f"Error building property for column '{column_name}': {e}")
                continue
        
        return properties
    
    def create_record(self, database_name: str, data: Dict[str, Any]) -> str:
        """
        Create a new record in the specified database.
        
        Args:
            database_name: Name of the configured database
            data: Dictionary of column names and values
        
        Returns:
            Success or error message
        """
        database_config = self.database_manager.get_database(database_name)
        if not database_config:
            return f"Error: Database '{database_name}' not found in configuration"
        
        # Validate required columns
        required_columns = [col for col in database_config.columns.values() if col.required]
        for column in required_columns:
            if column.name not in data or data[column.name] is None:
                return f"Error: Required column '{column.name}' is missing"
        
        # Build properties
        properties = self.build_properties(database_config, data)
        if not properties:
            return "Error: No valid properties to create"
        
        try:
            response = self.notion_client.pages.create(
                parent={"database_id": database_config.database_id},
                properties=properties
            )
            
            # Get the primary key value for confirmation
            primary_key = database_config.primary_key_column
            primary_value = data.get(primary_key, "New record")
            
            return f"Successfully created '{primary_value}' in {database_name}"
            
        except Exception as e:
            return f"Error creating record in {database_name}: {e}"
    
    def update_record(self, database_name: str, record_id: str, data: Dict[str, Any]) -> str:
        """
        Update an existing record in the specified database.
        
        Args:
            database_name: Name of the configured database
            record_id: Notion page ID of the record to update
            data: Dictionary of column names and values to update
        
        Returns:
            Success or error message
        """
        database_config = self.database_manager.get_database(database_name)
        if not database_config:
            return f"Error: Database '{database_name}' not found in configuration"
        
        # Build properties for update
        properties = self.build_properties(database_config, data)
        if not properties:
            return "Error: No valid properties to update"
        
        try:
            response = self.notion_client.pages.update(
                page_id=record_id,
                properties=properties
            )
            
            return f"Successfully updated record in {database_name}"
            
        except Exception as e:
            return f"Error updating record in {database_name}: {e}"
    
    def delete_record(self, database_name: str, record_id: str) -> str:
        """
        Delete (archive) a record in the specified database.
        
        Args:
            database_name: Name of the configured database
            record_id: Notion page ID of the record to delete
        
        Returns:
            Success or error message
        """
        database_config = self.database_manager.get_database(database_name)
        if not database_config:
            return f"Error: Database '{database_name}' not found in configuration"
        
        try:
            response = self.notion_client.pages.update(
                page_id=record_id,
                archived=True
            )
            
            return f"Successfully deleted record from {database_name}"
            
        except Exception as e:
            return f"Error deleting record from {database_name}: {e}"
    
    def bulk_create_records(self, database_name: str, records: List[Dict[str, Any]]) -> str:
        """
        Create multiple records in the specified database.
        
        Args:
            database_name: Name of the configured database
            records: List of dictionaries containing record data
        
        Returns:
            Success or error message with count
        """
        database_config = self.database_manager.get_database(database_name)
        if not database_config:
            return f"Error: Database '{database_name}' not found in configuration"
        
        if not records:
            return "Error: No records provided"
        
        created_count = 0
        errors = []
        
        for i, record_data in enumerate(records):
            try:
                result = self.create_record(database_name, record_data)
                if result.startswith("Successfully"):
                    created_count += 1
                else:
                    errors.append(f"Record {i+1}: {result}")
            except Exception as e:
                errors.append(f"Record {i+1}: {e}")
        
        result_msg = f"Created {created_count} out of {len(records)} records in {database_name}"
        
        if errors:
            result_msg += f"\nErrors:\n" + "\n".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                result_msg += f"\n... and {len(errors) - 5} more errors"
        
        return result_msg