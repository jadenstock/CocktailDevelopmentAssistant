import asyncio
import typer
import toml
from dataclasses import dataclass, field
from typing import Dict, List
from agents import Agent, ModelSettings, Runner, WebSearchTool, FileSearchTool
from src.settings import INSTA_POST_OPENAI_DB
from src.notion.notion_tools import (
    get_all_bottles_tool,
    get_available_ingredients_tool,
    save_cocktail_to_notion_tool,
    update_notion_bottle_tool
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
    handoff_description="Finds cocktail specs from reputible sources from the internet.",
    tools=[WebSearchTool(search_context_size="medium")],
    model=cocktail_spec_finder_agent_config["cocktail_spec_finder"]["model"],
    model_settings=ModelSettings(temperature=cocktail_spec_finder_agent_config["cocktail_spec_finder"]["temperature"])
)

flavor_affinity_config = toml.load("etc/flavor_affinity_agent.toml")
flavor_affinity_agent = Agent(
    name="Flavor Affinity Agent",
    instructions=flavor_affinity_config["flavor_affinity_agent"]["instructions"],
    handoff_description="Finds flavor affinities from the internet.",
    tools=[WebSearchTool(search_context_size="medium")],
    model=flavor_affinity_config["flavor_affinity_agent"]["model"],
    model_settings=ModelSettings(temperature=flavor_affinity_config["flavor_affinity_agent"]["temperature"])
)

cocktail_spec_analyzer_agent_config = toml.load("etc/cocktail_spec_analyzer.toml")
cocktail_spec_analyzer = Agent(
    name="Cocktail Spec Analyzer",
    instructions=cocktail_spec_analyzer_agent_config["cocktail_spec_analyzer"]["instructions"],
    handoff_description="Analyzes a cocktail spec and provides feedback.",
    tools=[WebSearchTool(search_context_size="medium")],
    model=cocktail_spec_analyzer_agent_config["cocktail_spec_analyzer"]["model"],
    model_settings=ModelSettings(temperature=cocktail_spec_analyzer_agent_config["cocktail_spec_analyzer"]["temperature"])
)

cocktail_naming_agent_config = toml.load("etc/cocktail_naming_agent.toml")
cocktail_naming_agent = Agent(
    name="Cocktail Naming Agent",
    instructions=cocktail_naming_agent_config["cocktail_naming_agent"]["instructions"],
    handoff_description="Creates a creative name for a cocktail.",
    tools=[],
    model=cocktail_naming_agent_config["cocktail_naming_agent"]["model"],
    model_settings=ModelSettings(temperature=cocktail_naming_agent_config["cocktail_naming_agent"]["temperature"])
)

bottle_inventory_agent_config = toml.load("etc/bottle_inventory_agent.toml")
bottle_inventory_agent = Agent(
    name="Bottle Inventory Agent",
    instructions=bottle_inventory_agent_config["bottle_inventory_agent"]["instructions"],
    handoff_description="Finds relevant bottles from the inventory.",
    tools=[
        get_all_bottles_tool,
        get_available_ingredients_tool
    ],
    model=bottle_inventory_agent_config["bottle_inventory_agent"]["model"],
    model_settings=ModelSettings(temperature=bottle_inventory_agent_config["bottle_inventory_agent"]["temperature"])
)

insta_post_agent_config = toml.load("etc/instagram_post_agent.toml")
insta_vector_id = INSTA_POST_OPENAI_DB
instagram_post_agent = Agent(
    name="Instagram Post Agent",
    instructions=insta_post_agent_config["instagram_post_agent"]["instructions"],
    handoff_description="Finds relevant instagram posts from db of old posts.",
    tools=[
        FileSearchTool(
            max_num_results=5,
            vector_store_ids=[insta_vector_id],
        )
    ],
    model=insta_post_agent_config["instagram_post_agent"]["model"],
    model_settings=ModelSettings(temperature=insta_post_agent_config["instagram_post_agent"]["temperature"])
)

instructions_config = toml.load("etc/main_agent_instructions.toml")
main_agent = Agent(
    name="Cocktail Development Orchestrator",
    instructions=instructions_config["main_agent"]["instructions"],
    tools=[
        cocktail_spec_finder.as_tool(
            tool_name="find_cocktail_specs",
            tool_description="Find cocktail specs given a general query.",
        ),
        flavor_affinity_agent.as_tool(
            tool_name="find_flavor_affinities",
            tool_description="Find flaor affinities given one or more flavors.",
        ),
        get_all_bottles_tool,
        get_available_ingredients_tool,
        cocktail_spec_analyzer.as_tool(
            tool_name="analyze_cocktail_spec",
            tool_description="Analyze a cocktail spec to get feedback.",
        ),
        cocktail_naming_agent.as_tool(
            tool_name="create_cocktail_name",
            tool_description="Create a cocktail name given a spec.",
        ),
        instagram_post_agent.as_tool(
            tool_name="find_relevant_instagram_posts",
            tool_description="Find relevant historical instagram posts for previous projects.",
        ),
        save_cocktail_to_notion_tool
    ],
    model=instructions_config["main_agent"]["model"],
)

bottle_researcher_agent_config = toml.load("etc/bottle_researcher_agent.toml")
bottle_researcher_agent = Agent(
    name="Bottle Researcher",
    instructions=bottle_researcher_agent_config["bottle_researcher_agent"]["instructions"],
    handoff_description="Researches and updates information about bottles in the inventory.",
    tools=[
        WebSearchTool(search_context_size="medium"),
        get_all_bottles_tool,
        update_notion_bottle_tool
    ],
    model=bottle_researcher_agent_config["bottle_researcher_agent"]["model"],
    model_settings=ModelSettings(temperature=bottle_researcher_agent_config["bottle_researcher_agent"]["temperature"])
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
    "bottle_researcher": bottle_researcher_agent,
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