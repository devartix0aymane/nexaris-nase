import os
import json
import sqlite3
import logging
import datetime
from typing import Dict, List, Optional, Union, Any

from .scenario_manager import ScenarioManager
from .user_manager import UserManager
from .difficulty_adjuster import DifficultyAdjuster

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('NASE.Engine')

class AdaptiveEngine:
    """Core engine for the NEXARIS Adaptive Scenario Engine (NASE).
    
    This class orchestrates the adaptive cybersecurity training process by:
    1. Managing user sessions and performance tracking
    2. Selecting appropriate scenarios based on user skill level
    3. Adjusting difficulty based on user responses
    4. Optionally integrating with cognitive load estimators and LLM generators
    """
    
    def __init__(self, 
                 database_path: str,
                 use_sqlite: bool = False,
                 cognitive_load_estimator = None,
                 llm_connector = None,
                 log_file: str = None):
        """Initialize the adaptive engine.
        
        Args:
            database_path: Path to the scenario database (JSON or SQLite)
            use_sqlite: If True, use SQLite database, otherwise use JSON
            cognitive_load_estimator: Optional connector to cognitive load estimation service
            llm_connector: Optional connector to LLM for scenario generation
            log_file: Path to log file for detailed logging
        """
        self.database_path = database_path
        self.use_sqlite = use_sqlite
        self.cognitive_load_estimator = cognitive_load_estimator
        self.llm_connector = llm_connector
        
        # Initialize components
        self.scenario_manager = ScenarioManager(database_path, use_sqlite)
        self.user_manager = UserManager(database_path, use_sqlite)
        self.difficulty_adjuster = DifficultyAdjuster()
        
        # Session state
        self.current_user_id = None
        self.session_start_time = None
        self.session_scenarios = []
        self.current_difficulty = 1  # Start with easiest difficulty
        
        # Configure file logging if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
        
        logger.info("NEXARIS Adaptive Scenario Engine initialized")
    
    def start_session(self, user_id: str) -> None:
        """Start a new training session for a user.
        
        Args:
            user_id: Unique identifier for the user
        """
        self.current_user_id = user_id
        self.session_start_time = datetime.datetime.now()
        self.session_scenarios = []
        
        # Load user profile or create if not exists
        user_profile = self.user_manager.get_user_profile(user_id)
        if not user_profile:
            logger.info(f"Creating new user profile for {user_id}")
            self.user_manager.create_user_profile(user_id)
            self.current_difficulty = 1  # New users start at lowest difficulty
        else:
            logger.info(f"Loaded existing profile for {user_id}")
            # Set initial difficulty based on user's historical performance
            self.current_difficulty = user_profile.get('current_difficulty', 1)
        
        logger.info(f"Started session for user {user_id} at difficulty level {self.current_difficulty}")
    
    def get_next_scenario(self) -> Dict[str, Any]:
        """Get the next scenario for the current user based on their performance.
        
        Returns:
            A dictionary containing the scenario details
        """
        if not self.current_user_id:
            raise ValueError("No active session. Call start_session() first.")
        
        # Check cognitive load if estimator is available
        cognitive_load = None
        if self.cognitive_load_estimator:
            try:
                cognitive_load = self.cognitive_load_estimator.estimate_load(self.current_user_id)
                logger.info(f"Estimated cognitive load: {cognitive_load}")
                
                # Adjust difficulty based on cognitive load
                if cognitive_load > 0.7:  # High cognitive load
                    logger.info("Reducing difficulty due to high cognitive load")
                    self.current_difficulty = max(1, self.current_difficulty - 1)
            except Exception as e:
                logger.warning(f"Failed to estimate cognitive load: {e}")
        
        # Get scenario matching the current difficulty
        scenario = self.scenario_manager.get_scenario_by_difficulty(
            self.current_difficulty, 
            exclude_ids=[s['id'] for s in self.session_scenarios]
        )
        
        # If no scenario found at current difficulty, try adjacent difficulties
        if not scenario:
            logger.info(f"No unused scenarios at difficulty {self.current_difficulty}, trying adjacent levels")
            for diff_adj in [1, -1, 2, -2]:
                new_diff = max(1, min(5, self.current_difficulty + diff_adj))
                scenario = self.scenario_manager.get_scenario_by_difficulty(
                    new_diff,
                    exclude_ids=[s['id'] for s in self.session_scenarios]
                )
                if scenario:
                    break
        
        # If still no scenario, try generating one with LLM if available
        if not scenario and self.llm_connector:
            try:
                logger.info(f"Generating new scenario at difficulty {self.current_difficulty}")
                scenario = self.generate_scenario(self.current_difficulty)
            except Exception as e:
                logger.warning(f"Failed to generate scenario: {e}")
        
        # If still no scenario, reuse an old one
        if not scenario:
            logger.warning("No unused scenarios available, reusing old scenarios")
            scenario = self.scenario_manager.get_scenario_by_difficulty(self.current_difficulty)
        
        # Add scenario to session history
        if scenario:
            self.session_scenarios.append(scenario)
            logger.info(f"Selected scenario {scenario['id']} at difficulty {scenario['difficulty']}")
        else:
            logger.error("Failed to find or generate any suitable scenario")
            # Return a basic fallback scenario
            scenario = {
                'id': 'fallback_scenario',
                'title': 'Basic Security Awareness',
                'description': 'This is a fallback scenario due to unavailability of suitable scenarios.',
                'content': 'Please identify if this is a security threat: An email asking you to verify your account details.',
                'difficulty': 1,
                'correct_answer': True,
                'explanation': 'This is a common phishing attempt. Always verify the sender and never click suspicious links.'
            }
        
        return scenario
    
    def process_response(self, scenario_id: str, correct: bool, response_time: float = None) -> Dict[str, Any]:
        """Process a user's response to a scenario and adjust difficulty.
        
        Args:
            scenario_id: ID of the scenario that was answered
            correct: Whether the user answered correctly
            response_time: Optional time (in seconds) taken to respond
            
        Returns:
            Dictionary with feedback and next difficulty level
        """
        if not self.current_user_id:
            raise ValueError("No active session. Call start_session() first.")
        
        # Find the scenario in the session history
        scenario = next((s for s in self.session_scenarios if s['id'] == scenario_id), None)
        if not scenario:
            logger.warning(f"Scenario {scenario_id} not found in session history")
            return {
                'status': 'error',
                'message': 'Scenario not found in session history'
            }
        
        # Record the response
        response_data = {
            'user_id': self.current_user_id,
            'scenario_id': scenario_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'correct': correct,
            'difficulty': scenario['difficulty'],
            'response_time': response_time
        }
        
        self.user_manager.record_response(response_data)
        
        # Adjust difficulty based on response
        old_difficulty = self.current_difficulty
        self.current_difficulty = self.difficulty_adjuster.adjust_difficulty(
            current_difficulty=self.current_difficulty,
            correct=correct,
            response_time=response_time,
            user_history=self.user_manager.get_recent_responses(self.current_user_id, limit=5)
        )
        
        # Update user profile with new difficulty
        self.user_manager.update_user_difficulty(self.current_user_id, self.current_difficulty)
        
        logger.info(f"User {self.current_user_id} answered {'correctly' if correct else 'incorrectly'}. "
                   f"Difficulty adjusted from {old_difficulty} to {self.current_difficulty}")
        
        return {
            'status': 'success',
            'correct': correct,
            'previous_difficulty': old_difficulty,
            'new_difficulty': self.current_difficulty,
            'feedback': scenario.get('explanation', ''),
            'message': 'Great job!' if correct else 'Keep learning!'
        }
    
    def end_session(self) -> Dict[str, Any]:
        """End the current session and return session statistics.
        
        Returns:
            Dictionary with session statistics
        """
        if not self.current_user_id:
            logger.warning("Attempted to end session but no active session found")
            return {
                'status': 'error',
                'message': 'No active session to end'
            }
        
        # Calculate session duration
        session_end_time = datetime.datetime.now()
        session_duration = (session_end_time - self.session_start_time).total_seconds()
        
        # Calculate session statistics
        total_scenarios = len(self.session_scenarios)
        responses = self.user_manager.get_session_responses(
            self.current_user_id, 
            start_time=self.session_start_time.isoformat()
        )
        
        correct_responses = sum(1 for r in responses if r.get('correct', False))
        accuracy = correct_responses / total_scenarios if total_scenarios > 0 else 0
        
        # Record session summary
        session_summary = {
            'user_id': self.current_user_id,
            'start_time': self.session_start_time.isoformat(),
            'end_time': session_end_time.isoformat(),
            'duration_seconds': session_duration,
            'total_scenarios': total_scenarios,
            'correct_responses': correct_responses,
            'accuracy': accuracy,
            'final_difficulty': self.current_difficulty
        }
        
        self.user_manager.record_session(session_summary)
        
        logger.info(f"Ended session for user {self.current_user_id}. "
                   f"Accuracy: {accuracy:.2f}, Final difficulty: {self.current_difficulty}")
        
        # Reset session state
        user_id = self.current_user_id
        self.current_user_id = None
        self.session_start_time = None
        self.session_scenarios = []
        
        return {
            'status': 'success',
            'user_id': user_id,
            'session_duration': session_duration,
            'total_scenarios': total_scenarios,
            'correct_responses': correct_responses,
            'accuracy': accuracy,
            'final_difficulty': self.current_difficulty
        }
    
    def generate_scenario(self, difficulty: int, theme: str = None) -> Dict[str, Any]:
        """Generate a new scenario using the LLM connector.
        
        Args:
            difficulty: Difficulty level (1-5)
            theme: Optional theme for the scenario (e.g., 'email phishing', 'social engineering')
            
        Returns:
            Dictionary containing the generated scenario
        """
        if not self.llm_connector:
            raise ValueError("LLM connector not initialized. Cannot generate scenarios.")
        
        # Generate a unique ID for the scenario
        scenario_id = f"gen_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{difficulty}"
        
        # Prepare prompt for the LLM
        prompt = f"Generate a cybersecurity training scenario at difficulty level {difficulty}/5"
        if theme:
            prompt += f" about {theme}"
        prompt += ". Include a title, description, scenario content, correct answer (true/false), and explanation."
        
        try:
            # Generate content with LLM
            generated_content = self.llm_connector.generate(prompt)
            
            # Parse the generated content (this would need to be adapted based on the LLM output format)
            # This is a simplified example
            scenario = {
                'id': scenario_id,
                'title': generated_content.get('title', f"Generated Scenario {difficulty}"),
                'description': generated_content.get('description', 'A generated cybersecurity scenario'),
                'content': generated_content.get('content', 'Default content'),
                'difficulty': difficulty,
                'correct_answer': generated_content.get('correct_answer', True),
                'explanation': generated_content.get('explanation', 'Default explanation'),
                'generated': True,
                'theme': theme,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # Save the generated scenario to the database
            self.scenario_manager.add_scenario(scenario)
            
            logger.info(f"Generated new scenario {scenario_id} with difficulty {difficulty}")
            return scenario
            
        except Exception as e:
            logger.error(f"Failed to generate scenario: {e}")
            raise