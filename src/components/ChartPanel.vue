<template>
  <div class="chart-panel">
    <div class="chart-toolbar">
      <div class="timeframe-group">
        <button
          v-for="d in timeframes"
          :key="d.value"
          :class="['tf-btn', { active: days === d.value }]"
          @click="setDays(d.value)"
        >
          {{ d.label }}
        </button>
      </div>
      <div class="chart-status" v-if="loading">
        <span class="spinner"></span> 載入中...
      </div>
      <div class="chart-status error" v-else-if="error">
        ⚠ {{ error }}
      </div>
    </div>
    <div ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { createChart, CrosshairMode } from 'lightweight-charts'
import { useCryptoPrice } from '../composables/useCryptoPrice.js'
import { calcSMA, calcRSI } from '../composables/usePrediction.js'

const props = defineProps({
  coinId: { type: String, required: true },
  days: { type: Number, default: 7 },
})

const emit = defineEmits(['price-update'])

const { loading, error, fetchOHLC, fetchCurrentPrice } = useCryptoPrice()

const timeframes = [
  { label: '1天', value: 1 },
  { label: '7天', value: 7 },
  { label: '30天', value: 30 },
  { label: '90天', value: 90 },
]

const chartContainer = ref(null)
const days = ref(props.days)
let chart = null
let candlestickSeries = null
let sma20Series = null
let sma50Series = null
let rsiSeries = null

function setDays(d) {
  days.value = d
  loadData()
}

async function loadData() {
  if (!chart) return

  const data = await fetchOHLC(props.coinId, days.value)
  if (data.length === 0) return

  // Update candlestick series
  candlestickSeries.setData(data)

  // Update SMA lines
  const sma20 = calcSMA(data, 20).filter(p => p.value !== null)
  const sma50 = calcSMA(data, 50).filter(p => p.value !== null)
  sma20Series.setData(sma20)
  sma50Series.setData(sma50)

  // RSI in a separate pane
  const rsiData = calcRSI(data, 14).filter(p => p.value !== null)
  rsiSeries.setData(rsiData)

  chart.timeScale().fitContent()

  // Emit latest price for the prediction panel
  const last = data[data.length - 1]
  emit('price-update', { open: last.open, high: last.high, low: last.low, close: last.close })
}

watch(() => props.coinId, () => {
  // Clear existing data and reload
  if (candlestickSeries) candlestickSeries.setData([])
  if (sma20Series) sma20Series.setData([])
  if (sma50Series) sma50Series.setData([])
  if (rsiSeries) rsiSeries.setData([])
  nextTick(loadData)
})

onMounted(() => {
  chart = createChart(chartContainer.value, {
    layout: {
      background: { color: '#1a1a2e' },
      textColor: '#a0a0c0',
    },
    grid: {
      vertLines: { color: '#2d2d44' },
      horzLines: { color: '#2d2d44' },
    },
    crosshair: { mode: CrosshairMode.Normal },
    rightPriceScale: { borderColor: '#3a3a5a' },
    timeScale: {
      borderColor: '#3a3a5a',
      timeVisible: true,
    },
    width: chartContainer.value.clientWidth,
    height: 480,
  })

  candlestickSeries = chart.addCandlestickSeries({
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderUpColor: '#26a69a',
    borderDownColor: '#ef5350',
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
  })

  sma20Series = chart.addLineSeries({
    color: '#f7931a',
    lineWidth: 2,
    title: 'SMA 20',
    priceLineVisible: false,
  })

  sma50Series = chart.addLineSeries({
    color: '#8b5cf6',
    lineWidth: 2,
    title: 'SMA 50',
    priceLineVisible: false,
  })

  // RSI pane
  const rsiPane = chart.addPane(0)
  chart.paneSize(rsiPane, 0.2)

  rsiSeries = chart.addLineSeries({
    color: '#00bcd4',
    lineWidth: 1,
    title: 'RSI 14',
    priceLineVisible: false,
  })

  // Override rsiSeries to add overbought/oversold reference lines
  rsiSeries.createPriceLine({
    price: 70,
    color: '#ef5350',
    lineStyle: 2, // Dashed
    title: '超買 70',
  })
  rsiSeries.createPriceLine({
    price: 30,
    color: '#26a69a',
    lineStyle: 2,
    title: '超賣 30',
  })

  // Move RSI series to the new pane
  chart.moveSeriesToPane(rsiSeries, rsiPane)

  loadData()

  // Poll current price every 60s
  const pollInterval = setInterval(async () => {
    const price = await fetchCurrentPrice(props.coinId)
    if (price) emit('price-update', { close: price })
  }, 60000)

  // Resize handler
  const onResize = () => {
    if (chart && chartContainer.value) {
      chart.resize(chartContainer.value.clientWidth, 480)
    }
  }
  window.addEventListener('resize', onResize)

  // Cleanup
  onUnmounted(() => {
    clearInterval(pollInterval)
    window.removeEventListener('resize', onResize)
    if (chart) chart.remove()
    chart = null
  })
})
</script>

<style scoped>
.chart-panel {
  background: #1a1a2e;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #2a2a3e;
}

.chart-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #16162a;
  border-bottom: 1px solid #2a2a3e;
}

.timeframe-group {
  display: flex;
  gap: 4px;
}

.tf-btn {
  background: transparent;
  color: #a0a0c0;
  border: 1px solid #3a3a5a;
  padding: 5px 14px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.tf-btn:hover {
  background: #2a2a4e;
  color: #fff;
}

.tf-btn.active {
  background: #8b5cf6;
  color: #fff;
  border-color: #8b5cf6;
}

.chart-status {
  font-size: 13px;
  color: #a0a0c0;
}

.chart-status.error {
  color: #ef5350;
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

.chart-container {
  width: 100%;
  height: 480px;
}
</style>
