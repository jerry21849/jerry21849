"""
遊戲常量定義
Game Constants & Balance Settings
"""
from typing import Dict, List, Tuple
from .types import EndingGrade, EndingCondition, BondDimension, EmotionAxis

# ==================== 數值範圍常量 ====================

AFFECTION_RANGE = (0, 100)        # 好感度範圍
AFFECTION_DECAY_MIN = 5           # 每週自然衰減最小值
AFFECTION_DECAY_MAX = 10          # 每週自然衰減最大值
AFFECTION_WEEKLY_LOSS_BASE = 7    # 每週基礎衰減

BOND_RANGE = (0, 100)             # 羈絆各維度範圍
POPULARITY_RANGE = (0, 100)       # 人氣值範圍
EMOTION_RANGE = (-50, 50)         # 情緒各軸範圍
STRESS_RANGE = (0, 100)           # 壓力範圍
STRESS_CRISIS_THRESHOLD = 100     # 壓力危機觸發閾值
STRESS_RECOVERY_RATE = 15         # 壓力恢復速率（每週）

# ==================== 蝴蝶效應常量 ====================

BUTTERFLY_MIN_WEIGHT = 0.2        # 最小影響權重
BUTTERFLY_MAX_WEIGHT = 0.4        # 最大影響權重
BUTTERFLY_DEFAULT_WEIGHT = 0.3    # 預設影響權重

# ==================== 製作人系統常量 ====================

PRODUCER_EDITING_RANGE = (-1, 1)  # 剪輯傾向範圍
PRODUCER_POPULARITY_IMPACT = 10   # 剪輯對人氣的最大影響
PRODUCER_AFFECTION_IMPACT = 5     # 剪輯對好感度的影響

# ==================== 評分系統常量 ====================

ENDING_SCORE_WEIGHTS = {
    "affection": 0.25,       # 好感度權重
    "bond": 0.25,            # 羈絆權重
    "emotion": 0.15,         # 情緒狀態權重
    "correct_rate": 0.20,    # 關鍵選擇正確率權重
    "hidden": 0.15,          # 隱藏條件達成權重
}

MAX_HIDDEN_CONDITIONS = 10   # 最大隱藏條件數量

# ==================== 結局評分閾值 ====================

ENDING_THRESHOLDS: Dict[EndingGrade, EndingCondition] = {
    EndingGrade.S_PLUS: EndingCondition(
        grade=EndingGrade.S_PLUS,
        min_affection=95,
        min_bond_total=90,
        min_correct_rate=0.95,
        required_hidden=["route_true_end", "all_bonds_max", "perfect_choices"],
        emotion_requirements={"joy": (40, 50), "courage": (40, 50)},
        description="完美結局：所有條件完美達成，隱藏路線解鎖"
    ),
    EndingGrade.S: EndingCondition(
        grade=EndingGrade.S,
        min_affection=85,
        min_bond_total=80,
        min_correct_rate=0.85,
        required_hidden=["route_true_end"],
        emotion_requirements={"joy": (30, 50)},
        description="極佳結局：主要條件達成，有 minor 遺憾"
    ),
    EndingGrade.A_PLUS: EndingCondition(
        grade=EndingGrade.A_PLUS,
        min_affection=75,
        min_bond_total=70,
        min_correct_rate=0.75,
        required_hidden=[],
        emotion_requirements={"joy": (20, 50)},
        description="很好結局：大部分條件達成"
    ),
    EndingGrade.A: EndingCondition(
        grade=EndingGrade.A,
        min_affection=65,
        min_bond_total=60,
        min_correct_rate=0.65,
        required_hidden=[],
        emotion_requirements={},
        description="好結局：基本條件達成"
    ),
    EndingGrade.B_PLUS: EndingCondition(
        grade=EndingGrade.B_PLUS,
        min_affection=55,
        min_bond_total=50,
        min_correct_rate=0.55,
        required_hidden=[],
        emotion_requirements={},
        description="不錯結局：有明顯缺點但可接受"
    ),
    EndingGrade.B: EndingCondition(
        grade=EndingGrade.B,
        min_affection=45,
        min_bond_total=40,
        min_correct_rate=0.45,
        required_hidden=[],
        emotion_requirements={},
        description="普通結局：平庸的結局"
    ),
    EndingGrade.C_PLUS: EndingCondition(
        grade=EndingGrade.C_PLUS,
        min_affection=35,
        min_bond_total=30,
        min_correct_rate=0.35,
        required_hidden=[],
        emotion_requirements={},
        description="不太好結局：有問題但還能接受"
    ),
    EndingGrade.C: EndingCondition(
        grade=EndingGrade.C,
        min_affection=25,
        min_bond_total=20,
        min_correct_rate=0.25,
        required_hidden=[],
        emotion_requirements={},
        description="不好結局：明顯的問題"
    ),
    EndingGrade.D_PLUS: EndingCondition(
        grade=EndingGrade.D_PLUS,
        min_affection=15,
        min_bond_total=10,
        min_correct_rate=0.15,
        required_hidden=[],
        emotion_requirements={},
        description="差結局：失敗的結局"
    ),
    EndingGrade.D_MINUS: EndingCondition(
        grade=EndingGrade.D_MINUS,
        min_affection=0,
        min_bond_total=0,
        min_correct_rate=0,
        required_hidden=[],
        emotion_requirements={},
        description="最差結局：完全失敗"
    ),
}

