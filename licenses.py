import json
import random
from datetime import datetime
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
LICENSE_FILE = DATA_DIR / "license.json"
LICENSE_CODES_FILE = DATA_DIR / "license_codes.json"


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_codes():
    ensure_data_dir()
    if not LICENSE_CODES_FILE.exists():
        LICENSE_CODES_FILE.write_text("[]", encoding="utf-8")
    try:
        return json.loads(LICENSE_CODES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_codes(codes):
    ensure_data_dir()
    LICENSE_CODES_FILE.write_text(json.dumps(codes, indent=2, ensure_ascii=False), encoding="utf-8")


def generate_license_token(customer_name, expires_at, max_devices=1, note=""):
    if not expires_at.strip():
        raise ValueError("Preencha a data de expiracao no formato AAAA-MM-DD.")
    try:
        datetime.strptime(expires_at.strip(), "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("Data invalida. Use o formato AAAA-MM-DD, por exemplo 2026-12-31.") from exc

    codes = _load_codes()

    while True:
        code = f"{random.randint(0, 9999):04d}"
        if not any(item["code"] == code for item in codes):
            break

    record = {
        "code": code,
        "customer_name": customer_name.strip() or "Cliente",
        "expires_at": expires_at.strip(),
        "max_devices": int(max_devices),
        "note": note.strip(),
        "issued_at": datetime.now().strftime("%Y-%m-%d"),
        "activated": False,
        "device_name": "",
        "activated_at": "",
    }
    codes.append(record)
    _save_codes(codes)
    return code


def activate_license(token, device_name):
    code = token.strip()
    if len(code) != 4 or not code.isdigit():
        raise ValueError("A licenca agora deve ter 4 digitos.")

    codes = _load_codes()
    selected = next((item for item in codes if item["code"] == code), None)
    if not selected:
        raise ValueError("Licenca de 4 digitos nao encontrada.")

    expires_at = datetime.strptime(selected["expires_at"], "%Y-%m-%d").date()
    if datetime.now().date() > expires_at:
        raise ValueError("Licenca expirada.")

    selected["activated"] = True
    selected["device_name"] = device_name.strip() or "Meu PC"
    selected["activated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _save_codes(codes)

    local_record = {
        "code": selected["code"],
        "device_name": selected["device_name"],
        "activated_at": selected["activated_at"],
        "payload": {
            "customer_name": selected["customer_name"],
            "expires_at": selected["expires_at"],
            "note": selected["note"],
            "max_devices": selected["max_devices"],
        },
    }
    ensure_data_dir()
    LICENSE_FILE.write_text(json.dumps(local_record, indent=2, ensure_ascii=False), encoding="utf-8")
    return local_record


def load_activated_license():
    ensure_data_dir()
    if not LICENSE_FILE.exists():
        return None
    try:
        return json.loads(LICENSE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def validate_activated_license():
    record = load_activated_license()
    if not record:
        return False, "Nenhuma licenca ativada no PC.", None

    expires_at = datetime.strptime(record["payload"]["expires_at"], "%Y-%m-%d").date()
    if datetime.now().date() > expires_at:
        return False, "Licenca expirada.", record
    return True, f"Licenca valida no PC com codigo {record['code']}.", record
