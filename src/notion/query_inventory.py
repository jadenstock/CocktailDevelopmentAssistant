#!/usr/bin/env python3
"""
Query bottle inventory from Notion database.

This script provides functions to query the bottle inventory in a Notion database,
including retrieving all available type tags and filtering bottles by type, name, or notes.
"""

import sys
from pathlib import Path
import toml
from notion_client import Client
from src.settings import (
    NOTION_API_KEY,
    BOTTLE_INVENTORY_NOTION_DB,
    SYRUPS_AND_JUICES_NOTION_DB,
    WINES_NOTION_DB
)

def load_config(config_path):
    """Load configuration from TOML file."""
    try:
        return toml.load(config_path)
    except Exception as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)

def create_notion_client(api_key):
    """Create a Notion client with the provided API key."""
    return Client(auth=api_key)


def format_bottles(bottles):
    """Format a list bottle objects."""
    bottle_str = ""
    for bottle in bottles:
        bottle_str += f"  - {bottle['name']} ({', '.join(bottle['type'])})"
        if bottle['almost_gone']:
            bottle_str += " (almost gone)"
        if bottle['not_for_mixing']:
            bottle_str += " (not for mixing)"
        if bottle['notes']:
            bottle_str += f"\n    Notes: {bottle['notes']}"
        if bottle['technical_notes']:
            bottle_str += f"\n    Technical Notes: {bottle['technical_notes']}"
        bottle_str += "\n"
    return bottle_str


def format_ingredients(ingredients):
    """Format a list of ingredients for display."""
    if not ingredients:
        return "No ingredients found"
    return "\n".join(f"- {ingredient['name']}" for ingredient in ingredients)


def format_wines(wines):
    """Format a list of wine objects for display."""
    if not wines:
        return "No wines found"

    wine_str = f"{len(wines)} wines found:\n"
    for wine in wines:
        wine_str += f"  - {wine['name']}"
        if wine['vintage_year']:
            wine_str += f" ({wine['vintage_year']})"
        if wine['notes']:
            wine_str += f"\n    Notes: {wine['notes']}"
        if wine['technical_notes']:
            wine_str += f"\n    Technical Notes: {wine['technical_notes']}"
        wine_str += "\n"
    return wine_str


def parse_notion_row_to_bottle(result):
    """
    Parse a Notion database row into a bottle dictionary.
    
    Args:
        result: A single result object from a Notion database query
        
    Returns:
        A dictionary containing standardized bottle information
    """
    properties = result.get('properties', {})
    bottle_id = result.get('id')
    
    # Extract name
    name_property = properties.get('Name', {})
    title = name_property.get('title', [])
    name = title[0].get('text', {}).get('content', '') if title else ''
    
    # Extract type tags
    type_property = properties.get('Type', {})
    multi_select = type_property.get('multi_select', [])
    types = [tag.get('name') for tag in multi_select]
    
    # Extract notes if available
    notes_property = properties.get('Notes', {})
    rich_text = notes_property.get('rich_text', [])
    notes = rich_text[0].get('text', {}).get('content', '') if rich_text else ''

    # Extract technical notes if available
    technical_notes_property = properties.get('Technical Notes', {})
    rich_text = technical_notes_property.get('rich_text', [])
    technical_notes = rich_text[0].get('text', {}).get('content', '') if rich_text else ''

    # Extract almost_gone toggle
    almost_gone_property = properties.get('almost_gone', {})
    almost_gone = almost_gone_property.get('checkbox', False)

    # Extract not_for_mixing toggle
    not_for_mixing_property = properties.get('not_for_mixing', {})
    not_for_mixing = not_for_mixing_property.get('checkbox', False)
    
    # Create and return bottle dictionary
    return {
        'name': name,
        'id': bottle_id,
        'type': types,
        'notes': notes,
        'technical_notes': technical_notes,
        'almost_gone': almost_gone,
        'not_for_mixing': not_for_mixing
    }


