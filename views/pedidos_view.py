import flet as ft
from datetime import date, datetime, timedelta
from models.constants import (
    COR_FUNDO, COR_CARD, COR_BORDA, COR_PRIMARIA, COR_SECUNDARIA,
    COR_TEXTO, COR_SUBTEXTO, COR_DESTAQUE, COR_ERRO, COR_SUCESSO,
)
from views.components import mk_btn, mk_titulo, mk_subtitulo
from views.components import mk_dialogo_confirmacao
from utils.impressora import imprimir_etiqueta, imprimir_etiquetas_lote, preview_etiqueta

STATUS_CONFIG = {
    "PENDENTE":   {"label": "Pendente",    "cor": "#FF9800", "icone": ft.Icons.HOURGLASS_EMPTY},
    "CONFIRMADO": {"label": "Confirmado",  "cor": COR_SUCESSO, "icone": ft.Icons.CHECK_CIRCLE_OUTLINE},
    "EM_PRODUCAO":{"label": "Em Produção", "cor": "#1565C0", "icone": ft.Icons.RESTAURANT},
    "PRONTO":     {"label": "Pronto",      "cor": "#6A1B9A", "icone": ft.Icons.DONE_ALL},
    "ENTREGUE":   {"label": "Entregue",    "cor": "#2E7D32", "icone": ft.Icons.CHECK_CIRCLE},
    "CANCELADO":  {"label": "Cancelado",   "cor": COR_ERRO,  "icone": ft.Icons.CANCEL_OUTLINED},
}

STATUS_PROXIMOS = {
    "PENDENTE":    ["CONFIRMADO", "CANCELADO"],
    "CONFIRMADO":  ["EM_PRODUCAO"],
    "EM_PRODUCAO": ["PRONTO"],
    "PRONTO":      ["ENTREGUE"],
    "ENTREGUE":    [],
    "CANCELADO":   [],
}


