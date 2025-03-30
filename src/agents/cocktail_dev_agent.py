from agents import Agent, Runner, handoff, WebSearchTool, FileSearchTool, RunContextWrapper
import asyncio
import argparse

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

import toml
import json


from src.notion.notion_tools import (
    query_bottles_by_type_tool,
    query_bottles_by_name_tool,
    get_available_types_tool
)

secrets_config = toml.load("etc/config.toml")



@dataclass
class CocktailContext:
    current_inventory: Dict[str, List[str]] = field(default_factory=dict)
    selected_ingredients: List[str] = field(default_factory=list)
    last_suggestions: List[Dict] = field(default_factory=list)
    user_preferences: Dict = field(default_factory=dict)

# Define sub-agents
cocktail_spec_finder = Agent(
    name="Cocktail Spec Finder",
    instructions=instructions_config["cocktail_spec_finder"]["instructions"],
    tools=[WebSearchTool()],
    model=instructions_config["cocktail_spec_finder"]["model"]
)

flavor_affinity_config = toml.load("etc/flavor_affinity_agent.toml")
flavor_affinity_agent = Agent(
    name="Flavor Affinity Agent",
    instructions=flavor_affinity_config["flavor_affinity_agent"]["instructions"],
    tools=[WebSearchTool()],
    model=flavor_affinity_config["flavor_affinity_agent"]["model"]
)

cocktail_spec_analyzer = Agent(
    name="Cocktail Spec Analyzer",
    instructions=instructions_config["cocktail_spec_analyzer"]["instructions"],
    tools=[WebSearchTool()],
    model=instructions_config["cocktail_spec_analyzer"]["model"]
)

cocktail_naming_agent = Agent(
    name="Cocktail Naming Agent",
    instructions=instructions_config["cocktail_naming_agent"]["instructions"],
    tools=[],
    model=instructions_config["cocktail_naming_agent"]["model"]
)

bottle_inventory_agent = Agent(
    name="Bottle Inventory Agent",
    instructions=instructions_config["bottle_inventory_agent"]["instructions"],
    tools=[
        query_bottles_by_type_tool,
        query_bottles_by_name_tool,
        get_available_types_tool
    ],
    model=instructions_config["bottle_inventory_agent"]["model"]
)

insta_post_agent_config = toml.load("etc/instagram_post_agent.toml")
insta_vector_id = secrets_config["openai"]["insta_post_vector_db"]
instagram_post_agent = Agent(
    name="Instagram Post Agent",
    instructions=insta_post_agent_config["instagram_post_agent"]["instructions"],
    tools=[
        FileSearchTool(
            max_num_results=5,
            vector_store_ids=[insta_vector_id],
        )
    ],
    model=insta_post_agent_config["instagram_post_agent"]["model"]
)

instructions_config = toml.load("etc/agent_instructions.toml")
# Main agent orchestrating handoffs
main_agent = Agent(
    name="Cocktail Development Orchestrator",
    instructions=instructions_config["main_agent"]["instructions"],
    handoffs=[
        cocktail_spec_finder,
        flavor_affinity_agent,
        bottle_inventory_agent,
        cocktail_spec_analyzer,
        cocktail_naming_agent,
        instagram_post_agent
    ]
)


@dataclass
class ConversationContext:
    history: List[Dict[str, str]] = field(default_factory=list)
    preferences: Dict = field(default_factory=dict)

async def main():
    print("=== Cocktail Conversation ===")
    print("Describe what you're craving or type 'exit'\n")
    
    context = ConversationContext()
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ('exit', 'quit', 'q'):
                break
                
            if not user_input:
                continue
                
            # Add to conversation history
            context.history.append({"role": "user", "content": user_input})
            
            # Generate prompt with full history
            prompt = "\n".join(
                f"{msg['role']}: {msg['content']}" 
                for msg in context.history[-6:]  # Keep last 6 exchanges
            )
            
            # Get AI response - CORRECTED CALL
            result = await Runner.run(
                main_agent,  # Positional argument
                input=prompt,
                context={"preferences": context.preferences}
            )
            
            # Store response
            ai_response = result.final_output
            context.history.append({"role": "assistant", "content": ai_response})
            
            print(f"\nAssistant: {ai_response}")
            
        except KeyboardInterrupt:
            print("\nEnding conversation...")
            break

if __name__ == "__main__":
    asyncio.run(main())