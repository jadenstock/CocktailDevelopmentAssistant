"""
Tools for the Cocktail Development Agent.

This module contains tool implementations that the agent can use.
"""

import json
import logging
from typing import List, Literal, Optional, TypedDict, Union, Dict, Any, Callable, Tuple

from src.notion.query_inventory import (
    create_notion_client,
    get_all_type_tags,
    query_bottles_by_type,
)

# Set up logging
logger = logging.getLogger(__name__)


class QueryInventoryInput(TypedDict):
    """Input for the query_inventory tool."""
    action: Literal["list_tags", "query", "query_name", "query_notes", "list_all"]
    type_tags: Optional[List[str]]
    name_query: Optional[str]
    notes_query: Optional[str]


class QueryInventoryOutput(TypedDict):
    """Output for the query_inventory tool."""
    result: Union[List[str], List[dict]]


def query_inventory_tool(
    notion_client, database_id
) -> Tuple[Dict[str, Any], Callable[[QueryInventoryInput], Dict[str, str]]]:
    """
    Create a tool for querying the bottle inventory.
    
    Args:
        notion_client: The Notion client instance
        database_id: The ID of the bottle inventory database
        
    Returns:
        A tuple containing the tool definition and the tool function
    """
    try:
        tool_def = {
            "type": "function",
            "function": {
                "name": "query_inventory",
                "description": "Query the bottle inventory to see what ingredients are available",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list_tags", "query", "query_name", "query_notes", "list_all"],
                            "description": "The action to perform",
                        },
                        "type_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Type tags to filter by when action is 'query'",
                        },
                        "name_query": {
                            "type": "string",
                            "description": "Name to search for when action is 'query_name'",
                        },
                        "notes_query": {
                            "type": "string",
                            "description": "Text to search for in notes when action is 'query_notes'",
                        },
                    },
                    "required": ["action"],
                },
            },
        }
    
        def tool_fn(params: QueryInventoryInput) -> Dict[str, str]:
            """
            Query the bottle inventory.
            
            Args:
                params: The parameters for the query
                
            Returns:
                The query results
            """
            try:
                action = params["action"]
                
                if action == "list_tags":
                    logger.info("Getting all type tags from inventory")
                    tags = get_all_type_tags(notion_client, database_id)
                    return {"output": json.dumps({"result": tags})}
                elif action == "query":
                    type_tags = params.get("type_tags", [])
                    if not type_tags:
                        logger.warning("No type_tags provided for query action")
                        return {"output": json.dumps({
                            "error": "No type_tags provided for query action"
                        })}
                    
                    logger.info(f"Querying bottles by type tags: {type_tags}")
                    bottles = query_bottles_by_type(notion_client, database_id, type_tags)
                    return {"output": json.dumps({"result": bottles})}
                elif action == "query_name":
                    name_query = params.get("name_query", "")
                    if not name_query:
                        logger.warning("No name_query provided for query_name action")
                        return {"output": json.dumps({
                            "error": "No name_query provided for query_name action"
                        })}
                    
                    logger.info(f"Querying bottles by name: {name_query}")
                    from src.notion.query_inventory import query_bottles_by_name
                    bottles = query_bottles_by_name(notion_client, database_id, name_query)
                    return {"output": json.dumps({"result": bottles})}
                elif action == "query_notes":
                    notes_query = params.get("notes_query", "")
                    if not notes_query:
                        logger.warning("No notes_query provided for query_notes action")
                        return {"output": json.dumps({
                            "error": "No notes_query provided for query_notes action"
                        })}
                    
                    logger.info(f"Querying bottles by notes: {notes_query}")
                    from src.notion.query_inventory import query_bottles_by_notes
                    bottles = query_bottles_by_notes(notion_client, database_id, notes_query)
                    return {"output": json.dumps({"result": bottles})}
                elif action == "list_all":
                    logger.info("Getting all bottles from inventory")
                    from src.notion.query_inventory import get_all_bottles
                    bottles = get_all_bottles(notion_client, database_id)
                    return {"output": json.dumps({"result": bottles})}
                else:
                    logger.warning(f"Unknown action: {action}")
                    return {"output": json.dumps({
                        "error": f"Unknown action: {action}"
                    })}
            except Exception as e:
                logger.error(f"Error in query_inventory tool: {e}")
                return {"output": json.dumps({
                    "error": f"Error in query_inventory tool: {str(e)}"
                })}
        
        return tool_def, tool_fn
    except Exception as e:
        logger.error(f"Error creating query_inventory tool: {e}")
        raise
