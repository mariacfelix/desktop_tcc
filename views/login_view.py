import flet as ft
from models.constants import COR_FUNDO, COR_CARD, COR_BORDA, COR_PRIMARIA, COR_TEXTO, COR_SUBTEXTO, COR_ERRO
from views.components import mk_campo, mk_btn


def build_login_view(page: ft.Page, api_marmiteria, state: dict, on_sucesso) -> ft.Container:
    f_email = mk_campo("E-mail", width=320)
    f_senha = mk_campo("Senha", width=320, password=True, can_reveal_password=True)
    txt_erro = ft.Text("", color=COR_ERRO, size=13)

    def fazer_login(e):
        email = (f_email.value or "").strip()
        senha = (f_senha.value or "").strip()
        if not email or not senha:
            txt_erro.value = "Preencha e-mail e senha."
            page.update()
            return
        dados, err = api_marmiteria.login(email, senha)
        if err or not dados:
            txt_erro.value = "Usuário ou senha inválidos."
            page.update()
            return
        state["marmiteria_id"]   = dados["id"]
        state["marmiteria_nome"] = dados["nome"]
        txt_erro.value = ""
        on_sucesso()

    def on_enter(e):
        if e.key == "Enter":
            fazer_login(e)

    f_senha.on_submit = fazer_login
    f_email.on_submit = lambda e: f_senha.focus()

    return ft.Container(
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
                        f_email,
                        f_senha,
                        txt_erro,
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