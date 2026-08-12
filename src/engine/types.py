"""
遊戲引擎類型定義
Game Engine Type Definitions
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple
import uuid


class EndingGrade(Enum):
    """結局評分等級"""
    S_PLUS = "S+"      # 完美：所有條件完美達成，隱藏路線解鎖
    S = "S"            # 極佳：主要條件達成，有 minor 遺憾
    A_PLUS = "A+"      # 很好：大部分條件達成
    A = "A"            # 好：基本條件達成
    B_PLUS = "B+"      # 不錯：有明顯缺點但可接受
    B = "B"            # 普通：平庸的結局
    C_PLUS = "C+"      # 不太好：有問題但還能接受
    C = "C"            # 不好：明顯的問題
    D_PLUS = "D+"      # 差：失敗的結局
    D_MINUS = "D-"     # 最差：完全失敗


class BondDimension(Enum):
    """羈絆四維"""
    WARMTH = "warmth"      # 溫暖
    TRUST = "trust"        # 信任
    SPARK = "spark"        # 火花
    TENSION = "tension"    # 拉扯


class EmotionAxis(Enum):
    """情緒四軸"""
    JOY = "joy"           # 喜悅
    LONGING = "longing"   # 思念
    ANXIETY = "anxiety"   # 焦慮
    COURAGE = "courage"   # 勇氣


class ProducerDecisionType(Enum):
    """製作人決策類型"""
    EDITING_TENDENCY = "editing"    # 剪輯傾向
    RULE_CHANGE = "rule"            # 規則變更
    ALLOCATION = "allocation"       # 資源分配
    PUBLICITY = "publicity"         # 宣傳策略


class ButterflyScope(Enum):
    """蝴蝶效應範圍"""
    DIRECT = "direct"      # 直接影響
    INDIRECT = "indirect"  # 間接影響
    HIDDEN = "hidden"      # 隱藏影響


@dataclass
class BondStats:
    """羈絆四維數值"""
    warmth: float = 0.0      # 0-100
    trust: float = 0.0       # 0-100
    spark: float = 0.0       # 0-100
    tension: float = 0.0     # 0-100
    
    def total(self) -> float:
        """計算總羈絆值"""
        return (self.warmth + self.trust + self.spark + self.tension) / 4.0
    
    def get(self, dim: BondDimension) -> float:
        """獲取指定維度的值"""
        return getattr(self, dim.value)
    
    def set(self, dim: BondDimension, value: float):
        """設置指定維度的值"""
        setattr(self, dim.value, max(0, min(100, value)))
    
    def add(self, dim: BondDimension, delta: float):
        """增減指定維度的值"""
        current = self.get(dim)
        self.set(dim, current + delta)


@dataclass
class EmotionStats:
    """情緒四軸數值"""
    joy: float = 0.0         # -50 to +50
    longing: float = 0.0     # -50 to +50
    anxiety: float = 0.0     # -50 to +50
    courage: float = 0.0     # -50 to +50
    
    def get(self, axis: EmotionAxis) -> float:
        """獲取指定軸的值"""
        return getattr(self, axis.value)
    
    def set(self, axis: EmotionAxis, value: float):
        """設置指定軸的值"""
        setattr(self, axis.value, max(-50, min(50, value)))
    
    def add(self, axis: EmotionAxis, delta: float):
        """增減指定軸的值"""
        current = self.get(axis)
        self.set(axis, current + delta)
    
    def average(self) -> float:
        """計算平均情緒值"""
        return (self.joy + self.longing + self.anxiety + self.courage) / 4.0
    
    def is_distressed(self) -> bool:
        """是否處於壓力狀態（負面情緒過多）"""
        negative = self.anxiety + (-self.joy) + (-self.courage)
        return negative > 60


@dataclass
class CharacterStats:
    """角色完整數值"""
    name: str
    character_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # 核心數值
    affection: float = 50.0       # 好感度 0-100
    bond: BondStats = field(default_factory=BondStats)
    popularity: float = 50.0      # 人氣值 0-100
    emotions: EmotionStats = field(default_factory=EmotionStats)
    stress: float = 0.0           # 壓力 0-100
    
    # 追蹤數值
    correct_choices: int = 0      # 正確選擇次數
    total_choices: int = 0        # 總選擇次數
    hidden_conditions: Set[str] = field(default_factory=set)  # 達成的隱藏條件
    
    def correct_rate(self) -> float:
        """計算關鍵選擇正確率"""
        if self.total_choices == 0:
            return 0.0
        return self.correct_choices / self.total_choices
    
    def stress_level(self) -> str:
        """壓力等級"""
        if self.stress >= 80:
            return "critical"
        elif self.stress >= 60:
            return "high"
        elif self.stress >= 40:
            return "moderate"
        elif self.stress >= 20:
            return "low"
        return "normal"


@dataclass
class ButterflyEffect:
    """蝴蝶效應規則"""
    rule_id: str
    source_character: str          # 觸發角色 ID
    target_character: str          # 影響角色 ID
    trigger_event: str             # 觸發事件 ID
    scope: ButterflyScope = ButterflyScope.DIRECT
    weight: float = 0.3            # 影響權重 0.2-0.4
    stat_modifiers: Dict[str, float] = field(default_factory=dict)
    hidden_requirement: Optional[str] = None  # 隱藏條件要求


@dataclass
class ProducerDecision:
    """製作人決策"""
    decision_id: str
    decision_type: ProducerDecisionType
    target_characters: List[str]    # 影響的角色 ID 列表
    effects: Dict[str, float]       # 效果映射
    editing_bias: float = 0.0       # 剪輯傾向 -1 到 +1
    public_perception_shift: float = 0.0  # 公眾印象轉變


@dataclass
class EndingCondition:
    """結局條件"""
    grade: EndingGrade
    min_affection: float = 0.0
    min_bond_total: float = 0.0
    min_correct_rate: float = 0.0
    required_hidden: List[str] = field(default_factory=list)
    emotion_requirements: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    description: str = ""


@dataclass
class GameEvent:
    """遊戲事件"""
    event_id: str
    week: int
    character_id: str
    event_type: str
    choice_id: Optional[str] = None
    effects: Dict[str, float] = field(default_factory=dict)
    is_correct: Optional[bool] = None
    unlocks_hidden: List[str] = field(default_factory=list)
