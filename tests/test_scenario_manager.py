import unittest
import os
import json
import tempfile
import sqlite3
from unittest.mock import patch, mock_open
from nase.scenario_manager import ScenarioManager


class TestScenarioManager(unittest.TestCase):
    def setUp(self):
        # Sample scenario data for testing
        self.sample_scenarios = [
            {
                "id": "scenario1",
                "title": "Test Phishing Email",
                "description": "Identify if this is a phishing email",
                "content": "Dear user, please click this link to verify your account...",
                "options": ["Legitimate", "Phishing"],
                "correct_answer": 1,
                "difficulty": 2,
                "explanation": "This is a phishing email because...",
                "theme": "email_phishing"
            },
            {
                "id": "scenario2",
                "title": "Password Security",
                "description": "Evaluate this password",
                "content": "Password: Password123",
                "options": ["Secure", "Insecure"],
                "correct_answer": 1,
                "difficulty": 1,
                "explanation": "This password is insecure because...",
                "theme": "password_security"
            }
        ]
    
    def test_init_json_db(self):
        # Test initialization with JSON database
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Mock the file operations
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.load') as mock_json_load:
                    with patch('json.dump') as mock_json_dump:
                        with patch('os.path.exists') as mock_exists:
                            # First call: file doesn't exist, second call: directory exists
                            mock_exists.side_effect = [False, True]
                            mock_json_load.return_value = self.sample_scenarios
                            
                            # Initialize the manager
                            manager = ScenarioManager(db_path=temp_path, db_type='json')
                            
                            # Verify the file was created with sample scenarios
                            mock_json_dump.assert_called_once()
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_init_sqlite_db(self):
        # Test initialization with SQLite database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Mock the SQLite operations
            with patch('sqlite3.connect') as mock_connect:
                mock_conn = mock_connect.return_value
                mock_cursor = mock_conn.cursor.return_value
                
                with patch('os.path.exists') as mock_exists:
                    # First call: file doesn't exist, second call: directory exists
                    mock_exists.side_effect = [False, True]
                    
                    # Initialize the manager
                    manager = ScenarioManager(db_path=temp_path, db_type='sqlite')
                    
                    # Verify the database was created
                    mock_connect.assert_called_with(temp_path)
                    # Verify execute was called to create table
                    mock_cursor.execute.assert_called()
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_get_all_scenarios_json(self):
        # Test getting all scenarios from JSON
        with patch('builtins.open', mock_open(read_data=json.dumps(self.sample_scenarios))):
            with patch('os.path.exists', return_value=True):
                manager = ScenarioManager(db_path='test.json', db_type='json')
                scenarios = manager.get_all_scenarios()
                
                # Verify we got the correct scenarios
                self.assertEqual(len(scenarios), 2)
                self.assertEqual(scenarios[0]['id'], 'scenario1')
                self.assertEqual(scenarios[1]['id'], 'scenario2')
    
    def test_get_scenario_by_id(self):
        # Test getting a scenario by ID
        with patch('builtins.open', mock_open(read_data=json.dumps(self.sample_scenarios))):
            with patch('os.path.exists', return_value=True):
                manager = ScenarioManager(db_path='test.json', db_type='json')
                scenario = manager.get_scenario_by_id('scenario2')
                
                # Verify we got the correct scenario
                self.assertEqual(scenario['id'], 'scenario2')
                self.assertEqual(scenario['title'], 'Password Security')
    
    def test_get_scenario_by_difficulty(self):
        # Test getting a scenario by difficulty
        with patch('builtins.open', mock_open(read_data=json.dumps(self.sample_scenarios))):
            with patch('os.path.exists', return_value=True):
                with patch('random.choice') as mock_choice:
                    # Mock random.choice to return the first matching scenario
                    mock_choice.side_effect = lambda x: x[0] if x else None
                    
                    manager = ScenarioManager(db_path='test.json', db_type='json')
                    scenario = manager.get_scenario_by_difficulty(1)
                    
                    # Verify we got a scenario with difficulty 1
                    self.assertEqual(scenario['difficulty'], 1)
                    self.assertEqual(scenario['id'], 'scenario2')
    
    def test_add_scenario(self):
        # Test adding a new scenario
        new_scenario = {
            "id": "scenario3",
            "title": "New Scenario",
            "description": "Test description",
            "content": "Test content",
            "options": ["Option 1", "Option 2"],
            "correct_answer": 0,
            "difficulty": 3,
            "explanation": "Test explanation",
            "theme": "test_theme"
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(self.sample_scenarios))):
            with patch('json.dump') as mock_dump:
                with patch('os.path.exists', return_value=True):
                    manager = ScenarioManager(db_path='test.json', db_type='json')
                    manager.add_scenario(new_scenario)
                    
                    # Verify json.dump was called to save the updated scenarios
                    mock_dump.assert_called_once()
                    # Get the scenarios that were saved
                    saved_scenarios = mock_dump.call_args[0][0]
                    # Verify the new scenario was added
                    self.assertEqual(len(saved_scenarios), 3)
                    self.assertEqual(saved_scenarios[2]['id'], 'scenario3')


if __name__ == "__main__":
    unittest.main()