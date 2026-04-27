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
from functools import cmp_to_key

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
# 2. MOTOR DA NUVEM
# ==========================================
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

# --- FUNÇÕES GLOBAIS DE BANCO DE DADOS ---
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
# 3. SISTEMA DE PERFIS
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
    return ft.Container(content=ft.Column([ft.Text("IDEALIZADO POR: GUILHERME CARUSO", size=10, color=C_TEXT_SEC, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER), ft.Text("DESENVOLVIDO POR: GUILHERME MONÇÃO", size=10, color=C_TEXT_SEC, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER), margin=ft.margin.only(top=24, bottom=12), width=float("inf"), alignment=ft.Alignment(0, 0))

# ==========================================
# 5. O APLICATIVO PRINCIPAL
# ==========================================
def main(page: ft.Page):
    page.title = "Beyblade X System"; page.theme_mode = ft.ThemeMode.DARK; page.bgcolor = C_BG; page.padding = 0
    page.fonts = {"Inter": "https://raw.githubusercontent.com/rsms/inter/master/docs/font-files/Inter-Regular.woff2"}
    page.theme = ft.Theme(font_family="Inter")

    app_state = {
        "current_user": None, "admin_viewing_org": "admin",
        "user_orgs": [], "active_org": "default", "session_token": None
    }

    def current_user(): return app_state["current_user"]
    def is_admin_max(): u = current_user(); return u and u["role"] == "admin_max"
    def is_pro(): u = current_user(); return u and u["role"] in ["admin_max", "pro"]
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
        app_state["current_user"] = None; app_state["admin_viewing_org"] = "admin"; app_state["session_token"] = None
        main_app_container.visible = False; bottom_nav.visible = False; login_container.visible = True
        login_container.content = build_auth_view(True)
        if force_msg: page.snack_bar = ft.SnackBar(ft.Text("Sua conta foi conectada em outro dispositivo!"), bgcolor=C_ERROR); page.snack_bar.open = True
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
        res = m_data.get("result", {}); b1_name = b_map.get(m_data.get("blader1"), "W.O. / A Definir"); b2_name = b_map.get(m_data.get("blader2"), "W.O. / A Definir")
        f1 = res.get("blader1Result", {}).get("finishes", {}); f2 = res.get("blader2Result", {}).get("finishes", {})
        def f_row(label, key, color): return ft.Row([ft.Text(str(f1.get(key, 0)), color=color, weight=ft.FontWeight.BOLD, size=16, width=30, text_align="center"), ft.Text(label, color=C_TEXT_SEC, expand=True, text_align="center", size=13), ft.Text(str(f2.get(key, 0)), color=color, weight=ft.FontWeight.BOLD, size=16, width=30, text_align="center")])
        dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), content_padding=24, title=ft.Text("Raio-X da Partida", color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, size=18, text_align="center"), content=ft.Column([ft.Row([ft.Text(b1_name, weight=ft.FontWeight.W_600, color=C_TEXT_PRI, expand=True, text_align="center", size=14), ft.Text("VS", size=11, color=C_TEXT_SEC), ft.Text(b2_name, weight=ft.FontWeight.W_600, color=C_TEXT_PRI, expand=True, text_align="center", size=14)]), ft.Divider(color=C_BORDER, height=20), f_row("XTREME", "xtreme", C_XTREME), f_row("BURST", "burst", C_BURST), f_row("OVER", "over", C_OVER), f_row("SPIN", "spin", C_SPIN), f_row("FLAG", "flag", C_FLAG), ft.Divider(color=C_BORDER, height=20), ft.Row([ft.Text(str(res.get("blader1Result", {}).get("totalPoints", 0)), size=24, color=C_PRIMARY, weight=ft.FontWeight.BOLD, width=30, text_align="center"), ft.Text("PONTOS GERAIS", color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, expand=True, text_align="center", size=12), ft.Text(str(res.get("blader2Result", {}).get("totalPoints", 0)), size=24, color=C_PRIMARY, weight=ft.FontWeight.BOLD, width=30, text_align="center")])], tight=True), actions=[SecondaryBtn("Fechar", lambda _: hide_dialog(dlg))])
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
            safe_cloud_sync(); db_users = get_users(); user_data = None
            
            if is_login:
                if u in db_users and (db_users[u].get("password") == p or (u in HARDCODED_USERS and HARDCODED_USERS[u]["password"] == p)):
                    user_data = db_users[u]
                    if user_data.get("password") != p: user_data["password"] = p; save_users(db_users)
                elif u in HARDCODED_USERS and HARDCODED_USERS[u]["password"] == p:
                    user_data = HARDCODED_USERS[u].copy()
                    db_users[u] = user_data
                    save_users(db_users)
                
                if user_data:
                    new_token = str(int(time.time() * 1000)) + str(random.randint(1000, 9999))
                    user_data["session_token"] = new_token; db_users[u] = user_data; save_users(db_users)
                    
                    org_str = user_data.get("org", u)
                    user_orgs = [o.strip() for o in org_str.split(",") if o.strip()]
                    app_state["current_user"] = {"username": u, "role": user_data.get("role", "basic"), "org": org_str}
                    app_state["user_orgs"] = user_orgs
                    app_state["active_org"] = user_orgs[0] if user_orgs else u
                    app_state["session_token"] = new_token
                    start_main_app(); return
                page.snack_bar = ft.SnackBar(ft.Text("Login inválido!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update()
            else:
                if u in HARDCODED_USERS or u in db_users: page.snack_bar = ft.SnackBar(ft.Text("Usuário já existe!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return
                new_token = str(int(time.time() * 1000)) + str(random.randint(1000, 9999))
                db_users[u] = {"password": p, "email": e_input.value.strip(), "role": "basic", "org": u, "session_token": new_token}
                save_users(db_users)
                app_state["current_user"] = {"username": u, "role": "basic", "org": u}; app_state["user_orgs"] = [u]; app_state["active_org"] = u; app_state["session_token"] = new_token
                start_main_app()

        return ft.Column([ft.Container(height=40), ft.Icon(ft.Icons.SECURITY, size=64, color=C_PRIMARY), ft.Text("Bem-vindo" if is_login else "Criar Conta", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), ft.Text("Motor oficial de torneios e treinos.", size=14, color=C_TEXT_SEC), ft.Container(height=20), u_input, e_input, p_input, PrimaryBtn("Entrar" if is_login else "Cadastrar", do_auth, width=float("inf")), ft.TextButton("Não tem conta? Cadastre-se" if is_login else "Já tem conta? Faça Login", on_click=lambda _: [setattr(login_container, 'content', build_auth_view(not is_login)), page.update()], style=ft.ButtonStyle(color=C_TEXT_SEC)), ft.Container(expand=True), CreditsFooter()], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    login_container.content = build_auth_view(True)

    main_app_container = ft.Container(expand=True, visible=False)
    bottom_nav = ft.NavigationBar(bgcolor=C_BG, indicator_color=C_SURFACE_SEC, visible=False, destinations=[ft.NavigationBarDestination(icon=ft.Icons.HOURGLASS_EMPTY, label="1"), ft.NavigationBarDestination(icon=ft.Icons.HOURGLASS_EMPTY, label="2")])
    
    history_state = {"active_tourn": None, "sub_tab": "tabelas"}
    home_state = {"sub_tab": "cadastro", "selected_ids": [], "temp_name": ""}
    tourn_state = {"sub_tab": None, "active_match": None, "match_state": {}}
    training_state = {"sub_tab": "setup", "match_data": None, "p1_score": 0, "p2_score": 0, "p1_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "p2_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "match_ended": False}

    # --- TELA 0: PERFIL ---
    def build_profile_view():
        user_orgs = app_state.get("user_orgs", [get_current_org()]); col_elements = [ft.Container(height=50), ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color=C_TEXT_SEC), ft.Text(f"Olá, {get_username()}!", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI)]
        if len(user_orgs) > 1 and not is_admin_max():
            dd_org = ft.Dropdown(label="Selecione o Ambiente", value=get_current_org(), options=[ft.dropdown.Option(key=o, text=o) for o in user_orgs], bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12, width=200)
            def apply_org(e):
                if dd_org.value:
                    app_state["active_org"] = str(dd_org.value); update_appbar(); tourn_state["sub_tab"] = None; tourn_state["active_match"] = None; history_state["active_tourn"] = None; history_state["sub_tab"] = "tabelas"; home_state["selected_ids"].clear()
                    page.snack_bar = ft.SnackBar(ft.Text(f"Ambiente alterado para {dd_org.value.upper()}!"), bgcolor=C_SUCCESS); page.snack_bar.open = True; refresh_current_tab()
            col_elements.extend([ft.Container(height=10), ft.Row([dd_org, PrimaryBtn("Confirmar", apply_org, width=120)], alignment=ft.MainAxisAlignment.CENTER)])
        else: col_elements.append(ft.Text(f"Ambiente: {get_current_org().upper()}", color=C_PRIMARY, size=14, weight=ft.FontWeight.BOLD))
            
        role_label = {"basic": "Licença Básica", "treinador": "Licença Treinador", "organizador": "Licença Organizador", "pro": "Licença PRO", "admin_max": "Licença Admin Suprema", "judge": "Licença Organizador"}.get(current_user().get("role", "basic"), "Licença Básica")
        col_elements.extend([ft.Container(height=10), Badge(role_label, C_PRIMARY), ft.Container(height=20), ft.Text("Sua conta permite gerenciar e visualizar dados exclusivos do seu ambiente atual de acordo com seu plano.", color=C_TEXT_SEC, text_align="center"), ft.Container(expand=True), ft.Divider(color=C_BORDER), CreditsFooter()])
        return ft.Container(padding=24, content=ft.Column(col_elements, horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO))

    # --- TELA 1: TREINO ISOLADO ---
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
                page.update(); 
                if training_state["p1_score"] >= PTS_WIN_TARGET or training_state["p2_score"] >= PTS_WIN_TARGET: process_win()

            def action_col(p): return ft.Column([PrimaryBtn(f"XTREME (+{PTS_MAP['xtreme']})", lambda _: add_points(p, PTS_MAP['xtreme'], "xtreme"), width=145, height=44, color=C_PRIMARY), SecondaryBtn(f"BURST (+{PTS_MAP['burst']})", lambda _: add_points(p, PTS_MAP['burst'], "burst"), width=145, height=44), SecondaryBtn(f"OVER (+{PTS_MAP['over']})", lambda _: add_points(p, PTS_MAP['over'], "over"), width=145, height=44), SecondaryBtn(f"SPIN (+{PTS_MAP['spin']})", lambda _: add_points(p, PTS_MAP['spin'], "spin"), width=145, height=44), SecondaryBtn(f"FLAG (+{PTS_MAP['flag']})", lambda _: add_points(p, PTS_MAP['flag'], "flag"), width=145, height=44)], spacing=12, alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

            return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Row([IconButton(ft.Icons.ARROW_BACK, lambda _: [training_state.update({"sub_tab": "setup"}), refresh_current_tab()]), ft.Text(f"TREINO: {m_data['treino_nome'].upper()}", color=C_TEXT_PRI, weight=ft.FontWeight.W_600, size=13, expand=True, text_align="center"), ft.Container(width=42)]), bgcolor=C_SUCCESS, padding=12, width=float("inf")), ft.Container(padding=24, expand=True, content=ft.Column([ft.Row([ft.Column([p1_display, score_p1, action_col(1)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER), ft.Container(width=1, bgcolor=C_BORDER, height=300, margin=ft.margin.symmetric(horizontal=8)), ft.Column([p2_display, score_p2, action_col(2)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START), ft.Container(expand=True), SecondaryBtn("Resetar", lambda _: [training_state.update({"p1_score": 0, "p2_score": 0, "p1_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "p2_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "match_ended": False}), setattr(score_p1, 'value', '0'), setattr(score_p2, 'value', '0'), page.update()], width=float("inf"), icon=ft.Icons.REFRESH)]))]))
        else:
            hist = _get_training_history()
            def get_recent(key):
                res = []
                for h in hist:
                    if h.get(key) and h.get(key) not in res: res.append(h.get(key))
                    if len(res) >= 6: break
                return res

            recents_nome = get_recent("NOME_TREINO"); recents_test = get_recent("COMBO_TESTADO"); recents_adv = get_recent("COMBO_ADVERSARIO")

            treino_nome_input = ft.TextField(label="Nome do Treino", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            combo_test_input = ft.TextField(label="Seu Combo", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            combo_adv_input = ft.TextField(label="Combo do Adversário", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            lado_dropdown = ft.Dropdown(label="Lado da Arena", options=[ft.dropdown.Option(key="B Side", text="B Side"), ft.dropdown.Option(key="X Side", text="X Side")], bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)

            def make_suggs(vals, target_input):
                if not vals: return ft.Container()
                def apply_sugg(e): target_input.value = e.control.data; page.update()
                chips = [ft.Container(content=ft.Text(v, size=11, color=C_PRIMARY, weight=ft.FontWeight.W_600), padding=ft.padding.symmetric(horizontal=10, vertical=4), bgcolor=f"{C_PRIMARY}15", border_radius=12, border=ft.border.all(1, f"{C_PRIMARY}40"), on_click=apply_sugg, data=v) for v in vals]
                return ft.Row(chips, wrap=True, spacing=6, run_spacing=6)

            def start_training(e):
                if not treino_nome_input.value or not combo_test_input.value or not combo_adv_input.value or not lado_dropdown.value: return
                training_state.update({"match_data": {"treino_nome": treino_nome_input.value.strip(), "combo_testado": combo_test_input.value.strip(), "combo_adversario": combo_adv_input.value.strip(), "lado_arena": lado_dropdown.value}, "p1_score": 0, "p2_score": 0, "p1_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "p2_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "match_ended": False, "sub_tab": "combat"}); refresh_current_tab()
            
            hist_list = ft.ListView(expand=True, spacing=10)
            for h in hist:
                res_color = C_SUCCESS if h.get("RESULTADO") == "Vitória" else C_ERROR
                hist_list.controls.append(AppCard(ft.Column([ft.Row([ft.Text(h.get("DATA", ""), color=C_TEXT_SEC, size=12), ft.Text(h.get("RESULTADO", ""), color=res_color, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Text(f"Treino: {h.get('NOME_TREINO', 'N/A')}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=14), ft.Text(f"Meu: {h.get('COMBO_TESTADO')}  VS  Adv: {h.get('COMBO_ADVERSARIO')}", color=C_TEXT_PRI, weight=ft.FontWeight.W_500), ft.Text(f"Placar: {h.get('PLACAR')} | Lado: {h.get('LADO_ARENA')}", color=C_TEXT_SEC, size=13)], spacing=4), padding=12))
            
            return ft.Container(padding=24, content=ft.Column([
                ft.Text("Laboratório de Combos", size=24, weight=ft.FontWeight.BOLD, color=C_PRIMARY), 
                treino_nome_input, make_suggs(recents_nome, treino_nome_input), ft.Container(height=4),
                combo_test_input, make_suggs(recents_test, combo_test_input), ft.Container(height=4),
                combo_adv_input, make_suggs(recents_adv, combo_adv_input), ft.Container(height=4),
                lado_dropdown, 
                PrimaryBtn("Arena de Treino", start_training, width=float("inf"), icon=ft.Icons.PLAY_ARROW), 
                ft.Divider(color=C_BORDER, height=20), 
                ft.Text("Histórico Privado", size=18, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), 
                ft.Container(content=hist_list, expand=True)
            ], scroll=ft.ScrollMode.AUTO))

    # --- TELA 2: BLADERS ---
    def build_home_view():
        if not has_torneio_access(): return ft.Container(content=ft.Text("Acesso Restrito.", color=C_ERROR), padding=24)
        bladers = _get_bladers()
        blader_input = ft.TextField(value=home_state["temp_name"], hint_text="Nome do Blader...", expand=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, text_size=14, border_radius=12)
        blader_input.on_change = lambda e: home_state.update({"temp_name": e.control.value})
        
        def add_blader(e):
            if blader_input.value.strip():
                safe_cloud_sync(); b_list = _get_bladers(); b_list.append({"id": str(int(time.time()*1000)), "name": blader_input.value.strip()})
                _save_bladers(b_list); home_state["temp_name"] = ""; refresh_current_tab()

        def confirm_remove_blader(b_id):
            safe_cloud_sync()
            if b_id in home_state["selected_ids"]: home_state["selected_ids"].remove(b_id)
            _save_bladers([b for b in _get_bladers() if b["id"] != b_id]); refresh_current_tab()

        bladers_list_ui = ft.ListView(expand=True, spacing=12)
        for b in bladers: bladers_list_ui.controls.append(AppCard(ft.Row([ft.Text(b["name"], weight=ft.FontWeight.W_500, color=C_TEXT_PRI, size=15, expand=True), IconButton(ft.Icons.DELETE_OUTLINE, lambda e, bid=b["id"]: confirm_remove_blader(bid), color=C_ERROR)]), padding=12))

        view_cadastro = ft.Column([ft.Row([blader_input, PrimaryBtn("Add", add_blader, width=80, height=52)]), ft.Container(height=12), ft.Container(content=bladers_list_ui, expand=True)])
        selection_list_ui = ft.ListView(expand=True, spacing=12)
        
        def toggle_selection(e, b_id):
            if e.control.value: home_state["selected_ids"].append(b_id) if b_id not in home_state["selected_ids"] else None
            else: home_state["selected_ids"].remove(b_id) if b_id in home_state["selected_ids"] else None
            btn_criar.content.controls[1].value = f"Avançar para Passo 2 ({len(home_state['selected_ids'])})"; page.update()

        for b in bladers: selection_list_ui.controls.append(AppCard(ft.Checkbox(label=b["name"], value=(b["id"] in home_state["selected_ids"]), on_change=lambda e, bid=b["id"]: toggle_selection(e, bid), fill_color=C_PRIMARY, check_color=C_BG, label_style=ft.TextStyle(color=C_TEXT_PRI, size=15, weight=ft.FontWeight.W_500)), padding=8))

        view_config_container = ft.Container(expand=True)

        def open_config_view(e):
            selected_bladers = [b for b in _get_bladers() if b["id"] in home_state["selected_ids"]]; total_b = len(selected_bladers)
            if total_b < 2: page.snack_bar = ft.SnackBar(ft.Text("Selecione pelo menos 2 Bladers!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return 
            config_state = {"num_groups": 1, "sizes": [total_b]}
            dist_col = ft.Column(spacing=4); sum_text = ft.Text("", color=C_TEXT_SEC, size=13, weight=ft.FontWeight.W_600)

            def update_dist_ui():
                dist_col.controls.clear(); current_sum = sum(config_state["sizes"])
                for i in range(config_state["num_groups"]):
                    def make_btn(idx, delta): return ft.IconButton(ft.Icons.ADD if delta>0 else ft.Icons.REMOVE, on_click=lambda e: (config_state["sizes"].__setitem__(idx, config_state["sizes"][idx] + delta) or update_dist_ui()) if config_state["sizes"][idx] + delta >= 1 else None, icon_color=C_TEXT_PRI, bgcolor=C_SURFACE_SEC, width=35, height=35)
                    dist_col.controls.append(ft.Row([ft.Text(f"Grupo {chr(65+i)}", color=C_TEXT_PRI, width=65, size=14, weight=ft.FontWeight.BOLD), make_btn(i, -1), ft.Text(str(config_state["sizes"][i]), color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, width=20, text_align="center"), make_btn(i, 1)], alignment=ft.MainAxisAlignment.CENTER, spacing=12))
                diff = total_b - current_sum
                if diff == 0: sum_text.value = f"✅ Perfeito: {total_b} vagas"; sum_text.color = C_SUCCESS
                elif diff > 0: sum_text.value = f"⚠️ Faltam {diff} vagas"; sum_text.color = C_ERROR
                else: sum_text.value = f"⚠️ Sobrando {-diff} vagas"; sum_text.color = C_ERROR
                page.update() 

            def on_group_count_change(e=None):
                new_count = int(dd_groups.value); config_state["num_groups"] = new_count
                base = total_b // new_count; rem = total_b % new_count
                config_state["sizes"] = [base + (1 if i < rem else 0) for i in range(new_count)]; update_dist_ui()

            dd_groups = ft.Dropdown(options=[ft.dropdown.Option(key=str(i), text=f"{i} Grupo(s)") for i in range(1, max(1, total_b // 2) + 1)], value="1", expand=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            dd_groups.on_change = on_group_count_change
            
            dd_advances = ft.Dropdown(options=[ft.dropdown.Option(key=str(i), text=f"{i} por Grupo") for i in range(1, 5)], value="2", expand=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            name_input = ft.TextField(label="Nome do Torneio", value=f"Torneio {datetime.now().strftime('%d/%m')}", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)

            def confirm_create(e):
                if sum(config_state["sizes"]) != total_b: return
                safe_cloud_sync(); groups = []; shuffled = list(selected_bladers); random.shuffle(shuffled); b_idx = 0; judges_pool = ["juiz_1", "juiz_2"] 
                for i, size in enumerate(config_state["sizes"]):
                    gb = shuffled[b_idx : b_idx + size]; b_idx += size
                    matches = [{"id": f"{i}-{j}-{k}-{int(time.time()*1000)}", "groupId": f"group-{i}", "blader1": gb[j]["id"], "blader2": gb[k]["id"], "completed": False, "judge": judges_pool[i % 2]} for j in range(len(gb)) for k in range(j + 1, len(gb))]
                    groups.append({"id": f"group-{i}", "name": f"Grupo {chr(65 + i)}", "bladerIds": [b["id"] for b in gb], "matches": matches})
                _save_tournament({"id": str(int(time.time())), "name": name_input.value.strip(), "date": datetime.now().strftime('%d/%m/%Y %H:%M'), "groups": groups, "status": "groups", "knockout": [], "participants": {b["id"]: b["name"] for b in selected_bladers}, "advancing_per_group": int(dd_advances.value)})
                home_state["selected_ids"].clear(); switch_home_tab("selecao"); tourn_state["sub_tab"] = "grupos"; nav_to_tab("Torneio") 
            
            update_dist_ui()
            view_config_container.content = ft.Column([ft.Text("Passo 2: Definir Grupos", size=14, color=C_TEXT_SEC), AppCard(ft.Column([name_input, ft.Row([dd_groups, ft.IconButton(ft.Icons.SYNC, on_click=on_group_count_change)]), dd_advances, dist_col, ft.Container(content=sum_text, alignment=ft.Alignment(0,0))], spacing=16)), ft.Row([SecondaryBtn("Voltar", lambda _: switch_home_tab("selecao"), expand=True), PrimaryBtn("Criar", confirm_create, expand=True)], spacing=12)], scroll=ft.ScrollMode.AUTO)
            switch_home_tab("config")

        btn_criar = PrimaryBtn(f"Avançar para Passo 2 ({len(home_state['selected_ids'])})", open_config_view, width=float("inf"), icon=ft.Icons.ROCKET_LAUNCH)
        view_selecao = ft.Column([ft.Text("Passo 1: Marque os Bladers", size=14, color=C_TEXT_SEC), ft.Container(content=selection_list_ui, expand=True), btn_criar])
        tab_nav_container = ft.Container(); content_switcher = ft.Container(expand=True)

        def switch_home_tab(tab_name):
            home_state["sub_tab"] = tab_name
            tabs = [ft.Container(content=ft.Text("Banco Geral", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if tab_name == "cadastro" else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if tab_name == "cadastro" else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_home_tab("cadastro")), ft.Container(content=ft.Text("Criar Torneio", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if tab_name in ["selecao", "config"] else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if tab_name in ["selecao", "config"] else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_home_tab("selecao"))]
            tab_nav_container.content = ft.Container(content=ft.Row(tabs, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BORDER), border_radius=10, padding=4, margin=ft.margin.only(bottom=16))
            content_switcher.content = view_cadastro if tab_name == "cadastro" else (view_selecao if tab_name == "selecao" else view_config_container); page.update()

        switch_home_tab(home_state["sub_tab"])
        return ft.Container(padding=24, content=ft.Column([ft.Text("Gestão de Bladers", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), tab_nav_container, content_switcher]))

    # --- TELA 3: COMBATE CASUAL ---
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

    # --- TELA 4: TORNEIO ---
    def build_tournament_view():
        if not has_torneio_access(): return ft.Container(content=ft.Text("Acesso Restrito.", color=C_ERROR), padding=24)
        if is_admin_max() and app_state.get("admin_viewing_org") == "admin":
            safe_cloud_sync(); tourns = app_data.get("tournaments", {}); hub_ui = ft.ListView(expand=True, spacing=12)
            for org_id, t_data in tourns.items():
                def enter_org(e, oid=org_id): app_state["admin_viewing_org"] = oid; update_appbar(); refresh_current_tab()
                hub_ui.controls.append(AppCard(ft.Row([ft.Column([ft.Text(f"AMBIENTE: {org_id.upper()}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=12), ft.Text(t_data.get("name", "Torneio"), color=C_TEXT_PRI, size=18, weight=ft.FontWeight.W_600)], expand=True), PrimaryBtn("Inspecionar", enter_org, icon=ft.Icons.VISIBILITY)])))
            return ft.Container(padding=24, content=ft.Column([ft.Text("Monitoramento Global", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), ft.Container(content=hub_ui, expand=True)]))

        tourn = _get_tournament()
        if not tourn: return ft.Container(content=ft.Column([ft.Icon(ft.Icons.EMOJI_EVENTS_OUTLINED, size=64, color=C_BORDER), ft.Text("Nenhum torneio em andamento.", color=C_TEXT_SEC, size=16)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True, alignment=ft.Alignment(0,0))
        bladers_map = get_snapshot_map(tourn)
        if tourn_state["sub_tab"] is None or (tourn_state["sub_tab"] == "matamata" and tourn.get("status") != "knockout"): tourn_state["sub_tab"] = "matamata" if tourn.get("status") == "knockout" else "grupos"
            
        if tourn_state["sub_tab"] == "combat":
            m_data = tourn_state["active_match"]; state = tourn_state["match_state"]
            is_md3 = m_data.get("is_md3", False)
            
            score_p1 = ft.Text(str(state["p1_score"]), size=64, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI)
            score_p2 = ft.Text(str(state["p2_score"]), size=64, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI)
            
            sets_p1 = ft.Text(f"Sets: {state.get('p1_sets', 0)}", size=18, color=C_PRIMARY, weight=ft.FontWeight.BOLD) if is_md3 else ft.Container()
            sets_p2 = ft.Text(f"Sets: {state.get('p2_sets', 0)}", size=18, color=C_PRIMARY, weight=ft.FontWeight.BOLD) if is_md3 else ft.Container()

            def process_win():
                if state["match_ended"]: return 
                state["match_ended"] = True
                
                if is_md3:
                    w_id = m_data["b1_id"] if state.get("p1_sets", 0) > state.get("p2_sets", 0) else m_data["b2_id"]
                else:
                    w_id = m_data["b1_id"] if state["p1_score"] > state["p2_score"] else m_data["b2_id"]
                
                def finish_match(e):
                    hide_dialog(dlg)
                    def async_save_match():
                        safe_cloud_sync(); fresh_t = _get_tournament()
                        loser_id = m_data["b2_id"] if w_id == m_data["b1_id"] else m_data["b1_id"]
                        
                        def get_total_pts(f): return f.get("xtreme",0)*3 + f.get("burst",0)*2 + f.get("over",0)*2 + f.get("spin",0)*1 + f.get("flag",0)*1
                        
                        final_res = {
                            "blader1Result": {"bladerId": m_data["b1_id"], "totalPoints": get_total_pts(state["p1_finishes"]), "finishes": state["p1_finishes"]}, 
                            "blader2Result": {"bladerId": m_data["b2_id"], "totalPoints": get_total_pts(state["p2_finishes"]), "finishes": state["p2_finishes"]}, 
                            "winner": w_id
                        }

                        if m_data["is_knockout"]:
                            target_w, target_l = None, None
                            for r in fresh_t.get("knockout", []):
                                for m in r.get("matches", []):
                                    if m.get("id") == m_data["match_id"]:
                                        m["completed"] = True
                                        m["result"] = final_res
                                        target_w = m.get("target_w"); target_l = m.get("target_l")
                                        
                                        if m.get("id") == "gf":
                                            losses = 0
                                            for rx in fresh_t.get("knockout", []):
                                                for mx in rx.get("matches", []):
                                                    if mx.get("completed") and mx.get("id") != "gf":
                                                        res_x = mx.get("result", {})
                                                        if res_x.get("blader1Result", {}).get("bladerId") == w_id and res_x.get("winner") != w_id: losses += 1
                                                        if res_x.get("blader2Result", {}).get("bladerId") == w_id and res_x.get("winner") != w_id: losses += 1
                                            
                                            if losses > 0 and not fresh_t.get("gf_reset_created"):
                                                reset_match = {"id": "gf_reset", "name": "Grande Final (Reset)", "blader1": m.get("blader1"), "blader2": m.get("blader2"), "completed": False, "judge": m.get("judge"), "is_md3": False}
                                                fresh_t["knockout"].append({"name": "Grande Final - Bracket Reset", "matches": [reset_match]})
                                                fresh_t["gf_reset_created"] = True
                                        break
                            
                            for rr in fresh_t.get("knockout", []):
                                for mm in rr.get("matches", []):
                                    if target_w and mm.get("id") == target_w:
                                        if mm.get("blader1") is None: mm["blader1"] = w_id
                                        elif mm.get("blader2") is None: mm["blader2"] = w_id
                                    if target_l and mm.get("id") == target_l:
                                        if mm.get("blader1") is None: mm["blader1"] = loser_id
                                        elif mm.get("blader2") is None: mm["blader2"] = loser_id
                            
                            changed = True
                            while changed:
                                changed = False
                                for r in fresh_t.get("knockout", []):
                                    for m in r.get("matches", []):
                                        if not m.get("completed") and (m.get("blader1") == "BYE" or m.get("blader2") == "BYE"):
                                            if m.get("blader1") and m.get("blader2"):
                                                rw_id = m.get("blader1") if m.get("blader2") == "BYE" else m.get("blader2")
                                                m["completed"] = True; m["result"] = {"winner": rw_id}
                                                tw = m.get("target_w"); tl = m.get("target_l")
                                                for rx in fresh_t.get("knockout", []):
                                                    for mx in rx.get("matches", []):
                                                        if tw and mx.get("id") == tw:
                                                            if mx.get("blader1") is None: mx["blader1"] = rw_id
                                                            elif mx.get("blader2") is None: mx["blader2"] = rw_id
                                                        if tl and mx.get("id") == tl:
                                                            if mx.get("blader1") is None: mx["blader1"] = "BYE"
                                                            elif mx.get("blader2") is None: mx["blader2"] = "BYE"
                                                changed = True
                        else:
                            for g in fresh_t.get("groups", []):
                                if g.get("id") == m_data["group_id"]:
                                    for m in g.get("matches", []):
                                        if m.get("id") == m_data["match_id"]:
                                            m["completed"] = True
                                            m["result"] = final_res
                        _save_tournament(fresh_t); tourn_state["sub_tab"] = "partidas"; tourn_state["active_match"] = None; refresh_current_tab() 
                    threading.Thread(target=async_save_match, daemon=True).start()

                dlg = ft.AlertDialog(modal=True, bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text(f"Vitória Registrada!", color=C_SUCCESS), actions=[PrimaryBtn("Confirmar", finish_match)])
                show_dialog(dlg)

            def add_points(player, pts, t_finish):
                if state["match_ended"]: return 
                if player == 1: state["p1_score"] += pts; state["p1_finishes"][t_finish] += 1; score_p1.value = str(state["p1_score"])
                else: state["p2_score"] += pts; state["p2_finishes"][t_finish] += 1; score_p2.value = str(state["p2_score"])
                page.update(); 
                
                if state["p1_score"] >= PTS_WIN_TARGET or state["p2_score"] >= PTS_WIN_TARGET:
                    if is_md3:
                        if state["p1_score"] >= PTS_WIN_TARGET: state["p1_sets"] = state.get("p1_sets", 0) + 1
                        else: state["p2_sets"] = state.get("p2_sets", 0) + 1
                        
                        if state.get("p1_sets", 0) >= 2 or state.get("p2_sets", 0) >= 2:
                            process_win()
                        else:
                            state["p1_score"] = 0; state["p2_score"] = 0
                            score_p1.value = "0"; score_p2.value = "0"
                            sets_p1.value = f"Sets: {state['p1_sets']}"; sets_p2.value = f"Sets: {state['p2_sets']}"
                            page.snack_bar = ft.SnackBar(ft.Text("🏁 Fim do Set! Iniciando próximo jogo..."), bgcolor=C_SUCCESS)
                            page.snack_bar.open = True
                            page.update()
                    else:
                        process_win()

            def action_col(p): return ft.Column([PrimaryBtn(f"XTREME (+3)", lambda _: add_points(p, 3, "xtreme"), width=145, height=44, color=C_PRIMARY), SecondaryBtn(f"BURST (+2)", lambda _: add_points(p, 2, "burst"), width=145, height=44), SecondaryBtn(f"OVER (+2)", lambda _: add_points(p, 2, "over"), width=145, height=44), SecondaryBtn(f"SPIN (+1)", lambda _: add_points(p, 1, "spin"), width=145, height=44), SecondaryBtn(f"FLAG (+{PTS_MAP['flag']})", lambda _: add_points(p, PTS_MAP['flag'], "flag"), width=145, height=44)], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

            return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Row([IconButton(ft.Icons.ARROW_BACK, lambda _: [tourn_state.update({"sub_tab": "partidas", "active_match": None}), refresh_current_tab()]), ft.Text(f"PARTIDA OFICIAL {'(MD3)' if is_md3 else ''}", color=C_TEXT_PRI, weight=ft.FontWeight.W_600, size=13, expand=True, text_align="center"), ft.Container(width=42)]), bgcolor=C_ERROR if m_data["is_knockout"] else C_PRIMARY, padding=12), ft.Container(padding=24, expand=True, content=ft.Column([ft.Row([ft.Column([ft.Text(m_data["b1_name"]), sets_p1, score_p1, action_col(1)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER), ft.Container(width=1, bgcolor=C_BORDER, height=300), ft.Column([ft.Text(m_data["b2_name"]), sets_p2, score_p2, action_col(2)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)]), ft.Container(expand=True)]))]))
            
        else:
            def open_admin_panel(e):
                safe_cloud_sync(); fresh_tourn = _get_tournament()
                in_tourn = [{"id": k, "name": v} for k, v in fresh_tourn.get("participants", {}).items()]
                out_tourn = [b for b in _get_bladers() if b["id"] not in fresh_tourn.get("participants", {})]

                dd_sai = ft.Dropdown(options=[ft.dropdown.Option(key=b["id"], text=b["name"]) for b in in_tourn], label="Quem saiu?", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI)
                dd_entra = ft.Dropdown(options=[ft.dropdown.Option(key=b["id"], text=b["name"]) for b in out_tourn], label="Quem entra?", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI)
                
                def perform_swap(e):
                    if not dd_sai.value or not dd_entra.value: return
                    id_sai, id_entra = dd_sai.value, dd_entra.value; nome_entra = next((b["name"] for b in out_tourn if b["id"] == id_entra), "Reserva")
                    
                    if "participants" not in fresh_tourn: fresh_tourn["participants"] = {}
                    if id_sai in fresh_tourn["participants"]: del fresh_tourn["participants"][id_sai]
                    fresh_tourn["participants"][id_entra] = nome_entra
                    
                    for g in fresh_tourn.get("groups", []):
                        g["bladerIds"] = [id_entra if x == id_sai else x for x in g.get("bladerIds", [])]
                        for m in g.get("matches", []):
                            if m.get("blader1") == id_sai: m["blader1"] = id_entra
                            if m.get("blader2") == id_sai: m["blader2"] = id_entra
                    for rd in fresh_tourn.get("knockout", []):
                        for m in rd.get("matches", []):
                            if m.get("blader1") == id_sai: m["blader1"] = id_entra
                            if m.get("blader2") == id_sai: m["blader2"] = id_entra
                    _save_tournament(fresh_tourn); hide_dialog(admin_dlg); refresh_current_tab()
                
                admin_dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Troca Oficial", color=C_TEXT_PRI), content=ft.Column([dd_sai, dd_entra], tight=True), actions=[PrimaryBtn("Substituir", perform_swap)])
                show_dialog(admin_dlg)

            def get_group_standings(group):
                standings = {b_id: {"id": b_id, "name": bladers_map.get(b_id, "Removido"), "j":0, "v":0, "d":0, "pf":0, "ps":0, "saldo":0, "xtreme":0} for b_id in group.get("bladerIds", [])}
                h2h_wins = {b_id: [] for b_id in group.get("bladerIds", [])}
                
                for match in group.get("matches", []):
                    if match.get("completed"):
                        res = match.get("result", {}); b1, b2, w = res.get("blader1Result", {}), res.get("blader2Result", {}), res.get("winner")
                        if not b1 or not b2: continue
                        
                        b1_id = b1.get("bladerId"); b2_id = b2.get("bladerId")
                        if w == b1_id: h2h_wins[b1_id].append(b2_id)
                        elif w == b2_id: h2h_wins[b2_id].append(b1_id)
                        
                        for bx, bx_data in [(b1, standings.get(b1_id)), (b2, standings.get(b2_id))]:
                            if bx_data is None: continue
                            bx_data["j"] += 1; bx_data["pf"] += bx.get("totalPoints", 0); bx_data["xtreme"] += bx.get("finishes", {}).get("xtreme", 0)
                            if w == bx.get("bladerId"): bx_data["v"] += 1
                            else: bx_data["d"] += 1
                        if standings.get(b1_id): standings[b1_id]["ps"] += b2.get("totalPoints", 0)
                        if standings.get(b2_id): standings[b2_id]["ps"] += b1.get("totalPoints", 0)
                
                for s in standings.values(): s["saldo"] = s["pf"] - s["ps"]
                
                def cmp_standings(a, b):
                    if a["v"] != b["v"]: return b["v"] - a["v"]
                    if a["saldo"] != b["saldo"]: return b["saldo"] - a["saldo"]
                    if b["id"] in h2h_wins.get(a["id"], []): return -1
                    if a["id"] in h2h_wins.get(b["id"], []): return 1
                    if a["xtreme"] != b["xtreme"]: return b["xtreme"] - a["xtreme"]
                    if a["pf"] != b["pf"]: return b["pf"] - a["pf"]
                    return 0
                    
                return sorted(standings.values(), key=cmp_to_key(cmp_standings))

            def prompt_advance_knockout(e):
                safe_cloud_sync(); fresh_tourn = _get_tournament()
                for g in fresh_tourn.get("groups", []):
                    if not all(m.get("completed") for m in g.get("matches", [])): page.snack_bar = ft.SnackBar(ft.Text("⚠️ Finalize todas as partidas primeiro!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return

                dd_format = ft.Dropdown(options=[
                    ft.dropdown.Option(key="single", text="Eliminação Simples"), 
                    ft.dropdown.Option(key="single_md3", text="Simples (MD3 nas Semis/Final)"), 
                    ft.dropdown.Option(key="double", text="Dupla Eliminação (Upper/Lower Bracket)")
                ], value="single", label="Formato do Mata-Mata", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI)
                
                def do_advance(e):
                    hide_dialog(dlg); 
                    is_double = (dd_format.value == "double")
                    is_single_md3 = (dd_format.value == "single_md3")
                    
                    adv_per_group = int(fresh_tourn.get("advancing_per_group", 2)); seeded_players = []
                    for pos in range(adv_per_group):
                        for g in fresh_tourn.get("groups", []):
                            st = get_group_standings(g)
                            if pos < len(st): seeded_players.append(st[pos]["id"])
                            
                    n = len(seeded_players); p2 = 1
                    while p2 < n: p2 *= 2
                    
                    padded = seeded_players + ["BYE"] * (p2 - n)
                    def get_seeds(size):
                        if size == 1: return [0]
                        half = get_seeds(size // 2); res = []
                        for x in half: res.append(x); res.append(size - 1 - x)
                        return res
                    order = get_seeds(p2); ordered_players = [padded[i] for i in order]
                    
                    knockout = []; flat_matches = {}; rounds = int(math.log2(p2))
                    def m_node(m_id, name, is_md3=False): 
                        return {"id": m_id, "name": name, "blader1": None, "blader2": None, "completed": False, "judge": random.choice(["juiz_1", "juiz_2"]), "is_md3": is_md3}
                    
                    ub_rounds = []
                    for r in range(rounds):
                        rm = []
                        for m in range(p2 // (2**(r+1))):
                            is_semi_or_final = (r >= rounds - 2)
                            match = m_node(f"ub-r{r}-m{m}", f"Winner Bracket R{r+1}" if r<rounds-1 else "Final Winner Bracket", is_md3=(is_single_md3 and is_semi_or_final))
                            rm.append(match); flat_matches[match["id"]] = match
                        ub_rounds.append(rm)
                    
                    for r in range(rounds - 1):
                        for m in range(len(ub_rounds[r])): ub_rounds[r][m]["target_w"] = ub_rounds[r+1][m//2]["id"]
                    
                    for i in range(p2 // 2):
                        ub_rounds[0][i]["blader1"] = ordered_players[2*i]
                        ub_rounds[0][i]["blader2"] = ordered_players[2*i+1]

                    if is_double and rounds >= 2:
                        lb_rounds = []
                        for r in range((rounds-1)*2):
                            rm = []
                            for m in range(p2 // (2**((r//2) + 2))):
                                match = m_node(f"lb-r{r}-m{m}", f"Lower Bracket R{r+1}" if r < (rounds-1)*2 -1 else "Final Lower Bracket")
                                rm.append(match); flat_matches[match["id"]] = match
                            lb_rounds.append(rm)
                        
                        for r in range(len(lb_rounds) - 1):
                            for m in range(len(lb_rounds[r])):
                                next_m = m//2 if r%2 != 0 else m
                                lb_rounds[r][m]["target_w"] = lb_rounds[r+1][next_m]["id"]
                                
                        for m in range(len(ub_rounds[0])): ub_rounds[0][m]["target_l"] = lb_rounds[0][m//2]["id"]
                        for r in range(1, rounds):
                            lb_target_r = r*2 - 1
                            if lb_target_r < len(lb_rounds):
                                for m in range(len(ub_rounds[r])):
                                    target_m = len(ub_rounds[r]) - 1 - m 
                                    ub_rounds[r][m]["target_l"] = lb_rounds[lb_target_r][target_m]["id"]
                                    
                        gf = m_node("gf", "Grande Final")
                        flat_matches[gf["id"]] = gf
                        ub_rounds[-1][0]["target_w"] = gf["id"]; lb_rounds[-1][0]["target_w"] = gf["id"]
                        
                        for i, r in enumerate(ub_rounds): knockout.append({"name": f"WB - Rodada {i+1}", "matches": r})
                        for i, r in enumerate(lb_rounds): knockout.append({"name": f"LB - Rodada {i+1}", "matches": r})
                        knockout.append({"name": "Grande Final", "matches": [gf]})
                    else:
                        if rounds >= 2:
                            tp = m_node("tp", "Disputa 3º Lugar", is_md3=is_single_md3)
                            flat_matches[tp["id"]] = tp
                            for m in range(2): ub_rounds[rounds-2][m]["target_l"] = tp["id"]
                            ub_rounds.append([tp])
                        for i, r in enumerate(ub_rounds): knockout.append({"name": f"Rodada {i+1}", "matches": r})

                    def push_target(t_id, p_id):
                        if not t_id: return
                        tm = flat_matches.get(t_id)
                        if tm:
                            if tm.get("blader1") is None: tm["blader1"] = p_id
                            elif tm.get("blader2") is None: tm["blader2"] = p_id

                    changed = True
                    while changed:
                        changed = False
                        for r in knockout:
                            for m in r["matches"]:
                                if not m.get("completed") and (m.get("blader1") == "BYE" or m.get("blader2") == "BYE"):
                                    if m.get("blader1") and m.get("blader2"): 
                                        real_p = m.get("blader1") if m.get("blader2") == "BYE" else m.get("blader2")
                                        m["completed"] = True; m["result"] = {"winner": real_p}
                                        push_target(m.get("target_w"), real_p); push_target(m.get("target_l"), "BYE")
                                        changed = True
                                        
                    fresh_tourn["knockout"] = knockout; fresh_tourn["status"] = "knockout"
                    _save_tournament(fresh_tourn); tourn_state["sub_tab"] = "matamata"; refresh_current_tab()

                dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Mata-Mata", color=C_TEXT_PRI), content=dd_format, actions=[PrimaryBtn("Gerar Chaves", do_advance)])
                show_dialog(dlg)

            view_grupos = ft.ListView(expand=True, spacing=16, padding=ft.padding.only(top=16))
            view_partidas = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))
            view_matamata = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))

            def get_match_action_ui(match_data, b1_n, b2_n, is_ko=False, r_idx=0):
                if match_data.get("completed"):
                    res = match_data.get("result", {})
                    if res.get("winner") == "BYE" or match_data.get("blader1") == "BYE" or match_data.get("blader2") == "BYE":
                        return ft.Text("Avançou (W.O.)", color=C_TEXT_SEC, size=12, weight=ft.FontWeight.BOLD)
                    pts1 = res.get("blader1Result", {}).get("totalPoints", 0); pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                    return ft.Row([ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=match_data: open_match_details(md, tourn))])
                else:
                    if is_ko and (match_data.get("blader1") is None or match_data.get("blader2") is None): return ft.Text("Aguardando...", color=C_TEXT_SEC, size=12)
                    assigned_judge = match_data.get("judge")
                    if has_torneio_access() or assigned_judge == get_username():
                        action_data = {"is_knockout": is_ko, "round_idx": r_idx, "match_id": match_data.get("id"), "group_id": match_data.get("groupId"), "b1_id": match_data.get("blader1"), "b1_name": b1_n, "b2_id": match_data.get("blader2"), "b2_name": b2_n, "judge": assigned_judge, "is_md3": match_data.get("is_md3", False)}
                        return PrimaryBtn("Jogar", lambda e: [tourn_state.update({"active_match": e.control.data, "match_state": {"p1_score": 0, "p2_score": 0, "p1_sets": 0, "p2_sets": 0, "p1_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "p2_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "match_ended": False}, "sub_tab": "combat"}), refresh_current_tab()], height=36, width=80, data=action_data)
                    else: return ft.Row([ft.Icon(ft.Icons.LOCK, size=14, color=C_TEXT_SEC), ft.Text(f"Apito: {assigned_judge or 'Admin'}", color=C_TEXT_SEC, size=11)])

            for group in tourn.get("groups", []):
                sorted_st = get_group_standings(group); g_col = ft.Column([ft.Text(group.get("name", "Grupo"), size=16, weight=ft.FontWeight.W_600, color=C_TEXT_PRI)])
                g_col.controls.append(ft.Container(content=ft.Row([ft.Text("#", width=20, size=12, color=C_TEXT_SEC), ft.Text("Blader", expand=True, size=12, color=C_TEXT_SEC), ft.Text("J", width=25, size=12, color=C_TEXT_SEC), ft.Text("V", width=25, size=12, color=C_TEXT_SEC), ft.Text("PF", width=25, size=12, color=C_TEXT_SEC), ft.Text("PS", width=25, size=12, color=C_TEXT_SEC), ft.Text("Sld", width=30, size=12, color=C_TEXT_SEC)]), padding=8, border=ft.border.only(bottom=ft.BorderSide(1, C_BORDER))))
                adv_limit = int(tourn.get("advancing_per_group", 2))
                for idx, st in enumerate(sorted_st): g_col.controls.append(ft.Container(content=ft.Row([ft.Text(str(idx+1), width=20, size=14, color=C_TEXT_PRI if idx < adv_limit else C_TEXT_SEC), ft.Text(st["name"], expand=True, size=14, color=C_TEXT_PRI), ft.Text(str(st["j"]), width=25, size=14, color=C_TEXT_SEC), ft.Text(str(st["v"]), width=25, size=14, color=C_TEXT_SEC), ft.Text(str(st["pf"]), width=25, size=14, color=C_TEXT_SEC), ft.Text(str(st["ps"]), width=25, size=14, color=C_TEXT_SEC), ft.Text(str(st["saldo"]), width=30, size=14, color=C_SUCCESS if st["saldo"] > 0 else C_ERROR)]), padding=8, bgcolor=C_SURFACE_SEC if idx < adv_limit else "transparent", border_radius=8))
                view_grupos.controls.append(AppCard(g_col))

                view_partidas.controls.append(ft.Text(group.get("name", ""), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC, margin=ft.margin.only(top=8)))
                for match in group.get("matches", []):
                    b1_name = bladers_map.get(match.get("blader1"), "Removido"); b2_name = bladers_map.get(match.get("blader2"), "Removido")
                    view_partidas.controls.append(AppCard(ft.Row([ft.Column([ft.Text(b1_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI), ft.Text("vs", size=10, color=C_TEXT_SEC), ft.Text(b2_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI)]), get_match_action_ui(match, b1_name, b2_name)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

            if tourn.get("status") == "groups" and has_torneio_access(): view_grupos.controls.append(PrimaryBtn("Avançar para Mata-Mata", prompt_advance_knockout, width=float("inf")))
            
            if tourn.get("knockout"):
                for r_idx, round_data in enumerate(tourn.get("knockout", [])):
                    view_matamata.controls.append(ft.Text(round_data.get("name", ""), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC, margin=ft.margin.only(top=8)))
                    for match in round_data.get("matches", []):
                        b1_id = match.get("blader1"); b2_id = match.get("blader2")
                        b1_name = bladers_map.get(b1_id, "A definir") if b1_id and b1_id != "BYE" else "W.O." if b1_id == "BYE" else "A definir"
                        b2_name = bladers_map.get(b2_id, "A definir") if b2_id and b2_id != "BYE" else "W.O." if b2_id == "BYE" else "A definir"
                        if match.get("name"): view_matamata.controls.append(ft.Text(match.get("name"), size=12, color=C_PRIMARY, text_align="center"))
                        view_matamata.controls.append(AppCard(ft.Row([ft.Column([ft.Text(b1_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI), ft.Text("vs", size=10, color=C_TEXT_SEC), ft.Text(b2_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI)]), get_match_action_ui(match, b1_name, b2_name, is_ko=True, r_idx=r_idx)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

            tab_nav_container = ft.Container(padding=ft.padding.symmetric(horizontal=24)); content_switcher = ft.Container(content=view_matamata if tourn_state["sub_tab"] == "matamata" else (view_partidas if tourn_state["sub_tab"] == "partidas" else view_grupos), expand=True)

            def switch_sub_tab(tab_name):
                tourn_state["sub_tab"] = tab_name
                is_g = tab_name == "grupos"; is_p = tab_name == "partidas"; is_m = tab_name == "matamata"
                tabs = [ft.Container(content=ft.Text("Grupos", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_g else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_g else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_sub_tab("grupos")), ft.Container(content=ft.Text("Partidas", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_p else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_p else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_sub_tab("partidas"))]
                if tourn.get("status") == "knockout": tabs.append(ft.Container(content=ft.Text("Mata-Mata", size=13, weight=ft.FontWeight.W_600, color=C_PRIMARY if is_m else C_TEXT_SEC), expand=True, bgcolor=f"{C_PRIMARY}15" if is_m else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_sub_tab("matamata")))
                tab_nav_container.content = ft.Container(content=ft.Row(tabs, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BORDER), border_radius=10, padding=4)
                content_switcher.content = view_grupos if tab_name == "grupos" else (view_partidas if tab_name == "partidas" else view_matamata); page.update()
            
            switch_sub_tab(tourn_state["sub_tab"])

            def open_end_dialog(e):
                def do_delete(ev):
                    _save_tournament(None); hide_dialog(end_dlg); refresh_current_tab()
                def do_save(ev):
                    _add_to_history(tourn); _save_tournament(None); hide_dialog(end_dlg); refresh_current_tab()
                end_dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Encerrar", color=C_TEXT_PRI), content=ft.Text("O que deseja fazer?", color=C_TEXT_SEC), actions=[SecondaryBtn("Excluir", do_delete), PrimaryBtn("Salvar no Histórico", do_save)])
                show_dialog(end_dlg)

            actions_row = [IconButton(ft.Icons.REFRESH, lambda _: [safe_cloud_sync(), refresh_current_tab()], color=C_PRIMARY)]
            if has_torneio_access(): actions_row.extend([IconButton(ft.Icons.SWAP_HORIZ, open_admin_panel, color=C_PRIMARY), IconButton(ft.Icons.POWER_SETTINGS_NEW, open_end_dialog, color=C_ERROR)])

            return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Row([ft.Column([ft.Text(tourn.get("name",""), size=20, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), ft.Text(f"Ambiente: {get_current_org().upper()}", size=12, color=C_PRIMARY)], spacing=0), ft.Row(actions_row)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=24), tab_nav_container, ft.Container(content=content_switcher, padding=ft.padding.symmetric(horizontal=24), expand=True)]))

    # --- TELA 5: HISTÓRICO ---
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
                    if w == "BYE": return
                    for b_key in ["blader1Result", "blader2Result"]:
                        b_res = res.get(b_key, {}); bid = b_res.get("bladerId")
                        if not bid or bid == "BYE": continue
                        if bid not in stats: stats[bid] = {"name": b_map_history.get(bid, "Removido"), "j":0, "v":0, "pts":0, "spin":0, "over":0, "burst":0, "xtreme":0, "flag":0}
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
                        res = m.get("result", {}); b1_n = b_map_history.get(m.get("blader1"), "Removido"); b2_n = b_map_history.get(m.get("blader2"), "Removido")
                        pts1 = res.get("blader1Result", {}).get("totalPoints", 0); pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                        status_ui = ft.Row([ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=m: open_match_details(md, t_data))])
                        view_tabelas.controls.append(AppCard(ft.Row([ft.Text(b1_n, size=14, color=C_TEXT_PRI), status_ui, ft.Text(b2_n, size=14, color=C_TEXT_PRI)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))
            
            for r in t_data.get("knockout", []):
                view_tabelas.controls.append(ft.Text(r.get("name", ""), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC, margin=ft.margin.only(top=8)))
                for match in r.get("matches", []):
                    match_title = match.get("name")
                    if match_title: view_tabelas.controls.append(ft.Text(match_title, size=12, color=C_PRIMARY, text_align="center"))
                    b1_id = match.get("blader1"); b2_id = match.get("blader2")
                    b1_name = b_map_history.get(b1_id, "A definir") if b1_id and b1_id != "BYE" else "W.O." if b1_id == "BYE" else "A definir"
                    b2_name = b_map_history.get(b2_id, "A definir") if b2_id and b2_id != "BYE" else "W.O." if b2_id == "BYE" else "A definir"
                    if match.get("completed"):
                        res = match.get("result", {})
                        if res.get("winner") == "BYE" or b1_id == "BYE" or b2_id == "BYE": status_ui = ft.Text("Avançou (W.O.)", color=C_TEXT_SEC, size=12, weight=ft.FontWeight.BOLD)
                        else:
                            pts1 = res.get("blader1Result", {}).get("totalPoints", 0); pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                            status_ui = ft.Row([ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=match: open_match_details(md, t_data))])
                        view_tabelas.controls.append(AppCard(ft.Row([ft.Text(b1_name, size=14, color=C_TEXT_PRI), status_ui, ft.Text(b2_name, size=14, color=C_TEXT_PRI)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

            view_stats = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))
            for st in sorted_stats: view_stats.controls.append(AppCard(ft.Column([ft.Row([ft.Text(st["name"], weight=ft.FontWeight.BOLD, size=16, color=C_TEXT_PRI, expand=True), ft.Text(f"{st['pts']} Pts", weight=ft.FontWeight.BOLD, size=16, color=C_PRIMARY)]), ft.Text(f"{st['v']} Vitórias em {st['j']} Jogos", size=12, color=C_TEXT_SEC), ft.Container(height=4), ft.Row([Badge(f"XT: {st['xtreme']}", C_XTREME), Badge(f"BU: {st['burst']}", C_BURST), Badge(f"OV: {st['over']}", C_OVER), Badge(f"SP: {st['spin']}", C_SPIN), Badge(f"FL: {st['flag']}", C_FLAG)], spacing=6, wrap=True)], spacing=4), padding=16))

            hist_nav_container = ft.Container(padding=ft.padding.symmetric(horizontal=24))
            content_switcher = ft.Container(content=view_tabelas if history_state["sub_tab"] == "tabelas" else view_stats, expand=True)

            def switch_det_tab(tab_name): 
                history_state["sub_tab"] = tab_name
                is_t = tab_name == "tabelas"
                tabs = [ft.Container(content=ft.Text("Chaves", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_t else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_t else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_det_tab("tabelas")), ft.Container(content=ft.Text("Estatísticas", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if not is_t else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if not is_t else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_det_tab("estatisticas"))]
                hist_nav_container.content = ft.Container(content=ft.Row(tabs, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BORDER), border_radius=10, padding=4)
                content_switcher.content = view_tabelas if tab_name == "tabelas" else view_stats; page.update()
            
            switch_det_tab(history_state["sub_tab"])
            org_header = f"[{t_data.get('org', 'admin').upper()}] " if is_admin_max() and app_state.get("admin_viewing_org") == "admin" else ""
            return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Row([IconButton(ft.Icons.ARROW_BACK, lambda _: [history_state.update({"active_tourn": None}), refresh_current_tab()]), ft.Text(f"{org_header}{t_data.get('name', '')}", size=18, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI, expand=True, text_align="right")]), padding=24), hist_nav_container, ft.Container(content=content_switcher, padding=ft.padding.symmetric(horizontal=24), expand=True)]))

        hist = _get_history()
        if not hist: return ft.Container(content=ft.Column([ft.Icon(ft.Icons.HISTORY, size=64, color=C_BORDER), ft.Text("Histórico vazio.", color=C_TEXT_SEC, size=16)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True, alignment=ft.Alignment(0,0))
        list_ui = ft.ListView(expand=True, spacing=12, padding=24)
        list_ui.controls.append(ft.Text("Torneios Anteriores", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI, margin=ft.margin.only(bottom=8)))
        
        def confirm_delete_history(t_id, t_name, t_org):
            def do_delete(e):
                safe_cloud_sync()
                with db_lock: app_data["history"] = [h for h in app_data.get("history", []) if not(h.get("id") == t_id and h.get("org", "admin") == t_org)]
                save_db(app_data); hide_dialog(dlg); refresh_current_tab(); page.snack_bar = ft.SnackBar(ft.Text("Torneio apagado!"), bgcolor=C_SUCCESS); page.snack_bar.open = True; page.update()
            dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Excluir Histórico", color=C_TEXT_PRI), content=ft.Text(f"Apagar '{t_name}'?", color=C_TEXT_SEC), actions=[SecondaryBtn("Cancelar", lambda _: hide_dialog(dlg)), PrimaryBtn("Excluir", do_delete, color=C_ERROR)])
            show_dialog(dlg)

        for t in hist:
            org_tag = f"[{t.get('org', 'admin').upper()}] " if is_admin_max() and app_state.get("admin_viewing_org") == "admin" else ""
            list_ui.controls.append(AppCard(ft.Row([ft.Column([ft.Text(f"{org_tag}{t.get('name', '')}", weight=ft.FontWeight.W_600, size=16, color=C_TEXT_PRI), ft.Text(f"{t.get('date', '')}", size=12, color=C_TEXT_SEC)], spacing=2, expand=True), IconButton(ft.Icons.VISIBILITY, lambda e, data=t: [history_state.update({"active_tourn": data, "sub_tab": "tabelas"}), refresh_current_tab()], color=C_PRIMARY), IconButton(ft.Icons.DELETE_OUTLINE, lambda e, tid=t.get("id"), tname=t.get("name", ""), torg=t.get("org", "admin"): confirm_delete_history(tid, tname, torg), color=C_ERROR)], spacing=12), padding=16))
        return ft.Container(content=list_ui, expand=True)

    # --- TELA 6: ADMIN MAX ---
    def build_admin_view():
        if not is_admin_max(): return ft.Container()
        admin_state = {"search_query": ""}; search_input = ft.TextField(hint_text="Buscar usuário...", prefix_icon=ft.Icons.SEARCH, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12, content_padding=10)
        users_list_ui = ft.ListView(expand=True, spacing=12)

        def render_users():
            users_list_ui.controls.clear(); query = admin_state["search_query"].lower()
            all_users = {k: v.copy() for k, v in HARDCODED_USERS.items()}
            for k, v in get_users().items(): all_users[k] = v

            for u_name, u_data in all_users.items():
                if query and query not in u_name.lower(): continue 
                
                role_dd = ft.Dropdown(value=u_data.get('role', 'basic'), options=[ft.dropdown.Option(key="basic", text="Básico"), ft.dropdown.Option(key="treinador", text="Treinador"), ft.dropdown.Option(key="organizador", text="Organizador"), ft.dropdown.Option(key="pro", text="Pro"), ft.dropdown.Option(key="admin_max", text="Admin Max")], width=130, height=40, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, text_size=12)
                org_input = ft.TextField(value=u_data.get('org', u_name), hint_text="Ex: org1, org2", label="Ambientes", width=120, height=40, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, text_size=12, content_padding=10)

                def save_user_role(e, un=u_name, dd=role_dd, oi=org_input, udt=u_data):
                    safe_cloud_sync(); db = get_users()
                    psw = udt.get("password")
                    if not psw and un in HARDCODED_USERS: psw = HARDCODED_USERS[un]["password"]
                    if not psw: psw = "123" # Fallback
                    
                    db[un] = {"password": psw, "role": dd.value, "org": oi.value.strip()}
                    save_users(db); page.snack_bar = ft.SnackBar(ft.Text(f"Acessos de {un} salvos!"), bgcolor=C_SUCCESS); page.snack_bar.open = True; page.update()

                btn_save = IconButton(ft.Icons.SAVE, lambda e, un=u_name, dd=role_dd, oi=org_input, udt=u_data: save_user_role(e, un, dd, oi, udt), color=C_SUCCESS)
                users_list_ui.controls.append(AppCard(ft.Row([ft.Text(u_name, weight=ft.FontWeight.W_600, size=14, color=C_TEXT_PRI, expand=True), org_input, role_dd, btn_save], spacing=8), padding=12))

            page.update()
        search_input.on_change = lambda e: [admin_state.update({"search_query": e.control.value}), render_users()]
        render_users() 
        return ft.Container(padding=24, content=ft.Column([ft.Text("Painel Supremo", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), search_input, ft.Container(height=8), ft.Container(content=users_list_ui, expand=True)]))

    content_area = ft.Container(expand=True)
    TABS_MAP = {"Bladers": build_home_view, "Treino": build_training_view, "Combate": build_quick_match_view, "Torneio": build_tournament_view, "Histórico": build_history_view, "Admin": build_admin_view, "Perfil": build_profile_view}

    def change_tab_programmatic(index):
        if not bottom_nav.destinations: return
        content_area.content = None; page.update()
        if build_func := TABS_MAP.get(bottom_nav.destinations[index].label): content_area.content = build_func()
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
        app_state["admin_viewing_org"] = "admin"; update_appbar()
        role = current_user().get("role", "basic"); dests = []
        if role in ["admin_max", "pro", "organizador", "judge"]: dests.append(ft.NavigationBarDestination(icon=ft.Icons.PEOPLE_OUTLINE, label="Bladers"))
        if role in ["admin_max", "pro", "treinador"]: dests.append(ft.NavigationBarDestination(icon=ft.Icons.FITNESS_CENTER_OUTLINED, label="Treino"))
        dests.append(ft.NavigationBarDestination(icon=ft.Icons.FLASH_ON_OUTLINED, label="Combate"))
        if role in ["admin_max", "pro", "organizador", "judge"]: dests.append(ft.NavigationBarDestination(icon=ft.Icons.EMOJI_EVENTS_OUTLINED, label="Torneio")); dests.append(ft.NavigationBarDestination(icon=ft.Icons.HISTORY_OUTLINED, label="Histórico"))
        if role == "admin_max": dests.append(ft.NavigationBarDestination(icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED, label="Admin"))
        dests.append(ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINE, label="Perfil"))
        bottom_nav.destinations = dests; bottom_nav.selected_index = 0; bottom_nav.on_change = change_tab; page.update(); change_tab_programmatic(0)

    main_app_container.content = ft.Column([content_area], expand=True)
    page.add(login_container, main_app_container, bottom_nav)

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
                            if app_state.get("current_user"):
                                u_name = app_state["current_user"]["username"]
                                if u_name in nuvem.get("users", {}):
                                    cloud_token = nuvem["users"][u_name].get("session_token")
                                    if cloud_token and app_state.get("session_token") and cloud_token != app_state.get("session_token"):
                                        do_logout(force_msg=True); continue
                            local_ts = app_data.get("last_updated", 0)
                            if nuvem.get("last_updated", 0) > local_ts:
                                app_data.clear(); app_data.update(nuvem)
                                needs_refresh = True
                            else: needs_refresh = False
                        if needs_refresh and bottom_nav.destinations:
                            if bottom_nav.destinations[bottom_nav.selected_index].label not in ["Bladers", "Treino", "Combate", "Admin"]: refresh_current_tab()
            except Exception: pass 
    threading.Thread(target=auto_sync_loop, daemon=True).start()

ft.run(main)
