import os
import json
import sqlite3
import logging
import datetime
from typing import Dict, List, Optional, Union, Any

# Configure logging
logger = logging.getLogger('NASE.UserManager')

class UserManager:
    """Manages user profiles, performance tracking, and session history.
    
    This class handles all user-related data, including:
    - Creating and updating user profiles
    - Recording user responses to scenarios
    - Tracking session history
    - Retrieving performance metrics
    """
    
    def __init__(self, database_path: str, use_sqlite: bool = False):
        """Initialize the user manager.
        
        Args:
            database_path: Path to the database (JSON or SQLite)
            use_sqlite: If True, use SQLite database, otherwise use JSON
        """
        self.database_path = database_path
        self.use_sqlite = use_sqlite
        
        # Derive user database path from scenario database path
        if use_sqlite:
            self.user_database_path = os.path.join(
                os.path.dirname(database_path),
                'users.db'
            )
        else:
            self.user_database_path = os.path.join(
                os.path.dirname(database_path),
                'users.json'
            )
        
        # Ensure the database exists
        self._initialize_database()
        
        logger.info(f"UserManager initialized with {'SQLite' if use_sqlite else 'JSON'} database at {self.user_database_path}")
    
    def _initialize_database(self) -> None:
        """Initialize the user database if it doesn't exist."""
        if self.use_sqlite:
            self._initialize_sqlite()
        else:
            self._initialize_json()
    
    def _initialize_sqlite(self) -> None:
        """Initialize the SQLite user database if it doesn't exist."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.user_database_path), exist_ok=True)
        
        # Connect to the database
        conn = sqlite3.connect(self.user_database_path)
        cursor = conn.cursor()
        
        # Create users table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            created_at TEXT NOT NULL,
            last_login TEXT,
            current_difficulty INTEGER DEFAULT 1,
            total_scenarios_attempted INTEGER DEFAULT 0,
            total_correct_responses INTEGER DEFAULT 0
        )
        ''')
        
        # Create responses table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            scenario_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            correct INTEGER NOT NULL,
            difficulty INTEGER NOT NULL,
            response_time REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create sessions table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration_seconds REAL,
            total_scenarios INTEGER DEFAULT 0,
            correct_responses INTEGER DEFAULT 0,
            accuracy REAL DEFAULT 0,
            final_difficulty INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"SQLite user database initialized at {self.user_database_path}")
    
    def _initialize_json(self) -> None:
        """Initialize the JSON user database if it doesn't exist."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.user_database_path), exist_ok=True)
        
        # Check if file exists
        if not os.path.exists(self.user_database_path):
            logger.info(f"Creating new JSON user database at {self.user_database_path}")
            
            # Create initial database structure
            data = {
                "users": {},
                "responses": [],
                "sessions": []
            }
            
            # Write to file
            with open(self.user_database_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        logger.info(f"JSON user database initialized at {self.user_database_path}")
    
    def create_user_profile(self, user_id: str, name: str = None, email: str = None) -> Dict[str, Any]:
        """Create a new user profile.
        
        Args:
            user_id: Unique identifier for the user
            name: Optional user name
            email: Optional user email
            
        Returns:
            The created user profile
        """
        # Check if user already exists
        existing_user = self.get_user_profile(user_id)
        if existing_user:
            logger.warning(f"User {user_id} already exists, returning existing profile")
            return existing_user
        
        # Create new user profile
        now = datetime.datetime.now().isoformat()
        user_profile = {
            "id": user_id,
            "name": name,
            "email": email,
            "created_at": now,
            "last_login": now,
            "current_difficulty": 1,
            "total_scenarios_attempted": 0,
            "total_correct_responses": 0
        }
        
        if self.use_sqlite:
            self._create_user_profile_sqlite(user_profile)
        else:
            self._create_user_profile_json(user_profile)
        
        logger.info(f"Created new user profile for {user_id}")
        return user_profile
    
    def _create_user_profile_sqlite(self, user_profile: Dict[str, Any]) -> None:
        """Create a new user profile in the SQLite database."""
        conn = sqlite3.connect(self.user_database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO users (id, name, email, created_at, last_login, current_difficulty, 
                         total_scenarios_attempted, total_correct_responses)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_profile["id"],
            user_profile.get("name"),
            user_profile.get("email"),
            user_profile["created_at"],
            user_profile["last_login"],
            user_profile["current_difficulty"],
            user_profile["total_scenarios_attempted"],
            user_profile["total_correct_responses"]
        ))
        
        conn.commit()
        conn.close()
    
    def _create_user_profile_json(self, user_profile: Dict[str, Any]) -> None:
        """Create a new user profile in the JSON database."""
        with open(self.user_database_path, 'r') as f:
            data = json.load(f)
        
        # Add user to users dictionary
        data["users"][user_profile["id"]] = user_profile
        
        # Write back to file
        with open(self.user_database_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a user profile by ID.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            The user profile dictionary or None if not found
        """
        if self.use_sqlite:
            return self._get_user_profile_sqlite(user_id)
        else:
            return self._get_user_profile_json(user_id)
    
    def _get_user_profile_sqlite(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a user profile from the SQLite database."""
        conn = sqlite3.connect(self.user_database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row:
            user_profile = dict(row)
            conn.close()
            return user_profile
        
        conn.close()
        return None
    
    def _get_user_profile_json(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a user profile from the JSON database."""
        with open(self.user_database_path, 'r') as f:
            data = json.load(f)
        
        return data["users"].get(user_id)
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update a user profile.
        
        Args:
            user_id: The unique identifier for the user
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_sqlite:
            return self._update_user_profile_sqlite(user_id, updates)
        else:
            return self._update_user_profile_json(user_id, updates)
    
    def _update_user_profile_sqlite(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update a user profile in the SQLite database."""
        try:
            conn = sqlite3.connect(self.user_database_path)
            cursor = conn.cursor()
            
            # Construct the SET part of the SQL query
            set_clause = []
            params = []
            
            for key, value in updates.items():
                set_clause.append(f"{key} = ?")
                params.append(value)
            
            # Add the user_id to the params
            params.append(user_id)
            
            # Execute the update
            cursor.execute(f'''
            UPDATE users
            SET {', '.join(set_clause)}
            WHERE id = ?
            ''', params)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated user profile for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user profile in SQLite database: {e}")
            return False
    
    def _update_user_profile_json(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update a user profile in the JSON database."""
        try:
            with open(self.user_database_path, 'r') as f:
                data = json.load(f)
            
            if user_id not in data["users"]:
                logger.warning(f"User {user_id} not found in JSON database")
                return False
            
            # Update the user profile
            for key, value in updates.items():
                data["users"][user_id][key] = value
            
            # Write back to file
            with open(self.user_database_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Updated user profile for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user profile in JSON database: {e}")
            return False
    
    def update_user_difficulty(self, user_id: str, difficulty: int) -> bool:
        """Update a user's current difficulty level.
        
        Args:
            user_id: The unique identifier for the user
            difficulty: The new difficulty level
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_user_profile(user_id, {"current_difficulty": difficulty})
    
    def record_response(self, response_data: Dict[str, Any]) -> bool:
        """Record a user's response to a scenario.
        
        Args:
            response_data: Dictionary containing response details
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_sqlite:
            return self._record_response_sqlite(response_data)
        else:
            return self._record_response_json(response_data)
    
    def _record_response_sqlite(self, response_data: Dict[str, Any]) -> bool:
        """Record a user's response in the SQLite database."""
        try:
            conn = sqlite3.connect(self.user_database_path)
            cursor = conn.cursor()
            
            # Insert the response
            cursor.execute('''
            INSERT INTO responses (user_id, scenario_id, timestamp, correct, difficulty, response_time)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                response_data["user_id"],
                response_data["scenario_id"],
                response_data["timestamp"],
                1 if response_data["correct"] else 0,
                response_data["difficulty"],
                response_data.get("response_time")
            ))
            
            # Update user statistics
            cursor.execute('''
            UPDATE users
            SET total_scenarios_attempted = total_scenarios_attempted + 1,
                total_correct_responses = total_correct_responses + ?
            WHERE id = ?
            ''', (1 if response_data["correct"] else 0, response_data["user_id"]))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded response for user {response_data['user_id']} to scenario {response_data['scenario_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record response in SQLite database: {e}")
            return False
    
    def _record_response_json(self, response_data: Dict[str, Any]) -> bool:
        """Record a user's response in the JSON database."""
        try:
            with open(self.user_database_path, 'r') as f:
                data = json.load(f)
            
            # Add response to responses list
            data["responses"].append(response_data)
            
            # Update user statistics
            if response_data["user_id"] in data["users"]:
                data["users"][response_data["user_id"]]["total_scenarios_attempted"] += 1
                if response_data["correct"]:
                    data["users"][response_data["user_id"]]["total_correct_responses"] += 1
            
            # Write back to file
            with open(self.user_database_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Recorded response for user {response_data['user_id']} to scenario {response_data['scenario_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record response in JSON database: {e}")
            return False
    
    def get_recent_responses(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get a user's most recent responses.
        
        Args:
            user_id: The unique identifier for the user
            limit: Maximum number of responses to return
            
        Returns:
            List of response dictionaries, most recent first
        """
        if self.use_sqlite:
            return self._get_recent_responses_sqlite(user_id, limit)
        else:
            return self._get_recent_responses_json(user_id, limit)
    
    def _get_recent_responses_sqlite(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get a user's most recent responses from the SQLite database."""
        conn = sqlite3.connect(self.user_database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM responses
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        
        responses = []
        for row in rows:
            response = dict(row)
            response["correct"] = bool(response["correct"])
            responses.append(response)
        
        conn.close()
        return responses
    
    def _get_recent_responses_json(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get a user's most recent responses from the JSON database."""
        with open(self.user_database_path, 'r') as f:
            data = json.load(f)
        
        # Filter responses by user_id
        user_responses = [r for r in data["responses"] if r["user_id"] == user_id]
        
        # Sort by timestamp (most recent first)
        user_responses.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Limit the number of responses
        return user_responses[:limit]
    
    def get_session_responses(self, user_id: str, start_time: str) -> List[Dict[str, Any]]:
        """Get all responses for a user in the current session.
        
        Args:
            user_id: The unique identifier for the user
            start_time: The ISO-formatted start time of the session
            
        Returns:
            List of response dictionaries in the session
        """
        if self.use_sqlite:
            return self._get_session_responses_sqlite(user_id, start_time)
        else:
            return self._get_session_responses_json(user_id, start_time)
    
    def _get_session_responses_sqlite(self, user_id: str, start_time: str) -> List[Dict[str, Any]]:
        """Get session responses from the SQLite database."""
        conn = sqlite3.connect(self.user_database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM responses
        WHERE user_id = ? AND timestamp >= ?
        ORDER BY timestamp ASC
        ''', (user_id, start_time))
        
        rows = cursor.fetchall()
        
        responses = []
        for row in rows:
            response = dict(row)
            response["correct"] = bool(response["correct"])
            responses.append(response)
        
        conn.close()
        return responses
    
    def _get_session_responses_json(self, user_id: str, start_time: str) -> List[Dict[str, Any]]:
        """Get session responses from the JSON database."""
        with open(self.user_database_path, 'r') as f:
            data = json.load(f)
        
        # Filter responses by user_id and timestamp
        session_responses = [
            r for r in data["responses"]
            if r["user_id"] == user_id and r["timestamp"] >= start_time
        ]
        
        # Sort by timestamp
        session_responses.sort(key=lambda x: x["timestamp"])
        
        return session_responses
    
    def record_session(self, session_data: Dict[str, Any]) -> bool:
        """Record a completed session.
        
        Args:
            session_data: Dictionary containing session details
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_sqlite:
            return self._record_session_sqlite(session_data)
        else:
            return self._record_session_json(session_data)
    
    def _record_session_sqlite(self, session_data: Dict[str, Any]) -> bool:
        """Record a session in the SQLite database."""
        try:
            conn = sqlite3.connect(self.user_database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO sessions (
                user_id, start_time, end_time, duration_seconds,
                total_scenarios, correct_responses, accuracy, final_difficulty
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_data["user_id"],
                session_data["start_time"],
                session_data["end_time"],
                session_data["duration_seconds"],
                session_data["total_scenarios"],
                session_data["correct_responses"],
                session_data["accuracy"],
                session_data["final_difficulty"]
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded session for user {session_data['user_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record session in SQLite database: {e}")
            return False
    
    def _record_session_json(self, session_data: Dict[str, Any]) -> bool:
        """Record a session in the JSON database."""
        try:
            with open(self.user_database_path, 'r') as f:
                data = json.load(f)
            
            # Add session to sessions list
            data["sessions"].append(session_data)
            
            # Write back to file
            with open(self.user_database_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Recorded session for user {session_data['user_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record session in JSON database: {e}")
            return False
    
    def get_user_performance_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of a user's overall performance.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            Dictionary with performance metrics
        """
        user_profile = self.get_user_profile(user_id)
        if not user_profile:
            logger.warning(f"User {user_id} not found")
            return {}
        
        # Get all user responses
        if self.use_sqlite:
            responses = self._get_all_user_responses_sqlite(user_id)
            sessions = self._get_all_user_sessions_sqlite(user_id)
        else:
            responses = self._get_all_user_responses_json(user_id)
            sessions = self._get_all_user_sessions_json(user_id)
        
        # Calculate metrics
        total_scenarios = len(responses)
        correct_responses = sum(1 for r in responses if r.get("correct", False))
        accuracy = correct_responses / total_scenarios if total_scenarios > 0 else 0
        
        # Calculate average difficulty over time
        if responses:
            difficulties = [r.get("difficulty", 1) for r in responses]
            avg_difficulty = sum(difficulties) / len(difficulties)
        else:
            avg_difficulty = 1
        
        # Calculate total training time
        total_duration = sum(s.get("duration_seconds", 0) for s in sessions)
        
        return {
            "user_id": user_id,
            "total_scenarios": total_scenarios,
            "correct_responses": correct_responses,
            "accuracy": accuracy,
            "current_difficulty": user_profile.get("current_difficulty", 1),
            "average_difficulty": avg_difficulty,
            "total_sessions": len(sessions),
            "total_training_time": total_duration,
            "created_at": user_profile.get("created_at"),
            "last_login": user_profile.get("last_login")
        }
    
    def _get_all_user_responses_sqlite(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all responses for a user from the SQLite database."""
        conn = sqlite3.connect(self.user_database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM responses WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        
        responses = []
        for row in rows:
            response = dict(row)
            response["correct"] = bool(response["correct"])
            responses.append(response)
        
        conn.close()
        return responses
    
    def _get_all_user_responses_json(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all responses for a user from the JSON database."""
        with open(self.user_database_path, 'r') as f:
            data = json.load(f)
        
        return [r for r in data["responses"] if r["user_id"] == user_id]
    
    def _get_all_user_sessions_sqlite(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user from the SQLite database."""
        conn = sqlite3.connect(self.user_database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sessions WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        
        sessions = [dict(row) for row in rows]
        
        conn.close()
        return sessions
    
    def _get_all_user_sessions_json(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user from the JSON database."""
        with open(self.user_database_path, 'r') as f:
            data = json.load(f)
        
        return [s for s in data["sessions"] if s["user_id"] == user_id]