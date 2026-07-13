"""Non-executing L0-L5 governance taxonomy."""

GOVERNANCE_LEVELS = {
    "L0": "read-only discovery and explanation",
    "L1": "existing low-risk temp/cache/log cleanup boundary",
    "L2": "future reversible quarantine proposal",
    "L3": "official uninstaller identification proposal",
    "L4": "high-risk registry/service/task/browser governance proposal",
    "L5": "forbidden automatic action",
}


def classify_governance_level(action: str) -> dict:
    text = str(action).lower()
    if "official_uninstaller" in text and any(x in text for x in ("identify", "inspect", "proposal")): level = "L3"
    elif any(x in text for x in ("silent", "automatic", "auto_", "delete", "uninstall", "disable")): level = "L5"
    elif any(x in text for x in ("registry", "service", "scheduled_task", "browser_change")): level = "L4"
    elif "quarantine" in text: level = "L2"
    elif any(x in text for x in ("temp", "cache", "log")): level = "L1"
    else: level = "L0"
    return {"level": level, "description": GOVERNANCE_LEVELS[level], "proposal_only": level in {"L2", "L3", "L4"}, "blocked": level == "L5", "execution_authorized": False, "execution_gating_eligible": False}
