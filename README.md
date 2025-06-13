# NEXARIS Adaptive Scenario Engine (NASE)

## Overview
The NEXARIS Adaptive Scenario Engine (NASE) is an intelligent cybersecurity training platform that dynamically adapts phishing and cyber-alert scenarios based on user performance. This engine demonstrates real-time intelligence adaptation and foresight by adjusting scenario difficulty according to user responses and cognitive load.

## Key Features
- **Dynamic Scenario Presentation**: Delivers customized cybersecurity scenarios to users
- **Adaptive Difficulty**: Automatically adjusts scenario complexity based on user performance
- **Performance Tracking**: Logs and analyzes user responses over time
- **Cognitive Load Integration**: Optional connection to cognitive load estimators to adapt to user mental fatigue
- **LLM Integration**: Optional connection to local LLM APIs for generating creative phishing content

## Project Structure
```
NEXARIS NASE/
├── README.md                     # Project documentation
├── requirements.txt              # Python dependencies
├── nase/                         # Main package directory
│   ├── __init__.py               # Package initialization
│   ├── engine.py                 # Core adaptive engine
│   ├── scenario_manager.py       # Scenario loading and selection
│   ├── user_manager.py           # User performance tracking
│   ├── difficulty_adjuster.py    # Scenario difficulty adjustment
│   ├── cognitive_load.py         # Cognitive load estimation integration
│   ├── llm_integration.py        # LLM API integration for content generation
│   └── database/                 # Database management
│       ├── __init__.py
│       ├── db_manager.py         # Database operations
│       └── models.py             # Data models
├── data/                         # Data directory
│   ├── scenarios.json            # Sample scenarios (JSON format)
│   └── scenarios.db              # SQLite database (alternative)
└── examples/                     # Example scripts
    ├── run_engine.py             # Basic engine usage example
    ├── cognitive_load_demo.py    # Demo with cognitive load integration
    └── llm_generation_demo.py    # Demo with LLM content generation
```

## Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/nexaris-nase.git
cd nexaris-nase

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage
```python
from nase.engine import AdaptiveEngine

# Initialize the engine
engine = AdaptiveEngine(database_path="data/scenarios.json")

# Start a session for a user
engine.start_session(user_id="user123")

# Get the next scenario
scenario = engine.get_next_scenario()

# Process user response
engine.process_response(scenario_id=scenario["id"], correct=True)

# End the session and save progress
engine.end_session()
```

### With Cognitive Load Integration
```python
from nase.engine import AdaptiveEngine
from nase.cognitive_load import NCLEConnector

# Initialize cognitive load estimator
cognitive_load_estimator = NCLEConnector(api_key="your_api_key")

# Initialize the engine with cognitive load integration
engine = AdaptiveEngine(
    database_path="data/scenarios.json",
    cognitive_load_estimator=cognitive_load_estimator
)

# The engine will now adapt based on both performance and cognitive load
```

### With LLM Content Generation
```python
from nase.engine import AdaptiveEngine
from nase.llm_integration import LLMConnector

# Initialize LLM connector
llm_connector = LLMConnector(model="local_llm", api_key="your_api_key")

# Initialize the engine with LLM integration
engine = AdaptiveEngine(
    database_path="data/scenarios.json",
    llm_connector=llm_connector
)

# Generate a new scenario with LLM
new_scenario = engine.generate_scenario(difficulty=3, theme="password phishing")
```

## Real-time Intelligence Adaptation

The NEXARIS Adaptive Scenario Engine demonstrates real-time intelligence through:

1. **Performance-Based Adaptation**: The engine analyzes user responses and adjusts scenario difficulty accordingly. If a user consistently performs well, the engine increases the complexity of scenarios. If a user struggles, the engine provides simpler scenarios or additional cues.

2. **Cognitive Load Awareness**: By integrating with cognitive load estimators, the engine can detect when a user is experiencing mental fatigue and adjust the training pace accordingly.

3. **Learning Pattern Recognition**: The engine tracks user performance over time, identifying patterns in learning and areas where additional training may be needed.

4. **Dynamic Content Generation**: With LLM integration, the engine can generate novel phishing scenarios that adapt to the user's skill level and training needs.

## Author
NEXARIS - Aymane Loukhai (devartix0aymane)

GitHub: [https://github.com/devartix0aymane](https://github.com/devartix0aymane)

## License
MIT License

Copyright (c) 2023 NEXARIS - Aymane Loukhai

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.