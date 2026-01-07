"""Middleware for model fallback functionality."""
from typing import Optional, List, Any
from langchain_groq import ChatGroq
from langchain_core.runnables import ConfigurableField
from langchain_core.language_models.chat_models import BaseChatModel
import logging

logger = logging.getLogger(__name__)


class ModelFallbackMiddleware:
    """Middleware that provides model fallback functionality.
    
    If the primary model fails, automatically falls back to backup model(s).
    """
    
    def __init__(
        self,
        primary_model_name: str = "qwen/qwen3-32b",
        backup_model_name: str = "openai/gpt-oss-20b",
        temperature: float = 0.0
    ):
        """Initialize the middleware with primary and backup models.
        
        Args:
            primary_model_name: Name of the primary model to use
            backup_model_name: Name of the backup model to use if primary fails
            temperature: Temperature setting for the models
        """
        self.primary_model_name = primary_model_name
        self.backup_model_name = backup_model_name
        self.temperature = temperature
        
        self.primary_model = self._create_model(primary_model_name)
        self.backup_model = self._create_model(backup_model_name)
        
        logger.info(f"Initialized ModelFallbackMiddleware with primary: {primary_model_name}, backup: {backup_model_name}")
    
    def _create_model(self, model_name: str) -> BaseChatModel:
        """Create a ChatGroq model with the given configuration.
        
        Args:
            model_name: Name of the model to create
            
        Returns:
            Configured ChatGroq model
        """
        return ChatGroq(
            model=model_name,
            temperature=self.temperature,
            timeout=10.0,  # Set timeout to 10 seconds for faster fallback
            max_retries=1,  # Only retry once before falling back
        ).configurable_fields(
            callbacks=ConfigurableField(
                id="callbacks",
                name="callbacks",
                description="A list of callback handlers to use for streaming.",
            )
        )
    
    def get_model(self) -> BaseChatModel:
        """Get the primary model with fallback capability.
        
        Returns:
            The primary model configured with fallback
        """
        # Use LangChain's built-in fallback mechanism
        return self.primary_model.with_fallbacks([self.backup_model])
    
    def get_primary_model(self) -> BaseChatModel:
        """Get only the primary model without fallback.
        
        Returns:
            The primary model
        """
        return self.primary_model
    
    def get_backup_model(self) -> BaseChatModel:
        """Get only the backup model.
        
        Returns:
            The backup model
        """
        return self.backup_model
    
    def update_primary_model(self, model_name: str):
        """Update the primary model.
        
        Args:
            model_name: Name of the new primary model
        """
        self.primary_model_name = model_name
        self.primary_model = self._create_model(model_name)
        logger.info(f"Updated primary model to: {model_name}")
    
    def update_backup_model(self, model_name: str):
        """Update the backup model.
        
        Args:
            model_name: Name of the new backup model
        """
        self.backup_model_name = model_name
        self.backup_model = self._create_model(model_name)
        logger.info(f"Updated backup model to: {model_name}")
