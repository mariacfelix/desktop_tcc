from datetime import date, timedelta
from typing import Optional
from utils.logger import log

CHAR_WIDTH = 32


def _linha(texto: str, largura: int = CHAR_WIDTH) -> str:
    return texto[:largura].ljust(largura)


def _separador(char: str = "-", largura: int = CHAR_WIDTH) -> str:
    return char * largura


def _centralizar(texto: str, largura: int = CHAR_WIDTH) -> str:
    return texto[:largura].center(largura)


def _backend_usb():
    import libusb_package
    return libusb_package.get_libusb1_backend()


def imprimir_etiqueta(pedido: dict, nome_marmiteria: str) -> tuple[bool, Optional[str]]:
    try:
        from escpos.printer import Usb
        printer = Usb(
            0x0483, 0x5743, profile="default",
            usb_args={"backend": _backend_usb()},
        )
        _enviar_etiqueta(printer, pedido, nome_marmiteria)
        printer.close()
        return True, None
    except Exception as e:
        log(f"ERRO impressora USB: {e}")
        return False, str(e)


def imprimir_etiquetas_lote(pedidos: list, nome_marmiteria: str) -> tuple[bool, Optional[str]]:
    try:
        from escpos.printer import Usb
        printer = Usb(
            0x0483, 0x5743, profile="default",
            usb_args={"backend": _backend_usb()},
        )
        for i, pedido in enumerate(pedidos):
            _enviar_etiqueta(printer, pedido, nome_marmiteria)
            if i < len(pedidos) - 1:
                printer.text("\n")
        printer.close()
        return True, None
    except Exception as e:
        log(f"ERRO impressora lote: {e}")
        return False, str(e)


def _enviar_etiqueta(printer, pedido: dict, nome_marmiteria: str):
    nome_cliente  = pedido.get("nomeCliente") or "—"
    cardapio_nome = pedido.get("cardapioNome") or "—"
    ings          = pedido.get("ingredientes") or []
    validade      = (date.today() + timedelta(days=30)).strftime("%d/%m/%Y")

    printer.set(align="center", bold=True, double_height=False, double_width=False)
    printer.text("Comida & Afeto\n")

    printer.set(align="center", bold=False, normal_textsize=True)
    printer.text(f"{nome_marmiteria}\n")

    printer.text(_separador() + "\n")

    printer.set(align="left", bold=True)
    printer.text(f"Cliente: {nome_cliente}\n")

    printer.set(align="left", bold=False)
    printer.text(f"Cardapio: {cardapio_nome}\n")

    printer.text(_separador() + "\n")

    printer.set(align="left", bold=True)
    printer.text("Ingredientes:\n")

    printer.set(align="left", bold=False)
    if ings:
        for ing in ings:
            nome_ing = ing.get("nome") or "—"
            printer.text(f"  - {nome_ing}\n")
    else:
        printer.text("  Sem ingredientes\n")

    printer.text(_separador() + "\n")

    printer.set(align="center", bold=True)
    printer.text(f"Validade: {validade}\n")

    printer.set(align="center", bold=False)
    printer.text("\n\n\n")
    printer.cut()


def preview_etiqueta(pedido: dict, nome_marmiteria: str) -> str:
    nome_cliente  = pedido.get("nomeCliente") or "—"
    cardapio_nome = pedido.get("cardapioNome") or "—"
    ings          = pedido.get("ingredientes") or []
    validade      = (date.today() + timedelta(days=30)).strftime("%d/%m/%Y")

    linhas = [
        _centralizar("Comida & Afeto"),
        _centralizar(nome_marmiteria),
        _separador(),
        f"Cliente: {nome_cliente}",
        f"Cardapio: {cardapio_nome}",
        _separador(),
        "Ingredientes:",
    ]

    if ings:
        for ing in ings:
            linhas.append(f"  - {ing.get('nome', '—')}")
    else:
        linhas.append("  Sem ingredientes")

    linhas += [
        _separador(),
        _centralizar(f"Validade: {validade}"),
    ]

    return "\n".join(linhas)