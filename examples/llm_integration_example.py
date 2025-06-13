import os
import sys
import logging
import json
from datetime import datetime

# Add the parent directory to the path so we can import the NASE package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import NASE components
from nase.engine import ScenarioEngine
from nase.scenario_manager import ScenarioManager
from nase.user_manager import UserManager
from nase.difficulty_adjuster import DifficultyAdjuster
from nase.cognitive_load import MockCognitiveLoadEstimator
from nase.llm_integration import MockLLMConnector, OpenAIConnector, LocalLLMConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nase_llm_example.log')
    ]
)

logger = logging.getLogger('NASE.LLMExample')


def generate_and_add_scenarios(scenario_manager, llm_connector, num_scenarios=3):
    """Generate scenarios using LLM and add them to the scenario manager.
    
    Args:
        scenario_manager: The ScenarioManager instance
        llm_connector: The LLM connector to use for generation
        num_scenarios: Number of scenarios to generate
        
    Returns:
        List of generated scenario IDs
    """
    scenario_ids = []
    
    # Define prompts for different difficulty levels
    difficulty_prompts = {
        1: "Generate a simple phishing email scenario for beginners. Make it obvious with clear red flags.",
        2: "Generate a moderately difficult phishing scenario with some subtle indicators.",
        3: "Generate a challenging phishing scenario that requires careful analysis to identify.",
        4: "Generate a difficult social engineering scenario that uses sophisticated techniques.",
        5: "Generate a very advanced and deceptive cybersecurity scenario that would challenge even experts."
    }
    
    # Generate scenarios for each difficulty level
    for difficulty in range(1, min(num_scenarios + 1, 6)):
        prompt = difficulty_prompts[difficulty]
        
        try:
            # Generate scenario using LLM
            logger.info(f"Generating scenario with difficulty {difficulty}...")
            scenario_data = llm_connector.generate(prompt)
            
            # Ensure the scenario has all required fields
            if not all(key in scenario_data for key in ['title', 'content', 'difficulty']):
                logger.warning(f"Generated scenario missing required fields: {scenario_data}")
                # Add missing fields with default values
                scenario_data.setdefault('title', f"Generated Scenario (Difficulty {difficulty})")
                scenario_data.setdefault('description', "A generated cybersecurity scenario")
                scenario_data.setdefault('content', "Please analyze this security situation carefully.")
                scenario_data.setdefault('difficulty', difficulty)
            
            # Ensure difficulty matches the requested level
            scenario_data['difficulty'] = difficulty
            
            # Add scenario to the manager
            scenario_id = scenario_manager.add_scenario(scenario_data)
            scenario_ids.append(scenario_id)
            
            logger.info(f"Added generated scenario with ID: {scenario_id}")
            
        except Exception as e:
            logger.error(f"Error generating scenario: {e}")
    
    return scenario_ids


