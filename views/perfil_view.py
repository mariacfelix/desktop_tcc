import re
import flet as ft
from models.constants import (
    COR_FUNDO, COR_CARD, COR_BORDA, COR_PRIMARIA,
    COR_TEXTO, COR_SUBTEXTO, COR_ERRO, COR_SUCESSO,
)
from views.components import mk_campo, mk_btn, mk_titulo, mk_subtitulo, mk_secao_label, mk_card


def aplicar_mascara_cnpj(valor: str) -> str:
    nums = "".join(c for c in (valor or "") if c.isdigit())[:14]
    r = ""
    for i, c in enumerate(nums):
        if i == 2 or i == 5:
            r += "."
        elif i == 8:
            r += "/"
        elif i == 12:
            r += "-"
        r += c
    return r


def aplicar_mascara_cep(valor: str) -> str:
    nums = "".join(c for c in (valor or "") if c.isdigit())[:8]
    if len(nums) > 5:
        return nums[:5] + "-" + nums[5:]
    return nums


def aplicar_mascara_telefone(valor: str) -> str:
    nums = "".join(c for c in (valor or "") if c.isdigit())[:11]
    if len(nums) <= 10:
        if len(nums) > 6:
            return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
        elif len(nums) > 2:
            return f"({nums[:2]}) {nums[2:]}"
        elif len(nums) > 0:
            return f"({nums}"
    else:
        return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"
    return nums


def validar_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def validar_cnpj(cnpj: str) -> bool:
    nums = "".join(c for c in cnpj if c.isdigit())
    return len(nums) == 14


def validar_cep(cep: str) -> bool:
    nums = "".join(c for c in cep if c.isdigit())
    return len(nums) == 8


def validar_telefone(tel: str) -> bool:
    nums = "".join(c for c in tel if c.isdigit())
    return len(nums) in (10, 11)


