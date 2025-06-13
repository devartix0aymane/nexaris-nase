import os
import sys
import logging
import json
import time
import random
from datetime import datetime

# Add the parent directory to the path so we can import the NASE package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import NASE components
from nase.engine import ScenarioEngine
from nase.scenario_manager import ScenarioManager
from nase.user_manager import UserManager
from nase.difficulty_adjuster import DifficultyAdjuster
from nase.cognitive_load import NCLEConnector, MockCognitiveLoadEstimator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nase_cognitive_example.log')
    ]
)

logger = logging.getLogger('NASE.CognitiveExample')


class SimulatedNCLEConnector(NCLEConnector):
    """A simulated NCLE connector that generates realistic cognitive load patterns.
    
    This class simulates a connection to a cognitive load estimation service,
    generating values that follow realistic patterns of mental fatigue over time.
    """
    
    def __init__(self, base_url="http://localhost:8080/api/ncle"):
        """Initialize the simulated NCLE connector.
        
        Args:
            base_url: Simulated base URL (not actually used for connections)
        """
        super().__init__(base_url)
        self.session_start_time = time.time()
        self.user_performance = {}  # Track user performance to influence load
        self.consecutive_correct = {}  # Track consecutive correct answers
        self.consecutive_incorrect = {}  # Track consecutive incorrect answers
        
        logger.info("Initialized SimulatedNCLEConnector")
    
    def estimate_load(self, user_id):
        """Estimate cognitive load based on time and user performance.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            A cognitive load estimate between 0.0 and 1.0
        """
        # Initialize user tracking if not exists
        if user_id not in self.user_performance:
            self.user_performance[user_id] = []
            self.consecutive_correct[user_id] = 0
            self.consecutive_incorrect[user_id] = 0
        
        # Calculate time-based fatigue (increases over time)
        session_duration = time.time() - self.session_start_time
        time_factor = min(0.6, session_duration / 3600)  # Max 0.6 after 1 hour
        
        # Calculate performance-based factors
        performance_history = self.user_performance[user_id]
        recent_performance = performance_history[-5:] if performance_history else []
        
        # Recent errors increase cognitive load
        error_factor = sum(1 for p in recent_performance if not p['correct']) * 0.1
        
        # Consecutive correct answers decrease cognitive load (confidence)
        confidence_factor = -0.05 * self.consecutive_correct[user_id]
        
        # Consecutive incorrect answers increase cognitive load (frustration)
        frustration_factor = 0.1 * self.consecutive_incorrect[user_id]
        
        # Add some randomness to simulate natural variations
        random_factor = random.uniform(-0.1, 0.1)
        
        # Calculate final load
        cognitive_load = 0.3 + time_factor + error_factor + confidence_factor + frustration_factor + random_factor
        
        # Ensure the value is between 0.0 and 1.0
        cognitive_load = max(0.0, min(1.0, cognitive_load))
        
        logger.debug(f"Estimated cognitive load for {user_id}: {cognitive_load:.2f}")
        return cognitive_load
    
    def record_performance(self, user_id, correct, response_time):
        """Record user performance to influence future cognitive load estimates.
        
        Args:
            user_id: The ID of the user
            correct: Whether the user answered correctly
            response_time: The time taken to respond
        """
        if user_id not in self.user_performance:
            self.user_performance[user_id] = []
            self.consecutive_correct[user_id] = 0
            self.consecutive_incorrect[user_id] = 0
        
        # Record the performance
        self.user_performance[user_id].append({
            'correct': correct,
            'response_time': response_time,
            'timestamp': time.time()
        })
        
        # Update consecutive counters
        if correct:
            self.consecutive_correct[user_id] += 1
            self.consecutive_incorrect[user_id] = 0
        else:
            self.consecutive_incorrect[user_id] += 1
            self.consecutive_correct[user_id] = 0
        
        logger.debug(f"Recorded performance for {user_id}: correct={correct}, time={response_time:.2f}s")


