# src/notion/save_cocktails.py
from notion_client import Client
from src.settings import COCKTAIL_PROJECTS_NOTION_DB, NOTION_API_KEY
# Removed asyncio import as it's not needed here anymore

# Removed 'async' from the function definition
def create_cocktail_project_page(database_id: str, name: str, spec: str, tags: list[str] = None, preference: int = None, notes: str = None):
    """Creates a new page for a cocktail in the specified Notion database with tags, preference score, and notes."""
    notion = Client(auth=NOTION_API_KEY)

    properties = {
        "Name": {"title": [{"text": {"content": name}}]},
        "Spec": {"rich_text": [{"text": {"content": spec}}]},
    }
    if tags:
        # Assuming 'Tags' is a Multi-select property
        properties["Tags"] = {"multi_select": [{"name": tag} for tag in tags]}
    if preference is not None:
        # Assuming 'Preference' is a Number property
        properties["Preference"] = {"number": preference}
    if notes:
        properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}

    try:
        # Removed 'await' from the function call
        response = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        # Optional: You might want to inspect the 'response' dict here
        # print(f"LOG: Notion API Response: {response}")
        return f"Successfully saved '{name}' to Notion."
    except Exception as e:
        print(f"LOG: Error creating Notion page: {e}")
        # Consider re-raising the exception or handling it more specifically
        # depending on your application's needs.
        return f"Error saving '{name}' to Notion: {e}"

if __name__ == '__main__':
    # Removed the async test function wrapper and asyncio.run
    result = create_cocktail_project_page(
        COCKTAIL_PROJECTS_NOTION_DB,
        name="Another Test Cocktail",
        spec="2 oz Bourbon, 1 oz Sweet Vermouth, 2 Dashes Bitters",
        tags=["Classic", "Whiskey-based"],
        preference=8,
        notes="Sounds like a solid Manhattan variation."
    )
    print(result)