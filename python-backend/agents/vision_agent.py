"""
Vision Agent - Analyzes business photos using Claude's vision capabilities.

This agent:
- Processes images of storefronts, inventory, workspace
- Extracts visual signals (cleanliness, organization, stock levels)
- Provides actionable insights and coaching tips
- Returns structured analysis
"""

import os
import base64
from typing import Dict, List
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

from state import BusinessPartnerState, PhotoInsight


class VisionAgent:
    """Agent specialized in analyzing business photos."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=1024,
        )

        # Initialize Langfuse for prompt management
        self.langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
        )

        # Prompt caching
        self.system_prompt = None
        self.prompt_cache_time = None
        self.prompt_ttl = 60  # seconds

    def get_system_prompt(self) -> str:
        """
        Fetch system prompt from Langfuse with caching.
        Falls back to default if Langfuse fetch fails.
        """
        import time

        now = time.time()

        # Return cached prompt if valid
        if self.system_prompt and self.prompt_cache_time and (now - self.prompt_cache_time < self.prompt_ttl):
            print(f"[LANGFUSE-VISION] Using cached prompt (age: {int(now - self.prompt_cache_time)}s)")
            return self.system_prompt

        # Try to fetch from Langfuse
        try:
            prompt_name = os.getenv("LANGFUSE_VISION_PROMPT_NAME", "vision-agent-system")
            print(f"[LANGFUSE-VISION] Fetching prompt: {prompt_name}")

            prompt_obj = self.langfuse.get_prompt(prompt_name)

            if prompt_obj and hasattr(prompt_obj, "prompt"):
                self.system_prompt = prompt_obj.prompt
                self.prompt_cache_time = now
                print(f"[LANGFUSE-VISION] ✓ Prompt fetched successfully (v{prompt_obj.version})")
                return self.system_prompt
            else:
                print(f"[LANGFUSE-VISION] ✗ Prompt object missing 'prompt' property")

        except Exception as e:
            print(f"[LANGFUSE-VISION] ✗ Error fetching prompt: {e}")

        # Fallback to default prompt
        print("[LANGFUSE-VISION] → Using fallback prompt")
        return self._get_fallback_prompt()

    def _get_fallback_prompt(self) -> str:
        """Fallback system prompt if Langfuse is unavailable."""
        return """You are a business consultant analyzing photos of small businesses.

Your task: Analyze the photo and provide:
1. Cleanliness score (0-10): How clean and well-maintained is the space?
2. Organization score (0-10): How organized is the inventory/workspace?
3. Stock level: "low", "medium", or "high" - how well-stocked does it appear?
4. 2-3 specific observations about what you see
5. 1-2 actionable coaching tips to improve the business

Be specific, practical, and encouraging. Focus on visual signals that indicate business health."""

    @observe(name="vision-agent-analyze")
    def analyze_photo(self, photo_b64: str, photo_index: int, business_context: Dict) -> PhotoInsight:
        """
        Analyze a single business photo and extract insights.

        Args:
            photo_b64: Base64 encoded image
            photo_index: Index of the photo in the list
            business_context: Dictionary with business_type, location, etc.

        Returns:
            PhotoInsight with structured analysis
        """

        # Fetch system prompt from Langfuse or use fallback
        system_prompt = self.get_system_prompt()

        # Determine media type from base64 prefix if present, default to jpeg
        media_type = "image/jpeg"
        if photo_b64.startswith("data:"):
            if "image/png" in photo_b64:
                media_type = "image/png"
            elif "image/webp" in photo_b64:
                media_type = "image/webp"
            # Strip the data:image/xxx;base64, prefix
            photo_b64 = photo_b64.split(",", 1)[1]

        context_str = f"Business type: {business_context.get('business_type', 'unknown')}, Location: {business_context.get('location', 'unknown')}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=[
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": photo_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"Analyze this business photo. Context: {context_str}\n\nProvide your analysis in this exact format:\nCleanliness: [score]/10\nOrganization: [score]/10\nStock Level: [low/medium/high]\nObservations:\n- [observation 1]\n- [observation 2]\nCoaching Tips:\n- [tip 1]\n- [tip 2]",
                    },
                ]
            ),
        ]

        # Add Langfuse context
        langfuse_context.update_current_observation(
            input={"photo_index": photo_index, "business_context": business_context},
            metadata={"agent": "vision", "model": "claude-sonnet-4-20250514"},
        )

        response = self.llm.invoke(messages)
        analysis_text = response.content

        # Parse the response
        insight = self._parse_analysis(analysis_text, photo_index)

        # Update Langfuse with output
        langfuse_context.update_current_observation(output=insight)

        return insight

    def _parse_analysis(self, analysis_text: str, photo_index: int) -> PhotoInsight:
        """Parse the LLM response into structured PhotoInsight."""

        lines = analysis_text.strip().split("\n")
        cleanliness_score = 7.5
        organization_score = 7.5
        stock_level = "medium"
        observations = []
        coaching_tips = []

        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Parse scores
            if line.lower().startswith("cleanliness:"):
                try:
                    score_str = line.split(":")[1].strip().split("/")[0]
                    cleanliness_score = float(score_str)
                except:
                    pass

            elif line.lower().startswith("organization:"):
                try:
                    score_str = line.split(":")[1].strip().split("/")[0]
                    organization_score = float(score_str)
                except:
                    pass

            elif line.lower().startswith("stock level:"):
                level = line.split(":")[1].strip().lower()
                if level in ["low", "medium", "high"]:
                    stock_level = level

            # Track sections
            elif line.lower().startswith("observations:"):
                current_section = "observations"
            elif line.lower().startswith("coaching tips:"):
                current_section = "coaching"

            # Collect bullet points
            elif line.startswith("-") or line.startswith("•"):
                text = line[1:].strip()
                if current_section == "observations":
                    observations.append(text)
                elif current_section == "coaching":
                    coaching_tips.append(text)

        return PhotoInsight(
            photo_index=photo_index,
            cleanliness_score=cleanliness_score,
            organization_score=organization_score,
            stock_level=stock_level,
            insights=observations if observations else ["Photo analyzed successfully"],
            coaching_tips=coaching_tips if coaching_tips else ["Continue maintaining your business well"],
        )

    @observe(name="vision-agent-process")
    def process(self, state: BusinessPartnerState) -> Dict:
        """
        Main entry point for the Vision Agent.

        Processes all photos in the state and returns updated state with insights.
        """

        # Extract business context
        business_context = {
            "business_type": state.get("business_type"),
            "location": state.get("location"),
            "business_name": state.get("business_name"),
        }

        photo_insights = []

        # Analyze each photo
        for idx, photo_b64 in enumerate(state.get("photos", [])):
            if photo_b64:  # Skip empty entries
                insight = self.analyze_photo(photo_b64, idx, business_context)
                photo_insights.append(insight)

        # Update state
        return {
            "photo_insights": photo_insights,
            "next_agent": None,  # Vision agent doesn't trigger other agents
        }


# Singleton instance (instantiated after env is loaded)
vision_agent = None

def initialize_vision_agent():
    global vision_agent
    if vision_agent is None:
        vision_agent = VisionAgent()
