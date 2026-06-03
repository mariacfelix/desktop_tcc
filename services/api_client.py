import requests
from utils.logger import log


def _get(url: str, params: dict = None):
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        log(f"ERRO GET {url}: {e}")
        return None, str(e)


def _post(url: str, payload: dict):
    try:
        r = requests.post(url, json=payload, timeout=5)
        log(f"POST {url} → {r.status_code} | {r.text[:200]}")
        r.raise_for_status()
        return r.json() if r.text.strip() else True, None
    except Exception as e:
        log(f"ERRO POST {url}: {e}")
        return None, str(e)


def _put(url: str, payload: dict):
    try:
        r = requests.put(url, json=payload, timeout=5)
        log(f"PUT {url} → {r.status_code}")
        r.raise_for_status()
        return r.json() if r.text.strip() else True, None
    except Exception as e:
        log(f"ERRO PUT {url}: {e}")
        return None, str(e)


def _patch(url: str, params: dict = None):
    try:
        r = requests.patch(url, params=params, timeout=5)
        log(f"PATCH {url} → {r.status_code}")
        r.raise_for_status()
        return True, None
    except Exception as e:
        log(f"ERRO PATCH {url}: {e}")
        return False, str(e)


def _delete(url: str):
    try:
        r = requests.delete(url, timeout=5)
        log(f"DELETE {url} → {r.status_code}")
        r.raise_for_status()
        return True, None
    except Exception as e:
        log(f"ERRO DELETE {url}: {e}")
        return False, str(e)


class MarmiteriaClient:
    def __init__(self, base: str):
        self.base = base

    def login(self, email: str, senha: str):
        return _post(f"{self.base}/login", {"username": email, "senha": senha})


class GastosClient:
    def __init__(self, base: str):
        self.base = base

    def listar(self, marmiteria_id: int):
        return _get(f"{self.base}/todos", {"marmiteriaId": marmiteria_id})

    def inserir(self, payload: dict):
        return _post(f"{self.base}/inserir", payload)

    def atualizar(self, payload: dict):
        return _put(f"{self.base}/atualizar", payload)

    def remover(self, gasto_id: int):
        return _delete(f"{self.base}/remover/{gasto_id}")


class CardapioClient:
    def __init__(self, base: str):
        self.base = base

    def listar(self, marmiteria_id: int):
        return _get(f"{self.base}/todos", {"marmiteriaId": marmiteria_id})

    def inserir(self, payload: dict):
        return _post(f"{self.base}/inserir", payload)

    def atualizar(self, payload: dict):
        return _put(f"{self.base}/atualizar", payload)

    def alterar_aberto(self, cardapio_id: int, aberto: bool):
        return _patch(f"{self.base}/aberto/{cardapio_id}", {"aberto": str(aberto).lower()})

    def remover(self, cardapio_id: int):
        return _delete(f"{self.base}/remover/{cardapio_id}")


class PedidoClient:
    def __init__(self, base: str):
        self.base = base

    def listar(self, marmiteria_id: int):
        return _get(f"{self.base}/todos", {"marmiteriaId": marmiteria_id})

    def inserir(self, payload: dict):
        return _post(f"{self.base}/inserir", payload)

    def remover(self, pedido_id: int):
        return _delete(f"{self.base}/remover/{pedido_id}")