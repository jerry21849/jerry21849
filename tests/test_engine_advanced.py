"""
遊戲引擎進階測試
Game Engine Advanced Tests - 驗證 S+ 結局達成條件
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.engine import (
    BalanceEngine, ScoringEngine, ButterflyEngine, ProducerSystem,
    CharacterStats, GameEvent, EndingGrade,
    BondDimension, EmotionAxis, create_game_engine
)


def test_s_plus_ending():
    """測試 S+ 完美結局達成"""
    print("=" * 60)
    print("測試 S+ 完美結局達成條件")
    print("=" * 60)
    
    engine = ScoringEngine()
    
    # 創建完美角色
    char = CharacterStats(name="完美角色")
    char.affection = 95
    char.bond.warmth = 95
    char.bond.trust = 95
    char.bond.spark = 95
    char.bond.tension = 95
    char.correct_choices = 19
    char.total_choices = 20
    char.hidden_conditions = {"route_true_end", "all_bonds_max", "perfect_choices"}
    char.emotions.joy = 45
    char.emotions.courage = 45
    
    report = engine.generate_report(char)
    
    print(f"角色: {char.name}")
    print(f"等級: {report['grade']}")
    print(f"總分: {report['total_score']}")
    print(f"等級描述: {report['grade_description']}")
    print(f"\n各項得分:")
    for key, value in report['score_breakdown'].items():
        print(f"  {key}: {value}")
    
    print(f"\n達成條件:")
    for key, value in report['requirements_met'].items():
        print(f"  {key}: {'✓' if value else '✗'}")
    
    assert report['grade'] == 'S+', f"應為 S+，實際為 {report['grade']}"
    print("\n✓ S+ 結局測試通過\n")
    
    return report


def test_all_grades():
    """測試所有等級"""
    print("=" * 60)
    print("測試所有結局等級")
    print("=" * 60)
    
    engine = ScoringEngine()
    
    # 創建不同等級的角色
    grades_to_test = [
        ("S+ 完美", {
            "affection": 95,
            "bond": (95, 95, 95, 95),
            "correct_rate": 0.95,
            "hidden": {"route_true_end", "all_bonds_max", "perfect_choices"},
            "joy": 45,
            "courage": 45,
        }),
        ("S 極佳", {
            "affection": 88,
            "bond": (85, 85, 80, 80),
            "correct_rate": 0.88,
            "hidden": {"route_true_end"},
            "joy": 35,
            "courage": 30,
        }),
        ("A+ 很好", {
            "affection": 78,
            "bond": (75, 70, 70, 65),
            "correct_rate": 0.78,
            "hidden": set(),
            "joy": 25,
            "courage": 20,
        }),
        ("A 好", {
            "affection": 68,
            "bond": (65, 60, 60, 55),
            "correct_rate": 0.68,
            "hidden": set(),
            "joy": 15,
            "courage": 10,
        }),
        ("B+ 不錯", {
            "affection": 58,
            "bond": (55, 50, 50, 45),
            "correct_rate": 0.58,
            "hidden": set(),
            "joy": 5,
            "courage": 0,
        }),
        ("B 普通", {
            "affection": 48,
            "bond": (45, 40, 40, 35),
            "correct_rate": 0.48,
            "hidden": set(),
            "joy": 0,
            "courage": -5,
        }),
        ("D- 最差", {
            "affection": 10,
            "bond": (10, 5, 5, 5),
            "correct_rate": 0.1,
            "hidden": set(),
            "joy": -40,
            "courage": -40,
        }),
    ]
    
    print("\n等級    | 總分  | 好感度 | 羈絆 | 正確率 | 描述")
    print("-" * 60)
    
    for name, stats in grades_to_test:
        char = CharacterStats(name=name)
        char.affection = stats["affection"]
        char.bond.warmth, char.bond.trust, char.bond.spark, char.bond.tension = stats["bond"]
        char.correct_choices = int(stats["correct_rate"] * 20)
        char.total_choices = 20
        char.hidden_conditions = stats["hidden"]
        char.emotions.joy = stats.get("joy", 0)
        char.emotions.courage = stats.get("courage", 0)
        
        report = engine.generate_report(char)
        grade = report['grade']
        score = report['total_score']
        aff = char.affection
        bond = char.bond.total()
        rate = char.correct_rate()
        desc = report['grade_description'][:20]
        
        print(f"{grade:4}    | {score:4.1f} | {aff:5.1f}  | {bond:4.1f} | {rate:5.1%} | {desc}")
    
    print("\n✓ 所有等級測試通過\n")


def test_butterfly_cross_character():
    """測試跨角色蝴蝶效應"""
    print("=" * 60)
    print("測試跨角色蝴蝶效應")
    print("=" * 60)
    
    balance = BalanceEngine()
    butterfly = ButterflyEngine(balance)
    
    # 創建角色
    char_a = CharacterStats(name="角色A")
    char_b = CharacterStats(name="角色B")
    char_a.affection = 80
    char_b.affection = 50
    
    # 創建蝴蝶效應
    from src.engine.types import ButterflyScope, ButterflyEffect
    
    effect = ButterflyEffect(
        rule_id="cross_effect",
        source_character=char_a.character_id,
        target_character=char_b.character_id,
        trigger_event="confession",
        scope=ButterflyScope.DIRECT,
        weight=0.35,
        stat_modifiers={
            "affection": 15,
            "bond_spark": 10,
            "emotion_joy": 8,
        }
    )
    butterfly.register_effect(effect)
    
    # 觸發
    event = GameEvent(
        event_id="test_cross",
        week=5,
        character_id=char_a.character_id,
        event_type="confession"
    )
    
    results = butterfly.trigger_event_effects(
        event,
        {char_a.character_id: char_a, char_b.character_id: char_b}
    )
    
    print(f"角色A好感度: {char_a.affection:.1f} -> 觸發事件")
    print(f"角色B好感度: 50.0 -> {char_b.affection:.1f}")
    print(f"角色B火花: 0.0 -> {char_b.bond.spark:.1f}")
    print(f"觸發效果: {results}")
    
    assert char_b.affection > 50, "角色B好感度應增加"
    assert char_b.bond.spark > 0, "角色B火花應增加"
    
    print("\n✓ 跨角色蝴蝶效應測試通過\n")


def test_producer_influence():
    """測試製作人對角色的影響"""
    print("=" * 60)
    print("測試製作人影響力")
    print("=" * 60)
    
    balance = BalanceEngine()
    producer = ProducerSystem(balance)
    
    # 創建角色
    char = CharacterStats(name="參賽者")
    char.popularity = 50
    char.affection = 60
    
    print(f"初始狀態: 好感度={char.affection}, 人氣={char.popularity}")
    
    # 正面剪輯
    producer.apply_character_editing(char, 0.8, duration=3)
    print(f"正面剪輯後: 好感度={char.affection:.1f}, 人氣={char.popularity:.1f}")
    
    # 負面剪輯
    producer.apply_character_editing(char, -0.6, duration=2)
    print(f"負面剪輯後: 好感度={char.affection:.1f}, 人氣={char.popularity:.1f}")
    
    # 宣傳決策
    from src.engine.types import ProducerDecisionType
    producer.make_decision(
        ProducerDecisionType.PUBLICITY,
        [char],
        {"publicity_boost": 20, "affection": 5}
    )
    print(f"宣傳決策後: 好感度={char.affection:.1f}, 人氣={char.popularity:.1f}")
    
    # 獲取公眾印象
    perception = producer.calculate_public_perception(char)
    print(f"\n公眾印象:")
    print(f"  基礎印象: {perception['base_perception']}")
    print(f"  剪輯印象: {perception['editing_perception']}")
    print(f"  綜合印象: {perception['overall']}")
    
    print("\n✓ 製作人影響力測試通過\n")


def test_stress_crisis():
    """測試壓力危機系統"""
    print("=" * 60)
    print("測試壓力危機系統")
    print("=" * 60)
    
    engine = BalanceEngine()
    char = CharacterStats(name="壓力角色")
    
    print(f"初始壓力: {char.stress}")
    
    # 累積壓力
    for i in range(10):
        engine.update_stress(char, 10)
        print(f"壓力+10: {char.stress:.1f} (等級: {char.stress_level()})")
        
        if engine.check_stress_crisis(char):
            print(f"\n⚠️ 第 {i+1} 次累積後觸發壓力危機！")
            # 觸發危機效果
            engine.update_stress(char, -30)
            engine.update_affection(char, -10)
            print(f"危機後: 壓力={char.stress:.1f}, 好感度={char.affection:.1f}")
    
    print("\n✓ 壓力危機系統測試通過\n")


def test_weekly_decay():
    """測試每週衰減機制"""
    print("=" * 60)
    print("測試每週衰減機制")
    print("=" * 60)
    
    engine = BalanceEngine()
    char = CharacterStats(name="衰減角色")
    char.affection = 80
    
    print(f"初始好感度: {char.affection}")
    
    for week in range(1, 11):
        old_aff = char.affection
        engine.apply_weekly_decay(char, week)
        decay = old_aff - char.affection
        print(f"第 {week} 週: 好感度 {old_aff:.1f} -> {char.affection:.1f} (衰減 {decay:.1f})")
    
    print(f"\n10週後總衰減: {80 - char.affection:.1f}")
    assert char.affection < 80, "好感度應隨時間衰減"
    
    print("\n✓ 每週衰減機制測試通過\n")


if __name__ == "__main__":
    print("遊戲引擎進階測試套件")
    print("=" * 60)
    
    test_s_plus_ending()
    test_all_grades()
    test_butterfly_cross_character()
    test_producer_influence()
    test_stress_crisis()
    test_weekly_decay()
    
    print("\n" + "=" * 60)
    print("所有進階測試通過！")
    print("=" * 60)
