"""
蝴蝶效應引擎
Butterfly Effect Engine

負責：
- 跨角色數值影響
- 多重觸發路徑
- 隱藏結局組合
- 影響權重計算
"""
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import uuid

from .types import (
    CharacterStats, ButterflyEffect, ButterflyScope,
    BondDimension, EmotionAxis, GameEvent
)
from .constants import (
    BUTTERFLY_MIN_WEIGHT, BUTTERFLY_MAX_WEIGHT, BUTTERFLY_DEFAULT_WEIGHT
)
from .balance import BalanceEngine


@dataclass
class ButterflyTrigger:
    """蝴蝶效應觸發條件"""
    trigger_id: str
    event_type: str
    source_character: str
    condition_check: Optional[callable] = None  # 自定義條件檢查
    min_value: Optional[float] = None          # 最小值要求
    required_hidden: List[str] = field(default_factory=list)


@dataclass 
class ButterflyChain:
    """蝴蝶效應鏈"""
    chain_id: str
    triggers: List[ButterflyTrigger]
    effects: List[ButterflyEffect]
    description: str = ""
    is_hidden: bool = False  # 是否為隱藏路徑


class ButterflyEngine:
    """蝴蝶效應引擎"""
    
    def __init__(self, balance_engine: BalanceEngine):
        """
        初始化蝴蝶效應引擎
        
        Args:
            balance_engine: 數值平衡引擎實例
        """
        self.balance_engine = balance_engine
        self.effects: Dict[str, ButterflyEffect] = {}
        self.chains: Dict[str, ButterflyChain] = {}
        self._effect_history: List[Dict] = []
    
    # ==================== 效果管理 ====================
    
    def register_effect(self, effect: ButterflyEffect):
        """註冊蝴蝶效應規則"""
        self.effects[effect.rule_id] = effect
    
    def register_chain(self, chain: ButterflyChain):
        """註冊蝴蝶效應鏈"""
        self.chains[chain.chain_id] = chain
    
    def remove_effect(self, rule_id: str):
        """移除蝴蝶效應規則"""
        if rule_id in self.effects:
            del self.effects[rule_id]
    
    # ==================== 影響計算 ====================
    
    def calculate_influence_weight(self, source: CharacterStats, 
                                   target: CharacterStats,
                                   base_weight: float) -> float:
        """
        計算實際影響權重
        
        基礎權重會根據角色狀態進行調整
        """
        # 基礎權重限制
        weight = max(BUTTERFLY_MIN_WEIGHT, min(BUTTERFLY_MAX_WEIGHT, base_weight))
        
        # 源角色好感度修正：好感度越高，影響力越大
        source_affection_factor = 0.8 + (source.affection / 100) * 0.4
        
        # 目標角色接受度：好感度越高，越容易接受影響
        target_receptivity = 0.7 + (target.affection / 100) * 0.6
        
        # 壓力修正：高壓力降低影響效果
        stress_factor = 1.0 - (target.stress / 100) * 0.3
        
        # 人氣差距修正：人氣差距越大，影響越明顯
        popularity_gap = abs(source.popularity - target.popularity) / 100
        popularity_factor = 1.0 + popularity_gap * 0.2
        
        final_weight = (weight * 
                       source_affection_factor * 
                       target_receptivity * 
                       stress_factor * 
                       popularity_factor)
        
        return max(BUTTERFLY_MIN_WEIGHT, min(BUTTERFLY_MAX_WEIGHT, final_weight))
    
    def apply_effect(self, effect: ButterflyEffect,
                     source: CharacterStats,
                     target: CharacterStats,
                     context: Dict = None) -> Dict[str, float]:
        """
        應用蝴蝶效應
        
        Args:
            effect: 蝴蝶效應規則
            source: 源角色（觸發者）
            target: 目標角色（受影響者）
            context: 額外上下文
            
        Returns:
            實際應用的效果
        """
        # 檢查隱藏條件要求
        if effect.hidden_requirement:
            if effect.hidden_requirement not in source.hidden_conditions:
                return {}
        
        # 計算實際權重
        actual_weight = self.calculate_influence_weight(
            source, target, effect.weight
        )
        
        applied = {}
        
        # 應用數值修正
        for stat_key, delta in effect.stat_modifiers.items():
            adjusted_delta = delta * actual_weight
            applied_stat = self._apply_stat_modifier(
                target, stat_key, adjusted_delta
            )
            if applied_stat is not None:
                applied[stat_key] = applied_stat
        
        # 記錄歷史
        history_entry = {
            "source": source.name,
            "target": target.name,
            "effect_id": effect.rule_id,
            "weight": actual_weight,
            "applied": applied,
        }
        self._effect_history.append(history_entry)
        
        return applied
    
    def _apply_stat_modifier(self, character: CharacterStats,
                             stat_key: str, delta: float) -> Optional[float]:
        """
        應用單一數值修正
        
        Returns:
            實際應用的變化量
        """
        # 好感度
        if stat_key == "affection":
            old = character.affection
            self.balance_engine.update_affection(character, delta)
            return character.affection - old
        
        # 羈絆四維
        bond_map = {
            "bond_warmth": BondDimension.WARMTH,
            "bond_trust": BondDimension.TRUST,
            "bond_spark": BondDimension.SPARK,
            "bond_tension": BondDimension.TENSION,
        }
        if stat_key in bond_map:
            dim = bond_map[stat_key]
            old = character.bond.get(dim)
            self.balance_engine.update_bond(character, dim, delta)
            return character.bond.get(dim) - old
        
        # 情緒四軸
        emotion_map = {
            "emotion_joy": EmotionAxis.JOY,
            "emotion_longing": EmotionAxis.LONGING,
            "emotion_anxiety": EmotionAxis.ANXIETY,
            "emotion_courage": EmotionAxis.COURAGE,
        }
        if stat_key in emotion_map:
            axis = emotion_map[stat_key]
            old = character.emotions.get(axis)
            self.balance_engine.update_emotion(character, axis, delta)
            return character.emotions.get(axis) - old
        
        # 人氣值
        if stat_key == "popularity":
            old = character.popularity
            self.balance_engine.update_popularity(character, delta)
            return character.popularity - old
        
        # 壓力
        if stat_key == "stress":
            old = character.stress
            self.balance_engine.update_stress(character, delta)
            return character.stress - old
        
        return None
    
    # ==================== 多重路徑 ====================
    
    def trigger_event_effects(self, event: GameEvent,
                              characters: Dict[str, CharacterStats]) -> List[Dict]:
        """
        觸發事件的所有蝴蝶效應
        
        Args:
            event: 遊戲事件
            characters: 所有角色數據
            
        Returns:
            應用的效果列表
        """
        source = characters.get(event.character_id)
        if not source:
            return []
        
        applied_effects = []
        
        # 查找所有適用的效果
        for effect in self.effects.values():
            if effect.trigger_event != event.event_type:
                continue
            
            if effect.source_character != event.character_id:
                # 檢查是否為間接受影響
                if effect.scope != ButterflyScope.INDIRECT:
                    continue
            
            # 獲取目標角色
            target = characters.get(effect.target_character)
            if not target:
                continue
            
            # 應用效果
            result = self.apply_effect(effect, source, target)
            if result:
                applied_effects.append({
                    "effect_id": effect.rule_id,
                    "target": target.name,
                    "changes": result
                })
        
        return applied_effects
    
    def check_chain_triggers(self, event: GameEvent,
                            characters: Dict[str, CharacterStats]) -> List[str]:
        """
        檢查蝴蝶效應鏈是否觸發
        
        Returns:
            觸發的鏈 ID 列表
        """
        triggered_chains = []
        
        for chain in self.chains.values():
            if self._check_chain(chain, event, characters):
                triggered_chains.append(chain.chain_id)
                # 執行鏈的效果
                self._execute_chain(chain, characters)
        
        return triggered_chains
    
    def _check_chain(self, chain: ButterflyChain,
                    event: GameEvent,
                    characters: Dict[str, CharacterStats]) -> bool:
        """檢查鏈是否滿足觸發條件"""
        # 檢查所有觸發條件
        for trigger in chain.triggers:
            if not self._check_trigger(trigger, event, characters):
                return False
        return True
    
    def _check_trigger(self, trigger: ButterflyTrigger,
                      event: GameEvent,
                      characters: Dict[str, CharacterStats]) -> bool:
        """檢查單一觸發條件"""
        # 事件類型匹配
        if trigger.event_type != event.event_type:
            return False
        
        # 角色匹配
        if trigger.source_character != event.character_id:
            return False
        
        # 自定義條件檢查
        if trigger.condition_check:
            source = characters.get(event.character_id)
            if not trigger.condition_check(source):
                return False
        
        # 最小值要求
        if trigger.min_value is not None:
            source = characters.get(event.character_id)
            if source and source.affection < trigger.min_value:
                return False
        
        # 隱藏條件要求
        if trigger.required_hidden:
            source = characters.get(event.character_id)
            if source:
                for hidden in trigger.required_hidden:
                    if hidden not in source.hidden_conditions:
                        return False
        
        return True
    
    def _execute_chain(self, chain: ButterflyChain,
                      characters: Dict[str, CharacterStats]):
        """執行蝴蝶效應鏈"""
        for effect in chain.effects:
            source = characters.get(effect.source_character)
            target = characters.get(effect.target_character)
            
            if source and target:
                self.apply_effect(effect, source, target)
    
    # ==================== 隱藏結局 ====================
    
    def check_hidden_ending(self, characters: Dict[str, CharacterStats]) -> Optional[str]:
        """
        檢查隱藏結局是否達成
        
        隱藏結局需要跨角色的特定組合
        """
        # 檢查跨角色組合條件
        combinations = [
            {
                "id": "true_end",
                "check": self._check_true_ending,
                "description": "真實結局：所有角色好感度滿分且羈絆全滿"
            },
            {
                "id": "secret_bond",
                "check": self._check_secret_bond,
                "description": "隱藏羈絆：特定角色組合的特殊羈絆"
            },
            {
                "id": "perfect_harmony",
                "check": self._check_perfect_harmony,
                "description": "完美和諧：所有角色情緒穩定且正面"
            },
        ]
        
        for combo in combinations:
            if combo["check"](characters):
                # 達成隱藏條件，更新所有角色
                for char in characters.values():
                    char.hidden_conditions.add(f"hidden_{combo['id']}")
                return combo["id"]
        
        return None
    
    def _check_true_ending(self, characters: Dict[str, CharacterStats]) -> bool:
        """檢查真實結局條件"""
        if len(characters) < 2:
            return False
        
        # 所有角色好感度 >= 90
        for char in characters.values():
            if char.affection < 90:
                return False
        
        # 至少一個角色羈絆全滿
        has_max_bond = False
        for char in characters.values():
            if (char.bond.warmth >= 95 and 
                char.bond.trust >= 95 and 
                char.bond.spark >= 95):
                has_max_bond = True
                break
        
        return has_max_bond
    
    def _check_secret_bond(self, characters: Dict[str, CharacterStats]) -> bool:
        """檢查隱藏羈絆條件"""
        char_list = list(characters.values())
        if len(char_list) < 2:
            return False
        
        # 特定角色組合的火花 >= 80 且信任 >= 80
        for i in range(len(char_list)):
            for j in range(i + 1, len(char_list)):
                if (char_list[i].bond.spark >= 80 and 
                    char_list[i].bond.trust >= 80 and
                    char_list[j].bond.spark >= 80 and
                    char_list[j].bond.trust >= 80):
                    return True
        
        return False
    
    def _check_perfect_harmony(self, characters: Dict[str, CharacterStats]) -> bool:
        """檢查完美和諧條件"""
        for char in characters.values():
            # 情緒必須全部正向
            if char.emotions.joy < 30:
                return False
            if char.emotions.anxiety > 0:
                return False
            if char.emotions.courage < 20:
                return False
            # 壓力必須低
            if char.stress > 30:
                return False
        
        return True
    
    # ==================== 輔助方法 ====================
    
    def get_effect_history(self) -> List[Dict]:
        """獲取效果歷史記錄"""
        return self._effect_history.copy()
    
    def get_character_influence_map(self, character_id: str) -> Dict[str, float]:
        """
        獲取角色對其他角色的影響力地圖
        
        Returns:
            {目標角色ID: 平均影響力}
        """
        influence_map = {}
        
        for effect in self.effects.values():
            if effect.source_character == character_id:
                target = effect.target_character
                if target not in influence_map:
                    influence_map[target] = []
                influence_map[target].append(effect.weight)
        
        # 計算平均影響力
        result = {}
        for target_id, weights in influence_map.items():
            result[target_id] = sum(weights) / len(weights)
        
        return result
    
    def simulate_butterfly_chain(self, initial_event: GameEvent,
                                 characters: Dict[str, CharacterStats],
                                 max_depth: int = 3) -> List[Dict]:
        """
        模擬蝴蝶效應鏈的傳播
        
        Args:
            initial_event: 初始事件
            characters: 所有角色數據
            max_depth: 最大傳播深度
            
        Returns:
            傳播過程記錄
        """
        propagation_log = []
        visited = set()
        
        def _propagate(event: GameEvent, depth: int):
            if depth > max_depth or event.character_id in visited:
                return
            
            visited.add(event.character_id)
            
            # 應用效果
            effects = self.trigger_event_effects(event, characters)
            if effects:
                propagation_log.append({
                    "depth": depth,
                    "source": event.character_id,
                    "effects": effects
                })
            
            # 檢查鏈
            chains = self.check_chain_triggers(event, characters)
            if chains:
                propagation_log.append({
                    "depth": depth,
                    "chains_triggered": chains
                })
            
            # 遞迴傳播
            for effect_info in effects:
                target_id = None
                for effect in self.effects.values():
                    if effect.rule_id == effect_info["effect_id"]:
                        target_id = effect.target_character
                        break
                
                if target_id and target_id not in visited:
                    # 創建新的事件觸發
                    new_event = GameEvent(
                        event_id=f"chain_{event.event_id}_{depth}",
                        week=event.week,
                        character_id=target_id,
                        event_type=f"chain_{event.event_type}",
                        choice_id=event.choice_id
                    )
                    _propagate(new_event, depth + 1)
        
        _propagate(initial_event, 0)
        
        return propagation_log
