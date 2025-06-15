"""
Generic query engine for Notion databases using configurable schemas.

This module provides generic query functionality that works with any
configured Notion database based on the database configuration.
"""

from typing import Dict, List, Any, Optional, Union
from notion_client import Client
from .database_config import (
    DatabaseConfig, 
    ColumnConfig, 
    FilterConfig, 
    NotionColumnType,
    NotionDatabaseManager
)


class NotionRowParser:
    """Generic parser for Notion database rows based on column configuration."""
    
    @staticmethod
    def parse_title_property(property_data: Dict[str, Any]) -> str:
        """Parse a title property."""
        title = property_data.get('title', [])
        return title[0].get('text', {}).get('content', '') if title else ''
    
    @staticmethod
    def parse_rich_text_property(property_data: Dict[str, Any]) -> str:
        """Parse a rich text property."""
        rich_text = property_data.get('rich_text', [])
        if not rich_text:
            return ''
        # Concatenate all text segments
        return ''.join([segment.get('text', {}).get('content', '') for segment in rich_text])
    
    @staticmethod
    def parse_multi_select_property(property_data: Dict[str, Any]) -> List[str]:
        """Parse a multi-select property."""
        multi_select = property_data.get('multi_select', [])
        return [tag.get('name', '') for tag in multi_select]
    
    @staticmethod
    def parse_select_property(property_data: Dict[str, Any]) -> Optional[str]:
        """Parse a select property."""
        select = property_data.get('select')
        return select.get('name') if select else None
    
    @staticmethod
    def parse_checkbox_property(property_data: Dict[str, Any]) -> bool:
        """Parse a checkbox property."""
        return property_data.get('checkbox', False)
    
    @staticmethod
    def parse_number_property(property_data: Dict[str, Any]) -> Optional[Union[int, float]]:
        """Parse a number property."""
        return property_data.get('number')
    
    @staticmethod
    def parse_date_property(property_data: Dict[str, Any]) -> Optional[str]:
        """Parse a date property."""
        date_data = property_data.get('date')
        if date_data:
            return date_data.get('start')
        return None
    
    @staticmethod
    def parse_people_property(property_data: Dict[str, Any]) -> List[str]:
        """Parse a people property."""
        people = property_data.get('people', [])
        return [person.get('name', '') for person in people]
    
    @staticmethod
    def parse_files_property(property_data: Dict[str, Any]) -> List[str]:
        """Parse a files property."""
        files = property_data.get('files', [])
        return [file.get('name', '') for file in files]
    
    @staticmethod
    def parse_url_property(property_data: Dict[str, Any]) -> Optional[str]:
        """Parse a URL property."""
        return property_data.get('url')
    
    @staticmethod
    def parse_email_property(property_data: Dict[str, Any]) -> Optional[str]:
        """Parse an email property."""
        return property_data.get('email')
    
    @staticmethod
    def parse_phone_property(property_data: Dict[str, Any]) -> Optional[str]:
        """Parse a phone number property."""
        return property_data.get('phone_number')


class NotionFilterBuilder:
    """Builds Notion API filters based on FilterConfig objects."""
    
    @staticmethod
    def build_filter(filter_config: FilterConfig) -> Dict[str, Any]:
        """Build a Notion API filter from a FilterConfig."""
        # Get the column type to determine the proper filter structure
        # For now, we'll use a generic approach and let Notion handle type validation
        
        filter_obj = {
            "property": filter_config.column_name
        }
        
        # Map common filter types to Notion API structure
        value = filter_config.value
        filter_type = filter_config.filter_type.lower()
        
        if filter_type in ["equals", "does_not_equal"]:
            # For checkbox, select, and other simple properties
            if isinstance(value, bool):
                filter_obj["checkbox"] = {"equals": value}
            elif isinstance(value, str):
                # Could be select, title, rich_text
                filter_obj["rich_text"] = {"equals" if filter_type == "equals" else "does_not_equal": value}
            elif isinstance(value, (int, float)):
                filter_obj["number"] = {"equals" if filter_type == "equals" else "does_not_equal": value}
        
        elif filter_type == "contains":
            if isinstance(value, str):
                filter_obj["rich_text"] = {"contains": value}
            elif isinstance(value, list):
                # For multi-select contains
                filter_obj["multi_select"] = {"contains": value[0] if value else ""}
        
        elif filter_type in ["greater_than", "greater_than_or_equal_to", "less_than", "less_than_or_equal_to"]:
            if isinstance(value, (int, float)):
                filter_obj["number"] = {filter_type: value}
            elif isinstance(value, str):  # Date string
                filter_obj["date"] = {filter_type: value}
        
        elif filter_type in ["on_or_after", "on_or_before", "past_week", "past_month", "past_year"]:
            filter_obj["date"] = {filter_type: value} if value else {filter_type: {}}
        
        return filter_obj
    
    @staticmethod
    def build_compound_filter(filters: List[FilterConfig], operator: str = "and") -> Dict[str, Any]:
        """Build a compound filter with multiple conditions."""
        filter_list = [NotionFilterBuilder.build_filter(f) for f in filters]
        
        if len(filter_list) == 1:
            return filter_list[0]
        
        return {operator: filter_list}


