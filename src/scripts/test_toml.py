import toml
import json


def load_and_print_toml(file_path):
    try:
        print(f"\nLoading {file_path}...")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        parsed_toml = toml.loads(content)
        print("\nParsed TOML:")
        for key, value in parsed_toml.items():
            print(f"{key}: {json.dumps(value, indent=2)}")
        return parsed_toml
    except Exception as e:
        print(f"Error loading {file_path}: {e}")

if __name__ == "__main__":
    # instructions_config = load_and_print_toml("etc/agent_instructions.toml")
    instructions_config = load_and_print_toml("etc/flavor_affinity_agent.toml")