def parse_notion_row_to_ingredient(result):
    """
    Parse a Notion database row into an ingredient dictionary.
    """
    properties = result.get('properties', {})
    
    # Extract name from the text column (assuming it is formatted as a title property)
    name_property = properties.get('Name', {})
    title = name_property.get('title', [])
    name = title[0].get('text', {}).get('content', '') if title else ''
    
    # Extract 'Have' from the toggle column (checkbox)
    have_property = properties.get('Have', {})
    have = have_property.get('checkbox', False)
    
    return {
        'name': name,
        'have': have
    }


def parse_notion_row_to_wine(result):
    """
    Parse a Notion database row into a wine dictionary.

    Args:
        result: A single result object from a Notion database query

    Returns:
        A dictionary containing standardized wine information
    """
    properties = result.get('properties', {})
    wine_id = result.get('id')

    # Extract name
    name_property = properties.get('Name', {})
    title = name_property.get('title', [])
    name = title[0].get('text', {}).get('content', '') if title else ''

    # Extract notes if available
    notes_property = properties.get('Notes', {})
    rich_text = notes_property.get('rich_text', [])
    notes = rich_text[0].get('text', {}).get('content', '') if rich_text else ''

    # Extract technical notes if available - concatenate all rich text segments
    technical_notes_property = properties.get('Technical Notes', {})
    rich_text = technical_notes_property.get('rich_text', [])
    technical_notes = ''.join([segment.get('text', {}).get('content', '') for segment in rich_text])

    # Extract vintage year (number)
    vintage_year_property = properties.get('Vintage Year', {})
    vintage_year = vintage_year_property.get('number', None)

    # Extract cellar toggle
    cellar_property = properties.get('Cellar', {})
    cellar = cellar_property.get('checkbox', False)

    # Extract drank toggle
    drank_property = properties.get('Drank', {})
    drank = drank_property.get('checkbox', False)

    return {
        'id': wine_id,
        'name': name,
        'notes': notes,
        'technical_notes': technical_notes,
        'vintage_year': vintage_year,
        'cellar': cellar,
        'drank': drank
    }


def query_notion_database(notion_client,
                          database_id,
                          parse_function=parse_notion_row_to_bottle,
                          filter_obj=None):
    """
    Query the Notion database with the provided filter and return all results.
    
    Args:
        notion_client: The Notion client instance
        database_id: The ID of the bottle inventory database
        filter_obj: Optional filter object to apply to the query
        
    Returns:
        A list of dictionaries containing bottle information
    """
    try:
        # Prepare query parameters
        query_params = {"database_id": database_id}
        if filter_obj:
            query_params["filter"] = filter_obj
            
        # Execute the initial query
        response = notion_client.databases.query(**query_params)

        # Extract bottle information from the results
        parsed_results = [parse_function(result) for result in response.get('results', [])]
        
        # Get additional pages if there are more results
        while response.get('has_more', False):
            next_cursor = response.get('next_cursor')
            query_params["start_cursor"] = next_cursor
            response = notion_client.databases.query(**query_params)
            
            # Add additional bottles to the list
            parsed_results.extend([parse_function(result) for result in response.get('results', [])])
        
        return parsed_results
    
    except Exception as e:
        print(f"Error querying Notion database: {e}")
        return []

def get_all_type_tags(notion_client, database_id):
    """
    Get all available tags under the 'Type' column.
    
    Args:
        notion_client: The Notion client instance
        database_id: The ID of the bottle inventory database
        
    Returns:
        A sorted list of unique type tags
    """
    try:
        # Query all bottles
        bottles = query_notion_database(notion_client, database_id)
        
        # Extract all unique tags
        all_tags = set()
        for bottle in bottles:
            for tag in bottle['type']:
                all_tags.add(tag)
        
        # Return sorted list of tags
        return sorted(all_tags)
    
    except Exception as e:
        print(f"Error retrieving type tags: {e}")
        return []

def query_bottles_by_type(notion_client, database_id, type_tags):
    """
    Query and return all bottles that match the specified type tags.
    
    Args:
        notion_client: The Notion client instance
        database_id: The ID of the bottle inventory database
        type_tags: A list of type tags to filter by
        
    Returns:
        A list of dictionaries containing bottle information
    """
    if not type_tags:
        print("No type tags provided for filtering")
        return []
    
    try:
        # Create a filter for the type tags
        filter_conditions = []
        for tag in type_tags:
            filter_conditions.append({
                "property": "Type",
                "multi_select": {
                    "contains": tag
                }
            })
        
        # If multiple tags, use AND condition
        if len(filter_conditions) > 1:
            filter_obj = {
                "and": filter_conditions
            }
        else:
            filter_obj = filter_conditions[0]
        
        # Query the database with the filter
        return query_notion_database(notion_client, database_id, filter_obj)
    
    except Exception as e:
        print(f"Error querying bottles by type: {e}")
        return []

