export OPENAI_API_KEY := $(shell python -c "import toml; import os.path; config_path = 'etc/local_config.toml' if os.path.exists('etc/local_config.toml') else 'etc/config.toml'; print(toml.load(config_path)['api_keys']['openai'])")

run-agent:
	set PYTHONPATH=. && python src/cocktail_dev_agent.py --agent $(or $(agent),main)