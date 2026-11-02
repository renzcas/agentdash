import re


PILLAR = {
    "name": "Strategy",
    "agent": "Strategist",
    "action": "Predict",
    "purpose": "Compare options and anticipate outcomes.",
}


class StrategistAgent:
    @staticmethod
    def process(data: str) -> dict[str, str]:
        question = " ".join(data.split())
        if re.search(r"\b(should|choose|decide|best|plan|strategy)\b", question, re.I):
            focus = "decision"
            approach = "List the viable options, compare them against explicit criteria, and choose a reversible first step."
        elif re.search(r"\b(how|build|create|implement|make)\b", question, re.I):
            focus = "implementation"
            approach = "Break the request into small steps and validate the first step before expanding scope."
        elif re.search(r"\b(why|what|explain|understand)\b", question, re.I):
            focus = "explanation"
            approach = "Separate known facts from assumptions, then identify what evidence would clarify the question."
        else:
            focus = "exploration"
            approach = "Clarify the desired outcome and compare a small number of plausible paths."

        return {
            "agent": "Strategist",
            "status": "Complete",
            "focus": focus,
            "approach": approach,
        }
