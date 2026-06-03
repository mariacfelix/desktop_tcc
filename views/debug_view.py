import flet as ft
import requests
from models.constants import (
    COR_CARD, COR_BORDA, COR_TEXTO, COR_SUBTEXTO, COR_SUCESSO,
    API_GASTOS,
)
from views.components import mk_btn, mk_titulo, mk_subtitulo
from utils.logger import get_logs, clear_logs, log


def build_debug_view(page: ft.Page, state: dict) -> ft.Container:
    status_icon = ft.Icon(ft.Icons.CIRCLE, color="grey", size=14)
    status_txt  = ft.Text("Não testado", color=COR_SUBTEXTO, size=13)
    log_view    = ft.ListView(expand=True, spacing=2, auto_scroll=True)

    def atualizar_log_view():
        log_view.controls.clear()
        for entrada in get_logs():
            cor = "#F44336" if any(x in entrada for x in ["ERRO", "FALHOU", "FALHA"]) \
                else "#4CAF50" if "OK" in entrada \
                else "#FF9800" if any(x in entrada for x in [">>>", "==="]) \
                else COR_SUBTEXTO
            log_view.controls.append(
                ft.Text(entrada, color=cor, size=11, font_family="monospace", selectable=True))

    def testar_api(e):
        log("=== TESTE DE CONEXÃO ===")
        try:
            r = requests.get(f"{API_GASTOS}/todos",
                             params={"marmiteriaId": state["marmiteria_id"]}, timeout=5)
            log(f"  HTTP {r.status_code} | {r.text[:300]}")
            status_icon.color = "#4CAF50" if r.status_code == 200 else "#FF9800"
            status_txt.value  = f"API OK — {r.status_code}" if r.status_code == 200 else f"Erro {r.status_code}"
        except Exception as ex:
            log(f"  FALHA: {ex}")
            status_icon.color = "#F44336"
            status_txt.value  = f"Sem conexão: {ex}"
        atualizar_log_view()
        page.update()

    def limpar_logs(e):
        clear_logs()
        atualizar_log_view()
        page.update()

    return ft.Container(
        expand=True, padding=ft.Padding.all(24),
        content=ft.Column(expand=True, spacing=16, controls=[
            ft.Column([mk_titulo("Debug"), mk_subtitulo("Diagnóstico e logs em tempo real")], spacing=4),
            ft.Divider(color=COR_BORDA),
            ft.Container(
                bgcolor=COR_CARD, border_radius=12, padding=ft.Padding.all(20),
                border=ft.Border.all(1, COR_BORDA),
                content=ft.Column([
                    ft.Row([status_icon, status_txt]),
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