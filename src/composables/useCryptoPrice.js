import { ref, computed } from 'vue'

const COINGECKO_BASE = 'https://api.coingecko.com/api/v3'

// Cache keyed by `${coinId}-${days}`
const ohlcCache = new Map()

export function useCryptoPrice() {
  const loading = ref(false)
  const error = ref(null)

  async function fetchOHLC(coinId, days = 7) {
    const cacheKey = `${coinId}-${days}`
    const cached = ohlcCache.get(cacheKey)
    if (cached) return cached

    loading.value = true
    error.value = null

    const url = `${COINGECKO_BASE}/coins/${coinId}/ohlc?vs_currency=usd&days=${days}`

    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const res = await fetch(url)
        if (!res.ok) {
          if (res.status === 429) {
            // Rate limited – wait and retry
            await new Promise(r => setTimeout(r, 1000 * (attempt + 1)))
            continue
          }
          throw new Error(`HTTP ${res.status}: ${res.statusText}`)
        }
        const json = await res.json()
        // json is an array of [timestamp_ms, open, high, low, close]
        const data = json.map(([t, open, high, low, close]) => ({
          time: Math.floor(t / 1000),
          open,
          high,
          low,
          close,
        }))
        ohlcCache.set(cacheKey, data)
        return data
      } catch (e) {
        error.value = e.message
        if (attempt < 2) await new Promise(r => setTimeout(r, 1000))
      }
    }
    return []
  }

  async function fetchCurrentPrice(coinId) {
    const url = `${COINGECKO_BASE}/simple/price?ids=${coinId}&vs_currencies=usd`
    try {
      const res = await fetch(url)
      if (!res.ok) return null
      const json = await res.json()
      return json[coinId]?.usd ?? null
    } catch {
      return null
    }
  }

  return { loading, error, fetchOHLC, fetchCurrentPrice }
}
