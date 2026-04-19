import flet as ft
import requests
import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, date
from typing import Optional

API_BASE = "http://localhost:8080/apiGastos"
MARMITERIA_ID = 1

CATEGORIAS = [
    "Proteínas", "Carboidratos", "Legumes", "Embalagens", "Gás / Energia",
    "Aluguel", "Transporte", "Mão de Obra", "Equipamentos", "Outros",
]

CORES_CATEGORIA = {
    "Proteínas":     "#FF8C42",
    "Carboidratos":  "#793911",
    "Legumes":       "#DF641D",
    "Embalagens":    "#FFB347",
    "Gás / Energia": "#FFA500",
    "Aluguel":       "#FF6B35",
    "Transporte":    "#FF4500",
    "Mão de Obra":   "#E8531A",
    "Equipamentos":  "#D4380D",
    "Outros":        "#8B4513",
}

COR_PRIMARIA   = "#902802"
COR_SECUNDARIA = "#FF8C42"
COR_FUNDO      = "#1A0D00"
COR_CARD       = "#2A1900"
COR_SIDEBAR    = "#110C00"
COR_BORDA      = "#563903"
COR_TEXTO      = "#FFFFFF"
COR_SUBTEXTO   = "#C9A876"
COR_DESTAQUE   = "#F79800"

_logs: list = []

def log(msg: str):
    entrada = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    _logs.append(entrada)
    print(entrada)
    if len(_logs) > 200:
        _logs.pop(0)

def aplicar_mascara_data(valor: str) -> str:
    nums = "".join(c for c in (valor or "") if c.isdigit())[:8]
    r = ""
    for i, c in enumerate(nums):
        if i == 2 or i == 4:
            r += "/"
        r += c
    return r

def api_listar():
    try:
        r = requests.get(f"{API_BASE}/todos",
                         params={"marmiteriaId": MARMITERIA_ID}, timeout=5)
        log(f"GET /todos → {r.status_code}")
        r.raise_for_status()
        dados = r.json()
        log(f"  {len(dados)} registro(s) retornado(s)")
        return dados, None
    except Exception as e:
        log(f"ERRO api_listar: {e}")
        return [], str(e)

def api_inserir(payload: dict):
    payload["marmiteriaId"] = MARMITERIA_ID
    try:
        log(f"POST /inserir → payload: {payload}")
        r = requests.post(f"{API_BASE}/inserir", json=payload, timeout=5)
        log(f"  status: {r.status_code} | body: {r.text[:200]}")
        r.raise_for_status()
        return True, None
    except Exception as e:
        log(f"ERRO api_inserir: {e}")
        return False, str(e)

def api_atualizar(payload: dict):
    payload["marmiteria"] = {"id": MARMITERIA_ID}
    try:
        log(f"PUT /atualizar → payload: {payload}")
        r = requests.put(f"{API_BASE}/atualizar", json=payload, timeout=5)
        log(f"  status: {r.status_code} | body: {r.text[:200]}")
        r.raise_for_status()
        return True, None
    except Exception as e:
        log(f"ERRO api_atualizar: {e}")
        return False, str(e)

def api_deletar(gasto_id: int):
    try:
        log(f"DELETE /remover/{gasto_id}")
        r = requests.delete(f"{API_BASE}/remover/{gasto_id}", timeout=5)
        log(f"  status: {r.status_code}")
        r.raise_for_status()
        return True, None
    except Exception as e:
        log(f"ERRO api_deletar: {e}")
        return False, str(e)

