#!/usr/bin/env python3
"""
Populate the OpenAI vector store with data from the Instagram posts JSONL file.

This script populates the vector store specified in the config file with
data from the insta_posts.jsonl file. It can be used to initialize or
update the vector store.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

import toml
import openai

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("vector_store_population.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Disable httpx INFO logging
logging.getLogger("httpx").setLevel(logging.WARNING)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Populate the OpenAI vector store with data from the Instagram posts JSONL file"
    )
    parser.add_argument(
        "-c", "--config",
        help="Path to the configuration file",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force update even if files already exist in the vector store",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check the status of the vector store without populating it",
    )
    return parser.parse_args()


def get_paths(config_path=None):
    """Get the paths to the configuration and data files."""
    if config_path is None:
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent
        config_path = project_root / "etc" / "config.toml"
        data_path = project_root / "data" / "insta_posts.jsonl"
    else:
        config_path = Path(config_path)
        project_root = config_path.parent.parent
        data_path = project_root / "data" / "insta_posts.jsonl"
    
    # Check if files exist
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"JSONL data file not found: {data_path}")
    
    return config_path, data_path


def check_vector_store_status(client, vector_store_id):
    """
    Check the status of files in the vector store.
    
    Args:
        client: The OpenAI client
        vector_store_id: The ID of the vector store
        
    Returns:
        A list of files in the vector store
    """
    try:
        # Get the vector store details
        vector_store = client.vector_stores.retrieve(vector_store_id)
        
        # Get the files in the vector store
        files = client.vector_stores.files.list(vector_store_id=vector_store_id)
        
        print(f"Vector Store: {vector_store.name} (ID: {vector_store.id})")
        print(f"Total files: {len(files.data)}")
        
        # Check statuses
        statuses = {}
        for file in files.data:
            status = file.status
            statuses[status] = statuses.get(status, 0) + 1
        
        for status, count in statuses.items():
            print(f"  - {status}: {count} files")
        
        return files.data
    except Exception as e:
        logger.error(f"Error checking vector store status: {e}")
        return []


def populate_vector_store(client, vector_store_id, data_path, force_update=True):
    """
    Populate the vector store with data from the JSONL file.
    
    Args:
        client: The OpenAI client
        vector_store_id: The ID of the vector store
        data_path: The path to the JSONL file
        force_update: If True, force update even if files already exist
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if the vector store already has files
        if not force_update:
            try:
                files = client.vector_stores.files.list(vector_store_id=vector_store_id)
                if len(files.data) > 0:
                    logger.info(f"Vector store already has {len(files.data)} files. Use --force to update anyway.")
                    return True
            except Exception as e:
                logger.warning(f"Could not check vector store files: {e}")
        
        logger.info(f"Populating vector store {vector_store_id} with data from {data_path}")
        
        # Read the JSONL file
        with open(data_path, "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]
        
        logger.info(f"Found {len(records)} records in JSONL file")
        
        # Create temporary files for each record
        temp_files = []
        for i, record in enumerate(records):
            # Create a meaningful filename
            title = record.get("title", "untitled").replace(" ", "_")
            filename = f"cocktail_{i}_{title}.json"
            temp_file_path = os.path.join(os.path.dirname(data_path), filename)
            
            # Write each record as a separate file
            with open(temp_file_path, "w", encoding="utf-8") as temp_file:
                json.dump(record, temp_file, ensure_ascii=False, indent=2)
            
            temp_files.append(temp_file_path)
        
        logger.info(f"Created {len(temp_files)} temporary files")
        
        # Upload each file to OpenAI and add to the vector store
        successful_uploads = 0
        failed_uploads = 0
        
        for temp_file_path in temp_files:
            try:
                # Upload the file to OpenAI
                with open(temp_file_path, "rb") as file_content:
                    file_response = client.files.create(
                        file=file_content,
                        purpose="user_data"
                    )
                
                # Add the file to the vector store
                client.vector_stores.files.create(
                    vector_store_id=vector_store_id,
                    file_id=file_response.id
                )
                
                logger.info(f"Successfully uploaded {os.path.basename(temp_file_path)} to vector store")
                successful_uploads += 1
                
            except Exception as e:
                logger.error(f"Error uploading {os.path.basename(temp_file_path)}: {str(e)}")
                failed_uploads += 1
            
            # Clean up the temporary file
            try:
                os.remove(temp_file_path)
            except:
                pass
        
        logger.info(f"Upload complete: {successful_uploads} successful, {failed_uploads} failed")
        return successful_uploads > 0
    except Exception as e:
        logger.error(f"Error populating vector store: {e}")
        return False


def main():
    """Main function."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Get the paths to the configuration and data files
        config_path, data_path = get_paths(args.config)
        
        # Load configuration
        config = toml.load(config_path)
        
        # Check if we have a vector store ID in the config
        if "openai" not in config or "insta_post_vector_db" not in config["openai"]:
            logger.error("Vector store ID not found in config file")
            print("Please add a vector store ID to the config file under [openai] section:")
            print("insta_post_vector_db = \"your_vector_store_id\"")
            sys.exit(1)
        
        # Get the vector store ID
        vector_store_id = config["openai"]["insta_post_vector_db"]
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=config["api_keys"]["openai"])
        
        # Check the status of the vector store
        if args.check:
            check_vector_store_status(client, vector_store_id)
            sys.exit(0)
        
        # Populate the vector store
        success = populate_vector_store(client, vector_store_id, data_path, args.force)
        
        if success:
            print("Vector store populated successfully")
            # Check the status of the vector store
            check_vector_store_status(client, vector_store_id)
        else:
            print("Failed to populate vector store")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
