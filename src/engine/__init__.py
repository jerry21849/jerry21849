"""
遊戲引擎模組
Game Engine Module

包含：
- types: 類型定義
- constants: 常量與平衡設定
- balance: 數值平衡系統
- scoring: 結局評分系統
- butterfly: 蝴蝶效應引擎
- producer: 公信系統（製作人視角）
"""
from .types import (
    EndingGrade,
    BondDimension,
    EmotionAxis,
    ProducerDecisionType,
    ButterflyScope,
    BondStats,
    EmotionStats,
    CharacterStats,
    ButterflyEffect,
    ProducerDecision,
    EndingCondition,
    GameEvent,
)

from .constants import (
    AFFECTION_RANGE,
    BOND_RANGE,
    POPULARITY_RANGE,
    EMOTION_RANGE,
    STRESS_RANGE,
    ENDING_THRESHOLDS,
    ENDING_SCORE_WEIGHTS,
    CHOICE_EFFECTS,
)

from .balance import BalanceEngine
from .scoring import ScoringEngine
from .butterfly import ButterflyEngine
from .producer import ProducerSystem

__all__ = [
    # Types
    "EndingGrade",
    "BondDimension",
    "EmotionAxis",
    "ProducerDecisionType",
    "ButterflyScope",
    "BondStats",
    "EmotionStats",
    "CharacterStats",
    "ButterflyEffect",
    "ProducerDecision",
    "EndingCondition",
    "GameEvent",
    
    # Constants
    "AFFECTION_RANGE",
    "BOND_RANGE",
    "POPULARITY_RANGE",
    "EMOTION_RANGE",
    "STRESS_RANGE",
    "ENDING_THRESHOLDS",
    "ENDING_SCORE_WEIGHTS",
    "CHOICE_EFFECTS",
    
    # Engines
    "BalanceEngine",
    "ScoringEngine",
    "ButterflyEngine",
    "ProducerSystem",
]


def create_game_engine():
    """
    創建完整遊戲引擎實例
    
    Returns:
        包含所有系統的字典
    """
    balance = BalanceEngine()
    scoring = ScoringEngine()
    butterfly = ButterflyEngine(balance)
    producer = ProducerSystem(balance)
    
    return {
        "balance": balance,
        "scoring": scoring,
        "butterfly": butterfly,
        "producer": producer,
    }
