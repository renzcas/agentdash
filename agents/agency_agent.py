PILLAR = {
    "name": "Agency",
    "agent": "Agency",
    "action": "Act",
    "purpose": "Choose and carry out an approved next step.",
}


class AgencyAgent:
    @staticmethod
    def process(data: str) -> dict[str, str]:
        return {
            "agent": "Agency",
            "status": "Complete",
            "recommendation": "Review the proposed next step and explicitly approve any real-world action.",
            "approval_required": "yes",
        }
