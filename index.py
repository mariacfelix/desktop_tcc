import flet as ft
import requests
import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, date, timedelta
from typing import Optional

API_BASE       = "http://localhost:8080"
API_GASTOS     = f"{API_BASE}/apiGastos"
API_MARMITERIA = f"{API_BASE}/apiMarmiteria"
API_CARDAPIO   = f"{API_BASE}/apiCardapio"
API_PEDIDO     = f"{API_BASE}/apiPedido"

state = {"marmiteria_id": None, "marmiteria_nome": None}

CATEGORIAS = [
    "Proteínas", "Carboidratos", "Legumes", "Embalagens", "Gás / Energia",
    "Aluguel", "Transporte", "Mão de Obra", "Equipamentos", "Outros",
]

CORES_CATEGORIA = {
    "Proteínas": "#A0522D", "Carboidratos": "#8B6914", "Legumes": "#6B8E23",
    "Embalagens": "#CC7722", "Gás / Energia": "#CD853F", "Aluguel": "#A0522D",
    "Transporte": "#8B4513", "Mão de Obra": "#D2691E", "Equipamentos": "#B8860B",
    "Outros": "#696969",
}

COR_PRIMARIA   = "#A0522D"
COR_SECUNDARIA = "#FF8C42"
COR_FUNDO      = "#ECE0D4"
COR_CARD       = "#E6D4BA"
COR_SIDEBAR    = "#E6D4BA"
COR_BORDA      = "#563903"
COR_TEXTO      = "#2C2C2C"
COR_SUBTEXTO   = "#4A4A4A"
COR_DESTAQUE   = "#CC7722"
COR_ERRO       = "#C62828"
COR_SUCESSO    = "#388E3C"

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

def mk_campo(label, **kw):
    return ft.TextField(
        label=label, bgcolor=COR_CARD, color=COR_TEXTO,
        label_style=ft.TextStyle(color=COR_SUBTEXTO),
        border_color=COR_BORDA, focused_border_color=COR_PRIMARIA,
        border_radius=10, cursor_color=COR_PRIMARIA, **kw,
    )