def gerar_grafico_pizza(gastos: list) -> Optional[str]:
    if not gastos:
        return None
    totais = {}
    for g in gastos:
        cat = g.get("categoria") or "Outros"
        totais[cat] = totais.get(cat, 0) + (g.get("custo") or 0)
    if not totais or sum(totais.values()) == 0:
        return None

    labels, sizes, cores = [], [], []
    for cat, val in sorted(totais.items(), key=lambda x: -x[1]):
        labels.append(cat)
        sizes.append(val)
        cores.append(CORES_CATEGORIA.get(cat, "#8B4513"))

    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    ax.pie(
        sizes, labels=None,
        autopct=lambda pct: f"{pct:.1f}%",
        colors=cores, startangle=140,
        wedgeprops=dict(width=0.6, edgecolor="none", linewidth=0),
        pctdistance=0.78,
        textprops={"color": "white", "fontsize": 8},
    )
    handles = [
        mpatches.Patch(color=cores[i], label=f"{labels[i]}  R${sizes[i]:,.2f}")
        for i in range(len(labels))
    ]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5),
              fontsize=8, framealpha=0, labelcolor="#C9A876")
    ax.set_title(f"Total: R${sum(sizes):,.2f}", color="#FF8C42",
                 fontsize=11, fontweight="bold", pad=10)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def mk_campo(label, **kw):
    return ft.TextField(
        label=label,
        bgcolor=COR_CARD, color=COR_TEXTO,
        label_style=ft.TextStyle(color=COR_SUBTEXTO),
        border_color=COR_BORDA, focused_border_color=COR_PRIMARIA,
        border_radius=10, cursor_color=COR_PRIMARIA,
        **kw,
    )

