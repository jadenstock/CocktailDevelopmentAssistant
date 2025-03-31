from pathlib import Path
import toml
import asyncio
from agents import function_tool
from src.notion.query_inventory import (
    load_config, create_notion_client,
    query_bottles_by_type, query_bottles_by_name,
    query_bottles_by_notes, get_all_bottles, get_all_type_tags
)

def get_notion_client_and_db():
    """Helper to load config and create Notion client/database ID."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    config_path = project_root / "etc" / "config.toml"
    config = load_config(config_path)
    notion_api_key = config["api_keys"]["notion"]
    bottle_db_id = config["notion"]["bottle_inventory_db"]
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

def format_bottles(bottles: list) -> str:
    """Format bottle data for LLM consumption"""
    if not bottles: return "No matching bottles found"
    return "\n".join(
        f"- {b['name']} ({', '.join(b['type'])})" + 
        (f"\n  Notes: {b['notes']}" if b['notes'] else "")
        for b in bottles
    )