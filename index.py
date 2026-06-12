import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import flet as ft
from models.state import state
from models.constants import (
    COR_FUNDO, COR_CARD, COR_SIDEBAR, COR_BORDA, COR_PRIMARIA,
    COR_TEXTO, COR_SUBTEXTO,
    API_MARMITERIA, API_GASTOS, API_CARDAPIO, API_PEDIDO,
)
from services.api_client import MarmiteriaClient, GastosClient, CardapioClient, PedidoClient
from views.login_view import build_login_view
from views.gastos_view import build_gastos_view
from views.dashboard_view import build_dashboard_view
from views.cardapio_view import build_cardapio_view
from views.pedidos_view import build_pedidos_view
from views.debug_view import build_debug_view

api_marmiteria = MarmiteriaClient(API_MARMITERIA)
api_gastos     = GastosClient(API_GASTOS)
api_cardapio   = CardapioClient(API_CARDAPIO)
api_pedido     = PedidoClient(API_PEDIDO)

ITENS_NAV = [
    (ft.Icons.RECEIPT_LONG_OUTLINED, ft.Icons.RECEIPT_LONG,       "Gastos"),
    (ft.Icons.BAR_CHART_OUTLINED,    ft.Icons.BAR_CHART_ROUNDED,  "Dashboard"),
    (ft.Icons.MENU_BOOK_OUTLINED,    ft.Icons.MENU_BOOK,          "Cardápio"),
    (ft.Icons.SHOPPING_BAG_OUTLINED, ft.Icons.SHOPPING_BAG,       "Pedidos"),
    # (ft.Icons.BUG_REPORT_OUTLINED,   ft.Icons.BUG_REPORT,         "Debug"),
]


def main(page: ft.Page):
    page.title        = "Comida & Afeto"
    page.bgcolor      = COR_FUNDO
    page.window.width = 1150
    page.window.height = 750
    page.window.min_width  = 900
    page.window.min_height = 600
    page.padding = 0

    nome_marmiteria_txt = ft.Text(
        "", size=13, color=COR_TEXTO,
        text_align=ft.TextAlign.CENTER,
        weight=ft.FontWeight.BOLD,
        max_lines=2,
        overflow=ft.TextOverflow.ELLIPSIS,
    )

    area_conteudo = ft.Container(expand=True)
    botoes_nav: list = []
    _idx_atual = [0]

    gasto_editando: dict = {}

    def on_editar_gasto(gasto: dict):
        trocar_tela(0)
        view_gastos.preencher_edicao(gasto)

    view_gastos    = build_gastos_view(page, api_gastos, state, gasto_editando)
    view_dashboard = build_dashboard_view(page, api_gastos, state, gasto_editando, on_editar_gasto)
    view_cardapio  = build_cardapio_view(page, api_cardapio, state)
    view_pedidos   = build_pedidos_view(page, api_pedido, state)
    # view_debug     = build_debug_view(page, state)

    TELAS = [view_gastos, view_dashboard, view_cardapio, view_pedidos, ]#view_debug

    def trocar_tela(idx: int):
        _idx_atual[0] = idx
        for i, btn in enumerate(botoes_nav):
            selecionado           = (i == idx)
            btn.bgcolor           = COR_PRIMARIA if selecionado else "transparent"
            icone_ctrl            = btn.content.controls[0]
            label_ctrl            = btn.content.controls[1]
            icone_ctrl.name       = ITENS_NAV[i][1] if selecionado else ITENS_NAV[i][0]
            icone_ctrl.color      = "white" if selecionado else COR_TEXTO
            label_ctrl.color      = "white" if selecionado else COR_TEXTO
            btn.update()

        area_conteudo.content = TELAS[idx]

        if idx == 0:
            view_gastos.recarregar() if hasattr(view_gastos, "recarregar") else page.update()
        elif idx == 1:
            view_dashboard.recarregar()
        elif idx == 2:
            view_cardapio.recarregar()
        elif idx == 3:
            view_pedidos.recarregar()
        else:
            page.update()

    for i, (icone_off, icone_on, label) in enumerate(ITENS_NAV):
        btn = ft.Container(
            content=ft.Column([
                ft.Icon(icone_off, color=COR_TEXTO, size=24),
                ft.Text(label, size=10, color=COR_TEXTO, weight=ft.FontWeight.W_600,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4, tight=True),
            padding=ft.Padding.symmetric(horizontal=8, vertical=10),
            border_radius=12, bgcolor="transparent", ink=True,
            on_click=lambda e, idx=i: trocar_tela(idx),
            width=90,
        )
        botoes_nav.append(btn)

    botoes_nav[0].bgcolor                            = COR_PRIMARIA
    botoes_nav[0].content.controls[0].name          = ITENS_NAV[0][1]
    botoes_nav[0].content.controls[0].color         = "white"
    botoes_nav[0].content.controls[1].color         = "white"

    sidebar = ft.Container(
        width=115, bgcolor=COR_SIDEBAR,
        border=ft.Border(right=ft.BorderSide(1, COR_BORDA)),
        content=ft.Column([
            ft.Container(
                width=115,
                padding=ft.Padding.symmetric(horizontal=10, vertical=18),
                content=ft.Column([
                    ft.Container(
                        ft.Image(src="assets/images/logo.png", width=72, height=72),
                        # alignment=ft.alignment.,
                    ),
                    ft.Container(height=8),
                    nome_marmiteria_txt,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            ),
            ft.Divider(color=COR_BORDA, height=1),
            ft.Container(
                expand=True,
                padding=ft.Padding.symmetric(horizontal=8, vertical=12),
                content=ft.Column(
                    controls=botoes_nav, spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
        ], spacing=0, expand=True),
    )

    tela_principal = ft.Row(controls=[sidebar, area_conteudo], spacing=0, expand=True)

    def on_login_sucesso():
        nome_marmiteria_txt.value = state["marmiteria_nome"] or ""
        area_conteudo.content     = TELAS[0]
        page.controls.clear()
        page.add(tela_principal)
        view_gastos.recarregar() if hasattr(view_gastos, "recarregar") else page.update()
        page.update()

    tela_login = build_login_view(page, api_marmiteria, state, on_login_sucesso)
    page.add(tela_login)


ft.app(target=main)