def query_bottles_by_name(notion_client, database_id, name_query):
    """
    Query and return all bottles that match the specified name query.
    
    Args:
        notion_client: The Notion client instance
        database_id: The ID of the bottle inventory database
        name_query: A string to search for in bottle names
        
    Returns:
        A list of dictionaries containing bottle information
    """
    if not name_query:
        print("No name query provided for filtering")
        return []
    
    try:
        # Create a filter for the name query
        filter_obj = {
            "property": "Name",
            "title": {
                "contains": name_query
            }
        }
        
        # Query the database with the filter
        return query_notion_database(notion_client, database_id, filter_obj)
    
    except Exception as e:
        print(f"Error querying bottles by name: {e}")
        return []

def query_bottles_by_notes(notion_client, database_id, notes_query):
    """
    Query and return all bottles that match the specified notes query.
    
    Args:
        notion_client: The Notion client instance
        database_id: The ID of the bottle inventory database
        notes_query: A string to search for in bottle notes
        
    Returns:
        A list of dictionaries containing bottle information
    """
    if not notes_query:
        print("No notes query provided for filtering")
        return []
    
    try:
        # Create a filter for the notes query
        filter_obj = {
            "property": "Notes",
            "rich_text": {
                "contains": notes_query
            }
        }
        
        # Query the database with the filter
        return query_notion_database(notion_client, database_id, filter_obj)
    
    except Exception as e:
        print(f"Error querying bottles by notes: {e}")
        return []

def get_all_bottles(notion_client, database_id):
    """
    Get all bottles in the inventory.

    Args:
        notion_client: The Notion client instance
        database_id: The ID of the bottle inventory database

    Returns:
        A list of dictionaries containing bottle information
    """
    try:
        # Query the database with no filter to get all entries
        return query_notion_database(notion_client, database_id)

    except Exception as e:
        print(f"Error getting all bottles: {e}")
        return []


def get_random_bottles(notion_client, database_id, count=3):
    """
    Get a specified number of random bottles from the inventory.

    Args:
        notion_client: The Notion client instance
        database_id: The ID of the bottle inventory database
        count: The number of random bottles to return (default: 3)

    Returns:
        A list of dictionaries containing random bottle information
    """
    import random

    try:
        # Get all bottles first
        all_bottles = query_notion_database(notion_client, database_id)

        if not all_bottles:
            print("No bottles found in inventory")
            return []

        # Return random selection, ensuring we don't try to select more than available
        selection_count = min(count, len(all_bottles))
        return random.sample(all_bottles, selection_count)

    except Exception as e:
        print(f"Error getting random bottles: {e}")
        return []


def get_all_ingredients(notion_client, database_id):
    """
    Get all available ingredients from the syrups and juices database.
    
    Args:
        notion_client: The Notion client instance
        database_id: The ID of the syrups and juices database
        
    Returns:
        A list of dictionaries containing ingredient information
    """
    try:
        # Create filter for Have=True
        filter_obj = {
            "property": "Have",
            "checkbox": {
                "equals": True
            }
        }
        
        # Query the database using the existing function
        ingredients = query_notion_database(notion_client,
                                        database_id,
                                        parse_function=parse_notion_row_to_ingredient,
                                        filter_obj=filter_obj)
        
        # Convert the results to ingredients format
        # ingredients = [{'name': result['name'], 'have': True} for result in results]
        # ingredients = [{'name': result['name'], 'have': True} for result in results

        return ingredients
    
    except Exception as e:
        print(f"Error getting ingredients: {e}")
        return []


