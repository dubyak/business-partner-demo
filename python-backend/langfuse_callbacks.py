"""
Langfuse callback handlers for LangChain integration.

This module provides callbacks to automatically trace LLM calls
through LangChain's callback system.
"""

from typing import Any, Dict, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langfuse.decorators import langfuse_context


class LangfuseCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler that automatically traces LLM calls to Langfuse.
    
    This handler integrates with Langfuse's @observe decorator context
    to create nested spans for LLM generations.
    """
    
    def __init__(self, trace_name: Optional[str] = None):
        """
        Initialize the callback handler.
        
        Args:
            trace_name: Optional name for the trace (defaults to "llm-call")
        """
        super().__init__()
        self.trace_name = trace_name or "llm-call"
    
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: list[str], **kwargs: Any
    ) -> None:
        """Called when LLM starts running."""
        # The @observe decorator context will handle the span creation
        # We just need to attach input metadata
        try:
            langfuse_context.update_current_observation(
                input={
                    "prompts": prompts,
                    "model": serialized.get("model_name", "unknown"),
                    **kwargs
                }
            )
        except Exception as e:
            # Don't fail if Langfuse context is not available
            pass
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM ends running."""
        try:
            # Extract token usage if available
            token_usage = {}
            if response.llm_output:
                token_usage = response.llm_output.get("token_usage", {})
            
            # Extract generations
            generations = []
            for gen_list in response.generations:
                for gen in gen_list:
                    generations.append({
                        "text": gen.text,
                        "generation_info": gen.generation_info
                    })
            
            # For most debugging/observability use-cases, the PRIMARY thing we
            # want to see in Langfuse is the actual LLM text output.
            # Expose the first generation's text at the top-level `text` field
            # so it shows up clearly in the UI while still keeping the full
            # generations array for deeper inspection.
            primary_text = generations[0]["text"] if generations else None
            
            langfuse_context.update_current_observation(
                output={
                    # Surface main completion directly
                    "text": primary_text,
                    # Keep full structured data for analysis
                    "generations": generations,
                    "token_usage": token_usage,
                },
                metadata={
                    "model": kwargs.get("model", "unknown"),
                    **kwargs
                }
            )
        except Exception as e:
            # Don't fail if Langfuse context is not available
            pass
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when LLM errors."""
        try:
            langfuse_context.update_current_observation(
                level="ERROR",
                output={"error": str(error), "error_type": type(error).__name__}
            )
        except Exception:
            pass

