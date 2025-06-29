import toml

try:
    secrets_config = toml.load("etc/local_config.toml")
except:
    secrets_config = toml.load("etc/config.toml")

OPENAI_API_KEY = secrets_config["api_keys"]["openai"]
NOTION_API_KEY = secrets_config["api_keys"]["notion"]

BOTTLE_INVENTORY_NOTION_DB = secrets_config["notion"]["bottle_inventory_db"]
SYRUPS_AND_JUICES_NOTION_DB = secrets_config["notion"]["syrups_and_juices_db"]
COCKTAIL_PROJECTS_NOTION_DB = secrets_config["notion"]["cocktail_projects_db"]
WINES_NOTION_DB = secrets_config["notion"]["wine_db"]

INSTA_POST_OPENAI_DB = secrets_config["openai"]["insta_post_vector_db"]