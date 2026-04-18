# -*- coding: utf-8 -*-
import flet as ft
import time
import math
import json
import threading 
import requests  
import random 
import csv
import os
from datetime import datetime

# ==========================================
# 1. DESIGN SYSTEM E CONSTANTES
# ==========================================
C_BG = "#0B0B0F"          
C_SURFACE = "#15161A"     
C_SURFACE_SEC = "#1C1D22" 
C_BORDER = "#2A2C33"      
C_TEXT_PRI = "#F5F7FA"    
C_TEXT_SEC = "#A7ADB7"    
C_PRIMARY = "#FF7A00"     
C_SUCCESS = "#22C55E"
C_ERROR = "#EF4444"

C_XTREME = C_PRIMARY; C_BURST = "#A855F7"; C_OVER = "#3B82F6"; C_SPIN = "#22C55E"; C_FLAG = "#EAB308"        
PTS_WIN_TARGET = 4
PTS_MAP = {"xtreme": 3, "burst": 2, "over": 2, "spin": 1, "flag": 1}

# ==========================================
# 2. MOTOR DA NUVEM (Migrado para V2 e com Trava de Sessão)
# ==========================================
# 👑 NOVO ENDEREÇO: Mata os APKs antigos instantaneamente
FIREBASE_URL = "https://beybladeapp-c303a-default-rtdb.firebaseio.com/beyblade_data_v2.json"

app_data = {"bladers": [], "tournaments": {}, "active_matches": {}, "history": [], "training_history": [], "users": {}, "last_updated": 0}
is_syncing = False 
db_lock = threading.RLock() 
on_sync_start, on_sync_end = None, None

def safe_cloud_sync():
    if on_sync_start: on_sync_start()
    try:
        res = requests.get(FIREBASE_URL, timeout=5)
        if res.status_code == 200 and res.json() is not None:
            with db_lock: 
                app_data.clear(); app_data.update(res.json())
                if "users" not in app_data: app_data["users"] = {}
                if "training_history" not in app_data: app_data["training_history"] = []
                if "tournaments" not in app_data: app_data["tournaments"] = {}
                if "active_matches" not in app_data: app_data["active_matches"] = {}
                if "last_updated" not in app_data: app_data["last_updated"] = 0
                
                if "tournament" in app_data:
                    if app_data["tournament"]: app_data["tournaments"]["admin"] = app_data["tournament"]
                    del app_data["tournament"]
                if "active_match" in app_data:
                    if app_data["active_match"]: app_data["active_matches"]["admin"] = app_data["active_match"]
                    del app_data["active_match"]
    except Exception: pass
    finally:
        if on_sync_end: on_sync_end()

def load_db(): safe_cloud_sync(); return app_data

def save_db(data_to_save):
    global is_syncing
    is_syncing = True
    with db_lock:
        data_to_save["last_updated"] = int(time.time() * 1000) 
        dados_copia = json.loads(json.dumps(data_to_save)) 
    if on_sync_start: on_sync_start()
    def _background_save(dados):
        global is_syncing
        for _ in range(3):
            try:
                if requests.put(FIREBASE_URL, json=dados, timeout=5).status_code == 200: break
            except Exception: time.sleep(1.5)
        is_syncing = False
        if on_sync_end: on_sync_end()
    threading.Thread(target=_background_save, args=(dados_copia,), daemon=True).start()

load_db()

# --- FUNÇÕES GLOBAIS DE BANCO DE DADOS SEPARADOS POR ORG ---
def get_bladers(org):
    with db_lock: return [b for b in json.loads(json.dumps(app_data.get("bladers", []))) if b.get("org", "admin") == org]

def save_bladers(bl_list, org): 
    for b in bl_list: b["org"] = org
    with db_lock:
        all_b = [b for b in app_data.get("bladers", []) if b.get("org", "admin") != org]
        all_b.extend(bl_list); app_data["bladers"] = all_b
    save_db(app_data)

def get_tournament(org):
    with db_lock: return json.loads(json.dumps(app_data.get("tournaments", {}).get(org)))

def save_tournament(t_data, org): 
    with db_lock:
        app_data.setdefault("tournaments", {})
        if t_data is None:
            if org in app_data["tournaments"]: del app_data["tournaments"][org]
        else: app_data["tournaments"][org] = t_data
    save_db(app_data)

def get_active_match(org):
    with db_lock: return json.loads(json.dumps(app_data.get("active_matches", {}).get(org)))

def set_active_match(m_data, org):
    with db_lock:
        app_data.setdefault("active_matches", {})
        if m_data is None:
            if org in app_data["active_matches"]: del app_data["active_matches"][org]
        else: app_data["active_matches"][org] = m_data
    save_db(app_data)

def get_history(org):
    with db_lock: return [h for h in json.loads(json.dumps(app_data.get("history", []))) if h.get("org", "admin") == org]

def add_to_history(t_data, org):
    t_data["org"] = org
    with db_lock: app_data.setdefault("history", []).insert(0, t_data)
    save_db(app_data)

def get_training_history(org):
    with db_lock: return [h for h in json.loads(json.dumps(app_data.get("training_history", []))) if h.get("org", "admin") == org]

def add_to_training_history(train_data, org):
    train_data["org"] = org
    with db_lock: app_data.setdefault("training_history", []).insert(0, train_data)
    save_db(app_data)

def get_users():
    with db_lock: return json.loads(json.dumps(app_data.get("users", {})))
def save_users(u_dict):
    with db_lock: app_data["users"] = u_dict; save_db(app_data)

# ==========================================
# 3. SISTEMA DE PERFIS (DADOS ORIGINAIS)
# ==========================================
HARDCODED_USERS = {
    "themonc08": {"password": "150217bR*", "role": "admin_max", "org": "admin"},
    "caruso": {"password": "bladerbey01", "role": "pro", "org": "OCB"},
    "juiz_1": {"password": "beyjuiz1", "role": "organizador", "org": "OCB"},
    "juiz_2": {"password": "beyjuiz2", "role": "organizador", "org": "OCB"}
}

# ==========================================
# 4. COMPONENTES UI
# ==========================================
def AppCard(content, padding=16, on_click=None, data=None): return ft.Container(content=content, padding=padding, bgcolor=C_SURFACE, border_radius=16, border=ft.border.all(1, C_BORDER), on_click=on_click, data=data)
def PrimaryBtn(text, on_click, width=None, height=48, icon=None, data=None, color=C_PRIMARY, expand=False): return ft.Container(content=ft.Row([ft.Icon(icon, color=C_TEXT_PRI, size=20)] + [ft.Text(text, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, size=14)], alignment=ft.MainAxisAlignment.CENTER, spacing=8) if icon else ft.Text(text, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, size=14), bgcolor=color, padding=8, border_radius=12, alignment=ft.Alignment(0, 0), width=width, height=height, on_click=on_click, data=data, expand=expand)
def SecondaryBtn(text, on_click, width=None, height=48, icon=None, data=None, expand=False): return ft.Container(content=ft.Row([ft.Icon(icon, color=C_TEXT_SEC, size=20)] + [ft.Text(text, color=C_TEXT_SEC, weight=ft.FontWeight.W_500, size=13)], alignment=ft.MainAxisAlignment.CENTER, spacing=8) if icon else ft.Text(text, color=C_TEXT_SEC, weight=ft.FontWeight.W_500, size=13), bgcolor=C_SURFACE_SEC, padding=8, border_radius=12, border=ft.border.all(1, C_BORDER), alignment=ft.Alignment(0, 0), width=width, height=height, on_click=on_click, data=data, expand=expand)
def IconButton(icon, on_click, color=C_TEXT_SEC, tooltip=None): return ft.Container(content=ft.Icon(icon, color=color, size=22), padding=10, border_radius=10, bgcolor=C_SURFACE_SEC, border=ft.border.all(1, C_BORDER), on_click=on_click, tooltip=tooltip)
def Badge(text, color): return ft.Container(content=ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=color), padding=6, bgcolor=f"{color}15", border_radius=6, border=ft.border.all(1, f"{color}40"))

