export OPENAI_API_KEY := $(shell python -c "import toml; import os.path; config_path = 'etc/local_config.toml' if os.path.exists('etc/local_config.toml') else 'etc/config.toml'; print(toml.load(config_path)['api_keys']['openai'])")

run-agent:
	export PYTHONPATH=. && python src/cocktail_dev_agent.py --agent $(or $(agent),main)

run-wine-agent:
	export PYTHONPATH=. && python src/cocktail_dev_agent.py --agent wine

run-ui:
	export PYTHONPATH=. && streamlit run src/ui.py

list-bottles:
	export PYTHONPATH=. && python src/notion/query_inventory.py --all

list-ingredients:
	export PYTHONPATH=. && python src/notion/query_inventory.py --ingredients

list-wines:
	export PYTHONPATH=. && python src/notion/query_inventory.py --wines

list-bottles-by-type:
	export PYTHONPATH=. && python src/notion/query_inventory.py --query $(type)

list-bottles-by-notes:
	export PYTHONPATH=. && python src/notion/query_inventory.py --notes $(notes)

test-update-inventory:
	export PYTHONPATH=. && python src/notion/update_inventory.py

test-save-cocktail:
	export PYTHONPATH=. && python src/notion/save_cocktails.py