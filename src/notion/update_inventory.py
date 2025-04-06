from src.settings import NOTION_API_KEY, BOTTLE_INVENTORY_NOTION_DB
from src.notion.query_inventory import create_notion_client, query_notion_database


async def update_notion_bottle(notion_client, database_id, name=None, types=None, notes_contains=None, technical_notes_contains=None,
                         updated_notes=None, updated_technical_notes=None):
    """
    Finds and updates a Notion bottle based on flexible search criteria.

    Args:
        notion_client: The Notion client instance.
        database_id: The ID of the bottle inventory database.
        name: (Optional) Exact name of the bottle to search for.
        types: (Optional) List of exact type tags the bottle must have.
        notes_contains: (Optional) String that must be present in the bottle's notes.
        technical_notes_contains: (Optional) String that must be present in the bottle's technical notes.
        updated_notes: (Optional) String to set as the new notes content.
        updated_technical_notes: (Optional) String to set as the new technical notes content.

    Returns:
        str: A message indicating the outcome of the operation.
    """
    filters = []
    if name:
        filters.append({"property": "Name", "title": {"equals": name}})
    if types:
        for tag in types:
            filters.append({"property": "Type", "multi_select": {"contains": tag}})
    if notes_contains:
        filters.append({"property": "Notes", "rich_text": {"contains": notes_contains}})
    if technical_notes_contains:
        filters.append({"property": "Technical Notes", "rich_text": {"contains": technical_notes_contains}})

    if not filters:
        return "Error: Please provide at least one search criteria (name, type, notes_contains, technical_notes_contains)."

    if len(filters) > 1:
        filter_obj = {"and": filters}
    else:
        filter_obj = filters[0]

    results = query_notion_database(notion_client, database_id, filter_obj)

    if len(results) == 0:
        return "No bottles found matching the criteria."
    elif len(results) > 1:
        bottle_list = "\n".join([f"- {bottle['name']} ({', '.join(bottle['type'])})" for bottle in results])
        return f"Error: Multiple bottles found matching the criteria:\n{bottle_list}\nPlease provide more specific search terms."
    else:
        bottle_to_update = results[0]
        page_id = bottle_to_update.get('id')
        if not page_id:
            return f"Error: Could not retrieve Notion page ID for '{bottle_to_update['name']}'."

        properties_to_update = {}
        if updated_notes is not None:
            properties_to_update["Notes"] = {"rich_text": [{"text": {"content": updated_notes}}]}
        if updated_technical_notes is not None:
            properties_to_update["Technical Notes"] = {"rich_text": [{"text": {"content": updated_technical_notes}}]}

        if not properties_to_update:
            return f"No updates provided for '{bottle_to_update['name']}'."

        try:
            response = notion_client.pages.update(
                page_id=page_id,
                properties=properties_to_update
            )
            update_fields = ", ".join(properties_to_update.keys())
            return f"Successfully updated '{update_fields}' for '{bottle_to_update['name']}' ({', '.join(bottle_to_update['type'])})."
        except Exception as e:
            print(f"LOG: Error during Notion API update: {e}")
            return f"Error updating '{bottle_to_update['name']}' ({', '.join(bottle_to_update['type'])}): {e}"