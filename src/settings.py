import toml

try:
    secrets_config = toml.load("etc/local_config.toml")
except:
    secrets_config = toml.load("etc/config.toml")

OPENAI_API_KEY = secrets_config["api_keys"]["openai"]
NOTION_API_KEY = secrets_config["api_keys"]["notion"]

BOTTLE_INVENTORY_NOTION_DB = secrets_config["notion"]["bottle_inventory_db"]
INSTA_POST_OPENAI_DB = secrets_config["openai"]["insta_post_vector_db"]

RECOMMENDED_PROMPT_PREFIX = "# System context\nYou are part of a multi-agent system called the Agents SDK, designed to make agent coordination and execution easy. Agents uses two primary abstraction: **Agents** and **Handoffs**. An agent encompasses instructions and tools and can hand off a conversation to another agent when appropriate. Handoffs are achieved by calling a handoff function, generally named `transfer_to_<agent_name>`. Transfers between agents are handled seamlessly in the background; do not mention or draw attention to these transfers in your conversation with the user.\n"
