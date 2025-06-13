import logging
import requests
import json
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger('NASE.CognitiveLoad')

class CognitiveLoadEstimator:
    """Base class for cognitive load estimation.
    
    This abstract class defines the interface for cognitive load estimators.
    Concrete implementations should inherit from this class and implement
    the estimate_load method.
    """
    
    def estimate_load(self, user_id: str) -> float:
        """Estimate the cognitive load for a user.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            A float between 0 and 1 representing the estimated cognitive load,
            where 0 is minimal load and 1 is maximum load
        """
        raise NotImplementedError("Subclasses must implement estimate_load")


class NCLEConnector(CognitiveLoadEstimator):
    """Connector for the NCLE (Neural Cognitive Load Estimator) service.
    
    This class provides integration with an external NCLE service that can
    estimate cognitive load based on various inputs such as response times,
    error rates, and potentially biometric data.
    """
    
    def __init__(self, api_key: str, api_url: str = "https://api.ncle.example.com/v1"):
        """Initialize the NCLE connector.
        
        Args:
            api_key: API key for authentication with the NCLE service
            api_url: Base URL for the NCLE API
        """
        self.api_key = api_key
        self.api_url = api_url
        
        logger.info(f"NCLEConnector initialized with API URL: {api_url}")
    
    def estimate_load(self, user_id: str) -> float:
        """Estimate cognitive load using the NCLE service.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            A float between 0 and 1 representing the estimated cognitive load
        """
        try:
            # Prepare the request to the NCLE API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "user_id": user_id,
                "timestamp": self._get_current_timestamp()
            }
            
            # Make the API request
            response = requests.post(
                f"{self.api_url}/estimate",
                headers=headers,
                json=payload
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                cognitive_load = data.get("cognitive_load", 0.5)  # Default to medium load if not provided
                logger.info(f"Estimated cognitive load for user {user_id}: {cognitive_load}")
                return cognitive_load
            else:
                logger.warning(f"Failed to estimate cognitive load: {response.status_code} - {response.text}")
                return 0.5  # Default to medium load on error
                
        except Exception as e:
            logger.error(f"Error estimating cognitive load: {e}")
            return 0.5  # Default to medium load on error
    
    def _get_current_timestamp(self) -> str:
        """Get the current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()


class MockCognitiveLoadEstimator(CognitiveLoadEstimator):
    """A mock implementation of cognitive load estimation for testing and development.
    
    This class simulates cognitive load estimation without requiring an external service.
    It can be used for development, testing, or when an actual cognitive load
    estimation service is not available.
    """
    
    def __init__(self, user_data: Dict[str, Dict[str, Any]] = None):
        """Initialize the mock estimator.
        
        Args:
            user_data: Optional dictionary mapping user IDs to mock data
        """
        self.user_data = user_data or {}
        self.default_load = 0.3  # Default cognitive load (relatively low)
        self.session_counts = {}  # Track number of estimates per user in a session
        
        logger.info("MockCognitiveLoadEstimator initialized")
    
    def estimate_load(self, user_id: str) -> float:
        """Estimate cognitive load using mock data.
        
        This implementation simulates cognitive load by:
        1. Using predefined values if available in user_data
        2. Gradually increasing load over time to simulate fatigue
        3. Adding some randomness to the estimates
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            A float between 0 and 1 representing the estimated cognitive load
        """
        import random
        
        # Initialize session count if not exists
        if user_id not in self.session_counts:
            self.session_counts[user_id] = 0
        
        # Increment session count
        self.session_counts[user_id] += 1
        
        # Get predefined load if available
        if user_id in self.user_data and "cognitive_load" in self.user_data[user_id]:
            base_load = self.user_data[user_id]["cognitive_load"]
        else:
            # Start with default load
            base_load = self.default_load
        
        # Increase load over time to simulate fatigue
        fatigue_factor = min(0.5, self.session_counts[user_id] * 0.02)  # Max +0.5 after 25 estimates
        
        # Add some randomness (-0.1 to +0.1)
        randomness = (random.random() - 0.5) * 0.2
        
        # Calculate final load
        cognitive_load = min(1.0, max(0.0, base_load + fatigue_factor + randomness))
        
        logger.info(f"Mock estimated cognitive load for user {user_id}: {cognitive_load:.2f} "
                   f"(base: {base_load:.2f}, fatigue: +{fatigue_factor:.2f}, random: {randomness:.2f})")
        
        return cognitive_load
    
    def reset_session(self, user_id: str) -> None:
        """Reset the session count for a user.
        
        This can be called when a user takes a break or starts a new session.
        
        Args:
            user_id: The unique identifier for the user
        """
        if user_id in self.session_counts:
            self.session_counts[user_id] = 0
            logger.info(f"Reset session count for user {user_id}")
    
    def set_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """Set mock data for a specific user.
        
        Args:
            user_id: The unique identifier for the user
            data: Dictionary of mock data for the user
        """
        self.user_data[user_id] = data
        logger.info(f"Set mock data for user {user_id}: {data}")