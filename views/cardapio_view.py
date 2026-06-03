import flet as ft
from datetime import datetime
from models.constants import (
    COR_FUNDO, COR_CARD, COR_BORDA, COR_PRIMARIA, COR_SECUNDARIA,
    COR_TEXTO, COR_SUBTEXTO, COR_ERRO, COR_SUCESSO,
)
from views.components import mk_campo, mk_btn, mk_card, mk_titulo, mk_subtitulo, mk_secao_label
from views.components import mk_dialogo_confirmacao, mk_dialogo_sucesso
from utils.mascara import aplicar_mascara_data


def build_cardapio_view(page: ft.Page, api_cardapio, state: dict) -> ft.Container:
    lista_cardapios  = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8)
    ingredientes_form: list = []
    col_ingredientes  = ft.Column(spacing=8)
    cardapio_editando: dict = {}

    f_nome     = mk_campo("Nome do cardápio", expand=True)
    f_validade = mk_campo("Validade", width=180, hint_text="DD/MM/AAAA")
    f_validade.on_change = lambda e: (
        setattr(e.control, "value", aplicar_mascara_data(e.control.value)),
        e.control.update(),
    )

    chk_sem_validade = ft.Checkbox(
        label="Sem validade", value=False,
        active_color=COR_PRIMARIA,
        label_style=ft.TextStyle(color=COR_TEXTO),
    )

    def on_chk_validade(e):
        f_validade.disabled = chk_sem_validade.value
        f_validade.update()

    chk_sem_validade.on_change = on_chk_validade

    btn_cancelar = ft.TextButton(
        "✕  Cancelar edição",
        style=ft.ButtonStyle(color=COR_SUBTEXTO),
        visible=False,
    )

    def snack(msg: str, cor: str = COR_SUCESSO):
        page.snack_bar = ft.SnackBar(ft.Text(msg, color="white"), bgcolor=cor, duration=2500)
        page.snack_bar.open = True
        page.update()

    def linha_ingrediente(idx: int, nome: str = "", valor: str = "") -> ft.Row:
        f_n = mk_campo(f"Ingrediente {idx + 1}", expand=True, value=nome)
        f_v = mk_campo("R$/g", width=120, value=valor, keyboard_type=ft.KeyboardType.NUMBER)
        entrada = {"nome": f_n, "valor": f_v}
        ingredientes_form.append(entrada)

        def remover(e):
            ingredientes_form.remove(entrada)
            col_ingredientes.controls.remove(row)
            col_ingredientes.update()

        row = ft.Row([
            f_n, f_v,
            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=COR_ERRO,
                          icon_size=18, on_click=remover),
        ], spacing=8)
        return row

    def adicionar_ingrediente(e):
        row = linha_ingrediente(len(ingredientes_form))
        col_ingredientes.controls.append(row)
        col_ingredientes.update()

    def limpar_form():
        cardapio_editando.clear()
        f_nome.value              = ""
        f_validade.value          = ""
        f_validade.disabled       = False
        chk_sem_validade.value    = False
        btn_cancelar.visible      = False
        ingredientes_form.clear()
        col_ingredientes.controls.clear()
        for i in range(3):
            col_ingredientes.controls.append(linha_ingrediente(i))
        page.update()

    btn_cancelar.on_click = lambda e: limpar_form()

    def salvar_cardapio(e):
        nome    = (f_nome.value or "").strip()
        sem_val = chk_sem_validade.value
        val_str = (f_validade.value or "").strip()

        if not nome:
            snack("Informe o nome do cardápio!", COR_ERRO); return

        validade_iso = None
        if not sem_val:
            if not val_str:
                snack("Informe a validade ou marque 'Sem validade'.", COR_ERRO); return
            try:
                validade_iso = datetime.strptime(val_str, "%d/%m/%Y").strftime("%Y-%m-%d")
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
            "nome": nome, "validade": validade_iso,
            "semValidade": sem_val, "aberto": True,
            "ingredientes": ings,
            "marmiteria": {"id": state["marmiteria_id"]},
        }

        if cardapio_editando.get("id"):
            payload["id"] = cardapio_editando["id"]
            ok, err = api_cardapio.atualizar(payload)
            if ok:
                snack("Cardápio atualizado!")
                limpar_form()
                recarregar()
            else:
                snack(f"Erro: {err}", COR_ERRO)
        else:
            ok, err = api_cardapio.inserir(payload)
            if ok:
                mk_dialogo_sucesso(page, "Cardápio criado!", f"'{nome}' foi criado com sucesso.")
                limpar_form()
                recarregar()
            else:
                snack(f"Erro: {err}", COR_ERRO)

    def recarregar():
        dados, _ = api_cardapio.listar(state["marmiteria_id"])
        cardapios = dados or []
        lista_cardapios.controls.clear()

        for c in cardapios:
            aberto  = c.get("aberto", True)
            val     = c.get("validade") or ""
            sem_val = c.get("semValidade", False)
            val_fmt = "Sem validade" if sem_val else (
                datetime.strptime(val[:10], "%Y-%m-%d").strftime("%d/%m/%Y") if val else "—"
            )
            ings = c.get("ingredientes") or []

            def toggle_aberto(ev, cid=c["id"], nome_c=c.get("nome", "?")):
                novo = ev.data.lower() == "true"
                ok, err = api_cardapio.alterar_aberto(cid, novo)
                if ok:
                    snack(f"'{nome_c}' {'aberto' if novo else 'fechado'} para pedidos.")
                else:
                    snack(f"Erro: {err}", COR_ERRO)
                recarregar()

            def editar(e, card=c):
                cardapio_editando.clear()
                cardapio_editando.update(card)
                f_nome.value          = card.get("nome", "")
                sem                   = card.get("semValidade", False)
                chk_sem_validade.value = sem
                f_validade.disabled   = sem
                v                     = card.get("validade") or ""
                f_validade.value      = datetime.strptime(v[:10], "%Y-%m-%d").strftime("%d/%m/%Y") if v else ""
                ingredientes_form.clear()
                col_ingredientes.controls.clear()
                for idx, ing in enumerate(card.get("ingredientes") or []):
                    col_ingredientes.controls.append(
                        linha_ingrediente(idx, ing.get("nome", ""), str(ing.get("valorPorGramas", "")))
                    )
                if not col_ingredientes.controls:
                    for i in range(3):
                        col_ingredientes.controls.append(linha_ingrediente(i))
                btn_cancelar.visible = True
                page.update()

            def deletar(e, card=c):
                mk_dialogo_confirmacao(
                    page,
                    "Excluir cardápio?",
                    f"Excluir '{card.get('nome')}'? Todos os pedidos vinculados serão removidos.",
                    lambda: (api_cardapio.remover(card["id"]), recarregar()),
                )

            lista_cardapios.controls.append(ft.Container(
                bgcolor=COR_FUNDO, border_radius=12,
                padding=ft.Padding.symmetric(horizontal=18, vertical=14),
                border=ft.Border(left=ft.BorderSide(4, COR_SUCESSO if aberto else COR_ERRO)),
                content=ft.Row([
                    ft.Column([
                        ft.Text(c.get("nome", "—"), color=COR_TEXTO, size=14, weight=ft.FontWeight.W_600),
                        ft.Text(f"Validade: {val_fmt}  •  {len(ings)} ingrediente(s)", color=COR_SUBTEXTO, size=11),
                        ft.Container(height=4),
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
                    ], spacing=2, expand=True),
                    ft.Row([
                        ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=COR_SECUNDARIA,
                                      tooltip="Editar", on_click=editar, icon_size=18),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=COR_ERRO,
                                      tooltip="Excluir", on_click=deletar, icon_size=18),
                    ], spacing=0),
                ], alignment=ft.MainAxisAlignment.START,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
            ))

        page.update()

    for i in range(3):
        col_ingredientes.controls.append(linha_ingrediente(i))

    painel_form = mk_card(ft.Column(spacing=14, controls=[
        mk_secao_label("Novo Cardápio"),
        ft.Row([f_nome, f_validade, chk_sem_validade], spacing=12,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
        mk_secao_label("Ingredientes"),
        col_ingredientes,
        ft.TextButton(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=COR_PRIMARIA, size=16),
                ft.Text("Adicionar ingrediente", color=COR_PRIMARIA, weight=ft.FontWeight.BOLD),
            ], tight=True, spacing=6),
            on_click=adicionar_ingrediente,
        ),
        ft.Divider(color=COR_BORDA),
        ft.Row([
            mk_btn("Salvar Cardápio", salvar_cardapio, ft.Icons.SAVE_OUTLINED),
            btn_cancelar,
        ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
    ]))

    container = ft.Container(
        expand=True, padding=ft.Padding.all(30),
        content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=20, controls=[
            ft.Column([mk_titulo("Cardápio"), mk_subtitulo("Gerencie os cardápios da sua marmitaria")], spacing=4),
            ft.Divider(color=COR_BORDA),
            painel_form,
            ft.Text("Cardápios cadastrados", size=16, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
            lista_cardapios,
        ]),
    )

    container.recarregar = recarregar
    return container