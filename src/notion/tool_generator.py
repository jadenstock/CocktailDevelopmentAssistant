"""
Dynamic tool generator for Notion databases - Fixed version without Pydantic issues.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from notion_client import Client
from agents import function_tool

from .database_config import DatabaseConfig, FilterConfig, NotionDatabaseManager, PermissionType
from .generic_query import GenericNotionQuery
from .generic_writer import GenericNotionWriter
from src.settings import NOTION_API_KEY


class NotionToolGenerator:
    """Generates function tools dynamically based on database configurations."""
    
    def __init__(self, database_manager: NotionDatabaseManager):
        self.database_manager = database_manager
        self.notion_client = Client(auth=NOTION_API_KEY)
        self.query_engine = GenericNotionQuery(self.notion_client, database_manager)
        self.writer_engine = GenericNotionWriter(self.notion_client, database_manager)
        self.generated_tools = {}
    
    def format_results(self, results: List[Dict[str, Any]], database_config: DatabaseConfig) -> str:
        """Format query results for display."""
        if not results:
            return "No results found"
        
        formatted_output = f"Found {len(results)} results:\n"
        
        for result in results:
            # Get the primary identifier
            primary_key = database_config.primary_key_column
            primary_value = result.get(primary_key, result.get('id', 'Unknown'))
            
            formatted_output += f"\n• {primary_value}"
            
            # Add key details from other columns
            for column_name, value in result.items():
                if column_name in ['id', 'url', primary_key] or value is None:
                    continue
                
                if isinstance(value, list) and value:
                    if len(value) == 1:
                        formatted_output += f"\n  {column_name}: {value[0]}"
                    else:
                        formatted_output += f"\n  {column_name}: {', '.join(str(v) for v in value)}"
                elif isinstance(value, bool):
                    if value:
                        formatted_output += f"\n  {column_name}: ✓"
                elif isinstance(value, (str, int, float)) and str(value).strip():
                    display_value = str(value)
                    if len(display_value) > 100:
                        display_value = display_value[:97] + "..."
                    formatted_output += f"\n  {column_name}: {display_value}"
        
        return formatted_output
    
    def generate_query_all_tool(self, database_config: DatabaseConfig) -> Callable:
        """Generate a tool to query all records from a database."""
        db_name = database_config.name
        
        async def tool_function() -> str:
            try:
                results = await asyncio.to_thread(
                    self.query_engine.get_all_rows,
                    db_name
                )
                return self.format_results(results, database_config)
            except Exception as e:
                return f"Error querying {db_name}: {e}"
        
        # Apply decorator and set metadata
        decorated = function_tool(tool_function)
        tool_name = f"get_all_{db_name}"
        
        # Store tool with metadata for retrieval
        return decorated
    
    def generate_search_tool(self, database_config: DatabaseConfig) -> Callable:
        """Generate a tool to search text across the database."""
        db_name = database_config.name
        
        async def tool_function(search_text: str) -> str:
            try:
                results = await asyncio.to_thread(
                    self.query_engine.search_by_text,
                    db_name,
                    search_text
                )
                return self.format_results(results, database_config)
            except Exception as e:
                return f"Error searching {db_name}: {e}"
        
        return function_tool(tool_function)
    
    def generate_filter_tool(self, database_config: DatabaseConfig, filter_name: str, filter_config: FilterConfig) -> Callable:
        """Generate a tool for a specific filter."""
        db_name = database_config.name
        
        async def tool_function() -> str:
            try:
                results = await asyncio.to_thread(
                    self.query_engine.query_database,
                    db_name,
                    filter_names=[filter_name]
                )
                return self.format_results(results, database_config)
            except Exception as e:
                return f"Error applying filter '{filter_name}' to {db_name}: {e}"
        
        return function_tool(tool_function)
    
    def generate_create_tool(self, database_config: DatabaseConfig) -> Optional[Callable]:
        """Generate a tool to create new records in a database."""
        writable_columns = database_config.get_writable_columns()
        if not writable_columns:
            return None
        
        db_name = database_config.name
        
        async def tool_function(**kwargs) -> str:
            try:
                # Validate required parameters
                required_params = [col.name for col in writable_columns if col.required]
                for param in required_params:
                    if param not in kwargs or kwargs[param] is None:
                        return f"Error: Required parameter '{param}' is missing"
                
                result = await asyncio.to_thread(
                    self.writer_engine.create_record,
                    db_name,
                    kwargs
                )
                return result
            except Exception as e:
                return f"Error creating record in {db_name}: {e}"
        
        return function_tool(tool_function)
    
    def generate_all_tools_for_database(self, database_config: DatabaseConfig) -> Dict[str, Callable]:
        """Generate all tools for a single database."""
        tools = {}
        db_name = database_config.name
        
        try:
            # Always generate query and search tools
            query_tool = self.generate_query_all_tool(database_config)
            tools[f"get_all_{db_name}"] = query_tool
            
            search_tool = self.generate_search_tool(database_config)
            tools[f"search_{db_name}"] = search_tool
            
            # Generate filter tools
            for filter_name, filter_config in database_config.filters.items():
                filter_tool = self.generate_filter_tool(database_config, filter_name, filter_config)
                tools[f"get_{db_name}_{filter_name}"] = filter_tool
            
            # Generate write tools if database has writable columns
            create_tool = self.generate_create_tool(database_config)
            if create_tool:
                tools[f"create_{db_name}_record"] = create_tool
            
        except Exception as e:
            print(f"Error generating tools for database '{db_name}': {e}")
        
        return tools
    
    def generate_all_tools(self) -> Dict[str, Callable]:
        """Generate all tools for all configured databases."""
        all_tools = {}
        
        for database_name, database_config in self.database_manager.databases.items():
            try:
                database_tools = self.generate_all_tools_for_database(database_config)
                all_tools.update(database_tools)
                print(f"Generated {len(database_tools)} tools for database '{database_name}'")
            except Exception as e:
                print(f"Error generating tools for database '{database_name}': {e}")
        
        self.generated_tools = all_tools
        return all_tools
    
    def list_available_tools(self) -> Dict[str, str]:
        """List all available tools with their descriptions."""
        if not self.generated_tools:
            self.generate_all_tools()
        
        return {
            name: getattr(tool, '__doc__', 'No description available')
            for name, tool in self.generated_tools.items()
        }