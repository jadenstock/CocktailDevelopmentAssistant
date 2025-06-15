import asyncio
from agents import function_tool
from src.settings import (
    NOTION_API_KEY,
    BOTTLE_INVENTORY_NOTION_DB,
    SYRUPS_AND_JUICES_NOTION_DB,
    COCKTAIL_PROJECTS_NOTION_DB,
    WINES_NOTION_DB
)

# Import the new abstract framework
from .abstract_notion_tools import get_notion_tools
from .database_config import FilterConfig

# Initialize the abstract notion tools system
_notion_tools = None

def get_abstract_tools():
    """Get the abstract notion tools instance."""
    global _notion_tools
    if _notion_tools is None:
        _notion_tools = get_notion_tools()
    return _notion_tools

@function_tool
async def query_bottles_by_type_tool(type_tags: list[str]) -> str:
    """Query bottles by type tags. Returns formatted list of matches."""
    abstract_tools = get_abstract_tools()
    
    # Create custom filters for each type tag
    type_filters = []
    for tag in type_tags:
        filter_config = FilterConfig(
            column_name="Type",
            filter_type="contains",
            value=tag,
            description=f"Filter by type: {tag}"
        )
        type_filters.append(filter_config)
    
    # Use the abstract query engine
    results = await asyncio.to_thread(
        abstract_tools.tool_generator.query_engine.query_database,
        "bottle_inventory",
        custom_filters=type_filters
    )
    
    # Format results similar to legacy format
    return abstract_tools.tool_generator.format_results(results, 
        abstract_tools.database_manager.get_database("bottle_inventory"))

@function_tool
async def query_bottles_by_name_tool(name_query: str) -> str:
    """Search bottles by name. Returns formatted matches."""
    abstract_tools = get_abstract_tools()
    
    # Use the search functionality
    results = await asyncio.to_thread(
        abstract_tools.tool_generator.query_engine.search_by_text,
        "bottle_inventory",
        name_query,
        ["Name"]  # Search only in the Name column
    )
    
    return abstract_tools.tool_generator.format_results(results, 
        abstract_tools.database_manager.get_database("bottle_inventory"))

@function_tool
async def get_available_types_tool() -> str:
    """List all available bottle types in inventory."""
    abstract_tools = get_abstract_tools()
    
    # Get all bottles and extract unique types
    results = await asyncio.to_thread(
        abstract_tools.tool_generator.query_engine.get_all_rows,
        "bottle_inventory"
    )
    
    # Extract unique types
    all_types = set()
    for bottle in results:
        bottle_types = bottle.get("Type", [])
        if isinstance(bottle_types, list):
            all_types.update(bottle_types)
        elif bottle_types:  # Single type as string
            all_types.add(bottle_types)
    
    sorted_types = sorted(all_types)
    return "\n- " + "\n- ".join(sorted_types) if sorted_types else "No types found"

@function_tool
async def get_all_bottles_tool() -> str:
    """Retrieve all bottles in the inventory. Returns formatted list of all bottles."""
    abstract_tools = get_abstract_tools()
    
    results = await asyncio.to_thread(
        abstract_tools.tool_generator.query_engine.get_all_rows,
        "bottle_inventory"
    )
    
    return abstract_tools.tool_generator.format_results(results, 
        abstract_tools.database_manager.get_database("bottle_inventory"))

@function_tool
async def get_available_ingredients_tool() -> str:
    """List all available ingredients (syrups, juices, etc) that we currently have."""
    abstract_tools = get_abstract_tools()
    
    # Use the predefined "available" filter for syrups and juices
    results = await asyncio.to_thread(
        abstract_tools.tool_generator.query_engine.query_database,
        "syrups_and_juices",
        filter_names=["available"]
    )
    
    # Format as simple ingredient list
    if not results:
        return "No ingredients found"
    
    ingredient_names = [result.get("Name", "Unknown") for result in results]
    return "\n".join(f"- {name}" for name in ingredient_names)

