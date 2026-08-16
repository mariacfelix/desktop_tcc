import flet as ft
from datetime import date, datetime
from models.constants import (
    CATEGORIAS, COR_CARD, COR_BORDA, COR_PRIMARIA,
    COR_TEXTO, COR_SUBTEXTO, COR_ERRO, COR_SUCESSO,
)
from views.components import mk_campo, mk_btn, mk_card, mk_titulo, mk_subtitulo, mk_secao_label
from utils.mascara import aplicar_mascara_data


def build_gastos_view(page: ft.Page, api_gastos, state: dict, gasto_editando: dict) -> ft.Container:
    _salvando = [False]

    f_custo = mk_campo("Valor (R$)", keyboard_type=ft.KeyboardType.NUMBER, width=180)
    f_obs   = mk_campo("Observação (opcional)", expand=True)
    f_data  = mk_campo("Data", width=210,
                        value=date.today().strftime("%d/%m/%Y"),
                        hint_text="DD/MM/AAAA")

    def on_data_change(e):
        c = e.control
        novo = aplicar_mascara_data(c.value)
        if c.value != novo:
            c.value = novo
            c.update()

    f_data.on_change = on_data_change

    dd_cat = ft.Dropdown(
        label="Categoria",
        options=[ft.dropdown.Option(key=c, content=ft.Text(c, color=COR_TEXTO)) for c in CATEGORIAS],
        bgcolor=COR_CARD,
        label_style=ft.TextStyle(color=COR_SUBTEXTO),
        border_color=COR_BORDA, focused_border_color=COR_PRIMARIA,
        border_radius=10, expand=True,
    )

    txt_btn_salvar = ft.Text("Salvar Gasto", color="white", weight=ft.FontWeight.BOLD)
    btn_cancelar   = ft.TextButton(
        "✕  Cancelar edição",
        style=ft.ButtonStyle(color=COR_SUBTEXTO),
        visible=False,
    )

    def snack(msg: str, cor: str = COR_SUCESSO):
        sb = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=cor, duration=2500, open=True)
        page.overlay.append(sb)
        page.update()

    def limpar_form():
        gasto_editando.clear()
        f_custo.value        = ""
        f_data.value         = date.today().strftime("%d/%m/%Y")
        f_obs.value          = ""
        dd_cat.value         = None
        txt_btn_salvar.value = "Salvar Gasto"
        btn_cancelar.visible = False
        page.update()

    btn_cancelar.on_click = lambda e: limpar_form()

    def salvar_gasto(e):
        if _salvando[0]:
            return
        _salvando[0] = True
        try:
            custo_str = (f_custo.value or "").replace(",", ".")
            categoria = dd_cat.value
            data_str  = (f_data.value or "").strip()
            if not custo_str or not categoria:
                snack("Preencha valor e categoria!", COR_ERRO); return
            try:
                custo = float(custo_str)
                if custo <= 0:
                    snack("O valor deve ser maior que zero!", COR_ERRO); return
            except ValueError:
                snack("Valor inválido!", COR_ERRO); return
            try:
                data_iso = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            except Exception:
                snack("Data inválida! Use DD/MM/AAAA", COR_ERRO); return
            payload = {
                "custo": custo, "categoria": categoria,
                "data": data_iso, "observacao": (f_obs.value or "").strip(),
            }
            if gasto_editando.get("id"):
                payload["id"]         = gasto_editando["id"]
                payload["marmiteria"] = {"id": state["marmiteria_id"]}
                ok, err = api_gastos.atualizar(payload)
                if ok:
                    snack("Gasto atualizado!")
                    limpar_form()
                else:
                    snack(f"Erro: {err}", COR_ERRO)
            else:
                payload["marmiteriaId"] = state["marmiteria_id"]
                ok, err = api_gastos.inserir(payload)
                if ok:
                    limpar_form()
                    snack("Gasto registrado com sucesso!")
                else:
                    snack(f"Erro: {err}", COR_ERRO)
        finally:
            _salvando[0] = False

    btn_salvar = ft.Container(
        content=ft.Row(
            [ft.Icon(ft.Icons.SAVE_OUTLINED, color="white", size=16), txt_btn_salvar],
            tight=True, spacing=6, alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=COR_PRIMARIA, border_radius=10, height=44,
        padding=ft.Padding.symmetric(horizontal=20, vertical=0),
        on_click=salvar_gasto, ink=True,
    )

    def preencher_edicao(gasto: dict):
        gasto_editando.clear()
        gasto_editando.update(gasto)
        f_custo.value        = str(gasto.get("custo") or "")
        f_data.value         = datetime.strptime(gasto["data"][:10], "%Y-%m-%d").strftime("%d/%m/%Y") \
                               if gasto.get("data") else ""
        f_obs.value          = gasto.get("observacao", "") or ""
        dd_cat.value         = gasto.get("categoria")
        txt_btn_salvar.value = "Atualizar Gasto"
        btn_cancelar.visible = True
        page.update()

    container = ft.Container(
        expand=True, padding=ft.Padding.all(36),
        content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=20, controls=[
            ft.Column([
                mk_titulo("Lançar Gasto"),
                mk_subtitulo("Registre os gastos da sua marmitaria"),
            ], spacing=4),
            ft.Divider(color=COR_BORDA),
            mk_card(ft.Column(spacing=16, controls=[
                mk_secao_label("Informações do Gasto"),
                ft.Row([dd_cat, f_custo], spacing=12),
                ft.Row([f_data, f_obs], spacing=12),
                ft.Divider(color=COR_BORDA),
                ft.Row([btn_salvar, btn_cancelar], spacing=16,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ])),
        ]),
    )

    container.preencher_edicao = preencher_edicao
    return container