def CreditsFooter():
    return ft.Container(
        content=ft.Column([
            ft.Text("IDEALIZADO POR: GUILHERME CARUSO", size=10, color=C_TEXT_SEC, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Text("DESENVOLVIDO POR: GUILHERME MONÇÃO", size=10, color=C_TEXT_SEC, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        margin=ft.margin.only(top=24, bottom=12),
        width=float("inf"),
        alignment=ft.Alignment(0, 0)
    )

# ==========================================
# 5. O APLICATIVO PRINCIPAL
# ==========================================
def main(page: ft.Page):
    page.title = "Beyblade X System"; page.theme_mode = ft.ThemeMode.DARK; page.bgcolor = C_BG; page.padding = 0
    page.window.width = 450; page.window.height = 800
    page.fonts = {"Inter": "https://raw.githubusercontent.com/rsms/inter/master/docs/font-files/Inter-Regular.woff2"}
    page.theme = ft.Theme(font_family="Inter")

    # 👑 ESTADO LOCAL DA SESSÃO (COM TOKEN DE SEGURANÇA)
    app_state = {
        "current_user": None,
        "admin_viewing_org": "admin",
        "user_orgs": [],
        "active_org": "default",
        "session_token": None
    }

    # SISTEMA DE PERMISSÕES (LICENÇAS)
    def current_user(): return app_state["current_user"]
    def is_admin_max(): u = current_user(); return u and u["role"] == "admin_max"
    def has_treino_access(): u = current_user(); return u and u["role"] in ["admin_max", "pro", "treinador"]
    def has_torneio_access(): u = current_user(); return u and u["role"] in ["admin_max", "pro", "organizador", "judge"]
    def get_username(): u = current_user(); return u["username"] if u else ""
    
    def get_current_org():
        u = current_user()
        if not u: return "default"
        if is_admin_max():
            viewing = app_state.get("admin_viewing_org")
            if viewing and viewing != "admin": return viewing
            return "admin"
        return app_state.get("active_org") or u.get("org", u["username"])

    # WRAPPERS DB DINÂMICOS
    def _get_bladers(): return get_bladers(get_current_org())
    def _save_bladers(l): save_bladers(l, get_current_org())
    def _get_tournament(): return get_tournament(get_current_org())
    def _save_tournament(d): save_tournament(d, get_current_org())
    def _get_active_match(): return get_active_match(get_current_org())
    def _set_active_match(d): set_active_match(d, get_current_org())
    def _add_to_history(d): add_to_history(d, get_current_org())
    def _add_to_training_history(d): add_to_training_history(d, get_current_org())

    def _get_history():
        if is_admin_max() and app_state.get("admin_viewing_org") == "admin":
            with db_lock: return json.loads(json.dumps(app_data.get("history", [])))
        return get_history(get_current_org())

    def _get_training_history():
        if is_admin_max() and app_state.get("admin_viewing_org") == "admin":
            with db_lock: return json.loads(json.dumps(app_data.get("training_history", [])))
        return get_training_history(get_current_org())

    def do_logout(e=None, force_msg=False):
        app_state["current_user"] = None
        app_state["admin_viewing_org"] = "admin"
        app_state["session_token"] = None
        main_app_container.visible = False; bottom_nav.visible = False; login_container.visible = True
        login_container.content = build_auth_view(True) # Redesenha a tela de login
        if force_msg:
            page.snack_bar = ft.SnackBar(ft.Text("Sua conta foi conectada em outro dispositivo!"), bgcolor=C_ERROR)
            page.snack_bar.open = True
        page.update()

    sync_ring = ft.ProgressRing(width=16, height=16, color=C_PRIMARY, stroke_width=2, visible=False)
    page.appbar = ft.AppBar(title=ft.Text("Beyblade X", size=16, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), bgcolor=C_BG, actions=[])

    def update_appbar():
        actions = [ft.Container(content=sync_ring, padding=ft.padding.only(right=10))]
        if is_admin_max() and app_state.get("admin_viewing_org") != "admin":
            actions.append(ft.Container(content=ft.Text(f"SAIR DA ORG: {app_state['admin_viewing_org'].upper()}", color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, size=11), bgcolor=C_ERROR, padding=6, border_radius=8, margin=ft.margin.only(right=10), on_click=lambda _: [app_state.update({"admin_viewing_org": "admin"}), update_appbar(), refresh_current_tab()]))
        elif len(app_state.get("user_orgs", [])) > 1 and not is_admin_max():
            actions.append(ft.Container(content=ft.Text(f"ORG: {get_current_org().upper()}", color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, size=11), bgcolor=C_PRIMARY, padding=6, border_radius=8, margin=ft.margin.only(right=10)))
            
        actions.append(ft.IconButton(ft.Icons.LOGOUT, icon_color=C_ERROR, on_click=lambda e: do_logout(e), tooltip="Sair"))
        page.appbar.actions = actions; page.update()

    def _show_sync(): sync_ring.visible = True; page.update()
    def _hide_sync(): sync_ring.visible = False; page.update()
    global on_sync_start, on_sync_end
    on_sync_start, on_sync_end = _show_sync, _hide_sync

    def show_dialog(dlg):
        if dlg not in page.overlay: page.overlay.append(dlg)
        dlg.open = True; page.update()
    def hide_dialog(dlg): dlg.open = False; page.update()

    def get_snapshot_map(tourn_data):
        b_map = {b["id"]: b["name"] for b in _get_bladers()}
        if tourn_data and "participants" in tourn_data: b_map.update(tourn_data["participants"])
        return b_map

    def open_match_details(m_data, tourn_context=None):
        b_map = get_snapshot_map(tourn_context)
        res = m_data.get("result", {}); b1_name = b_map.get(m_data.get("blader1"), "A Definir"); b2_name = b_map.get(m_data.get("blader2"), "A Definir")
        f1 = res.get("blader1Result", {}).get("finishes", {}); f2 = res.get("blader2Result", {}).get("finishes", {})
        def f_row(label, key, color): return ft.Row([ft.Text(str(f1.get(key, 0)), color=color, weight=ft.FontWeight.BOLD, size=16, width=30, text_align="center"), ft.Text(label, color=C_TEXT_SEC, expand=True, text_align="center", size=13), ft.Text(str(f2.get(key, 0)), color=color, weight=ft.FontWeight.BOLD, size=16, width=30, text_align="center")])
        dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), content_padding=24, title=ft.Text("Raio-X da Partida", color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, size=18, text_align="center"), content=ft.Column([ft.Row([ft.Text(b1_name, weight=ft.FontWeight.W_600, color=C_TEXT_PRI, expand=True, text_align="center", size=14), ft.Text("VS", size=11, color=C_TEXT_SEC), ft.Text(b2_name, weight=ft.FontWeight.W_600, color=C_TEXT_PRI, expand=True, text_align="center", size=14)]), ft.Divider(color=C_BORDER, height=20), f_row("XTREME", "xtreme", C_XTREME), f_row("BURST", "burst", C_BURST), f_row("OVER", "over", C_OVER), f_row("SPIN", "spin", C_SPIN), f_row("FLAG", "flag", C_FLAG), ft.Divider(color=C_BORDER, height=20), ft.Row([ft.Text(str(res.get("blader1Result", {}).get("totalPoints", 0)), size=24, color=C_PRIMARY, weight=ft.FontWeight.BOLD, width=30, text_align="center"), ft.Text("PONTOS", color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, expand=True, text_align="center", size=14), ft.Text(str(res.get("blader2Result", {}).get("totalPoints", 0)), size=24, color=C_PRIMARY, weight=ft.FontWeight.BOLD, width=30, text_align="center")])], tight=True), actions=[SecondaryBtn("Fechar", lambda _: hide_dialog(dlg))])
        show_dialog(dlg)

    # --- TELA DE LOGIN ---
    login_container = ft.Container(expand=True, padding=24)
    def build_auth_view(is_login=True):
        u_input = ft.TextField(label="Usuário", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
        p_input = ft.TextField(label="Senha", password=True, can_reveal_password=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
        e_input = ft.TextField(label="Email", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12, visible=not is_login)

        def do_auth(e):
            u, p = u_input.value.strip(), p_input.value.strip()
            if not u or not p: page.snack_bar = ft.SnackBar(ft.Text("Preencha tudo!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return
            safe_cloud_sync(); db_users = get_users()
            user_data = None
            
            if is_login:
                if u in db_users and db_users[u].get("password") == p: user_data = db_users[u]
                elif u in HARDCODED_USERS and HARDCODED_USERS[u]["password"] == p:
                    user_data = HARDCODED_USERS[u]
                    # Salva os hardcoded no banco para poder gerenciar o Token
                    db_users[u] = user_data.copy() 
                
                if user_data:
                    # 👑 GERA O TOKEN DE SEGURANÇA (BLOQUEIA ACESSO SIMULTÂNEO)
                    new_token = str(int(time.time() * 1000)) + str(random.randint(1000, 9999))
                    db_users[u]["session_token"] = new_token
                    save_users(db_users)
                    
                    org_str = user_data.get("org", u)
                    user_orgs = [o.strip() for o in org_str.split(",") if o.strip()]
                    app_state["current_user"] = {"username": u, "role": user_data.get("role", "basic"), "org": org_str}
                    app_state["user_orgs"] = user_orgs
                    app_state["active_org"] = user_orgs[0] if user_orgs else u
                    app_state["session_token"] = new_token # Salva no cofre local
                    
                    start_main_app(); return
                page.snack_bar = ft.SnackBar(ft.Text("Login inválido!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update()
            else:
                if u in HARDCODED_USERS or u in db_users: page.snack_bar = ft.SnackBar(ft.Text("Usuário já existe!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return
                new_token = str(int(time.time() * 1000)) + str(random.randint(1000, 9999))
                db_users[u] = {"password": p, "email": e_input.value.strip(), "role": "basic", "org": u, "session_token": new_token}
                save_users(db_users)
                
                app_state["current_user"] = {"username": u, "role": "basic", "org": u}
                app_state["user_orgs"] = [u]
                app_state["active_org"] = u
                app_state["session_token"] = new_token
                start_main_app()

        return ft.Column([
            ft.Container(height=40), ft.Icon(ft.Icons.SECURITY, size=64, color=C_PRIMARY), 
            ft.Text("Bem-vindo" if is_login else "Criar Conta", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), 
            ft.Text("Motor oficial de torneios e treinos.", size=14, color=C_TEXT_SEC), 
            ft.Container(height=20), u_input, e_input, p_input, 
            PrimaryBtn("Entrar" if is_login else "Cadastrar", do_auth, width=float("inf")), 
            ft.TextButton("Não tem conta? Cadastre-se" if is_login else "Já tem conta? Faça Login", on_click=lambda _: [setattr(login_container, 'content', build_auth_view(not is_login)), page.update()], style=ft.ButtonStyle(color=C_TEXT_SEC)),
            ft.Container(expand=True),
            CreditsFooter()
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    login_container.content = build_auth_view(True)

    # --- NAVEGAÇÃO GERAL E ESTADOS ---
    main_app_container = ft.Container(expand=True, visible=False)
    bottom_nav = ft.NavigationBar(bgcolor=C_BG, indicator_color=C_SURFACE_SEC, visible=False, destinations=[ft.NavigationBarDestination(icon=ft.Icons.HOURGLASS_EMPTY, label="1"), ft.NavigationBarDestination(icon=ft.Icons.HOURGLASS_EMPTY, label="2")])
    
    history_state = {"active_tourn": None, "sub_tab": "tabelas"}
    home_state = {"sub_tab": "cadastro", "selected_ids": [], "temp_name": ""}
    tourn_state = {"sub_tab": None, "active_match": None, "match_state": {}}
    training_state = {"sub_tab": "setup", "match_data": None, "p1_score": 0, "p2_score": 0, "p1_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "p2_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "match_ended": False}

    # 👑 TELA 0: PERFIL COM DROPDOWN DE ORGS E CRÉDITOS
    def build_profile_view():
        user_orgs = app_state.get("user_orgs", [get_current_org()])
        
        col_elements = [
            ft.Container(height=50), ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color=C_TEXT_SEC), 
            ft.Text(f"Olá, {get_username()}!", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI)
        ]
        
        if len(user_orgs) > 1 and not is_admin_max():
            dd_org = ft.Dropdown(label="Selecione o Ambiente", value=get_current_org(), options=[ft.dropdown.Option(o) for o in user_orgs], bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12, width=200)
            def apply_org(e):
                if dd_org.value:
                    app_state["active_org"] = str(dd_org.value)
                    update_appbar()
                    tourn_state["sub_tab"] = None; tourn_state["active_match"] = None
                    history_state["active_tourn"] = None; history_state["sub_tab"] = "tabelas"
                    home_state["selected_ids"].clear()
                    page.snack_bar = ft.SnackBar(ft.Text(f"Ambiente alterado para {dd_org.value.upper()}!"), bgcolor=C_SUCCESS)
                    page.snack_bar.open = True; refresh_current_tab()
            btn_confirmar = PrimaryBtn("Confirmar", apply_org, width=120)
            col_elements.extend([ft.Container(height=10), ft.Row([dd_org, btn_confirmar], alignment=ft.MainAxisAlignment.CENTER)])
        else:
            col_elements.append(ft.Text(f"Ambiente: {get_current_org().upper()}", color=C_PRIMARY, size=14, weight=ft.FontWeight.BOLD))
            
        role_label = {
            "basic": "Licença Básica", "treinador": "Licença Treinador", 
            "organizador": "Licença Organizador", "pro": "Licença PRO", "admin_max": "Licença Admin Suprema", "judge": "Licença Organizador"
        }.get(current_user().get("role", "basic"), "Licença Básica")

        col_elements.extend([
            ft.Container(height=10), Badge(role_label, C_PRIMARY), ft.Container(height=20),
            ft.Text("Sua conta permite gerenciar e visualizar dados exclusivos do seu ambiente atual de acordo com seu plano.", color=C_TEXT_SEC, text_align="center"),
            ft.Container(expand=True), 
            ft.Divider(color=C_BORDER),
            CreditsFooter()
        ])
        return ft.Container(padding=24, content=ft.Column(col_elements, horizontal_alignment=ft.CrossAxisAlignment.CENTER))

    # --- TELA 1: TREINO ISOLADO (TREINADORES E PRO) ---
    def build_training_view():
        if not has_treino_access(): return ft.Container(content=ft.Text("Acesso Restrito. Exija a Licença Treinador ou PRO.", color=C_ERROR), padding=24)

        if training_state["sub_tab"] == "combat":
            m_data = training_state["match_data"]; score_p1 = ft.Text(str(training_state["p1_score"]), size=64, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI); score_p2 = ft.Text(str(training_state["p2_score"]), size=64, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI)
            p1_display = ft.Text(m_data["combo_testado"], size=16, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, text_align="center", overflow=ft.TextOverflow.ELLIPSIS)
            p2_display = ft.Text(m_data["combo_adversario"], size=16, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, text_align="center", overflow=ft.TextOverflow.ELLIPSIS)

            def process_win():
                if training_state["match_ended"]: return 
                training_state["match_ended"] = True
                def finish_match(e):
                    hide_dialog(dlg)
                    def async_save_training():
                        safe_cloud_sync()
                        record = {"id": str(int(time.time()*1000)), "DATA": datetime.now().strftime('%d/%m/%Y %H:%M'), "NOME_TREINO": m_data["treino_nome"], "COMBO_TESTADO": m_data["combo_testado"], "COMBO_ADVERSARIO": m_data["combo_adversario"], "LADO_ARENA": m_data["lado_arena"], "MEU_XTREME": training_state["p1_finishes"]["xtreme"], "MEU_BURST": training_state["p1_finishes"]["burst"], "MEU_OVER": training_state["p1_finishes"]["over"], "MEU_SPIN": training_state["p1_finishes"]["spin"], "MEU_FLAG": training_state["p1_finishes"]["flag"], "ADV_XTREME": training_state["p2_finishes"]["xtreme"], "ADV_BURST": training_state["p2_finishes"]["burst"], "ADV_OVER": training_state["p2_finishes"]["over"], "ADV_SPIN": training_state["p2_finishes"]["spin"], "ADV_FLAG": training_state["p2_finishes"]["flag"], "PLACAR": f'{training_state["p1_score"]} x {training_state["p2_score"]}', "RESULTADO": "Vitória" if training_state["p1_score"] > training_state["p2_score"] else "Derrota"}
                        _add_to_training_history(record); training_state["sub_tab"] = "setup"; refresh_current_tab()
                    threading.Thread(target=async_save_training, daemon=True).start()
                dlg = ft.AlertDialog(modal=True, bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text(f"Treino Concluído!", color=C_SUCCESS, weight=ft.FontWeight.BOLD), content=ft.Text("Os dados foram capturados para a planilha.", color=C_TEXT_SEC), actions=[PrimaryBtn("Salvar e Voltar", finish_match, width=float("inf"))])
                show_dialog(dlg)

            def add_points(player, pts, t_finish):
                if training_state["match_ended"]: return 
                if player == 1: training_state["p1_score"] += pts; training_state["p1_finishes"][t_finish] += 1; score_p1.value = str(training_state["p1_score"])
                else: training_state["p2_score"] += pts; training_state["p2_finishes"][t_finish] += 1; score_p2.value = str(training_state["p2_score"])
                page.update()
                if training_state["p1_score"] >= PTS_WIN_TARGET or training_state["p2_score"] >= PTS_WIN_TARGET: process_win()

            def reset_match(e=None):
                training_state["p1_score"], training_state["p2_score"] = 0, 0
                training_state["p1_finishes"] = {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}; training_state["p2_finishes"] = {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}
                training_state["match_ended"] = False; score_p1.value, score_p2.value = "0", "0"; page.update()

            def action_col(p):
                return ft.Column([PrimaryBtn(f"XTREME (+{PTS_MAP['xtreme']})", lambda _: add_points(p, PTS_MAP['xtreme'], "xtreme"), width=145, height=44, color=C_PRIMARY), SecondaryBtn(f"BURST (+{PTS_MAP['burst']})", lambda _: add_points(p, PTS_MAP['burst'], "burst"), width=145, height=44), SecondaryBtn(f"OVER (+{PTS_MAP['over']})", lambda _: add_points(p, PTS_MAP['over'], "over"), width=145, height=44), SecondaryBtn(f"SPIN (+{PTS_MAP['spin']})", lambda _: add_points(p, PTS_MAP['spin'], "spin"), width=145, height=44), SecondaryBtn(f"FLAG (+{PTS_MAP['flag']})", lambda _: add_points(p, PTS_MAP['flag'], "flag"), width=145, height=44)], spacing=12, alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

            return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Row([IconButton(ft.Icons.ARROW_BACK, lambda _: [training_state.update({"sub_tab": "setup"}), refresh_current_tab()]), ft.Text(f"TREINO: {m_data['treino_nome'].upper()}", color=C_TEXT_PRI, weight=ft.FontWeight.W_600, size=13, expand=True, text_align="center"), ft.Container(width=42)]), bgcolor=C_SUCCESS, padding=12, width=float("inf")), ft.Container(padding=24, expand=True, content=ft.Column([ft.Row([ft.Column([p1_display, score_p1, action_col(1)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER), ft.Container(width=1, bgcolor=C_BORDER, height=300, margin=ft.margin.symmetric(horizontal=8)), ft.Column([p2_display, score_p2, action_col(2)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START), ft.Container(expand=True), SecondaryBtn("Resetar Placar", reset_match, width=float("inf"), icon=ft.Icons.REFRESH)]))]))
        
        else:
            treino_nome_input = ft.TextField(label="Nome do Treino (Ex: Teste Foco)", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            combo_test_input = ft.TextField(label="Seu Combo (Testado)", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            combo_adv_input = ft.TextField(label="Combo do Adversário", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            lado_dropdown = ft.Dropdown(label="Lado da Arena", options=[ft.dropdown.Option("B Side"), ft.dropdown.Option("X Side")], bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)

            def start_training(e):
                if not treino_nome_input.value or not combo_test_input.value or not combo_adv_input.value or not lado_dropdown.value:
                    page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos do treino!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return
                training_state["match_data"] = {"treino_nome": treino_nome_input.value.strip(), "combo_testado": combo_test_input.value.strip(), "combo_adversario": combo_adv_input.value.strip(), "lado_arena": lado_dropdown.value}
                training_state["p1_score"], training_state["p2_score"] = 0, 0
                training_state["p1_finishes"] = {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}; training_state["p2_finishes"] = {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}
                training_state["match_ended"] = False; training_state["sub_tab"] = "combat"; refresh_current_tab()

            def confirm_delete_training(t_id, t_name):
                def do_delete(e):
                    safe_cloud_sync()
                    with db_lock:
                        org = get_current_org()
                        hist = app_data.get("training_history", [])
                        app_data["training_history"] = [h for h in hist if not(h.get("id") == t_id and h.get("org", "admin") == org)]
                    save_db(app_data); hide_dialog(dlg); refresh_current_tab(); page.snack_bar = ft.SnackBar(ft.Text("Treino apagado!"), bgcolor=C_SUCCESS); page.snack_bar.open = True; page.update()
                dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Excluir Treino", color=C_TEXT_PRI), content=ft.Text(f"Apagar '{t_name}'?", color=C_TEXT_SEC), actions=[SecondaryBtn("Cancelar", lambda _: hide_dialog(dlg)), PrimaryBtn("Excluir", do_delete, color=C_ERROR)])
                show_dialog(dlg)

            def trigger_export(e):
                hist = _get_training_history()
                if not hist: page.snack_bar = ft.SnackBar(ft.Text("Nenhum histórico para exportar."), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return
                filename = f"Treino_{get_current_org()}_{int(time.time())}.csv"
                paths_to_try = ["/storage/emulated/0/Download", os.path.join(os.path.expanduser("~"), "Downloads"), os.getcwd()]
                success_path = ""
                headers = ["DATA", "NOME_TREINO", "COMBO_TESTADO", "COMBO_ADVERSARIO", "LADO_ARENA", "MEU_XTREME", "MEU_BURST", "MEU_OVER", "MEU_SPIN", "MEU_FLAG", "ADV_XTREME", "ADV_BURST", "ADV_OVER", "ADV_SPIN", "ADV_FLAG", "PLACAR", "RESULTADO"]

                for base_path in paths_to_try:
                    if os.path.exists(base_path) and os.path.isdir(base_path):
                        try:
                            filepath = os.path.join(base_path, filename)
                            with open(filepath, mode='w', encoding='utf-8-sig', newline='') as f:
                                writer = csv.writer(f, delimiter=';'); writer.writerow(headers)
                                for row in hist: writer.writerow([row.get(h, "0") for h in headers])
                            success_path = filepath; break 
                        except Exception: continue
                
                if success_path: dlg = ft.AlertDialog(title=ft.Text("Sucesso!"), content=ft.Text(f"Planilha exportada em:\n\n{success_path}", size=13), actions=[ft.TextButton("OK", on_click=lambda _: hide_dialog(dlg))]); show_dialog(dlg)
                else:
                    try:
                        filepath = os.path.abspath(filename)
                        with open(filepath, mode='w', encoding='utf-8-sig', newline='') as f:
                            writer = csv.writer(f, delimiter=';'); writer.writerow(headers)
                            for row in hist: writer.writerow([row.get(h, "0") for h in headers])
                        dlg = ft.AlertDialog(title=ft.Text("Aviso"), content=ft.Text(f"Salvo na pasta do app:\n\n{filepath}", size=13), actions=[ft.TextButton("OK", on_click=lambda _: hide_dialog(dlg))]); show_dialog(dlg)
                    except Exception: dlg = ft.AlertDialog(title=ft.Text("Erro"), content=ft.Text("Sem permissão para salvar no sistema."), actions=[ft.TextButton("OK", on_click=lambda _: hide_dialog(dlg))]); show_dialog(dlg)

            hist = _get_training_history()
            hist_list = ft.ListView(expand=True, spacing=10)
            for h in hist:
                res_color = C_SUCCESS if h.get("RESULTADO") == "Vitória" else C_ERROR
                hist_list.controls.append(AppCard(ft.Column([
                    ft.Row([ft.Text(h.get("DATA", ""), color=C_TEXT_SEC, size=12), ft.Row([ft.Text(h.get("RESULTADO", ""), color=res_color, weight=ft.FontWeight.BOLD), IconButton(ft.Icons.DELETE_OUTLINE, lambda e, t_id=h.get('id'), t_name=h.get('NOME_TREINO', 'Treino'): confirm_delete_training(t_id, t_name), color=C_ERROR)])], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(f"Treino: {h.get('NOME_TREINO', 'N/A')}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=14),
                    ft.Text(f"Meu: {h.get('COMBO_TESTADO')}  VS  Adv: {h.get('COMBO_ADVERSARIO')}", color=C_TEXT_PRI, weight=ft.FontWeight.W_500),
                    ft.Text(f"Placar: {h.get('PLACAR')} | Lado: {h.get('LADO_ARENA')}", color=C_TEXT_SEC, size=13),
                    ft.Text(f"MEU (XT:{h.get('MEU_XTREME',0)} OV:{h.get('MEU_OVER',0)} SP:{h.get('MEU_SPIN',0)}) | ADV (XT:{h.get('ADV_XTREME',0)} OV:{h.get('ADV_OVER',0)} SP:{h.get('ADV_SPIN',0)})", color=C_TEXT_SEC, size=11)
                ], spacing=4), padding=12))
            if not hist: hist_list.controls.append(ft.Text("Nenhum treino registrado ainda no seu ambiente.", color=C_TEXT_SEC))

            return ft.Container(padding=24, content=ft.Column([ft.Text("Laboratório de Combos", size=24, weight=ft.FontWeight.BOLD, color=C_PRIMARY), ft.Text("Configure os combos para iniciar a partida na arena.", size=13, color=C_TEXT_SEC), ft.Container(height=10), treino_nome_input, combo_test_input, combo_adv_input, lado_dropdown, PrimaryBtn("Ir para Arena de Treino", start_training, width=float("inf"), icon=ft.Icons.PLAY_ARROW), ft.Divider(color=C_BORDER, height=20), ft.Row([ft.Text("Histórico Privado", size=18, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI, expand=True), SecondaryBtn("Exportar CSV", trigger_export, icon=ft.Icons.DOWNLOAD)]), ft.Container(content=hist_list, expand=True)]))

    # --- TELA 2: BLADERS (ORGANIZADOR/PRO/ADMIN) ---
    def build_home_view():
        if not has_torneio_access(): return ft.Container(content=ft.Text("Acesso Restrito. Exclusivo Organizadores e Pro.", color=C_ERROR), padding=24)
        bladers = _get_bladers()
        def save_temp_name(e): home_state["temp_name"] = e.control.value
        
        blader_input = ft.TextField(value=home_state["temp_name"], hint_text="Nome do Blader...", expand=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, text_size=14, border_radius=12, content_padding=16, cursor_color=C_PRIMARY)
        blader_input.on_change = save_temp_name
        
        is_adding = False
        def add_blader(e):
            nonlocal is_adding
            if is_adding: return
            if blader_input.value.strip():
                is_adding = True; safe_cloud_sync(); b_list = _get_bladers()
                b_list.append({"id": str(int(time.time())), "name": blader_input.value.strip()})
                _save_bladers(b_list); home_state["temp_name"] = ""; blader_input.value = ""; refresh_current_tab(); is_adding = False

        def confirm_remove_blader(b_id, b_name):
            def do_remove(e):
                safe_cloud_sync()
                if b_id in home_state["selected_ids"]: home_state["selected_ids"].remove(b_id)
                _save_bladers([b for b in _get_bladers() if b["id"] != b_id]); hide_dialog(dlg_confirm); refresh_current_tab()
            dlg_confirm = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Confirmar", color=C_TEXT_PRI), content=ft.Text(f"Remover '{b_name}'?", color=C_TEXT_SEC), actions=[SecondaryBtn("Cancelar", lambda _: hide_dialog(dlg_confirm)), PrimaryBtn("Remover", do_remove, color=C_ERROR)])
            show_dialog(dlg_confirm)

        bladers_list_ui = ft.ListView(expand=True, spacing=12)
        for b in bladers: bladers_list_ui.controls.append(AppCard(ft.Row([ft.Text(b["name"], weight=ft.FontWeight.W_500, color=C_TEXT_PRI, size=15, expand=True), IconButton(ft.Icons.DELETE_OUTLINE, lambda e, bid=b["id"], bname=b["name"]: confirm_remove_blader(bid, bname), color=C_ERROR)]), padding=12))

        view_cadastro = ft.Column([ft.Text("Adicionar Participantes", size=14, color=C_TEXT_SEC), ft.Row([blader_input, PrimaryBtn("Add", add_blader, width=80, height=52)]), ft.Container(height=12), ft.Container(content=bladers_list_ui, expand=True)])
        
        selection_list_ui = ft.ListView(expand=True, spacing=12)
        def toggle_selection(e, b_id):
            if e.control.value:
                if b_id not in home_state["selected_ids"]: home_state["selected_ids"].append(b_id)
            else:
                if b_id in home_state["selected_ids"]: home_state["selected_ids"].remove(b_id)
            btn_criar.content.controls[1].value = f"Avançar para Passo 2 ({len(home_state['selected_ids'])})"; page.update()

        for b in bladers: selection_list_ui.controls.append(AppCard(ft.Checkbox(label=b["name"], value=(b["id"] in home_state["selected_ids"]), on_change=lambda e, bid=b["id"]: toggle_selection(e, bid), fill_color=C_PRIMARY, check_color=C_BG, label_style=ft.TextStyle(color=C_TEXT_PRI, size=15, weight=ft.FontWeight.W_500)), padding=8))

        view_config_container = ft.Container(expand=True)

        def open_config_view(e):
            selected_bladers = [b for b in _get_bladers() if b["id"] in home_state["selected_ids"]]; total_b = len(selected_bladers)
            if total_b < 2: page.snack_bar = ft.SnackBar(ft.Text("Selecione pelo menos 2 Bladers!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return 
            
            config_state = {"num_groups": 1, "sizes": [total_b]}
            max_groups = max(1, total_b // 2)
            dist_col = ft.Column(spacing=4); sum_text = ft.Text("", color=C_TEXT_SEC, size=13, weight=ft.FontWeight.W_600)

            def update_dist_ui():
                dist_col.controls.clear(); current_sum = sum(config_state["sizes"])
                for i in range(config_state["num_groups"]):
                    def make_btn(idx, delta):
                        def on_click(e):
                            if config_state["sizes"][idx] + delta >= 1: config_state["sizes"][idx] += delta; update_dist_ui()
                        return ft.IconButton(ft.Icons.ADD if delta>0 else ft.Icons.REMOVE, on_click=on_click, icon_color=C_TEXT_PRI, bgcolor=C_SURFACE_SEC, width=35, height=35)
                    dist_col.controls.append(ft.Row([ft.Text(f"Grupo {chr(65+i)}", color=C_TEXT_PRI, width=65, size=14, weight=ft.FontWeight.BOLD), make_btn(i, -1), ft.Text(str(config_state["sizes"][i]), color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, width=20, text_align="center"), make_btn(i, 1)], alignment=ft.MainAxisAlignment.CENTER, spacing=12))
                
                diff = total_b - current_sum
                if diff == 0: sum_text.value = f"✅ Total perfeito: {total_b} participantes"; sum_text.color = C_SUCCESS
                elif diff > 0: sum_text.value = f"⚠️ Faltam alocar {diff} participante(s)"; sum_text.color = C_ERROR
                else: sum_text.value = f"⚠️ Sobrando {-diff} vaga(s). Reduza."; sum_text.color = C_ERROR
                page.update() 

            def on_group_count_change(e=None):
                new_count = int(dd_groups.value); config_state["num_groups"] = new_count
                base = total_b // new_count; rem = total_b % new_count
                config_state["sizes"] = [base + (1 if i < rem else 0) for i in range(new_count)]; update_dist_ui()

            dd_groups = ft.Dropdown(options=[ft.dropdown.Option(key=str(i), text=f"{i} Grupo(s)") for i in range(1, max_groups + 1)], value="1", expand=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            dd_groups.on_change = on_group_count_change 
            btn_refresh = ft.Container(content=ft.Icon(ft.Icons.SYNC, color=C_PRIMARY), bgcolor=C_SURFACE_SEC, padding=12, border_radius=12, border=ft.border.all(1, C_BORDER), on_click=on_group_count_change, tooltip="Atualizar Distribuição")
            
            dd_advances = ft.Dropdown(options=[ft.dropdown.Option(key=str(i), text=f"{i} por Grupo") for i in range(1, 5)], value="2", expand=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            name_input = ft.TextField(label="Nome do Torneio", value=f"Torneio {datetime.now().strftime('%d/%m')}", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)

            def optimize_match_order(match_list):
                if len(match_list) <= 2: return match_list
                random.shuffle(match_list); arranged = [match_list.pop(0)]
                while match_list:
                    best_idx = 0; best_score = -999
                    for idx, m in enumerate(match_list):
                        score = 0; players = {m["blader1"], m["blader2"]}; last_players = {arranged[-1]["blader1"], arranged[-1]["blader2"]}
                        if players.intersection(last_players): score -= 10
                        if len(arranged) >= 2:
                            prev_players = {arranged[-2]["blader1"], arranged[-2]["blader2"]}
                            if players.intersection(prev_players): score -= 5
                        if score > best_score: best_score = score; best_idx = idx
                    arranged.append(match_list.pop(best_idx))
                return arranged

            def confirm_create(e):
                if sum(config_state["sizes"]) != total_b: page.snack_bar = ft.SnackBar(ft.Text("⚠️ Ajuste as vagas! Use o botão atualizar (🔄) se necessário."), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return
                safe_cloud_sync(); groups = []
                participants_snapshot = {b["id"]: b["name"] for b in selected_bladers}
                shuffled_bladers = list(selected_bladers); random.shuffle(shuffled_bladers) 
                blader_idx = 0; judges_pool = ["juiz_1", "juiz_2"] 
                num_groups = len(config_state["sizes"]); is_odd_groups = (num_groups % 2 != 0)
                
                for i, size in enumerate(config_state["sizes"]):
                    group_bladers = shuffled_bladers[blader_idx : blader_idx + size]; blader_idx += size
                    matches = [{"id": f"{i}-{j}-{k}-{int(time.time()*1000)}", "groupId": f"group-{i}", "blader1": group_bladers[j]["id"], "blader2": group_bladers[k]["id"], "completed": False} for j in range(len(group_bladers)) for k in range(j + 1, len(group_bladers))]
                    matches = optimize_match_order(matches)
                    
                    if is_odd_groups and i == num_groups - 1:
                        for m_idx, match in enumerate(matches): match["judge"] = judges_pool[m_idx % 2]
                    else:
                        g_judge = judges_pool[i % 2]
                        for match in matches: match["judge"] = g_judge
                            
                    groups.append({"id": f"group-{i}", "name": f"Grupo {chr(65 + i)}", "bladerIds": [b["id"] for b in group_bladers], "matches": matches})
                
                _save_tournament({"id": str(int(time.time())), "name": name_input.value.strip() or "Torneio X", "date": datetime.now().strftime('%d/%m/%Y %H:%M'), "groups": groups, "status": "groups", "knockout": [], "participants": participants_snapshot, "advancing_per_group": int(dd_advances.value)})
                home_state["selected_ids"].clear(); switch_home_tab("selecao"); tourn_state["sub_tab"] = "grupos"; nav_to_tab("Torneio") 
            
            update_dist_ui()
            view_config_container.content = ft.Column([ft.Text("Passo 2: Definir Grupos e Vagas", size=14, color=C_TEXT_SEC), AppCard(ft.Column([name_input, ft.Text("Quantidade de Grupos:", color=C_TEXT_SEC, size=13), ft.Row([dd_groups, btn_refresh]), ft.Text("Avançam por Grupo:", color=C_TEXT_SEC, size=13), ft.Row([dd_advances]), ft.Divider(color=C_BORDER, height=20), ft.Text("Ajuste manual de vagas:", color=C_TEXT_SEC, size=13), dist_col, ft.Container(content=sum_text, alignment=ft.Alignment(0,0))], spacing=16)), ft.Row([SecondaryBtn("Voltar", lambda _: switch_home_tab("selecao"), expand=True), PrimaryBtn("Sortear e Criar", confirm_create, expand=True)], spacing=12)], scroll=ft.ScrollMode.AUTO)
            switch_home_tab("config")

        btn_criar = PrimaryBtn(f"Avançar para Passo 2 ({len(home_state['selected_ids'])})", open_config_view, width=float("inf"), icon=ft.Icons.ROCKET_LAUNCH)
        view_selecao = ft.Column([ft.Text("Passo 1: Marque os Bladers", size=14, color=C_TEXT_SEC), ft.Container(content=selection_list_ui, expand=True), ft.Divider(color=C_BORDER, height=12), btn_criar])
        tab_nav_container = ft.Container(); content_switcher = ft.Container(expand=True)

        def build_home_tab_row():
            is_c = home_state["sub_tab"] == "cadastro"; is_s = home_state["sub_tab"] in ["selecao", "config"]
            tabs = [ft.Container(content=ft.Text("Banco Geral", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_c else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_c else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_home_tab("cadastro")), ft.Container(content=ft.Text("Criar Torneio", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_s else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_s else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_home_tab("selecao"))]
            tab_nav_container.content = ft.Container(content=ft.Row(tabs, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BORDER), border_radius=10, padding=4, margin=ft.margin.only(bottom=16))

        def switch_home_tab(tab_name):
            home_state["sub_tab"] = tab_name; build_home_tab_row()
            if tab_name == "cadastro": content_switcher.content = view_cadastro
            elif tab_name == "selecao": content_switcher.content = view_selecao
            elif tab_name == "config": content_switcher.content = view_config_container
            page.update()

        switch_home_tab(home_state["sub_tab"])
        return ft.Container(padding=24, content=ft.Column([ft.Text("Gestão de Bladers", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), tab_nav_container, content_switcher]))

    # --- TELA 3: COMBATE CASUAL (TODOS) ---
    def build_quick_match_view():
        state = {"p1_score": 0, "p2_score": 0, "p1_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "p2_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "match_ended": False}
        score_p1 = ft.Text("0", size=64, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI); score_p2 = ft.Text("0", size=64, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI)
        p1_input = ft.TextField(value="Jogador 1", text_align=ft.TextAlign.CENTER, bgcolor="transparent", border_color="transparent", color=C_TEXT_PRI, text_size=16, content_padding=0)
        p2_input = ft.TextField(value="Jogador 2", text_align=ft.TextAlign.CENTER, bgcolor="transparent", border_color="transparent", color=C_TEXT_PRI, text_size=16, content_padding=0)

        def process_win():
            if state["match_ended"]: return 
            state["match_ended"] = True
            winner = p1_input.value.strip() if state["p1_score"] > state["p2_score"] else p2_input.value.strip()
            def reset_and_close(e): hide_dialog(dlg); reset()
            dlg = ft.AlertDialog(modal=True, bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text(f"🏆 Vitória de {winner}!", color=C_PRIMARY, weight=ft.FontWeight.BOLD), content=ft.Text("Partida casual concluída.", color=C_TEXT_SEC), actions=[PrimaryBtn("Limpar Placar", reset_and_close, width=float("inf"))])
            show_dialog(dlg)

        def add_points(player, pts, type_finish):
            if state["match_ended"]: return 
            if player == 1: state["p1_score"] += pts; state["p1_finishes"][type_finish] += 1; score_p1.value = str(state["p1_score"])
            else: state["p2_score"] += pts; state["p2_finishes"][type_finish] += 1; score_p2.value = str(state["p2_score"])
            page.update()
            if state["p1_score"] >= PTS_WIN_TARGET or state["p2_score"] >= PTS_WIN_TARGET: process_win()

        def reset(e=None):
            state["p1_score"], state["p2_score"], state["match_ended"] = 0, 0, False; score_p1.value, score_p2.value = "0", "0"; page.update()

        def action_col(p):
            return ft.Column([PrimaryBtn(f"XTREME (+{PTS_MAP['xtreme']})", lambda _: add_points(p, PTS_MAP['xtreme'], "xtreme"), width=145, height=44, color=C_PRIMARY), SecondaryBtn(f"BURST (+{PTS_MAP['burst']})", lambda _: add_points(p, PTS_MAP['burst'], "burst"), width=145, height=44), SecondaryBtn(f"OVER (+{PTS_MAP['over']})", lambda _: add_points(p, PTS_MAP['over'], "over"), width=145, height=44), SecondaryBtn(f"SPIN (+{PTS_MAP['spin']})", lambda _: add_points(p, PTS_MAP['spin'], "spin"), width=145, height=44), SecondaryBtn(f"FLAG (+{PTS_MAP['flag']})", lambda _: add_points(p, PTS_MAP['flag'], "flag"), width=145, height=44)], spacing=12, alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Text("PARTIDA CASUAL", color=C_TEXT_SEC, weight=ft.FontWeight.W_600, size=13, text_align="center"), bgcolor=C_SURFACE_SEC, padding=12, width=float("inf")), ft.Container(padding=24, expand=True, content=ft.Column([ft.Row([ft.Column([p1_input, score_p1, action_col(1)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER), ft.Container(width=1, bgcolor=C_BORDER, height=300, margin=ft.margin.symmetric(horizontal=8)), ft.Column([p2_input, score_p2, action_col(2)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START), ft.Container(expand=True), SecondaryBtn("Resetar Placar", reset, width=float("inf"), icon=ft.Icons.REFRESH)]))]))

    # --- TELA 4: TORNEIO E HUB ADMIN (ORGANIZADORES/PRO/ADMIN) ---
    def build_tournament_view():
        if not has_torneio_access(): return ft.Container(content=ft.Text("Acesso Restrito.", color=C_ERROR), padding=24)
        
        if is_admin_max() and app_state.get("admin_viewing_org") == "admin":
            safe_cloud_sync(); tourns = app_data.get("tournaments", {})
            hub_ui = ft.ListView(expand=True, spacing=12)
            
            def force_delete_active(e, oid):
                def confirm(e):
                    safe_cloud_sync()
                    with db_lock:
                        if oid in app_data.get("tournaments", {}): del app_data["tournaments"][oid]
                        if oid in app_data.get("active_matches", {}): del app_data["active_matches"][oid]
                    save_db(app_data); hide_dialog(dlg); refresh_current_tab(); page.snack_bar = ft.SnackBar(ft.Text(f"Torneio apagado!"), bgcolor=C_SUCCESS); page.snack_bar.open = True; page.update()
                dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Excluir Torneio Ativo", color=C_TEXT_PRI), content=ft.Text(f"Apagar permanentemente o torneio da Org {oid.upper()}?", color=C_TEXT_SEC), actions=[SecondaryBtn("Cancelar", lambda _: hide_dialog(dlg)), PrimaryBtn("Excluir", confirm, color=C_ERROR)])
                show_dialog(dlg)

            for org_id, t_data in tourns.items():
                def enter_org(e, oid=org_id):
                    app_state["admin_viewing_org"] = oid
                    tourn_state["sub_tab"] = None
                    tourn_state["active_match"] = None
                    history_state["active_tourn"] = None
                    update_appbar()
                    refresh_current_tab()
                    
                hub_ui.controls.append(AppCard(ft.Row([ft.Column([ft.Text(f"AMBIENTE: {org_id.upper()}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=12), ft.Text(t_data.get("name", "Torneio"), color=C_TEXT_PRI, size=18, weight=ft.FontWeight.W_600)], expand=True), PrimaryBtn("Inspecionar", enter_org, icon=ft.Icons.VISIBILITY), IconButton(ft.Icons.DELETE_OUTLINE, lambda e, oid=org_id: force_delete_active(e, oid), color=C_ERROR)])))
            if not hub_ui.controls: hub_ui.controls.append(ft.Text("Nenhum torneio ativo no momento em nenhum ambiente.", color=C_TEXT_SEC))
            return ft.Container(padding=24, content=ft.Column([ft.Text("Monitoramento Global", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), ft.Text("Selecione um torneio ativo para assumir o controle da tabela.", color=C_TEXT_SEC, size=13), ft.Container(height=12), ft.Container(content=hub_ui, expand=True)]))

        tourn = _get_tournament()
        if not tourn: return ft.Container(content=ft.Column([ft.Icon(ft.Icons.EMOJI_EVENTS_OUTLINED, size=64, color=C_BORDER), ft.Text("Nenhum torneio em andamento.", color=C_TEXT_SEC, size=16)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True, alignment=ft.Alignment(0,0))

        bladers_map = get_snapshot_map(tourn)
        
        if tourn_state["sub_tab"] is None or (tourn_state["sub_tab"] == "matamata" and tourn.get("status") != "knockout"): 
            tourn_state["sub_tab"] = "matamata" if tourn.get("status") == "knockout" else "grupos"
            
        if tourn_state["sub_tab"] == "combat":
            m_data = tourn_state["active_match"]; state = tourn_state["match_state"]
            score_p1 = ft.Text(str(state["p1_score"]), size=64, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI)
            score_p2 = ft.Text(str(state["p2_score"]), size=64, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI)
            p1_display = ft.Text(m_data["b1_name"], size=16, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, text_align="center", overflow=ft.TextOverflow.ELLIPSIS)
            p2_display = ft.Text(m_data["b2_name"], size=16, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, text_align="center", overflow=ft.TextOverflow.ELLIPSIS)

            def process_win():
                if state["match_ended"]: return 
                state["match_ended"] = True
                winner_name = m_data["b1_name"] if state["p1_score"] > state["p2_score"] else m_data["b2_name"]
                w_id = m_data["b1_id"] if state["p1_score"] > state["p2_score"] else m_data["b2_id"]
                
                def finish_match(e):
                    hide_dialog(dlg)
                    def async_save_match():
                        safe_cloud_sync(); fresh_t = _get_tournament()
                        if not fresh_t: return
                        loser_id = m_data["b2_id"] if w_id == m_data["b1_id"] else m_data["b1_id"]
                        
                        if m_data["is_knockout"]:
                            r_idx = m_data["round_idx"]; m_idx = 0
                            for i, m in enumerate(fresh_t.get("knockout", [])[r_idx].get("matches", [])):
                                if m.get("id") == m_data["match_id"]:
                                    m_idx = i; m["completed"] = True
                                    m["result"] = {"blader1Result": {"bladerId": m_data["b1_id"], "totalPoints": state["p1_score"], "finishes": state["p1_finishes"]}, "blader2Result": {"bladerId": m_data["b2_id"], "totalPoints": state["p2_score"], "finishes": state["p2_finishes"]}, "winner": w_id}
                                    break
                            if r_idx + 1 < len(fresh_t.get("knockout", [])):
                                next_m_idx = m_idx // 2; is_p1 = (m_idx % 2 == 0); is_semi = (r_idx == len(fresh_t["knockout"]) - 2)
                                if is_semi:
                                    if is_p1: fresh_t["knockout"][r_idx + 1]["matches"][0]["blader1"] = w_id
                                    else:     fresh_t["knockout"][r_idx + 1]["matches"][0]["blader2"] = w_id
                                    if len(fresh_t["knockout"][r_idx + 1]["matches"]) > 1:
                                        if is_p1: fresh_t["knockout"][r_idx + 1]["matches"][1]["blader1"] = loser_id
                                        else:     fresh_t["knockout"][r_idx + 1]["matches"][1]["blader2"] = loser_id
                                else:
                                    if is_p1: fresh_t["knockout"][r_idx + 1]["matches"][next_m_idx]["blader1"] = w_id
                                    else:     fresh_t["knockout"][r_idx + 1]["matches"][next_m_idx]["blader2"] = w_id
                        else:
                            for g in fresh_t.get("groups", []):
                                if g.get("id") == m_data["group_id"]:
                                    for m in g.get("matches", []):
                                        if m.get("id") == m_data["match_id"]:
                                            m["completed"] = True
                                            m["result"] = {"blader1Result": {"bladerId": m_data["b1_id"], "totalPoints": state["p1_score"], "finishes": state["p1_finishes"]}, "blader2Result": {"bladerId": m_data["b2_id"], "totalPoints": state["p2_score"], "finishes": state["p2_finishes"]}, "winner": w_id}
                        _save_tournament(fresh_t); tourn_state["sub_tab"] = "partidas"; tourn_state["active_match"] = None; refresh_current_tab() 
                    threading.Thread(target=async_save_match, daemon=True).start()

                dlg = ft.AlertDialog(modal=True, bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text(f"🏆 Vitória de {winner_name}!", color=C_PRIMARY, weight=ft.FontWeight.BOLD), content=ft.Text("Partida concluída na nuvem.", color=C_TEXT_SEC), actions=[PrimaryBtn("Confirmar e Voltar", finish_match, width=float("inf"))])
                show_dialog(dlg)

            def add_points(player, pts, type_finish):
                if state["match_ended"]: return 
                if player == 1: state["p1_score"] += pts; state["p1_finishes"][type_finish] += 1; score_p1.value = str(state["p1_score"])
                else: state["p2_score"] += pts; state["p2_finishes"][type_finish] += 1; score_p2.value = str(state["p2_score"])
                page.update()
                if state["p1_score"] >= PTS_WIN_TARGET or state["p2_score"] >= PTS_WIN_TARGET: process_win()

            def reset_match(e=None):
                state["p1_score"], state["p2_score"] = 0, 0
                state["p1_finishes"] = {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}; state["p2_finishes"] = {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}
                state["match_ended"] = False; score_p1.value, score_p2.value = "0", "0"; page.update()
                
            def cancel_match(e): tourn_state["sub_tab"] = "partidas"; tourn_state["active_match"] = None; refresh_current_tab()

            def action_col(p): return ft.Column([PrimaryBtn(f"XTREME (+{PTS_MAP['xtreme']})", lambda _: add_points(p, PTS_MAP['xtreme'], "xtreme"), width=145, height=44, color=C_PRIMARY), SecondaryBtn(f"BURST (+{PTS_MAP['burst']})", lambda _: add_points(p, PTS_MAP['burst'], "burst"), width=145, height=44), SecondaryBtn(f"OVER (+{PTS_MAP['over']})", lambda _: add_points(p, PTS_MAP['over'], "over"), width=145, height=44), SecondaryBtn(f"SPIN (+{PTS_MAP['spin']})", lambda _: add_points(p, PTS_MAP['spin'], "spin"), width=145, height=44), SecondaryBtn(f"FLAG (+{PTS_MAP['flag']})", lambda _: add_points(p, PTS_MAP['flag'], "flag"), width=145, height=44)], spacing=12, alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

            header_txt = "ELIMINATÓRIAS (OFICIAL)" if m_data["is_knockout"] else "FASE DE GRUPOS (OFICIAL)"
            header_col = C_ERROR if m_data["is_knockout"] else C_PRIMARY
            return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Row([IconButton(ft.Icons.ARROW_BACK, cancel_match), ft.Text(header_txt, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, size=13, expand=True, text_align="center"), ft.Container(width=42)]), bgcolor=header_col, padding=12, width=float("inf")), ft.Container(padding=24, expand=True, content=ft.Column([ft.Row([ft.Column([p1_display, score_p1, action_col(1)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER), ft.Container(width=1, bgcolor=C_BORDER, height=300, margin=ft.margin.symmetric(horizontal=8)), ft.Column([p2_display, score_p2, action_col(2)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START), ft.Container(expand=True), SecondaryBtn("Resetar Placar", reset_match, width=float("inf"), icon=ft.Icons.REFRESH)]))]))
            
        else:
            def open_admin_panel(e):
                if not is_pro() and not is_admin_max() and current_user().get("role") != "organizador": 
                    page.snack_bar = ft.SnackBar(ft.Text("Apenas admins/organizadores podem modificar a tabela."), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return
                safe_cloud_sync(); fresh_tourn = _get_tournament()
                in_tourn = [{"id": k, "name": v} for k, v in fresh_tourn.get("participants", {}).items()]
                out_tourn = [b for b in _get_bladers() if b["id"] not in fresh_tourn.get("participants", {})]

                dd_sai = ft.Dropdown(options=[ft.dropdown.Option(key=b["id"], text=b["name"]) for b in in_tourn], label="Quem saiu?", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI)
                if not out_tourn:
                    content_ui = ft.Text("⚠️ Você não tem Reservas no Banco.", color=C_ERROR, size=14, text_align="center"); actions_ui = [SecondaryBtn("Fechar", lambda _: hide_dialog(admin_dlg))]
                else:
                    dd_entra = ft.Dropdown(options=[ft.dropdown.Option(key=b["id"], text=b["name"]) for b in out_tourn], label="Quem entra?", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI)
                    content_ui = ft.Column([ft.Text("O reserva herda a vaga e os pontos de quem saiu.", color=C_TEXT_SEC, size=13), dd_sai, ft.Icon(ft.Icons.SWAP_VERT, color=C_PRIMARY), dd_entra], tight=True, horizontal_alignment="center")
                    
                    def perform_swap(e):
                        if not dd_sai.value or not dd_entra.value: return
                        id_sai, id_entra = dd_sai.value, dd_entra.value; nome_entra = next((b["name"] for b in out_tourn if b["id"] == id_entra), "Reserva")
                        if id_sai in fresh_tourn.get("participants", {}): del fresh_tourn["participants"][id_sai]
                        fresh_tourn["participants"][id_entra] = nome_entra
                        for g in fresh_tourn.get("groups", []):
                            g["bladerIds"] = [id_entra if x == id_sai else x for x in g.get("bladerIds", [])]
                            for m in g.get("matches", []):
                                if m.get("blader1") == id_sai: m["blader1"] = id_entra
                                if m.get("blader2") == id_sai: m["blader2"] = id_entra
                                if m.get("completed"):
                                    res = m.get("result", {})
                                    if res.get("blader1Result", {}).get("bladerId") == id_sai: res["blader1Result"]["bladerId"] = id_entra
                                    if res.get("blader2Result", {}).get("bladerId") == id_sai: res["blader2Result"]["bladerId"] = id_entra
                                    if res.get("winner") == id_sai: res["winner"] = id_entra
                        for rd in fresh_tourn.get("knockout", []):
                            for m in rd.get("matches", []):
                                if m.get("blader1") == id_sai: m["blader1"] = id_entra
                                if m.get("blader2") == id_sai: m["blader2"] = id_entra
                                if m.get("completed"):
                                    res = m.get("result", {})
                                    if res.get("blader1Result", {}).get("bladerId") == id_sai: res["blader1Result"]["bladerId"] = id_entra
                                    if res.get("blader2Result", {}).get("bladerId") == id_sai: res["blader2Result"]["bladerId"] = id_entra
                                    if res.get("winner") == id_sai: res["winner"] = id_entra
                        _save_tournament(fresh_tourn); hide_dialog(admin_dlg); refresh_current_tab()
                    actions_ui = [SecondaryBtn("Cancelar", lambda _: hide_dialog(admin_dlg)), PrimaryBtn("Substituir", perform_swap)]
                admin_dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Troca Oficial", color=C_TEXT_PRI, weight=ft.FontWeight.BOLD), content=content_ui, actions=actions_ui)
                show_dialog(admin_dlg)

            def get_group_standings(group):
                standings = {b_id: {"id": b_id, "name": bladers_map.get(b_id, "Blader Removido"), "j":0, "v":0, "d":0, "pf":0, "ps":0, "saldo":0, "xtreme":0} for b_id in group.get("bladerIds", [])}
                for match in group.get("matches", []):
                    if match.get("completed"):
                        res = match.get("result", {}); b1, b2, w = res.get("blader1Result", {}), res.get("blader2Result", {}), res.get("winner")
                        if not b1 or not b2: continue
                        for bx, bx_data in [(b1, standings.get(b1.get("bladerId"))), (b2, standings.get(b2.get("bladerId")))]:
                            if bx_data is None: continue
                            bx_data["j"] += 1; bx_data["pf"] += bx.get("totalPoints", 0); bx_data["xtreme"] += bx.get("finishes", {}).get("xtreme", 0)
                            if w == bx.get("bladerId"): bx_data["v"] += 1
                            else: bx_data["d"] += 1
                        if standings.get(b1.get("bladerId")): standings[b1["bladerId"]]["ps"] += b2.get("totalPoints", 0)
                        if standings.get(b2.get("bladerId")): standings[b2["bladerId"]]["ps"] += b1.get("totalPoints", 0)
                for s in standings.values(): s["saldo"] = s["pf"] - s["ps"]
                return sorted(standings.values(), key=lambda x: (x["v"], x["saldo"], x["xtreme"], x["pf"]), reverse=True)

            def advance_to_knockout(e):
                if not has_torneio_access(): return
                safe_cloud_sync(); fresh_tourn = _get_tournament()
                for g in fresh_tourn.get("groups", []):
                    if not all(m.get("completed") for m in g.get("matches", [])): page.snack_bar = ft.SnackBar(ft.Text(f"⚠️ Finalize todas as partidas do {g.get('name', 'Grupo')} antes de avançar!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return

                adv_per_group = int(fresh_tourn.get("advancing_per_group", 2)); seeded_players = []
                for pos in range(adv_per_group):
                    for g in fresh_tourn.get("groups", []):
                        st = get_group_standings(g)
                        if pos < len(st): seeded_players.append(st[pos]["id"])
                n = len(seeded_players)
                if n < 2: return 
                p2 = 1
                while p2 < n: p2 *= 2
                padded = seeded_players + [None] * (p2 - n)
                def get_seeds(size):
                    if size == 1: return [0]
                    half = get_seeds(size // 2); res = []
                    for x in half: res.append(x); res.append(size - 1 - x)
                    return res
                order = get_seeds(p2); ordered_players = [padded[i] for i in order]
                
                knockout = []; rounds = int(math.log2(p2)); round_names = {1: "Grande Final", 2: "Semifinais", 3: "Quartas de Final", 4: "Oitavas de Final", 5: "16 avos"}
                judges_pool = ["juiz_1", "juiz_2"]; curr_matches = []
                for i in range(0, p2, 2):
                    p1 = ordered_players[i]; p2_id = ordered_players[i+1]; is_bye = p1 is None or p2_id is None
                    winner = p1 if p2_id is None else p2_id if p1 is None else None
                    m = {"id": f"r0-m{i//2}-{int(time.time()*1000)}", "blader1": p1, "blader2": p2_id, "completed": is_bye, "judge": random.choice(judges_pool)}
                    if is_bye and winner is not None: m["result"] = {"blader1Result": {"bladerId": p1, "totalPoints": 0, "finishes": {}}, "blader2Result": {"bladerId": p2_id, "totalPoints": 0, "finishes": {}}, "winner": winner}
                    curr_matches.append(m)
                knockout.append({"name": round_names.get(rounds, f"Rodada {1}"), "matches": curr_matches})
                
                for r in range(1, rounds):
                    next_matches = []; prev_matches = knockout[r-1].get("matches", [])
                    for i in range(len(prev_matches) // 2):
                        m1 = prev_matches[i*2]; m2 = prev_matches[i*2 + 1]
                        b1 = m1.get("result", {}).get("winner") if m1.get("completed") else None
                        b2 = m2.get("result", {}).get("winner") if m2.get("completed") else None
                        next_matches.append({"id": f"r{r}-m{i}-{int(time.time()*1000)}", "blader1": b1, "blader2": b2, "completed": False, "judge": random.choice(judges_pool)})
                    knockout.append({"name": round_names.get(rounds - r, f"Rodada {r+1}"), "matches": next_matches})

                if rounds >= 2: knockout[-1]["matches"].append({"id": f"r{rounds-1}-m1-{int(time.time()*1000)}", "name": "Disputa de 3º Lugar", "blader1": None, "blader2": None, "completed": False, "judge": random.choice(judges_pool)})

                fresh_tourn["knockout"] = knockout; fresh_tourn["status"] = "knockout"; _save_tournament(fresh_tourn); tourn_state["sub_tab"] = "matamata"; refresh_current_tab()

            view_grupos = ft.ListView(expand=True, spacing=16, padding=ft.padding.only(top=16))
            view_partidas = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))
            view_matamata = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))

            def go_to_match(e):
                tourn_state["active_match"] = e.control.data
                tourn_state["match_state"] = {"p1_score": 0, "p2_score": 0, "p1_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "p2_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "match_ended": False}
                tourn_state["sub_tab"] = "combat"
                refresh_current_tab()

            def get_match_action_ui(match_data, b1_n, b2_n, is_ko=False, r_idx=0):
                if match_data.get("completed"):
                    res = match_data.get("result", {})
                    if match_data.get("blader1") is None or match_data.get("blader2") is None: return ft.Text("Avançou (W.O.)", color=C_TEXT_SEC, size=12)
                    pts1 = res.get("blader1Result", {}).get("totalPoints", 0); pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                    return ft.Row([ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=match_data: open_match_details(md, tourn))])
                else:
                    if is_ko and (match_data.get("blader1") is None or match_data.get("blader2") is None): return ft.Text("Aguardando...", color=C_TEXT_SEC, size=12)
                    assigned_judge = match_data.get("judge")
                    if has_torneio_access() or assigned_judge == get_username():
                        action_data = {"is_knockout": is_ko, "round_idx": r_idx, "match_id": match_data.get("id"), "group_id": match_data.get("groupId"), "b1_id": match_data.get("blader1"), "b1_name": b1_n, "b2_id": match_data.get("blader2"), "b2_name": b2_n, "judge": assigned_judge}
                        return PrimaryBtn("Jogar", go_to_match, height=36, width=80, data=action_data)
                    else: return ft.Row([ft.Icon(ft.Icons.LOCK, size=14, color=C_TEXT_SEC), ft.Text(f"Apito: {assigned_judge or 'Admin'}", color=C_TEXT_SEC, size=11)])

            for group in tourn.get("groups", []):
                sorted_st = get_group_standings(group); g_col = ft.Column([ft.Text(group.get("name", "Grupo"), size=16, weight=ft.FontWeight.W_600, color=C_TEXT_PRI)])
                g_col.controls.append(ft.Container(content=ft.Row([ft.Text("#", width=20, size=12, color=C_TEXT_SEC), ft.Text("Blader", expand=True, size=12, color=C_TEXT_SEC), ft.Text("J", width=25, size=12, color=C_TEXT_SEC, text_align="center"), ft.Text("V", width=25, size=12, color=C_TEXT_SEC, text_align="center"), ft.Text("PF", width=25, size=12, color=C_TEXT_SEC, text_align="center"), ft.Text("Sld", width=30, size=12, color=C_TEXT_SEC, text_align="center")]), padding=8, border=ft.border.only(bottom=ft.BorderSide(1, C_BORDER))))
                
                adv_limit = int(tourn.get("advancing_per_group", 2))
                for idx, st in enumerate(sorted_st):
                    is_top = idx < adv_limit 
                    g_col.controls.append(ft.Container(content=ft.Row([ft.Text(str(idx+1), width=20, size=14, color=C_TEXT_PRI if is_top else C_TEXT_SEC, weight=ft.FontWeight.W_600 if is_top else ft.FontWeight.NORMAL), ft.Text(st["name"], expand=True, size=14, color=C_TEXT_PRI, overflow=ft.TextOverflow.ELLIPSIS), ft.Text(str(st["j"]), width=25, size=14, color=C_TEXT_SEC, text_align="center"), ft.Text(str(st["v"]), width=25, size=14, color=C_TEXT_SEC, text_align="center"), ft.Text(str(st["pf"]), width=25, size=14, color=C_TEXT_SEC, text_align="center"), ft.Text(str(st["saldo"]), width=30, size=14, color=C_SUCCESS if st["saldo"] > 0 else C_ERROR, text_align="center", weight=ft.FontWeight.W_500)]), padding=8, bgcolor=C_SURFACE_SEC if is_top else "transparent", border_radius=8))
                view_grupos.controls.append(AppCard(g_col))

                view_partidas.controls.append(ft.Text(group.get("name", ""), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC, margin=ft.margin.only(top=8)))
                for match in group.get("matches", []):
                    b1_name = bladers_map.get(match.get("blader1"), "Blader Removido"); b2_name = bladers_map.get(match.get("blader2"), "Blader Removido")
                    view_partidas.controls.append(AppCard(ft.Row([ft.Column([ft.Text(b1_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI), ft.Text("vs", size=10, color=C_TEXT_SEC), ft.Text(b2_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI)]), get_match_action_ui(match, b1_name, b2_name)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

            if tourn.get("status") == "groups" and has_torneio_access(): view_grupos.controls.append(PrimaryBtn("Avançar para Mata-Mata", advance_to_knockout, width=float("inf")))
            
            if tourn.get("knockout"):
                for r_idx, round_data in enumerate(tourn.get("knockout", [])):
                    view_matamata.controls.append(ft.Text(round_data.get("name", ""), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC, margin=ft.margin.only(top=8)))
                    for match in round_data.get("matches", []):
                        b1_id = match.get("blader1"); b2_id = match.get("blader2")
                        b1_name = bladers_map.get(b1_id, "A definir") if b1_id else "A definir"; b2_name = bladers_map.get(b2_id, "A definir") if b2_id else "A definir"
                        match_title = match.get("name")
                        if match_title: view_matamata.controls.append(ft.Text(match_title, size=12, color=C_PRIMARY, text_align="center"))
                        status_ui = get_match_action_ui(match, b1_name, b2_name, is_ko=True, r_idx=r_idx)
                        view_matamata.controls.append(AppCard(ft.Row([ft.Column([ft.Text(b1_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI), ft.Text("vs", size=10, color=C_TEXT_SEC), ft.Text(b2_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI)]), status_ui], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

            tab_nav_container = ft.Container(padding=ft.padding.symmetric(horizontal=24))
            content_switcher = ft.Container(content=view_matamata if tourn_state["sub_tab"] == "matamata" else (view_partidas if tourn_state["sub_tab"] == "partidas" else view_grupos), expand=True)

            def build_tab_row():
                is_g = tourn_state["sub_tab"] == "grupos"; is_p = tourn_state["sub_tab"] == "partidas"; is_m = tourn_state["sub_tab"] == "matamata"
                tabs = [ft.Container(content=ft.Text("Grupos", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_g else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_g else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_sub_tab("grupos")), ft.Container(content=ft.Text("Partidas", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_p else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_p else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_sub_tab("partidas"))]
                if tourn.get("status") == "knockout": tabs.append(ft.Container(content=ft.Text("Mata-Mata", size=13, weight=ft.FontWeight.W_600, color=C_PRIMARY if is_m else C_TEXT_SEC), expand=True, bgcolor=f"{C_PRIMARY}15" if is_m else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_sub_tab("matamata")))
                tab_nav_container.content = ft.Container(content=ft.Row(tabs, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BORDER), border_radius=10, padding=4)

            def switch_sub_tab(tab_name): tourn_state["sub_tab"] = tab_name; build_tab_row(); page.update(); content_switcher.content = view_grupos if tab_name == "grupos" else (view_partidas if tab_name == "partidas" else view_matamata); page.update()
            build_tab_row() 

            def prompt_end_tourn(e):
                if not has_torneio_access(): return
                def handle_action(action):
                    safe_cloud_sync() 
                    if action == "salvar": _add_to_history(tourn)
                    _save_tournament(None); hide_dialog(dlg); refresh_current_tab()
                dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Encerrar Torneio", color=C_TEXT_PRI, size=18, weight=ft.FontWeight.BOLD), content=ft.Text("O que deseja fazer com os dados?", color=C_TEXT_SEC, size=14), actions=[SecondaryBtn("Excluir", lambda _: handle_action("excluir")), PrimaryBtn("Salvar no Histórico", lambda _: handle_action("salvar"))])
                show_dialog(dlg)

            actions_row = [IconButton(ft.Icons.REFRESH, lambda _: [safe_cloud_sync(), refresh_current_tab()], color=C_PRIMARY)]
            if has_torneio_access(): actions_row.extend([IconButton(ft.Icons.SWAP_HORIZ, open_admin_panel, color=C_PRIMARY), IconButton(ft.Icons.POWER_SETTINGS_NEW, prompt_end_tourn, color=C_ERROR)])

            return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Row([ft.Column([ft.Text(tourn.get("name",""), size=20, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), ft.Text(f"Ambiente: {get_current_org().upper()}", size=12, color=C_PRIMARY)], spacing=0), ft.Row(actions_row)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=24), tab_nav_container, ft.Container(content=content_switcher, padding=ft.padding.symmetric(horizontal=24), expand=True)]))

    # --- TELA 5: HISTÓRICO DE TORNEIOS (ORGANIZADOR/PRO/ADMIN) ---
    def build_history_view():
        if not has_torneio_access(): return ft.Container(content=ft.Text("Acesso Restrito.", color=C_ERROR), padding=24)

        if history_state["active_tourn"]:
            t_data = history_state["active_tourn"]
            
            b_map_history = {b["id"]: b["name"] for b in get_bladers(t_data.get("org", "admin"))}
            if "participants" in t_data: b_map_history.update(t_data["participants"])

            stats = {}
            def process_stats(m):
                if m.get("completed"):
                    res = m.get("result", {}); w = res.get("winner")
                    for b_key in ["blader1Result", "blader2Result"]:
                        b_res = res.get(b_key, {}); bid = b_res.get("bladerId")
                        if not bid: continue
                        if bid not in stats: stats[bid] = {"name": b_map_history.get(bid, "Blader Removido"), "j":0, "v":0, "pts":0, "spin":0, "over":0, "burst":0, "xtreme":0, "flag":0}
                        stats[bid]["j"] += 1; stats[bid]["pts"] += b_res.get("totalPoints", 0)
                        f_data = b_res.get("finishes", {})
                        stats[bid]["spin"] += f_data.get("spin", 0); stats[bid]["over"] += f_data.get("over", 0); stats[bid]["burst"] += f_data.get("burst", 0); stats[bid]["xtreme"] += f_data.get("xtreme", 0); stats[bid]["flag"] += f_data.get("flag", 0)
                        if w == bid: stats[bid]["v"] += 1

            for g in t_data.get("groups", []):
                for m in g.get("matches", []): process_stats(m)
            for r in t_data.get("knockout", []):
                for m in r.get("matches", []): process_stats(m)
            sorted_stats = sorted(stats.values(), key=lambda x: (x["v"], x["pts"], x["xtreme"]), reverse=True)

            view_tabelas = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))
            for g in t_data.get("groups", []):
                view_tabelas.controls.append(ft.Text(g.get('name', ''), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC))
                for m in g.get("matches", []):
                    if m.get("completed"):
                        res = m.get("result", {}); b1_n = b_map_history.get(m.get("blader1"), "Blader Removido"); b2_n = b_map_history.get(m.get("blader2"), "Blader Removido")
                        pts1 = res.get("blader1Result", {}).get("totalPoints", 0); pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                        status_ui = ft.Row([ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=m: open_match_details(md, t_data))])
                        view_tabelas.controls.append(AppCard(ft.Row([ft.Text(b1_n, size=14, color=C_TEXT_PRI), status_ui, ft.Text(b2_n, size=14, color=C_TEXT_PRI)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))
            
            for r in t_data.get("knockout", []):
                view_tabelas.controls.append(ft.Text(r.get("name", ""), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC, margin=ft.margin.only(top=8)))
                for match in r.get("matches", []):
                    match_title = match.get("name")
                    if match_title: view_tabelas.controls.append(ft.Text(match_title, size=12, color=C_PRIMARY, text_align="center"))
                    b1_id = match.get("blader1"); b2_id = match.get("blader2")
                    b1_name = b_map_history.get(b1_id, "A definir") if b1_id else "A definir"; b2_name = b_map_history.get(b2_id, "A definir") if b2_id else "A definir"
                    if match.get("completed"):
                        res = match.get("result", {})
                        if b1_id is None or b2_id is None: status_ui = ft.Text("Avançou (W.O.)", color=C_TEXT_SEC, size=12)
                        else:
                            pts1 = res.get("blader1Result", {}).get("totalPoints", 0); pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                            status_ui = ft.Row([ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=match: open_match_details(md, t_data))])
                        view_tabelas.controls.append(AppCard(ft.Row([ft.Text(b1_name, size=14, color=C_TEXT_PRI), status_ui, ft.Text(b2_name, size=14, color=C_TEXT_PRI)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

            view_stats = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))
            for st in sorted_stats: view_stats.controls.append(AppCard(ft.Column([ft.Row([ft.Text(st["name"], weight=ft.FontWeight.BOLD, size=16, color=C_TEXT_PRI, expand=True), ft.Text(f"{st['pts']} Pts", weight=ft.FontWeight.BOLD, size=16, color=C_PRIMARY)]), ft.Text(f"{st['v']} Vitórias em {st['j']} Jogos", size=12, color=C_TEXT_SEC), ft.Container(height=4), ft.Row([Badge(f"XT: {st['xtreme']}", C_XTREME), Badge(f"BU: {st['burst']}", C_BURST), Badge(f"OV: {st['over']}", C_OVER), Badge(f"SP: {st['spin']}", C_SPIN), Badge(f"FL: {st['flag']}", C_FLAG)], spacing=6, wrap=True)], spacing=4), padding=16))

            hist_nav_container = ft.Container(padding=ft.padding.symmetric(horizontal=24))
            content_switcher = ft.Container(content=view_tabelas if history_state["sub_tab"] == "tabelas" else view_stats, expand=True)

            def build_hist_tab_row():
                is_t = history_state["sub_tab"] == "tabelas"
                tabs = [ft.Container(content=ft.Text("Chaves", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_t else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_t else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_det_tab("tabelas")), ft.Container(content=ft.Text("Estatísticas", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if not is_t else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if not is_t else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_det_tab("estatisticas"))]
                hist_nav_container.content = ft.Container(content=ft.Row(tabs, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BORDER), border_radius=10, padding=4)

            def switch_det_tab(tab_name): history_state["sub_tab"] = tab_name; build_hist_tab_row(); content_switcher.content = view_tabelas if tab_name == "tabelas" else view_stats; page.update()
            build_hist_tab_row()
            def close_detail(e): history_state["active_tourn"] = None; refresh_current_tab()
            
            org_header = f"[{t_data.get('org', 'admin').upper()}] " if is_admin_max() and app_state.get("admin_viewing_org") == "admin" else ""

            return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Row([IconButton(ft.Icons.ARROW_BACK, lambda _: [history_state.update({"active_tourn": None}), refresh_current_tab()]), ft.Text(f"{org_header}{t_data.get('name', '')}", size=18, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI, expand=True, text_align="right")]), padding=24), hist_nav_container, ft.Container(content=content_switcher, padding=ft.padding.symmetric(horizontal=24), expand=True)]))

        hist = _get_history()
        if not hist: return ft.Container(content=ft.Column([ft.Icon(ft.Icons.HISTORY, size=64, color=C_BORDER), ft.Text("Histórico vazio.", color=C_TEXT_SEC, size=16)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True, alignment=ft.Alignment(0,0))
        list_ui = ft.ListView(expand=True, spacing=12, padding=24)
        list_ui.controls.append(ft.Text("Torneios Anteriores", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI, margin=ft.margin.only(bottom=8)))
        
        def confirm_delete_history(t_id, t_name, t_org):
            def do_delete(e):
                safe_cloud_sync()
                with db_lock:
                    h_list = app_data.get("history", [])
                    app_data["history"] = [h for h in h_list if not(h.get("id") == t_id and h.get("org", "admin") == t_org)]
                save_db(app_data); hide_dialog(dlg); refresh_current_tab(); page.snack_bar = ft.SnackBar(ft.Text("Torneio apagado!"), bgcolor=C_SUCCESS); page.snack_bar.open = True; page.update()
            dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Excluir Histórico", color=C_TEXT_PRI), content=ft.Text(f"Apagar '{t_name}'?", color=C_TEXT_SEC), actions=[SecondaryBtn("Cancelar", lambda _: hide_dialog(dlg)), PrimaryBtn("Excluir", do_delete, color=C_ERROR)])
            show_dialog(dlg)

        for t in hist:
            org_tag = f"[{t.get('org', 'admin').upper()}] " if is_admin_max() and app_state.get("admin_viewing_org") == "admin" else ""
            list_ui.controls.append(AppCard(ft.Row([
                ft.Column([ft.Text(f"{org_tag}{t.get('name', '')}", weight=ft.FontWeight.W_600, size=16, color=C_TEXT_PRI), ft.Text(f"{t.get('date', '')}", size=12, color=C_TEXT_SEC)], spacing=2, expand=True), 
                IconButton(ft.Icons.VISIBILITY, lambda e, data=t: [history_state.update({"active_tourn": data, "sub_tab": "tabelas"}), refresh_current_tab()], color=C_PRIMARY),
                IconButton(ft.Icons.DELETE_OUTLINE, lambda e, tid=t.get("id"), tname=t.get("name", ""), torg=t.get("org", "admin"): confirm_delete_history(tid, tname, torg), color=C_ERROR)
            ], spacing=12), padding=16))
        return ft.Container(content=list_ui, expand=True)

    # --- TELA 6: PAINEL ADMIN MAX (AGORA COM OS NOVOS PLANOS COMERCIAIS) ---
    def build_admin_view():
        if not is_admin_max(): return ft.Container(content=ft.Text("Acesso Negado.", color=C_ERROR), padding=24)
        admin_state = {"search_query": ""}
        search_input = ft.TextField(hint_text="Buscar usuário...", prefix_icon=ft.Icons.SEARCH, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12, content_padding=10)
        
        def on_search_change(e): admin_state["search_query"] = e.control.value; render_users()
        search_input.on_change = on_search_change
        
        users_list_ui = ft.ListView(expand=True, spacing=12)

        def render_users():
            users_list_ui.controls.clear()
            query = admin_state["search_query"].lower()
            
            all_users = {k: v.copy() for k, v in HARDCODED_USERS.items()}
            for k, v in get_users().items(): all_users[k] = v

            for u_name, u_data in all_users.items():
                if query and query not in u_name.lower(): continue 
                
                role_dd = ft.Dropdown(
                    value=u_data.get('role', 'basic'), 
                    options=[
                        ft.dropdown.Option("basic", "Básico"), 
                        ft.dropdown.Option("treinador", "Treinador"), 
                        ft.dropdown.Option("organizador", "Organizador"), 
                        ft.dropdown.Option("pro", "Pro"), 
                        ft.dropdown.Option("admin_max", "Admin Max")
                    ], 
                    width=130, height=40, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, text_size=12
                )
                org_input = ft.TextField(value=u_data.get('org', u_name), hint_text="Ex: org1, org2", label="Ambientes", width=120, height=40, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, text_size=12, content_padding=10)

                def save_user_role(e, un=u_name, dd=role_dd, oi=org_input, psw=u_data.get("password", "123")):
                    safe_cloud_sync(); db = get_users()
                    db[un] = {"password": psw, "role": dd.value, "org": oi.value.strip()}
                    save_users(db); page.snack_bar = ft.SnackBar(ft.Text(f"Acessos de {un} salvos!"), bgcolor=C_SUCCESS); page.snack_bar.open = True; page.update()

                def delete_user(e, un=u_name):
                    def confirm(e):
                        safe_cloud_sync(); db = get_users()
                        if un in db: del db[un]
                        save_users(db); hide_dialog(dlg); refresh_current_tab()
                    dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Excluir", color=C_TEXT_PRI), content=ft.Text(f"Deletar usuário '{un}'?", color=C_TEXT_SEC), actions=[SecondaryBtn("Cancelar", lambda _: hide_dialog(dlg)), PrimaryBtn("Excluir", confirm, color=C_ERROR)])
                    show_dialog(dlg)

                btn_save = IconButton(ft.Icons.SAVE, lambda e, un=u_name, dd=role_dd, oi=org_input: save_user_role(e, un, dd, oi), color=C_SUCCESS)
                btn_del = IconButton(ft.Icons.DELETE, lambda e, un=u_name: delete_user(e, un), color=C_ERROR)
                users_list_ui.controls.append(AppCard(ft.Row([ft.Text(u_name, weight=ft.FontWeight.W_600, size=14, color=C_TEXT_PRI, expand=True), org_input, role_dd, btn_save, btn_del], spacing=8), padding=12))

            if not users_list_ui.controls: users_list_ui.controls.append(ft.Text("Nenhum usuário encontrado.", color=C_TEXT_SEC))
            page.update()

        render_users() 
        return ft.Container(padding=24, content=ft.Column([ft.Text("Painel Supremo", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), ft.Text("Para dar acesso a várias Orgs, separe com vírgulas.", size=12, color=C_TEXT_SEC), search_input, ft.Container(height=8), ft.Container(content=users_list_ui, expand=True)]))

    # ==========================================
    # LÓGICA DE NAVEGAÇÃO DINÂMICA
    # ==========================================
    content_area = ft.Container(expand=True)
    TABS_MAP = {"Bladers": build_home_view, "Treino": build_training_view, "Combate": build_quick_match_view, "Torneio": build_tournament_view, "Histórico": build_history_view, "Admin": build_admin_view, "Perfil": build_profile_view}

    def change_tab_programmatic(index):
        if not bottom_nav.destinations: return
        selected_label = bottom_nav.destinations[index].label
        content_area.content = None; page.update()
        if build_func := TABS_MAP.get(selected_label): content_area.content = build_func()
        page.update()

    def nav_to_tab(tab_label):
        for i, dest in enumerate(bottom_nav.destinations):
            if dest.label == tab_label: bottom_nav.selected_index = i; bottom_nav.update(); change_tab_programmatic(i); break

    def change_tab(e): 
        try: new_idx = int(e.data) 
        except: new_idx = e.control.selected_index
        bottom_nav.selected_index = new_idx; bottom_nav.update(); change_tab_programmatic(new_idx)
    
    def refresh_current_tab(): 
        if bottom_nav.visible and bottom_nav.destinations: change_tab_programmatic(bottom_nav.selected_index)

    def start_main_app():
        login_container.visible = False; main_app_container.visible = True; bottom_nav.visible = True
        app_state["admin_viewing_org"] = "admin" 
        update_appbar()
        role = current_user().get("role", "basic")
        dests = []
        
        # 👑 A NOVA LÓGICA DE ABAS BASEADA NAS LICENÇAS COMPRADAS
        if role in ["admin_max", "pro", "organizador", "judge"]:
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.PEOPLE_OUTLINE, label="Bladers"))
            
        if role in ["admin_max", "pro", "treinador"]:
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.FITNESS_CENTER_OUTLINED, label="Treino"))
            
        # Todos têm acesso ao Combate Casual
        dests.append(ft.NavigationBarDestination(icon=ft.Icons.FLASH_ON_OUTLINED, label="Combate"))
        
        if role in ["admin_max", "pro", "organizador", "judge"]:
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.EMOJI_EVENTS_OUTLINED, label="Torneio"))
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.HISTORY_OUTLINED, label="Histórico"))
            
        if role == "admin_max": 
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED, label="Admin"))
            
        dests.append(ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINE, label="Perfil"))
            
        bottom_nav.destinations = dests; bottom_nav.selected_index = 0; bottom_nav.on_change = change_tab
        page.update(); change_tab_programmatic(0)

    main_app_container.content = ft.Column([content_area], expand=True)
    page.add(login_container, main_app_container, bottom_nav)

    # 👑 O CÃO DE GUARDA (VERIFICA O TOKEN DE SESSÃO)
    def auto_sync_loop():
        global is_syncing
        while True:
            time.sleep(5) 
            if is_syncing or login_container.visible: continue 
            try:
                res = requests.get(FIREBASE_URL, timeout=5)
                if res.status_code == 200:
                    nuvem = res.json()
                    if nuvem:
                        with db_lock:
                            # VERIFICAÇÃO DE SEGURANÇA: Fui logado em outro lugar?
                            if app_state.get("current_user"):
                                u_name = app_state["current_user"]["username"]
                                cloud_users = nuvem.get("users", {})
                                if u_name in cloud_users:
                                    cloud_token = cloud_users[u_name].get("session_token")
                                    local_token = app_state.get("session_token")
                                    if cloud_token and local_token and cloud_token != local_token:
                                        # Fui derrubado! Alguém conectou na minha conta.
                                        do_logout(force_msg=True)
                                        continue

                            local_ts = app_data.get("last_updated", 0); remote_ts = nuvem.get("last_updated", 0)
                            if remote_ts > local_ts:
                                app_data.clear(); app_data.update(nuvem)
                                if "users" not in app_data: app_data["users"] = {}
                                if "training_history" not in app_data: app_data["training_history"] = []
                                if "tournaments" not in app_data: app_data["tournaments"] = {}
                                if "active_matches" not in app_data: app_data["active_matches"] = {}
                                if "last_updated" not in app_data: app_data["last_updated"] = 0
                                needs_refresh = True
                            else: needs_refresh = False
                        if needs_refresh and bottom_nav.destinations:
                            current_label = bottom_nav.destinations[bottom_nav.selected_index].label
                            if current_label not in ["Bladers", "Treino", "Combate", "Admin"]: refresh_current_tab()
            except Exception: pass 
    threading.Thread(target=auto_sync_loop, daemon=True).start()

ft.run(main)
