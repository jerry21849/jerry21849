"""
數值平衡系統
Stat Balance System

負責：
- 好感度衰減與更新
- 羈絆四維平衡
- 情緒系統管理
- 壓力系統管理
- 人氣值計算
"""
from typing import Dict, Optional, Set
import random

from .types import (
    CharacterStats, BondStats, EmotionStats,
    BondDimension, EmotionAxis
)
from .constants import (
    AFFECTION_RANGE, AFFECTION_DECAY_MIN, AFFECTION_DECAY_MAX,
    BOND_RANGE, POPULARITY_RANGE, EMOTION_RANGE, STRESS_RANGE,
    STRESS_CRISIS_THRESHOLD, STRESS_RECOVERY_RATE,
    get_affection_decay, get_stress_recovery, CHOICE_EFFECTS
)


class BalanceEngine:
    """數值平衡引擎"""
    
    def __init__(self):
        """初始化平衡引擎"""
        self._validate_constants()
    
    def _validate_constants(self):
        """驗證常量設定是否合理"""
        assert AFFECTION_RANGE == (0, 100), "好感度範圍應為 0-100"
        assert BOND_RANGE == (0, 100), "羈絆範圍應為 0-100"
        assert POPULARITY_RANGE == (0, 100), "人氣值範圍應為 0-100"
        assert EMOTION_RANGE == (-50, 50), "情緒範圍應為 -50 到 +50"
        assert STRESS_RANGE == (0, 100), "壓力範圍應為 0-100"
    
    # ==================== 好感度管理 ====================
    
    def update_affection(self, character: CharacterStats, delta: float) -> float:
        """
        更新好感度
        
        Args:
            character: 角色數據
            delta: 變化量（正數增加，負數減少）
            
        Returns:
            更新後的好感度
        """
        old_value = character.affection
        character.affection = max(AFFECTION_RANGE[0], 
                                  min(AFFECTION_RANGE[1], 
                                      character.affection + delta))
        return character.affection
    
    def apply_weekly_decay(self, character: CharacterStats, week: int) -> float:
        """
        每週好感度自然衰減
        
        Args:
            character: 角色數據
            week: 當前週數
            
        Returns:
            衰減後的好感度
        """
        decay = get_affection_decay(week)
        # 隨機波動 ±2
        decay += random.uniform(-2, 2)
        decay = max(AFFECTION_DECAY_MIN, min(AFFECTION_DECAY_MAX, decay))
        
        return self.update_affection(character, -decay)
    
    def get_affection_modifier(self, character: CharacterStats) -> float:
        """
        根據好感度獲取修正係數
        
        好感度越高，後續增加越難（遞減效應）
        """
        if character.affection >= 80:
            return 0.5  # 高好感度時，增加效果減半
        elif character.affection >= 60:
            return 0.75
        elif character.affection >= 40:
            return 1.0
        elif character.affection >= 20:
            return 1.2  # 低好感度時，更容易增加
        return 1.5
    
    # ==================== 羈絆系統 ====================
    
    def update_bond(self, character: CharacterStats, 
                    dimension: BondDimension, delta: float) -> float:
        """
        更新羈絆特定維度
        
        Args:
            character: 角色數據
            dimension: 維度
            delta: 變化量
            
        Returns:
            更新後的數值
        """
        old_value = character.bond.get(dimension)
        new_value = max(BOND_RANGE[0], min(BOND_RANGE[1], old_value + delta))
        character.bond.set(dimension, new_value)
        return new_value
    
    def update_all_bonds(self, character: CharacterStats, 
                         modifiers: Dict[BondDimension, float]) -> BondStats:
        """
        批量更新羈絆四維
        
        Args:
            character: 角色數據
            modifiers: 各維度的變化量
            
        Returns:
            更新後的羈絆數據
        """
        for dim, delta in modifiers.items():
            self.update_bond(character, dim, delta)
        return character.bond
    
    def get_bond_synergy(self, character: CharacterStats) -> float:
        """
        計算羈絆協同效應
        
        當四維平衡時，產生額外加成
        """
        values = [
            character.bond.warmth,
            character.bond.trust,
            character.bond.spark,
            character.bond.tension
        ]
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        
        # 方差越小（越平衡），協同效應越高
        if variance < 100:  # 標準差 < 10
            return 1.2  # +20% 加成
        elif variance < 400:  # 標準差 < 20
            return 1.1  # +10% 加成
        return 1.0
    
    def is_bond_maxed(self, character: CharacterStats) -> bool:
        """檢查羈絆是否全滿"""
        return (character.bond.warmth >= 95 and 
                character.bond.trust >= 95 and 
                character.bond.spark >= 95 and 
                character.bond.tension >= 95)
    
    # ==================== 情緒系統 ====================
    
    def update_emotion(self, character: CharacterStats,
                       axis: EmotionAxis, delta: float) -> float:
        """
        更新情緒特定軸
        
        Args:
            character: 角色數據
            axis: 情緒軸
            delta: 變化量
            
        Returns:
            更新後的數值
        """
        old_value = character.emotions.get(axis)
        new_value = max(EMOTION_RANGE[0], min(EMOTION_RANGE[1], old_value + delta))
        character.emotions.set(axis, new_value)
        return new_value
    
    def update_all_emotions(self, character: CharacterStats,
                            modifiers: Dict[EmotionAxis, float]) -> EmotionStats:
        """批量更新情緒四軸"""
        for axis, delta in modifiers.items():
            self.update_emotion(character, axis, delta)
        return character.emotions
    
    def normalize_emotions(self, character: CharacterStats):
        """
        情緒正規化
        
        長期處於極端情緒會逐漸回歸
        """
        for axis in EmotionAxis:
            value = character.emotions.get(axis)
            # 向 0 回歸 5%
            new_value = value * 0.95
            character.emotions.set(axis, new_value)
    
    def get_emotion_stability(self, character: CharacterStats) -> float:
        """
        計算情緒穩定度
        
        穩定度影響後續情緒變化的幅度
        """
        avg = character.emotions.average()
        if abs(avg) < 10:
            return 0.8  # 穩定時，情緒變化減弱
        elif abs(avg) < 25:
            return 1.0
        return 1.2  # 不穩定時，情緒變化放大
    
    # ==================== 壓力系統 ====================
    
    def update_stress(self, character: CharacterStats, delta: float) -> float:
        """
        更新壓力值
        
        Args:
            character: 角色數據
            delta: 變化量
            
        Returns:
            更新後的壓力值
        """
        old_value = character.stress
        character.stress = max(STRESS_RANGE[0], 
                               min(STRESS_RANGE[1], 
                                   character.stress + delta))
        return character.stress
    
    def check_stress_crisis(self, character: CharacterStats) -> bool:
        """
        檢查是否觸發壓力危機
        
        Returns:
            True 如果壓力已滿觸發危機
        """
        return character.stress >= STRESS_CRISIS_THRESHOLD
    
    def apply_stress_recovery(self, character: CharacterStats) -> float:
        """
        每週壓力自然恢復
        
        Returns:
            恢復後的壓力值
        """
        recovery = get_stress_recovery(character.stress)
        return self.update_stress(character, -recovery)
    
    def get_stress_effects(self, character: CharacterStats) -> Dict[str, float]:
        """
        獲取壓力對其他數值的影響
        
        Returns:
            各數值的修正量
        """
        level = character.stress
        effects = {}
        
        if level >= 80:
            effects["affection"] = -5      # 高壓力降低好感度獲取
            effects["bond_decay"] = -2     # 羈絆略微下降
            effects["emotion_anxiety"] = 3  # 焦慮增加
        elif level >= 60:
            effects["affection"] = -3
            effects["emotion_anxiety"] = 2
        elif level >= 40:
            effects["affection"] = -1
        
        return effects
    
    # ==================== 人氣值系統 ====================
    
    def update_popularity(self, character: CharacterStats, delta: float) -> float:
        """更新人氣值"""
        character.popularity = max(POPULARITY_RANGE[0],
                                   min(POPULARITY_RANGE[1],
                                       character.popularity + delta))
        return character.popularity
    
    def get_popularity_modifier(self, character: CharacterStats) -> float:
        """
        人氣值修正係數
        
        高人氣影響後續選擇的效果
        """
        if character.popularity >= 80:
            return 1.3  # 高人氣加成
        elif character.popularity >= 60:
            return 1.15
        elif character.popularity >= 40:
            return 1.0
        elif character.popularity >= 20:
            return 0.9
        return 0.8  # 低人氣減益
    
    # ==================== 綜合效果 ====================
    
    def apply_choice_effect(self, character: CharacterStats, 
                           effect_type: str) -> Dict[str, float]:
        """
        應用選擇效果
        
        Args:
            character: 角色數據
            effect_type: 效果類型（positive_small, negative_medium 等）
            
        Returns:
            實際應用的效果
        """
        if effect_type not in CHOICE_EFFECTS:
            return {}
        
        template = CHOICE_EFFECTS[effect_type]
        applied = {}
        
        # 獲取修正係數
        aff_modifier = self.get_affection_modifier(character)
        bond_synergy = self.get_bond_synergy(character)
        pop_modifier = self.get_popularity_modifier(character)
        emotion_stability = self.get_emotion_stability(character)
        
        # 應用好感度變化
        if "affection" in template:
            delta = template["affection"] * aff_modifier
            self.update_affection(character, delta)
            applied["affection"] = delta
        
        # 應用羈絆變化
        bond_map = {
            "bond_warmth": BondDimension.WARMTH,
            "bond_trust": BondDimension.TRUST,
            "bond_spark": BondDimension.SPARK,
            "bond_tension": BondDimension.TENSION,
        }
        for key, dim in bond_map.items():
            if key in template:
                delta = template[key] * bond_synergy
                self.update_bond(character, dim, delta)
                applied[key] = delta
        
        # 應用情緒變化
        emotion_map = {
            "emotion_joy": EmotionAxis.JOY,
            "emotion_longing": EmotionAxis.LONGING,
            "emotion_anxiety": EmotionAxis.ANXIETY,
            "emotion_courage": EmotionAxis.COURAGE,
        }
        for key, axis in emotion_map.items():
            if key in template:
                delta = template[key] * emotion_stability
                self.update_emotion(character, axis, delta)
                applied[key] = delta
        
        # 應用人氣變化
        if "popularity" in template:
            delta = template["popularity"] * pop_modifier
            self.update_popularity(character, delta)
            applied["popularity"] = delta
        
        # 應用壓力變化
        if "stress" in template:
            self.update_stress(character, template["stress"])
            applied["stress"] = template["stress"]
        
        return applied
    
    def process_weekly_update(self, character: CharacterStats, week: int) -> Dict:
        """
        處理每週更新
        
        Returns:
            本週更新摘要
        """
        summary = {
            "week": week,
            "character": character.name,
            "changes": {},
            "events": []
        }
        
        # 好感度衰減
        old_aff = character.affection
        self.apply_weekly_decay(character, week)
        summary["changes"]["affection"] = character.affection - old_aff
        
        # 壓力恢復
        old_stress = character.stress
        self.apply_stress_recovery(character)
        summary["changes"]["stress"] = character.stress - old_stress
        
        # 情緒正規化
        old_emotions = {
            axis: character.emotions.get(axis) 
            for axis in EmotionAxis
        }
        self.normalize_emotions(character)
        for axis in EmotionAxis:
            diff = character.emotions.get(axis) - old_emotions[axis]
            if abs(diff) > 0.1:
                summary["changes"][f"emotion_{axis.value}"] = diff
        
        # 檢查壓力危機
        if self.check_stress_crisis(character):
            summary["events"].append("stress_crisis")
            # 觸發危機時壓力部分釋放
            self.update_stress(character, -30)
            # 負面效果
            self.update_affection(character, -10)
            for dim in BondDimension:
                self.update_bond(character, dim, -5)
        
        return summary
    
    def calculate_overall_score(self, character: CharacterStats) -> float:
        """
        計算角色綜合分數
        
        用於快速評估角色狀態
        """
        # 好感度得分 (0-25)
        affection_score = (character.affection / 100) * 25
        
        # 羈絆得分 (0-25)
        bond_score = (character.bond.total() / 100) * 25
        
        # 情緒得分 (0-20)
        emotion_avg = character.emotions.average()
        emotion_score = ((emotion_avg + 50) / 100) * 20  # 正規化到 0-20
        
        # 正確率得分 (0-15)
        correct_score = character.correct_rate() * 15
        
        # 壓力扣分 (0-15)
        stress_penalty = (character.stress / 100) * 15
        
        return affection_score + bond_score + emotion_score + correct_score - stress_penalty