def build_perfil_view(page: ft.Page, api_marmiteria, state: dict, on_logout) -> ft.Container:

    f_nome     = mk_campo("Nome da marmitaria", expand=True)
    f_email    = mk_campo("E-mail", expand=True)
    f_telefone = mk_campo("Telefone", width=210, hint_text="(00) 00000-0000")
    f_cnpj     = mk_campo("CNPJ", width=200, hint_text="00.000.000/0000-00")
    f_cep      = mk_campo("CEP", width=150, hint_text="00000-000")
    f_numero   = mk_campo("Número", width=110)
    f_senha_atual = mk_campo("Senha atual", expand=True,
                              password=True, can_reveal_password=True)
    f_senha       = mk_campo("Nova senha", expand=True,
                              password=True, can_reveal_password=True)

    txt_erro = ft.Text("", color=COR_ERRO, size=13)
    txt_ok   = ft.Text("", color=COR_SUCESSO, size=13)

    def on_cnpj_change(e):
        c = e.control
        novo = aplicar_mascara_cnpj(c.value)
        if c.value != novo:
            c.value = novo
            c.update()

    def on_cep_change(e):
        c = e.control
        novo = aplicar_mascara_cep(c.value)
        if c.value != novo:
            c.value = novo
            c.update()

    def on_telefone_change(e):
        c = e.control
        novo = aplicar_mascara_telefone(c.value)
        if c.value != novo:
            c.value = novo
            c.update()

    f_cnpj.on_change     = on_cnpj_change
    f_cep.on_change      = on_cep_change
    f_telefone.on_change = on_telefone_change

    def snack(msg: str, cor: str = COR_SUCESSO):
        sb = ft.SnackBar(
            content=ft.Text(msg, color="white"),
            bgcolor=cor, duration=2500, open=True,
        )
        page.overlay.append(sb)
        page.update()

    def erro(msg: str):
        txt_erro.value = msg
        txt_ok.value   = ""
        page.update()

    def carregar_dados():
        dados, err = api_marmiteria.buscar(state["marmiteria_id"])
        if err or not dados:
            erro("Erro ao carregar dados.")
            return
        f_nome.value        = dados.get("nome") or ""
        f_email.value       = dados.get("email") or ""
        f_telefone.value    = dados.get("telefone") or ""
        f_cnpj.value        = dados.get("cnpj") or ""
        f_cep.value         = dados.get("cep") or ""
        f_numero.value      = dados.get("numero") or ""
        f_senha.value       = ""
        f_senha_atual.value = ""
        txt_erro.value      = ""
        txt_ok.value        = ""
        page.update()

    def salvar(e):
        nome  = (f_nome.value or "").strip()
        email = (f_email.value or "").strip()
        tel   = (f_telefone.value or "").strip()
        cnpj  = (f_cnpj.value or "").strip()
        cep   = (f_cep.value or "").strip()

        if not nome:
            erro("O nome é obrigatório."); return
        if not email:
            erro("O e-mail é obrigatório."); return
        if not validar_email(email):
            erro("E-mail inválido. Use o formato nome@dominio.com"); return
        if cnpj and not validar_cnpj(cnpj):
            erro("CNPJ inválido. Use o formato 00.000.000/0000-00"); return
        if cep and not validar_cep(cep):
            erro("CEP inválido. Use o formato 00000-000"); return
        if tel and not validar_telefone(tel):
            erro("Telefone inválido. Use (00) 00000-0000 ou (00) 0000-0000"); return

        senha       = (f_senha.value or "").strip()
        senha_atual = (f_senha_atual.value or "").strip()
        if senha and not senha_atual:
            erro("Informe a senha atual para alterá-la."); return

        payload = {
            "id":       state["marmiteria_id"],
            "nome":     nome,
            "email":    email,
            "telefone": tel,
            "cnpj":     cnpj,
            "cep":      cep,
            "numero":   (f_numero.value or "").strip(),
        }
        if senha:
            payload["senha"]      = senha
            payload["senhaAtual"] = senha_atual

        ok, err = api_marmiteria.atualizar(payload)
        if ok:
            state["marmiteria_nome"] = nome
            txt_erro.value      = ""
            txt_ok.value        = "Dados atualizados com sucesso!"
            f_senha.value       = ""
            f_senha_atual.value = ""
            snack("Perfil atualizado!")
            page.update()
        else:
            if "401" in str(err) or "Senha atual" in str(err):
                erro("Senha atual incorreta.")
            else:
                erro(f"Erro ao salvar: {err}")

    def logout(e):
        def confirmar(ev):
            page.pop_dialog()
            page.update()
            state["marmiteria_id"]   = None
            state["marmiteria_nome"] = None
            on_logout()

        def cancelar(ev):
            page.pop_dialog()
            page.update()

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Sair da conta", color=COR_TEXTO, weight=ft.FontWeight.BOLD),
            content=ft.Text("Deseja realmente sair?", color=COR_SUBTEXTO),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=COR_SUBTEXTO), on_click=cancelar),
                mk_btn("Sair", confirmar, bgcolor=COR_ERRO),
            ],
            bgcolor=COR_CARD, shape=ft.RoundedRectangleBorder(radius=14),
        ))

    btn_salvar = mk_btn("Salvar alterações", salvar, ft.Icons.SAVE_OUTLINED)
    btn_logout = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.LOGOUT_ROUNDED, color=COR_ERRO, size=16),
            ft.Text("Sair da conta", color=COR_ERRO, weight=ft.FontWeight.BOLD),
        ], tight=True, spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=COR_FUNDO,
        border=ft.Border.all(1, COR_ERRO),
        border_radius=10, height=44,
        padding=ft.Padding.symmetric(horizontal=20, vertical=0),
        on_click=logout, ink=True,
    )

    container = ft.Container(
        expand=True,
        padding=ft.Padding.all(36),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Column([
                    mk_titulo("Perfil da Marmitaria"),
                    mk_subtitulo("Edite as informações da sua marmitaria"),
                ], spacing=4),
                ft.Divider(color=COR_BORDA),
                mk_card(ft.Column(spacing=16, controls=[
                    mk_secao_label("Informações gerais"),
                    ft.Row([f_nome, f_email], spacing=12),
                    ft.Row([f_telefone, f_cnpj], spacing=12),
                    ft.Row([f_cep, f_numero], spacing=12),
                    ft.Divider(color=COR_BORDA),
                    mk_secao_label("Segurança"),
                    ft.Text("Preencha apenas se quiser alterar a senha",
                            size=11, color=COR_SUBTEXTO),
                    ft.Row([f_senha_atual, f_senha], spacing=12),
                    ft.Divider(color=COR_BORDA),
                    txt_erro,
                    txt_ok,
                    ft.Row([btn_salvar, btn_logout], spacing=16,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ])),
            ],
        ),
    )

    container.carregar_dados = carregar_dados
    return container