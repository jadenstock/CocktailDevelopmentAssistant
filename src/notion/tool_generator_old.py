"""
Dynamic tool generator for Notion databases.

This module automatically generates function tools based on database configurations,
eliminating the need to manually create tools for each database operation.
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
    
    def _create_tool(self, func: Callable, tool_name: str, description: str) -> Callable:
        """Helper to create a properly decorated function tool."""
        func.__name__ = tool_name
        func.__doc__ = description
        
        # Apply the function_tool decorator
        decorated_tool = function_tool(func)
        
        # Preserve the name and doc after decoration
        try:
            decorated_tool.__name__ = tool_name
            decorated_tool.__doc__ = description
        except AttributeError:
            # Some decorators create read-only objects, that's okay
            pass
        
        return decorated_tool
    
    def format_results(self, results: List[Dict[str, Any]], database_config: DatabaseConfig) -> str:
        """Format query results for display."""
        if not results:
            return "No results found"
        
        formatted_output = f"Found {len(results)} results:\n"
        
        for result in results:
            # Get the primary identifier (usually Name or title column)
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
                    if value:  # Only show True values to reduce clutter
                        formatted_output += f"\n  {column_name}: ✓"
                elif isinstance(value, (str, int, float)) and str(value).strip():
                    # Truncate long text
                    display_value = str(value)
                    if len(display_value) > 100:
                        display_value = display_value[:97] + "..."
                    formatted_output += f"\n  {column_name}: {display_value}"
        
        return formatted_output
    
    def generate_query_all_tool(self, database_config: DatabaseConfig) -> Callable:
        """Generate a tool to query all records from a database."""
        
        async def query_all_tool() -> str:
            """Get all records from the database."""
            try:
                results = await asyncio.to_thread(
                    self.query_engine.get_all_rows,
                    database_config.name
                )
                return self.format_results(results, database_config)
            except Exception as e:
                return f"Error querying {database_config.name}: {e}"
        
        # Create and return the decorated tool
        tool_name = f"get_all_{database_config.name}"
        description = f"Get all records from the {database_config.description or database_config.name} database."
        
        return self._create_tool(query_all_tool, tool_name, description)
    
    def generate_search_tool(self, database_config: DatabaseConfig) -> Callable:
        """Generate a tool to search text across the database."""
        
        async def search_tool(search_text: str) -> str:
            """Search for text across the database."""
            try:
                results = await asyncio.to_thread(
                    self.query_engine.search_by_text,
                    database_config.name,
                    search_text
                )
                return self.format_results(results, database_config)
            except Exception as e:
                return f"Error searching {database_config.name}: {e}"
        
        tool_name = f"search_{database_config.name}"
        description = f"Search for text across the {database_config.description or database_config.name} database."
        
        return self._create_tool(search_tool, tool_name, description)
    
    def generate_filter_tools(self, database_config: DatabaseConfig) -> List[Callable]:
        """Generate tools for predefined filters."""
        tools = []
        
        for filter_name, filter_config in database_config.filters.items():
            
            @function_tool
            async def filter_tool() -> str:
                f"""Query {database_config.name} using the '{filter_name}' filter: {filter_config.description}"""
                try:
                    results = await asyncio.to_thread(
                        self.query_engine.query_database,
                        database_config.name,
                        filter_names=[filter_name]
                    )
                    return self.format_results(results, database_config)
                except Exception as e:
                    return f"Error applying filter '{filter_name}' to {database_config.name}: {e}"
            
            # Set dynamic name and docstring
            tool_name = f"get_{database_config.name}_{filter_name}"
            filter_tool.__name__ = tool_name
            filter_tool.__doc__ = f"Query {database_config.name} using the '{filter_name}' filter: {filter_config.description}"
            
            tools.append(filter_tool)
        
        return tools
    
    def generate_column_search_tools(self, database_config: DatabaseConfig) -> List[Callable]:
        """Generate tools for searching specific columns."""
        tools = []
        
        # Generate tools for multi-select and select columns
        for column_name, column_config in database_config.columns.items():
            if column_config.notion_type.value in ['multi_select', 'select'] and column_config.permission != PermissionType.WRITE:
                
                @function_tool
                async def column_search_tool(search_value: str) -> str:
                    f"""Search {database_config.name} by {column_name} containing the specified value."""
                    try:
                        custom_filter = FilterConfig(
                            column_name=column_name,
                            filter_type="contains",
                            value=search_value,
                            description=f"Search {column_name} for {search_value}"
                        )
                        results = await asyncio.to_thread(
                            self.query_engine.query_database,
                            database_config.name,
                            custom_filters=[custom_filter]
                        )
                        return self.format_results(results, database_config)
                    except Exception as e:
                        return f"Error searching {column_name} in {database_config.name}: {e}"
                
                # Set dynamic name and docstring
                tool_name = f"search_{database_config.name}_by_{column_name.lower().replace(' ', '_')}"
                column_search_tool.__name__ = tool_name
                column_search_tool.__doc__ = f"Search {database_config.name} by {column_name} containing the specified value."
                
                tools.append(column_search_tool)
        
        return tools
    
    def generate_create_tool(self, database_config: DatabaseConfig) -> Optional[Callable]:
        """Generate a tool to create new records in a database."""
        writable_columns = database_config.get_writable_columns()
        if not writable_columns:
            return None
        
        # Build function signature dynamically
        required_params = [col.name for col in writable_columns if col.required]
        optional_params = [col.name for col in writable_columns if not col.required]
        
        @function_tool
        async def create_tool(**kwargs) -> str:
            f"""Create a new record in the {database_config.description or database_config.name} database."""
            try:
                # Validate required parameters
                for param in required_params:
                    if param not in kwargs or kwargs[param] is None:
                        return f"Error: Required parameter '{param}' is missing"
                
                result = await asyncio.to_thread(
                    self.writer_engine.create_record,
                    database_config.name,
                    kwargs
                )
                return result
            except Exception as e:
                return f"Error creating record in {database_config.name}: {e}"
        
        # Set dynamic name and docstring
        tool_name = f"create_{database_config.name}_record"
        create_tool.__name__ = tool_name
        
        # Build dynamic docstring with parameter info
        param_info = []
        for col in writable_columns:
            param_desc = f"{col.name} ({col.notion_type.value})"
            if col.required:
                param_desc += " [REQUIRED]"
            if col.description:
                param_desc += f": {col.description}"
            param_info.append(param_desc)
        
        create_tool.__doc__ = f"""Create a new record in the {database_config.description or database_config.name} database.
        
        Parameters:
        {chr(10).join(f'  - {info}' for info in param_info)}
        """
        
        return create_tool
    
    def generate_update_tool(self, database_config: DatabaseConfig) -> Optional[Callable]:
        """Generate a tool to update records in a database."""
        writable_columns = database_config.get_writable_columns()
        if not writable_columns:
            return None
        
        @function_tool
        async def update_tool(record_id: str, **kwargs) -> str:
            f"""Update a record in the {database_config.description or database_config.name} database."""
            try:
                result = await asyncio.to_thread(
                    self.writer_engine.update_record,
                    database_config.name,
                    record_id,
                    kwargs
                )
                return result
            except Exception as e:
                return f"Error updating record in {database_config.name}: {e}"
        
        # Set dynamic name and docstring
        tool_name = f"update_{database_config.name}_record"
        update_tool.__name__ = tool_name
        update_tool.__doc__ = f"Update a record in the {database_config.description or database_config.name} database by record ID."
        
        return update_tool
    
    def generate_all_tools_for_database(self, database_config: DatabaseConfig) -> Dict[str, Callable]:
        """Generate all tools for a single database."""
        tools = {}
        
        # Always generate query and search tools
        tools[f"get_all_{database_config.name}"] = self.generate_query_all_tool(database_config)
        tools[f"search_{database_config.name}"] = self.generate_search_tool(database_config)
        
        # Generate filter tools
        filter_tools = self.generate_filter_tools(database_config)
        for tool in filter_tools:
            tools[tool.__name__] = tool
        
        # Generate column search tools
        column_tools = self.generate_column_search_tools(database_config)
        for tool in column_tools:
            tools[tool.__name__] = tool
        
        # Generate write tools if database has writable columns
        create_tool = self.generate_create_tool(database_config)
        if create_tool:
            tools[create_tool.__name__] = create_tool
        
        update_tool = self.generate_update_tool(database_config)
        if update_tool:
            tools[update_tool.__name__] = update_tool
        
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
    
    def get_tools_for_database(self, database_name: str) -> Dict[str, Callable]:
        """Get all tools for a specific database."""
        database_config = self.database_manager.get_database(database_name)
        if not database_config:
            raise ValueError(f"Database '{database_name}' not found")
        
        return self.generate_all_tools_for_database(database_config)
    
    def list_available_tools(self) -> Dict[str, str]:
        """List all available tools with their descriptions."""
        if not self.generated_tools:
            self.generate_all_tools()
        
        return {
            name: tool.__doc__ or "No description available"
            for name, tool in self.generated_tools.items()
        }