def mk_btn(texto, on_click, icone=None, bgcolor=None, cor_texto="white"):
    controles = []
    if icone:
        controles.append(ft.Icon(icone, color=cor_texto, size=16))
    controles.append(ft.Text(texto, color=cor_texto, weight=ft.FontWeight.BOLD))
    return ft.Container(
        content=ft.Row(controles, tight=True, spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=bgcolor or COR_PRIMARIA, border_radius=10, height=44,
        padding=ft.Padding.symmetric(horizontal=20, vertical=0),
        on_click=on_click, ink=True,
    )

def api_get(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        log(f"ERRO GET {url}: {e}")
        return None, str(e)

def api_post(url, payload):
    try:
        r = requests.post(url, json=payload, timeout=5)
        log(f"POST {url} → {r.status_code} | {r.text[:200]}")
        r.raise_for_status()
        return r.json() if r.text.strip() else True, None
    except Exception as e:
        log(f"ERRO POST {url}: {e}")
        return None, str(e)

def api_put(url, payload):
    try:
        r = requests.put(url, json=payload, timeout=5)
        log(f"PUT {url} → {r.status_code}")
        r.raise_for_status()
        return r.json() if r.text.strip() else True, None
    except Exception as e:
        log(f"ERRO PUT {url}: {e}")
        return None, str(e)

def api_patch(url, params=None):
    try:
        r = requests.patch(url, params=params, timeout=5)
        log(f"PATCH {url} → {r.status_code}")
        r.raise_for_status()
        return True, None
    except Exception as e:
        log(f"ERRO PATCH {url}: {e}")
        return False, str(e)

def api_delete(url):
    try:
        r = requests.delete(url, timeout=5)
        log(f"DELETE {url} → {r.status_code}")
        r.raise_for_status()
        return True, None
    except Exception as e:
        log(f"ERRO DELETE {url}: {e}")
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
        cores.append(CORES_CATEGORIA.get(cat, "#696969"))
    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    ax.pie(sizes, labels=None, autopct=lambda pct: f"{pct:.1f}%", colors=cores,
           startangle=140, wedgeprops=dict(width=0.6, edgecolor="none", linewidth=0),
           pctdistance=0.78, textprops={"color": COR_TEXTO, "fontsize": 8})
    handles = [mpatches.Patch(color=cores[i], label=f"{labels[i]}  R${sizes[i]:,.2f}") for i in range(len(labels))]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5),
              fontsize=8, framealpha=0, labelcolor=COR_SUBTEXTO)
    ax.set_title(f"Total: R${sum(sizes):,.2f}", color=COR_PRIMARIA, fontsize=11, fontweight="bold", pad=10)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def main(page: ft.Page):
    page.title = "Comida & Afeto"
    page.bgcolor = COR_FUNDO
    page.window.width = 1150
    page.window.height = 750
    page.window.min_width = 900
    page.window.min_height = 600
    page.padding = 0

    todos_gastos: list = []
    gasto_editando: dict = {}
    _salvando = [False]

    def snack(msg: str, cor: str = COR_SUCESSO):
        page.snack_bar = ft.SnackBar(ft.Text(msg, color="white"), bgcolor=cor, duration=2500)
        page.snack_bar.open = True
        page.update()

    def abrir_dialogo(dlg):
        page.dialog = dlg
        page.dialog.open = True
        page.update()

    def fechar_dialogo(e=None):
        if page.dialog:
            page.dialog.open = False
        page.update()

    def dialogo_sucesso(titulo: str, corpo: str):
        abrir_dialogo(ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=COR_SUCESSO, size=28),
                ft.Text(f"  {titulo}", color=COR_TEXTO, weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Text(corpo, color=COR_SUBTEXTO, size=14),
            actions=[mk_btn("OK", fechar_dialogo)],
            bgcolor=COR_CARD, shape=ft.RoundedRectangleBorder(radius=14),
        ))

    area_conteudo = ft.Container(expand=True)

    def trocar_tela(idx: int):
        telas = [tela_gastos, tela_dashboard, tela_cardapio, tela_pedidos, tela_debug]
        area_conteudo.content = telas[idx]
        if idx == 1:
            recarregar_gastos()
        elif idx == 2:
            recarregar_cardapios()
        elif idx == 3:
            recarregar_pedidos()
        else:
            page.update()

    f_login_user = mk_campo("E-mail", width=320)
    f_login_senha = mk_campo("Senha", width=320, password=True, can_reveal_password=True)
    txt_login_erro = ft.Text("", color=COR_ERRO, size=13)

    def fazer_login(e):
        user = (f_login_user.value or "").strip()
        senha = (f_login_senha.value or "").strip()
        if not user or not senha:
            txt_login_erro.value = "Preencha e-mail e senha."
            page.update()
            return
        dados, err = api_post(f"{API_MARMITERIA}/login", {"username": user, "senha": senha})
        if err or not dados:
            txt_login_erro.value = "Usuário ou senha inválidos."
            page.update()
            return
        state["marmiteria_id"] = dados["id"]
        state["marmiteria_nome"] = dados["nome"]
        txt_login_erro.value = ""
        page.controls.clear()
        page.add(tela_principal)
        recarregar_gastos()
        page.update()

    tela_login = ft.Container(
        expand=True,
        bgcolor=COR_FUNDO,
        content=ft.Column(
            [
                ft.Image(src="assets/images/logo.png", width=100, height=100),
                ft.Text("Comida & Afeto", size=28, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                ft.Text("Gestão da sua marmitaria", size=14, color=COR_SUBTEXTO),
                ft.Container(height=20),
                ft.Container(
                    bgcolor=COR_CARD, border_radius=16,
                    padding=ft.Padding.all(32),
                    border=ft.Border.all(1, COR_BORDA),
                    content=ft.Column([
                        ft.Text("Entrar", size=18, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                        ft.Container(height=8),
                        f_login_user,
                        f_login_senha,
                        txt_login_erro,
                        ft.Container(height=4),
                        mk_btn("Entrar", fazer_login, ft.Icons.LOGIN_ROUNDED),
                    ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        ),
    )

    f_custo = mk_campo("Valor (R$)", keyboard_type=ft.KeyboardType.NUMBER, width=180)
    f_obs   = mk_campo("Observação (opcional)", expand=True)
    f_data  = mk_campo("Data", width=210, value=date.today().strftime("%d/%m/%Y"),
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
        options=[ft.dropdown.Option(c) for c in CATEGORIAS],
        bgcolor=COR_CARD, color=COR_TEXTO,
        label_style=ft.TextStyle(color=COR_SUBTEXTO),
        border_color=COR_BORDA, focused_border_color=COR_PRIMARIA,
        border_radius=10, expand=True,
    )

    btn_cancelar_gasto = ft.TextButton("✕  Cancelar edição",
                                       style=ft.ButtonStyle(color=COR_SUBTEXTO), visible=False)

    def limpar_form_gasto():
        gasto_editando.clear()
        f_custo.value = ""
        f_data.value = date.today().strftime("%d/%m/%Y")
        f_obs.value = ""
        dd_cat.value = None
        btn_salvar_gasto.content.controls[1].value = "Salvar Gasto"
        btn_cancelar_gasto.visible = False
        page.update()

    btn_cancelar_gasto.on_click = lambda e: limpar_form_gasto()

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
            except ValueError:
                snack("Valor inválido!", COR_ERRO); return
            try:
                data_iso = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            except Exception:
                snack("Data inválida! Use DD/MM/AAAA", COR_ERRO); return
            payload = {"custo": custo, "categoria": categoria, "data": data_iso,
                       "observacao": (f_obs.value or "").strip()}
            if gasto_editando.get("id"):
                payload["id"] = gasto_editando["id"]
                payload["marmiteria"] = {"id": state["marmiteria_id"]}
                ok, err = api_put(f"{API_GASTOS}/atualizar", payload)
                if ok:
                    snack("Gasto atualizado!")
                    limpar_form_gasto()
                    recarregar_gastos()
                else:
                    snack(f"Erro: {err}", COR_ERRO)
            else:
                payload["marmiteriaId"] = state["marmiteria_id"]
                ok, err = api_post(f"{API_GASTOS}/inserir", payload)
                if ok:
                    limpar_form_gasto()
                    recarregar_gastos()
                    dialogo_sucesso("Gasto registrado!", f"{categoria} — R$ {custo:,.2f}")
                else:
                    snack(f"Erro: {err}", COR_ERRO)
        finally:
            _salvando[0] = False

    btn_salvar_gasto = mk_btn("Salvar Gasto", salvar_gasto, ft.Icons.SAVE_OUTLINED)

    tela_gastos = ft.Container(
        expand=True, padding=ft.Padding.all(36),
        content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=20, controls=[
            ft.Column([
                ft.Text("Lançar Gasto", size=24, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                ft.Text("Registre os gastos da sua marmitaria", size=13, color=COR_SUBTEXTO),
            ], spacing=4),
            ft.Divider(color=COR_BORDA),
            ft.Container(
                bgcolor=COR_CARD, border_radius=16, padding=ft.Padding.all(24),
                border=ft.Border.all(1, COR_BORDA),
                content=ft.Column(spacing=16, controls=[
                    ft.Text("Informações do Gasto", size=13, color=COR_SUBTEXTO, weight=ft.FontWeight.W_600),
                    ft.Row([dd_cat, f_custo], spacing=12),
                    ft.Row([f_data, f_obs], spacing=12),
                    ft.Divider(color=COR_BORDA),
                    ft.Row([btn_salvar_gasto, btn_cancelar_gasto], spacing=16,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ]),
            ),
        ]),
    )

    pizza_container = ft.Container(
        content=ft.Text("Nenhum dado para exibir.", color=COR_SUBTEXTO, size=13), expand=True)
    lista_cards_gastos = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8, expand=True)
    total_txt = ft.Text("Total: R$ 0,00", color=COR_DESTAQUE, size=15, weight=ft.FontWeight.BOLD)

    dd_filtro_cat = ft.Dropdown(
        label="Categoria", value="Todas",
        options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(c) for c in CATEGORIAS],
        bgcolor=COR_CARD, color=COR_TEXTO,
        label_style=ft.TextStyle(color=COR_SUBTEXTO),
        border_color=COR_BORDA, focused_border_color=COR_PRIMARIA,
        border_radius=10, width=200,
    )
    f_de = mk_campo("De", width=150, hint_text="DD/MM/AAAA")
    f_ate = mk_campo("Até", width=150, hint_text="DD/MM/AAAA")

    def on_filtro_data(e):
        c = e.control
        novo = aplicar_mascara_data(c.value)
        if c.value != novo:
            c.value = novo
            c.update()

    f_de.on_change = on_filtro_data
    f_ate.on_change = on_filtro_data

    def filtrar_gastos(gastos):
        res = gastos
        cat_sel = dd_filtro_cat.value or "Todas"
        if cat_sel != "Todas":
            res = [g for g in res if (g.get("categoria") or "") == cat_sel]
        try:
            d_de = datetime.strptime(f_de.value.strip(), "%d/%m/%Y").date() if (f_de.value or "").strip() else None
        except Exception:
            d_de = None
        try:
            d_ate = datetime.strptime(f_ate.value.strip(), "%d/%m/%Y").date() if (f_ate.value or "").strip() else None
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
            f_data.value = datetime.strptime(gasto["data"][:10], "%Y-%m-%d").strftime("%d/%m/%Y") if gasto.get("data") else ""
            f_obs.value = gasto.get("observacao", "") or ""
            dd_cat.value = gasto.get("categoria")
            btn_salvar_gasto.content.controls[1].value = "Atualizar Gasto"
            btn_cancelar_gasto.visible = True
            _on_nav(0)

        def on_deletar(e, gasto=g):
            def confirmar(ev):
                fechar_dialogo()
                if ev.control.text == "Excluir":
                    ok, err = api_delete(f"{API_GASTOS}/remover/{gasto['id']}")
                    if ok:
                        snack("Gasto removido!")
                        recarregar_gastos()
                    else:
                        snack(f"Erro: {err}", COR_ERRO)

            abrir_dialogo(ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmar exclusão", color=COR_TEXTO, weight=ft.FontWeight.BOLD),
                content=ft.Text(f"Excluir gasto de R$ {(gasto.get('custo') or 0):,.2f} ({gasto.get('categoria', '—')})?", color=COR_SUBTEXTO),
                actions=[
                    ft.TextButton("Cancelar", style=ft.ButtonStyle(color=COR_SUBTEXTO), on_click=confirmar),
                    mk_btn("Excluir", confirmar, bgcolor=COR_ERRO),
                ],
                bgcolor=COR_CARD, shape=ft.RoundedRectangleBorder(radius=14),
            ))

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
                    ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=COR_SECUNDARIA, tooltip="Editar", on_click=on_editar, icon_size=18),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=COR_ERRO, tooltip="Excluir", on_click=on_deletar, icon_size=18),
                ], spacing=0),
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
        )

    def atualizar_dashboard():
        filtrados = filtrar_gastos(todos_gastos)
        b64 = gerar_grafico_pizza(filtrados)
        pizza_container.content = ft.Image(src="data:image/png;base64," + b64, width=460, fit="contain") if b64 \
            else ft.Text("Nenhum dado para exibir.", color=COR_SUBTEXTO, size=13)
        lista_cards_gastos.controls.clear()
        for g in sorted(filtrados, key=lambda x: x.get("data") or "", reverse=True):
            lista_cards_gastos.controls.append(card_gasto(g))
        total = sum((g.get("custo") or 0) for g in filtrados)
        total_txt.value = f"Total: R$ {total:,.2f}"
        page.update()

    def recarregar_gastos():
        nonlocal todos_gastos
        dados, err = api_get(f"{API_GASTOS}/todos", {"marmiteriaId": state["marmiteria_id"]})
        todos_gastos = dados or []
        atualizar_dashboard()

    def aplicar_filtros(e):
        atualizar_dashboard()

    def limpar_filtros(e):
        dd_filtro_cat.value = "Todas"
        f_de.value = f_ate.value = ""
        atualizar_dashboard()

    tela_dashboard = ft.Container(
        expand=True, padding=ft.Padding.all(24),
        content=ft.Column(expand=True, spacing=16, controls=[
            ft.Row([
                ft.Column([
                    ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                    ft.Text("Visão geral dos seus gastos", size=13, color=COR_SUBTEXTO),
                ], spacing=2, expand=True),
                total_txt,
                ft.IconButton(ft.Icons.REFRESH_ROUNDED, icon_color=COR_SECUNDARIA,
                              tooltip="Atualizar", on_click=lambda e: recarregar_gastos()),
            ]),
            ft.Container(
                bgcolor=COR_CARD, border_radius=12,
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                border=ft.Border.all(1, COR_BORDA),
                content=ft.Row([
                    dd_filtro_cat, f_de, f_ate,
                    mk_btn("Filtrar", aplicar_filtros, ft.Icons.FILTER_ALT_OUTLINED),
                    ft.TextButton("Limpar", style=ft.ButtonStyle(color=COR_SUBTEXTO), on_click=limpar_filtros),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            ft.Row(expand=True, spacing=16, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
                ft.Container(
                    width=500, bgcolor=COR_CARD, border_radius=14,
                    border=ft.Border.all(1, COR_BORDA), padding=ft.Padding.all(20),
                    content=ft.Column([
                        ft.Text("Gastos por Categoria", color=COR_SUBTEXTO, size=12, weight=ft.FontWeight.W_600),
                        ft.Divider(color=COR_BORDA, height=12),
                        pizza_container,
                    ], expand=True),
                ),
                ft.Container(
                    expand=True, bgcolor=COR_CARD, border_radius=14,
                    border=ft.Border.all(1, COR_BORDA), padding=ft.Padding.all(20),
                    content=ft.Column([
                        ft.Text("Lançamentos", color=COR_SUBTEXTO, size=12, weight=ft.FontWeight.W_600),
                        ft.Divider(color=COR_BORDA, height=12),
                        lista_cards_gastos,
                    ], expand=True),
                ),
            ]),
        ]),
    )

    lista_cardapios = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8)
    f_card_nome = mk_campo("Nome do cardápio", expand=True)
    f_card_validade = mk_campo("Validade", width=180, hint_text="DD/MM/AAAA")
    f_card_validade.on_change = on_data_change
    chk_sem_validade = ft.Checkbox(label="Sem validade", value=False,
                                   active_color=COR_PRIMARIA,
                                   label_style=ft.TextStyle(color=COR_TEXTO))
    ingredientes_form: list = []
    col_ingredientes = ft.Column(spacing=8)
    cardapio_editando: dict = {}

    def chk_validade_change(e):
        f_card_validade.disabled = chk_sem_validade.value
        f_card_validade.update()

    chk_sem_validade.on_change = chk_validade_change

    def linha_ingrediente(idx: int, nome="", valor=""):
        f_nome = mk_campo(f"Ingrediente {idx + 1}", expand=True, value=nome)
        f_valor = mk_campo("R$/g", width=120, value=valor, keyboard_type=ft.KeyboardType.NUMBER)
        linha = {"nome": f_nome, "valor": f_valor}
        ingredientes_form.append(linha)

        def remover(e):
            ingredientes_form.remove(linha)
            col_ingredientes.controls.remove(row)
            col_ingredientes.update()

        row = ft.Row([f_nome, f_valor,
                      ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=COR_ERRO,
                                    icon_size=18, on_click=remover)], spacing=8)
        return row

    def adicionar_ingrediente(e):
        idx = len(ingredientes_form)
        row = linha_ingrediente(idx)
        col_ingredientes.controls.append(row)
        col_ingredientes.update()

    def limpar_form_cardapio():
        cardapio_editando.clear()
        f_card_nome.value = ""
        f_card_validade.value = ""
        f_card_validade.disabled = False
        chk_sem_validade.value = False
        ingredientes_form.clear()
        col_ingredientes.controls.clear()
        for i in range(3):
            col_ingredientes.controls.append(linha_ingrediente(i))
        page.update()

    def salvar_cardapio(e):
        nome = (f_card_nome.value or "").strip()
        sem_val = chk_sem_validade.value
        validade_str = (f_card_validade.value or "").strip()
        if not nome:
            snack("Informe o nome do cardápio!", COR_ERRO); return
        validade_iso = None
        if not sem_val:
            if not validade_str:
                snack("Informe a validade ou marque 'Sem validade'.", COR_ERRO); return
            try:
                validade_iso = datetime.strptime(validade_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            except Exception:
                snack("Data de validade inválida!", COR_ERRO); return
        ings = []
        for idx, linha in enumerate(ingredientes_form):
            n = (linha["nome"].value or "").strip()
            v = (linha["valor"].value or "").replace(",", ".")
            if not n:
                continue
            try:
                vf = float(v)
            except Exception:
                snack(f"Valor inválido no ingrediente '{n}'", COR_ERRO); return
            ings.append({"nome": n, "valorPorGramas": vf, "posicao": idx + 1})

        payload = {
            "nome": nome,
            "validade": validade_iso,
            "semValidade": sem_val,
            "aberto": True,
            "ingredientes": ings,
            "marmiteria": {"id": state["marmiteria_id"]},
        }

        if cardapio_editando.get("id"):
            payload["id"] = cardapio_editando["id"]
            ok, err = api_put(f"{API_CARDAPIO}/atualizar", payload)
            if ok:
                snack("Cardápio atualizado!")
                limpar_form_cardapio()
                recarregar_cardapios()
            else:
                snack(f"Erro: {err}", COR_ERRO)
        else:
            ok, err = api_post(f"{API_CARDAPIO}/inserir", payload)
            if ok:
                dialogo_sucesso("Cardápio criado!", f"'{nome}' foi criado com sucesso.")
                limpar_form_cardapio()
                recarregar_cardapios()
            else:
                snack(f"Erro: {err}", COR_ERRO)

    btn_cancelar_card = ft.TextButton("✕  Cancelar edição",
                                      style=ft.ButtonStyle(color=COR_SUBTEXTO), visible=False)
    btn_cancelar_card.on_click = lambda e: limpar_form_cardapio()

    def recarregar_cardapios():
        dados, err = api_get(f"{API_CARDAPIO}/todos", {"marmiteriaId": state["marmiteria_id"]})
        cardapios = dados or []
        lista_cardapios.controls.clear()

        for c in cardapios:
            aberto = c.get("aberto", True)
            validade = c.get("validade") or ""
            sem_val = c.get("semValidade", False)
            val_fmt = "Sem validade" if sem_val else (
                datetime.strptime(validade[:10], "%Y-%m-%d").strftime("%d/%m/%Y") if validade else "—")
            ings = c.get("ingredientes") or []

            def toggle_aberto(e, cid=c["id"], nome_card=c.get("nome","?")):
                novo = str(e.data).lower() == "true"
                log(f">>> toggle_aberto: cid={cid} novo={novo} e.data={e.data}")
                ok, err = api_patch(
                    f"{API_CARDAPIO}/aberto/{cid}",
                    {"aberto": str(novo).lower()}
                )
                log(f">>> PATCH resultado: ok={ok} err={err}")
                if ok:
                    snack(f"'{nome_card}' {'aberto' if novo else 'fechado'} para pedidos.")
                else:
                    snack(f"Erro: {err}", COR_ERRO)
                recarregar_cardapios()

            def editar_cardapio(e, card=c):
                cardapio_editando.clear()
                cardapio_editando.update(card)
                f_card_nome.value = card.get("nome", "")
                sem = card.get("semValidade", False)
                chk_sem_validade.value = sem
                f_card_validade.disabled = sem
                v = card.get("validade") or ""
                f_card_validade.value = datetime.strptime(v[:10], "%Y-%m-%d").strftime("%d/%m/%Y") if v else ""
                ingredientes_form.clear()
                col_ingredientes.controls.clear()
                for idx, ing in enumerate(card.get("ingredientes") or []):
                    col_ingredientes.controls.append(
                        linha_ingrediente(idx, ing.get("nome", ""), str(ing.get("valorPorGramas", ""))))
                if not col_ingredientes.controls:
                    for i in range(3):
                        col_ingredientes.controls.append(linha_ingrediente(i))
                btn_cancelar_card.visible = True
                page.update()

            def deletar_cardapio(e, card=c):
                def confirmar(ev):
                    fechar_dialogo()
                    if ev.control.text == "Excluir":
                        api_delete(f"{API_CARDAPIO}/remover/{card['id']}")
                        recarregar_cardapios()

                abrir_dialogo(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Excluir cardápio?", color=COR_TEXTO, weight=ft.FontWeight.BOLD),
                    content=ft.Text(f"Excluir '{card.get('nome')}'? Todos os pedidos vinculados serão removidos.", color=COR_SUBTEXTO),
                    actions=[
                        ft.TextButton("Cancelar", style=ft.ButtonStyle(color=COR_SUBTEXTO), on_click=confirmar),
                        mk_btn("Excluir", confirmar, bgcolor=COR_ERRO),
                    ],
                    bgcolor=COR_CARD, shape=ft.RoundedRectangleBorder(radius=14),
                ))

            lista_cardapios.controls.append(ft.Container(
                bgcolor=COR_FUNDO, border_radius=12,
                padding=ft.Padding.symmetric(horizontal=18, vertical=14),
                border=ft.Border(left=ft.BorderSide(4, COR_SUCESSO if aberto else COR_ERRO)),
                content=ft.Row([
                    ft.Column([
                        ft.Text(c.get("nome", "—"), color=COR_TEXTO, size=14, weight=ft.FontWeight.W_600),
                        ft.Text(f"Validade: {val_fmt}  •  {len(ings)} ingrediente(s)", color=COR_SUBTEXTO, size=11),
                        ft.Container(height=4),
                        ft.Row([
                            ft.Switch(
                                value=aberto,
                                active_color=COR_SUCESSO,
                                inactive_thumb_color=COR_ERRO,
                                inactive_track_color="#FFCDD2",
                                on_change=toggle_aberto,
                                label="Aberto para pedidos" if aberto else "Fechado",
                                label_text_style=ft.TextStyle(
                                    color=COR_SUCESSO if aberto else COR_ERRO,
                                    size=12, weight=ft.FontWeight.W_600,
                                ),
                            ),
                        ], spacing=4),
                    ], spacing=2, expand=True),
                    ft.Row([
                        ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=COR_SECUNDARIA,
                                      tooltip="Editar", on_click=editar_cardapio, icon_size=18),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=COR_ERRO,
                                      tooltip="Excluir", on_click=deletar_cardapio, icon_size=18),
                    ], spacing=0),
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
            ))

        page.update()

    for i in range(3):
        col_ingredientes.controls.append(linha_ingrediente(i))

    tela_cardapio = ft.Container(
        expand=True, padding=ft.Padding.all(30),
        content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=20, controls=[
            ft.Column([
                ft.Text("Cardápio", size=24, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                ft.Text("Gerencie os cardápios da sua marmitaria", size=13, color=COR_SUBTEXTO),
            ], spacing=4),
            ft.Divider(color=COR_BORDA),
            ft.Container(
                bgcolor=COR_CARD, border_radius=16, padding=ft.Padding.all(24),
                border=ft.Border.all(1, COR_BORDA),
                content=ft.Column(spacing=14, controls=[
                    ft.Text("Novo Cardápio", size=13, color=COR_SUBTEXTO, weight=ft.FontWeight.W_600),
                    ft.Row([f_card_nome, f_card_validade, chk_sem_validade], spacing=12,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Text("Ingredientes", size=12, color=COR_SUBTEXTO, weight=ft.FontWeight.W_600),
                    col_ingredientes,
                    ft.TextButton(
                        content=ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=COR_PRIMARIA, size=16),
                                        ft.Text("Adicionar ingrediente", color=COR_PRIMARIA, weight=ft.FontWeight.BOLD)],
                                       tight=True, spacing=6),
                        on_click=adicionar_ingrediente,
                    ),
                    ft.Divider(color=COR_BORDA),
                    ft.Row([mk_btn("Salvar Cardápio", salvar_cardapio, ft.Icons.SAVE_OUTLINED), btn_cancelar_card],
                           spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ]),
            ),
            ft.Text("Cardápios cadastrados", size=16, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
            lista_cardapios,
        ]),
    )

    lista_pedidos = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8, expand=True)
    _pedidos_state: list = []          # cache dos pedidos carregados
    _checks_pedidos: dict = {}         # pid -> Checkbox ref

    def _conteudo_etiqueta(pedido: dict):
        nome_cliente = pedido.get("nomeCliente") or "—"
        cardapio_nome = pedido.get("cardapioNome") or "—"
        ings = pedido.get("ingredientes") or []
        validade_etiqueta = (date.today() + timedelta(days=30)).strftime("%d/%m/%Y")
        itens_ings = [
            ft.Row([ft.Icon(ft.Icons.FIBER_MANUAL_RECORD, size=8, color=COR_PRIMARIA),
                    ft.Text(i.get("nome", "—"), size=12, color=COR_SUBTEXTO)], spacing=4)
            for i in ings
        ] if ings else [ft.Text("Sem ingredientes", size=12, color=COR_SUBTEXTO)]

        return ft.Container(
            width=340, bgcolor=COR_FUNDO, border_radius=10,
            padding=ft.Padding.all(20),
            border=ft.Border.all(2, COR_BORDA),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LUNCH_DINING, color=COR_PRIMARIA, size=20),
                    ft.Text("Comida & Afeto", size=16, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                ], spacing=8),
                ft.Divider(color=COR_BORDA),
                ft.Text(f"Cliente: {nome_cliente}", size=13, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                ft.Text(f"Cardápio: {cardapio_nome}", size=12, color=COR_SUBTEXTO),
                ft.Divider(color=COR_BORDA),
                ft.Text("Ingredientes:", size=12, weight=ft.FontWeight.W_600, color=COR_TEXTO),
                *itens_ings,
                ft.Divider(color=COR_BORDA),
                ft.Text(f"Validade: {validade_etiqueta}", size=13, weight=ft.FontWeight.BOLD, color=COR_DESTAQUE),
            ], spacing=6),
        )

    def imprimir_etiqueta(pedido: dict):
        abrir_dialogo(ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.LABEL_OUTLINE, color=COR_PRIMARIA, size=24),
                ft.Text("  Etiqueta", color=COR_TEXTO, weight=ft.FontWeight.BOLD),
            ]),
            content=_conteudo_etiqueta(pedido),
            actions=[
                ft.TextButton("Fechar", style=ft.ButtonStyle(color=COR_SUBTEXTO), on_click=fechar_dialogo),
            ],
            bgcolor=COR_CARD, shape=ft.RoundedRectangleBorder(radius=14),
        ))

    def imprimir_etiquetas_selecionadas(e):
        selecionados = [p for p in _pedidos_state
                        if _checks_pedidos.get(p.get("id")) and _checks_pedidos[p.get("id")].value]
        if not selecionados:
            snack("Selecione ao menos um pedido!", COR_ERRO)
            return

        etiquetas = []
        for p in selecionados:
            etiquetas.append(_conteudo_etiqueta(p))
            etiquetas.append(ft.Divider(color=COR_BORDA, height=16))

        abrir_dialogo(ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.PRINT, color=COR_PRIMARIA, size=24),
                ft.Text(f"  {len(selecionados)} Etiqueta(s)", color=COR_TEXTO, weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Container(
                width=380,
                height=500,
                content=ft.Column(etiquetas, scroll=ft.ScrollMode.AUTO, spacing=0),
            ),
            actions=[
                ft.TextButton("Fechar", style=ft.ButtonStyle(color=COR_SUBTEXTO), on_click=fechar_dialogo),
            ],
            bgcolor=COR_CARD, shape=ft.RoundedRectangleBorder(radius=14),
        ))

    def selecionar_todos_pedidos(e):
        for chk in _checks_pedidos.values():
            chk.value = True
            chk.update()

    def desselecionar_todos_pedidos(e):
        for chk in _checks_pedidos.values():
            chk.value = False
            chk.update()

    def recarregar_pedidos():
        nonlocal _pedidos_state
        dados, err = api_get(f"{API_PEDIDO}/todos", {"marmiteriaId": state["marmiteria_id"]})
        pedidos = dados or []
        _pedidos_state = pedidos
        _checks_pedidos.clear()
        lista_pedidos.controls.clear()

        if not pedidos:
            lista_pedidos.controls.append(
                ft.Text("Nenhum pedido encontrado.", color=COR_SUBTEXTO, size=13))
        else:
            for p in sorted(pedidos, key=lambda x: x.get("dataCriada") or "", reverse=True):
                pid = p.get("id")
                nome = p.get("nomeCliente") or "—"
                cardapio_nome = p.get("cardapioNome") or "—"
                valor = p.get("valor") or 0
                status_val = p.get("status") or "—"
                ings = p.get("ingredientes") or []

                # ── Cor e ícone de status (aberto/fechado) ──────────────────
                aberto_cardapio = p.get("cardapioAberto")  # pode não vir da API
                cor_status = COR_SUCESSO if status_val == "PENDENTE" else COR_SUBTEXTO
                icone_status = ft.Icons.PENDING_ACTIONS if status_val == "PENDENTE" else ft.Icons.CHECK_CIRCLE_OUTLINE

                chk = ft.Checkbox(value=False, active_color=COR_PRIMARIA)
                _checks_pedidos[pid] = chk

                def on_deletar_pedido(e, ped=p):
                    def confirmar(ev):
                        fechar_dialogo()
                        if ev.control.text == "Excluir":
                            api_delete(f"{API_PEDIDO}/remover/{ped['id']}")
                            recarregar_pedidos()
                    abrir_dialogo(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Excluir pedido?", color=COR_TEXTO, weight=ft.FontWeight.BOLD),
                        content=ft.Text(f"Excluir pedido de {ped.get('nomeCliente', '—')}?", color=COR_SUBTEXTO),
                        actions=[
                            ft.TextButton("Cancelar", style=ft.ButtonStyle(color=COR_SUBTEXTO), on_click=confirmar),
                            mk_btn("Excluir", confirmar, bgcolor=COR_ERRO),
                        ],
                        bgcolor=COR_CARD, shape=ft.RoundedRectangleBorder(radius=14),
                    ))

                lista_pedidos.controls.append(ft.Container(
                    bgcolor=COR_FUNDO, border_radius=12,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=12),
                    border=ft.Border(left=ft.BorderSide(4, COR_PRIMARIA)),
                    content=ft.Row([
                        chk,
                        ft.Column([
                            ft.Text(nome, color=COR_TEXTO, size=14, weight=ft.FontWeight.W_600),
                            ft.Text(f"Cardápio: {cardapio_nome}  •  {len(ings)} ingrediente(s)",
                                    color=COR_SUBTEXTO, size=11),
                            ft.Row([
                                ft.Icon(icone_status, color=cor_status, size=12),
                                ft.Text(status_val, color=cor_status, size=11,
                                        weight=ft.FontWeight.W_600),
                            ], spacing=4),
                        ], spacing=3, expand=True),
                        ft.Text(f"R$ {float(valor):,.2f}", color=COR_DESTAQUE,
                                size=15, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.IconButton(
                                ft.Icons.LABEL_OUTLINE, icon_color=COR_DESTAQUE,
                                tooltip="Ver etiqueta",
                                on_click=lambda e, ped=p: imprimir_etiqueta(ped),
                                icon_size=20,
                            ),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=COR_ERRO,
                                          tooltip="Excluir", on_click=on_deletar_pedido, icon_size=20),
                        ], spacing=0),
                    ], alignment=ft.MainAxisAlignment.START,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                ))

        page.update()

    tela_pedidos = ft.Container(
        expand=True, padding=ft.Padding.all(30),
        content=ft.Column(expand=True, spacing=16, controls=[
            ft.Row([
                ft.Column([
                    ft.Text("Pedidos", size=24, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                    ft.Text("Pedidos recebidos pela sua marmitaria", size=13, color=COR_SUBTEXTO),
                ], spacing=2, expand=True),
                ft.IconButton(ft.Icons.REFRESH_ROUNDED, icon_color=COR_SECUNDARIA,
                              tooltip="Atualizar", on_click=lambda e: recarregar_pedidos()),
            ]),
            ft.Divider(color=COR_BORDA),
            # ── Barra de ações em lote ───────────────────────────────────
            ft.Container(
                bgcolor=COR_CARD, border_radius=10,
                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                border=ft.Border.all(1, COR_BORDA),
                content=ft.Row([
                    ft.TextButton(
                        content=ft.Row([ft.Icon(ft.Icons.CHECK_BOX_OUTLINED, color=COR_PRIMARIA, size=16),
                                        ft.Text("Selecionar todos", color=COR_PRIMARIA, size=13)], spacing=4, tight=True),
                        on_click=selecionar_todos_pedidos,
                    ),
                    ft.TextButton(
                        content=ft.Row([ft.Icon(ft.Icons.CHECK_BOX_OUTLINE_BLANK, color=COR_SUBTEXTO, size=16),
                                        ft.Text("Desmarcar todos", color=COR_SUBTEXTO, size=13)], spacing=4, tight=True),
                        on_click=desselecionar_todos_pedidos,
                    ),
                    ft.Container(expand=True),
                    mk_btn("Imprimir selecionados", imprimir_etiquetas_selecionadas,
                           ft.Icons.PRINT_OUTLINED, COR_PRIMARIA),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            lista_pedidos,
        ]),
    )

    status_api_icon = ft.Icon(ft.Icons.CIRCLE, color="grey", size=14)
    status_api_txt  = ft.Text("Não testado", color=COR_SUBTEXTO, size=13)
    log_view = ft.ListView(expand=True, spacing=2, auto_scroll=True)

    def testar_api(e):
        log("=== TESTE DE CONEXÃO ===")
        try:
            r = requests.get(f"{API_GASTOS}/todos", params={"marmiteriaId": state["marmiteria_id"]}, timeout=5)
            log(f"  HTTP {r.status_code} | {r.text[:300]}")
            status_api_icon.color = "#4CAF50" if r.status_code == 200 else "#FF9800"
            status_api_txt.value = f"API OK — {r.status_code}" if r.status_code == 200 else f"Erro {r.status_code}"
        except Exception as ex:
            log(f"  FALHA: {ex}")
            status_api_icon.color = "#F44336"
            status_api_txt.value = f"Sem conexão: {ex}"
        atualizar_log_view()
        page.update()

    def limpar_logs(e):
        _logs.clear()
        atualizar_log_view()
        page.update()

    def atualizar_log_view():
        log_view.controls.clear()
        for entrada in _logs:
            cor = "#F44336" if any(x in entrada for x in ["ERRO", "FALHOU", "FALHA"]) \
                else "#4CAF50" if "OK" in entrada \
                else "#FF9800" if any(x in entrada for x in [">>>", "==="]) \
                else COR_SUBTEXTO
            log_view.controls.append(
                ft.Text(entrada, color=cor, size=11, font_family="monospace", selectable=True))

    tela_debug = ft.Container(
        expand=True, padding=ft.Padding.all(24),
        content=ft.Column(expand=True, spacing=16, controls=[
            ft.Column([
                ft.Text("Debug", size=24, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                ft.Text("Diagnóstico e logs em tempo real", size=13, color=COR_SUBTEXTO),
            ], spacing=4),
            ft.Divider(color=COR_BORDA),
            ft.Container(
                bgcolor=COR_CARD, border_radius=12, padding=ft.Padding.all(20),
                border=ft.Border.all(1, COR_BORDA),
                content=ft.Column([
                    ft.Row([status_api_icon, status_api_txt,
                            ft.Text(f"  ({API_BASE})", color=COR_BORDA, size=11)]),
                    ft.Divider(color=COR_BORDA, height=8),
                    ft.Row([
                        mk_btn("Testar conexão", testar_api, ft.Icons.WIFI_ROUNDED, "#1565C0"),
                        mk_btn("Limpar logs", limpar_logs, ft.Icons.DELETE_SWEEP_OUTLINED, "#B71C1C"),
                    ], spacing=10),
                ], spacing=10),
            ),
            ft.Container(
                expand=True, bgcolor=COR_CARD, border_radius=12,
                padding=ft.Padding.all(16), border=ft.Border.all(1, COR_BORDA),
                content=ft.Column([
                    ft.Text("Log de requisições", color=COR_SUBTEXTO, size=12, weight=ft.FontWeight.W_600),
                    ft.Divider(color=COR_BORDA, height=8),
                    log_view,
                ], expand=True),
            ),
        ]),
    )

    _idx_selecionado = [0]

    ITENS_NAV = [
        (ft.Icons.RECEIPT_LONG_OUTLINED, ft.Icons.RECEIPT_LONG,       "Gastos"),
        (ft.Icons.BAR_CHART_OUTLINED,    ft.Icons.BAR_CHART_ROUNDED,  "Dashboard"),
        (ft.Icons.MENU_BOOK_OUTLINED,    ft.Icons.MENU_BOOK,          "Cardápio"),
        (ft.Icons.SHOPPING_BAG_OUTLINED, ft.Icons.SHOPPING_BAG,       "Pedidos"),
        (ft.Icons.BUG_REPORT_OUTLINED,   ft.Icons.BUG_REPORT,         "Debug"),
    ]

    botoes_nav = []

    def _on_nav(idx):
        _idx_selecionado[0] = idx
        for i, btn in enumerate(botoes_nav):
            selecionado = (i == idx)
            btn.bgcolor = COR_PRIMARIA if selecionado else "transparent"
            btn.content.controls[0].name  = ITENS_NAV[i][1] if selecionado else ITENS_NAV[i][0]
            btn.content.controls[0].color = "white" if selecionado else COR_TEXTO
            btn.content.controls[1].color = "white" if selecionado else COR_TEXTO
            btn.border_radius = 12
            btn.update()
        trocar_tela(idx)

    for i, (icone_off, icone_on, label) in enumerate(ITENS_NAV):
        idx_capturado = i
        btn = ft.Container(
            content=ft.Column([
                ft.Icon(icone_off, color=COR_TEXTO, size=24),
                ft.Text(label, size=10, color=COR_TEXTO, weight=ft.FontWeight.W_600,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4, tight=True),
            padding=ft.Padding.symmetric(horizontal=8, vertical=10),
            border_radius=12,
            bgcolor="transparent",
            ink=True,
            on_click=lambda e, idx=idx_capturado: _on_nav(idx),
            width=90,
        )
        botoes_nav.append(btn)

    # Marcar o primeiro como selecionado
    botoes_nav[0].bgcolor = COR_PRIMARIA
    botoes_nav[0].content.controls[0].name  = ITENS_NAV[0][1]
    botoes_nav[0].content.controls[0].color = "white"
    botoes_nav[0].content.controls[1].color = "white"

    col_nav = ft.Column(
        controls=botoes_nav,
        spacing=4,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    nome_marmiteria_txt = ft.Text("", size=10, color=COR_SUBTEXTO,
                                   text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.W_600)

    sidebar = ft.Container(
        width=110, bgcolor=COR_SIDEBAR,
        border=ft.Border(right=ft.BorderSide(1, COR_BORDA)),
        content=ft.Column([
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=4, vertical=14),
                content=ft.Column([
                    ft.Image(src="assets/images/logo.png", width=60, height=60),
                    nome_marmiteria_txt,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            ),
            ft.Divider(color=COR_BORDA, height=1),
            ft.Container(
                expand=True,
                padding=ft.Padding.symmetric(horizontal=8, vertical=12),
                content=col_nav,
            ),
        ], spacing=0, expand=True),
    )

    area_conteudo.content = tela_gastos

    tela_principal = ft.Row(
        controls=[sidebar, area_conteudo],
        spacing=0, expand=True,
    )

    def pos_login():
        nome_marmiteria_txt.value = state["marmiteria_nome"] or ""

    page.add(tela_login)

    original_recarregar = recarregar_gastos

    def recarregar_gastos_com_nome():
        pos_login()
        original_recarregar()

    recarregar_gastos = recarregar_gastos_com_nome


ft.app(target=main)