@function_tool
async def get_available_wines_tool() -> str:
    """List all available wines that we currently have."""
    abstract_tools = get_abstract_tools()
    
    # Use compound filter: not in cellar AND not drank
    not_cellar_filter = FilterConfig(
        column_name="Cellar",
        filter_type="equals",
        value=False,
        description="Not in cellar"
    )
    
    not_drank_filter = FilterConfig(
        column_name="Drank", 
        filter_type="equals",
        value=False,
        description="Not consumed"
    )
    
    results = await asyncio.to_thread(
        abstract_tools.tool_generator.query_engine.query_database,
        "wines",
        custom_filters=[not_cellar_filter, not_drank_filter]
    )
    
    return abstract_tools.tool_generator.format_results(results, 
        abstract_tools.database_manager.get_database("wines"))


@function_tool
async def update_notion_bottle_tool(name: str = None,
                                    types: list[str] = None,
                                    notes_contains: str = None,
                                    technical_notes_contains: str = None,
                                    updated_notes: str = None,
                                    updated_technical_notes: str = None) -> str:
    """
    Finds and updates a Notion bottle based on flexible search criteria.
    Specify search criteria (name, types, notes_contains, technical_notes_contains)
    and the fields to update (updated_notes, updated_technical_notes).
    Will fail if zero or more than one bottle matches the search criteria.
    """
    abstract_tools = get_abstract_tools()
    
    # Build search filters based on provided criteria
    search_filters = []
    
    if name:
        search_filters.append(FilterConfig(
            column_name="Name",
            filter_type="contains",
            value=name,
            description=f"Name contains: {name}"
        ))
    
    if types:
        for bottle_type in types:
            search_filters.append(FilterConfig(
                column_name="Type",
                filter_type="contains", 
                value=bottle_type,
                description=f"Type contains: {bottle_type}"
            ))
    
    if notes_contains:
        search_filters.append(FilterConfig(
            column_name="Notes",
            filter_type="contains",
            value=notes_contains,
            description=f"Notes contains: {notes_contains}"
        ))
    
    if technical_notes_contains:
        search_filters.append(FilterConfig(
            column_name="Technical Notes",
            filter_type="contains",
            value=technical_notes_contains,
            description=f"Technical Notes contains: {technical_notes_contains}"
        ))
    
    if not search_filters:
        return "Error: No search criteria provided"
    
    # Find matching bottles
    results = await asyncio.to_thread(
        abstract_tools.tool_generator.query_engine.query_database,
        "bottle_inventory",
        custom_filters=search_filters
    )
    
    if len(results) == 0:
        return "Error: No bottles found matching the search criteria"
    elif len(results) > 1:
        return f"Error: Found {len(results)} bottles matching criteria. Please be more specific."
    
    # Update the single matching bottle
    bottle = results[0]
    bottle_id = bottle.get('id')
    
    if not bottle_id:
        return "Error: Could not get bottle ID for update"
    
    # Build update data
    update_data = {}
    if updated_notes is not None:
        update_data["Notes"] = updated_notes
    if updated_technical_notes is not None:
        update_data["Technical Notes"] = updated_technical_notes
    
    if not update_data:
        return "Error: No update data provided"
    
    # Perform the update
    result = await asyncio.to_thread(
        abstract_tools.tool_generator.writer_engine.update_record,
        "bottle_inventory",
        bottle_id,
        update_data
    )
    
    return result


@function_tool
async def save_cocktail_to_notion_tool(name: str, spec: str, tags: list[str] = None, preference: int = None, notes: str = None) -> str:
    """
    Saves a cocktail recipe to the 'Cocktail Projects' Notion database.

    Args:
        name: The name of the cocktail.
        spec: The recipe specification (e.g., '2 oz Gin, 1 oz Lime, 0.75 oz Simple Syrup').
        tags: Optional list of descriptive tags (e.g., ['Gin-based', 'Sour']).
        preference: Optional numerical score (e.g., 8) indicating preference level.
        notes: Optional text notes about the cocktail idea or project.

    Returns:
        A string indicating success or failure.
    """
    abstract_tools = get_abstract_tools()
    
    # Build the cocktail data
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
    
    # Create the record using the abstract framework
    result = await asyncio.to_thread(
        abstract_tools.tool_generator.writer_engine.create_record,
        "cocktail_projects",
        cocktail_data
    )
    
    return result