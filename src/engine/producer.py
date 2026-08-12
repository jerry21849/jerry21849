"""
公信系統（製作人視角）
Producer System

負責：
- 製作人決策管理
- 剪輯傾向影響
- 公眾印象計算
- 規則事件處理
"""
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import uuid

from .types import (
    CharacterStats, ProducerDecision, ProducerDecisionType,
    BondDimension, EmotionAxis
)
from .constants import (
    PRODUCER_EDITING_RANGE, PRODUCER_POPULARITY_IMPACT,
    PRODUCER_AFFECTION_IMPACT
)
from .balance import BalanceEngine


class PublicPerception(Enum):
    """公眾印象傾向"""
    FAVORABLE = "favorable"      # 好感
    NEUTRAL = "neutral"          # 中立
    UNFAVORABLE = "unfavorable"  # 不好感
    CONTROVERSIAL = "controversial"  # 有爭議


@dataclass
class EditingEffect:
    """剪輯效果"""
    character_id: str
    tendency: float              # -1 到 +1（負面到正面剪輯）
    duration: int                # 持續週數
    public_perception: PublicPerception = PublicPerception.NEUTRAL
    popularity_change: float = 0.0
    description: str = ""


@dataclass
class RuleEvent:
    """規則事件"""
    event_id: str
    event_type: str
    affected_characters: List[str]
    effects: Dict[str, float]
    duration: int = 1            # 持續週數
    is_permanent: bool = False
    description: str = ""


@dataclass 
class ProducerState:
    """製作人狀態"""
    editing_tendency: float = 0.0     # 整體剪輯傾向 -1 到 +1
    reputation: float = 50.0          # 製作人聲望 0-100
    decisions_made: int = 0
    active_rules: List[RuleEvent] = field(default_factory=list)
    character_biases: Dict[str, float] = field(default_factory=dict)


