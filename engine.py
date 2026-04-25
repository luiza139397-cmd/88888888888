import threading
import time
from datetime import datetime

from config import CHART_CANDLE_LIMIT, MAIN_LOOP_SLEEP_SECONDS, SIGNAL_PREPARE_SECONDS, STATUS_INTERVAL_SECONDS, TIMEFRAME_SECONDS
from signals import calculate_signal


class BotEngine:
    def __init__(self, log_callback, status_callback, signal_callback, chart_callback, result_callback):
        self.log_callback = log_callback
        self.status_callback = status_callback
        self.signal_callback = signal_callback
        self.chart_callback = chart_callback
        self.result_callback = result_callback
        self.running = False
        self.thread = None
        self.last_signal_keys = set()
        self.pending_entries = {}
        self.prepare_seconds = SIGNAL_PREPARE_SECONDS

    def start(self, platforms, assets, amount, expiration, telegram_service, auto_trade, prepare_seconds):
        if self.running:
            return False, "O bot ja esta rodando."

        self.running = True
        self.last_signal_keys.clear()
        self.pending_entries.clear()
        self.prepare_seconds = prepare_seconds
        self.thread = threading.Thread(
            target=self._run,
            args=(platforms, assets, amount, expiration, telegram_service, auto_trade),
            daemon=True,
        )
        self.thread.start()
        return True, "Bot iniciado."

    def stop(self):
        self.running = False
        return True, "Bot parado."

    def _log(self, message):
        self.log_callback(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def _set_status(self, message):
        self.status_callback(message)

    def _run(self, platforms, assets, amount, expiration, telegram_service, auto_trade):
        self._set_status("Conectando plataformas...")

        for platform in platforms:
            ok, message = platform.connect()
            if ok:
                self._log(f"{platform.name}: {message}")
            else:
                self._log(f"{platform.name}: {message}")

        self._set_status("Bot ativo e monitorando.")
        next_status = 0

        while self.running:
            now = time.time()
            if now >= next_status:
                self._log("Loop ativo. Continuando a busca por sinais.")
                next_status = now + STATUS_INTERVAL_SECONDS

            self._execute_pending_entries(amount, expiration)

            for platform in platforms:
                for asset in assets:
                    if not self.running:
                        break
                    self._process_asset(platform, asset, amount, expiration, telegram_service, auto_trade, now)

            time.sleep(MAIN_LOOP_SLEEP_SECONDS)

        self._set_status("Bot desligado.")

    def _process_asset(self, platform, asset, amount, expiration, telegram_service, auto_trade, now):
        try:
            candles = platform.get_candles(asset)
            if not candles:
                self._log(f"{platform.name} | {asset}: sem velas retornadas.")
                return

            self.chart_callback(platform.name, asset, candles[-CHART_CANDLE_LIMIT:])
            seconds_until_close = self._seconds_until_next_candle(now)
            current_candle = candles[-1]
            current_candle_id = current_candle.get("id", current_candle.get("from", "sem-id"))

            if seconds_until_close > self.prepare_seconds:
                return

            signal, reason = calculate_signal(candles)
            if not signal:
                return

            signal_key = f"{platform.name}:{asset}:{current_candle_id}:{signal}"
            if signal_key in self.last_signal_keys:
                return
            self.last_signal_keys.add(signal_key)

            entry_time = self._next_candle_open(now)
            direction_label = "CALL" if signal == "call" else "PUT"
            message = (
                f"SINAL PREPARADO\n"
                f"Plataforma: {platform.name}\n"
                f"Ativo: {asset}\n"
                f"Direcao: {direction_label}\n"
                f"Entrada prevista: {datetime.fromtimestamp(entry_time).strftime('%H:%M:%S')}\n"
                f"Motivo: {reason}"
            )

            self._log(message.replace("\n", " | "))
            self.signal_callback(message)
            self.result_callback("signal", {"platform": platform.name, "asset": asset})

            if telegram_service.is_ready():
                ok, tg_message = telegram_service.send(message)
                self._log(f"Telegram: {tg_message}")
                if not ok:
                    self._set_status("Falha no Telegram.")

            if auto_trade:
                entry_key = f"{platform.name}:{asset}"
                self.pending_entries[entry_key] = {
                    "platform": platform,
                    "asset": asset,
                    "signal": signal,
                    "amount": amount,
                    "expiration": expiration,
                    "entry_time": entry_time,
                }
                self._log(
                    f"{platform.name} | {asset}: operacao agendada para {datetime.fromtimestamp(entry_time).strftime('%H:%M:%S')}."
                )
                self._set_status(f"Operacao agendada em {platform.name} para a proxima vela.")
        except Exception as exc:
            self._log(f"{platform.name} | {asset}: erro durante analise: {exc}")

    def _execute_pending_entries(self, amount, expiration):
        if not self.pending_entries:
            return

        now = time.time()
        ready_keys = [key for key, data in self.pending_entries.items() if now >= data["entry_time"]]
        for key in ready_keys:
            data = self.pending_entries.pop(key)
            platform = data["platform"]
            asset = data["asset"]
            signal = data["signal"]

            self._set_status(f"Entrando na abertura da vela em {platform.name}...")
            ok, order_id, trade_message = platform.place_order(
                asset,
                signal,
                data["amount"],
                data["expiration"],
            )
            self._log(f"{platform.name} | {asset}: {trade_message}")
            if not ok or not order_id:
                self._set_status("Falha ao executar entrada no tempo.")
                continue
            self._wait_result(platform, order_id, asset)

    def _wait_result(self, platform, order_id, asset, timeout=25):
        started = time.time()
        self._set_status(f"Aguardando resultado em {platform.name}...")
        while self.running and (time.time() - started) < timeout:
            result = platform.check_result(order_id)
            if result is None:
                time.sleep(1)
                continue

            if result > 0:
                self._log(f"{platform.name} | {asset}: WIN de R${result:.2f}")
            else:
                self._log(f"{platform.name} | {asset}: LOSS de R${result:.2f}")
            self.result_callback(
                "trade_result",
                {"platform": platform.name, "asset": asset, "result": result},
            )
            self._set_status("Bot ativo e monitorando.")
            return

        self._log(f"{platform.name} | {asset}: resultado nao voltou a tempo, seguindo o loop.")
        self._set_status("Bot ativo e monitorando.")

    def _seconds_until_next_candle(self, now):
        return TIMEFRAME_SECONDS - (int(now) % TIMEFRAME_SECONDS)

    def _next_candle_open(self, now):
        return now - (now % TIMEFRAME_SECONDS) + TIMEFRAME_SECONDS
