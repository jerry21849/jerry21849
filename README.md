# 加密貨幣多代理智能助手 (Crypto Crew)

一站式「研究 + 預測 + 回測 + Paper Trading」AI 助手。  
採用 **CrewAI** 多代理架構，**全部數據源鎖定免費層**。

## 功能

- 🎯 **市場數據** — CoinGecko + Binance 免費 API 即時報價
- 📰 **新聞摘要** — onchainos CLI / CryptoCompare 頭條 + 影響評級
- 🔬 **技術分析** — 本地 `ta` 庫計算 RSI、MACD、布林、SMA、ATR 等
- ⛓️ **鏈上基本面** — DefiLlama TVL + 項目健康度
- 💬 **市場情緒** — Fear & Greed 指數 + X 社群情緒
- 🔮 **價格預測** — 綜合多維度數據，多空雙面觀點
- 📈 **回測** — RSI / MA 交叉 / 布林帶策略回測（Sharpe、MaxDD、勝率）
- ⚠️ **風險管理** — VaR、ATR、波動率、倉位建議
- 💼 **Paper Trading** — 模擬交易（0.1% 手續費 + 滑點、狀態持久化）

## 安裝

```bash
# 1. 建立虛擬環境
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. 安裝
pip install -e ".[dev]"

# 3. 配置 LLM
cp .env.example .env
# 編輯 .env，填入你的 OPENAI_API_KEY
```

## 免責聲明

> ⚠️ **本分析僅供參考，不是財務建議。加密貨幣波動極大，投資有虧損風險，請自行研究（DYOR）。預測準確率無法保證。**

每次輸出皆自動附加此免責聲明。

## 使用

### CLI 模式

```bash
# 基本分析
python -m crypto_crew "分析 BTC"

# 完整分析 + 回測 + Paper Trading
python -m crypto_crew "分析 ETH，給我未來 7 天預測，回測 RSI 策略，開始 Paper Trading"

# 指定風險偏好
python -m crypto_crew "分析 SOL" --risk aggressive

# 指定初始資金
python -m crypto_crew "分析 BTC" --cash 50000

# 互動模式（不帶參數）
python -m crypto_crew
```

## 數據源

| 來源 | 類型 | 是否需要金鑰 |
|------|------|-------------|
| CoinGecko API | 價格、歷史 OHLCV | ❌ 免費 |
| Binance API | 價格、K 線（備用） | ❌ 免費 |
| alternative.me | Fear & Greed 指數 | ❌ 免費 |
| DefiLlama | TVL、鏈上數據 | ❌ 免費 |
| CryptoCompare | 新聞 | ❌ 免費額度 |
| onchainos CLI | 新聞、情緒（本機） | ❌ 免費額度 |
| agent-reach / twitter CLI | X 社群情緒（本機） | ❌ 免費（需登入） |

## 開發

```bash
# 安裝 dev 依賴
pip install -e ".[dev]"

# 運行測試
pytest -q

# 測試覆蓋率
pytest --cov=crypto_crew -q
```

## 免責聲明（再次強調）

本軟體僅供教育與研究目的。不構成投資建議。加密貨幣交易具有高風險，可能導致資金損失。請自行承擔風險。