class ProducerSystem:
    """製作人系統"""
    
    def __init__(self, balance_engine: BalanceEngine):
        """
        初始化製作人系統
        
        Args:
            balance_engine: 數值平衡引擎
        """
        self.balance_engine = balance_engine
        self.state = ProducerState()
        self._editing_history: List[EditingEffect] = []
        self._decision_history: List[ProducerDecision] = []
    
    # ==================== 剪輯傾向管理 ====================
    
    def set_editing_tendency(self, tendency: float) -> float:
        """
        設置整體剪輯傾向
        
        Args:
            tendency: -1（完全負面）到 +1（完全正面）
            
        Returns:
            實際設定的值
        """
        self.state.editing_tendency = max(
            PRODUCER_EDITING_RANGE[0],
            min(PRODUCER_EDITING_RANGE[1], tendency)
        )
        return self.state.editing_tendency
    
    def apply_character_editing(self, character: CharacterStats,
                               tendency: float, duration: int = 1) -> EditingEffect:
        """
        對特定角色應用剪輯效果
        
        Args:
            character: 角色數據
            tendency: 剪輯傾向 -1 到 +1
            duration: 持續週數
            
        Returns:
            剪輯效果記錄
        """
        # 限制範圍
        tendency = max(-1, min(1, tendency))
        
        # 計算人氣影響
        popularity_change = tendency * PRODUCER_POPULARITY_IMPACT
        self.balance_engine.update_popularity(character, popularity_change)
        
        # 計算好感度影響（間接影響）
        affection_change = tendency * PRODUCER_AFFECTION_IMPACT * 0.5
        self.balance_engine.update_affection(character, affection_change)
        
        # 判斷公眾印象
        if tendency >= 0.5:
            perception = PublicPerception.FAVORABLE
        elif tendency >= 0:
            perception = PublicPerception.NEUTRAL
        elif tendency >= -0.5:
            perception = PublicPerception.UNFAVORABLE
        else:
            perception = PublicPerception.CONTROVERSIAL
        
        # 創建效果記錄
        effect = EditingEffect(
            character_id=character.character_id,
            tendency=tendency,
            duration=duration,
            public_perception=perception,
            popularity_change=popularity_change,
            description=self._generate_editing_description(tendency)
        )
        
        self._editing_history.append(effect)
        
        # 更新角色偏見
        current_bias = self.state.character_biases.get(character.character_id, 0)
        self.state.character_biases[character.character_id] = current_bias + tendency * 0.3
        
        return effect
    
    def _generate_editing_description(self, tendency: float) -> str:
        """生成剪輯描述"""
        if tendency >= 0.7:
            return "正面特寫：強調角色優點，放大正面情緒"
        elif tendency >= 0.3:
            return "輕度正面：稍微突出正面形象"
        elif tendency >= -0.3:
            return "中立剪輯：均衡呈現"
        elif tendency >= -0.7:
            return "輕度負面：稍微突出爭議面"
        else:
            return "負面剪輯：強調缺點，製造衝突"
    
    # ==================== 製作人決策 ====================
    
    def make_decision(self, decision_type: ProducerDecisionType,
                     target_characters: List[CharacterStats],
                     effects: Dict[str, float]) -> ProducerDecision:
        """
        製作人做出決策
        
        Args:
            decision_type: 決策類型
            target_characters: 目標角色列表
            effects: 效果映射
            
        Returns:
            決策記錄
        """
        # 創建決策
        decision = ProducerDecision(
            decision_id=str(uuid.uuid4())[:8],
            decision_type=decision_type,
            target_characters=[c.character_id for c in target_characters],
            effects=effects,
            editing_bias=self.state.editing_tendency
        )
        
        # 應用決策效果
        for char in target_characters:
            self._apply_decision_effects(char, effects, decision_type)
        
        self._decision_history.append(decision)
        self.state.decisions_made += 1
        
        return decision
    
    def _apply_decision_effects(self, character: CharacterStats,
                               effects: Dict[str, float],
                               decision_type: ProducerDecisionType):
        """應用決策效果"""
        # 基本效果映射
        stat_map = {
            "affection": lambda d: self.balance_engine.update_affection(character, d),
            "popularity": lambda d: self.balance_engine.update_popularity(character, d),
            "stress": lambda d: self.balance_engine.update_stress(character, d),
            "bond_warmth": lambda d: self.balance_engine.update_bond(
                character, BondDimension.WARMTH, d
            ),
            "bond_trust": lambda d: self.balance_engine.update_bond(
                character, BondDimension.TRUST, d
            ),
            "bond_spark": lambda d: self.balance_engine.update_bond(
                character, BondDimension.SPARK, d
            ),
            "emotion_joy": lambda d: self.balance_engine.update_emotion(
                character, EmotionAxis.JOY, d
            ),
            "emotion_anxiety": lambda d: self.balance_engine.update_emotion(
                character, EmotionAxis.ANXIETY, d
            ),
        }
        
        # 應用效果
        for stat_key, delta in effects.items():
            if stat_key in stat_map:
                stat_map[stat_key](delta)
        
        # 根據決策類型的特殊處理
        if decision_type == ProducerDecisionType.EDITING_TENDENCY:
            # 剪輯決策會影響人氣
            editing_effect = effects.get("editing_tendency", 0) * PRODUCER_POPULARITY_IMPACT
            self.balance_engine.update_popularity(character, editing_effect)
        
        elif decision_type == ProducerDecisionType.RULE_CHANGE:
            # 規則變更可能增加壓力
            self.balance_engine.update_stress(character, 5)
        
        elif decision_type == ProducerDecisionType.PUBLICITY:
            # 宣傳策略影響人氣
            publicity_boost = effects.get("publicity_boost", 0)
            self.balance_engine.update_popularity(character, publicity_boost)
    
    # ==================== 規則事件 ====================
    
    def create_rule_event(self, event_type: str,
                         affected_characters: List[str],
                         effects: Dict[str, float],
                         duration: int = 1,
                         description: str = "") -> RuleEvent:
        """
        創建規則事件
        
        Args:
            event_type: 事件類型
            affected_characters: 受影響角色 ID 列表
            effects: 效果
            duration: 持續週數
            description: 描述
            
        Returns:
            規則事件
        """
        event = RuleEvent(
            event_id=str(uuid.uuid4())[:8],
            event_type=event_type,
            affected_characters=affected_characters,
            effects=effects,
            duration=duration,
            description=description
        )
        
        self.state.active_rules.append(event)
        
        return event
    
    def process_rule_events(self, characters: Dict[str, CharacterStats]) -> List[Dict]:
        """
        處理進行中的規則事件
        
        Returns:
            本週處理的事件效果
        """
        processed = []
        remaining = []
        
        for rule in self.state.active_rules:
            # 應用效果
            for char_id in rule.affected_characters:
                if char_id in characters:
                    char = characters[char_id]
                    for stat_key, delta in rule.effects.items():
                        self._apply_single_stat(char, stat_key, delta)
            
            processed.append({
                "event_id": rule.event_id,
                "event_type": rule.event_type,
                "effects": rule.effects,
                "remaining_weeks": rule.duration
            })
            
            # 減少持續時間
            rule.duration -= 1
            if rule.duration > 0 or rule.is_permanent:
                remaining.append(rule)
        
        self.state.active_rules = remaining
        
        return processed
    
    def _apply_single_stat(self, character: CharacterStats,
                          stat_key: str, delta: float):
        """應用單一數值變化"""
        stat_map = {
            "affection": lambda: self.balance_engine.update_affection(character, delta),
            "popularity": lambda: self.balance_engine.update_popularity(character, delta),
            "stress": lambda: self.balance_engine.update_stress(character, delta),
            "bond_warmth": lambda: self.balance_engine.update_bond(
                character, BondDimension.WARMTH, delta
            ),
            "bond_trust": lambda: self.balance_engine.update_bond(
                character, BondDimension.TRUST, delta
            ),
            "bond_spark": lambda: self.balance_engine.update_bond(
                character, BondDimension.SPARK, delta
            ),
            "bond_tension": lambda: self.balance_engine.update_bond(
                character, BondDimension.TENSION, delta
            ),
        }
        
        if stat_key in stat_map:
            stat_map[stat_key]()
    
    # ==================== 公眾印象 ====================
    
    def calculate_public_perception(self, character: CharacterStats) -> Dict:
        """
        計算角色的公眾印象
        
        Returns:
            公眾印象分析
        """
        # 基礎印象（基於人氣）
        if character.popularity >= 80:
            base_perception = "廣受歡迎"
        elif character.popularity >= 60:
            base_perception = "受歡迎"
        elif character.popularity >= 40:
            base_perception = "普通"
        elif character.popularity >= 20:
            base_perception = "不太受歡迎"
        else:
            base_perception = "不受欢迎"
        
        # 剪輯影響
        character_bias = self.state.character_biases.get(
            character.character_id, 0
        )
        
        if character_bias >= 0.5:
            editing_perception = "正面形象"
        elif character_bias >= 0:
            editing_perception = "中性形象"
        elif character_bias >= -0.5:
            editing_perception = "負面形象"
        else:
            editing_perception = "爭議形象"
        
        # 情緒影響公眾印象
        emotion_avg = character.emotions.average()
        if emotion_avg >= 20:
            emotion_perception = "情緒穩定"
        elif emotion_avg >= 0:
            emotion_perception = "情緒正常"
        elif emotion_avg >= -20:
            emotion_perception = "情緒波動"
        else:
            emotion_perception = "情緒不穩定"
        
        return {
            "base_perception": base_perception,
            "editing_perception": editing_perception,
            "emotion_perception": emotion_perception,
            "popularity": character.popularity,
            "editing_bias": character_bias,
            "overall": self._calculate_overall_perception(
                character.popularity, character_bias, emotion_avg
            )
        }
    
    def _calculate_overall_perception(self, popularity: float,
                                     editing_bias: float,
                                     emotion_avg: float) -> str:
        """計算綜合印象"""
        score = (popularity / 100) * 40 + \
                ((editing_bias + 1) / 2) * 30 + \
                ((emotion_avg + 50) / 100) * 30
        
        if score >= 70:
            return "非常好"
        elif score >= 50:
            return "好"
        elif score >= 30:
            return "普通"
        elif score >= 15:
            return "差"
        else:
            return "非常差"
    
    # ==================== 資訊查詢 ====================
    
    def get_character_bias(self, character_id: str) -> float:
        """獲取對特定角色的剪輯偏見"""
        return self.state.character_biases.get(character_id, 0.0)
    
    def get_editing_history(self) -> List[Dict]:
        """獲取剪輯歷史"""
        return [
            {
                "character_id": e.character_id,
                "tendency": e.tendency,
                "duration": e.duration,
                "perception": e.public_perception.value,
                "description": e.description
            }
            for e in self._editing_history
        ]
    
    def get_decision_history(self) -> List[Dict]:
        """獲取決策歷史"""
        return [
            {
                "decision_id": d.decision_id,
                "type": d.decision_type.value,
                "targets": d.target_characters,
                "effects": d.effects
            }
            for d in self._decision_history
        ]
    
    def get_active_rules(self) -> List[Dict]:
        """獲取進行中的規則"""
        return [
            {
                "event_id": r.event_id,
                "type": r.event_type,
                "remaining": r.duration,
                "description": r.description
            }
            for r in self.state.active_rules
        ]
    
    # ==================== 報告生成 ====================
    
    def generate_producer_report(self, characters: Dict[str, CharacterStats]) -> Dict:
        """
        生成製作人報告
        
        Returns:
            完整報告
        """
        report = {
            "producer_state": {
                "editing_tendency": self.state.editing_tendency,
                "reputation": self.state.reputation,
                "decisions_made": self.state.decisions_made,
            },
            "character_perceptions": {},
            "active_rules": self.get_active_rules(),
            "editing_history_count": len(self._editing_history),
            "decision_history_count": len(self._decision_history),
        }
        
        # 各角色印象
        for char_id, char in characters.items():
            report["character_perceptions"][char.name] = \
                self.calculate_public_perception(char)
        
        return report
    
    def reset(self):
        """重置製作人系統"""
        self.state = ProducerState()
        self._editing_history.clear()
        self._decision_history.clear()
