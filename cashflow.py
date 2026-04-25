import json
from datetime import datetime
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
CASHFLOW_FILE = DATA_DIR / "cashflow.json"


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _default_cashflow():
    return {
        "initial_balance": 100.0,
        "current_balance": 100.0,
        "wins": 0,
        "losses": 0,
        "signals": 0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "last_result": 0.0,
        "updated_at": "",
        "history": [],
    }


def load_cashflow():
    ensure_data_dir()
    if not CASHFLOW_FILE.exists():
        data = _default_cashflow()
        save_cashflow(data)
        return data
    try:
        return json.loads(CASHFLOW_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = _default_cashflow()
        save_cashflow(data)
        return data


def save_cashflow(data):
    ensure_data_dir()
    CASHFLOW_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def set_initial_balance(value):
    data = load_cashflow()
    value = float(value)
    data["initial_balance"] = value
    data["current_balance"] = value
    data["wins"] = 0
    data["losses"] = 0
    data["signals"] = 0
    data["gross_profit"] = 0.0
    data["gross_loss"] = 0.0
    data["last_result"] = 0.0
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["history"] = []
    save_cashflow(data)
    return data


def register_signal():
    data = load_cashflow()
    data["signals"] += 1
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_cashflow(data)
    return data


def register_result(platform_name, asset, result_value):
    data = load_cashflow()
    result_value = float(result_value)
    data["current_balance"] = round(data["current_balance"] + result_value, 2)
    data["last_result"] = round(result_value, 2)
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if result_value > 0:
        data["wins"] += 1
        data["gross_profit"] = round(data["gross_profit"] + result_value, 2)
    else:
        data["losses"] += 1
        data["gross_loss"] = round(data["gross_loss"] + abs(result_value), 2)

    data["history"].append(
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "platform": platform_name,
            "asset": asset,
            "result": round(result_value, 2),
            "balance_after": data["current_balance"],
        }
    )
    data["history"] = data["history"][-100:]
    save_cashflow(data)
    return data