def main():
    """Example of using the NEXARIS Adaptive Scenario Engine with LLM integration."""
    
    # Initialize components
    logger.info("Initializing NASE components with LLM integration...")
    
    # Use JSON database for this example
    db_type = "json"
    
    # Initialize the scenario manager with sample data
    scenario_manager = ScenarioManager(
        db_type=db_type,
        db_path="llm_example_scenarios.json",
        initialize_with_samples=True  # Start with some basic scenarios
    )
    
    # Initialize the user manager
    user_manager = UserManager(
        db_type=db_type,
        db_path="llm_example_users.json"
    )
    
    # Initialize the difficulty adjuster
    difficulty_adjuster = DifficultyAdjuster()
    
    # Initialize a mock cognitive load estimator
    cognitive_load_estimator = MockCognitiveLoadEstimator()
    
    # Initialize the LLM connector
    # For this example, we'll use the MockLLMConnector
    # In a real application, you might use OpenAIConnector or LocalLLMConnector
    llm_connector = MockLLMConnector()
    
    # Uncomment to use OpenAI (requires API key)
    # api_key = os.environ.get("OPENAI_API_KEY")
    # if api_key:
    #     llm_connector = OpenAIConnector(api_key=api_key)
    # else:
    #     logger.warning("No OpenAI API key found, using MockLLMConnector instead")
    #     llm_connector = MockLLMConnector()
    
    # Uncomment to use a local LLM (requires running local API)
    # llm_connector = LocalLLMConnector(api_url="http://localhost:8000/v1/completions")
    
    # Generate and add some scenarios using the LLM
    generated_scenario_ids = generate_and_add_scenarios(scenario_manager, llm_connector, num_scenarios=3)
    
    # Create the engine
    engine = ScenarioEngine(
        scenario_manager=scenario_manager,
        user_manager=user_manager,
        difficulty_adjuster=difficulty_adjuster,
        cognitive_load_estimator=cognitive_load_estimator
    )
    
    # Create or get a user
    user_id = "llm_example_user"
    if not user_manager.user_exists(user_id):
        user_manager.create_user(user_id, "LLM Example User")
        logger.info(f"Created new user: {user_id}")
    
    # Start a new session
    session_id = engine.start_session(user_id)
    logger.info(f"Started new session: {session_id}")
    
    # Prioritize the generated scenarios
    engine.set_scenario_priority(session_id, generated_scenario_ids)
    
    # Simulate a training session
    for i in range(len(generated_scenario_ids) + 2):  # +2 to include some regular scenarios
        # Get the next scenario
        scenario = engine.get_next_scenario(session_id)
        
        if not scenario:
            logger.warning("No more scenarios available")
            break
        
        # Display the scenario
        print("\n" + "=" * 50)
        print(f"Scenario {i+1}: {scenario['title']}")
        print("=" * 50)
        print(f"Difficulty: {scenario['difficulty']}")
        print(f"\n{scenario['content']}\n")
        
        # Display options if available
        if 'options' in scenario:
            print("Options:")
            for j, option in enumerate(scenario['options']):
                print(f"  {j}. {option}")
        else:
            print("Is this a legitimate message/situation? (y/n)")
        
        # Get user input
        if 'options' in scenario:
            while True:
                try:
                    user_answer = int(input("Enter your answer (number): "))
                    if 0 <= user_answer < len(scenario['options']):
                        break
                    print(f"Please enter a number between 0 and {len(scenario['options'])-1}")
                except ValueError:
                    print("Please enter a valid number")
            
            correct = user_answer == scenario.get('correct_answer', 0)
        else:
            user_input = input("Your answer (y/n): ").lower()
            user_answer = user_input
            correct_answer = scenario.get('correct_answer', True)  # Default to True if not specified
            
            # Convert correct_answer to boolean if it's a string
            if isinstance(correct_answer, str):
                correct_answer = correct_answer.lower() in ['true', 'yes', 'y', '1']
            
            correct = (user_input in ['y', 'yes'] and correct_answer) or \
                     (user_input in ['n', 'no'] and not correct_answer)
        
        # Record response time (in a real app, you'd measure actual time)
        response_time = 5.0 if correct else 10.0
        
        # Process the response
        engine.process_response(
            session_id=session_id,
            scenario_id=scenario['id'],
            correct=correct,
            response_time=response_time,
            user_answer=user_answer
        )
        
        # Display feedback
        print("\nFeedback:")
        print(f"Your answer: {user_answer}")
        
        if 'correct_answer' in scenario:
            print(f"Correct answer: {scenario['correct_answer']}")
        
        if 'explanation' in scenario:
            print(f"Explanation: {scenario['explanation']}")
        
        print(f"You answered {'correctly' if correct else 'incorrectly'}")
        
        # Get cognitive load estimate
        cognitive_load = cognitive_load_estimator.estimate_load(user_id)
        print(f"Estimated cognitive load: {cognitive_load:.2f}")
        
        # Generate a new scenario based on performance
        if i >= 2:  # After a few scenarios
            difficulty = difficulty_adjuster.get_optimal_difficulty(user_id)
            difficulty = max(1, min(5, round(difficulty)))  # Ensure it's between 1-5
            
            print("\nGenerating a new personalized scenario based on your performance...")
            
            # Create a prompt based on performance
            if correct:
                theme = "social engineering" if i % 2 == 0 else "phishing"
                prompt = f"Generate a difficulty level {difficulty} {theme} scenario that's slightly more challenging than the previous one."
            else:
                theme = "phishing" if i % 2 == 0 else "password security"
                prompt = f"Generate a difficulty level {difficulty} {theme} scenario with clear educational value to help the user learn."
            
            try:
                # Generate a new scenario
                new_scenario = llm_connector.generate(prompt)
                new_scenario['difficulty'] = difficulty
                
                # Add to scenario manager
                new_id = scenario_manager.add_scenario(new_scenario)
                
                # Prioritize for next round
                engine.set_scenario_priority(session_id, [new_id])
                
                print(f"New personalized scenario generated and added to your queue!")
            except Exception as e:
                logger.error(f"Error generating new scenario: {e}")
        
        # Continue to next scenario
        input("\nPress Enter to continue...")
    
    # End the session
    session_summary = engine.end_session(session_id)
    
    # Display session summary
    print("\n" + "=" * 50)
    print("Session Summary")
    print("=" * 50)
    print(f"User: {session_summary['user_id']}")
    print(f"Session ID: {session_summary['session_id']}")
    print(f"Start Time: {session_summary['start_time']}")
    print(f"End Time: {session_summary['end_time']}")
    print(f"Duration: {session_summary['duration']:.2f} seconds")
    print(f"Scenarios Completed: {session_summary['scenarios_completed']}")
    print(f"Correct Responses: {session_summary['correct_responses']}")
    print(f"Accuracy: {session_summary['accuracy']:.2f}%")
    print(f"Average Response Time: {session_summary['avg_response_time']:.2f} seconds")
    print(f"Starting Difficulty: {session_summary['starting_difficulty']}")
    print(f"Ending Difficulty: {session_summary['ending_difficulty']}")
    print(f"Difficulty Change: {session_summary['difficulty_change']:+.2f}")
    
    logger.info("LLM integration example completed successfully")


if __name__ == "__main__":
    main()