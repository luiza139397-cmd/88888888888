from statistics import mean


def calculate_signal(candles):
    if not candles or len(candles) < 16:
        return None, "Sem velas suficientes."

    try:
        analysis_candles = candles[:-1]
        closes = [candle["close"] for candle in analysis_candles]
        opens = [candle["open"] for candle in analysis_candles]

        fast_price = closes[-1]
        slow_avg = mean(closes[-5:])
        previous_fast = closes[-2]
        previous_slow = mean(closes[-6:-1])

        current_diff = fast_price - slow_avg
        previous_diff = previous_fast - previous_slow
        momentum = mean([closes[i] - opens[i] for i in range(-3, 0)])

        if previous_diff <= 0 and current_diff > 0 and momentum > 0:
            return "call", "Virada compradora detectada."
        if previous_diff >= 0 and current_diff < 0 and momentum < 0:
            return "put", "Virada vendedora detectada."
    except Exception as exc:
        return None, f"Erro ao calcular sinal: {exc}"

    return None, "Sem sinal claro no momento."
