<template>
  <div class="prediction-panel">
    <h2 class="panel-title">📊 預測分析</h2>

    <div v-if="!currentPrice" class="loading-msg">
      <span class="spinner"></span> 等待價格資料...
    </div>

    <template v-else>
      <!-- Current price -->
      <div class="price-row">
        <span class="label">當前價格</span>
        <span class="price-value">${{ formatPrice(priceClose) }}</span>
      </div>

      <!-- Signal -->
      <div class="signal-row" :class="signalClass">
        <span class="label">趨勢訊號</span>
        <span class="signal-badge">{{ signalText }} ({{ signal.confidence }}%)</span>
      </div>

      <div class="signal-detail">{{ signal.detail }}</div>

      <!-- Support / Resistance -->
      <div class="levels-row">
        <div class="level-box">
          <span class="level-label">🟢 支撐位</span>
          <span class="level-value">{{ supportText }}</span>
        </div>
        <div class="level-box">
          <span class="level-label">🔴 壓力位</span>
          <span class="level-value">{{ resistanceText }}</span>
        </div>
      </div>

      <!-- RSI Summary -->
      <div class="indicator-row">
        <span class="label">RSI (14)</span>
        <span class="value" :style="{ color: rsiColor }">{{ rsiValue }}</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useCryptoPrice } from '../composables/useCryptoPrice.js'
import { calcRSI, calcSupportResistance, generateSignal } from '../composables/usePrediction.js'

const props = defineProps({
  coinId: { type: String, required: true },
  currentPrice: { type: Object, default: null },
})

const { fetchOHLC } = useCryptoPrice()
const ohlcData = ref([])

// Load OHLC data for indicator calculation
const loadIndicators = async () => {
  const data = await fetchOHLC(props.coinId, 90)
  if (data && data.length > 0) {
    ohlcData.value = data
  }
}

// Reload when coin changes
watch(() => props.coinId, () => {
  ohlcData.value = []
  loadIndicators()
}, { immediate: true })

// Computed indicators derived from ohlcData
const priceClose = computed(() => {
  if (props.currentPrice) return props.currentPrice.close
  if (ohlcData.value.length > 0) return ohlcData.value[ohlcData.value.length - 1].close
  return null
})

const rsiArr = computed(() => calcRSI(ohlcData.value, 14))
const rsiValue = computed(() => {
  if (rsiArr.value.length === 0) return '--'
  const last = rsiArr.value[rsiArr.value.length - 1].value
  return last !== null ? last.toFixed(1) : '--'
})

const rsiColor = computed(() => {
  const v = parseFloat(rsiValue.value)
  if (isNaN(v)) return '#a0a0c0'
  if (v > 70) return '#ef5350'
  if (v < 30) return '#26a69a'
  return '#e0e0e0'
})

const levels = computed(() => calcSupportResistance(ohlcData.value, 20))
const supportText = computed(() => levels.value.support !== null ? `$${formatPrice(levels.value.support)}` : '--')
const resistanceText = computed(() => levels.value.resistance !== null ? `$${formatPrice(levels.value.resistance)}` : '--')

const signal = computed(() => generateSignal(ohlcData.value))

const signalText = computed(() => {
  switch (signal.value.signal) {
    case 'buy': return '買入'
    case 'sell': return '賣出'
    default: return '持有觀望'
  }
})

const signalClass = computed(() => {
  return `signal-${signal.value.signal}`
})

function formatPrice(val) {
  if (val == null) return '--'
  if (val >= 100) return val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (val >= 1) return val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })
  return val.toLocaleString(undefined, { minimumFractionDigits: 4, maximumFractionDigits: 8 })
}
</script>

<style scoped>
.prediction-panel {
  background: #1a1a2e;
  border: 1px solid #2a2a3e;
  border-radius: 12px;
  padding: 20px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #c0c0e0;
}

.loading-msg {
  color: #707090;
  font-size: 14px;
}

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid #3a3a5a;
  border-top-color: #8b5cf6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  vertical-align: middle;
  margin-right: 6px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.price-row,
.signal-row,
.indicator-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #2a2a3e;
}

.price-row {
  border-bottom: none;
  padding-top: 0;
}

.label {
  color: #8080a0;
  font-size: 14px;
}

.price-value {
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
}

.signal-badge {
  font-weight: 700;
  font-size: 16px;
}

.signal-buy .signal-badge { color: #26a69a; }
.signal-sell .signal-badge { color: #ef5350; }
.signal-hold .signal-badge { color: #ffb74d; }

.signal-detail {
  font-size: 13px;
  color: #8080a0;
  margin: 8px 0 12px;
  line-height: 1.5;
}

.levels-row {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.level-box {
  flex: 1;
  background: #16162a;
  border: 1px solid #2a2a3e;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.level-label {
  font-size: 12px;
  color: #8080a0;
}

.level-value {
  font-size: 16px;
  font-weight: 600;
  color: #e0e0e0;
}

.value {
  font-weight: 600;
  font-size: 15px;
}
</style>
