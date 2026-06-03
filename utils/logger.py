from datetime import datetime

_logs: list = []


def log(msg: str):
    entrada = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    _logs.append(entrada)
    print(entrada)
    if len(_logs) > 200:
        _logs.pop(0)


def get_logs() -> list:
    return _logs


def clear_logs():
    _logs.clear()