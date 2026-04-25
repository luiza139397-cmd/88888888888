import time


class BasePlatform:
    name = "Base"
    supported = False

    def __init__(self, email, password, account_type="PRACTICE"):
        self.email = email.strip()
        self.password = password.strip()
        self.account_type = account_type
        self.connected = False

    def connect(self):
        raise NotImplementedError

    def ensure_connection(self):
        if self.connected:
            return True, "Conexao ja ativa."
        return self.connect()

    def get_candles(self, asset, timeframe_seconds=60, count=20):
        raise NotImplementedError

    def place_order(self, asset, direction, amount, expiration_minutes=1):
        raise NotImplementedError

    def check_result(self, order_id):
        raise NotImplementedError


class IQOptionPlatform(BasePlatform):
    name = "IQ Option"
    supported = True

    def __init__(self, email, password, account_type="PRACTICE"):
        super().__init__(email, password, account_type)
        self.api = None

    def connect(self):
        try:
            from iqoptionapi.stable_api import IQ_Option
        except Exception as exc:
            return False, f"Biblioteca da IQ Option indisponivel: {exc}"

        try:
            self.api = IQ_Option(self.email, self.password)
            ok, reason = self.api.connect()
            if not ok:
                self.connected = False
                return False, f"Falha no login IQ Option: {reason}"
            self.api.change_balance(self.account_type)
            self.connected = True
            return True, "Conectado na IQ Option."
        except Exception as exc:
            self.connected = False
            return False, f"Erro ao conectar na IQ Option: {exc}"

    def ensure_connection(self):
        if self.api is not None:
            try:
                if self.api.check_connect():
                    self.connected = True
                    return True, "Conexao IQ Option ativa."
            except Exception:
                self.connected = False
        return self.connect()

    def get_candles(self, asset, timeframe_seconds=60, count=20):
        ok, message = self.ensure_connection()
        if not ok:
            raise RuntimeError(message)
        candles = self.api.get_candles(asset, timeframe_seconds, count, int(time.time()))
        return candles or []

    def place_order(self, asset, direction, amount, expiration_minutes=1):
        ok, message = self.ensure_connection()
        if not ok:
            return False, None, message
        success, order_id = self.api.buy(amount, asset, direction, expiration_minutes)
        if not success:
            return False, None, "Ordem recusada pela IQ Option."
        return True, order_id, "Ordem enviada para IQ Option."

    def check_result(self, order_id):
        ok, _ = self.ensure_connection()
        if not ok:
            return None
        try:
            result = self.api.check_win_v4(order_id)
            if result is None:
                return None
            return float(result)
        except Exception:
            return None


class QuotexPlatform(BasePlatform):
    name = "Quotex"
    supported = False

    def connect(self):
        return False, "Conector da Quotex ainda nao foi ligado. Estrutura pronta para integrar sua API."

    def get_candles(self, asset, timeframe_seconds=60, count=20):
        raise RuntimeError("Quotex ainda nao integrada neste ambiente.")

    def place_order(self, asset, direction, amount, expiration_minutes=1):
        return False, None, "Quotex ainda nao integrada neste ambiente."

    def check_result(self, order_id):
        return None


class ExnovaPlatform(BasePlatform):
    name = "Exnova"
    supported = False

    def connect(self):
        return False, "Conector da Exnova ainda nao foi ligado. Estrutura pronta para integrar sua API."

    def get_candles(self, asset, timeframe_seconds=60, count=20):
        raise RuntimeError("Exnova ainda nao integrada neste ambiente.")

    def place_order(self, asset, direction, amount, expiration_minutes=1):
        return False, None, "Exnova ainda nao integrada neste ambiente."

    def check_result(self, order_id):
        return None


PLATFORM_MAP = {
    "IQ Option": IQOptionPlatform,
    "Quotex": QuotexPlatform,
    "Exnova": ExnovaPlatform,
}
