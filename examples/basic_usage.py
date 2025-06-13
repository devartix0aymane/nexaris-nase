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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nase_example.log')
    ]
)

logger = logging.getLogger('NASE.Example')


def main():
    """Basic example of using the NEXARIS Adaptive Scenario Engine."""
    
    # Initialize components
    logger.info("Initializing NASE components...")
    
    # Use JSON database for this example
    db_type = "json"
    
    # Initialize the scenario manager with sample data
    scenario_manager = ScenarioManager(
        db_type=db_type,
        db_path="example_scenarios.json",
        initialize_with_samples=True
    )
    
    # Initialize the user manager
    user_manager = UserManager(
        db_type=db_type,
        db_path="example_users.json"
    )
    
    # Initialize the difficulty adjuster
    difficulty_adjuster = DifficultyAdjuster()
    
    # Initialize a mock cognitive load estimator for this example
    cognitive_load_estimator = MockCognitiveLoadEstimator()
    
    # Create the engine
    engine = ScenarioEngine(
        scenario_manager=scenario_manager,
        user_manager=user_manager,
        difficulty_adjuster=difficulty_adjuster,
        cognitive_load_estimator=cognitive_load_estimator
    )
    
    # Create or get a user
    user_id = "example_user"
    if not user_manager.user_exists(user_id):
        user_manager.create_user(user_id, "Example User")
        logger.info(f"Created new user: {user_id}")
    
    # Start a new session
    session_id = engine.start_session(user_id)
    logger.info(f"Started new session: {session_id}")
    
    # Simulate a training session with 5 scenarios
    for i in range(5):
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
        
        # Simulate user response (alternating correct and incorrect)
        # In a real application, you would get actual user input
        if i % 2 == 0:
            # Simulate correct answer
            correct = True
            response_time = 5.0  # 5 seconds
            user_answer = scenario.get('correct_answer', 0)
        else:
            # Simulate incorrect answer
            correct = False
            response_time = 10.0  # 10 seconds (user took longer)
            user_answer = (scenario.get('correct_answer', 0) + 1) % len(scenario.get('options', [1, 2]))
        
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
        print(f"Correct answer: {scenario.get('correct_answer', 'N/A')}")
        print(f"Explanation: {scenario.get('explanation', 'No explanation provided')}")
        print(f"You answered {'correctly' if correct else 'incorrectly'}")
        
        # Get cognitive load estimate (in a real application, this might come from external sensors)
        cognitive_load = cognitive_load_estimator.estimate_load(user_id)
        print(f"Estimated cognitive load: {cognitive_load:.2f}")
        
        # Simulate a short delay between scenarios
        input("\nPress Enter to continue to the next scenario...")
    
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
    
    # Get user performance summary
    user_summary = user_manager.get_user_performance_summary(user_id)
    
    print("\n" + "=" * 50)
    print("User Performance Summary")
    print("=" * 50)
    print(f"User: {user_id}")
    print(f"Total Sessions: {user_summary['total_sessions']}")
    print(f"Total Scenarios: {user_summary['total_scenarios']}")
    print(f"Overall Accuracy: {user_summary['overall_accuracy']:.2f}%")
    print(f"Average Response Time: {user_summary['avg_response_time']:.2f} seconds")
    print(f"Current Difficulty Level: {user_summary['current_difficulty_level']:.2f}")
    
    logger.info("Example completed successfully")


if __name__ == "__main__":
    main()