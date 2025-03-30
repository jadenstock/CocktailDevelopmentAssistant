import toml

try:
    secrets_config = toml.load("etc/local_config.toml")
except:
    secrets_config = toml.load("etc/config.toml")

OPENAI_API_KEY = secrets_config["api_keys"]["openai"]
NOTION_API_KEY = secrets_config["api_keys"]["notion"]

BOTTLE_INVENTORY_NOTION_DB = secrets_config["notion"]["bottle_inventory_db"]
INSTA_POST_OPENAI_DB = secrets_config["openai"]["insta_post_vector_db"]