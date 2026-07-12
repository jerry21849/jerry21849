/**
 * Compute a Simple Moving Average over `period` bars.
 * Returns an array of {time, value} the same length as `data`,
 * with nulls for the first (period-1) entries.
 */
export function calcSMA(data, period) {
  if (!data || data.length < period) return []
  const result = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push({ time: data[i].time, value: null })
      continue
    }
    let sum = 0
    for (let j = i - period + 1; j <= i; j++) {
      sum += data[j].close
    }
    result.push({ time: data[i].time, value: sum / period })
  }
  return result
}

/**
 * Compute RSI over `period` bars using Wilder's smoothing.
 * Returns an array of {time, value} with nulls for the first `period` entries.
 */
export function calcRSI(data, period = 14) {
  if (!data || data.length <= period) return []
  const result = []
  let avgGain = 0
  let avgLoss = 0

  // First RSI value uses simple average of gains/losses
  for (let i = 1; i <= period; i++) {
    const diff = data[i].close - data[i - 1].close
    if (diff >= 0) avgGain += diff
    else avgLoss -= diff
  }
  avgGain /= period
  avgLoss /= period

  // pad nulls
  for (let i = 0; i <= period; i++) {
    result.push({ time: data[i].time, value: null })
  }

  let rs = avgLoss === 0 ? 999 : avgGain / avgLoss
  result[period].value = 100 - 100 / (1 + rs)

  for (let i = period + 1; i < data.length; i++) {
    const diff = data[i].close - data[i - 1].close
    const gain = diff >= 0 ? diff : 0
    const loss = diff < 0 ? -diff : 0
    avgGain = (avgGain * (period - 1) + gain) / period
    avgLoss = (avgLoss * (period - 1) + loss) / period
    rs = avgLoss === 0 ? 999 : avgGain / avgLoss
    result.push({ time: data[i].time, value: 100 - 100 / (1 + rs) })
  }

  return result
}

/**
 * Find local support and resistance levels by scanning for pivot highs/lows
 * over the last `lookback` bars. Returns { support, resistance }.
 */
export function calcSupportResistance(data, lookback = 20) {
  if (!data || data.length < lookback * 2) return { support: null, resistance: null }

  const slice = data.slice(-lookback)
  let lowest = Infinity
  let highest = -Infinity
  for (const bar of slice) {
    if (bar.low < lowest) lowest = bar.low
    if (bar.high > highest) highest = bar.high
  }

  // Use recent close as anchor to refine
  const recentClose = data[data.length - 1].close
  const band = (highest - lowest) * 0.15
  let resistance = null
  let support = null

  // Resistance: highest point above current price, or fallback to highest
  const pivotsHigh = []
  for (let i = 2; i < slice.length; i++) {
    if (slice[i].high > slice[i - 1].high && slice[i].high > slice[i - 2].high) {
      pivotsHigh.push(slice[i].high)
    }
  }
  resistance = pivotsHigh.length > 0
    ? pivotsHigh.reduce((a, b) => a > b ? a : b)
    : highest

  const pivotsLow = []
  for (let i = 2; i < slice.length; i++) {
    if (slice[i].low < slice[i - 1].low && slice[i].low < slice[i - 2].low) {
      pivotsLow.push(slice[i].low)
    }
  }
  support = pivotsLow.length > 0
    ? pivotsLow.reduce((a, b) => a < b ? a : b)
    : lowest

  return {
    support: Math.floor(support * 100) / 100,
    resistance: Math.ceil(resistance * 100) / 100,
  }
}

/**
 * Generate a trading signal from the calculated indicators.
 * Returns { signal: 'buy' | 'sell' | 'hold', confidence: 0-100, detail: string }
 */
export function generateSignal(data) {
  if (!data || data.length < 50) return { signal: 'hold', confidence: 0, detail: '資料不足，無法計算' }

  const close = data.map(d => d.close)
  const lastPrice = close[close.length - 1]

  // RSI
  const rsiArr = calcRSI(data, 14)
  const lastRSI = rsiArr.length > 0 ? rsiArr[rsiArr.length - 1].value : 50

  // SMA20 / SMA50
  const sma20 = calcSMA(data, 20)
  const sma50 = calcSMA(data, 50)
  const lastSMA20 = sma20.length > 0 ? sma20[sma20.length - 1].value : null
  const lastSMA50 = sma50.length > 0 ? sma50[sma50.length - 1].value : null

  // Trend: compare last 3 closes
  const shortTrend = close[close.length - 1] > close[close.length - 3] ? 'up' : 'down'

  let score = 50 // neutral baseline

  // RSI scoring
  if (lastRSI !== null) {
    if (lastRSI < 30) score += 20  // oversold → bullish
    else if (lastRSI < 40) score += 10
    else if (lastRSI > 70) score -= 20 // overbought → bearish
    else if (lastRSI > 60) score -= 10
  }

  // SMA crossover scoring
  if (lastSMA20 !== null && lastSMA50 !== null) {
    if (lastPrice > lastSMA20) score += 5
    if (lastPrice > lastSMA50) score += 5
    if (lastSMA20 > lastSMA50) score += 5 // bullish alignment
    else score -= 5
  }

  // Trend scoring
  if (shortTrend === 'up') score += 5
  else score -= 5

  score = Math.max(0, Math.min(100, score))

  let signal, detail
  if (score >= 65) {
    signal = 'buy'
    detail = `多頭訊號 (RSI: ${lastRSI?.toFixed(1) ?? 'N/A'}, 價格${lastSMA20 !== null && lastPrice > lastSMA20 ? '' : '略'}高於20日均線)`
  } else if (score <= 35) {
    signal = 'sell'
    detail = `空頭訊號 (RSI: ${lastRSI?.toFixed(1) ?? 'N/A'}, 價格${lastSMA20 !== null && lastPrice < lastSMA20 ? '' : '略'}低於20日均線)`
  } else {
    signal = 'hold'
    detail = `盤整觀望 (RSI: ${lastRSI?.toFixed(1) ?? 'N/A'}, 趨勢不明朗)`
  }

  return { signal, confidence: score, detail }
}
