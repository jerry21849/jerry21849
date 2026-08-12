"""
遊戲引擎測試
Game Engine Tests
"""
import sys
import os

# 添加 src 目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.engine import (
    BalanceEngine, ScoringEngine, ButterflyEngine, ProducerSystem,
    CharacterStats, GameEvent, EndingGrade, ProducerDecisionType,
    BondDimension, EmotionAxis, create_game_engine
)


def test_balance_engine():
    """測試數值平衡系統"""
    print("=" * 60)
    print("測試數值平衡系統")
    print("=" * 60)
    
    engine = BalanceEngine()
    
    # 創建測試角色
    char = CharacterStats(name="測試角色")
    print(f"初始好感度: {char.affection}")
    
    # 測試好感度更新
    engine.update_affection(char, 10)
    print(f"增加10後: {char.affection}")
    assert char.affection == 60, f"好感度應為60，實際為{char.affection}"
    
    engine.update_affection(char, -20)
    print(f"減少20後: {char.affection}")
    assert char.affection == 40, f"好感度應為40，實際為{char.affection}"
    
    # 測試羈絆更新
    engine.update_bond(char, BondDimension.WARMTH, 15)
    print(f"溫暖+15後: {char.bond.warmth}")
    assert char.bond.warmth == 15
    
    engine.update_bond(char, BondDimension.TRUST, 20)
    engine.update_bond(char, BondDimension.SPARK, 25)
    engine.update_bond(char, BondDimension.TENSION, 10)
    
    print(f"羈絆總值: {char.bond.total()}")
    
    # 測試情緒更新
    engine.update_emotion(char, EmotionAxis.JOY, 20)
    print(f"喜悅+20後: {char.emotions.joy}")
    assert char.emotions.joy == 20
    
    # 測試壓力
    engine.update_stress(char, 50)
    print(f"壓力+50後: {char.stress}")
    assert char.stress == 50
    
    # 測試選擇效果
    applied = engine.apply_choice_effect(char, "positive_medium")
    print(f"正面中等效果: {applied}")
    
    # 測試每週更新
    weekly = engine.process_weekly_update(char, week=1)
    print(f"每週更新摘要: {weekly}")
    
    print("✓ 數值平衡系統測試通過\n")


def test_scoring_engine():
    """測試結局評分系統"""
    print("=" * 60)
    print("測試結局評分系統")
    print("=" * 60)
    
    engine = ScoringEngine()
    
    # 測試不同等級的角色
    test_cases = [
        ("完美角色", 95, (95, 95, 95, 95), 0.95, {"route_true_end", "all_bonds_max"}),
        ("優秀角色", 80, (80, 80, 70, 70), 0.80, {"route_true_end"}),
        ("普通角色", 50, (50, 50, 50, 50), 0.50, set()),
        ("失敗角色", 20, (20, 20, 10, 10), 0.20, set()),
    ]
    
    for name, aff, bonds, correct_rate, hidden in test_cases:
        char = CharacterStats(name=name)
        char.affection = aff
        char.bond.warmth, char.bond.trust, char.bond.spark, char.bond.tension = bonds
        char.correct_choices = int(correct_rate * 10)
        char.total_choices = 10
        char.hidden_conditions = hidden
        
        report = engine.generate_report(char)
        print(f"\n{name}:")
        print(f"  等級: {report['grade']}")
        print(f"  總分: {report['total_score']}")
        print(f"  細項: {report['score_breakdown']}")
    
    print("\n✓ 結局評分系統測試通過\n")