def build_pedidos_view(page: ft.Page, api_pedido, state: dict) -> ft.Container:
    lista_pedidos:   ft.Column = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8, expand=True)
    _pedidos_state:  list      = []
    _checks:         dict      = {}

    def snack(msg: str, cor: str = COR_SUCESSO):
        sb = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=cor, duration=2500, open=True)
        page.overlay.append(sb)
        page.update()

    def fechar_dialogo(e=None):
        page.pop_dialog()
        page.update()

    def _preview_widget(pedido: dict) -> ft.Container:
        nome_cliente  = pedido.get("nomeCliente") or f"Usuário #{pedido.get('userId', '—')}"
        cardapio_nome = pedido.get("cardapioNome") or "—"
        ings          = pedido.get("ingredientes") or []
        validade      = (date.today() + timedelta(days=30)).strftime("%d/%m/%Y")
        nome_marmit   = state.get("marmiteria_nome") or "Comida & Afeto"

        itens = [
            ft.Row([
                ft.Icon(ft.Icons.FIBER_MANUAL_RECORD, size=8, color=COR_PRIMARIA),
                ft.Text(i.get("nome", "—"), size=12, color=COR_SUBTEXTO),
            ], spacing=4)
            for i in ings
        ] if ings else [ft.Text("Sem ingredientes", size=12, color=COR_SUBTEXTO)]

        return ft.Container(
            width=210, bgcolor=COR_FUNDO, border_radius=8,
            padding=ft.Padding.all(16),
            border=ft.Border.all(2, COR_BORDA),
            content=ft.Column([
                ft.Row([
                    ft.Image(src="assets/images/logo.png", width=28, height=28),
                    ft.Text("Comida & Afeto", size=12, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                ], spacing=6),
                ft.Text(nome_marmit, size=10, color=COR_SUBTEXTO),
                ft.Divider(color=COR_BORDA),
                ft.Text("Cliente:", size=10, color=COR_SUBTEXTO),
                ft.Text(nome_cliente, size=12, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                ft.Text(f"Cardápio: {cardapio_nome}", size=10, color=COR_SUBTEXTO),
                ft.Divider(color=COR_BORDA),
                ft.Text("Ingredientes:", size=10, weight=ft.FontWeight.W_600, color=COR_TEXTO),
                *itens,
                ft.Divider(color=COR_BORDA),
                ft.Text(f"Validade: {validade}", size=12, weight=ft.FontWeight.BOLD, color=COR_DESTAQUE),
            ], spacing=4),
        )

    def abrir_detalhes(pedido: dict):
        nome_cliente  = pedido.get("nomeCliente") or f"Usuário #{pedido.get('userId', '—')}"
        cardapio_nome = pedido.get("cardapioNome") or "—"
        valor         = float(pedido.get("valor") or 0)
        status_val    = pedido.get("status") or "PENDENTE"
        ings          = pedido.get("ingredientes") or []
        cfg           = STATUS_CONFIG.get(status_val, STATUS_CONFIG["PENDENTE"])

        try:
            criado_em = datetime.fromisoformat(pedido["dataCriada"]).strftime("%d/%m/%Y %H:%M") \
                        if pedido.get("dataCriada") else "—"
        except Exception:
            criado_em = "—"

        linhas_ings = []
        for ing in sorted(ings, key=lambda x: x.get("posicao") or 0):
            nome_ing = ing.get("nome") or "—"
            gramas   = ing.get("gramas") or 0
            linhas_ings.append(
                ft.Container(
                    bgcolor=COR_FUNDO, border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    border=ft.Border.all(1, COR_BORDA),
                    content=ft.Row([
                        ft.Icon(ft.Icons.RESTAURANT_MENU, size=14, color=COR_PRIMARIA),
                        ft.Text(nome_ing, size=13, color=COR_TEXTO, expand=True),
                        ft.Text(f"{gramas}g", size=13, color=COR_SUBTEXTO, weight=ft.FontWeight.W_600),
                    ], spacing=8),
                )
            )

        if not linhas_ings:
            linhas_ings.append(ft.Text("Sem ingredientes registrados.", color=COR_SUBTEXTO, size=13))

        def imprimir(e):
            fechar_dialogo()
            ok, err = imprimir_etiqueta(pedido, state.get("marmiteria_nome") or "Comida & Afeto")
            if ok:
                snack("Etiqueta enviada para impressão!")
            else:
                snack(f"Erro na impressora: {err}", COR_ERRO)

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.RECEIPT_LONG, color=COR_PRIMARIA, size=22),
                ft.Text("  Detalhes do Pedido", color=COR_TEXTO, weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Container(
                width=420,
                content=ft.Column([
                    ft.Text(nome_cliente, size=22, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                    ft.Row([
                        ft.Icon(cfg["icone"], color=cfg["cor"], size=14),
                        ft.Text(cfg["label"], color=cfg["cor"], size=12, weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                        ft.Text(f"Feito em: {criado_em}", color=COR_SUBTEXTO, size=11),
                    ]),
                    ft.Divider(color=COR_BORDA),
                    ft.Row([
                        ft.Text("Cardápio:", size=12, color=COR_SUBTEXTO),
                        ft.Text(cardapio_nome, size=13, color=COR_TEXTO, weight=ft.FontWeight.W_600),
                    ], spacing=6),
                    ft.Row([
                        ft.Text("Total:", size=12, color=COR_SUBTEXTO),
                        ft.Text(f"R$ {valor:,.2f}", size=15, color=COR_DESTAQUE, weight=ft.FontWeight.BOLD),
                    ], spacing=6),
                    ft.Divider(color=COR_BORDA),
                    ft.Text("Ingredientes do pedido:", size=13, weight=ft.FontWeight.W_600, color=COR_TEXTO),
                    ft.Column(linhas_ings, spacing=6),
                ], spacing=8, scroll=ft.ScrollMode.AUTO),
            ),
            actions=[
                ft.TextButton("Fechar", style=ft.ButtonStyle(color=COR_SUBTEXTO), on_click=fechar_dialogo),
                mk_btn("Imprimir etiqueta", imprimir, ft.Icons.PRINT),
            ],
            bgcolor=COR_CARD, shape=ft.RoundedRectangleBorder(radius=14),
        ))

    def abrir_preview_impressao(pedido: dict):
        nome_marmit = state.get("marmiteria_nome") or "Comida & Afeto"

        def imprimir(e):
            fechar_dialogo()
            ok, err = imprimir_etiqueta(pedido, nome_marmit)
            snack("Etiqueta enviada!" if ok else f"Erro: {err}", COR_SUCESSO if ok else COR_ERRO)

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.LABEL_OUTLINE, color=COR_PRIMARIA, size=24),
                ft.Text("  Preview da Etiqueta (55mm)", color=COR_TEXTO, weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Column([
                ft.Text("Preview:", color=COR_SUBTEXTO, size=11),
                _preview_widget(pedido),
            ], spacing=8, tight=True),
            actions=[
                ft.TextButton("Fechar", style=ft.ButtonStyle(color=COR_SUBTEXTO), on_click=fechar_dialogo),
                mk_btn("Imprimir", imprimir, ft.Icons.PRINT),
            ],
            bgcolor=COR_CARD, shape=ft.RoundedRectangleBorder(radius=14),
        ))

    def imprimir_selecionados(e):
        selecionados = [p for p in _pedidos_state if _checks.get(p.get("id")) and _checks[p.get("id")].value]
        if not selecionados:
            snack("Selecione ao menos um pedido!", COR_ERRO)
            return
        nome_marmit = state.get("marmiteria_nome") or "Comida & Afeto"

        def confirmar_impressao(ev):
            fechar_dialogo()
            ok, err = imprimir_etiquetas_lote(selecionados, nome_marmit)
            snack(f"{len(selecionados)} etiqueta(s) enviadas!" if ok else f"Erro: {err}",
                  COR_SUCESSO if ok else COR_ERRO)

        previews = []
        for p in selecionados:
            previews.append(_preview_widget(p))
            previews.append(ft.Divider(color=COR_BORDA, height=12))

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.PRINT, color=COR_PRIMARIA, size=24),
                ft.Text(f"  Imprimir {len(selecionados)} etiqueta(s)", color=COR_TEXTO, weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Container(
                width=400, height=500,
                content=ft.Column(previews, scroll=ft.ScrollMode.AUTO, spacing=0),
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=COR_SUBTEXTO), on_click=fechar_dialogo),
                mk_btn("Confirmar impressão", confirmar_impressao, ft.Icons.PRINT),
            ],
            bgcolor=COR_CARD, shape=ft.RoundedRectangleBorder(radius=14),
        ))

    def selecionar_todos(e):
        for chk in _checks.values():
            chk.value = True
            chk.update()

    def desselecionar_todos(e):
        for chk in _checks.values():
            chk.value = False
            chk.update()

    def _botoes_status(pedido: dict) -> ft.Row:
        status_atual = pedido.get("status") or "PENDENTE"
        proximos     = STATUS_PROXIMOS.get(status_atual, [])
        botoes       = []

        for prox in proximos:
            cfg   = STATUS_CONFIG.get(prox, {})
            label = cfg.get("label", prox)
            cor   = cfg.get("cor", COR_PRIMARIA)

            def mudar_status(e, pid=pedido.get("id"), novo=prox):
                ok, err = api_pedido.atualizar_status(pid, novo)
                if ok:
                    snack(f"Status atualizado para {STATUS_CONFIG.get(novo, {}).get('label', novo)}!")
                    recarregar()
                else:
                    snack(f"Erro: {err}", COR_ERRO)

            botoes.append(ft.Container(
                content=ft.Text(f"→ {label}", size=11, color="white", weight=ft.FontWeight.BOLD),
                bgcolor=cor, border_radius=8, height=30,
                padding=ft.Padding.symmetric(horizontal=10, vertical=0),
                on_click=mudar_status, ink=True,
            ))

        return ft.Row(botoes, spacing=6)

    def recarregar():
        nonlocal _pedidos_state
        dados, err = api_pedido.listar(state["marmiteria_id"])
        print(f"[PEDIDOS] err={err} dados={dados}")
        _pedidos_state = dados or []
        _checks.clear()
        lista_pedidos.controls.clear()

        if not _pedidos_state:
            lista_pedidos.controls.append(
                ft.Text("Nenhum pedido encontrado.", color=COR_SUBTEXTO, size=13))
        else:
            for p in sorted(_pedidos_state, key=lambda x: x.get("dataCriada") or "", reverse=True):
                pid          = p.get("id")
                nome         = p.get("nomeCliente") or f"Usuário #{p.get('userId', '—')}"
                cardapio_nom = p.get("cardapioNome") or "—"
                valor        = float(p.get("valor") or 0)
                status_val   = p.get("status") or "PENDENTE"
                ings         = p.get("ingredientes") or []
                cfg          = STATUS_CONFIG.get(status_val, STATUS_CONFIG["PENDENTE"])

                chk = ft.Checkbox(value=False, active_color=COR_PRIMARIA)
                _checks[pid] = chk

                def on_deletar(e, ped=p):
                    mk_dialogo_confirmacao(
                        page,
                        "Excluir pedido?",
                        f"Excluir pedido de {ped.get('nomeCliente', '—')}?",
                        lambda: (api_pedido.remover(ped["id"]), recarregar()),
                    )

                lista_pedidos.controls.append(ft.Container(
                    bgcolor=COR_CARD, border_radius=12,
                    padding=ft.Padding.symmetric(horizontal=16, vertical=14),
                    border=ft.Border(left=ft.BorderSide(4, cfg["cor"])),
                    content=ft.Row([
                        chk,
                        ft.Column([
                            ft.Text(nome, size=18, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA),
                            ft.Text(
                                f"Cardápio: {cardapio_nom}  •  {len(ings)} ingrediente(s)",
                                color=COR_SUBTEXTO, size=11,
                            ),
                            ft.Container(height=4),
                            _botoes_status(p),
                        ], spacing=2, expand=True),
                        ft.Column([
                            ft.Text(f"R$ {valor:,.2f}", color=COR_DESTAQUE,
                                    size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(height=4),
                            ft.Row([
                                ft.Icon(cfg["icone"], color=cfg["cor"], size=14),
                                ft.Text(cfg["label"], color=cfg["cor"], size=12,
                                        weight=ft.FontWeight.W_600),
                            ], spacing=4),
                            ft.Container(height=4),
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.INFO_OUTLINE, color=COR_PRIMARIA, size=14),
                                    ft.Text("Ver detalhes", color=COR_PRIMARIA, size=12,
                                            weight=ft.FontWeight.W_600),
                                ], spacing=4, tight=True),
                                on_click=lambda e, ped=p: abrir_detalhes(ped),
                                ink=True, border_radius=8,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=6),
                            ),
                        ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=0),
                    ], alignment=ft.MainAxisAlignment.START,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                ))

        page.update()

    barra_acoes = ft.Container(
        bgcolor=COR_CARD, border_radius=10,
        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
        border=ft.Border.all(1, COR_BORDA),
        content=ft.Row([
            ft.TextButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_BOX_OUTLINED, color=COR_PRIMARIA, size=16),
                    ft.Text("Selecionar todos", color=COR_PRIMARIA, size=13),
                ], spacing=4, tight=True),
                on_click=selecionar_todos,
            ),
            ft.TextButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_BOX_OUTLINE_BLANK, color=COR_SUBTEXTO, size=16),
                    ft.Text("Desmarcar todos", color=COR_SUBTEXTO, size=13),
                ], spacing=4, tight=True),
                on_click=desselecionar_todos,
            ),
            ft.Container(expand=True),
            mk_btn("Imprimir selecionados", imprimir_selecionados, ft.Icons.PRINT_OUTLINED),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
    )

    container = ft.Container(
        expand=True, padding=ft.Padding.all(30),
        content=ft.Column(expand=True, spacing=16, controls=[
            ft.Row([
                ft.Column([
                    mk_titulo("Pedidos"),
                    mk_subtitulo("Pedidos recebidos pela sua marmitaria"),
                ], spacing=2, expand=True),
                ft.IconButton(ft.Icons.REFRESH_ROUNDED, icon_color=COR_SECUNDARIA,
                              tooltip="Atualizar", on_click=lambda e: recarregar()),
            ]),
            ft.Divider(color=COR_BORDA),
            barra_acoes,
            lista_pedidos,
        ]),
    )

    container.recarregar = recarregar
    return container