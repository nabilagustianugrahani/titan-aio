"""Swarm Intelligence — MiroFish GraphRAG + ReportAgent adapter for Titan AIO.

Conditionally imported — all features degrade gracefully when Zep/OpenAI keys are absent.

Usage:
    from Services.swarm.adapter import swarm
    if swarm.ready:
        result = await swarm.predict_trend("elektronik", "berita terbaru...")
        report = await swarm.report_campaign(campaign_data)
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class SwarmIntelligence:
    """Swarm intelligence: GraphRAG knowledge graphs + ReACT report generation.

    Wraps MiroFish's core capabilities into Titan AIO's service layer.
    """

    def __init__(self) -> None:
        self._llm_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
        self._zep_key = os.environ.get("ZEP_API_KEY")
        self._graph = None
        self._report = None
        self._ontology = None
        self._init()

    def _init(self) -> None:
        if self._zep_key:
            try:
                from Services.swarm.app.services.graph_builder import GraphBuilderService
                from Services.swarm.app.services.ontology_generator import OntologyGenerator

                self._graph = GraphBuilderService(api_key=self._zep_key)
                self._ontology = OntologyGenerator()
                logger.info("Swarm: GraphRAG ready (Zep)")
            except Exception as e:
                logger.debug("Swarm: GraphRAG unavailable: %s", e)

        if self._llm_key:
            try:
                from Services.swarm.app.services.report_agent import ReportAgentService
                from Services.swarm.app.services.text_processor import TextProcessor

                self._report = ReportAgentService()
                self._text = TextProcessor()
                logger.info("Swarm: ReportAgent + TextProcessor ready")
            except Exception as e:
                logger.debug("Swarm: ReportAgent unavailable: %s", e)

    @property
    def ready(self) -> bool:
        return any([self._graph, self._report])

    @property
    def capabilities(self) -> list[str]:
        caps = []
        if self._graph:
            caps.append("graph_rag")
        if self._report:
            caps.append("report_generation")
        return caps

    # ── GraphRAG ─────────────────────────────────────────────────────

    async def build_knowledge_graph(self, text: str, domain: str = "umum") -> dict[str, Any]:
        """Build a knowledge graph from raw text using Zep GraphRAG.

        Returns task_id for polling, or error dict if Zep unavailable.
        """
        if not self._graph:
            return {"error": "GraphRAG requires ZEP_API_KEY"}

        try:
            ontology = self._ontology.generate_ontology(text, domain) if self._ontology else {}
            task_id = self._graph.build_graph_async(
                text=text,
                ontology=ontology or {"entities": ["product", "brand", "trend"]},
                graph_name=f"titan-{hash(text) % 10000}",
            )
            return {"task_id": task_id, "status": "building"}
        except Exception as e:
            logger.warning("Graph build failed: %s", e)
            return {"error": str(e)}

    async def analyze_market_from_news(self, news_text: str, category: str) -> dict[str, Any]:
        """Extract entities, trends, and insights from news text.

        Uses ontology generator + graph builder pipeline.
        """
        if not self._graph or not self._ontology:
            return await self._llm_fallback(f"Analyze this market news for {category}: {news_text[:2000]}")

        try:
            ontology = self._ontology.generate_ontology(news_text, category)
            graph_id = self._graph.build_graph_async(
                text=news_text,
                ontology=ontology,
                graph_name=f"market-{category}",
            )
            return {"graph_task_id": graph_id, "ontology": ontology, "status": "processing"}
        except Exception as e:
            logger.warning("Market analysis failed: %s", e)
            return await self._llm_fallback(f"Analyze this market news for {category}: {news_text[:2000]}")

    # ── Report Generation ────────────────────────────────────────────

    async def report_campaign(self, campaign_data: dict[str, Any]) -> dict[str, Any]:
        """Generate structured campaign report using ReACT pattern.

        Accepts any dict with product_title, metrics, hooks, etc.
        """
        if not self._report:
            return {
                "report": "Swarm report generation requires OPENAI_API_KEY",
                "sections": [],
            }

        try:
            topic = campaign_data.get("product_title", "Affiliate Campaign")
            requirements = (
                f"Analyze this affiliate campaign: {topic}. "
                f"Include: market positioning, hook effectiveness, "
                f"platform performance, optimization recommendations."
            )
            report = self._report.generate_report(topic=topic, requirements=requirements)
            if isinstance(report, dict):
                return report
            return {"report": str(report), "sections": []}
        except Exception as e:
            logger.warning("Report generation failed: %s", e)
            return {"error": str(e)}

    async def predict_trend(self, category: str, context: str = "") -> dict[str, Any]:
        """Predict trend direction using LLM analysis.

        Uses report agent when available, direct LLM call otherwise.
        """
        if self._report:
            try:
                r = self._report.generate_report(
                    topic=f"Trend prediction: {category}",
                    requirements=f"Context: {context[:1000] if context else 'None'}\n"
                    f"Predict next 30-day trend for {category} category. "
                    f"Include: direction, key drivers, confidence, actionable insights.",
                )
                return r if isinstance(r, dict) else {"prediction": str(r)}
            except Exception:
                pass
        return await self._llm_fallback(
            f"Predict the next 30-day trend for '{category}' e-commerce category. "
            f"Context: {context[:1000] if context else 'No specific context.'}"
            f"\nGive: direction (up/down/stable), key drivers, confidence level.",
        )

    # ── Fallback ─────────────────────────────────────────────────────

    async def _llm_fallback(self, prompt: str) -> dict[str, Any]:
        """Pure LLM analysis when MiroFish services unavailable."""
        if not self._llm_key:
            return {"error": "No LLM key configured (OPENAI_API_KEY)"}
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=self._llm_key,
                base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
            )
            resp = await client.chat.completions.create(
                model=os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            text = resp.choices[0].message.content or ""
            return {
                "analysis": text,
                "model": os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini"),
                "source": "llm_fallback",
            }
        except Exception as e:
            logger.warning("LLM fallback failed: %s", e)
            return {"error": str(e)}


# Singleton
_swarm: SwarmIntelligence | None = None


def get_swarm() -> SwarmIntelligence:
    global _swarm
    if _swarm is None:
        _swarm = SwarmIntelligence()
    return _swarm


# Convenience alias
swarm = get_swarm()