def test_butterfly_engine():
    """測試蝴蝶效應引擎"""
    print("=" * 60)
    print("測試蝴蝶效應引擎")
    print("=" * 60)
    
    balance = BalanceEngine()
    engine = ButterflyEngine(balance)
    
    # 創建角色
    char_a = CharacterStats(name="角色A")
    char_b = CharacterStats(name="角色B")
    char_a.affection = 70
    char_b.affection = 50
    
    # 註冊蝴蝶效應
    from src.engine.types import ButterflyScope, ButterflyEffect
    
    effect = ButterflyEffect(
        rule_id="test_effect",
        source_character=char_a.character_id,
        target_character=char_b.character_id,
        trigger_event="confession",
        scope=ButterflyScope.DIRECT,
        weight=0.3,
        stat_modifiers={
            "affection": 10,
            "bond_warmth": 5,
        }
    )
    engine.register_effect(effect)
    
    # 觸發效果
    event = GameEvent(
        event_id="test_event",
        week=3,
        character_id=char_a.character_id,
        event_type="confession"
    )
    
    results = engine.trigger_event_effects(
        event,
        {char_a.character_id: char_a, char_b.character_id: char_b}
    )
    
    print(f"觸發效果: {results}")
    print(f"角色B好感度: {char_b.affection}")
    print(f"角色B溫暖: {char_b.bond.warmth}")
    
    assert char_b.affection > 50, "好感度應該增加"
    
    print("\n✓ 蝴蝶效應引擎測試通過\n")


def test_producer_system():
    """測試製作人系統"""
    print("=" * 60)
    print("測試製作人系統")
    print("=" * 60)
    
    balance = BalanceEngine()
    system = ProducerSystem(balance)
    
    # 創建角色
    char = CharacterStats(name="參賽者A")
    char.popularity = 50
    
    # 設置剪輯傾向
    system.set_editing_tendency(0.5)
    print(f"剪輯傾向: {system.state.editing_tendency}")
    
    # 應用剪輯效果
    effect = system.apply_character_editing(char, 0.7, duration=2)
    print(f"剪輯效果: {effect.description}")
    print(f"人氣變化: {effect.popularity_change}")
    
    # 做出決策
    decision = system.make_decision(
        ProducerDecisionType.PUBLICITY,
        [char],
        {"publicity_boost": 15}
    )
    print(f"決策ID: {decision.decision_id}")
    
    # 計算公眾印象
    perception = system.calculate_public_perception(char)
    print(f"公眾印象: {perception}")
    
    # 生成報告
    report = system.generate_producer_report({char.character_id: char})
    print(f"製作人報告: {report}")
    
    print("\n✓ 製作人系統測試通過\n")


def test_full_integration():
    """測試完整整合"""
    print("=" * 60)
    print("測試完整整合")
    print("=" * 60)
    
    # 創建完整引擎
    engine = create_game_engine()
    
    # 創建角色
    characters = {
        "char1": CharacterStats(name="小明"),
        "char2": CharacterStats(name="小紅"),
    }
    
    # 模擬遊戲過程
    for week in range(1, 6):
        print(f"\n--- 第 {week} 週 ---")
        
        for char_id, char in characters.items():
            # 每週更新
            weekly = engine["balance"].process_weekly_update(char, week)
            print(f"{char.name} 週報: 好感度={char.affection:.1f}, 壓力={char.stress:.1f}")
            
            # 隨機選擇效果
            import random
            effect_type = random.choice(["positive_small", "positive_medium", "neutral"])
            engine["balance"].apply_choice_effect(char, effect_type)
    
    # 評分
    print("\n" + "=" * 60)
    print("最終評分")
    print("=" * 60)
    
    for char_id, char in characters.items():
        report = engine["scoring"].generate_report(char)
        print(f"\n{char.name}:")
        print(f"  等級: {report['grade']}")
        print(f"  總分: {report['total_score']:.2f}")
    
    print("\n✓ 完整整合測試通過\n")


if __name__ == "__main__":
    print("遊戲引擎測試套件")
    print("=" * 60)
    
    test_balance_engine()
    test_scoring_engine()
    test_butterfly_engine()
    test_producer_system()
    test_full_integration()
    
    print("\n" + "=" * 60)
    print("所有測試通過！")
    print("=" * 60)
