"""
Abstract Notion tools - the main entry point for the new configurable system.

This module provides the primary interface for loading configurations and
generating tools dynamically. It can be used as a drop-in replacement for
the existing notion_tools.py system.
"""

import os
from typing import Dict, List, Callable, Optional
from .config_loader import ConfigLoader
from .tool_generator import NotionToolGenerator
from .database_config import NotionDatabaseManager
from src.settings import NOTION_API_KEY


class AbstractNotionTools:
    """Main interface for the abstract Notion tools system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the abstract Notion tools system.
        
        Args:
            config_path: Path to the database configuration TOML file.
                        If None, will try to load from etc/databases_config.toml
                        or fall back to legacy configuration.
        """
        self.database_manager = None
        self.tool_generator = None
        self.tools = {}
        
        # Load configuration
        if config_path is None:
            config_path = "etc/databases_config.toml"
        
        if os.path.exists(config_path):
            try:
                self.database_manager = ConfigLoader.load_from_toml(config_path)
                print(f"Loaded database configuration from {config_path}")
            except Exception as e:
                print(f"Error loading config from {config_path}: {e}")
                print("Falling back to legacy configuration...")
                self.database_manager = ConfigLoader.create_legacy_config()
        else:
            print(f"Config file {config_path} not found. Using legacy configuration...")
            self.database_manager = ConfigLoader.create_legacy_config()
        
        # Replace placeholder database IDs with actual values from settings
        self._update_database_ids()
        
        # Initialize tool generator
        self.tool_generator = NotionToolGenerator(self.database_manager)
    
    def _update_database_ids(self):
        """Update database IDs from settings."""
        from src.settings import (
            BOTTLE_INVENTORY_NOTION_DB,
            SYRUPS_AND_JUICES_NOTION_DB,
            COCKTAIL_PROJECTS_NOTION_DB,
            WINES_NOTION_DB
        )
        
        # Map configuration database names to settings variables
        id_mapping = {
            "bottle_inventory": BOTTLE_INVENTORY_NOTION_DB,
            "syrups_and_juices": SYRUPS_AND_JUICES_NOTION_DB,
            "cocktail_projects": COCKTAIL_PROJECTS_NOTION_DB,
            "wines": WINES_NOTION_DB
        }
        
        for db_name, db_id in id_mapping.items():
            database_config = self.database_manager.get_database(db_name)
            if database_config:
                database_config.database_id = db_id
    
    def generate_all_tools(self) -> Dict[str, Callable]:
        """Generate all tools for all configured databases."""
        self.tools = self.tool_generator.generate_all_tools()
        return self.tools
    
    def get_tools_for_database(self, database_name: str) -> Dict[str, Callable]:
        """Get all tools for a specific database."""
        return self.tool_generator.get_tools_for_database(database_name)
    
    def get_tool(self, tool_name: str) -> Optional[Callable]:
        """Get a specific tool by name."""
        if not self.tools:
            self.generate_all_tools()
        return self.tools.get(tool_name)
    
    def list_databases(self) -> List[str]:
        """List all configured databases."""
        return self.database_manager.list_databases()
    
    def list_tools(self) -> Dict[str, str]:
        """List all available tools with descriptions."""
        return self.tool_generator.list_available_tools()
    
    def add_database_from_config(self, database_name: str, config_dict: Dict) -> None:
        """Add a new database configuration at runtime."""
        database_config = ConfigLoader.load_database_config(database_name, config_dict)
        self.database_manager.add_database(database_config)
        
        # Regenerate tools to include the new database
        self.tools.update(self.tool_generator.generate_all_tools_for_database(database_config))
    
    def get_legacy_compatible_tools(self) -> Dict[str, Callable]:
        """
        Get tools with names compatible with the legacy system.
        
        This method provides backward compatibility by returning tools
        with the same names as the original notion_tools.py functions.
        """
        if not self.tools:
            self.generate_all_tools()
        
        # Map new tool names to legacy names for backward compatibility
        legacy_mapping = {
            "get_all_bottle_inventory": "get_all_bottles_tool",
            "search_bottle_inventory": "query_bottles_by_name_tool",
            "search_bottle_inventory_by_type": "query_bottles_by_type_tool",
            "get_bottle_inventory_available": "get_available_types_tool",
            "get_all_syrups_and_juices": "get_available_ingredients_tool",
            "get_all_wines": "get_available_wines_tool",
            "create_cocktail_projects_record": "save_cocktail_to_notion_tool",
            "update_bottle_inventory_record": "update_notion_bottle_tool"
        }
        
        legacy_tools = {}
        for new_name, legacy_name in legacy_mapping.items():
            if new_name in self.tools:
                tool = self.tools[new_name]
                # Create a copy with the legacy name
                legacy_tool = tool
                legacy_tool.__name__ = legacy_name
                legacy_tools[legacy_name] = legacy_tool
        
        return legacy_tools


# Global instance for easy access
_notion_tools_instance = None


def get_notion_tools(config_path: Optional[str] = None) -> AbstractNotionTools:
    """Get the global AbstractNotionTools instance."""
    global _notion_tools_instance
    if _notion_tools_instance is None:
        _notion_tools_instance = AbstractNotionTools(config_path)
    return _notion_tools_instance


def get_all_tools(config_path: Optional[str] = None) -> Dict[str, Callable]:
    """Get all generated tools."""
    tools_instance = get_notion_tools(config_path)
    return tools_instance.generate_all_tools()


def get_legacy_tools(config_path: Optional[str] = None) -> Dict[str, Callable]:
    """Get tools with legacy-compatible names."""
    tools_instance = get_notion_tools(config_path)
    return tools_instance.get_legacy_compatible_tools()


# Example usage and testing
if __name__ == "__main__":
    # Initialize the system
    notion_tools = AbstractNotionTools()
    
    # List available databases
    print("Available databases:")
    for db_name in notion_tools.list_databases():
        print(f"  - {db_name}")
    
    # Generate all tools
    tools = notion_tools.generate_all_tools()
    print(f"\nGenerated {len(tools)} tools:")
    
    # List all tools
    tool_list = notion_tools.list_tools()
    for tool_name, description in tool_list.items():
        print(f"  - {tool_name}: {description}")
    
    # Example: Add a new database configuration at runtime
    fitness_config = {
        "database_id": "your_fitness_db_id_here",
        "description": "Personal fitness tracking database",
        "primary_key_column": "Date",
        "columns": {
            "Date": {
                "type": "date",
                "permission": "read_write",
                "description": "Workout date",
                "required": True
            },
            "Exercise": {
                "type": "title",
                "permission": "read_write",
                "description": "Exercise name",
                "required": True
            },
            "Duration": {
                "type": "number",
                "permission": "read_write",
                "description": "Duration in minutes"
            },
            "Completed": {
                "type": "checkbox",
                "permission": "read_write",
                "description": "Whether completed"
            }
        },
        "filters": {
            "completed": {
                "column_name": "Completed",
                "filter_type": "equals",
                "value": True,
                "description": "Completed workouts"
            }
        }
    }
    
    # Add the fitness database (commented out for now)
    # notion_tools.add_database_from_config("fitness_tracking", fitness_config)
    # print(f"\nAdded fitness database. Total tools: {len(notion_tools.tools)}")