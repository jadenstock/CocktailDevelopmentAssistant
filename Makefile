export OPENAI_API_KEY := $(shell python -c "import toml; print(toml.load('etc/config.toml')['api_keys']['openai'])")

run:
	python src/main.py


agent:
	python src/agents/cocktail_dev_agent.py


