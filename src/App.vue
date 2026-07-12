<template>
  <div class="app">
    <header class="header">
      <div class="header-left">
        <h1 class="logo">🔮 CRYPTO預測助手</h1>
      </div>
      <div class="header-right">
        <select v-model="selectedCoin" class="coin-select" @change="onCoinChange">
          <option v-for="c in coins" :key="c.id" :value="c.id">{{ c.name }} ({{ c.symbol.toUpperCase() }})</option>
        </select>
      </div>
    </header>

    <main class="main">
      <ChartPanel
        :coin-id="selectedCoin"
        :days="days"
        @price-update="onPriceUpdate"
      />
      <PredictionPanel
        :current-price="currentPrice"
        :coin-id="selectedCoin"
      />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ChartPanel from './components/ChartPanel.vue'
import PredictionPanel from './components/PredictionPanel.vue'

const coins = [
  { id: 'bitcoin', name: 'Bitcoin', symbol: 'btc' },
  { id: 'ethereum', name: 'Ethereum', symbol: 'eth' },
  { id: 'solana', name: 'Solana', symbol: 'sol' },
  { id: 'ripple', name: 'XRP', symbol: 'xrp' },
  { id: 'cardano', name: 'Cardano', symbol: 'ada' },
  { id: 'dogecoin', name: 'Dogecoin', symbol: 'doge' },
  { id: 'polkadot', name: 'Polkadot', symbol: 'dot' },
  { id: 'avalanche-2', name: 'Avalanche', symbol: 'avax' },
]

const selectedCoin = ref('bitcoin')
const days = ref(7)
const currentPrice = ref(null)

function onCoinChange() {
  currentPrice.value = null
}

function onPriceUpdate(price) {
  currentPrice.value = price
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: #0f0f1a;
  color: #e0e0e0;
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  min-height: 100vh;
}

.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0 20px;
  border-bottom: 1px solid #2a2a3e;
  margin-bottom: 20px;
}

.logo {
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, #f7931a, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.coin-select {
  background: #1e1e32;
  color: #e0e0e0;
  border: 1px solid #3a3a5a;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  outline: none;
  min-width: 180px;
}

.coin-select:focus {
  border-color: #8b5cf6;
}

.main {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
