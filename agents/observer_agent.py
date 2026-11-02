import re


PILLAR = {
    "name": "Survival",
    "agent": "Observer",
    "action": "Observe",
    "purpose": "Notice signals, events, and changes.",
}


class ObserverAgent:
    @staticmethod
    def process(data: str) -> dict[str, str]:
        normalized = " ".join(data.split())
        words = re.findall(r"\b[\w'-]+\b", normalized)
        stop_words = {
            "a", "an", "and", "are", "as", "at", "be", "by", "can", "do",
            "for", "from", "how", "i", "in", "is", "it", "of", "on", "or",
            "the", "to", "we", "what", "when", "where", "which", "who",
            "why", "will", "with",
        }
        signals = [word for word in words if word.casefold() not in stop_words]
        sentence_count = len([part for part in re.split(r"[.!?]+", normalized) if part.strip()])

        return {
            "agent": "Observer",
            "status": "Complete",
            "signal": normalized,
            "observation": f"Observed {len(words)} words across {sentence_count} sentence(s).",
            "signals": ", ".join(signals) if signals else "No distinctive terms detected.",
        }
