PILLAR = {
    "name": "Compression",
    "agent": "Compression",
    "action": "Simplify",
    "purpose": "Reduce complexity into useful summaries.",
}


class CompressionAgent:
    @staticmethod
    def process(data: str) -> dict[str, str]:
        summary = " ".join(data.split())
        if len(summary) > 160:
            summary = summary[:157].rstrip() + "..."
        return {
            "agent": "Compression",
            "status": "Complete",
            "summary": summary or "No investigation question was provided.",
        }