def get_available_wines(notion_client, database_id):
    """
    Get wines that are neither in the cellar nor marked as drank.

    Args:
        notion_client: The Notion client instance
        database_id: The ID of the wine database

    Returns:
        A list of dictionaries containing wine information
    """
    try:
        # Filter: Cellar == False AND Drank == False
        filter_obj = {
            "and": [
                {
                    "property": "Cellar",
                    "checkbox": {
                        "equals": False
                    }
                },
                {
                    "property": "Drank",
                    "checkbox": {
                        "equals": False
                    }
                }
            ]
        }

        # Query the database using the existing function
        wines = query_notion_database(notion_client,
                                        database_id,
                                        parse_function=parse_notion_row_to_wine,
                                        filter_obj=filter_obj)

        return wines

    except Exception as e:
        print(f"Error getting uncategorized wines: {e}")
        return []


def main():
    """Main function to run the script with command-line arguments."""
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Query bottle inventory from Notion database')
    parser.add_argument('--tags', action='store_true', help='List all available type tags')
    parser.add_argument('--query', nargs='+', help='Query bottles by type tags (e.g., --query amaro "traditional italian amaro")')
    parser.add_argument('--name', help='Query bottles by name (e.g., --name "Campari")')
    parser.add_argument('--notes', help='Query bottles by notes (e.g., --notes "bitter")')
    parser.add_argument('--all', action='store_true', help='List all bottles in the inventory')
    parser.add_argument('--wines', action='store_true', help='List all wines in the inventory')
    parser.add_argument('--ingredients', action='store_true', help='List all ingredients in the inventory')
    args = parser.parse_args()
    
    # Get Notion API key and database ID
    notion_api_key = NOTION_API_KEY
    bottle_db_id = BOTTLE_INVENTORY_NOTION_DB
    notion = create_notion_client(notion_api_key)
    
    # If no arguments provided, show help
    if not args.tags and not args.query and not args.name and not args.notes and not args.all and not args.wines and not args.ingredients:
        parser.print_help()
        print("\nExamples:")
        print("  List all type tags:  python query_inventory.py --tags")
        print("  Query by type:       python query_inventory.py --query amaro")
        print("  Query by multiple types (AND): python query_inventory.py --query amaro \"traditional italian amaro\"")
        print("  Query by name:       python query_inventory.py --name \"Campari\"")
        print("  Query by notes:      python query_inventory.py --notes \"bitter\"")
        print("  List all bottles:    python query_inventory.py --all")
        print("  List all wines:      python query_inventory.py --wines")
        print("  List all wines:      python query_inventory.py --ingredients")
        return
    
    # List all type tags
    if args.tags:
        print("Getting all type tags...")
        all_tags = get_all_type_tags(notion, bottle_db_id)
        print(f"Found {len(all_tags)} unique type tags:")
        for tag in all_tags:
            print(f"  - {tag}")
    
    # Query bottles by type
    if args.query:
        print(f"Querying bottles with type: {args.query}")
        bottles = query_bottles_by_type(notion, bottle_db_id, args.query)
        print(f"Found {len(bottles)} bottles:")
        print(format_bottles(bottles))
    
    # Query bottles by name
    if args.name:
        print(f"Querying bottles with name containing: {args.name}")
        bottles = query_bottles_by_name(notion, bottle_db_id, args.name)
        print(f"Found {len(bottles)} bottles:")
        print(format_bottles(bottles))
    
    # Query bottles by notes
    if args.notes:
        print(f"Querying bottles with notes containing: {args.notes}")
        bottles = query_bottles_by_notes(notion, bottle_db_id, args.notes)
        print(f"Found {len(bottles)} bottles:")
        print(format_bottles(bottles))
    
    # List all bottles
    if args.all:
        print("Getting all bottles...")
        bottles = get_all_bottles(notion, bottle_db_id)
        print(f"Found {len(bottles)} bottles:")
        print(format_bottles(bottles))

    # list all ingredients
    if args.ingredients:
        print("Getting all ingredients...")
        ingredients = get_all_ingredients(notion, SYRUPS_AND_JUICES_NOTION_DB)
        print(f"Found {len(ingredients)} ingredients:")
        print(format_ingredients(ingredients))

    # list all wines
    if args.wines:
        print("Getting all wines...")
        wines = get_available_wines(notion, WINES_NOTION_DB)
        print(f"Found {len(wines)} wines:")
        print(format_wines(wines))

if __name__ == "__main__":
    main()