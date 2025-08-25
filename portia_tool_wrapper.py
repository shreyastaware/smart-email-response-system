"""
Custom Tool wrapper for Portia AI compatibility
Handles the abstract Tool class implementation requirements
"""

from typing import Callable, Any, Dict, Optional
from pydantic import BaseModel, Field

class CustomTool:
    """Simple Tool implementation that wraps function-based tools"""
    
    def __init__(self, name: str, description: str, function: Callable):
        """
        Initialize custom tool with function-based implementation
        
        Args:
            name: Tool name
            description: Tool description  
            function: The actual function to execute
        """
        self.name = name
        self.description = description
        self.function = function
        # Add Pydantic-like attributes that Portia might expect
        self.__pydantic_fields_set__ = set()
        self.__pydantic_extra__ = None
        self.__pydantic_private__ = None
    
    def run(self, **kwargs) -> Any:
        """
        Execute the tool function with given arguments
        This method is required by the abstract Tool class
        
        Args:
            **kwargs: Arguments to pass to the function
            
        Returns:
            Result from the function execution
        """
        return self.function(**kwargs)
    
    def __call__(self, **kwargs) -> Any:
        """
        Make the tool callable directly
        
        Args:
            **kwargs: Arguments to pass to the function
            
        Returns:
            Result from the function execution
        """
        return self.run(**kwargs)
    
    def dict(self, **kwargs) -> Dict:
        """Return tool as dictionary for Pydantic compatibility"""
        return {
            'name': self.name,
            'description': self.description
        }
    
    def model_dump(self, **kwargs) -> Dict:
        """Return tool as dictionary (Pydantic v2 compatibility)"""
        return self.dict(**kwargs)


def create_tool(name: str, description: str, function: Callable) -> CustomTool:
    """
    Factory function to create a custom tool
    
    Args:
        name: Tool name
        description: Tool description
        function: The function to wrap
        
    Returns:
        CustomTool instance
    """
    return CustomTool(name=name, description=description, function=function)
