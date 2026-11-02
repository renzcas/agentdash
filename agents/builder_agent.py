PILLAR = {
    "name": "Construction",
    "agent": "Builder",
    "action": "Build",
    "purpose": "Turn validated ideas into maintainable work.",
}


class BuilderAgent:
    @staticmethod
    def process(data: str) -> dict[str, str]:
        focus = data.strip() or "the requested outcome"
        return {
            "agent": "Builder",
            "status": "Complete",
            "next_step": f"Define one measurable outcome for {focus}, then implement and test the smallest change.",
        }
