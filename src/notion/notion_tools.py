from pathlib import Path
import asyncio
from agents import function_tool
from src.settings import (
    NOTION_API_KEY,
    BOTTLE_INVENTORY_NOTION_DB,
    SYRUPS_AND_JUICES_NOTION_DB,
    COCKTAIL_PROJECTS_NOTION_DB,
    WINES_NOTION_DB
)
from src.notion.query_inventory import (
    create_notion_client,
    query_bottles_by_type,
    query_bottles_by_name,
    query_bottles_by_notes,
    get_all_bottles,
    get_random_bottles,
    get_all_type_tags,
    get_all_ingredients,
    get_available_wines,
    format_bottles,
    format_ingredients,
    format_wines
)
from src.notion.update_inventory import update_notion_bottle
from src.notion.save_cocktails import create_cocktail_project_page

def get_notion_client_and_db():
    """Helper to load config and create Notion client/database ID."""
    notion_api_key = NOTION_API_KEY
    bottle_db_id = BOTTLE_INVENTORY_NOTION_DB
    return create_notion_client(notion_api_key), bottle_db_id

@function_tool
async def query_bottles_by_type_tool(type_tags: list[str]) -> str:
    """Query bottles by type tags. Returns formatted list of matches."""
    notion, db_id = get_notion_client_and_db()
    bottles = await asyncio.to_thread(query_bottles_by_type, notion, db_id, type_tags)
    return format_bottles(bottles)

@function_tool
async def query_bottles_by_name_tool(name_query: str) -> str:
    """Search bottles by name. Returns formatted matches."""
    notion, db_id = get_notion_client_and_db()
    bottles = await asyncio.to_thread(query_bottles_by_name, notion, db_id, name_query)
    return format_bottles(bottles)

@function_tool
async def get_available_types_tool() -> str:
    """List all available bottle types in inventory."""
    notion, db_id = get_notion_client_and_db()
    types = await asyncio.to_thread(get_all_type_tags, notion, db_id)
    return "\n- " + "\n- ".join(types) if types else "No types found"

@function_tool
async def get_all_bottles_tool() -> str:
    """Retrieve all bottles in the inventory. Returns formatted list of all bottles."""
    notion, db_id = get_notion_client_and_db()
    bottles = await asyncio.to_thread(get_all_bottles, notion, db_id)
    return format_bottles(bottles)

@function_tool
async def get_random_bottles_tool(count: int = 3) -> str:
    """Get a specified number of random bottles from the inventory. Default is 3 bottles."""
    notion, db_id = get_notion_client_and_db()
    bottles = await asyncio.to_thread(get_random_bottles, notion, db_id, count)
    return format_bottles(bottles)

@function_tool
async def get_available_ingredients_tool() -> str:
    """List all available ingredients (syrups, juices, etc) that we currently have."""
    notion, _ = get_notion_client_and_db()
    ingredients = await asyncio.to_thread(get_all_ingredients, notion, SYRUPS_AND_JUICES_NOTION_DB)
    return format_ingredients(ingredients)

@function_tool
async def get_available_wines_tool() -> str:
    """List all available wines that we currently have."""
    notion, _ = get_notion_client_and_db()
    wines = await asyncio.to_thread(get_available_wines, notion, WINES_NOTION_DB)
    return format_wines(wines)


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
    notion, db_id = get_notion_client_and_db()
    result =  await update_notion_bottle(
        notion,
        db_id,
        name=name,
        types=types,
        notes_contains=notes_contains,
        technical_notes_contains=technical_notes_contains,
        updated_notes=updated_notes,
        updated_technical_notes=updated_technical_notes
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
    # The create_cocktail_project_page function is synchronous,
    # so we run it in a separate thread to avoid blocking the async event loop.
    result = await asyncio.to_thread(
        create_cocktail_project_page,
        database_id=COCKTAIL_PROJECTS_NOTION_DB,
        name=name,
        spec=spec,
        tags=tags,
        preference=preference,
        notes=notes
    )
    return result