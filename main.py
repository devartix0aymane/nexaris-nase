#!/usr/bin/env python3

import os
import sys
import logging
import argparse
from datetime import datetime

# Import NASE components
from nase.engine import ScenarioEngine
from nase.scenario_manager import ScenarioManager
from nase.user_manager import UserManager
from nase.difficulty_adjuster import DifficultyAdjuster
from nase.cognitive_load import MockCognitiveLoadEstimator
from nase.llm_integration import MockLLMConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nase.log')
    ]
)

logger = logging.getLogger('NASE.Main')


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='NEXARIS Adaptive Scenario Engine (NASE)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('--user', '-u', type=str, default='default_user',
                        help='User ID for the session')
    parser.add_argument('--db-type', '-d', choices=['json', 'sqlite'], default='json',
                        help='Database type to use')
    parser.add_argument('--scenarios-db', type=str, default='scenarios.json',
                        help='Path to scenarios database')
    parser.add_argument('--users-db', type=str, default='users.json',
                        help='Path to users database')
    parser.add_argument('--cognitive-load', '-c', action='store_true',
                        help='Enable cognitive load estimation')
    parser.add_argument('--llm', '-m', action='store_true',
                        help='Enable LLM integration')
    parser.add_argument('--scenarios', '-s', type=int, default=5,
                        help='Number of scenarios to present')
    parser.add_argument('--no-samples', action='store_true',
                        help='Do not initialize with sample scenarios')
    
    return parser.parse_args()


def main():
    """Main entry point for the NASE engine."""
    # Parse command-line arguments
    args = parse_args()
    
    # Initialize components
    logger.info("Initializing NASE components...")
    
    # Initialize the scenario manager
    scenario_manager = ScenarioManager(
        db_type=args.db_type,
        db_path=args.scenarios_db,
        initialize_with_samples=not args.no_samples
    )
    
    # Initialize the user manager
    user_manager = UserManager(
        db_type=args.db_type,
        db_path=args.users_db
    )
    
    # Initialize the difficulty adjuster
    difficulty_adjuster = DifficultyAdjuster()
    
    # Initialize cognitive load estimator if enabled
    cognitive_load_estimator = None
    if args.cognitive_load:
        cognitive_load_estimator = MockCognitiveLoadEstimator()
        logger.info("Cognitive load estimation enabled")
    
    # Initialize LLM connector if enabled
    llm_connector = None
    if args.llm:
        llm_connector = MockLLMConnector()
        logger.info("LLM integration enabled")
    
    # Create the engine
    engine = ScenarioEngine(
        scenario_manager=scenario_manager,
        user_manager=user_manager,
        difficulty_adjuster=difficulty_adjuster,
        cognitive_load_estimator=cognitive_load_estimator,
        llm_connector=llm_connector
    )
    
    # Create user if it doesn't exist
    if not user_manager.user_exists(args.user):
        user_manager.create_user(args.user, f"User {args.user}")
        logger.info(f"Created new user: {args.user}")
    
    # Start a new session
    session_id = engine.start_session(args.user)
    logger.info(f"Started new session: {session_id}")
    
    # Present scenarios
    for i in range(args.scenarios):
        # Get the next scenario
        scenario = engine.get_next_scenario(session_id)
        
        if not scenario:
            print("\nNo more scenarios available.")
            break
        
        # Display the scenario
        print("\n" + "=" * 50)
        print(f"Scenario {i+1}/{args.scenarios}: {scenario['title']}")
        print("=" * 50)
        print(f"Difficulty: {scenario['difficulty']}")
        print(f"\n{scenario['content']}\n")
        
        # Display options if available
        if 'options' in scenario:
            print("Options:")
            for j, option in enumerate(scenario['options']):
                print(f"  {j}. {option}")
            
            # Get user input
            while True:
                try:
                    user_answer = int(input("\nEnter your answer (number): "))
                    if 0 <= user_answer < len(scenario['options']):
                        break
                    print(f"Please enter a number between 0 and {len(scenario['options'])-1}")
                except ValueError:
                    print("Please enter a valid number")
            
            correct = user_answer == scenario.get('correct_answer', 0)
        else:
            # Yes/No question
            while True:
                user_input = input("\nIs this legitimate? (y/n): ").lower()
                if user_input in ['y', 'yes', 'n', 'no']:
                    break
                print("Please enter 'y' or 'n'")
            
            user_answer = user_input
            correct_answer = scenario.get('correct_answer', True)
            
            # Convert correct_answer to boolean if it's a string
            if isinstance(correct_answer, str):
                correct_answer = correct_answer.lower() in ['true', 'yes', 'y', '1']
            
            correct = (user_input in ['y', 'yes'] and correct_answer) or \
                     (user_input in ['n', 'no'] and not correct_answer)
        
        # Record response time (in a real app, you'd measure actual time)
        response_time = 5.0  # Default value
        
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
        if 'correct_answer' in scenario:
            if isinstance(scenario['correct_answer'], int):
                print(f"Correct answer: {scenario['correct_answer']} - {scenario['options'][scenario['correct_answer']]}")
            else:
                print(f"Correct answer: {scenario['correct_answer']}")
        
        print(f"You answered {'correctly' if correct else 'incorrectly'}")
        
        if 'explanation' in scenario:
            print(f"\nExplanation: {scenario['explanation']}")
        
        # If cognitive load is enabled, show estimate
        if args.cognitive_load and cognitive_load_estimator:
            cognitive_load = cognitive_load_estimator.estimate_load(args.user)
            print(f"\nEstimated cognitive load: {cognitive_load:.2f}")
            
            if cognitive_load > 0.7:
                print("Your cognitive load is high. Consider taking a short break.")
        
        # Continue to next scenario
        if i < args.scenarios - 1:
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
    user_summary = user_manager.get_user_performance_summary(args.user)
    
    print("\n" + "=" * 50)
    print("User Performance Summary")
    print("=" * 50)
    print(f"User: {args.user}")
    print(f"Total Sessions: {user_summary['total_sessions']}")
    print(f"Total Scenarios: {user_summary['total_scenarios']}")
    print(f"Overall Accuracy: {user_summary['overall_accuracy']:.2f}%")
    print(f"Average Response Time: {user_summary['avg_response_time']:.2f} seconds")
    print(f"Current Difficulty Level: {user_summary['current_difficulty_level']:.2f}")
    
    logger.info("NASE session completed successfully")


if __name__ == "__main__":
    main()