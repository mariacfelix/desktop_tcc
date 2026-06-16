import flet as ft
from models.constants import (
    COR_CARD, COR_TEXTO, COR_SUBTEXTO, COR_BORDA, COR_PRIMARIA,
)


def mk_campo(label: str, **kw) -> ft.TextField:
    return ft.TextField(
        label=label,
        bgcolor=COR_CARD, color=COR_TEXTO,
        label_style=ft.TextStyle(color=COR_SUBTEXTO),
        border_color=COR_BORDA, focused_border_color=COR_PRIMARIA,
        border_radius=10, cursor_color=COR_PRIMARIA,
        **kw,
    )


def mk_btn(texto: str, on_click, icone=None, bgcolor: str = None, cor_texto: str = "white") -> ft.Container:
    controles = []
    if icone:
        controles.append(ft.Icon(icone, color=cor_texto, size=16))
    controles.append(ft.Text(texto, color=cor_texto, weight=ft.FontWeight.BOLD))
    return ft.Container(
        content=ft.Row(
            controles, tight=True, spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=bgcolor or COR_PRIMARIA,
        border_radius=10, height=44,
        padding=ft.Padding.symmetric(horizontal=20, vertical=0),
        on_click=on_click, ink=True,
    )


def mk_titulo(texto: str) -> ft.Text:
    return ft.Text(texto, size=24, weight=ft.FontWeight.BOLD, color=COR_TEXTO)


def mk_subtitulo(texto: str) -> ft.Text:
    return ft.Text(texto, size=13, color=COR_SUBTEXTO)


def mk_secao_label(texto: str) -> ft.Text:
    return ft.Text(texto, size=13, color=COR_SUBTEXTO, weight=ft.FontWeight.W_600)


def mk_card(content: ft.Control, padding: int = 24) -> ft.Container:
    return ft.Container(
        bgcolor=COR_CARD, border_radius=16,
        padding=ft.Padding.all(padding),
        border=ft.Border.all(1, COR_BORDA),
        content=content,
    )


def mk_dialogo_confirmacao(page: ft.Page, titulo: str, mensagem: str, on_confirmar):
    def cancelar(ev):
        page.pop_dialog()
        page.update()

    def confirmar(ev):
        page.pop_dialog()
        page.update()
        on_confirmar()

    from models.constants import COR_ERRO
    page.show_dialog(ft.AlertDialog(
        modal=True,
        title=ft.Text(titulo, color=COR_TEXTO, weight=ft.FontWeight.BOLD),
        content=ft.Text(mensagem, color=COR_SUBTEXTO),
        actions=[
            ft.TextButton("Cancelar", style=ft.ButtonStyle(color=COR_SUBTEXTO), on_click=cancelar),
            mk_btn("Excluir", confirmar, bgcolor=COR_ERRO),
        ],
        bgcolor=COR_CARD, shape=ft.RoundedRectangleBorder(radius=14),
    ))


def mk_dialogo_sucesso(page: ft.Page, titulo: str, corpo: str):
    from models.constants import COR_SUCESSO

    def fechar(e):
        page.pop_dialog()
        page.update()

    page.show_dialog(ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=COR_SUCESSO, size=28),
            ft.Text(f"  {titulo}", color=COR_TEXTO, weight=ft.FontWeight.BOLD),
        ]),
        content=ft.Text(corpo, color=COR_SUBTEXTO, size=14),
        actions=[mk_btn("OK", fechar)],
        bgcolor=COR_CARD, shape=ft.RoundedRectangleBorder(radius=14),
    ))