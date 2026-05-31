"""
AI创作工坊 - Research Agent

Retrieval-Augmented Generation (RAG) powered research agent:
- Queries the knowledge base for relevant information
- Synthesizes findings into structured research reports
- Provides citations and source tracking
- Used by other agents (video, comment) for background research
"""

import json
from typing import Any

from observability.logger import get_logger
from inference.llm_client import LLMClient

logger = get_logger(__name__)


class ResearchAgent:
    """
    Agent for RAG-powered research and information retrieval.

    Uses the RAG pipeline (retriever + reranker + generator) to:
    1. Search the knowledge base for relevant documents
    2. Extract key findings with citations
    3. Synthesize information into structured reports
    4. Identify knowledge gaps and suggest further research
    """

    def __init__(self, llm_client: LLMClient, retriever=None):
        self.llm = llm_client
        self.retriever = retriever
        self.name = "research_agent"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Main entry point called by the orchestrator.

        Reads from state:
            - input_data.query: Research query
            - input_data.max_results: Max documents to retrieve
            - input_data.depth: "quick" | "standard" | "deep"

        Writes to state:
            - research_result: Structured research findings
        """
        task_id = state.get("task_id", "unknown")
        input_data = state.get("input_data", {})
        query = input_data.get("query", input_data.get("topic", ""))
        max_results = input_data.get("max_results", 10)
        depth = input_data.get("depth", "standard")

        logger.info(
            f"Research agent: querying '{query}' (depth={depth})",
            extra={"task_id": task_id},
        )

        # Step 1: Retrieve relevant documents
        documents = await self._retrieve_documents(query, max_results)

        # Step 2: Extract key findings
        findings = await self._extract_findings(query, documents, depth)

        # Step 3: Synthesize into report
        report = await self._synthesize_report(query, findings, documents)

        result = {
            "research_result": {
                "query": query,
                "documents_found": len(documents),
                "documents": [
                    {"content": d.get("content", "")[:500], "source": d.get("source", "")}
                    for d in documents
                ],
                "key_findings": findings,
                "report": report,
                "confidence_score": self._calculate_confidence(documents, findings),
            }
        }

        logger.info(
            f"Research complete: {len(findings)} findings from {len(documents)} documents",
            extra={"task_id": task_id},
        )
        return result

    async def _retrieve_documents(self, query: str, max_results: int) -> list[dict]:
        """
        Retrieve relevant documents from the vector store.
        Falls back to empty list if retriever is not available.
        """
        if self.retriever is None:
            logger.warning("No retriever configured — returning empty results")
            return []

        try:
            results = await self.retriever.retrieve(query, top_k=max_results)
            return results
        except Exception as e:
            logger.error(f"Retrieval failed: {e}", exc_info=True)
            return []

    async def _extract_findings(
        self, query: str, documents: list[dict], depth: str
    ) -> list[str]:
        """
        Extract key findings from retrieved documents using the LLM.
        """
        if not documents:
            return ["No relevant documents found in the knowledge base."]

        doc_text = "\n\n".join(
            f"[Document {i+1}] {d.get('content', '')[:1000]}"
            for i, d in enumerate(documents[:10])
        )

        max_findings = {"quick": 3, "standard": 5, "deep": 10}.get(depth, 5)

        prompt = f"""Extract the {max_findings} most important findings from these documents relevant to the query: "{query}"

Documents:
{doc_text}

For each finding:
- Be specific and factual
- Include which document(s) support it
- Note any contradictions between documents
- Assess confidence level (high/medium/low)

Return a JSON array of strings, each being a key finding.
Example: ["Finding 1...", "Finding 2...", ...]"""

        response = await self.llm.generate(
            prompt=prompt,
            system="You are a research analyst. Extract factual findings with source attribution. Always respond with valid JSON.",
            temperature=0.2,
            max_tokens=2000,
        )

        try:
            findings = json.loads(response.content)
            if not isinstance(findings, list):
                findings = [str(findings)]
        except json.JSONDecodeError:
            # Fallback: split by newlines
            findings = [
                line.strip("- ").strip()
                for line in response.content.split("\n")
                if line.strip() and not line.strip().startswith("[")
            ][:max_findings]

        return findings

    async def _synthesize_report(
        self, query: str, findings: list[str], documents: list[dict]
    ) -> dict:
        """
        Synthesize findings into a structured research report.
        """
        findings_text = "\n".join(f"- {f}" for f in findings)

        prompt = f"""Based on these research findings, create a structured report for the query: "{query}"

Key Findings:
{findings_text}

Create a report with:
1. "summary": 2-3 sentence overview
2. "details": Detailed analysis paragraph
3. "key_points": Top 3-5 bullet points
4. "sources": List of source references
5. "gaps": What information is missing
6. "recommendations": Suggested next steps

Respond as JSON."""

        response = await self.llm.generate(
            prompt=prompt,
            system="You are a research report writer. Be concise and factual. Always respond with valid JSON.",
            temperature=0.3,
            max_tokens=1500,
        )

        try:
            report = json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                report = json.loads(content[start:end])
            else:
                report = {
                    "summary": f"Research on: {query}",
                    "details": response.content[:500],
                    "key_points": findings[:3],
                }

        return report

    def _calculate_confidence(self, documents: list, findings: list) -> float:
        """
        Calculate confidence score based on document availability and consistency.
        """
        if not documents:
            return 0.0
        if not findings:
            return 0.1

        # More documents and findings = higher confidence (up to a point)
        doc_score = min(len(documents) / 5.0, 1.0)
        finding_score = min(len(findings) / 3.0, 1.0)

        return round((doc_score * 0.6 + finding_score * 0.4), 2)