def mk_btn(texto, on_click, icone=None, bgcolor=None):
    controles = []
    if icone:
        controles.append(ft.Icon(icone, color="white", size=16))
    controles.append(ft.Text(texto, color="white", weight=ft.FontWeight.BOLD))
    return ft.Container(
        content=ft.Row(controles, tight=True, spacing=6,
                       alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=bgcolor or COR_PRIMARIA,
        border_radius=10, height=44,
        padding=ft.Padding.symmetric(horizontal=20, vertical=0),
        on_click=on_click, ink=True,
    )

def main(page: ft.Page):
    page.title = "Comida & Afeto – Gestão de Gastos"
    page.bgcolor = COR_FUNDO
    page.window.width = 1100
    page.window.height = 720
    page.window.min_width = 900
    page.window.min_height = 600
    page.padding = 0

    todos_gastos: list = []
    gasto_editando: dict = {}
    _salvando = [False]

    def snack(msg: str, cor: str = "#388E3C"):
        page.snack_bar = ft.SnackBar(
            ft.Text(msg, color="white"), bgcolor=cor, duration=2500
        )
        page.snack_bar.open = True
        page.update()

    def dialogo_sucesso(categoria: str, custo: float):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color="#4CAF50", size=28),
                ft.Text("  Gasto registrado!", color=COR_TEXTO,
                        weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Column([
                ft.Text(f"Categoria: {categoria}", color=COR_SUBTEXTO, size=13),
                ft.Text(f"Valor: R$ {custo:,.2f}", color=COR_DESTAQUE,
                        size=16, weight=ft.FontWeight.BOLD),
            ], spacing=8, tight=True),
            bgcolor=COR_CARD,
            shape=ft.RoundedRectangleBorder(radius=14),
        )
        def fechar(e):
            dlg.open = False
            page.update()
        dlg.actions = [mk_btn("OK", fechar)]
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    f_custo = mk_campo("Valor (R$)", keyboard_type=ft.KeyboardType.NUMBER, width=180)
    f_obs   = mk_campo("Observação (opcional)", expand=True)
    f_data  = mk_campo("Data", width=210,
                       value=date.today().strftime("%d/%m/%Y"),
                       hint_text="DD/MM/AAAA", max_length=10)

    def on_data_change(e):
        c = e.control
        novo = aplicar_mascara_data(c.value)
        if c.value != novo:
            c.value = novo
            c.update()

    f_data.on_change = on_data_change

    dd_cat = ft.Dropdown(
        label="Categoria",
        options=[ft.dropdown.Option(c) for c in CATEGORIAS],
        bgcolor=COR_CARD, color=COR_TEXTO,
        label_style=ft.TextStyle(color=COR_SUBTEXTO),
        border_color=COR_BORDA, focused_border_color=COR_PRIMARIA,
        border_radius=10, expand=True,
    )

    btn_cancelar = ft.TextButton(
        "✕  Cancelar edição",
        style=ft.ButtonStyle(color=COR_SUBTEXTO),
        visible=False,
    )

    def limpar_form():
        gasto_editando.clear()
        f_custo.value = ""
        f_data.value = date.today().strftime("%d/%m/%Y")
        f_obs.value = ""
        dd_cat.value = None
        btn_salvar.content.controls[1].value = "Salvar Gasto"
        btn_cancelar.visible = False
        page.update()

    btn_cancelar.on_click = lambda e: limpar_form()

    def salvar_gasto(e):
        if _salvando[0]:
            return
        _salvando[0] = True
        try:
            log(">>> salvar_gasto CHAMADO")
            custo_str = (f_custo.value or "").replace(",", ".")
            categoria = dd_cat.value
            data_str  = (f_data.value or "").strip()
            log(f"  custo={custo_str!r} categoria={categoria!r} data={data_str!r}")

            if not custo_str or not categoria:
                snack("Preencha valor e categoria!", "#C62828"); return
            try:
                custo = float(custo_str)
            except ValueError:
                snack("Valor inválido!", "#C62828"); return
            try:
                data_iso = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            except Exception:
                snack("Data inválida! Use DD/MM/AAAA", "#C62828"); return

            payload = {
                "custo": custo,
                "categoria": categoria,
                "data": data_iso,
                "observacao": (f_obs.value or "").strip(),
            }

            if gasto_editando.get("id"):
                payload["id"] = gasto_editando["id"]
                ok, err = api_atualizar(payload)
                if ok:
                    snack("Gasto atualizado!")
                    limpar_form()
                    recarregar_gastos()
                else:
                    snack(f"Erro: {err}", "#C62828")
            else:
                ok, err = api_inserir(payload)
                if ok:
                    limpar_form()
                    recarregar_gastos()
                    dialogo_sucesso(categoria, custo)
                else:
                    snack(f"Erro: {err}", "#C62828")
        finally:
            _salvando[0] = False

    btn_salvar = mk_btn("Salvar Gasto", salvar_gasto, ft.Icons.SAVE_OUTLINED)

    tela_lancamento = ft.Container(
        expand=True,
        padding=ft.Padding.all(36),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Column([
                    ft.Text("Lançar Gasto", size=24,
                            weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                    ft.Text("Registre os gastos da sua marmitaria",
                            size=13, color=COR_SUBTEXTO),
                ], spacing=4),
                ft.Divider(color=COR_BORDA),
                ft.Container(
                    bgcolor=COR_CARD,
                    border_radius=16,
                    padding=ft.Padding.all(24),
                    border=ft.Border.all(1, COR_BORDA),
                    content=ft.Column(
                        spacing=16,
                        controls=[
                            ft.Text("Informações do Gasto", size=13,
                                    color=COR_SUBTEXTO, weight=ft.FontWeight.W_600),
                            ft.Row([dd_cat, f_custo], spacing=12),
                            ft.Row([f_data, f_obs], spacing=12),
                            ft.Divider(color=COR_BORDA),
                            ft.Row([btn_salvar, btn_cancelar], spacing=16,
                                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ],
                    ),
                ),
            ],
        ),
    )

    pizza_container = ft.Container(
        content=ft.Text("Nenhum dado para exibir.", color=COR_SUBTEXTO, size=13),
        expand=True,
    )
    lista_cards = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8, expand=True)
    total_txt   = ft.Text("Total: R$ 0,00", color=COR_DESTAQUE,
                          size=15, weight=ft.FontWeight.BOLD)

    dd_filtro_cat = ft.Dropdown(
        label="Categoria",
        options=[ft.dropdown.Option("Todas")] +
                [ft.dropdown.Option(c) for c in CATEGORIAS],
        value="Todas",
        bgcolor=COR_CARD, color=COR_TEXTO,
        label_style=ft.TextStyle(color=COR_SUBTEXTO),
        border_color=COR_BORDA, focused_border_color=COR_PRIMARIA,
        border_radius=10, width=200,
    )

    f_de  = mk_campo("De", width=150, hint_text="DD/MM/AAAA", max_length=10)
    f_ate = mk_campo("Até", width=150, hint_text="DD/MM/AAAA", max_length=10)

    f_de.on_change  = lambda e: setattr(e.control, 'value', aplicar_mascara_data(e.control.value)) or e.control.update()
    f_ate.on_change = lambda e: setattr(e.control, 'value', aplicar_mascara_data(e.control.value)) or e.control.update()

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

    def card_gasto(g: dict):
        cor = CORES_CATEGORIA.get(g.get("categoria") or "", COR_PRIMARIA)
        try:
            data_fmt = datetime.strptime(g["data"][:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            data_fmt = g.get("data") or "—"
        obs = g.get("observacao") or ""

        def on_editar(e, gasto=g):
            gasto_editando.clear()
            gasto_editando.update(gasto)
            f_custo.value = str(gasto.get("custo") or "")
            f_data.value  = datetime.strptime(
                gasto["data"][:10], "%Y-%m-%d").strftime("%d/%m/%Y") \
                if gasto.get("data") else ""
            f_obs.value   = gasto.get("observacao") or ""
            dd_cat.value  = gasto.get("categoria")
            btn_salvar.content.controls[1].value = "Atualizar Gasto"
            btn_cancelar.visible = True
            nav_rail.selected_index = 0
            area_conteudo.content = tela_lancamento
            page.update()

        def on_deletar(e, gasto=g):
            log(f">>> on_deletar CHAMADO id={gasto.get('id')}")
            def fechar_dialogo(ev):
                dlg_confirm.open = False
                page.update()

            def executar_exclusao(ev):
                dlg_confirm.open = False
                page.update()
                ok, err = api_deletar(gasto["id"])
                if ok:
                    snack("Gasto removido!")
                    recarregar_gastos()
                else:
                    snack(f"Erro: {err}", "#C62828")

            dlg_confirm = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmar exclusão", color=COR_TEXTO,
                               weight=ft.FontWeight.BOLD),
                content=ft.Text(
                    f"Excluir gasto de R$ {(gasto.get('custo') or 0):,.2f}"
                    f" ({gasto.get('categoria') or '—'})?",
                    color=COR_SUBTEXTO,
                ),
                actions=[
                    ft.TextButton("Cancelar",
                                  style=ft.ButtonStyle(color=COR_SUBTEXTO),
                                  on_click=fechar_dialogo),
                    mk_btn("Excluir", executar_exclusao, bgcolor="#C62828"),
                ],
                bgcolor=COR_CARD,
                shape=ft.RoundedRectangleBorder(radius=14),
            )
            page.overlay.append(dlg_confirm)
            dlg_confirm.open = True
            page.update()

        return ft.Container(
            bgcolor=COR_CARD,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=18, vertical=12),
            border=ft.Border(left=ft.BorderSide(4, cor)),
            content=ft.Row(
                controls=[
                    ft.Container(width=8, height=8, bgcolor=cor, border_radius=4),
                    ft.Column([
                        ft.Text(g.get("categoria") or "—", color=COR_TEXTO,
                                size=14, weight=ft.FontWeight.W_600),
                        ft.Text(
                            (data_fmt or "—") + (f"  •  {obs}" if obs else ""),
                            color=COR_SUBTEXTO, size=11,
                        ),
                    ], spacing=2, expand=True),
                    ft.Text(f"R$ {(g.get('custo') or 0):,.2f}", color=cor,
                            size=15, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.EDIT_OUTLINED,
                                            color=COR_SECUNDARIA, size=18),
                            tooltip="Editar",
                            on_click=on_editar,
                            ink=True, border_radius=20,
                            padding=ft.Padding.all(8),
                        ),
                        ft.Container(
                            content=ft.Icon(ft.Icons.DELETE_OUTLINE,
                                            color="#EF5350", size=18),
                            tooltip="Excluir",
                            on_click=on_deletar,
                            ink=True, border_radius=20,
                            padding=ft.Padding.all(8),
                        ),
                    ], spacing=0),
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
            ),
        )

    def atualizar_dashboard():
        filtrados = filtrar(todos_gastos)
        b64 = gerar_grafico_pizza(filtrados)
        if b64:
            pizza_container.content = ft.Image(
                src="data:image/png;base64," + b64, width=460, fit="contain"
            )
        else:
            pizza_container.content = ft.Text(
                "Nenhum dado para exibir.", color=COR_SUBTEXTO, size=13
            )
        lista_cards.controls.clear()
        for g in sorted(filtrados, key=lambda x: x.get("data") or "", reverse=True):
            lista_cards.controls.append(card_gasto(g))
        total = sum((g.get("custo") or 0) for g in filtrados)
        total_txt.value = f"Total: R$ {total:,.2f}"
        page.update()

    def recarregar_gastos():
        nonlocal todos_gastos
        log(">>> recarregar_gastos")
        dados, err = api_listar()
        if err:
            log(f"  ERRO ao listar: {err}")
            snack(f"Erro na API: {err}", "#C62828")
        todos_gastos = dados
        log(f"  {len(todos_gastos)} gasto(s) carregado(s)")
        atualizar_dashboard()

    def aplicar_filtros(e):
        atualizar_dashboard()

    def limpar_filtros(e):
        dd_filtro_cat.value = "Todas"
        f_de.value = ""
        f_ate.value = ""
        atualizar_dashboard()

    tela_dashboard = ft.Container(
        expand=True,
        padding=ft.Padding.all(24),
        content=ft.Column(
            expand=True,
            spacing=16,
            controls=[
                ft.Row([
                    ft.Column([
                        ft.Text("Dashboard", size=24,
                                weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                        ft.Text("Visão geral dos seus gastos",
                                size=13, color=COR_SUBTEXTO),
                    ], spacing=2, expand=True),
                    total_txt,
                    ft.IconButton(ft.Icons.REFRESH_ROUNDED,
                                  icon_color=COR_SECUNDARIA,
                                  tooltip="Atualizar",
                                  on_click=lambda e: recarregar_gastos()),
                ]),
                ft.Container(
                    bgcolor=COR_CARD,
                    border_radius=12,
                    padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    border=ft.Border.all(1, COR_BORDA),
                    content=ft.Row(
                        [
                            dd_filtro_cat,
                            f_de,
                            f_ate,
                            mk_btn("Filtrar", aplicar_filtros,
                                   icone=ft.Icons.FILTER_ALT_OUTLINED),
                            ft.TextButton(
                                "Limpar",
                                style=ft.ButtonStyle(color=COR_SUBTEXTO),
                                on_click=limpar_filtros,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Row(
                    expand=True,
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(
                            width=500,
                            bgcolor=COR_CARD,
                            border_radius=14,
                            border=ft.Border.all(1, COR_BORDA),
                            padding=ft.Padding.all(20),
                            content=ft.Column([
                                ft.Text("Gastos por Categoria",
                                        color=COR_SUBTEXTO, size=12,
                                        weight=ft.FontWeight.W_600),
                                ft.Divider(color=COR_BORDA, height=12),
                                pizza_container,
                            ], expand=True),
                        ),
                        ft.Container(
                            expand=True,
                            bgcolor=COR_CARD,
                            border_radius=14,
                            border=ft.Border.all(1, COR_BORDA),
                            padding=ft.Padding.all(20),
                            content=ft.Column([
                                ft.Text("Lançamentos", color=COR_SUBTEXTO,
                                        size=12, weight=ft.FontWeight.W_600),
                                ft.Divider(color=COR_BORDA, height=12),
                                lista_cards,
                            ], expand=True),
                        ),
                    ],
                ),
            ],
        ),
    )

    area_conteudo = ft.Container(expand=True, content=tela_lancamento)

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        bgcolor=COR_SIDEBAR,
        indicator_color=COR_PRIMARIA,
        min_width=88,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED,
                selected_icon=ft.Icons.ADD_CIRCLE_ROUNDED,
                label="Lançar",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.BAR_CHART_OUTLINED,
                selected_icon=ft.Icons.BAR_CHART_ROUNDED,
                label="Dashboard",
            ),
        ],
        on_change=lambda e: trocar_tela(e.control.selected_index),
    )

    def trocar_tela(idx: int):
        if idx == 0:
            area_conteudo.content = tela_lancamento
            page.update()
        elif idx == 1:
            area_conteudo.content = tela_dashboard
            recarregar_gastos()

    sidebar = ft.Container(
        width=88,
        bgcolor=COR_SIDEBAR,
        border=ft.Border(right=ft.BorderSide(1, COR_BORDA)),
        content=ft.Column(
            [
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=0, vertical=18),
                    content=ft.Column([
                        ft.Text("COMIDA&", size=12, color=COR_PRIMARIA,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text("AFETO", size=15, color=COR_PRIMARIA,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                ),
                ft.Divider(color=COR_BORDA, height=1),
                ft.Container(expand=True, content=nav_rail),
            ],
            spacing=0,
            expand=True,
        ),
    )

    page.add(
        ft.Row(
            controls=[sidebar, area_conteudo],
            spacing=0,
            expand=True,
        )
    )

    recarregar_gastos()


ft.app(target=main)