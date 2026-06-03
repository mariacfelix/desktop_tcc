import flet as ft
from datetime import datetime
from models.constants import (
    CATEGORIAS, CORES_CATEGORIA,
    COR_FUNDO, COR_CARD, COR_BORDA, COR_PRIMARIA, COR_SECUNDARIA,
    COR_TEXTO, COR_SUBTEXTO, COR_DESTAQUE, COR_ERRO, COR_SUCESSO,
)
from views.components import mk_campo, mk_btn, mk_secao_label, mk_titulo, mk_subtitulo
from views.components import mk_dialogo_confirmacao
from utils.mascara import aplicar_mascara_data
from utils.grafico import gerar_grafico_pizza


def build_dashboard_view(
    page: ft.Page,
    api_gastos,
    state: dict,
    gasto_editando: dict,
    on_editar_gasto,
) -> ft.Container:
    todos_gastos: list = []

    pizza_container = ft.Container(
        content=ft.Text("Nenhum dado para exibir.", color=COR_SUBTEXTO, size=13),
        expand=True,
    )
    lista_cards = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8, expand=True)
    total_txt   = ft.Text("Total: R$ 0,00", color=COR_DESTAQUE, size=15, weight=ft.FontWeight.BOLD)

    dd_filtro_cat = ft.Dropdown(
        label="Categoria", value="Todas",
        options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(c) for c in CATEGORIAS],
        bgcolor=COR_CARD, color=COR_TEXTO,
        label_style=ft.TextStyle(color=COR_SUBTEXTO),
        border_color=COR_BORDA, focused_border_color=COR_PRIMARIA,
        border_radius=10, width=200,
    )
    f_de  = mk_campo("De",  width=150, hint_text="DD/MM/AAAA")
    f_ate = mk_campo("Até", width=150, hint_text="DD/MM/AAAA")

    def on_filtro_data(e):
        c = e.control
        novo = aplicar_mascara_data(c.value)
        if c.value != novo:
            c.value = novo
            c.update()

    f_de.on_change  = on_filtro_data
    f_ate.on_change = on_filtro_data

    def snack(msg: str, cor: str = COR_SUCESSO):
        page.snack_bar = ft.SnackBar(ft.Text(msg, color="white"), bgcolor=cor, duration=2500)
        page.snack_bar.open = True
        page.update()

    def filtrar(gastos):
        res = gastos
        cat_sel = dd_filtro_cat.value or "Todas"
        if cat_sel != "Todas":
            res = [g for g in res if (g.get("categoria") or "") == cat_sel]
        try:
            d_de = datetime.strptime(f_de.value.strip(), "%d/%m/%Y").date() \
                   if (f_de.value or "").strip() else None
        except Exception:
            d_de = None
        try:
            d_ate = datetime.strptime(f_ate.value.strip(), "%d/%m/%Y").date() \
                    if (f_ate.value or "").strip() else None
        except Exception:
            d_ate = None
        if d_de or d_ate:
            tmp = []
            for g in res:
                try:
                    dg = datetime.strptime((g.get("data") or "")[:10], "%Y-%m-%d").date()
                except Exception:
                    tmp.append(g); continue
                if d_de and dg < d_de: continue
                if d_ate and dg > d_ate: continue
                tmp.append(g)
            res = tmp
        return res

    def atualizar():
        filtrados = filtrar(todos_gastos)
        b64 = gerar_grafico_pizza(filtrados)
        pizza_container.content = (
            ft.Image(src="data:image/png;base64," + b64, width=460, fit="contain")
            if b64 else ft.Text("Nenhum dado para exibir.", color=COR_SUBTEXTO, size=13)
        )
        lista_cards.controls.clear()
        for g in sorted(filtrados, key=lambda x: x.get("data") or "", reverse=True):
            lista_cards.controls.append(_card_gasto(g))
        total = sum((g.get("custo") or 0) for g in filtrados)
        total_txt.value = f"Total: R$ {total:,.2f}"
        page.update()

    def recarregar():
        nonlocal todos_gastos
        dados, _ = api_gastos.listar(state["marmiteria_id"])
        todos_gastos = dados or []
        atualizar()

    def limpar_filtros(e):
        dd_filtro_cat.value = "Todas"
        f_de.value = f_ate.value = ""
        atualizar()

    def _card_gasto(g: dict) -> ft.Container:
        cor = CORES_CATEGORIA.get(g.get("categoria") or "", COR_PRIMARIA)
        try:
            data_fmt = datetime.strptime(g["data"][:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            data_fmt = g.get("data") or "—"
        obs = g.get("observacao") or ""

        def on_editar(e, gasto=g):
            on_editar_gasto(gasto)

        def on_deletar(e, gasto=g):
            mk_dialogo_confirmacao(
                page,
                "Confirmar exclusão",
                f"Excluir gasto de R$ {(gasto.get('custo') or 0):,.2f} ({gasto.get('categoria', '—')})?",
                lambda: (api_gastos.remover(gasto["id"]), snack("Gasto removido!"), recarregar()),
            )

        return ft.Container(
            bgcolor=COR_FUNDO, border_radius=12,
            padding=ft.Padding.symmetric(horizontal=18, vertical=12),
            border=ft.Border(left=ft.BorderSide(4, cor)),
            content=ft.Row(controls=[
                ft.Container(width=8, height=8, bgcolor=cor, border_radius=4),
                ft.Column([
                    ft.Text(g.get("categoria") or "—", color=COR_TEXTO, size=14, weight=ft.FontWeight.W_600),
                    ft.Text((data_fmt or "—") + (f"  •  {obs}" if obs else ""), color=COR_SUBTEXTO, size=11),
                ], spacing=2, expand=True),
                ft.Text(f"R$ {(g.get('custo') or 0):,.2f}", color=cor, size=15, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=COR_SECUNDARIA,
                                  tooltip="Editar", on_click=on_editar, icon_size=18),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=COR_ERRO,
                                  tooltip="Excluir", on_click=on_deletar, icon_size=18),
                ], spacing=0),
            ], alignment=ft.MainAxisAlignment.START,
               vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
        )

    container = ft.Container(
        expand=True, padding=ft.Padding.all(24),
        content=ft.Column(expand=True, spacing=16, controls=[
            ft.Row([
                ft.Column([
                    mk_titulo("Dashboard"),
                    mk_subtitulo("Visão geral dos seus gastos"),
                ], spacing=2, expand=True),
                total_txt,
                ft.IconButton(ft.Icons.REFRESH_ROUNDED, icon_color=COR_SECUNDARIA,
                              tooltip="Atualizar", on_click=lambda e: recarregar()),
            ]),
            ft.Container(
                bgcolor=COR_CARD, border_radius=12,
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                border=ft.Border.all(1, COR_BORDA),
                content=ft.Row([
                    dd_filtro_cat, f_de, f_ate,
                    mk_btn("Filtrar", lambda e: atualizar(), ft.Icons.FILTER_ALT_OUTLINED),
                    ft.TextButton("Limpar", style=ft.ButtonStyle(color=COR_SUBTEXTO), on_click=limpar_filtros),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            ft.Row(expand=True, spacing=16, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
                ft.Container(
                    width=500, bgcolor=COR_CARD, border_radius=14,
                    border=ft.Border.all(1, COR_BORDA), padding=ft.Padding.all(20),
                    content=ft.Column([
                        mk_secao_label("Gastos por Categoria"),
                        ft.Divider(color=COR_BORDA, height=12),
                        pizza_container,
                    ], expand=True),
                ),
                ft.Container(
                    expand=True, bgcolor=COR_CARD, border_radius=14,
                    border=ft.Border.all(1, COR_BORDA), padding=ft.Padding.all(20),
                    content=ft.Column([
                        mk_secao_label("Lançamentos"),
                        ft.Divider(color=COR_BORDA, height=12),
                        lista_cards,
                    ], expand=True),
                ),
            ]),
        ]),
    )

    container.recarregar = recarregar
    return container