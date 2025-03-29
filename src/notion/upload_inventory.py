#!/usr/bin/env python3
"""
Upload bottle inventory to Notion database.

This script reads bottle inventory data from a JSONL file and uploads it to a
Notion database using the Notion API.
"""

import json
import os
import sys
from pathlib import Path
import jsonlines
import toml
from notion_client import Client

def load_config(config_path):
    """Load configuration from TOML file."""
    try:
        return toml.load(config_path)
    except Exception as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)

def read_bottle_inventory(inventory_path):
    """Read bottle inventory data from JSONL file."""
    bottles = []
    try:
        with jsonlines.open(inventory_path) as reader:
            for obj in reader:
                bottles.append(obj)
        return bottles
    except Exception as e:
        print(f"Error reading inventory file: {e}")
        sys.exit(1)

def create_notion_client(api_key):
    """Create a Notion client with the provided API key."""
    return Client(auth=api_key)

def upload_to_notion(notion_client, database_id, bottles):
    """Upload bottle inventory to Notion database."""
    success_count = 0
    error_count = 0
    
    for bottle in bottles:
        try:
            # Create properties for the Notion page
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": bottle["name"]
                            }
                        }
                    ]
                },
                "Type": {
                    "multi_select": [
                        {"name": type_item} for type_item in bottle["type"]
                    ]
                }
            }
            
            # Add notes if present
            if "notes" in bottle and bottle["notes"]:
                properties["Notes"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": bottle["notes"]
                            }
                        }
                    ]
                }
            
            # Create the page in the database
            notion_client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            
            success_count += 1
            print(f"Uploaded: {bottle['name']}")
            
        except Exception as e:
            error_count += 1
            print(f"Error uploading {bottle['name']}: {e}")
    
    return success_count, error_count

def main():
    """Main function to run the script."""
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    # Load configuration
    config_path = project_root / "etc" / "config.toml"
    config = load_config(config_path)
    
    # Get Notion API key and database ID
    notion_api_key = config["api_keys"]["notion"]
    bottle_db_id = config["notion"]["bottle_inventory_db"]
    
    # Get inventory file path
    data_dir = config["paths"]["data_dir"]
    if data_dir.startswith("./"):
        data_dir = data_dir[2:]  # Remove leading './'
    inventory_path = project_root / data_dir / "bottle_inventory.jsonl"
    
    # Read bottle inventory
    bottles = read_bottle_inventory(inventory_path)
    print(f"Found {len(bottles)} bottles in inventory")
    
    # Create Notion client
    notion = create_notion_client(notion_api_key)
    
    # Upload to Notion
    print(f"Uploading to Notion database: {bottle_db_id}")
    success, errors = upload_to_notion(notion, bottle_db_id, bottles)
    
    # Print summary
    print(f"\nUpload complete!")
    print(f"Successfully uploaded: {success}")
    print(f"Errors: {errors}")

if __name__ == "__main__":
    main()
