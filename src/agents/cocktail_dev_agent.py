import asyncio
import typer
import toml
from dataclasses import dataclass, field
from typing import Dict, List
from agents import Agent, Runner, WebSearchTool, FileSearchTool
from src.settings import INSTA_POST_OPENAI_DB
from src.notion.notion_tools import (
    query_bottles_by_type_tool,
    query_bottles_by_name_tool,
    get_available_types_tool,
    get_all_bottles_tool
)

app = typer.Typer()

@dataclass
class ConversationContext:
    history: List[Dict[str, str]] = field(default_factory=list)
    preferences: Dict = field(default_factory=dict)

# === Initialize All Agents ===
cocktail_spec_finder_agent_config = toml.load("etc/cocktail_spec_finder.toml")
cocktail_spec_finder = Agent(
    name="Cocktail Spec Finder",
    instructions=cocktail_spec_finder_agent_config["cocktail_spec_finder"]["instructions"],
    tools=[WebSearchTool()],
    model=cocktail_spec_finder_agent_config["cocktail_spec_finder"]["model"]
)

flavor_affinity_config = toml.load("etc/flavor_affinity_agent.toml")
flavor_affinity_agent = Agent(
    name="Flavor Affinity Agent",
    instructions=flavor_affinity_config["flavor_affinity_agent"]["instructions"],
    tools=[WebSearchTool()],
    model=flavor_affinity_config["flavor_affinity_agent"]["model"]
)

cocktail_spec_analyzer_agent_config = toml.load("etc/cocktail_spec_analyzer.toml")
cocktail_spec_analyzer = Agent(
    name="Cocktail Spec Analyzer",
    instructions=cocktail_spec_analyzer_agent_config["cocktail_spec_analyzer"]["instructions"],
    tools=[WebSearchTool()],
    model=cocktail_spec_analyzer_agent_config["cocktail_spec_analyzer"]["model"]
)

cocktail_naming_agent_config = toml.load("etc/cocktail_naming_agent.toml")
cocktail_naming_agent = Agent(
    name="Cocktail Naming Agent",
    instructions=cocktail_naming_agent_config["cocktail_naming_agent"]["instructions"],
    tools=[],
    model=cocktail_naming_agent_config["cocktail_naming_agent"]["model"]
)

bottle_inventory_agent_config = toml.load("etc/bottle_inventory_agent.toml")
bottle_inventory_agent = Agent(
    name="Bottle Inventory Agent",
    instructions=bottle_inventory_agent_config["bottle_inventory_agent"]["instructions"],
    tools=[
        get_all_bottles_tool
    ],
    model=bottle_inventory_agent_config["bottle_inventory_agent"]["model"]
)

insta_post_agent_config = toml.load("etc/instagram_post_agent.toml")
insta_vector_id = INSTA_POST_OPENAI_DB
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

# === Create a Mapping of Agent Names ===
AGENTS = {
    "main": main_agent,
    "cocktail_spec_finder": cocktail_spec_finder,
    "flavor_affinity": flavor_affinity_agent,
    "cocktail_spec_analyzer": cocktail_spec_analyzer,
    "cocktail_naming": cocktail_naming_agent,
    "bottle_inventory": bottle_inventory_agent,
    "instagram_post": instagram_post_agent,
}

@app.command()
def run(agent: str = typer.Option("main", help=f"Specify which agent to use. options: {AGENTS.keys()}")):
    """Run the chatbot with the selected agent."""
    if agent not in AGENTS:
        typer.echo(f"Error: Agent '{agent}' not found. Available agents: {', '.join(AGENTS.keys())}")
        raise typer.Exit(1)

    selected_agent = AGENTS[agent]
    typer.echo(f"Running {selected_agent.name}...\n")

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

                context.history.append({"role": "user", "content": user_input})
                prompt = "\n".join(f"{msg['role']}: {msg['content']}" for msg in context.history[-6:])

                result = await Runner.run(
                    selected_agent,
                    input=prompt,
                    context={"preferences": context.preferences}
                )

                ai_response = result.final_output
                context.history.append({"role": "assistant", "content": ai_response})

                print(f"\nAssistant: {ai_response}")

            except KeyboardInterrupt:
                print("\nEnding conversation...")
                break

    asyncio.run(main())

if __name__ == "__main__":
    app()