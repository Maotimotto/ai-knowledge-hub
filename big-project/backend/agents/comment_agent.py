"""
AI创作工坊 - Comment Analysis Agent

AI-powered comment management:
- Sentiment analysis (positive/negative/neutral)
- Spam and toxicity detection
- Smart reply generation
- Trend analysis across comments
- Priority flagging for moderation
"""

import json
from typing import Any

from observability.logger import get_logger
from inference.llm_client import LLMClient

logger = get_logger(__name__)


class CommentAgent:
    """
    Agent for AI-powered comment analysis and response generation.

    Capabilities:
    1. Sentiment analysis with confidence scores
    2. Toxicity and spam detection
    3. Context-aware reply generation
    4. Comment summarization for large volumes
    5. Priority flagging for human moderation
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.name = "comment_agent"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Main entry point called by the orchestrator.

        Reads from state:
            - input_data.comments: List of comments to analyze
            - input_data.video_id: Associated video ID
            - input_data.action: "analyze" | "respond" | "summarize"

        Writes to state:
            - comment_result: Analysis results and generated responses
        """
        task_id = state.get("task_id", "unknown")
        input_data = state.get("input_data", {})
        comments = input_data.get("comments", [])
        action = input_data.get("action", "analyze")

        logger.info(
            f"Comment agent: {action} for {len(comments)} comments",
            extra={"task_id": task_id},
        )

        if action == "analyze":
            result = await self._analyze_comments(comments, task_id)
        elif action == "respond":
            video_context = input_data.get("video_context", "")
            result = await self._generate_responses(comments, video_context, task_id)
        elif action == "summarize":
            result = await self._summarize_comments(comments, task_id)
        else:
            result = {"error": f"Unknown action: {action}"}

        return {"comment_result": result}

    async def _analyze_comments(self, comments: list[dict], task_id: str) -> dict:
        """
        Analyze comments for sentiment, toxicity, and spam.
        Uses structured LLM output for consistent results.
        """
        if not comments:
            return {"analyses": [], "summary": {"total": 0}}

        comments_text = "\n".join(
            f"[{i+1}] {c.get('author', 'Anonymous')}: {c.get('text', '')}"
            for i, c in enumerate(comments[:50])  # Limit to 50 per batch
        )

        prompt = f"""Analyze these video comments. For each comment, provide:
1. sentiment: "positive", "negative", or "neutral"
2. sentiment_score: float from -1.0 to 1.0
3. is_toxic: boolean
4. is_spam: boolean
5. topics: list of discussed topics
6. needs_moderation: boolean (true if toxic, spam, or offensive)
7. suggested_action: "approve", "flag", "delete", or "reply"

Comments:
{comments_text}

Respond with a JSON object: {{"analyses": [{{...}}, ...], "summary": {{"total": N, "positive": N, "negative": N, "neutral": N, "toxic": N, "spam": N}}}}"""

        response = await self.llm.generate(
            prompt=prompt,
            system="You are a content moderation AI. Always respond with valid JSON.",
            temperature=0.1,  # Low temperature for consistent analysis
            max_tokens=3000,
        )

        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                result = json.loads(content[start:end])
            else:
                result = {
                    "analyses": [
                        {"sentiment": "neutral", "needs_moderation": False}
                        for _ in comments
                    ],
                    "summary": {"total": len(comments)},
                }

        # Track token usage
        result["token_usage"] = response.usage
        return result

    async def _generate_responses(
        self, comments: list[dict], video_context: str, task_id: str
    ) -> dict:
        """
        Generate AI-powered responses to comments.
        Responses are context-aware and match the tone of the original comment.
        """
        responses = []

        for comment in comments[:20]:  # Process up to 20 at a time
            comment_text = comment.get("text", "")
            author = comment.get("author", "viewer")

            prompt = f"""Generate a helpful, engaging reply to this video comment.

Video context: {video_context[:500] if video_context else "N/A"}

Comment from {author}: "{comment_text}"

Guidelines:
- Be friendly and authentic
- Address the commenter's specific point
- Keep it concise (1-3 sentences)
- If it's a question, provide a helpful answer
- If it's positive feedback, express gratitude
- If it's criticism, acknowledge it constructively
- Never be defensive or dismissive

Reply:"""

            response = await self.llm.generate(
                prompt=prompt,
                system="You are a friendly, professional content creator responding to your audience.",
                temperature=0.7,
                max_tokens=200,
            )

            responses.append({
                "original_comment": comment,
                "suggested_reply": response.content.strip(),
                "tone": "auto",
                "needs_review": True,  # Always flag for human review
            })

        return {
            "responses": responses,
            "total_generated": len(responses),
        }

    async def _summarize_comments(self, comments: list[dict], task_id: str) -> dict:
        """
        Generate a summary of large comment volumes.
        Useful for understanding audience reception at a glance.
        """
        comments_text = "\n".join(
            f"- {c.get('text', '')}" for c in comments[:100]
        )

        prompt = f"""Summarize these {len(comments)} video comments into actionable insights:

{comments_text}

Provide:
1. "overall_sentiment": General audience feeling
2. "top_topics": Most discussed topics (list)
3. "common_questions": Frequently asked questions (list)
4. "positive_highlights": What viewers loved (list)
5. "improvement_suggestions": Constructive feedback (list)
6. "action_items": Specific things the creator should do (list)

Respond as JSON."""

        response = await self.llm.generate(
            prompt=prompt,
            system="You are an audience analytics expert. Respond with valid JSON.",
            temperature=0.3,
            max_tokens=1500,
        )

        try:
            summary = json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                summary = json.loads(content[start:end])
            else:
                summary = {"overall_sentiment": "mixed", "top_topics": []}

        return {"summary": summary, "comments_analyzed": len(comments)}
