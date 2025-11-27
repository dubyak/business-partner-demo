"""
Evaluators for the Business Partner multi-agent system.

These evaluators can be used with Langfuse's evaluation framework.
"""

import os
import re
from typing import Dict, Any, Optional

# Note: Langfuse evaluators are typically created in the UI or via API
# These are helper functions that can be used with Langfuse's evaluation framework
# To use with Langfuse, create evaluators in the UI and reference them, or use the API

def evaluate_no_looping(output: str, expected_state: dict, forbidden_phrases: Optional[list] = None) -> float:
    """
    Evaluates if agent avoids asking for already-collected information.
    
    Args:
        output: The agent's response text
        expected_state: Dictionary of information that should already be collected
        forbidden_phrases: Optional list of phrases that should NOT appear
    
    Returns:
        Score 0-1 (1 = perfect, 0 = asked for info it already has)
    """
    score = 1.0
    output_lower = output.lower()
    
    # Default forbidden phrases if not provided
    if forbidden_phrases is None:
        forbidden_phrases = []
    
    # Check for forbidden phrases
    for phrase in forbidden_phrases:
        if phrase.lower() in output_lower:
            score -= 0.5
    
    # Check if output asks for business_type when it's already collected
    if expected_state.get("business_type"):
        business_questions = [
            "what type of business",
            "what kind of business",
            "what business do you run",
        ]
        for question in business_questions:
            if question in output_lower:
                score -= 0.3
    
    # Check if output asks for location when it's already collected
    if expected_state.get("location"):
        location_questions = [
            "where are you located",
            "where is your business",
            "what is your location",
        ]
        for question in location_questions:
            if question in output_lower:
                score -= 0.3
    
    # Check if output asks for years_operating when it's already collected
    if expected_state.get("years_operating"):
        years_questions = [
            "how long have you been operating",
            "how many years",
            "how long have you been",
        ]
        for question in years_questions:
            if question in output_lower:
                score -= 0.2
    
    # Bonus: Check if agent acknowledges what it knows
    if expected_state.get("business_type") and expected_state.get("location"):
        if expected_state["business_type"].lower() in output_lower and expected_state["location"].lower() in output_lower:
            score += 0.1  # Bonus for acknowledging
    
    return max(0.0, min(1.0, score))


def evaluate_state_extraction(output_state: dict, expected_state: dict) -> float:
    """
    Evaluates if state extraction is accurate.
    
    Args:
        output_state: The actual state after processing
        expected_state: The expected state values
    
    Returns:
        Score 0-1 based on how many fields match
    """
    matches = 0
    total = 0
    
    for key, expected_value in expected_state.items():
        if expected_value is not None:
            total += 1
            actual_value = output_state.get(key)
            
            if actual_value == expected_value:
                matches += 1
            elif isinstance(expected_value, str) and isinstance(actual_value, str):
                # Fuzzy match for strings (case-insensitive, partial match)
                expected_lower = expected_value.lower()
                actual_lower = actual_value.lower()
                if expected_lower in actual_lower or actual_lower in expected_lower:
                    matches += 0.8  # Partial credit for fuzzy match
            elif isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                # Numeric match with tolerance
                if abs(expected_value - actual_value) < 0.01:
                    matches += 1
    
    return matches / total if total > 0 else 0.0


def evaluate_response_quality(output: str, context: dict) -> float:
    """
    Evaluates response quality using simple heuristics.
    For production, use LLM-as-a-Judge instead.
    
    Args:
        output: The agent's response
        context: Context about what should be in the response
    
    Returns:
        Score 0-1
    """
    score = 1.0
    output_lower = output.lower()
    
    # Check length (not too short, not too long)
    if len(output) < 50:
        score -= 0.2  # Too short
    elif len(output) > 1000:
        score -= 0.1  # Too long
    
    # Check for helpful phrases
    helpful_phrases = ["help", "assist", "support", "advice", "suggest"]
    if any(phrase in output_lower for phrase in helpful_phrases):
        score += 0.1
    
    # Check for professional tone (no excessive emojis, no slang)
    emoji_count = len(re.findall(r'[😀-🙏🌀-🗿]', output))
    if emoji_count > 3:
        score -= 0.1
    
    return max(0.0, min(1.0, score))


def evaluate_routing_accuracy(actual_routing: list, expected_routing: list) -> float:
    """
    Evaluates if agents were called in the correct order.
    
    Args:
        actual_routing: List of agent names in order they were called
        expected_routing: List of expected agent names in order
    
    Returns:
        Score 0-1 based on routing sequence match
    """
    if not expected_routing:
        return 1.0  # No expected routing means any routing is fine
    
    # Check if expected sequence appears in actual sequence
    expected_str = " -> ".join(expected_routing)
    actual_str = " -> ".join(actual_routing)
    
    if expected_str in actual_str:
        return 1.0
    
    # Partial credit for matching subsequences
    matches = 0
    for i, expected_agent in enumerate(expected_routing):
        if i < len(actual_routing) and actual_routing[i] == expected_agent:
            matches += 1
    
    return matches / len(expected_routing) if expected_routing else 0.0


def evaluate_onboarding_efficiency(num_exchanges: int, target_exchanges: int = 7) -> float:
    """
    Evaluates if onboarding was completed efficiently.
    
    Args:
        num_exchanges: Number of message exchanges to complete onboarding
        target_exchanges: Target number of exchanges (default 7)
    
    Returns:
        Score 0-1 (1 = at or below target, decreases as exchanges increase)
    """
    if num_exchanges <= target_exchanges:
        return 1.0
    
    # Penalize for going over target
    excess = num_exchanges - target_exchanges
    penalty = min(0.5, excess * 0.1)  # Max 0.5 penalty
    
    return max(0.0, 1.0 - penalty)

