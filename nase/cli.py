#!/usr/bin/env python3

import os
import sys
import argparse
import logging
import json
import time
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
        logging.FileHandler('nase_cli.log')
    ]
)

logger = logging.getLogger('NASE.CLI')


class NaseCLI:
    """Command-line interface for the NEXARIS Adaptive Scenario Engine."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.engine = None
        self.session_id = None
        self.user_id = None
        self.config = {
            'db_type': 'json',
            'scenarios_db_path': 'scenarios.json',
            'users_db_path': 'users.json',
            'use_cognitive_load': False,
            'use_llm': False,
            'initialize_with_samples': True
        }
    
    def parse_args(self):
        """Parse command-line arguments."""
        parser = argparse.ArgumentParser(
            description='NEXARIS Adaptive Scenario Engine (NASE) CLI',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        
        # General options
        parser.add_argument('--user', '-u', type=str, default='default_user',
                            help='User ID for the session')
        parser.add_argument('--db-type', '-d', choices=['json', 'sqlite'], default='json',
                            help='Database type to use')
        parser.add_argument('--scenarios-db', type=str, default='scenarios.json',
                            help='Path to scenarios database')
        parser.add_argument('--users-db', type=str, default='users.json',
                            help='Path to users database')
        parser.add_argument('--log-level', '-l', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                            default='INFO', help='Logging level')
        
        # Feature flags
        parser.add_argument('--cognitive-load', '-c', action='store_true',
                            help='Enable cognitive load estimation')
        parser.add_argument('--llm', '-m', action='store_true',
                            help='Enable LLM integration for scenario generation')
        parser.add_argument('--no-samples', action='store_true',
                            help='Do not initialize with sample scenarios')
        
        # Commands
        subparsers = parser.add_subparsers(dest='command', help='Command to run')
        
        # Training session command
        train_parser = subparsers.add_parser('train', help='Start a training session')
        train_parser.add_argument('--scenarios', '-s', type=int, default=5,
                                help='Number of scenarios to present')
        
        # List scenarios command
        list_parser = subparsers.add_parser('list-scenarios', help='List available scenarios')
        list_parser.add_argument('--difficulty', '-d', type=int, choices=range(1, 6),
                                help='Filter by difficulty level (1-5)')
        list_parser.add_argument('--theme', '-t', type=str,
                                help='Filter by theme')
        
        # User stats command
        stats_parser = subparsers.add_parser('user-stats', help='Show user statistics')
        stats_parser.add_argument('--user', '-u', type=str,
                                help='User ID to show stats for (defaults to current user)')
        
        # Add scenario command
        add_parser = subparsers.add_parser('add-scenario', help='Add a new scenario')
        add_parser.add_argument('--file', '-f', type=str, required=True,
                                help='JSON file containing the scenario data')
        
        # Generate scenario command
        gen_parser = subparsers.add_parser('generate-scenario', 
                                        help='Generate a new scenario using LLM')
        gen_parser.add_argument('--difficulty', '-d', type=int, choices=range(1, 6), default=3,
                                help='Difficulty level (1-5)')
        gen_parser.add_argument('--theme', '-t', type=str, default='phishing',
                                help='Theme for the scenario')
        gen_parser.add_argument('--save', '-s', action='store_true',
                                help='Save the generated scenario to the database')
        
        args = parser.parse_args()
        
        # If no command is provided, show help and exit
        if not args.command:
            parser.print_help()
            sys.exit(1)
        
        return args
    
    def setup(self, args):
        """Set up the engine based on command-line arguments."""
        # Configure logging level
        logging.getLogger().setLevel(getattr(logging, args.log_level))
        
        # Set configuration from arguments
        self.config['db_type'] = args.db_type
        self.config['scenarios_db_path'] = args.scenarios_db
        self.config['users_db_path'] = args.users_db
        self.config['use_cognitive_load'] = args.cognitive_load
        self.config['use_llm'] = args.llm
        self.config['initialize_with_samples'] = not args.no_samples
        
        self.user_id = args.user
        
        # Initialize components
        logger.info("Initializing NASE components...")
        
        # Initialize the scenario manager
        scenario_manager = ScenarioManager(
            db_type=self.config['db_type'],
            db_path=self.config['scenarios_db_path'],
            initialize_with_samples=self.config['initialize_with_samples']
        )
        
        # Initialize the user manager
        user_manager = UserManager(
            db_type=self.config['db_type'],
            db_path=self.config['users_db_path']
        )
        
        # Initialize the difficulty adjuster
        difficulty_adjuster = DifficultyAdjuster()
        
        # Initialize cognitive load estimator if enabled
        cognitive_load_estimator = None
        if self.config['use_cognitive_load']:
            cognitive_load_estimator = MockCognitiveLoadEstimator()
            logger.info("Cognitive load estimation enabled")
        
        # Initialize LLM connector if enabled
        llm_connector = None
        if self.config['use_llm']:
            llm_connector = MockLLMConnector()
            logger.info("LLM integration enabled")
        
        # Create the engine
        self.engine = ScenarioEngine(
            scenario_manager=scenario_manager,
            user_manager=user_manager,
            difficulty_adjuster=difficulty_adjuster,
            cognitive_load_estimator=cognitive_load_estimator,
            llm_connector=llm_connector
        )
        
        # Create user if it doesn't exist
        if not user_manager.user_exists(self.user_id):
            user_manager.create_user(self.user_id, f"User {self.user_id}")
            logger.info(f"Created new user: {self.user_id}")
    
    def run_training_session(self, num_scenarios=5):
        """Run a training session with the specified number of scenarios."""
        if not self.engine:
            logger.error("Engine not initialized")
            return
        
        # Start a new session
        self.session_id = self.engine.start_session(self.user_id)
        logger.info(f"Started new session: {self.session_id}")
        
        # Present scenarios
        for i in range(num_scenarios):
            # Get the next scenario
            scenario = self.engine.get_next_scenario(self.session_id)
            
            if not scenario:
                print("\nNo more scenarios available.")
                break
            
            # Display the scenario
            print("\n" + "=" * 50)
            print(f"Scenario {i+1}/{num_scenarios}: {scenario['title']}")
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
            self.engine.process_response(
                session_id=self.session_id,
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
            if self.config['use_cognitive_load'] and self.engine.cognitive_load_estimator:
                cognitive_load = self.engine.cognitive_load_estimator.estimate_load(self.user_id)
                print(f"\nEstimated cognitive load: {cognitive_load:.2f}")
                
                if cognitive_load > 0.7:
                    print("Your cognitive load is high. Consider taking a short break.")
            
            # Continue to next scenario
            if i < num_scenarios - 1:
                input("\nPress Enter to continue to the next scenario...")
        
        # End the session
        session_summary = self.engine.end_session(self.session_id)
        
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
        
        logger.info("Training session completed successfully")
    
    def list_scenarios(self, difficulty=None, theme=None):
        """List available scenarios, optionally filtered by difficulty or theme."""
        if not self.engine:
            logger.error("Engine not initialized")
            return
        
        # Get all scenarios
        scenarios = self.engine.scenario_manager.get_all_scenarios()
        
        # Apply filters
        if difficulty is not None:
            scenarios = [s for s in scenarios if s.get('difficulty') == difficulty]
        
        if theme is not None:
            scenarios = [s for s in scenarios if theme.lower() in s.get('theme', '').lower()]
        
        # Display scenarios
        if not scenarios:
            print("No scenarios found matching the criteria.")
            return
        
        print(f"\nFound {len(scenarios)} scenarios:")
        print("=" * 50)
        
        for i, scenario in enumerate(scenarios):
            print(f"{i+1}. {scenario['title']}")
            print(f"   ID: {scenario['id']}")
            print(f"   Difficulty: {scenario.get('difficulty', 'N/A')}")
            print(f"   Theme: {scenario.get('theme', 'N/A')}")
            print(f"   Description: {scenario.get('description', 'N/A')}")
            print()
    
    def show_user_stats(self, user_id=None):
        """Show statistics for the specified user."""
        if not self.engine:
            logger.error("Engine not initialized")
            return
        
        # Use current user if not specified
        if user_id is None:
            user_id = self.user_id
        
        # Check if user exists
        if not self.engine.user_manager.user_exists(user_id):
            print(f"User '{user_id}' does not exist.")
            return
        
        # Get user performance summary
        user_summary = self.engine.user_manager.get_user_performance_summary(user_id)
        
        # Display user statistics
        print("\n" + "=" * 50)
        print(f"User Performance Summary for {user_id}")
        print("=" * 50)
        print(f"Total Sessions: {user_summary['total_sessions']}")
        print(f"Total Scenarios: {user_summary['total_scenarios']}")
        print(f"Overall Accuracy: {user_summary['overall_accuracy']:.2f}%")
        print(f"Average Response Time: {user_summary['avg_response_time']:.2f} seconds")
        print(f"Current Difficulty Level: {user_summary['current_difficulty_level']:.2f}")
        
        # Get recent responses
        recent_responses = self.engine.user_manager.get_recent_responses(user_id, limit=5)
        
        if recent_responses:
            print("\nRecent Responses:")
            for i, response in enumerate(recent_responses):
                print(f"{i+1}. Scenario: {response.get('scenario_id', 'N/A')}")
                print(f"   Correct: {response.get('correct', 'N/A')}")
                print(f"   Response Time: {response.get('response_time', 'N/A'):.2f} seconds")
                print(f"   Timestamp: {response.get('timestamp', 'N/A')}")
                print()
    
    def add_scenario(self, file_path):
        """Add a new scenario from a JSON file."""
        if not self.engine:
            logger.error("Engine not initialized")
            return
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"File '{file_path}' does not exist.")
            return
        
        try:
            # Load scenario data from file
            with open(file_path, 'r') as f:
                scenario_data = json.load(f)
            
            # Check if it's a single scenario or a list
            if isinstance(scenario_data, list):
                # Add multiple scenarios
                added_ids = []
                for scenario in scenario_data:
                    scenario_id = self.engine.scenario_manager.add_scenario(scenario)
                    added_ids.append(scenario_id)
                
                print(f"Added {len(added_ids)} scenarios with IDs: {', '.join(added_ids)}")
            else:
                # Add single scenario
                scenario_id = self.engine.scenario_manager.add_scenario(scenario_data)
                print(f"Added scenario with ID: {scenario_id}")
            
        except Exception as e:
            print(f"Error adding scenario: {e}")
    
    def generate_scenario(self, difficulty=3, theme='phishing', save=False):
        """Generate a new scenario using LLM."""
        if not self.engine:
            logger.error("Engine not initialized")
            return
        
        # Check if LLM is enabled
        if not self.config['use_llm'] or not self.engine.llm_connector:
            print("LLM integration is not enabled. Use --llm flag to enable it.")
            return
        
        try:
            # Create prompt
            prompt = f"Generate a difficulty level {difficulty} {theme} scenario for cybersecurity training."
            
            print(f"Generating scenario with difficulty {difficulty} and theme '{theme}'...")
            
            # Generate scenario
            scenario_data = self.engine.llm_connector.generate(prompt)
            
            # Ensure difficulty matches requested level
            scenario_data['difficulty'] = difficulty
            
            # Display generated scenario
            print("\n" + "=" * 50)
            print("Generated Scenario")
            print("=" * 50)
            print(f"Title: {scenario_data.get('title', 'Untitled')}")
            print(f"Difficulty: {scenario_data.get('difficulty', 'N/A')}")
            print(f"Description: {scenario_data.get('description', 'N/A')}")
            print(f"\nContent:\n{scenario_data.get('content', 'No content')}")
            
            if 'options' in scenario_data:
                print("\nOptions:")
                for i, option in enumerate(scenario_data['options']):
                    print(f"  {i}. {option}")
            
            if 'correct_answer' in scenario_data:
                print(f"\nCorrect Answer: {scenario_data['correct_answer']}")
            
            if 'explanation' in scenario_data:
                print(f"\nExplanation: {scenario_data['explanation']}")
            
            # Save scenario if requested
            if save:
                scenario_id = self.engine.scenario_manager.add_scenario(scenario_data)
                print(f"\nScenario saved with ID: {scenario_id}")
            
        except Exception as e:
            print(f"Error generating scenario: {e}")
    
    def run(self):
        """Run the CLI."""
        # Parse command-line arguments
        args = self.parse_args()
        
        # Set up the engine
        self.setup(args)
        
        # Execute the requested command
        if args.command == 'train':
            self.run_training_session(args.scenarios)
        elif args.command == 'list-scenarios':
            self.list_scenarios(args.difficulty, args.theme)
        elif args.command == 'user-stats':
            self.show_user_stats(args.user)
        elif args.command == 'add-scenario':
            self.add_scenario(args.file)
        elif args.command == 'generate-scenario':
            self.generate_scenario(args.difficulty, args.theme, args.save)


def main():
    """Main entry point for the CLI."""
    cli = NaseCLI()
    cli.run()


if __name__ == "__main__":
    main()