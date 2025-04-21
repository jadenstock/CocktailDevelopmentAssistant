export OPENAI_API_KEY := $(shell python -c "import toml; import os.path; config_path = 'etc/local_config.toml' if os.path.exists('etc/local_config.toml') else 'etc/config.toml'; print(toml.load(config_path)['api_keys']['openai'])")

run-agent:
	set PYTHONPATH=. && python src/cocktail_dev_agent.py --agent $(or $(agent),main)

list-bottles:
	set PYTHONPATH=. && python src/notion/query_inventory.py --all

list-bottles-by-type:
	set PYTHONPATH=. && python src/notion/query_inventory.py --query $(type)

list-bottles-by-notes:
	set PYTHONPATH=. && python src/notion/query_inventory.py --notes $(notes)

test-update-inventory:
	set PYTHONPATH=. && python src/notion/update_inventory.py

test-save-cocktail:
	set PYTHONPATH=. && python src/notion/save_cocktails.py