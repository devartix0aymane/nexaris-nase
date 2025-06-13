import unittest
from unittest.mock import MagicMock, patch
from nase.engine import ScenarioEngine
from nase.scenario_manager import ScenarioManager
from nase.user_manager import UserManager
from nase.difficulty_adjuster import DifficultyAdjuster


class TestScenarioEngine(unittest.TestCase):
    def setUp(self):
        # Create mock objects for dependencies
        self.scenario_manager = MagicMock(spec=ScenarioManager)
        self.user_manager = MagicMock(spec=UserManager)
        self.difficulty_adjuster = MagicMock(spec=DifficultyAdjuster)
        self.cognitive_load_estimator = MagicMock()
        self.llm_connector = MagicMock()
        
        # Sample scenario data for testing
        self.sample_scenario = {
            "id": "scenario1",
            "title": "Test Phishing Email",
            "description": "Identify if this is a phishing email",
            "content": "Dear user, please click this link to verify your account...",
            "options": ["Legitimate", "Phishing"],
            "correct_answer": 1,
            "difficulty": 2,
            "explanation": "This is a phishing email because...",
            "theme": "email_phishing"
        }
        
        # Configure mocks
        self.scenario_manager.get_scenario_by_id.return_value = self.sample_scenario
        self.scenario_manager.get_scenario_by_difficulty.return_value = self.sample_scenario
        
        # Create the engine instance
        self.engine = ScenarioEngine(
            scenario_manager=self.scenario_manager,
            user_manager=self.user_manager,
            difficulty_adjuster=self.difficulty_adjuster,
            cognitive_load_estimator=self.cognitive_load_estimator,
            llm_connector=self.llm_connector
        )
    
    def test_start_session(self):
        # Test starting a session
        self.engine.start_session("user123")
        
        # Verify user_manager was called to create session
        self.user_manager.create_session.assert_called_once_with("user123")
        
        # Verify session is active
        self.assertTrue(self.engine.session_active)
        self.assertEqual(self.engine.current_user_id, "user123")
    
    def test_get_next_scenario(self):
        # Setup session
        self.engine.start_session("user123")
        
        # Mock difficulty adjuster to return a specific difficulty
        self.difficulty_adjuster.get_optimal_difficulty.return_value = 2
        
        # Get next scenario
        scenario = self.engine.get_next_scenario()
        
        # Verify the correct methods were called
        self.difficulty_adjuster.get_optimal_difficulty.assert_called_once()
        self.scenario_manager.get_scenario_by_difficulty.assert_called_once_with(2)
        
        # Verify the returned scenario
        self.assertEqual(scenario, self.sample_scenario)
    
    def test_process_response_correct(self):
        # Setup session
        self.engine.start_session("user123")
        self.engine.current_scenario = self.sample_scenario
        
        # Process a correct response
        result = self.engine.process_response("scenario1", 1, 5.0)  # correct answer, 5 seconds
        
        # Verify user_manager was called to record response
        self.user_manager.record_scenario_response.assert_called_once()
        
        # Verify difficulty_adjuster was called to adjust difficulty
        self.difficulty_adjuster.adjust_difficulty.assert_called_once()
        
        # Verify result contains correct information
        self.assertTrue(result["correct"])
        self.assertEqual(result["explanation"], self.sample_scenario["explanation"])
    
    def test_process_response_incorrect(self):
        # Setup session
        self.engine.start_session("user123")
        self.engine.current_scenario = self.sample_scenario
        
        # Process an incorrect response
        result = self.engine.process_response("scenario1", 0, 5.0)  # incorrect answer, 5 seconds
        
        # Verify result contains correct information
        self.assertFalse(result["correct"])
    
    def test_end_session(self):
        # Setup session
        self.engine.start_session("user123")
        
        # End the session
        summary = self.engine.end_session()
        
        # Verify user_manager was called to end session
        self.user_manager.end_session.assert_called_once()
        
        # Verify session is no longer active
        self.assertFalse(self.engine.session_active)
        self.assertIsNone(self.engine.current_user_id)
        self.assertIsNone(self.engine.current_scenario)


if __name__ == "__main__":
    unittest.main()