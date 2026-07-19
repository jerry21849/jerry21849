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
- 📈 **回測** — RSI / MA 交叉 / 布林帶 / 均值回歸 / MACD 柱狀圖
- ⚠️ **風險管理** — VaR、ATR、波動率、倉位建議
- 💼 **Paper Trading** — 模擬交易（0.1% 手續費 + 滑點、多策略隔離、狀態持久化）
- 📦 **組合分析** — 多幣種波動率反向加權配置建議
- 🌐 **Web UI** — Gradio 前端（`python -m crypto_crew web`）

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

# 多幣種組合分析
python -m crypto_crew portfolio --coins btc,eth,sol

# Gradio Web UI
python -m crypto_crew web --port 7860

# 互動模式
python -m crypto_crew
```

也可使用 entry point：`crypto-crew "分析 BTC"`。

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
pip install -e ".[dev]"
pytest -q
```

## 架構備註

- CrewAI hierarchical 流程；Task 之間透過 `context` 傳遞輸出。
- LLM 不可用時自動降級為工具鏈 fallback（仍產出結構化報告）。
- Paper Trading 狀態：`crypto_crew/state/paper_portfolio.json`（支援 `strategy_tag` 多策略隔離）。
- RAG / 預測準確率自動回饋不在當前範圍。

## 免責聲明（再次強調）

本軟體僅供教育與研究目的。不構成投資建議。加密貨幣交易具有高風險，可能導致資金損失。請自行承擔風險。
