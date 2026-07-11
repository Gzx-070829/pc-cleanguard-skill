"""Chinese-first behavior taxonomy for explainable PUP evidence."""

from __future__ import annotations

from enum import Enum
from typing import Tuple


class PUPBehaviorCategory(str, Enum):
    """Stable behavior categories; never an execution or removal verdict."""

    FORCED_INSTALLATION = "forced_installation"
    DIFFICULT_UNINSTALL = "difficult_uninstall"
    BROWSER_HIJACKING = "browser_hijacking"
    AD_POPUP = "ad_popup"
    MALICIOUS_COLLECTION = "malicious_collection"
    MALICIOUS_UNINSTALL = "malicious_uninstall"
    MALICIOUS_BUNDLING = "malicious_bundling"
    OTHER_USER_RIGHTS_VIOLATION = "other_user_rights_violation"


_TAXONOMY = {
    PUPBehaviorCategory.FORCED_INSTALLATION: (
        "强制安装",
        "在缺少清晰、独立且可撤回同意的情况下推动或完成安装。",
    ),
    PUPBehaviorCategory.DIFFICULT_UNINSTALL: (
        "难以卸载",
        "卸载入口缺失、误导、反复恢复或留下影响用户选择的组件。",
    ),
    PUPBehaviorCategory.BROWSER_HIJACKING: (
        "浏览器劫持",
        "未经充分同意修改浏览器主页、搜索、代理、扩展或相关设置。",
    ),
    PUPBehaviorCategory.AD_POPUP: (
        "广告弹窗",
        "持续展示干扰性广告、弹窗或诱导交互，且缺少清晰关闭方式。",
    ),
    PUPBehaviorCategory.MALICIOUS_COLLECTION: (
        "恶意收集",
        "超出功能必要范围收集数据，或缺少透明目的、范围和同意。",
    ),
    PUPBehaviorCategory.MALICIOUS_UNINSTALL: (
        "恶意卸载",
        "未经授权移除、破坏或阻碍其他软件及其用户选择。",
    ),
    PUPBehaviorCategory.MALICIOUS_BUNDLING: (
        "恶意捆绑",
        "以模糊默认项、误导按钮或隐藏披露捆绑额外软件。",
    ),
    PUPBehaviorCategory.OTHER_USER_RIGHTS_VIOLATION: (
        "其他侵害用户权益行为",
        "其他有证据表明损害知情、同意、选择、隐私或恢复权利的行为。",
    ),
}


def pup_behavior_label_zh(category: PUPBehaviorCategory) -> str:
    if not isinstance(category, PUPBehaviorCategory):
        raise TypeError("category must be a PUPBehaviorCategory")
    return _TAXONOMY[category][0]


def pup_taxonomy_records() -> Tuple[dict, ...]:
    """Return ordered explanation records with hard non-authorization flags."""

    return tuple(
        {
            "category": category,
            "value": category.value,
            "label_zh": _TAXONOMY[category][0],
            "description_zh": _TAXONOMY[category][1],
            "requires_human_review": True,
            "execution_authorized": False,
        }
        for category in PUPBehaviorCategory
    )
