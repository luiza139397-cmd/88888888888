import requests

from config import TELEGRAM_TIMEOUT


class TelegramService:
    def __init__(self, enabled=False, token="", chat_id=""):
        self.enabled = enabled
        self.token = token.strip()
        self.chat_id = chat_id.strip()

    def is_ready(self):
        return self.enabled and bool(self.token) and bool(self.chat_id)

    def send(self, message):
        if not self.is_ready():
            return False, "Telegram desativado ou incompleto."

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message}

        try:
            response = requests.post(url, json=payload, timeout=TELEGRAM_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                return False, data.get("description", "Resposta invalida do Telegram.")
            return True, "Mensagem enviada ao Telegram."
        except requests.RequestException as exc:
            return False, f"Falha ao enviar para Telegram: {exc}"
        except ValueError:
            return False, "Resposta do Telegram nao veio em JSON."
