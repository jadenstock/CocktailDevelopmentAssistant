from agents import Agent, Runner, handoff, WebSearchTool
import asyncio
import argparse

import toml

from src.notion.notion_tools import (
    query_bottles_by_type_tool,
    query_bottles_by_name_tool,
    get_available_types_tool
)

instructions_config = toml.load("etc/instructions.toml")

# Define sub-agents
cocktail_spec_finder = Agent(
    name="Cocktail Spec Finder",
    instructions=instructions_config["cocktail_spec_finder"]["instructions"],
    tools=[WebSearchTool()]
)

flavor_affinity_agent = Agent(
    name="Flavor Affinity Agent",
    instructions=instructions_config["flavor_affinity_agent"]["instructions"],
    tools=[WebSearchTool()]
)

cocktail_spec_analyzer = Agent(
    name="Cocktail Spec Analyzer",
    instructions=instructions_config["cocktail_spec_analyzer"]["instructions"],
    tools=[]
)

cocktail_naming_agent = Agent(
    name="Cocktail Naming Agent",
    instructions=instructions_config["cocktail_naming_agent"]["instructions"],
    tools=[]
)

bottle_inventory_agent = Agent(
    name="Bottle Inventory Agent",
    instructions=instructions_config["bottle_inventory_agent"]["instructions"],
    tools=[
        query_bottles_by_type_tool,
        query_bottles_by_name_tool,
        get_available_types_tool
    ]
)

# Main agent orchestrating handoffs
main_agent = Agent(
    name="Cocktail Development Orchestrator",
    instructions=instructions_config["main_agent"]["instructions"],
    handoffs=[
        cocktail_spec_finder,
        flavor_affinity_agent,
        bottle_inventory_agent,
        cocktail_spec_analyzer,
        cocktail_naming_agent
    ]
)

async def main():
    print("Starting cocktail development agent...")
    print("Type your cocktail request (e.g., 'Find me a pear-forward cocktail and suggest a name')\n")
    
    # Get input interactively
    while True:
        try:
            query = input("Your cocktail request (or 'quit' to exit): ")
            if query.lower() in ('quit', 'exit', 'q'):
                break
                
            if not query.strip():
                print("Please enter a valid request.")
                continue
                
            print("\nProcessing your request...\n")
            result = await Runner.run(main_agent, input=query)
            print("\nResults:")
            print(result.final_output)
            print("\n" + "="*50 + "\n")  # Add separator for clarity
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    asyncio.run(main())