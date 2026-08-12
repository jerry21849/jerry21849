"""
結局評分系統
Ending Scoring System

負責：
- 根據角色數值計算結局分數
- 評定結局等級（S+ 到 D-）
- 計算各項指標的得分
- 驗證隱藏條件
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .types import (
    CharacterStats, EndingGrade, EndingCondition,
    BondDimension, EmotionAxis
)
from .constants import (
    ENDING_THRESHOLDS, ENDING_SCORE_WEIGHTS, MAX_HIDDEN_CONDITIONS
)


@dataclass
class ScoreBreakdown:
    """評分明細"""
    affection_score: float = 0.0
    bond_score: float = 0.0
    emotion_score: float = 0.0
    correct_rate_score: float = 0.0
    hidden_score: float = 0.0
    total_score: float = 0.0
    grade: EndingGrade = EndingGrade.D_MINUS
    details: Dict[str, str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class ScoringEngine:
    """結局評分引擎"""
    
    def __init__(self):
        """初始化評分引擎"""
        self._validate_weights()
    
    def _validate_weights(self):
        """驗證權重總和為 1"""
        total = sum(ENDING_SCORE_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001, f"權重總和應為 1.0，實際為 {total}"
    
    # ==================== 各項指標計算 ====================
    
    def calculate_affection_score(self, character: CharacterStats) -> Tuple[float, str]:
        """
        計算好感度得分
        
        Returns:
            (得分 0-25, 說明)
        """
        aff = character.affection
        
        if aff >= 90:
            score = 25
            desc = f"好感度極高 ({aff:.1f}/100)：完美"
        elif aff >= 75:
            score = 20
            desc = f"好感度很高 ({aff:.1f}/100)：優秀"
        elif aff >= 60:
            score = 15
            desc = f"好感度良好 ({aff:.1f}/100)：穩定"
        elif aff >= 45:
            score = 10
            desc = f"好感度普通 ({aff:.1f}/100)：一般"
        elif aff >= 30:
            score = 5
            desc = f"好感度較低 ({aff:.1f}/100)：需要努力"
        elif aff >= 15:
            score = 2
            desc = f"好感度很低 ({aff:.1f}/100)：危險"
        else:
            score = 0
            desc = f"好感度極低 ({aff:.1f}/100)：失敗"
        
        return score, desc
    
    def calculate_bond_score(self, character: CharacterStats) -> Tuple[float, str]:
        """
        計算羈絆得分
        
        Returns:
            (得分 0-25, 說明)
        """
        bond = character.bond
        total = bond.total()
        
        # 基礎得分
        if total >= 90:
            base_score = 22
        elif total >= 75:
            base_score = 18
        elif total >= 60:
            base_score = 14
        elif total >= 45:
            base_score = 10
        elif total >= 30:
            base_score = 6
        elif total >= 15:
            base_score = 3
        else:
            base_score = 0
        
        # 平衡加成：四維越平衡，額外加分
        values = [bond.warmth, bond.trust, bond.spark, bond.tension]
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        
        if variance < 100:  # 非常平衡
            balance_bonus = 3
            balance_desc = "四維非常平衡"
        elif variance < 400:  # 較平衡
            balance_bonus = 2
            balance_desc = "四維較平衡"
        elif variance < 900:  # 一般
            balance_bonus = 1
            balance_desc = "四維一般"
        else:
            balance_bonus = 0
            balance_desc = "四維失衡"
        
        score = min(25, base_score + balance_bonus)
        
        desc = (f"羈絆總值: {total:.1f}/100 | "
                f"溫暖: {bond.warmth:.0f} 信任: {bond.trust:.0f} "
                f"火花: {bond.spark:.0f} 拉扯: {bond.tension:.0f} | "
                f"{balance_desc}")
        
        return score, desc
    
    def calculate_emotion_score(self, character: CharacterStats) -> Tuple[float, str]:
        """
        計算情緒狀態得分
        
        Returns:
            (得分 0-20, 說明)
        """
        emotions = character.emotions
        
        # 正面情緒得分
        positive = (emotions.joy + emotions.courage) / 2  # -50 到 +50
        # 負面情緒扣分
        negative = (emotions.anxiety + (-emotions.longing)) / 2
        
        # 正規化到 0-100
        positive_norm = (positive + 50) / 100 * 100
        negative_norm = (50 - negative) / 100 * 100
        
        # 綜合情緒分
        emotion_health = (positive_norm * 0.6 + negative_norm * 0.4)
        
        if emotion_health >= 80:
            score = 20
            desc = "情緒狀態極佳：積極樂觀"
        elif emotion_health >= 65:
            score = 16
            desc = "情緒狀態良好：穩定正向"
        elif emotion_health >= 50:
            score = 12
            desc = "情緒狀態普通：有波動"
        elif emotion_health >= 35:
            score = 8
            desc = "情緒狀態較差：負面情緒較多"
        elif emotion_health >= 20:
            score = 4
            desc = "情緒狀態差：需要支持"
        else:
            score = 0
            desc = "情緒狀態極差：瀕臨崩潰"
        
        return score, desc
    
    def calculate_correct_rate_score(self, character: CharacterStats) -> Tuple[float, str]:
        """
        計算關鍵選擇正確率得分
        
        Returns:
            (得分 0-20, 說明)
        """
        rate = character.correct_rate()
        total = character.total_choices
        correct = character.correct_choices
        
        if total == 0:
            return 10, "無選擇記錄"
        
        score = rate * 20
        
        if rate >= 0.9:
            desc = f"正確率極高 ({correct}/{total} = {rate:.1%})"
        elif rate >= 0.7:
            desc = f"正確率良好 ({correct}/{total} = {rate:.1%})"
        elif rate >= 0.5:
            desc = f"正確率普通 ({correct}/{total} = {rate:.1%})"
        elif rate >= 0.3:
            desc = f"正確率較低 ({correct}/{total} = {rate:.1%})"
        else:
            desc = f"正確率很低 ({correct}/{total} = {rate:.1%})"
        
        return score, desc
    
    def calculate_hidden_score(self, character: CharacterStats) -> Tuple[float, str]:
        """
        計算隱藏條件得分
        
        Returns:
            (得分 0-15, 說明)
        """
        hidden_count = len(character.hidden_conditions)
        max_hidden = MAX_HIDDEN_CONDITIONS
        
        # 基礎分
        base_score = (hidden_count / max_hidden) * 12
        
        # 特殊隱藏條件加成
        special_bonuses = {
            "route_true_end": 3,
            "all_bonds_max": 2,
            "perfect_choices": 2,
        }
        
        bonus = 0
        achieved_special = []
        for condition, bonus_value in special_bonuses.items():
            if condition in character.hidden_conditions:
                bonus += bonus_value
                achieved_special.append(condition)
        
        score = min(15, base_score + bonus)
        
        desc = f"隱藏條件: {hidden_count}/{max_hidden} 已達成"
        if achieved_special:
            desc += f" | 特殊: {', '.join(achieved_special)}"
        
        return score, desc
    
    # ==================== 綜合評分 ====================
    
    def calculate_total_score(self, character: CharacterStats) -> ScoreBreakdown:
        """
        計算綜合評分
        
        Returns:
            ScoreBreakdown 包含各項得分和總分
        """
        breakdown = ScoreBreakdown()
        
        # 計算各項得分
        breakdown.affection_score, affection_desc = self.calculate_affection_score(character)
        breakdown.bond_score, bond_desc = self.calculate_bond_score(character)
        breakdown.emotion_score, emotion_desc = self.calculate_emotion_score(character)
        breakdown.correct_rate_score, correct_desc = self.calculate_correct_rate_score(character)
        breakdown.hidden_score, hidden_desc = self.calculate_hidden_score(character)
        
        # 綜合評分 (滿分 105，上限 100)
        weighted_total = (
            breakdown.affection_score +
            breakdown.bond_score +
            breakdown.emotion_score +
            breakdown.correct_rate_score +
            breakdown.hidden_score
        )
        
        breakdown.total_score = min(100, weighted_total)
        
        # 詳細說明
        breakdown.details = {
            "好感度": affection_desc,
            "羈絆": bond_desc,
            "情緒": emotion_desc,
            "正確率": correct_desc,
            "隱藏": hidden_desc,
        }
        
        return breakdown
    
    def determine_grade(self, character: CharacterStats) -> ScoreBreakdown:
        """
        決定結局等級
        
        Returns:
            ScoreBreakdown 包含最終等級
        """
        breakdown = self.calculate_total_score(character)
        
        # 按順序檢查各等級條件
        grade_order = [
            EndingGrade.S_PLUS, EndingGrade.S,
            EndingGrade.A_PLUS, EndingGrade.A,
            EndingGrade.B_PLUS, EndingGrade.B,
            EndingGrade.C_PLUS, EndingGrade.C,
            EndingGrade.D_PLUS, EndingGrade.D_MINUS
        ]
        
        for grade in grade_order:
            condition = ENDING_THRESHOLDS[grade]
            if self._check_condition(character, condition):
                breakdown.grade = grade
                break
        
        return breakdown
    
    def _check_condition(self, character: CharacterStats, 
                        condition: EndingCondition) -> bool:
        """
        檢查角色是否滿足結局條件
        
        所有條件都必須滿足
        """
        # 好感度檢查
        if character.affection < condition.min_affection:
            return False
        
        # 羈絆檢查
        if character.bond.total() < condition.min_bond_total:
            return False
        
        # 正確率檢查
        if character.correct_rate() < condition.min_correct_rate:
            return False
        
        # 隱藏條件檢查
        for required in condition.required_hidden:
            if required not in character.hidden_conditions:
                return False
        
        # 情緒條件檢查
        for axis_name, (min_val, max_val) in condition.emotion_requirements.items():
            axis = EmotionAxis(axis_name)
            value = character.emotions.get(axis)
            if value < min_val or value > max_val:
                return False
        
        return True
    
    # ==================== 分數區間判定 ====================
    
    def get_score_range(self, score: float) -> Tuple[str, str]:
        """
        根據分數返回區間描述
        
        Returns:
            (等級標籤, 描述)
        """
        if score >= 95:
            return "S+", "完美區間"
        elif score >= 85:
            return "S", "極佳區間"
        elif score >= 75:
            return "A+", "很好區間"
        elif score >= 65:
            return "A", "好區間"
        elif score >= 55:
            return "B+", "不錯區間"
        elif score >= 45:
            return "B", "普通區間"
        elif score >= 35:
            return "C+", "不太好區間"
        elif score >= 25:
            return "C", "不好區間"
        elif score >= 15:
            return "D+", "差區間"
        else:
            return "D-", "最差區間"
    
    def get_grade_description(self, grade: EndingGrade) -> str:
        """獲取等級的詳細描述"""
        condition = ENDING_THRESHOLDS[grade]
        return condition.description
    
    def compare_characters(self, characters: List[CharacterStats]) -> List[Tuple[str, ScoreBreakdown]]:
        """
        比較多個角色的評分
        
        Returns:
            按分數排序的角色評分列表
        """
        results = []
        for char in characters:
            breakdown = self.determine_grade(char)
            results.append((char.name, breakdown))
        
        # 按分數降序排序
        results.sort(key=lambda x: x[1].total_score, reverse=True)
        
        return results
    
    def generate_report(self, character: CharacterStats) -> Dict:
        """
        生成詳細評分報告
        
        Returns:
            完整報告字典
        """
        breakdown = self.determine_grade(character)
        condition = ENDING_THRESHOLDS[breakdown.grade]
        
        report = {
            "character": character.name,
            "grade": breakdown.grade.value,
            "grade_description": condition.description,
            "total_score": round(breakdown.total_score, 2),
            "score_breakdown": {
                "好感度": round(breakdown.affection_score, 2),
                "羈絆": round(breakdown.bond_score, 2),
                "情緒": round(breakdown.emotion_score, 2),
                "正確率": round(breakdown.correct_rate_score, 2),
                "隱藏條件": round(breakdown.hidden_score, 2),
            },
            "details": breakdown.details,
            "character_stats": {
                "好感度": character.affection,
                "羈絆總值": character.bond.total(),
                "人氣值": character.popularity,
                "壓力": character.stress,
                "情緒平均": character.emotions.average(),
                "正確率": f"{character.correct_rate():.1%}",
                "隱藏條件數": len(character.hidden_conditions),
            },
            "requirements_met": {
                "好感度": character.affection >= condition.min_affection,
                "羈絆": character.bond.total() >= condition.min_bond_total,
                "正確率": character.correct_rate() >= condition.min_correct_rate,
                "隱藏條件": all(
                    h in character.hidden_conditions 
                    for h in condition.required_hidden
                ),
            }
        }
        
        return report
