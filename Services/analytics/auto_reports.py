"""Auto-Reports — generate weekly/monthly performance reports automatically."""

from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime
import hashlib


class ReportSection(BaseModel):
    title: str
    content: str
    metrics: dict = {}
    recommendations: list[str] = []


class AutoReport(BaseModel):
    report_id: str = ""
    report_type: str = ""  # weekly/monthly/daily
    period: str = ""
    generated_at: str = ""
    sections: list[ReportSection] = []
    summary: str = ""
    score: int = 0  # 0-100 overall health


class AutoReportGenerator:
    def __init__(self):
        self.reports: list[AutoReport] = []
        self.data: dict[str, list[dict]] = {}

    async def record_data(self, category: str, data: dict):
        if category not in self.data:
            self.data[category] = []
        self.data[category].append({**data, "timestamp": datetime.now().isoformat()})

    async def generate_report(self, report_type: str = "weekly") -> AutoReport:
        rid = hashlib.md5(f"{report_type}:{datetime.now().isoformat()}".encode()).hexdigest()[:10]
        sections = []

        # Revenue Section
        revenue_data = self.data.get("revenue", [])
        total_rev = sum(d.get("revenue", 0) for d in revenue_data[-30:])
        total_spend = sum(d.get("ad_spend", 0) for d in revenue_data[-30:])
        roi = round((total_rev - total_spend) / max(1, total_spend) * 100, 1)
        sections.append(ReportSection(
            title="💰 Revenue Performance",
            content=f"Total Revenue: ${total_rev:.2f}\nTotal Ad Spend: ${total_spend:.2f}\nNet Profit: ${total_rev - total_spend:.2f}\nROI: {roi}%",
            metrics={"revenue": total_rev, "ad_spend": total_spend, "roi": roi},
            recommendations=["Scale winning campaigns"] if roi > 100 else ["Optimize underperforming campaigns"],
        ))

        # Campaign Section
        campaign_data = self.data.get("campaigns", [])
        active = sum(1 for d in campaign_data if d.get("status") == "active")
        completed = sum(1 for d in campaign_data if d.get("status") == "completed")
        sections.append(ReportSection(
            title="📋 Campaign Status",
            content=f"Active: {active}\nCompleted: {completed}\nTotal: {active + completed}",
            metrics={"active": active, "completed": completed},
        ))

        # Content Performance
        content_data = self.data.get("content", [])
        avg_ctr = sum(d.get("ctr", 0) for d in content_data) / max(1, len(content_data))
        sections.append(ReportSection(
            title="📊 Content Performance",
            content=f"Average CTR: {avg_ctr:.2f}%\nTotal Content Pieces: {len(content_data)}",
            metrics={"avg_ctr": avg_ctr, "total_content": len(content_data)},
            recommendations=["Improve hooks for higher CTR"] if avg_ctr < 2 else ["Content performing well"],
        ))

        # Overall Score
        score = 50
        if roi > 50: score += 15
        if roi > 100: score += 10
        if active > 0: score += 10
        if avg_ctr > 2: score += 10
        if avg_ctr > 5: score += 5
        score = min(100, score)

        summary = f"Overall Health: {score}/100. "
        if score >= 80:
            summary += "Excellent performance! Keep scaling."
        elif score >= 60:
            summary += "Good performance. Room for optimization."
        else:
            summary += "Needs attention. Review recommendations."

        period_map = {"daily": "Last 24 hours", "weekly": "Last 7 days", "monthly": "Last 30 days"}
        report = AutoReport(
            report_id=rid, report_type=report_type, period=period_map.get(report_type, "Custom"),
            generated_at=datetime.now().isoformat(), sections=sections, summary=summary, score=score,
        )
        self.reports.append(report)
        return report

    async def get_reports(self, report_type: str = "", limit: int = 10) -> list[AutoReport]:
        result = self.reports
        if report_type:
            result = [r for r in result if r.report_type == report_type]
        return result[-limit:]

    async def get_stats(self) -> dict:
        return {"total_reports": len(self.reports), "data_categories": list(self.data.keys())}