def main():
    """Example of using the NEXARIS Adaptive Scenario Engine with cognitive load integration."""
    
    # Initialize components
    logger.info("Initializing NASE components with cognitive load integration...")
    
    # Use JSON database for this example
    db_type = "json"
    
    # Initialize the scenario manager with sample data
    scenario_manager = ScenarioManager(
        db_type=db_type,
        db_path="cognitive_example_scenarios.json",
        initialize_with_samples=True
    )
    
    # Initialize the user manager
    user_manager = UserManager(
        db_type=db_type,
        db_path="cognitive_example_users.json"
    )
    
    # Initialize the difficulty adjuster with cognitive load sensitivity
    difficulty_adjuster = DifficultyAdjuster(cognitive_load_weight=0.7)
    
    # Initialize the simulated cognitive load estimator
    cognitive_load_estimator = SimulatedNCLEConnector()
    
    # Create the engine
    engine = ScenarioEngine(
        scenario_manager=scenario_manager,
        user_manager=user_manager,
        difficulty_adjuster=difficulty_adjuster,
        cognitive_load_estimator=cognitive_load_estimator
    )
    
    # Create or get a user
    user_id = "cognitive_example_user"
    if not user_manager.user_exists(user_id):
        user_manager.create_user(user_id, "Cognitive Example User")
        logger.info(f"Created new user: {user_id}")
    
    # Start a new session
    session_id = engine.start_session(user_id)
    logger.info(f"Started new session: {session_id}")
    
    # Simulate a training session with 10 scenarios
    for i in range(10):
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
        
        # Get cognitive load estimate before user response
        pre_response_load = cognitive_load_estimator.estimate_load(user_id)
        print(f"\nCurrent cognitive load: {pre_response_load:.2f}")
        
        # Provide difficulty adjustment based on cognitive load
        if pre_response_load > 0.7:
            print("\n[SYSTEM] Detecting high cognitive load. Taking a short break might help.")
            print("[SYSTEM] This scenario has been simplified to reduce mental fatigue.")
        elif pre_response_load > 0.5:
            print("\n[SYSTEM] Moderate cognitive load detected. Take your time with this scenario.")
        
        # Simulate user response with varying patterns
        # In a real application, you would get actual user input
        start_time = time.time()
        
        # Simulate user thinking time (longer when cognitive load is higher)
        thinking_time = 2 + pre_response_load * 8  # 2-10 seconds based on load
        print(f"\nThinking...")
        time.sleep(min(thinking_time, 3))  # Cap at 3 seconds for the example
        
        # Determine if the answer will be correct based on cognitive load
        # Higher cognitive load increases chance of mistakes
        correct_threshold = 0.8 - (pre_response_load * 0.6)  # 0.8 to 0.2 based on load
        correct = random.random() < correct_threshold
        
        # Simulate user answer
        if 'options' in scenario:
            if correct:
                user_answer = scenario.get('correct_answer', 0)
            else:
                # Pick a wrong answer
                options = list(range(len(scenario['options'])))
                options.remove(scenario.get('correct_answer', 0))
                user_answer = random.choice(options)
            
            print(f"Your answer: {user_answer}")
        else:
            correct_answer = scenario.get('correct_answer', True)
            if isinstance(correct_answer, str):
                correct_answer = correct_answer.lower() in ['true', 'yes', 'y', '1']
            
            user_answer = correct_answer if correct else not correct_answer
            print(f"Your answer: {'Yes' if user_answer else 'No'}")
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Record the performance in the cognitive load estimator
        cognitive_load_estimator.record_performance(user_id, correct, response_time)
        
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
            print(f"Correct answer: {scenario['correct_answer']}")
        
        print(f"You answered {'correctly' if correct else 'incorrectly'}")
        print(f"Response time: {response_time:.2f} seconds")
        
        if 'explanation' in scenario:
            print(f"\nExplanation: {scenario['explanation']}")
        
        # Get updated cognitive load estimate after response
        post_response_load = cognitive_load_estimator.estimate_load(user_id)
        print(f"\nUpdated cognitive load: {post_response_load:.2f}")
        
        # Show cognitive load change
        load_change = post_response_load - pre_response_load
        if load_change > 0.1:
            print("Your cognitive load has increased significantly.")
        elif load_change < -0.1:
            print("Your cognitive load has decreased.")
        
        # Provide adaptive feedback based on cognitive load
        if post_response_load > 0.8:
            print("\n[SYSTEM] High mental fatigue detected. The next scenario will be simplified.")
            print("[SYSTEM] Consider taking a short break before continuing.")
            
            # Simulate a break if cognitive load is very high
            if post_response_load > 0.9:
                print("\n[SYSTEM] Enforcing a short break to reduce cognitive load...")
                for _ in range(3):
                    print(".", end="", flush=True)
                    time.sleep(1)
                print("\n[SYSTEM] Break complete. Continuing with reduced difficulty.")
                
                # Simulate cognitive load reduction after break
                cognitive_load_estimator.consecutive_incorrect[user_id] = 0
        
        # Simulate a delay between scenarios
        input("\nPress Enter to continue to the next scenario...")
    
    # End the session
    session_summary = engine.end_session(session_id)
    
    # Display session summary
    print("\n" + "=" * 50)
    print("Session Summary with Cognitive Load Analysis")
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
    
    # Add cognitive load analysis
    final_cognitive_load = cognitive_load_estimator.estimate_load(user_id)
    print(f"\nCognitive Load Analysis:")
    print(f"Final Cognitive Load: {final_cognitive_load:.2f}")
    
    # Interpret the cognitive load
    if final_cognitive_load < 0.3:
        print("Interpretation: Low cognitive load - User is alert and engaged")
        print("Recommendation: Increase difficulty for more challenge")
    elif final_cognitive_load < 0.6:
        print("Interpretation: Moderate cognitive load - User is in optimal learning zone")
        print("Recommendation: Maintain current difficulty level")
    else:
        print("Interpretation: High cognitive load - User may be experiencing mental fatigue")
        print("Recommendation: Decrease difficulty or take a break")
    
    logger.info("Cognitive load integration example completed successfully")


if __name__ == "__main__":
    main()