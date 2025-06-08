# Cocktail Development High Quality

This project is a multi-agent orchestration system for cocktail development. It integrates various agents that fetch cocktail specifications, analyze recipes, generate creative names, manage bottle inventories, and handle Notion-based data operations. The agents communicate via both command-line interactions and Notion API, providing a streamlined workflow for cocktail development and inventory management.

## Overview

The project leverages several agents with dedicated responsibilities:
- **Cocktail Spec Finder:** Searches for cocktail specifications using web search.
- **Flavor Affinity Agent:** Retrieves flavor affinities from online sources.
- **Cocktail Spec Analyzer:** Analyzes cocktail specifications and provides feedback.
- **Cocktail Naming Agent:** Generates creative cocktail names.
- **Bottle Inventory Agent:** Interfaces with a Notion database to list and filter available bottles.
- **Wine Agent:** Retrieves wines from the inventory.
- **Instagram Post Agent:** Searches historical Instagram posts using a file search tool.
- **Bottle Researcher Agent:** Researches and updates bottle information in the inventory.

A main orchestration agent, *Cocktail Development Orchestrator*, ties these functionalities together, providing an interactive Typer CLI interface that guides the user through cocktail development conversations.

## File Structure

- **Makefile**  
  Provides several commands to run different agents and query operations:
  - `run-agent`: Launches the main cocktail development agent.
  - `run-wine-agent`: Starts the wine agent.
  - `list-bottles`: Lists all bottles in the Notion inventory.
  - `list-ingredients`: Lists available ingredients from the Notion inventory.
  - `list-wines`: Lists available wines from the Notion inventory.
  - `list-bottles-by-type`: Filters bottles by their type.
  - `list-bottles-by-notes`: Filters bottles by notes.
  - `test-update-inventory`: Tests updating the Notion inventory.
  - `test-save-cocktail`: Tests saving a cocktail to Notion.

- **etc/**  
  Contains TOML configuration files for each agent including:
  - `cocktail_spec_finder.toml`
  - `flavor_affinity_agent.toml`
  - `cocktail_spec_analyzer.toml`
  - `cocktail_naming_agent.toml`
  - `bottle_inventory_agent.toml`
  - `bottle_researcher_agent.toml`
  - `instagram_post_agent.toml`
  - `wine_agent.toml`
  - `main_agent_instructions.toml`  
  Also contains configuration (`config.toml` and optionally `local_config.toml`) for API keys and settings.

- **src/**  
  Contains the source code:
  - **cocktail_dev_agent.py**  
    Implements the main Typer CLI application that orchestrates the conversation and agent responses.
  - **settings.py**  
    Defines project settings such as API keys and Notion database IDs.
  - **notion/**  
    Includes modules for Notion integration:
    - `query_inventory.py` – Provides functions to query and format bottle inventory, ingredients, and wines from the Notion database.
    - `notion_tools.py`  
    - `save_cocktails.py`  
    - `update_inventory.py`  
    - `upload_inventory.py`
    
- **data/**  
  Contains any project-specific data files.

## Setup and Configuration

1. **Python Environment:**  
   Ensure you have Python 3.x installed. Dependencies are managed via the provided `pyproject.toml`.

2. **Configuration Files:**  
   - Place your API key in either `etc/local_config.toml` or `etc/config.toml` under the `[api_keys]` section (key: `openai`).
   - Make sure other agent-specific configurations in the `etc/` folder are correctly set up according to your requirements.

3. **Notion Integration:**  
   - Verify that the Notion API key and database IDs are properly configured in `src/settings.py`.
   - The project uses Notion’s API to manage bottle inventories, ingredients, and wines.

## Usage

### Running Agents
Use the Makefile commands to run agents from the command line. For example:

- **Start the Main Agent:**
  ```
  make run-agent
  ```
  This launches the interactive cocktail development session.

- **Run the Wine Agent:**
  ```
  make run-wine-agent
  ```

### Querying Inventory
The project includes scripts to query the Notion database for inventory management:
- **List all bottles:**
  ```
  make list-bottles
  ```
- **List available ingredients:**
  ```
  make list-ingredients
  ```
- **List available wines:**
  ```
  make list-wines
  ```
- **Filter bottles by type or notes:**
  Use corresponding commands (`list-bottles-by-type` and `list-bottles-by-notes`) with parameters.

- **Testing Inventory Updates:**
  ```
  make test-update-inventory
  ```
- **Testing Cocktail Save:**
  ```
  make test-save-cocktail
  ```

## Prompt Optimization

The system includes an AI-powered prompt optimization feature that analyzes chat session performance and automatically improves agent prompts.

### How It Works

1. **Rate Conversations:** Use the Streamlit UI to rate chat sessions (1-5 stars) and add feedback notes
2. **Performance Tracking:** The system analyzes ratings and identifies agents that need improvement (avg rating < 3.5/5)
3. **AI Optimization:** A specialized optimizer agent analyzes low-rated sessions and generates improved prompts
4. **Git-Friendly Versioning:** New prompt versions are saved as `agent_v2.toml`, `agent_v3.toml`, etc.

### Usage

**Via Streamlit UI:**
- Go to the "Prompt Management" tab
- View performance metrics for each agent
- Click "Auto-Optimize" for agents that need improvement
- Review and deploy the generated prompt versions

**Via CLI:**
```bash
# Show performance summary
python src/scripts/simple_optimizer.py performance

# List agents that need optimization  
python src/scripts/simple_optimizer.py candidates

# Optimize a specific agent
python src/scripts/simple_optimizer.py optimize main_agent

# Auto-optimize all candidates
python src/scripts/simple_optimizer.py auto
```

### Deploying Optimized Prompts

1. Review the generated file (e.g., `etc/main_agent_v2.toml`)
2. Test the new prompt version
3. If satisfied, replace the original: `mv etc/main_agent_v2.toml etc/main_agent_instructions.toml`
4. Commit to git: `git add . && git commit -m "Optimize main agent prompt"`

The optimization process analyzes conversation patterns, identifies common issues, and generates targeted improvements while preserving the agent's core identity and successful patterns.

## Development and Contribution

- The project follows a modular structure where each agent is defined with specific responsibilities.
- Agents are configured using TOML files in the `etc/` directory that define instructions, model settings, and available tools.
- Contributions and improvements can be made by modifying the configurations or source code in the `src/` directory.
- The prompt optimization system allows for iterative improvement of agent performance based on real usage data.

## Conclusion

This project demonstrates an integrated solution for cocktail development, combining AI-driven agents, web and file search tools, and direct interactions with a Notion database for inventory management. The modular design and clearly defined commands provide a robust framework for experimental and production-grade cocktail development workflows.
