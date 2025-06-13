import logging
from typing import Dict, List, Optional, Union, Any

# Configure logging
logger = logging.getLogger('NASE.DifficultyAdjuster')

class DifficultyAdjuster:
    """Adjusts scenario difficulty based on user performance.
    
    This class implements the adaptive difficulty algorithm that determines
    how scenario difficulty should change based on user responses, response times,
    and historical performance patterns.
    """
    
    def __init__(self, 
                 min_difficulty: int = 1, 
                 max_difficulty: int = 5,
                 consecutive_correct_threshold: int = 2,
                 consecutive_incorrect_threshold: int = 1,
                 response_time_weight: float = 0.3):
        """Initialize the difficulty adjuster.
        
        Args:
            min_difficulty: Minimum difficulty level (default: 1)
            max_difficulty: Maximum difficulty level (default: 5)
            consecutive_correct_threshold: Number of consecutive correct answers needed to increase difficulty
            consecutive_incorrect_threshold: Number of consecutive incorrect answers needed to decrease difficulty
            response_time_weight: Weight given to response time in difficulty adjustment (0-1)
        """
        self.min_difficulty = min_difficulty
        self.max_difficulty = max_difficulty
        self.consecutive_correct_threshold = consecutive_correct_threshold
        self.consecutive_incorrect_threshold = consecutive_incorrect_threshold
        self.response_time_weight = response_time_weight
        
        logger.info("DifficultyAdjuster initialized")
    
    def adjust_difficulty(self, 
                          current_difficulty: int, 
                          correct: bool, 
                          response_time: Optional[float] = None,
                          user_history: List[Dict[str, Any]] = None) -> int:
        """Adjust difficulty based on user performance.
        
        Args:
            current_difficulty: The current difficulty level
            correct: Whether the user answered correctly
            response_time: Optional time (in seconds) taken to respond
            user_history: Optional list of recent user responses
            
        Returns:
            The new difficulty level
        """
        # Ensure current_difficulty is within bounds
        current_difficulty = max(self.min_difficulty, min(self.max_difficulty, current_difficulty))
        
        # Initialize new difficulty to current difficulty
        new_difficulty = current_difficulty
        
        # If no history is provided, make a simple adjustment based on correctness
        if not user_history:
            if correct:
                # Increase difficulty if correct
                if current_difficulty < self.max_difficulty:
                    new_difficulty = current_difficulty + 1
            else:
                # Decrease difficulty if incorrect
                if current_difficulty > self.min_difficulty:
                    new_difficulty = current_difficulty - 1
        else:
            # Make a more sophisticated adjustment based on history
            new_difficulty = self._adjust_based_on_history(current_difficulty, correct, response_time, user_history)
        
        # Ensure the new difficulty is within bounds
        new_difficulty = max(self.min_difficulty, min(self.max_difficulty, new_difficulty))
        
        logger.info(f"Adjusted difficulty from {current_difficulty} to {new_difficulty} "
                   f"based on {'correct' if correct else 'incorrect'} answer")
        
        return new_difficulty
    
    def _adjust_based_on_history(self, 
                                current_difficulty: int, 
                                correct: bool, 
                                response_time: Optional[float],
                                user_history: List[Dict[str, Any]]) -> int:
        """Make a sophisticated difficulty adjustment based on user history.
        
        Args:
            current_difficulty: The current difficulty level
            correct: Whether the user answered correctly
            response_time: Optional time (in seconds) taken to respond
            user_history: List of recent user responses
            
        Returns:
            The new difficulty level
        """
        # Add the current response to the history for analysis
        full_history = user_history + [{
            "correct": correct,
            "difficulty": current_difficulty,
            "response_time": response_time
        }]
        
        # Count consecutive correct/incorrect answers
        consecutive_correct = 0
        consecutive_incorrect = 0
        
        # Analyze from most recent to oldest
        for response in reversed(full_history):
            if response["correct"]:
                consecutive_correct += 1
                consecutive_incorrect = 0
            else:
                consecutive_incorrect += 1
                consecutive_correct = 0
        
        # Determine if difficulty should change based on consecutive answers
        if consecutive_correct >= self.consecutive_correct_threshold:
            # Increase difficulty if enough consecutive correct answers
            new_difficulty = current_difficulty + 1
        elif consecutive_incorrect >= self.consecutive_incorrect_threshold:
            # Decrease difficulty if enough consecutive incorrect answers
            new_difficulty = current_difficulty - 1
        else:
            # No change based on correctness pattern
            new_difficulty = current_difficulty
        
        # Adjust based on response time if available
        if response_time is not None and correct:
            # Only adjust for response time if the answer was correct
            new_difficulty = self._adjust_for_response_time(new_difficulty, response_time, full_history)
        
        return new_difficulty
    
    def _adjust_for_response_time(self, 
                                 difficulty: int, 
                                 response_time: float,
                                 history: List[Dict[str, Any]]) -> int:
        """Adjust difficulty based on response time.
        
        If the user answers quickly, they might be ready for a harder difficulty.
        If they answer slowly but correctly, they might be at their limit.
        
        Args:
            difficulty: The current calculated difficulty level
            response_time: Time (in seconds) taken to respond
            history: List of user responses including the current one
            
        Returns:
            The adjusted difficulty level
        """
        # Calculate average response time for correct answers at this difficulty
        relevant_responses = [r for r in history 
                             if r.get("correct", False) 
                             and r.get("difficulty") == difficulty 
                             and r.get("response_time") is not None]
        
        if not relevant_responses:
            return difficulty
        
        avg_response_time = sum(r.get("response_time", 0) for r in relevant_responses) / len(relevant_responses)
        
        # If response time is significantly faster than average, consider increasing difficulty
        if response_time < avg_response_time * 0.7 and difficulty < self.max_difficulty:
            # User answered much faster than average, might be ready for harder questions
            logger.info(f"Fast response time ({response_time:.2f}s vs avg {avg_response_time:.2f}s), "
                       f"considering difficulty increase")
            
            # Apply response time weight to determine if difficulty should increase
            if self.response_time_weight > 0.5:  # Only increase if we give significant weight to response time
                return difficulty + 1
        
        # If response time is significantly slower than average but still correct,
        # the user might be at their limit, so don't increase difficulty further
        if response_time > avg_response_time * 1.5 and difficulty > self.min_difficulty:
            logger.info(f"Slow response time ({response_time:.2f}s vs avg {avg_response_time:.2f}s), "
                       f"considering maintaining current difficulty")
            
            # Apply response time weight
            if self.response_time_weight > 0.5:  # Only adjust if we give significant weight to response time
                return difficulty
        
        return difficulty
    
    def estimate_optimal_difficulty(self, user_history: List[Dict[str, Any]]) -> int:
        """Estimate the optimal difficulty level based on user history.
        
        This can be used to set an initial difficulty when starting a new session
        for a returning user.
        
        Args:
            user_history: List of user responses
            
        Returns:
            The estimated optimal difficulty level
        """
        if not user_history:
            return self.min_difficulty
        
        # Group responses by difficulty
        difficulty_performance = {}
        for response in user_history:
            difficulty = response.get("difficulty", 1)
            if difficulty not in difficulty_performance:
                difficulty_performance[difficulty] = {
                    "total": 0,
                    "correct": 0
                }
            
            difficulty_performance[difficulty]["total"] += 1
            if response.get("correct", False):
                difficulty_performance[difficulty]["correct"] += 1
        
        # Calculate accuracy for each difficulty
        for difficulty, stats in difficulty_performance.items():
            stats["accuracy"] = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        
        # Find the highest difficulty with acceptable accuracy (e.g., > 70%)
        target_accuracy = 0.7
        optimal_difficulty = self.min_difficulty
        
        for difficulty in range(self.max_difficulty, self.min_difficulty - 1, -1):
            if difficulty in difficulty_performance:
                stats = difficulty_performance[difficulty]
                # Only consider difficulties with enough samples
                if stats["total"] >= 3 and stats["accuracy"] >= target_accuracy:
                    optimal_difficulty = difficulty
                    break
        
        logger.info(f"Estimated optimal difficulty: {optimal_difficulty} based on user history")
        return optimal_difficulty