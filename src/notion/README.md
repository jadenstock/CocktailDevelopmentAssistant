# Abstract Notion Tools System

A configurable, abstract framework for working with Notion databases that eliminates the need to write custom code for each database. Simply configure your database schema and get auto-generated tools for reading, writing, and querying.

## Features

- **Zero-code database integration**: Configure databases in TOML, get tools automatically
- **Type-safe operations**: Built-in validation for all database operations
- **Flexible filtering**: Support for complex queries with predefined and custom filters
- **Backward compatibility**: Drop-in replacement for existing notion_tools.py
- **Dynamic tool generation**: Tools are created automatically based on your schema
- **Multiple database support**: Manage multiple Notion databases from a single configuration

## Quick Start

### 1. Configure Your Database

Create or update `etc/databases_config.toml`:

```toml
[databases.my_database]
database_id = "your_notion_database_id"
description = "My custom database"
primary_key_column = "Name"

[databases.my_database.columns.Name]
type = "title"
permission = "read_write"
description = "The name field"
required = true

[databases.my_database.columns.Status]
type = "select"
permission = "read_write"
description = "Current status"

[databases.my_database.filters.active]
column_name = "Status"
filter_type = "equals"
value = "Active"
description = "Only active records"
```

### 2. Generate Tools

```python
from src.notion.abstract_notion_tools import get_notion_tools

# Initialize the system
notion_tools = get_notion_tools()

# Generate all tools
tools = notion_tools.generate_all_tools()

# Use the auto-generated tools
get_all_my_database = tools["get_all_my_database"]
search_my_database = tools["search_my_database"]
create_my_database_record = tools["create_my_database_record"]

# Use them in your agents
results = await get_all_my_database()
```

### 3. Add to Agent Tools

```python
from agents import Agent
from src.notion.abstract_notion_tools import get_all_tools

# Get all auto-generated tools
notion_tools = get_all_tools()

# Create your agent with the tools
agent = Agent(
    tools=list(notion_tools.values()),
    instructions="You can now work with all configured databases!"
)
```

## Configuration Reference

### Database Configuration

```toml
[databases.database_name]
database_id = "notion_database_id"          # Required: Notion database ID
description = "Human readable description"  # Optional: Description
primary_key_column = "Name"                 # Optional: Primary key column (default: "Name")
```

### Column Configuration

```toml
[databases.database_name.columns.column_name]
type = "column_type"                        # Required: See supported types below
permission = "read_write"                   # Required: read, write, or read_write
description = "Column description"          # Optional: Human readable description
required = false                           # Optional: Whether required for creation (default: false)
```

#### Supported Column Types

- `title` - Title/name field (required for every database)
- `rich_text` - Multi-line text
- `multi_select` - Multiple choice tags
- `select` - Single choice dropdown
- `checkbox` - Boolean true/false
- `number` - Numeric values
- `date` - Date fields
- `url` - URL fields
- `email` - Email fields
- `phone_number` - Phone number fields
- `people` - Person/user references
- `files` - File attachments

### Filter Configuration

```toml
[databases.database_name.filters.filter_name]
column_name = "column_to_filter"            # Required: Column to filter on
filter_type = "equals"                      # Required: Type of filter
value = "filter_value"                      # Required: Value to filter by
description = "Filter description"          # Optional: Human readable description
```

#### Supported Filter Types

- `equals`, `does_not_equal` - Exact matching
- `contains`, `does_not_contain` - Text contains
- `starts_with`, `ends_with` - Text starts/ends with
- `is_empty`, `is_not_empty` - Empty/non-empty fields
- `greater_than`, `less_than` - Numeric/date comparisons
- `greater_than_or_equal_to`, `less_than_or_equal_to` - Inclusive comparisons
- `on_or_after`, `on_or_before` - Date comparisons
- `past_week`, `past_month`, `past_year` - Relative date filters
- `next_week`, `next_month`, `next_year` - Future date filters

## Auto-Generated Tools

For each configured database, the system automatically generates:

### Query Tools
- `get_all_{database_name}` - Get all records
- `search_{database_name}` - Full-text search across all text fields
- `get_{database_name}_{filter_name}` - Apply predefined filters
- `search_{database_name}_by_{column_name}` - Search by specific columns

### Write Tools (if writable columns exist)
- `create_{database_name}_record` - Create new records
- `update_{database_name}_record` - Update existing records

## Advanced Usage

### Custom Filters at Runtime

```python
from src.notion.database_config import FilterConfig
from src.notion.abstract_notion_tools import get_notion_tools

notion_tools = get_notion_tools()

# Create a custom filter
custom_filter = FilterConfig(
    column_name="Date",
    filter_type="on_or_after",
    value="2024-01-01",
    description="Records from this year"
)

# Use the query engine directly
results = notion_tools.tool_generator.query_engine.query_database(
    "my_database",
    custom_filters=[custom_filter]
)
```

