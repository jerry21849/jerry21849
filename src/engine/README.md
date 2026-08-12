# 遊戲引擎模組 (Game Engine Module)

## 概覽

本模組實現了遊戲的核心系統，包括數值平衡、結局評分、蝴蝶效應和製作人系統。

## 目錄結構

```
src/engine/
├── __init__.py      # 模組入口，暴露所有公共 API
├── types.py         # 類型定義
├── constants.py     # 常量與平衡設定
├── balance.py       # 數值平衡系統
├── scoring.py       # 結局評分系統
├── butterfly.py     # 蝴蝶效應引擎
└── producer.py      # 公信系統（製作人視角）
```

## 核心系統

### 1. 數值平衡系統 (`balance.py`)

負責管理所有角色數值的變化與平衡。

**數值範圍：**
- 好感度：0-100，每週自然衰減 5-10
- 羈絆四維（溫暖/信任/火花/拉扯）：各 0-100
- 人氣值：0-100
- 情緒四軸（喜悅/思念/焦慮/勇氣）：各 -50 到 +50
- 壓力系統：累積到 100 會觸發危機事件

**主要方法：**
```python
engine = BalanceEngine()

# 更新好感度
engine.update_affection(character, delta)

# 每週衰減
engine.apply_weekly_decay(character, week)

# 應用選擇效果
engine.apply_choice_effect(character, "positive_medium")

# 獲取每週更新摘要
weekly = engine.process_weekly_update(character, week)
```

### 2. 結局評分系統 (`scoring.py`)

根據角色數值計算結局分數，評定等級（S+ 到 D-）。

**評分維度：**
- 好感度得分 (0-25)
- 羈絆得分 (0-25)
- 情緒狀態得分 (0-20)
- 關鍵選擇正確率 (0-20)
- 隱藏條件達成 (0-15)

**結局等級：**
| 等級 | 描述 | 最低分數 |
|------|------|----------|
| S+ | 完美：所有條件完美達成，隱藏路線解鎖 | 95 |
| S | 極佳：主要條件達成，有 minor 遺憾 | 85 |
| A+ | 很好：大部分條件達成 | 75 |
| A | 好：基本條件達成 | 65 |
| B+ | 不錯：有明顯缺點但可接受 | 55 |
| B | 普通：平庸的結局 | 45 |
| C+ | 不太好：有問題但還能接受 | 35 |
| C | 不好：明顯的問題 | 25 |
| D+ | 差：失敗的結局 | 15 |
| D- | 最差：完全失敗 | 0 |

**主要方法：**
```python
engine = ScoringEngine()

# 獲取評分報告
report = engine.generate_report(character)
# 返回: {"grade": "S+", "total_score": 95.6, ...}

# 比較多個角色
results = engine.compare_characters([char_a, char_b, char_c])
```

### 3. 蝴蝶效應引擎 (`butterfly.py`)

實現跨角色的數值影響，支持多重觸發路徑和隱藏結局。

**影響機制：**
- 角色 A 的選擇會以 20-40% 的權重影響角色 B
- 影響力基於角色狀態動態計算
- 支持效應鏈傳播

**主要方法：**
```python
engine = ButterflyEngine(balance_engine)

# 註冊蝴蝶效應
effect = ButterflyEffect(
    rule_id="confession_effect",
    source_character=char_a.character_id,
    target_character=char_b.character_id,
    trigger_event="confession",
    weight=0.3,
    stat_modifiers={"affection": 10, "bond_spark": 5}
)
engine.register_effect(effect)

# 觸發事件效果
results = engine.trigger_event_effects(event, characters)

# 檢查隱藏結局
hidden = engine.check_hidden_ending(characters)
```

### 4. 製作人系統 (`producer.py`)

模擬製作人的決策影響，包括剪輯傾向和公眾印象。

**主要功能：**
- 剪輯傾向影響角色形象
- 製作人決策改變角色數值
- 規則事件改變賽制
- 公眾印象計算

**主要方法：**
```python
system = ProducerSystem(balance_engine)

# 設置剪輯傾向
system.set_editing_tendency(0.5)  # -1 到 +1

# 應用剪輯效果
effect = system.apply_character_editing(character, 0.7, duration=2)

# 製作人決策
decision = system.make_decision(
    ProducerDecisionType.PUBLICITY,
    [character],
    {"publicity_boost": 15}
)

# 獲取公眾印象
perception = system.calculate_public_perception(character)
```

## 快速開始

```python
from src.engine import create_game_engine

# 創建完整引擎
engine = create_game_engine()

# 創建角色
from src.engine import CharacterStats
char = CharacterStats(name="小明")

# 模擬遊戲過程
for week in range(1, 11):
    # 每週更新
    engine["balance"].process_weekly_update(char, week)
    
    # 應用選擇效果
    engine["balance"].apply_choice_effect(char, "positive_medium")

# 最終評分
report = engine["scoring"].generate_report(char)
print(f"結局: {report['grade']}")
```

## 選擇效果類型

| 類型 | 好感度 | 羈絆 | 情緒 | 壓力 |
|------|--------|------|------|------|
| positive_small | +5 | +3 | +5 | -3 |
| positive_medium | +10 | +5 | +8 | -5 |
| positive_large | +15 | +8 | +12 | -8 |
| negative_small | -5 | +3 | +5 | +5 |
| negative_medium | -10 | -5 | +8 | +10 |
| negative_large | -15 | -8 | +12 | +15 |
| brave | +3 | +5 | +10 | -2 |
| risky | +8 | +10 | +5 | +8 |

## 隱藏結局條件

| 結局 | 條件 |
|------|------|
| true_end | 所有角色好感度 >= 90，至少一個角色羈絆全滿 |
| secret_bond | 特定角色組合火花 >= 80 且信任 >= 80 |
| perfect_harmony | 所有角色情緒穩定且正面 |

## 測試

運行測試套件：
```bash
# 基本測試
python tests/test_engine.py

# 進階測試
python tests/test_engine_advanced.py
```

## 注意事項

1. 好感度會隨時間自然衰減，需要持續互動維持
2. 壓力累積到 100 會觸發危機事件，影響所有數值
3. 蝴蝶效應的影響力會根據角色狀態動態調整
4. 製作人的剪輯傾向會累積影響角色的公眾形象
5. 隱藏結局需要跨角色的特定組合才能達成
