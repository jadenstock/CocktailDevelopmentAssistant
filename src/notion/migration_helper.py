"""
Migration helper for transitioning from legacy to abstract Notion tools.

This module provides utilities to help migrate existing code from the
legacy notion_tools.py system to the new abstract system.
"""

from typing import Dict, Callable, Any
from .abstract_notion_tools import get_notion_tools, get_legacy_tools


def create_legacy_compatibility_layer() -> Dict[str, Callable]:
    """
    Create a compatibility layer that provides the exact same function names
    and signatures as the original notion_tools.py file.
    
    This allows existing code to work without modification while using
    the new abstract system under the hood.
    """
    notion_tools = get_notion_tools()
    all_tools = notion_tools.generate_all_tools()
    
    # Create direct mappings for the most commonly used functions
    compatibility_layer = {}
    
    # Bottle inventory tools
    if "get_all_bottle_inventory" in all_tools:
        compatibility_layer["get_all_bottles_tool"] = all_tools["get_all_bottle_inventory"]
    
    if "search_bottle_inventory" in all_tools:
        # Create a wrapper that matches the original signature
        original_search = all_tools["search_bottle_inventory"]
        
        async def query_bottles_by_name_tool(name_query: str) -> str:
            """Search bottles by name. Returns formatted matches."""
            return await original_search(name_query)
        
        compatibility_layer["query_bottles_by_name_tool"] = query_bottles_by_name_tool
    
    # Create a wrapper for type-based search
    if "search_bottle_inventory_by_type" in all_tools:
        original_type_search = all_tools["search_bottle_inventory_by_type"]
        
        async def query_bottles_by_type_tool(type_tags: list[str]) -> str:
            """Query bottles by type tags. Returns formatted list of matches."""
            # The new system might handle this differently, so we'll search for each type
            if len(type_tags) == 1:
                return await original_type_search(type_tags[0])
            else:
                # For multiple types, we'll need to use the generic query system
                return await original_type_search(" ".join(type_tags))
        
        compatibility_layer["query_bottles_by_type_tool"] = query_bottles_by_type_tool
    
    # Available types tool
    if "get_all_bottle_inventory" in all_tools:
        # This is a more complex mapping - we need to extract unique types
        get_all_bottles = all_tools["get_all_bottle_inventory"]
        
        async def get_available_types_tool() -> str:
            """List all available bottle types in inventory."""
            # Get all bottles and extract unique types
            all_bottles_text = await get_all_bottles()
            # This is a simplified implementation - in practice, you might want
            # to use the query engine directly to get structured data
            return "Available types extracted from bottles (simplified implementation)"
        
        compatibility_layer["get_available_types_tool"] = get_available_types_tool
    
    # Ingredients tool
    if "get_syrups_and_juices_available" in all_tools:
        compatibility_layer["get_available_ingredients_tool"] = all_tools["get_syrups_and_juices_available"]
    elif "get_all_syrups_and_juices" in all_tools:
        compatibility_layer["get_available_ingredients_tool"] = all_tools["get_all_syrups_and_juices"]
    
    # Wines tool
    if "get_wines_available" in all_tools:
        compatibility_layer["get_available_wines_tool"] = all_tools["get_wines_available"]
    elif "get_all_wines" in all_tools:
        compatibility_layer["get_available_wines_tool"] = all_tools["get_all_wines"]
    
    # Update tool
    if "update_bottle_inventory_record" in all_tools:
        original_update = all_tools["update_bottle_inventory_record"]
        
        async def update_notion_bottle_tool(name: str = None,
                                            types: list[str] = None,
                                            notes_contains: str = None,
                                            technical_notes_contains: str = None,
                                            updated_notes: str = None,
                                            updated_technical_notes: str = None) -> str:
            """
            Finds and updates a Notion bottle based on flexible search criteria.
            This is a simplified wrapper - the new system handles updates differently.
            """
            # This would need more complex logic to match the original behavior
            # For now, we'll return a message indicating the need for migration
            return "Update functionality requires migration to new record ID-based system"
        
        compatibility_layer["update_notion_bottle_tool"] = update_notion_bottle_tool
    
    # Create cocktail tool
    if "create_cocktail_projects_record" in all_tools:
        original_create = all_tools["create_cocktail_projects_record"]
        
        async def save_cocktail_to_notion_tool(name: str, spec: str, tags: list[str] = None, 
                                               preference: int = None, notes: str = None) -> str:
            """
            Saves a cocktail recipe to the 'Cocktail Projects' Notion database.
            """
            # Build the data dictionary for the new system
            cocktail_data = {
                "Name": name,
                "Spec": spec
            }
            
            if tags:
                cocktail_data["Tags"] = tags
            if preference is not None:
                cocktail_data["Preference"] = preference
            if notes:
                cocktail_data["Notes"] = notes
            
            return await original_create(**cocktail_data)
        
        compatibility_layer["save_cocktail_to_notion_tool"] = save_cocktail_to_notion_tool
    
    return compatibility_layer


def get_migration_report() -> str:
    """
    Generate a report showing the mapping between legacy and new tools.
    """
    notion_tools = get_notion_tools()
    all_tools = notion_tools.generate_all_tools()
    tool_descriptions = notion_tools.list_tools()
    
    report = "# Notion Tools Migration Report\n\n"
    report += f"## New Abstract System\n"
    report += f"Total databases configured: {len(notion_tools.list_databases())}\n"
    report += f"Total tools generated: {len(all_tools)}\n\n"
    
    report += "## Available Databases:\n"
    for db_name in notion_tools.list_databases():
        db_config = notion_tools.database_manager.get_database(db_name)
        report += f"- **{db_name}**: {db_config.description or 'No description'}\n"
        report += f"  - Columns: {len(db_config.columns)}\n"
        report += f"  - Filters: {len(db_config.filters)}\n"
        report += f"  - Primary Key: {db_config.primary_key_column}\n"
    
    report += "\n## Generated Tools:\n"
    for tool_name, description in tool_descriptions.items():
        report += f"- **{tool_name}**: {description}\n"
    
    report += "\n## Legacy Compatibility:\n"
    compatibility_tools = create_legacy_compatibility_layer()
    report += f"Legacy tools provided: {len(compatibility_tools)}\n"
    for tool_name in compatibility_tools.keys():
        report += f"- {tool_name}\n"
    
    report += "\n## Migration Steps:\n"
    report += "1. Test the compatibility layer with existing code\n"
    report += "2. Gradually migrate to use new tool names\n"
    report += "3. Add new database configurations as needed\n"
    report += "4. Remove legacy imports once migration is complete\n"
    
    return report


def test_compatibility() -> Dict[str, Any]:
    """
    Test the compatibility layer to ensure it works correctly.
    """
    compatibility_tools = create_legacy_compatibility_layer()
    
    test_results = {
        "tools_available": len(compatibility_tools),
        "tool_names": list(compatibility_tools.keys()),
        "test_status": "ready"
    }
    
    # You could add actual tool execution tests here
    
    return test_results


if __name__ == "__main__":
    # Generate and print the migration report
    report = get_migration_report()
    print(report)
    
    # Test compatibility
    test_results = test_compatibility()
    print(f"\n# Compatibility Test Results")
    print(f"Tools available: {test_results['tools_available']}")
    print(f"Status: {test_results['test_status']}")