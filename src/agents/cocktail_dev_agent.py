from agents import Agent, Runner, handoff, WebSearchTool
import asyncio

import toml
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

# Main agent orchestrating handoffs
main_agent = Agent(
    name="Cocktail Development Orchestrator",
    instructions=instructions_config["main_agent"]["instructions"],
    handoffs=[
        cocktail_spec_finder,
        flavor_affinity_agent,
        cocktail_spec_analyzer,
        cocktail_naming_agent
    ]
)

async def main():
    print("Starting agent...")
    query = "Find me a pear-forward cocktail and suggest a name."
    result = await Runner.run(main_agent, input=query)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
