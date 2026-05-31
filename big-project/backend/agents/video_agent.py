"""
AI创作工坊 - Video Generation Agent

Handles AI-powered video content creation:
- Script generation from topics/keywords
- Scene planning and storyboarding
- Audio/narration generation
- Video assembly pipeline

Inspired by MoneyPrinterTurbo's approach to automated video creation.
"""

import asyncio
import uuid
from typing import Any

from observability.logger import get_logger
from inference.llm_client import LLMClient

logger = get_logger(__name__)


class VideoAgent:
    """
    Agent for AI video generation workflows.

    Workflow:
    1. Research topic (calls research agent via orchestrator)
    2. Generate script with LLM
    3. Plan scenes (visual + narration segments)
    4. Generate assets (images, audio)
    5. Assemble final video

    Each step updates the GraphState so the orchestrator can track progress.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.name = "video_agent"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Main entry point called by the orchestrator.

        Reads from state:
            - input_data.topic: Video topic
            - input_data.style: Video style (educational, entertainment, etc.)
            - input_data.duration: Target duration in seconds
            - research_result: Background research (if available)

        Writes to state:
            - video_result: Generated video metadata and assets
        """
        task_id = state.get("task_id", "unknown")
        input_data = state.get("input_data", {})
        topic = input_data.get("topic", "AI Technology")
        style = input_data.get("style", "educational")
        duration = input_data.get("duration", 60)
        research = state.get("research_result", {})

        logger.info(f"Starting video generation for topic: {topic}", extra={"task_id": task_id})

        # Step 1: Generate script
        script = await self._generate_script(topic, style, duration, research)

        # Step 2: Plan scenes
        scenes = await self._plan_scenes(script, duration)

        # Step 3: Generate production notes
        production = await self._generate_production_notes(scenes, style)

        result = {
            "video_result": {
                "task_id": task_id,
                "topic": topic,
                "style": style,
                "target_duration": duration,
                "script": script,
                "scenes": scenes,
                "production_notes": production,
                "status": "generated",
                "estimated_cost": self._estimate_cost(script, scenes),
            }
        }

        logger.info(f"Video generation complete: {len(scenes)} scenes", extra={"task_id": task_id})
        return result

    async def _generate_script(
        self, topic: str, style: str, duration: int, research: dict
    ) -> dict[str, Any]:
        """Generate a video script using the LLM."""
        research_context = ""
        if research:
            key_findings = research.get("key_findings", [])
            if key_findings:
                research_context = f"\nBackground research findings:\n" + "\n".join(
                    f"- {f}" for f in key_findings[:5]
                )

        prompt = f"""You are a professional video scriptwriter. Generate a script for a {duration}-second {style} video about "{topic}".

{research_context}

Output a JSON object with:
- "title": Catchy video title
- "hook": Opening hook (first 5 seconds)
- "sections": Array of sections, each with:
  - "heading": Section title
  - "narration": Narration text (conversational, engaging)
  - "visual_description": What should appear on screen
  - "duration_seconds": How long this section lasts
- "cta": Call to action at the end
- "tags": Array of relevant tags for SEO

Total narration should fit within {duration} seconds (~150 words per 60 seconds).
Make it engaging, informative, and suitable for social media."""

        response = await self.llm.generate(
            prompt=prompt,
            system="You are a professional video scriptwriter. Always respond with valid JSON.",
            temperature=0.7,
            max_tokens=2000,
        )

        # Parse JSON response (handle potential formatting issues)
        import json
        try:
            script = json.loads(response.content)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                script = json.loads(content[start:end])
            else:
                script = {
                    "title": f"Video about {topic}",
                    "hook": f"Did you know about {topic}?",
                    "sections": [],
                    "cta": "Like and subscribe!",
                    "tags": [topic],
                }

        return script

    async def _plan_scenes(self, script: dict, target_duration: int) -> list[dict]:
        """
        Plan individual scenes from the script.
        Each scene maps to a visual + narration segment.
        """
        scenes = []
        current_time = 0.0

        # Hook scene
        if "hook" in script:
            scenes.append({
                "scene_id": str(uuid.uuid4())[:8],
                "type": "hook",
                "start_time": current_time,
                "duration": 5.0,
                "narration": script["hook"],
                "visual_type": "text_overlay",
                "visual_params": {"animation": "zoom_in", "bg_color": "#1a1a2e"},
            })
            current_time += 5.0

        # Content scenes
        sections = script.get("sections", [])
        time_per_section = (target_duration - 10.0) / max(len(sections), 1)

        for i, section in enumerate(sections):
            duration = section.get("duration_seconds", time_per_section)
            scenes.append({
                "scene_id": str(uuid.uuid4())[:8],
                "type": "content",
                "section_index": i,
                "start_time": current_time,
                "duration": duration,
                "heading": section.get("heading", ""),
                "narration": section.get("narration", ""),
                "visual_description": section.get("visual_description", ""),
                "visual_type": "image_with_text",
                "visual_params": {
                    "transition": "fade" if i > 0 else "none",
                    "text_position": "bottom",
                },
            })
            current_time += duration

        # CTA scene
        scenes.append({
            "scene_id": str(uuid.uuid4())[:8],
            "type": "cta",
            "start_time": current_time,
            "duration": 5.0,
            "narration": script.get("cta", "Thanks for watching!"),
            "visual_type": "animated_text",
            "visual_params": {"animation": "bounce", "bg_color": "#16213e"},
        })

        return scenes

    async def _generate_production_notes(self, scenes: list, style: str) -> dict:
        """Generate production guidance for video assembly."""
        return {
            "total_scenes": len(scenes),
            "total_duration": sum(s.get("duration", 0) for s in scenes),
            "recommended_resolution": "1080x1920" if style == "short" else "1920x1080",
            "fps": 30,
            "audio": {
                "narration_voice": "neutral",
                "background_music": "lo-fi" if style == "educational" else "upbeat",
                "music_volume": 0.15,
            },
            "visual_style": {
                "color_scheme": "dark" if style == "tech" else "vibrant",
                "font": "Inter",
                "transitions": "smooth",
            },
        }

    def _estimate_cost(self, script: dict, scenes: list) -> dict:
        """Estimate the token cost of video generation."""
        word_count = len(str(script).split())
        return {
            "llm_tokens_estimate": word_count * 3,  # rough estimate
            "generation_time_estimate_seconds": len(scenes) * 2,
        }