# ==================== 計算公式常量 ====================

def get_affection_decay(week: int) -> float:
    """根據週數計算好感度衰減量"""
    # 隨著時間增加，衰減略微增加
    base_decay = AFFECTION_WEEKLY_LOSS_BASE
    time_factor = 1.0 + (week * 0.02)  # 每週增加 2% 衰減
    return min(base_decay * time_factor, AFFECTION_DECAY_MAX)


def get_stress_recovery(stress_level: float) -> float:
    """根據壓力等級計算恢復量"""
    if stress_level >= 80:
        return STRESS_RECOVERY_RATE * 0.5  # 高壓力恢復慢
    elif stress_level >= 60:
        return STRESS_RECOVERY_RATE * 0.75
    return STRESS_RECOVERY_RATE


# ==================== 選擇效果表 ====================

CHOICE_EFFECTS = {
    "positive_small": {
        "affection": 5,
        "bond_warmth": 3,
        "emotion_joy": 5,
        "stress": -3,
    },
    "positive_medium": {
        "affection": 10,
        "bond_warmth": 5,
        "bond_trust": 3,
        "emotion_joy": 8,
        "stress": -5,
    },
    "positive_large": {
        "affection": 15,
        "bond_warmth": 8,
        "bond_trust": 5,
        "bond_spark": 3,
        "emotion_joy": 12,
        "stress": -8,
    },
    "negative_small": {
        "affection": -5,
        "bond_tension": 3,
        "emotion_anxiety": 5,
        "stress": 5,
    },
    "negative_medium": {
        "affection": -10,
        "bond_trust": -5,
        "bond_tension": 5,
        "emotion_anxiety": 8,
        "popularity": -5,
        "stress": 10,
    },
    "negative_large": {
        "affection": -15,
        "bond_trust": -8,
        "bond_tension": 8,
        "emotion_anxiety": 12,
        "popularity": -10,
        "stress": 15,
    },
    "neutral": {
        "affection": 0,
        "emotion_courage": 2,
    },
    "brave": {
        "affection": 3,
        "bond_spark": 5,
        "emotion_courage": 10,
        "popularity": 3,
        "stress": -2,
    },
    "risky": {
        "affection": 8,
        "bond_spark": 10,
        "emotion_courage": 5,
        "emotion_anxiety": 10,
        "stress": 8,
    },
}
