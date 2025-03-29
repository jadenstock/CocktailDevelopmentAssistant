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
        # Query the database with no filter to get all entries
        response = notion_client.databases.query(
            database_id=database_id
        )
        
        # Extract all type tags from the results
        all_tags = []
        for result in response.get('results', []):
            properties = result.get('properties', {})
            type_property = properties.get('Type', {})
            multi_select = type_property.get('multi_select', [])
            
            for tag in multi_select:
                tag_name = tag.get('name')
                if tag_name and tag_name not in all_tags:
                    all_tags.append(tag_name)
        
        # Get additional pages if there are more results
        while response.get('has_more', False):
            next_cursor = response.get('next_cursor')
            response = notion_client.databases.query(
                database_id=database_id,
                start_cursor=next_cursor
            )
            
            for result in response.get('results', []):
                properties = result.get('properties', {})
                type_property = properties.get('Type', {})
                multi_select = type_property.get('multi_select', [])
                
                for tag in multi_select:
                    tag_name = tag.get('name')
                    if tag_name and tag_name not in all_tags:
                        all_tags.append(tag_name)
        
        # Sort the tags alphabetically
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
        response = notion_client.databases.query(
            database_id=database_id,
            filter=filter_obj
        )
        
        # Extract bottle information from the results
        bottles = []
        for result in response.get('results', []):
            properties = result.get('properties', {})
            
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
            
            # Add bottle to results
            bottles.append({
                'name': name,
                'type': types,
                'notes': notes
            })
        
        # Get additional pages if there are more results
        while response.get('has_more', False):
            next_cursor = response.get('next_cursor')
            response = notion_client.databases.query(
                database_id=database_id,
                filter=filter_obj,
                start_cursor=next_cursor
            )
            
            for result in response.get('results', []):
                properties = result.get('properties', {})
                
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
                
                # Add bottle to results
                bottles.append({
                    'name': name,
                    'type': types,
                    'notes': notes
                })
        
        return bottles
    
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
        response = notion_client.databases.query(
            database_id=database_id,
            filter=filter_obj
        )
        
        # Extract bottle information from the results
        bottles = []
        for result in response.get('results', []):
            properties = result.get('properties', {})
            
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
            
            # Add bottle to results
            bottles.append({
                'name': name,
                'type': types,
                'notes': notes
            })
        
        # Get additional pages if there are more results
        while response.get('has_more', False):
            next_cursor = response.get('next_cursor')
            response = notion_client.databases.query(
                database_id=database_id,
                filter=filter_obj,
                start_cursor=next_cursor
            )
            
            for result in response.get('results', []):
                properties = result.get('properties', {})
                
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
                
                # Add bottle to results
                bottles.append({
                    'name': name,
                    'type': types,
                    'notes': notes
                })
        
        return bottles
    
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
        response = notion_client.databases.query(
            database_id=database_id,
            filter=filter_obj
        )
        
        # Extract bottle information from the results
        bottles = []
        for result in response.get('results', []):
            properties = result.get('properties', {})
            
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
            
            # Add bottle to results
            bottles.append({
                'name': name,
                'type': types,
                'notes': notes
            })
        
        # Get additional pages if there are more results
        while response.get('has_more', False):
            next_cursor = response.get('next_cursor')
            response = notion_client.databases.query(
                database_id=database_id,
                filter=filter_obj,
                start_cursor=next_cursor
            )
            
            for result in response.get('results', []):
                properties = result.get('properties', {})
                
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
                
                # Add bottle to results
                bottles.append({
                    'name': name,
                    'type': types,
                    'notes': notes
                })
        
        return bottles
    
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
        response = notion_client.databases.query(
            database_id=database_id
        )
        
        # Extract bottle information from the results
        bottles = []
        for result in response.get('results', []):
            properties = result.get('properties', {})
            
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
            
            # Add bottle to results
            bottles.append({
                'name': name,
                'type': types,
                'notes': notes
            })
        
        # Get additional pages if there are more results
        while response.get('has_more', False):
            next_cursor = response.get('next_cursor')
            response = notion_client.databases.query(
                database_id=database_id,
                start_cursor=next_cursor
            )
            
            for result in response.get('results', []):
                properties = result.get('properties', {})
                
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
                
                # Add bottle to results
                bottles.append({
                    'name': name,
                    'type': types,
                    'notes': notes
                })
        
        return bottles
    
    except Exception as e:
        print(f"Error getting all bottles: {e}")
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
    args = parser.parse_args()
    
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    # Load configuration
    config_path = project_root / "etc" / "config.toml"
    config = load_config(config_path)
    
    # Get Notion API key and database ID
    notion_api_key = config["api_keys"]["notion"]
    bottle_db_id = config["notion"]["bottle_inventory_db"]
    
    # Create Notion client
    notion = create_notion_client(notion_api_key)
    
    # If no arguments provided, show help
    if not args.tags and not args.query and not args.name and not args.notes and not args.all:
        parser.print_help()
        print("\nExamples:")
        print("  List all type tags:  python query_inventory.py --tags")
        print("  Query by type:       python query_inventory.py --query amaro")
        print("  Query by multiple types (AND): python query_inventory.py --query amaro \"traditional italian amaro\"")
        print("  Query by name:       python query_inventory.py --name \"Campari\"")
        print("  Query by notes:      python query_inventory.py --notes \"bitter\"")
        print("  List all bottles:    python query_inventory.py --all")
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
        for bottle in bottles:
            print(f"  - {bottle['name']} ({', '.join(bottle['type'])})")
            if bottle['notes']:
                print(f"    Notes: {bottle['notes']}")
    
    # Query bottles by name
    if args.name:
        print(f"Querying bottles with name containing: {args.name}")
        bottles = query_bottles_by_name(notion, bottle_db_id, args.name)
        print(f"Found {len(bottles)} bottles:")
        for bottle in bottles:
            print(f"  - {bottle['name']} ({', '.join(bottle['type'])})")
            if bottle['notes']:
                print(f"    Notes: {bottle['notes']}")
    
    # Query bottles by notes
    if args.notes:
        print(f"Querying bottles with notes containing: {args.notes}")
        bottles = query_bottles_by_notes(notion, bottle_db_id, args.notes)
        print(f"Found {len(bottles)} bottles:")
        for bottle in bottles:
            print(f"  - {bottle['name']} ({', '.join(bottle['type'])})")
            if bottle['notes']:
                print(f"    Notes: {bottle['notes']}")
    
    # List all bottles
    if args.all:
        print("Getting all bottles...")
        bottles = get_all_bottles(notion, bottle_db_id)
        print(f"Found {len(bottles)} bottles:")
        for bottle in bottles:
            print(f"  - {bottle['name']} ({', '.join(bottle['type'])})")
            if bottle['notes']:
                print(f"    Notes: {bottle['notes']}")

if __name__ == "__main__":
    main()
