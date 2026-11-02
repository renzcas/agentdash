PILLAR = {
    "name": "Wisdom",
    "agent": "Wisdom",
    "action": "Understand",
    "purpose": "Question assumptions and interpret evidence.",
}


class WisdomAgent:
    @staticmethod
    def process(data: str) -> dict[str, str]:
        has_question_mark = "?" in data
        return {
            "agent": "Wisdom",
            "status": "Complete",
            "reflection": (
                "The prompt is phrased as a question; clarify its success criteria before acting."
                if has_question_mark
                else "The prompt may omit its intended outcome; clarify success criteria before acting."
            ),
            "evidence_limit": (
                "This deterministic scaffold uses prompt text only; it does not verify claims or consult "
                "external evidence."
            ),
        }
