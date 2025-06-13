import logging
import json
import requests
import os
from typing import Dict, Any, List, Optional, Union

# Configure logging
logger = logging.getLogger('NASE.LLMIntegration')

class LLMConnector:
    """Base class for LLM (Large Language Model) integration.
    
    This abstract class defines the interface for LLM connectors.
    Concrete implementations should inherit from this class and implement
    the generate method.
    """
    
    def generate(self, prompt: str) -> Dict[str, Any]:
        """Generate content using the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            A dictionary containing the generated content
        """
        raise NotImplementedError("Subclasses must implement generate")


class OpenAIConnector(LLMConnector):
    """Connector for OpenAI's API (e.g., GPT models).
    
    This class provides integration with OpenAI's API for generating
    cybersecurity training scenarios.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """Initialize the OpenAI connector.
        
        Args:
            api_key: API key for authentication with OpenAI
            model: The model to use for generation
        """
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        logger.info(f"OpenAIConnector initialized with model: {model}")
    
    def generate(self, prompt: str) -> Dict[str, Any]:
        """Generate content using OpenAI's API.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            A dictionary containing the parsed generated content
        """
        try:
            # Prepare the request to the OpenAI API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Construct a system prompt that guides the model to generate structured output
            system_prompt = (
                "You are a cybersecurity training scenario generator. "
                "Create realistic and educational phishing or security awareness scenarios. "
                "Your response should be in JSON format with the following fields: "
                "title, description, content, correct_answer (true/false), explanation, and difficulty (1-5)."
            )
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            # Make the API request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # Parse the JSON response
                try:
                    # Try to parse the entire response as JSON
                    scenario_data = json.loads(content)
                except json.JSONDecodeError:
                    # If that fails, try to extract JSON from the text
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        try:
                            scenario_data = json.loads(json_match.group(0))
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse JSON from response: {content}")
                            # Return a basic structure with the raw content
                            return {
                                "title": "Generated Scenario",
                                "description": "A generated cybersecurity scenario",
                                "content": content,
                                "correct_answer": True,
                                "explanation": "Please review the scenario carefully",
                                "difficulty": 3
                            }
                    else:
                        logger.error(f"No JSON found in response: {content}")
                        # Return a basic structure with the raw content
                        return {
                            "title": "Generated Scenario",
                            "description": "A generated cybersecurity scenario",
                            "content": content,
                            "correct_answer": True,
                            "explanation": "Please review the scenario carefully",
                            "difficulty": 3
                        }
                
                logger.info(f"Generated scenario with title: {scenario_data.get('title', 'Untitled')}")
                return scenario_data
            else:
                logger.warning(f"Failed to generate content: {response.status_code} - {response.text}")
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise


class LocalLLMConnector(LLMConnector):
    """Connector for local LLM deployments.
    
    This class provides integration with locally deployed language models
    such as LLaMA, Falcon, or other open-source models.
    """
    
    def __init__(self, api_url: str, model: str = "local_model"):
        """Initialize the local LLM connector.
        
        Args:
            api_url: URL for the local LLM API
            model: The model name or identifier
        """
        self.api_url = api_url
        self.model = model
        
        logger.info(f"LocalLLMConnector initialized with URL: {api_url}, model: {model}")
    
    def generate(self, prompt: str) -> Dict[str, Any]:
        """Generate content using a local LLM.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            A dictionary containing the parsed generated content
        """
        try:
            # Prepare the request to the local LLM API
            headers = {
                "Content-Type": "application/json"
            }
            
            # Construct a system prompt that guides the model to generate structured output
            system_prompt = (
                "You are a cybersecurity training scenario generator. "
                "Create realistic and educational phishing or security awareness scenarios. "
                "Your response should be in JSON format with the following fields: "
                "title, description, content, correct_answer (true/false), explanation, and difficulty (1-5)."
            )
            
            # The payload structure may need to be adjusted based on the specific API
            payload = {
                "model": self.model,
                "prompt": f"{system_prompt}\n\n{prompt}",
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            # Make the API request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                content = data.get("text", "")
                
                # Parse the JSON response
                try:
                    # Try to parse the entire response as JSON
                    scenario_data = json.loads(content)
                except json.JSONDecodeError:
                    # If that fails, try to extract JSON from the text
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        try:
                            scenario_data = json.loads(json_match.group(0))
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse JSON from response: {content}")
                            # Return a basic structure with the raw content
                            return {
                                "title": "Generated Scenario",
                                "description": "A generated cybersecurity scenario",
                                "content": content,
                                "correct_answer": True,
                                "explanation": "Please review the scenario carefully",
                                "difficulty": 3
                            }
                    else:
                        logger.error(f"No JSON found in response: {content}")
                        # Return a basic structure with the raw content
                        return {
                            "title": "Generated Scenario",
                            "description": "A generated cybersecurity scenario",
                            "content": content,
                            "correct_answer": True,
                            "explanation": "Please review the scenario carefully",
                            "difficulty": 3
                        }
                
                logger.info(f"Generated scenario with title: {scenario_data.get('title', 'Untitled')}")
                return scenario_data
            else:
                logger.warning(f"Failed to generate content: {response.status_code} - {response.text}")
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise


class MockLLMConnector(LLMConnector):
    """A mock implementation of LLM generation for testing and development.
    
    This class simulates LLM generation without requiring an external service.
    It can be used for development, testing, or when an actual LLM service
    is not available.
    """
    
    def __init__(self, templates_path: str = None):
        """Initialize the mock LLM connector.
        
        Args:
            templates_path: Optional path to JSON file with scenario templates
        """
        self.templates = []
        
        # Load templates if provided
        if templates_path and os.path.exists(templates_path):
            try:
                with open(templates_path, 'r') as f:
                    self.templates = json.load(f)
                logger.info(f"Loaded {len(self.templates)} scenario templates from {templates_path}")
            except Exception as e:
                logger.error(f"Failed to load templates from {templates_path}: {e}")
        
        # If no templates loaded, use default templates
        if not self.templates:
            self.templates = self._get_default_templates()
            logger.info(f"Using {len(self.templates)} default scenario templates")
    
    def generate(self, prompt: str) -> Dict[str, Any]:
        """Generate content using templates.
        
        Args:
            prompt: The prompt describing the desired scenario
            
        Returns:
            A dictionary containing the generated scenario
        """
        import random
        
        # Parse the prompt to extract parameters
        difficulty = self._extract_difficulty(prompt)
        theme = self._extract_theme(prompt)
        
        # Filter templates by difficulty and theme if specified
        matching_templates = self.templates
        
        if difficulty:
            matching_templates = [t for t in matching_templates if t.get("difficulty") == difficulty]
        
        if theme and matching_templates:
            # Find templates with matching theme, if none match, keep all difficulty-matched templates
            theme_matched = [t for t in matching_templates if theme.lower() in t.get("theme", "").lower()]
            if theme_matched:
                matching_templates = theme_matched
        
        # If no matching templates, use all templates
        if not matching_templates:
            matching_templates = self.templates
        
        # Select a random template
        template = random.choice(matching_templates)
        
        # Customize the template
        scenario = self._customize_template(template, difficulty, theme)
        
        logger.info(f"Generated mock scenario with title: {scenario['title']}")
        return scenario
    
    def _extract_difficulty(self, prompt: str) -> Optional[int]:
        """Extract difficulty level from the prompt."""
        import re
        
        # Look for patterns like "difficulty level 3" or "level 3 difficulty"
        difficulty_match = re.search(r'difficulty\s*level\s*(\d+)|level\s*(\d+)\s*difficulty', prompt, re.IGNORECASE)
        if difficulty_match:
            # Get the first non-None group
            for group in difficulty_match.groups():
                if group:
                    difficulty = int(group)
                    return min(5, max(1, difficulty))  # Ensure difficulty is between 1-5
        
        # Look for patterns like "difficulty 3"
        difficulty_match = re.search(r'difficulty\s*(\d+)', prompt, re.IGNORECASE)
        if difficulty_match:
            difficulty = int(difficulty_match.group(1))
            return min(5, max(1, difficulty))  # Ensure difficulty is between 1-5
        
        return None
    
    def _extract_theme(self, prompt: str) -> Optional[str]:
        """Extract theme from the prompt."""
        import re
        
        # Look for patterns like "about phishing" or "theme: social engineering"
        theme_match = re.search(r'about\s+([\w\s]+)|theme[:\s]+([\w\s]+)', prompt, re.IGNORECASE)
        if theme_match:
            # Get the first non-None group
            for group in theme_match.groups():
                if group:
                    return group.strip()
        
        # Common cybersecurity themes to check for
        themes = [
            "phishing", "social engineering", "password", "malware", "ransomware",
            "data breach", "insider threat", "physical security", "mobile security"
        ]
        
        for theme in themes:
            if theme in prompt.lower():
                return theme
        
        return None
    
    def _customize_template(self, template: Dict[str, Any], difficulty: Optional[int], theme: Optional[str]) -> Dict[str, Any]:
        """Customize a template based on the requested difficulty and theme."""
        import random
        import copy
        
        # Create a deep copy to avoid modifying the original template
        scenario = copy.deepcopy(template)
        
        # Set difficulty if specified
        if difficulty:
            scenario["difficulty"] = difficulty
        
        # Customize based on theme if specified
        if theme:
            scenario["theme"] = theme
            
            # Modify title and description to include theme
            if "title" in scenario and not theme.lower() in scenario["title"].lower():
                scenario["title"] = f"{theme.title()} {scenario['title']}"
            
            if "description" in scenario:
                scenario["description"] = f"A {theme.lower()} scenario: {scenario['description']}"
        
        # Add some randomness to make each generation unique
        if "content" in scenario:
            # List of company names to randomly insert
            companies = ["Acme Corp", "TechGiant", "SecureBank", "GlobalHealth", "InnovateCo"]
            company = random.choice(companies)
            
            # Replace placeholders or generic terms with random values
            scenario["content"] = scenario["content"].replace("the company", company)
            scenario["content"] = scenario["content"].replace("your company", company)
        
        return scenario
    
    def _get_default_templates(self) -> List[Dict[str, Any]]:
        """Return a list of default scenario templates."""
        return [
            {
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
            }
        ]