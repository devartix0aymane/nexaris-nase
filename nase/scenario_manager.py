import os
import json
import sqlite3
import random
import logging
from typing import Dict, List, Optional, Union, Any

# Configure logging
logger = logging.getLogger('NASE.ScenarioManager')

class ScenarioManager:
    """Manages the loading, storing, and retrieval of cybersecurity training scenarios.
    
    This class handles all interactions with the scenario database, whether it's
    stored in JSON or SQLite format. It provides methods to retrieve scenarios
    based on various criteria such as difficulty level.
    """
    
    def __init__(self, database_path: str, use_sqlite: bool = False):
        """Initialize the scenario manager.
        
        Args:
            database_path: Path to the scenario database (JSON or SQLite)
            use_sqlite: If True, use SQLite database, otherwise use JSON
        """
        self.database_path = database_path
        self.use_sqlite = use_sqlite
        
        # Ensure the database exists
        self._initialize_database()
        
        logger.info(f"ScenarioManager initialized with {'SQLite' if use_sqlite else 'JSON'} database at {database_path}")
    
    def _initialize_database(self) -> None:
        """Initialize the database if it doesn't exist."""
        if self.use_sqlite:
            self._initialize_sqlite()
        else:
            self._initialize_json()
    
    def _initialize_sqlite(self) -> None:
        """Initialize the SQLite database if it doesn't exist."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        
        # Connect to the database
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Create scenarios table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scenarios (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            content TEXT NOT NULL,
            difficulty INTEGER NOT NULL,
            correct_answer INTEGER NOT NULL,
            explanation TEXT,
            theme TEXT,
            generated INTEGER DEFAULT 0,
            timestamp TEXT
        )
        ''')
        
        # Check if we need to add sample data
        cursor.execute("SELECT COUNT(*) FROM scenarios")
        count = cursor.fetchone()[0]
        
        if count == 0:
            logger.info("Adding sample scenarios to SQLite database")
            sample_scenarios = self._get_sample_scenarios()
            
            for scenario in sample_scenarios:
                cursor.execute('''
                INSERT INTO scenarios (id, title, description, content, difficulty, correct_answer, explanation, theme, generated, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    scenario['id'],
                    scenario['title'],
                    scenario.get('description', ''),
                    scenario['content'],
                    scenario['difficulty'],
                    1 if scenario['correct_answer'] else 0,
                    scenario.get('explanation', ''),
                    scenario.get('theme', ''),
                    1 if scenario.get('generated', False) else 0,
                    scenario.get('timestamp', '')
                ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"SQLite database initialized at {self.database_path}")
    
    def _initialize_json(self) -> None:
        """Initialize the JSON database if it doesn't exist."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        
        # Check if file exists
        if not os.path.exists(self.database_path):
            logger.info(f"Creating new JSON database at {self.database_path}")
            
            # Create initial database with sample scenarios
            data = {
                "scenarios": self._get_sample_scenarios()
            }
            
            # Write to file
            with open(self.database_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        logger.info(f"JSON database initialized at {self.database_path}")
    
    def _get_sample_scenarios(self) -> List[Dict[str, Any]]:
        """Return a list of sample scenarios for initial database population."""
        return [
            {
                "id": "phish_001",
                "title": "Suspicious Email Alert",
                "description": "A basic email phishing attempt",
                "content": "You receive an email with the subject 'Urgent: Your account has been compromised'. The email asks you to click a link and enter your credentials to secure your account. The sender's email is 'security-alert@g00gle.com'. What should you do?",
                "options": [
                    "Click the link and enter your credentials to secure your account",
                    "Ignore the email and delete it",
                    "Forward the email to your IT department and report it as suspicious",
                    "Reply to the sender asking for more information"
                ],
                "correct_answer": 2,  # Index of the correct option
                "difficulty": 1,
                "explanation": "This is a phishing attempt. The sender's email domain 'g00gle.com' is suspicious (notice the zeros instead of 'o's). Legitimate security alerts typically don't ask you to click links and enter credentials. Always report suspicious emails to your IT department.",
                "theme": "email phishing"
            },
            {
                "id": "phish_002",
                "title": "Password Reset Request",
                "description": "A password reset phishing attempt",
                "content": "You receive an email claiming to be from Microsoft Office 365 stating that your password is about to expire. It provides a link to reset your password. The email looks professional and has Microsoft logos. What is the best action?",
                "options": [
                    "Click the link and reset your password",
                    "Check the sender's email address for legitimacy",
                    "Ignore the email as it's definitely a scam",
                    "Open your browser and navigate directly to Office 365 to check your password status"
                ],
                "correct_answer": 3,  # Index of the correct option
                "difficulty": 2,
                "explanation": "Even if an email looks legitimate, you should never click on password reset links directly from emails. Instead, open your browser and navigate directly to the service's official website. This prevents you from being directed to a phishing site.",
                "theme": "password security"
            },
            {
                "id": "social_001",
                "title": "Unexpected Call from IT",
                "description": "A social engineering attempt via phone",
                "content": "You receive a call from someone claiming to be from your company's IT department. They say they've detected suspicious activity on your account and need your password to fix the issue. What should you do?",
                "options": [
                    "Provide your password since they're from IT",
                    "Ask for their employee ID and call back the official IT helpdesk",
                    "Tell them you'll change your password yourself",
                    "Hang up immediately without saying anything"
                ],
                "correct_answer": 1,  # Index of the correct option
                "difficulty": 2,
                "explanation": "This is a social engineering attempt. IT staff should never ask for your password. The best approach is to verify the caller's identity by asking for their employee ID and then calling back through the official IT helpdesk number that you look up independently.",
                "theme": "social engineering"
            },
            {
                "id": "malware_001",
                "title": "Suspicious Attachment",
                "description": "Identifying a malicious email attachment",
                "content": "You receive an email with the subject 'Invoice for your recent purchase'. The email contains an attachment named 'Invoice_details.exe'. You don't recall making any recent purchases. What should you do?",
                "options": [
                    "Open the attachment to see what purchase it refers to",
                    "Reply to the sender asking for clarification",
                    "Delete the email without opening the attachment",
                    "Save the attachment and scan it with antivirus software"
                ],
                "correct_answer": 2,  # Index of the correct option
                "difficulty": 1,
                "explanation": "This is likely a malware distribution attempt. Executable files (.exe) sent via email are almost always malicious. If you don't recognize the sender or aren't expecting an invoice, you should delete the email without opening any attachments.",
                "theme": "malware"
            },
            {
                "id": "phish_003",
                "title": "CEO Urgent Request",
                "description": "A sophisticated whaling/spear-phishing attempt",
                "content": "You receive an email that appears to be from your company's CEO. The email says: 'I'm in an emergency meeting and need you to purchase $500 in gift cards for a client. Please keep this confidential and send the gift card codes to me ASAP. I'll reimburse you later.' The email address looks legitimate. What should you do?",
                "options": [
                    "Purchase the gift cards and send the codes as requested",
                    "Reply to the email asking for more details",
                    "Contact the CEO through another channel to verify the request",
                    "Forward the email to your supervisor for guidance"
                ],
                "correct_answer": 2,  # Index of the correct option
                "difficulty": 3,
                "explanation": "This is a common CEO fraud or 'whaling' attack. Even if the email appears legitimate, unusual requests involving money or gift cards should always be verified through a different communication channel. Call or text the CEO directly using their known contact information.",
                "theme": "whaling"
            },
            {
                "id": "security_001",
                "title": "Public WiFi Usage",
                "description": "Identifying secure practices for public WiFi",
                "content": "You're working at a coffee shop and need to access your company's financial reports. The coffee shop offers free WiFi. What is the most secure way to access these sensitive documents?",
                "options": [
                    "Connect to the free WiFi and access the documents directly",
                    "Ask the barista for the WiFi password first, then connect",
                    "Use your phone's mobile hotspot instead of the public WiFi",
                    "Wait until you return to the office to access the documents"
                ],
                "correct_answer": 2,  # Index of the correct option
                "difficulty": 2,
                "explanation": "Public WiFi networks, even password-protected ones, are not secure for accessing sensitive information. Using your phone's mobile hotspot creates a private connection that is much more secure than public WiFi.",
                "theme": "network security"
            },
            {
                "id": "phish_004",
                "title": "Advanced Spear Phishing",
                "description": "A highly targeted phishing attempt with personal information",
                "content": "You receive an email referencing a recent conference you attended and includes specific details about your presentation. It claims to have additional resources related to your topic and includes a link to download them. The sender's name is someone you don't recognize. What should you do?",
                "options": [
                    "Click the link since the email shows knowledge of your activities",
                    "Reply thanking them for the resources",
                    "Check the email header and link destination before deciding",
                    "Delete the email since you don't recognize the sender"
                ],
                "correct_answer": 2,  # Index of the correct option
                "difficulty": 4,
                "explanation": "This is a sophisticated spear phishing attempt. The attacker has researched you and included legitimate details to gain trust. Always verify the email header and hover over links to check their true destination before clicking. Consider contacting conference organizers to verify if they shared your information with this person.",
                "theme": "spear phishing"
            },
            {
                "id": "ransomware_001",
                "title": "Ransomware Prevention",
                "description": "Identifying best practices to prevent ransomware",
                "content": "Your colleague mentions that they received a strange email with an Office document that asked them to 'Enable Macros' to view the content. They're not sure what to do. What advice should you give them?",
                "options": [
                    "Enable macros if the document looks important",
                    "Save the document and scan it with antivirus before opening",
                    "Never enable macros on documents from email and delete this one",
                    "Forward the email to IT before taking any action"
                ],
                "correct_answer": 3,  # Index of the correct option
                "difficulty": 3,
                "explanation": "This is a common ransomware delivery method. Malicious macros in Office documents are a primary vector for ransomware infections. The best practice is to forward suspicious emails to IT for analysis without opening attachments or enabling macros.",
                "theme": "ransomware"
            },
            {
                "id": "security_002",
                "title": "Multi-Factor Authentication",
                "description": "Understanding the importance of MFA",
                "content": "You receive a notification on your phone asking you to approve a login attempt for your work account, but you haven't tried to log in. What should you do?",
                "options": [
                    "Approve the request since it's using the official authentication app",
                    "Ignore the notification and it will eventually disappear",
                    "Deny the request and immediately change your password",
                    "Contact IT to report the incident"
                ],
                "correct_answer": 2,  # Index of the correct option
                "difficulty": 3,
                "explanation": "This scenario indicates that someone has your password and is trying to log in to your account. Multi-factor authentication is working correctly by asking for your approval. You should deny the request and immediately change your password to prevent further attempts. Additionally, you should report the incident to IT.",
                "theme": "authentication"
            },
            {
                "id": "security_003",
                "title": "Data Exfiltration Attempt",
                "description": "Recognizing and responding to data theft attempts",
                "content": "You notice a coworker copying large amounts of company data to a personal USB drive after hours when they think no one is watching. What is the most appropriate action?",
                "options": [
                    "Confront them directly about what they're doing",
                    "Do nothing, it's not your responsibility",
                    "Casually ask them what project they're working on so late",
                    "Report the suspicious behavior to security or management without confrontation"
                ],
                "correct_answer": 3,  # Index of the correct option
                "difficulty": 5,
                "explanation": "This appears to be a potential data exfiltration attempt. Confronting the person could be dangerous or give them time to cover their tracks. The appropriate response is to report the suspicious behavior to security personnel or management who are trained to handle such situations.",
                "theme": "insider threat"
            }
        ]
    
    def get_all_scenarios(self) -> List[Dict[str, Any]]:
        """Retrieve all scenarios from the database.
        
        Returns:
            List of scenario dictionaries
        """
        if self.use_sqlite:
            return self._get_all_scenarios_sqlite()
        else:
            return self._get_all_scenarios_json()
    
    def _get_all_scenarios_sqlite(self) -> List[Dict[str, Any]]:
        """Retrieve all scenarios from the SQLite database."""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM scenarios")
        rows = cursor.fetchall()
        
        scenarios = []
        for row in rows:
            scenario = dict(row)
            # Convert SQLite INTEGER to Python bool for correct_answer
            scenario['correct_answer'] = bool(scenario['correct_answer'])
            scenario['generated'] = bool(scenario['generated'])
            scenarios.append(scenario)
        
        conn.close()
        return scenarios
    
    def _get_all_scenarios_json(self) -> List[Dict[str, Any]]:
        """Retrieve all scenarios from the JSON database."""
        with open(self.database_path, 'r') as f:
            data = json.load(f)
        
        return data.get("scenarios", [])
    
    def get_scenario_by_id(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific scenario by its ID.
        
        Args:
            scenario_id: The unique identifier of the scenario
            
        Returns:
            The scenario dictionary or None if not found
        """
        if self.use_sqlite:
            return self._get_scenario_by_id_sqlite(scenario_id)
        else:
            return self._get_scenario_by_id_json(scenario_id)
    
    def _get_scenario_by_id_sqlite(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific scenario by its ID from the SQLite database."""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,))
        row = cursor.fetchone()
        
        if row:
            scenario = dict(row)
            scenario['correct_answer'] = bool(scenario['correct_answer'])
            scenario['generated'] = bool(scenario['generated'])
            conn.close()
            return scenario
        
        conn.close()
        return None
    
    def _get_scenario_by_id_json(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific scenario by its ID from the JSON database."""
        with open(self.database_path, 'r') as f:
            data = json.load(f)
        
        for scenario in data.get("scenarios", []):
            if scenario.get("id") == scenario_id:
                return scenario
        
        return None
    
    def get_scenario_by_difficulty(self, difficulty: int, exclude_ids: List[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a random scenario matching the specified difficulty level.
        
        Args:
            difficulty: The difficulty level to match (1-5)
            exclude_ids: Optional list of scenario IDs to exclude
            
        Returns:
            A random scenario dictionary matching the criteria or None if not found
        """
        if exclude_ids is None:
            exclude_ids = []
        
        if self.use_sqlite:
            return self._get_scenario_by_difficulty_sqlite(difficulty, exclude_ids)
        else:
            return self._get_scenario_by_difficulty_json(difficulty, exclude_ids)
    
    def _get_scenario_by_difficulty_sqlite(self, difficulty: int, exclude_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Retrieve a random scenario by difficulty from the SQLite database."""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Construct the query with placeholders for the exclude_ids
        query = "SELECT * FROM scenarios WHERE difficulty = ?"
        params = [difficulty]
        
        if exclude_ids:
            placeholders = ','.join(['?'] * len(exclude_ids))
            query += f" AND id NOT IN ({placeholders})"
            params.extend(exclude_ids)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if rows:
            # Select a random scenario from the results
            row = random.choice(rows)
            scenario = dict(row)
            scenario['correct_answer'] = bool(scenario['correct_answer'])
            scenario['generated'] = bool(scenario['generated'])
            conn.close()
            return scenario
        
        conn.close()
        return None
    
    def _get_scenario_by_difficulty_json(self, difficulty: int, exclude_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Retrieve a random scenario by difficulty from the JSON database."""
        with open(self.database_path, 'r') as f:
            data = json.load(f)
        
        # Filter scenarios by difficulty and exclude_ids
        matching_scenarios = [
            s for s in data.get("scenarios", [])
            if s.get("difficulty") == difficulty and s.get("id") not in exclude_ids
        ]
        
        if matching_scenarios:
            return random.choice(matching_scenarios)
        
        return None
    
    def add_scenario(self, scenario: Dict[str, Any]) -> bool:
        """Add a new scenario to the database.
        
        Args:
            scenario: The scenario dictionary to add
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_sqlite:
            return self._add_scenario_sqlite(scenario)
        else:
            return self._add_scenario_json(scenario)
    
    def _add_scenario_sqlite(self, scenario: Dict[str, Any]) -> bool:
        """Add a new scenario to the SQLite database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO scenarios (id, title, description, content, difficulty, correct_answer, explanation, theme, generated, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scenario['id'],
                scenario['title'],
                scenario.get('description', ''),
                scenario['content'],
                scenario['difficulty'],
                1 if scenario['correct_answer'] else 0,
                scenario.get('explanation', ''),
                scenario.get('theme', ''),
                1 if scenario.get('generated', False) else 0,
                scenario.get('timestamp', '')
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added new scenario {scenario['id']} to SQLite database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add scenario to SQLite database: {e}")
            return False
    
    def _add_scenario_json(self, scenario: Dict[str, Any]) -> bool:
        """Add a new scenario to the JSON database."""
        try:
            with open(self.database_path, 'r') as f:
                data = json.load(f)
            
            # Check if scenario with this ID already exists
            for i, existing_scenario in enumerate(data.get("scenarios", [])):
                if existing_scenario.get("id") == scenario["id"]:
                    # Replace the existing scenario
                    data["scenarios"][i] = scenario
                    break
            else:
                # Scenario doesn't exist, add it
                if "scenarios" not in data:
                    data["scenarios"] = []
                data["scenarios"].append(scenario)
            
            # Write back to file
            with open(self.database_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Added new scenario {scenario['id']} to JSON database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add scenario to JSON database: {e}")
            return False
    
    def update_scenario(self, scenario_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing scenario in the database.
        
        Args:
            scenario_id: The ID of the scenario to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_sqlite:
            return self._update_scenario_sqlite(scenario_id, updates)
        else:
            return self._update_scenario_json(scenario_id, updates)
    
    def _update_scenario_sqlite(self, scenario_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing scenario in the SQLite database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Construct the SET part of the SQL query
            set_clause = []
            params = []
            
            for key, value in updates.items():
                if key in ['correct_answer', 'generated']:
                    # Convert boolean to INTEGER for SQLite
                    value = 1 if value else 0
                
                set_clause.append(f"{key} = ?")
                params.append(value)
            
            # Add the scenario_id to the params
            params.append(scenario_id)
            
            # Execute the update
            cursor.execute(f'''
            UPDATE scenarios
            SET {', '.join(set_clause)}
            WHERE id = ?
            ''', params)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated scenario {scenario_id} in SQLite database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update scenario in SQLite database: {e}")
            return False
    
    def _update_scenario_json(self, scenario_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing scenario in the JSON database."""
        try:
            with open(self.database_path, 'r') as f:
                data = json.load(f)
            
            # Find the scenario to update
            for i, scenario in enumerate(data.get("scenarios", [])):
                if scenario.get("id") == scenario_id:
                    # Update the scenario
                    for key, value in updates.items():
                        data["scenarios"][i][key] = value
                    
                    # Write back to file
                    with open(self.database_path, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    logger.info(f"Updated scenario {scenario_id} in JSON database")
                    return True
            
            logger.warning(f"Scenario {scenario_id} not found in JSON database")
            return False
            
        except Exception as e:
            logger.error(f"Failed to update scenario in JSON database: {e}")
            return False
    
    def delete_scenario(self, scenario_id: str) -> bool:
        """Delete a scenario from the database.
        
        Args:
            scenario_id: The ID of the scenario to delete
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_sqlite:
            return self._delete_scenario_sqlite(scenario_id)
        else:
            return self._delete_scenario_json(scenario_id)
    
    def _delete_scenario_sqlite(self, scenario_id: str) -> bool:
        """Delete a scenario from the SQLite database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Deleted scenario {scenario_id} from SQLite database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete scenario from SQLite database: {e}")
            return False
    
    def _delete_scenario_json(self, scenario_id: str) -> bool:
        """Delete a scenario from the JSON database."""
        try:
            with open(self.database_path, 'r') as f:
                data = json.load(f)
            
            # Find the scenario to delete
            for i, scenario in enumerate(data.get("scenarios", [])):
                if scenario.get("id") == scenario_id:
                    # Remove the scenario
                    del data["scenarios"][i]
                    
                    # Write back to file
                    with open(self.database_path, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    logger.info(f"Deleted scenario {scenario_id} from JSON database")
                    return True
            
            logger.warning(f"Scenario {scenario_id} not found in JSON database")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete scenario from JSON database: {e}")
            return False