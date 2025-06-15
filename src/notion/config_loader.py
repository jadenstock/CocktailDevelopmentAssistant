"""
Configuration loader for Notion databases from TOML files.

This module handles loading database configurations from TOML files and
creating the appropriate DatabaseConfig objects.
"""

import toml
from typing import Dict, Any, Optional
from .database_config import (
    DatabaseConfig, 
    ColumnConfig, 
    FilterConfig, 
    NotionColumnType, 
    PermissionType,
    NotionDatabaseManager
)


class ConfigLoader:
    """Loads Notion database configurations from TOML files."""
    
    @staticmethod
    def _parse_column_type(type_str: str) -> NotionColumnType:
        """Parse column type string to NotionColumnType enum."""
        try:
            return NotionColumnType(type_str.lower())
        except ValueError:
            raise ValueError(f"Unsupported column type: {type_str}")
    
    @staticmethod
    def _parse_permission(permission_str: str) -> PermissionType:
        """Parse permission string to PermissionType enum."""
        try:
            return PermissionType(permission_str.lower())
        except ValueError:
            raise ValueError(f"Unsupported permission type: {permission_str}")
    
    @staticmethod
    def _create_column_config(name: str, column_data: Dict[str, Any]) -> ColumnConfig:
        """Create a ColumnConfig from dictionary data."""
        column_type = ConfigLoader._parse_column_type(column_data.get("type", "rich_text"))
        permission = ConfigLoader._parse_permission(column_data.get("permission", "read"))
        
        return ColumnConfig(
            name=name,
            notion_type=column_type,
            permission=permission,
            description=column_data.get("description"),
            required=column_data.get("required", False),
            multi_select_options=column_data.get("multi_select_options"),
            select_options=column_data.get("select_options")
        )
    
    @staticmethod
    def _create_filter_config(filter_data: Dict[str, Any]) -> FilterConfig:
        """Create a FilterConfig from dictionary data."""
        return FilterConfig(
            column_name=filter_data["column_name"],
            filter_type=filter_data["filter_type"],
            value=filter_data["value"],
            description=filter_data.get("description")
        )
    
    @staticmethod
    def load_database_config(name: str, config_data: Dict[str, Any]) -> DatabaseConfig:
        """Load a single database configuration from dictionary data."""
        database_config = DatabaseConfig(
            name=name,
            database_id=config_data["database_id"],
            description=config_data.get("description"),
            primary_key_column=config_data.get("primary_key_column", "Name")
        )
        
        # Load columns
        columns_data = config_data.get("columns", {})
        for column_name, column_info in columns_data.items():
            column_config = ConfigLoader._create_column_config(column_name, column_info)
            database_config.add_column(column_config)
        
        # Load filters
        filters_data = config_data.get("filters", {})
        for filter_name, filter_info in filters_data.items():
            filter_config = ConfigLoader._create_filter_config(filter_info)
            database_config.add_filter(filter_name, filter_config)
        
        return database_config
    
    @staticmethod
    def load_from_toml(config_path: str) -> NotionDatabaseManager:
        """Load all database configurations from a TOML file."""
        try:
            config_data = toml.load(config_path)
        except Exception as e:
            raise ValueError(f"Failed to load TOML config: {e}")
        
        manager = NotionDatabaseManager()
        
        # Load databases from the 'databases' section
        databases_config = config_data.get("databases", {})
        for db_name, db_config in databases_config.items():
            try:
                database = ConfigLoader.load_database_config(db_name, db_config)
                manager.add_database(database)
            except Exception as e:
                print(f"Warning: Failed to load database '{db_name}': {e}")
                continue
        
        return manager
    
    @staticmethod
    def create_legacy_config() -> NotionDatabaseManager:
        """Create configuration for existing legacy databases."""
        manager = NotionDatabaseManager()
        
        # Bottle Inventory Database
        bottle_db = DatabaseConfig(
            name="bottle_inventory",
            database_id="BOTTLE_INVENTORY_NOTION_DB",  # Will be replaced with actual ID
            description="Cocktail bottle inventory database",
            primary_key_column="Name"
        )
        
        # Add bottle inventory columns
        bottle_db.add_column(ColumnConfig("Name", NotionColumnType.TITLE, PermissionType.READ_WRITE))
        bottle_db.add_column(ColumnConfig("Type", NotionColumnType.MULTI_SELECT, PermissionType.READ_WRITE))
        bottle_db.add_column(ColumnConfig("Notes", NotionColumnType.RICH_TEXT, PermissionType.READ_WRITE))
        bottle_db.add_column(ColumnConfig("Technical Notes", NotionColumnType.RICH_TEXT, PermissionType.READ_WRITE))
        bottle_db.add_column(ColumnConfig("almost_gone", NotionColumnType.CHECKBOX, PermissionType.READ_WRITE))
        bottle_db.add_column(ColumnConfig("not_for_mixing", NotionColumnType.CHECKBOX, PermissionType.READ_WRITE))
        
        # Add common filters
        bottle_db.add_filter("available", FilterConfig("almost_gone", "equals", False, "Bottles that are not almost gone"))
        bottle_db.add_filter("for_mixing", FilterConfig("not_for_mixing", "equals", False, "Bottles suitable for mixing"))
        
        manager.add_database(bottle_db)
        
        # Syrups and Juices Database
        syrups_db = DatabaseConfig(
            name="syrups_and_juices",
            database_id="SYRUPS_AND_JUICES_NOTION_DB",
            description="Syrups and juices inventory database"
        )
        
        syrups_db.add_column(ColumnConfig("Name", NotionColumnType.TITLE, PermissionType.READ_WRITE))
        syrups_db.add_column(ColumnConfig("Have", NotionColumnType.CHECKBOX, PermissionType.READ_WRITE))
        
        syrups_db.add_filter("available", FilterConfig("Have", "equals", True, "Ingredients we currently have"))
        
        manager.add_database(syrups_db)
        
        # Cocktail Projects Database
        cocktails_db = DatabaseConfig(
            name="cocktail_projects",
            database_id="COCKTAIL_PROJECTS_NOTION_DB",
            description="Cocktail projects and recipes database"
        )
        
        cocktails_db.add_column(ColumnConfig("Name", NotionColumnType.TITLE, PermissionType.READ_WRITE))
        cocktails_db.add_column(ColumnConfig("Spec", NotionColumnType.RICH_TEXT, PermissionType.READ_WRITE))
        cocktails_db.add_column(ColumnConfig("Tags", NotionColumnType.MULTI_SELECT, PermissionType.READ_WRITE))
        cocktails_db.add_column(ColumnConfig("Preference", NotionColumnType.NUMBER, PermissionType.READ_WRITE))
        cocktails_db.add_column(ColumnConfig("Notes", NotionColumnType.RICH_TEXT, PermissionType.READ_WRITE))
        
        manager.add_database(cocktails_db)
        
        # Wine Database
        wine_db = DatabaseConfig(
            name="wines",
            database_id="WINES_NOTION_DB",
            description="Wine inventory database"
        )
        
        wine_db.add_column(ColumnConfig("Name", NotionColumnType.TITLE, PermissionType.READ_WRITE))
        wine_db.add_column(ColumnConfig("Notes", NotionColumnType.RICH_TEXT, PermissionType.READ_WRITE))
        wine_db.add_column(ColumnConfig("Technical Notes", NotionColumnType.RICH_TEXT, PermissionType.READ_WRITE))
        wine_db.add_column(ColumnConfig("Vintage Year", NotionColumnType.NUMBER, PermissionType.READ_WRITE))
        wine_db.add_column(ColumnConfig("Cellar", NotionColumnType.CHECKBOX, PermissionType.READ_WRITE))
        wine_db.add_column(ColumnConfig("Drank", NotionColumnType.CHECKBOX, PermissionType.READ_WRITE))
        
        wine_db.add_filter("available", FilterConfig("Cellar", "equals", False, "Wines not in cellar"))
        wine_db.add_filter("not_drank", FilterConfig("Drank", "equals", False, "Wines not yet consumed"))
        
        manager.add_database(wine_db)
        
        return manager