class GenericNotionQuery:
    """Generic Notion database query engine."""
    
    def __init__(self, notion_client: Client, database_manager: NotionDatabaseManager):
        self.notion_client = notion_client
        self.database_manager = database_manager
        self.parser = NotionRowParser()
        self.filter_builder = NotionFilterBuilder()
    
    def parse_row(self, row_data: Dict[str, Any], database_config: DatabaseConfig) -> Dict[str, Any]:
        """Parse a Notion row based on the database configuration."""
        properties = row_data.get('properties', {})
        parsed_row = {
            'id': row_data.get('id'),
            'url': row_data.get('url')
        }
        
        # Parse each configured column
        for column_name, column_config in database_config.columns.items():
            property_data = properties.get(column_name, {})
            
            try:
                if column_config.notion_type == NotionColumnType.TITLE:
                    parsed_row[column_name] = self.parser.parse_title_property(property_data)
                elif column_config.notion_type == NotionColumnType.RICH_TEXT:
                    parsed_row[column_name] = self.parser.parse_rich_text_property(property_data)
                elif column_config.notion_type == NotionColumnType.MULTI_SELECT:
                    parsed_row[column_name] = self.parser.parse_multi_select_property(property_data)
                elif column_config.notion_type == NotionColumnType.SELECT:
                    parsed_row[column_name] = self.parser.parse_select_property(property_data)
                elif column_config.notion_type == NotionColumnType.CHECKBOX:
                    parsed_row[column_name] = self.parser.parse_checkbox_property(property_data)
                elif column_config.notion_type == NotionColumnType.NUMBER:
                    parsed_row[column_name] = self.parser.parse_number_property(property_data)
                elif column_config.notion_type == NotionColumnType.DATE:
                    parsed_row[column_name] = self.parser.parse_date_property(property_data)
                elif column_config.notion_type == NotionColumnType.PEOPLE:
                    parsed_row[column_name] = self.parser.parse_people_property(property_data)
                elif column_config.notion_type == NotionColumnType.FILES:
                    parsed_row[column_name] = self.parser.parse_files_property(property_data)
                elif column_config.notion_type == NotionColumnType.URL:
                    parsed_row[column_name] = self.parser.parse_url_property(property_data)
                elif column_config.notion_type == NotionColumnType.EMAIL:
                    parsed_row[column_name] = self.parser.parse_email_property(property_data)
                elif column_config.notion_type == NotionColumnType.PHONE_NUMBER:
                    parsed_row[column_name] = self.parser.parse_phone_property(property_data)
                else:
                    # Fallback: try to extract as rich text
                    parsed_row[column_name] = self.parser.parse_rich_text_property(property_data)
            
            except Exception as e:
                print(f"Warning: Failed to parse column '{column_name}': {e}")
                parsed_row[column_name] = None
        
        return parsed_row
    
    def query_database(
        self,
        database_name: str,
        filter_names: Optional[List[str]] = None,
        custom_filters: Optional[List[FilterConfig]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        page_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query a database with optional filters.
        
        Args:
            database_name: Name of the configured database
            filter_names: List of predefined filter names from the database config
            custom_filters: List of custom FilterConfig objects
            sorts: List of sort configurations
            page_size: Maximum number of results per page
        
        Returns:
            List of parsed row dictionaries
        """
        database_config = self.database_manager.get_database(database_name)
        if not database_config:
            raise ValueError(f"Database '{database_name}' not found in configuration")
        
        # Build query parameters
        query_params = {"database_id": database_config.database_id}
        
        # Build filters
        all_filters = []
        
        # Add predefined filters
        if filter_names:
            for filter_name in filter_names:
                filter_config = database_config.filters.get(filter_name)
                if filter_config:
                    all_filters.append(filter_config)
                else:
                    print(f"Warning: Filter '{filter_name}' not found for database '{database_name}'")
        
        # Add custom filters
        if custom_filters:
            all_filters.extend(custom_filters)
        
        # Build the compound filter
        if all_filters:
            if len(all_filters) == 1:
                query_params["filter"] = self.filter_builder.build_filter(all_filters[0])
            else:
                query_params["filter"] = self.filter_builder.build_compound_filter(all_filters)
        
        # Add sorts
        if sorts:
            query_params["sorts"] = sorts
        
        # Add page size
        if page_size:
            query_params["page_size"] = min(page_size, 100)  # Notion API limit
        
        try:
            # Execute the query
            response = self.notion_client.databases.query(**query_params)
            results = []
            
            # Parse initial results
            for row in response.get('results', []):
                parsed_row = self.parse_row(row, database_config)
                results.append(parsed_row)
            
            # Handle pagination
            while response.get('has_more', False) and (not page_size or len(results) < page_size):
                query_params["start_cursor"] = response.get('next_cursor')
                response = self.notion_client.databases.query(**query_params)
                
                for row in response.get('results', []):
                    parsed_row = self.parse_row(row, database_config)
                    results.append(parsed_row)
                    
                    if page_size and len(results) >= page_size:
                        break
            
            return results
        
        except Exception as e:
            print(f"Error querying database '{database_name}': {e}")
            return []
    
    def get_all_rows(self, database_name: str) -> List[Dict[str, Any]]:
        """Get all rows from a database."""
        return self.query_database(database_name)
    
    def search_by_text(self, database_name: str, search_text: str, search_columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for text across specified columns or all text columns."""
        database_config = self.database_manager.get_database(database_name)
        if not database_config:
            raise ValueError(f"Database '{database_name}' not found in configuration")
        
        # Determine which columns to search
        if not search_columns:
            # Search all title and rich_text columns
            search_columns = [
                col.name for col in database_config.columns.values()
                if col.notion_type in [NotionColumnType.TITLE, NotionColumnType.RICH_TEXT]
            ]
        
        # Create filters for each column (OR condition)
        search_filters = []
        for column_name in search_columns:
            column_config = database_config.get_column_by_name(column_name)
            if column_config:
                filter_config = FilterConfig(
                    column_name=column_name,
                    filter_type="contains",
                    value=search_text,
                    description=f"Search for '{search_text}' in {column_name}"
                )
                search_filters.append(filter_config)
        
        if not search_filters:
            return []
        
        # Use OR logic for multiple column search
        query_params = {"database_id": database_config.database_id}
        if len(search_filters) == 1:
            query_params["filter"] = self.filter_builder.build_filter(search_filters[0])
        else:
            query_params["filter"] = self.filter_builder.build_compound_filter(search_filters, "or")
        
        try:
            response = self.notion_client.databases.query(**query_params)
            results = []
            
            for row in response.get('results', []):
                parsed_row = self.parse_row(row, database_config)
                results.append(parsed_row)
            
            # Handle pagination
            while response.get('has_more', False):
                query_params["start_cursor"] = response.get('next_cursor')
                response = self.notion_client.databases.query(**query_params)
                
                for row in response.get('results', []):
                    parsed_row = self.parse_row(row, database_config)
                    results.append(parsed_row)
            
            return results
        
        except Exception as e:
            print(f"Error searching database '{database_name}': {e}")
            return []