### Adding Databases at Runtime

```python
# Define a new database configuration
fitness_config = {
    "database_id": "your_fitness_db_id",
    "description": "Fitness tracking database",
    "columns": {
        "Date": {"type": "date", "permission": "read_write", "required": True},
        "Exercise": {"type": "title", "permission": "read_write", "required": True},
        "Duration": {"type": "number", "permission": "read_write"},
        "Completed": {"type": "checkbox", "permission": "read_write"}
    },
    "filters": {
        "completed": {
            "column_name": "Completed",
            "filter_type": "equals",
            "value": True
        }
    }
}

# Add it to the system
notion_tools.add_database_from_config("fitness_tracking", fitness_config)
```

### Validation

```python
from src.notion.validation import validate_configuration_file, create_validation_report

# Validate your configuration
is_valid, errors = validate_configuration_file("etc/databases_config.toml")

if not is_valid:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")

# Generate a detailed report
report = create_validation_report("etc/databases_config.toml")
print(report)
```

## Migration from Legacy System

### Option 1: Compatibility Layer

Use the compatibility layer for instant migration:

```python
# Replace this:
from src.notion.notion_tools import get_all_bottles_tool

# With this:
from src.notion.migration_helper import create_legacy_compatibility_layer
legacy_tools = create_legacy_compatibility_layer()
get_all_bottles_tool = legacy_tools["get_all_bottles_tool"]
```

### Option 2: Gradual Migration

1. Keep existing imports working
2. Start using new tool names for new code
3. Gradually update existing code
4. Remove old system once migration is complete

```python
# New approach
from src.notion.abstract_notion_tools import get_all_tools
all_tools = get_all_tools()

# Use the new tool names
get_all_bottles = all_tools["get_all_bottle_inventory"]
search_bottles = all_tools["search_bottle_inventory"]
```

## Error Handling

The system includes comprehensive error handling:

```python
try:
    results = await get_all_my_database()
except Exception as e:
    print(f"Database query failed: {e}")
    # The error message will include specific details about what went wrong
```

Common error scenarios:
- Invalid database configuration
- Missing required fields
- Type validation errors
- Notion API errors
- Network connectivity issues

## Examples

### Fitness Tracking Database

```toml
[databases.workouts]
database_id = "your_workout_db_id"
description = "Personal workout tracking"
primary_key_column = "Date"

[databases.workouts.columns.Date]
type = "date"
permission = "read_write"
required = true

[databases.workouts.columns.Exercise]
type = "title"
permission = "read_write"
required = true

[databases.workouts.columns.Duration]
type = "number"
permission = "read_write"
description = "Duration in minutes"

[databases.workouts.columns.Type]
type = "multi_select"
permission = "read_write"
description = "Workout type"

[databases.workouts.columns.Completed]
type = "checkbox"
permission = "read_write"

[databases.workouts.filters.completed]
column_name = "Completed"
filter_type = "equals"
value = true
description = "Completed workouts"

[databases.workouts.filters.this_week]
column_name = "Date"
filter_type = "past_week"
value = ""
description = "This week's workouts"
```

This generates tools like:
- `get_all_workouts()`
- `search_workouts(search_text)`
- `get_workouts_completed()`
- `get_workouts_this_week()`
- `create_workouts_record(Date, Exercise, Duration=None, Type=None, Completed=None)`
- `update_workouts_record(record_id, **kwargs)`

### Task Management Database

```toml
[databases.tasks]
database_id = "your_tasks_db_id"
description = "Task management system"

[databases.tasks.columns.Name]
type = "title"
permission = "read_write"
required = true

[databases.tasks.columns.Status]
type = "select"
permission = "read_write"
description = "Task status"

[databases.tasks.columns.Priority]
type = "select"
permission = "read_write"
description = "Task priority"

[databases.tasks.columns."Due Date"]
type = "date"
permission = "read_write"

[databases.tasks.columns.Completed]
type = "checkbox"
permission = "read_write"

[databases.tasks.filters.pending]
column_name = "Status"
filter_type = "equals"
value = "In Progress"

[databases.tasks.filters.overdue]
column_name = "Due Date"
filter_type = "on_or_before"
value = "today"
```

## Contributing

When adding new features:

1. Update the appropriate module in `src/notion/`
2. Add validation in `validation.py`
3. Update this README with examples
4. Add tests for new functionality

## Architecture

```
src/notion/
├── database_config.py      # Core configuration classes
├── config_loader.py        # TOML configuration loading
├── generic_query.py        # Database querying engine
├── generic_writer.py       # Database writing engine
├── tool_generator.py       # Dynamic tool generation
├── abstract_notion_tools.py # Main entry point
├── migration_helper.py     # Legacy compatibility
├── validation.py           # Schema validation
└── README.md              # This file
```

The system is designed to be modular and extensible, making it easy to add new features or customize behavior for specific use cases.