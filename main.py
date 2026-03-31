import flet as ft
import time
import math
import json
import threading 
import requests  
import random 
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

C_XTREME = C_PRIMARY
C_BURST = "#A855F7"       
C_OVER = "#3B82F6"        
C_SPIN = "#22C55E"        
C_FLAG = "#EAB308"        

PTS_WIN_TARGET = 4
PTS_MAP = {"xtreme": 3, "burst": 2, "over": 2, "spin": 1, "flag": 1}

# ==========================================
# 2. MOTOR DA NUVEM BLINDADO
# ==========================================
FIREBASE_URL = "https://beybladeapp-c303a-default-rtdb.firebaseio.com/beyblade_data.json"

app_data = {"bladers": [], "tournament": None, "active_match": None, "history": [], "users": {}, "last_updated": 0}
is_syncing = False 
db_lock = threading.Lock() 

on_sync_start = None
on_sync_end = None

def safe_cloud_sync():
    if on_sync_start: on_sync_start()
    try:
        res = requests.get(FIREBASE_URL, timeout=5)
        if res.status_code == 200 and res.json() is not None:
            with db_lock: 
                app_data.clear()
                app_data.update(res.json())
                if "users" not in app_data: app_data["users"] = {}
                if "last_updated" not in app_data: app_data["last_updated"] = 0
    except Exception as e:
        pass
    finally:
        if on_sync_end: on_sync_end()

def load_db():
    safe_cloud_sync()
    return app_data

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
                res = requests.put(FIREBASE_URL, json=dados, timeout=5)
                if res.status_code == 200: break
            except Exception:
                time.sleep(1.5)
        is_syncing = False
        if on_sync_end: on_sync_end()

    threading.Thread(target=_background_save, args=(dados_copia,), daemon=True).start()

load_db()

def get_bladers():
    with db_lock: return json.loads(json.dumps(app_data.get("bladers", [])))
def save_bladers(bladers_list): 
    with db_lock: app_data["bladers"] = bladers_list
    save_db(app_data)
def get_tournament():
    with db_lock: return json.loads(json.dumps(app_data.get("tournament"))) if app_data.get("tournament") else None
def save_tournament(tourn_data): 
    with db_lock: app_data["tournament"] = tourn_data
    save_db(app_data)
def get_active_match():
    with db_lock: return json.loads(json.dumps(app_data.get("active_match"))) if app_data.get("active_match") else None
def set_active_match(match_data):
    with db_lock: app_data["active_match"] = match_data
    save_db(app_data)
def get_history():
    with db_lock: return json.loads(json.dumps(app_data.get("history", [])))
def add_to_history(tourn_data):
    with db_lock:
        hist = app_data.get("history", [])
        hist.insert(0, tourn_data)
        app_data["history"] = hist
    save_db(app_data)
def get_users():
    with db_lock: return json.loads(json.dumps(app_data.get("users", {})))
def save_users(users_dict):
    with db_lock: app_data["users"] = users_dict
    save_db(app_data)

# ==========================================
# 3. SISTEMA DE PERFIS (RBAC)
# ==========================================
HARDCODED_USERS = {
    "themonc08": {"password": "150217bR*", "role": "admin_max"},
    "caruso": {"password": "bladerbey01", "role": "pro"},
    "juiz_1": {"password": "beyjuiz1", "role": "judge"},
    "juiz_2": {"password": "beyjuiz2", "role": "judge"}
}

app_state = {"current_user": None}

def is_admin_max(): return app_state["current_user"] and app_state["current_user"]["role"] == "admin_max"
def is_pro(): return app_state["current_user"] and app_state["current_user"]["role"] in ["admin_max", "pro"]
def is_judge(): return app_state["current_user"] and app_state["current_user"]["role"] == "judge"
def get_username(): return app_state["current_user"]["username"] if app_state["current_user"] else ""

# ==========================================
# 4. COMPONENTES UI
# ==========================================
def AppCard(content, padding=16, on_click=None, data=None):
    return ft.Container(content=content, padding=padding, bgcolor=C_SURFACE, border_radius=16, border=ft.border.all(1, C_BORDER), on_click=on_click, data=data)

def PrimaryBtn(text, on_click, width=None, height=48, icon=None, data=None, color=C_PRIMARY, expand=False):
    items = []
    if icon: items.append(ft.Icon(icon, color=C_TEXT_PRI, size=20))
    items.append(ft.Text(text, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, size=14))
    return ft.Container(content=ft.Row(items, alignment=ft.MainAxisAlignment.CENTER, spacing=8) if icon else items[0], bgcolor=color, padding=8, border_radius=12, alignment=ft.Alignment(0, 0), width=width, height=height, on_click=on_click, data=data, expand=expand)

def SecondaryBtn(text, on_click, width=None, height=48, icon=None, data=None, expand=False):
    items = []
    if icon: items.append(ft.Icon(icon, color=C_TEXT_SEC, size=20))
    items.append(ft.Text(text, color=C_TEXT_SEC, weight=ft.FontWeight.W_500, size=13))
    return ft.Container(content=ft.Row(items, alignment=ft.MainAxisAlignment.CENTER, spacing=8) if icon else items[0], bgcolor=C_SURFACE_SEC, padding=8, border_radius=12, border=ft.border.all(1, C_BORDER), alignment=ft.Alignment(0, 0), width=width, height=height, on_click=on_click, data=data, expand=expand)

def IconButton(icon, on_click, color=C_TEXT_SEC, tooltip=None):
    return ft.Container(content=ft.Icon(icon, color=color, size=22), padding=10, border_radius=10, bgcolor=C_SURFACE_SEC, border=ft.border.all(1, C_BORDER), on_click=on_click, tooltip=tooltip)

def Badge(text, color):
    return ft.Container(content=ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=color), padding=6, bgcolor=f"{color}15", border_radius=6, border=ft.border.all(1, f"{color}40"))

# ==========================================
# 5. O APLICATIVO PRINCIPAL
# ==========================================
def main(page: ft.Page):
    page.title = "Beyblade X Counter"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = C_BG
    page.padding = 0
    page.window.width = 450
    page.window.height = 800
    page.fonts = {"Inter": "https://raw.githubusercontent.com/rsms/inter/master/docs/font-files/Inter-Regular.woff2"}
    page.theme = ft.Theme(font_family="Inter")

    def do_logout(e=None):
        app_state["current_user"] = None
        main_app_container.visible = False
        bottom_nav.visible = False
        login_container.visible = True
        page.update()

    sync_ring = ft.ProgressRing(width=16, height=16, color=C_PRIMARY, stroke_width=2, visible=False)
    page.appbar = ft.AppBar(
        title=ft.Text("Beyblade X", size=16, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI),
        bgcolor=C_BG, 
        actions=[
            ft.Container(content=sync_ring, padding=ft.padding.only(right=10)),
            ft.IconButton(ft.Icons.LOGOUT, icon_color=C_ERROR, on_click=do_logout, tooltip="Sair da Conta")
        ]
    )

    def _show_sync(): sync_ring.visible = True; page.update()
    def _hide_sync(): sync_ring.visible = False; page.update()

    global on_sync_start, on_sync_end
    on_sync_start = _show_sync
    on_sync_end = _hide_sync

    def show_dialog(dlg):
        if dlg not in page.overlay: page.overlay.append(dlg)
        dlg.open = True; page.update()

    def hide_dialog(dlg): dlg.open = False; page.update()

    def get_snapshot_map(tourn_data):
        b_map = {b["id"]: b["name"] for b in get_bladers()}
        if tourn_data and "participants" in tourn_data: b_map.update(tourn_data["participants"])
        return b_map

    def open_match_details(m_data, tourn_context=None):
        b_map = get_snapshot_map(tourn_context)
        res = m_data.get("result", {})
        b1_name = b_map.get(m_data.get("blader1"), "A Definir")
        b2_name = b_map.get(m_data.get("blader2"), "A Definir")
        f1 = res.get("blader1Result", {}).get("finishes", {})
        f2 = res.get("blader2Result", {}).get("finishes", {})

        def f_row(label, key, color): return ft.Row([ft.Text(str(f1.get(key, 0)), color=color, weight=ft.FontWeight.BOLD, size=16, width=30, text_align="center"), ft.Text(label, color=C_TEXT_SEC, expand=True, text_align="center", size=13), ft.Text(str(f2.get(key, 0)), color=color, weight=ft.FontWeight.BOLD, size=16, width=30, text_align="center")])

        dlg = ft.AlertDialog(
            bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), content_padding=24,
            title=ft.Text("Raio-X da Partida", color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, size=18, text_align="center"),
            content=ft.Column([
                ft.Row([ft.Text(b1_name, weight=ft.FontWeight.W_600, color=C_TEXT_PRI, expand=True, text_align="center", size=14), ft.Text("VS", size=11, color=C_TEXT_SEC), ft.Text(b2_name, weight=ft.FontWeight.W_600, color=C_TEXT_PRI, expand=True, text_align="center", size=14)]),
                ft.Divider(color=C_BORDER, height=20),
                f_row("XTREME", "xtreme", C_XTREME), f_row("BURST", "burst", C_BURST), f_row("OVER", "over", C_OVER), f_row("SPIN", "spin", C_SPIN), f_row("FLAG", "flag", C_FLAG),
                ft.Divider(color=C_BORDER, height=20),
                ft.Row([ft.Text(str(res.get("blader1Result", {}).get("totalPoints", 0)), size=24, color=C_PRIMARY, weight=ft.FontWeight.BOLD, width=30, text_align="center"), ft.Text("PONTOS", color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, expand=True, text_align="center", size=14), ft.Text(str(res.get("blader2Result", {}).get("totalPoints", 0)), size=24, color=C_PRIMARY, weight=ft.FontWeight.BOLD, width=30, text_align="center")])
            ], tight=True), actions=[SecondaryBtn("Fechar", lambda _: hide_dialog(dlg))]
        )
        show_dialog(dlg)

    # --- TELA DE LOGIN / REGISTRO ---
    login_container = ft.Container(expand=True, padding=24)
    
    def build_auth_view(is_login=True):
        username_input = ft.TextField(label="Usuário", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
        password_input = ft.TextField(label="Senha", password=True, can_reveal_password=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
        email_input = ft.TextField(label="Email", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12, visible=not is_login)

        def do_auth(e):
            u = username_input.value.strip()
            p = password_input.value.strip()
            if not u or not p:
                page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return
            
            safe_cloud_sync()
            db_users = get_users()

            if is_login:
                if u in HARDCODED_USERS and HARDCODED_USERS[u]["password"] == p:
                    app_state["current_user"] = {"username": u, "role": HARDCODED_USERS[u]["role"]}
                    start_main_app(); return
                if u in db_users and db_users[u].get("password") == p:
                    app_state["current_user"] = {"username": u, "role": db_users[u].get("role", "basic")}
                    start_main_app(); return
                page.snack_bar = ft.SnackBar(ft.Text("Usuário ou senha inválidos!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update()
            else:
                em = email_input.value.strip()
                if u in HARDCODED_USERS or u in db_users:
                    page.snack_bar = ft.SnackBar(ft.Text("Usuário já existe! Escolha outro."), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return
                
                db_users[u] = {"password": p, "email": em, "role": "basic"}
                save_users(db_users)
                app_state["current_user"] = {"username": u, "role": "basic"}
                start_main_app()

        def toggle_mode(e): login_container.content = build_auth_view(not is_login); page.update()

        title_txt = "Bem-vindo de volta" if is_login else "Criar Conta"
        btn_txt = "Entrar" if is_login else "Cadastrar"
        switch_txt = "Não tem conta? Cadastre-se" if is_login else "Já tem conta? Faça Login"

        return ft.Column([
            ft.Container(height=40), ft.Icon(ft.Icons.SECURITY, size=64, color=C_PRIMARY),
            ft.Text(title_txt, size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI),
            ft.Text("Faça login para acessar o motor de torneios.", size=14, color=C_TEXT_SEC),
            ft.Container(height=20), username_input, email_input, password_input,
            PrimaryBtn(btn_txt, do_auth, width=float("inf")),
            ft.TextButton(switch_txt, on_click=toggle_mode, style=ft.ButtonStyle(color=C_TEXT_SEC))
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    login_container.content = build_auth_view(True)

    # ==========================================
    # LÓGICA DE VIEWS (PÓS-LOGIN)
    # ==========================================
    main_app_container = ft.Container(expand=True, visible=False)
    
    bottom_nav = ft.NavigationBar(
        bgcolor=C_BG, indicator_color=C_SURFACE_SEC, visible=False, 
        destinations=[ft.NavigationBarDestination(icon=ft.Icons.HOURGLASS_EMPTY, label="1"), ft.NavigationBarDestination(icon=ft.Icons.HOURGLASS_EMPTY, label="2")]
    )
    
    history_state = {"active_tourn": None, "sub_tab": "tabelas"}
    home_state = {"sub_tab": "cadastro", "selected_ids": [], "temp_name": ""}
    tourn_state = {"sub_tab": None}

    # --- TELA 0: PERFIL BÁSICO ---
    def build_profile_view():
        return ft.Container(
            padding=24,
            content=ft.Column([
                ft.Container(height=50),
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color=C_TEXT_SEC),
                ft.Text(f"Olá, {get_username()}!", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI),
                ft.Container(height=10),
                Badge("Acesso Básico", C_PRIMARY),
                ft.Container(height=20),
                ft.Text("Sua conta permite usar a aba Combate para contador de partidas casuais.", color=C_TEXT_SEC, text_align="center"),
                ft.Text("Peça a um Administrador para elevar seu cargo para Pro ou Juiz.", color=C_PRIMARY, text_align="center")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    # --- TELA 1: BLADERS (APENAS PRO/ADMIN) ---
    def build_home_view():
        if not is_pro(): return ft.Container(content=ft.Text("Acesso Restrito.", color=C_ERROR), padding=24)

        bladers = get_bladers()
        def save_temp_name(e): home_state["temp_name"] = e.control.value
        blader_input = ft.TextField(value=home_state["temp_name"], hint_text="Nome do Blader...", expand=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, text_size=14, border_radius=12, content_padding=16, cursor_color=C_PRIMARY, on_change=save_temp_name)
        
        is_adding = False
        def add_blader(e):
            nonlocal is_adding
            if is_adding: return
            if blader_input.value.strip():
                is_adding = True
                safe_cloud_sync() 
                b_list = get_bladers()
                b_list.append({"id": str(int(time.time())), "name": blader_input.value.strip()})
                save_bladers(b_list)
                home_state["temp_name"] = ""
                blader_input.value = ""
                refresh_current_tab()
                is_adding = False

        def confirm_remove_blader(b_id, b_name):
            def do_remove(e):
                safe_cloud_sync()
                if b_id in home_state["selected_ids"]: home_state["selected_ids"].remove(b_id)
                save_bladers([b for b in get_bladers() if b["id"] != b_id])
                hide_dialog(dlg_confirm)
                refresh_current_tab()
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
            btn_criar.content.controls[1].value = f"Avançar para Passo 2 ({len(home_state['selected_ids'])})"
            page.update()

        for b in bladers: selection_list_ui.controls.append(AppCard(ft.Checkbox(label=b["name"], value=(b["id"] in home_state["selected_ids"]), on_change=lambda e, bid=b["id"]: toggle_selection(e, bid), fill_color=C_PRIMARY, check_color=C_BG, label_style=ft.TextStyle(color=C_TEXT_PRI, size=15, weight=ft.FontWeight.W_500)), padding=8))

        view_config_container = ft.Container(expand=True)

        def open_config_view(e):
            selected_bladers = [b for b in get_bladers() if b["id"] in home_state["selected_ids"]]
            total_b = len(selected_bladers)
            if total_b < 2:
                page.snack_bar = ft.SnackBar(ft.Text("Selecione pelo menos 2 Bladers!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return 
            
            config_state = {"num_groups": 1, "sizes": [total_b]}
            max_groups = max(1, total_b // 2)
            dist_col = ft.Column(spacing=4) 
            sum_text = ft.Text("", color=C_TEXT_SEC, size=13, weight=ft.FontWeight.W_600)

            def update_dist_ui():
                dist_col.controls.clear()
                current_sum = sum(config_state["sizes"])
                for i in range(config_state["num_groups"]):
                    def make_btn(idx, delta):
                        def on_click(e):
                            if config_state["sizes"][idx] + delta >= 1:
                                config_state["sizes"][idx] += delta
                                update_dist_ui()
                        return ft.IconButton(ft.Icons.ADD if delta>0 else ft.Icons.REMOVE, on_click=on_click, icon_color=C_TEXT_PRI, bgcolor=C_SURFACE_SEC, width=35, height=35)
                    dist_col.controls.append(ft.Row([ft.Text(f"Grupo {chr(65+i)}", color=C_TEXT_PRI, width=65, size=14, weight=ft.FontWeight.BOLD), make_btn(i, -1), ft.Text(str(config_state["sizes"][i]), color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, width=20, text_align="center"), make_btn(i, 1)], alignment=ft.MainAxisAlignment.CENTER, spacing=12))
                
                diff = total_b - current_sum
                if diff == 0: sum_text.value = f"✅ Total perfeito: {total_b} participantes"; sum_text.color = C_SUCCESS
                elif diff > 0: sum_text.value = f"⚠️ Faltam alocar {diff} participante(s)"; sum_text.color = C_ERROR
                else: sum_text.value = f"⚠️ Sobrando {-diff} vaga(s). Reduza."; sum_text.color = C_ERROR
                page.update() 

            def on_group_count_change(e=None):
                new_count = int(dd_groups.value)
                config_state["num_groups"] = new_count
                base = total_b // new_count
                rem = total_b % new_count
                config_state["sizes"] = [base + (1 if i < rem else 0) for i in range(new_count)]
                update_dist_ui()

            dd_groups = ft.Dropdown(options=[ft.dropdown.Option(key=str(i), text=f"{i} Grupo(s)") for i in range(1, max_groups + 1)], value="1", expand=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            dd_groups.on_change = on_group_count_change 
            btn_refresh = ft.Container(content=ft.Icon(ft.Icons.SYNC, color=C_PRIMARY), bgcolor=C_SURFACE_SEC, padding=12, border_radius=12, border=ft.border.all(1, C_BORDER), on_click=on_group_count_change)
            dd_advances = ft.Dropdown(options=[ft.dropdown.Option(key=str(i), text=f"{i} por Grupo") for i in range(1, 5)], value="2", expand=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            name_input = ft.TextField(label="Nome do Torneio", value=f"Torneio {datetime.now().strftime('%d/%m')}", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)

            def optimize_match_order(match_list):
                if len(match_list) <= 2: return match_list
                random.shuffle(match_list)
                arranged = [match_list.pop(0)]
                while match_list:
                    best_idx = 0
                    best_score = -999
                    for idx, m in enumerate(match_list):
                        score = 0
                        players = {m["blader1"], m["blader2"]}
                        last_players = {arranged[-1]["blader1"], arranged[-1]["blader2"]}
                        if players.intersection(last_players): score -= 10
                        if len(arranged) >= 2:
                            prev_players = {arranged[-2]["blader1"], arranged[-2]["blader2"]}
                            if players.intersection(prev_players): score -= 5
                        if score > best_score:
                            best_score = score
                            best_idx = idx
                    arranged.append(match_list.pop(best_idx))
                return arranged

            def confirm_create(e):
                if sum(config_state["sizes"]) != total_b:
                    page.snack_bar = ft.SnackBar(ft.Text("⚠️ Ajuste as vagas! A soma deve ser igual ao número de participantes."), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return
                safe_cloud_sync() 
                groups = []
                participants_snapshot = {b["id"]: b["name"] for b in selected_bladers}
                shuffled_bladers = list(selected_bladers)
                random.shuffle(shuffled_bladers) 
                
                blader_idx = 0
                judges_pool = ["juiz_1", "juiz_2"] 
                num_groups = len(config_state["sizes"])
                is_odd_groups = (num_groups % 2 != 0)
                
                for i, size in enumerate(config_state["sizes"]):
                    group_bladers = shuffled_bladers[blader_idx : blader_idx + size]
                    blader_idx += size
                    
                    matches = [{"id": f"{i}-{j}-{k}-{int(time.time()*1000)}", "groupId": f"group-{i}", "blader1": group_bladers[j]["id"], "blader2": group_bladers[k]["id"], "completed": False} for j in range(len(group_bladers)) for k in range(j + 1, len(group_bladers))]
                    matches = optimize_match_order(matches)
                    
                    if is_odd_groups and i == num_groups - 1:
                        for m_idx, match in enumerate(matches):
                            match["judge"] = judges_pool[m_idx % 2]
                    else:
                        g_judge = judges_pool[i % 2]
                        for match in matches:
                            match["judge"] = g_judge
                            
                    groups.append({"id": f"group-{i}", "name": f"Grupo {chr(65 + i)}", "bladerIds": [b["id"] for b in group_bladers], "matches": matches})
                
                save_tournament({"id": str(int(time.time())), "name": name_input.value.strip() or "Torneio X", "date": datetime.now().strftime('%d/%m/%Y %H:%M'), "groups": groups, "status": "groups", "knockout": [], "participants": participants_snapshot, "advancing_per_group": int(dd_advances.value)})
                home_state["selected_ids"].clear()
                switch_home_tab("selecao") 
                tourn_state["sub_tab"] = "grupos"
                nav_to_tab("Torneio") 
            
            update_dist_ui()
            view_config_container.content = ft.Column([ft.Text("Passo 2: Definir Grupos e Vagas", size=14, color=C_TEXT_SEC), AppCard(ft.Column([name_input, ft.Text("Quantidade de Grupos: (Se falhar, clique no ícone 🔄)", color=C_TEXT_SEC, size=13), ft.Row([dd_groups, btn_refresh]), ft.Text("Avançam por Grupo (Mata-Mata):", color=C_TEXT_SEC, size=13), ft.Row([dd_advances]), ft.Divider(color=C_BORDER, height=20), ft.Text("Ajuste manual de vagas:", color=C_TEXT_SEC, size=13), dist_col, ft.Container(content=sum_text, alignment=ft.Alignment(0,0))], spacing=16)), ft.Row([SecondaryBtn("Voltar", lambda _: switch_home_tab("selecao"), expand=True), PrimaryBtn("Sortear e Criar", confirm_create, expand=True)], spacing=12)], scroll=ft.ScrollMode.AUTO)
            switch_home_tab("config")

        btn_criar = PrimaryBtn(f"Avançar para Passo 2 ({len(home_state['selected_ids'])})", open_config_view, width=float("inf"), icon=ft.Icons.ROCKET_LAUNCH)
        view_selecao = ft.Column([ft.Text("Passo 1: Marque os Bladers participantes", size=14, color=C_TEXT_SEC), ft.Container(content=selection_list_ui, expand=True), ft.Divider(color=C_BORDER, height=12), btn_criar])
        tab_nav_container = ft.Container()
        content_switcher = ft.Container(expand=True)

        def build_home_tab_row():
            is_c = home_state["sub_tab"] == "cadastro"
            is_s = home_state["sub_tab"] in ["selecao", "config"]
            tabs = [ft.Container(content=ft.Text("Banco Geral", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_c else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_c else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_home_tab("cadastro")), ft.Container(content=ft.Text("Criar Torneio", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_s else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_s else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_home_tab("selecao"))]
            tab_nav_container.content = ft.Container(content=ft.Row(tabs, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BORDER), border_radius=10, padding=4, margin=ft.margin.only(bottom=16))

        def switch_home_tab(tab_name):
            home_state["sub_tab"] = tab_name
            build_home_tab_row()
            if tab_name == "cadastro": content_switcher.content = view_cadastro
            elif tab_name == "selecao": content_switcher.content = view_selecao
            elif tab_name == "config": content_switcher.content = view_config_container
            page.update()

        switch_home_tab(home_state["sub_tab"])
        return ft.Container(padding=24, content=ft.Column([ft.Text("Gestão de Bladers", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), tab_nav_container, content_switcher]))

    # --- TELA 2: PARTIDA RÁPIDA ---
    def build_quick_match_view():
        active_match = get_active_match()
        is_tournament = active_match is not None

        can_judge = False
        if is_pro():
            can_judge = True
        elif is_judge():
            if is_tournament:
                can_judge = (active_match.get("judge") == get_username())
            else:
                can_judge = True 
        else: 
            if not is_tournament: 
                can_judge = True 

        state = {"p1_score": 0, "p2_score": 0, "p1_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "p2_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}, "match_ended": False}
        
        score_p1 = ft.Text("0", size=64, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI)
        score_p2 = ft.Text("0", size=64, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI)

        if is_tournament:
            p1_display = ft.Text(active_match.get("b1_name", ""), size=16, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, text_align="center", overflow=ft.TextOverflow.ELLIPSIS)
            p2_display = ft.Text(active_match.get("b2_name", ""), size=16, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, text_align="center", overflow=ft.TextOverflow.ELLIPSIS)
            get_p1_name = lambda: active_match.get("b1_name", "")
            get_p2_name = lambda: active_match.get("b2_name", "")
        else:
            p1_input = ft.TextField(value="Jogador 1", text_align=ft.TextAlign.CENTER, bgcolor="transparent", border_color="transparent", color=C_TEXT_PRI, text_size=16, content_padding=0, read_only=not can_judge)
            p2_input = ft.TextField(value="Jogador 2", text_align=ft.TextAlign.CENTER, bgcolor="transparent", border_color="transparent", color=C_TEXT_PRI, text_size=16, content_padding=0, read_only=not can_judge)
            p1_display, p2_display = p1_input, p2_input
            get_p1_name = lambda: p1_input.value.strip() or "Jogador 1"
            get_p2_name = lambda: p2_input.value.strip() or "Jogador 2"

        def process_win():
            if state["match_ended"]: return 
            state["match_ended"] = True
            winner = get_p1_name() if state["p1_score"] > state["p2_score"] else get_p2_name()
            
            def finish_match(e):
                hide_dialog(dlg)
                if is_tournament:
                    nav_to_tab("Torneio")
                    
                    def async_save_match():
                        safe_cloud_sync() 
                        tourn = get_tournament()
                        if not tourn: return
                        
                        w_id = active_match.get("b1_id") if state["p1_score"] > state["p2_score"] else active_match.get("b2_id")
                        loser_id = active_match.get("b2_id") if w_id == active_match.get("b1_id") else active_match.get("b1_id")
                        
                        if active_match.get("is_knockout"):
                            r_idx = active_match.get("round_idx")
                            m_idx = 0
                            for i, m in enumerate(tourn.get("knockout", [])[r_idx].get("matches", [])):
                                if m.get("id") == active_match.get("match_id"):
                                    m_idx = i
                                    m["completed"] = True
                                    m["result"] = {"blader1Result": {"bladerId": active_match.get("b1_id"), "totalPoints": state["p1_score"], "finishes": state["p1_finishes"]}, "blader2Result": {"bladerId": active_match.get("b2_id"), "totalPoints": state["p2_score"], "finishes": state["p2_finishes"]}, "winner": w_id}
                                    break
                            
                            if r_idx + 1 < len(tourn.get("knockout", [])):
                                next_m_idx = m_idx // 2
                                is_p1 = (m_idx % 2 == 0)
                                is_semi = (r_idx == len(tourn["knockout"]) - 2)
                                
                                if is_semi:
                                    if is_p1: tourn["knockout"][r_idx + 1]["matches"][0]["blader1"] = w_id
                                    else:     tourn["knockout"][r_idx + 1]["matches"][0]["blader2"] = w_id
                                    
                                    if len(tourn["knockout"][r_idx + 1]["matches"]) > 1:
                                        if is_p1: tourn["knockout"][r_idx + 1]["matches"][1]["blader1"] = loser_id
                                        else:     tourn["knockout"][r_idx + 1]["matches"][1]["blader2"] = loser_id
                                else:
                                    if is_p1: tourn["knockout"][r_idx + 1]["matches"][next_m_idx]["blader1"] = w_id
                                    else:     tourn["knockout"][r_idx + 1]["matches"][next_m_idx]["blader2"] = w_id
                        else:
                            for g in tourn.get("groups", []):
                                if g.get("id") == active_match.get("group_id"):
                                    for m in g.get("matches", []):
                                        if m.get("id") == active_match.get("match_id"):
                                            m["completed"] = True
                                            m["result"] = {"blader1Result": {"bladerId": active_match.get("b1_id"), "totalPoints": state["p1_score"], "finishes": state["p1_finishes"]}, "blader2Result": {"bladerId": active_match.get("b2_id"), "totalPoints": state["p2_score"], "finishes": state["p2_finishes"]}, "winner": w_id}
                        
                        save_tournament(tourn) 
                        set_active_match(None) 
                    threading.Thread(target=async_save_match, daemon=True).start()
                else:
                    reset()

            dlg = ft.AlertDialog(modal=True, bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text(f"🏆 Vitória de {winner}!", color=C_PRIMARY, weight=ft.FontWeight.BOLD), content=ft.Text("Partida concluída e computada.", color=C_TEXT_SEC), actions=[PrimaryBtn("Confirmar e Voltar", finish_match, width=float("inf"))])
            show_dialog(dlg)

        def add_points(player, pts, type_finish):
            if state["match_ended"] or not can_judge: return 
            if player == 1:
                state["p1_score"] += pts
                state["p1_finishes"][type_finish] += 1
                score_p1.value = str(state["p1_score"])
            else:
                state["p2_score"] += pts
                state["p2_finishes"][type_finish] += 1
                score_p2.value = str(state["p2_score"])
            page.update()
            if state["p1_score"] >= PTS_WIN_TARGET or state["p2_score"] >= PTS_WIN_TARGET: 
                process_win()

        def reset(e=None):
            if not can_judge: return
            state["p1_score"], state["p2_score"] = 0, 0
            state["p1_finishes"] = {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}
            state["p2_finishes"] = {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}
            state["match_ended"] = False
            score_p1.value, score_p2.value = "0", "0"
            page.update()

        def action_col(p):
            col = C_PRIMARY if can_judge else C_SURFACE_SEC
            def wrapper(pts, t):
                return lambda _: add_points(p, pts, t) if can_judge else None
            
            return ft.Column([
                PrimaryBtn(f"XTREME (+{PTS_MAP['xtreme']})", wrapper(PTS_MAP['xtreme'], "xtreme"), width=145, height=44, color=col),
                SecondaryBtn(f"BURST (+{PTS_MAP['burst']})", wrapper(PTS_MAP['burst'], "burst"), width=145, height=44),
                SecondaryBtn(f"OVER (+{PTS_MAP['over']})", wrapper(PTS_MAP['over'], "over"), width=145, height=44),
                SecondaryBtn(f"SPIN (+{PTS_MAP['spin']})", wrapper(PTS_MAP['spin'], "spin"), width=145, height=44),
                SecondaryBtn(f"FLAG (+{PTS_MAP['flag']})", wrapper(PTS_MAP['flag'], "flag"), width=145, height=44),
            ], spacing=12, alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        if is_tournament:
            header_txt = "ELIMINATÓRIAS" if active_match.get("is_knockout") else "FASE DE GRUPOS"
            header_col = C_ERROR if active_match.get("is_knockout") else C_PRIMARY
            if not can_judge:
                header_txt += f" (Visualizando - Apito: {active_match.get('judge')})"
                header_col = C_SURFACE_SEC
        else:
            header_txt = "PARTIDA CASUAL"
            header_col = C_SURFACE_SEC

        return ft.Container(
            padding=0,
            content=ft.Column([
                ft.Container(content=ft.Text(header_txt, color=C_TEXT_PRI if is_tournament else C_TEXT_SEC, weight=ft.FontWeight.W_600, size=13, text_align="center"), bgcolor=header_col if is_tournament else "transparent", padding=12, width=float("inf"), border=ft.border.only(bottom=ft.BorderSide(1, C_BORDER)) if not is_tournament else None),
                ft.Container(padding=24, expand=True, content=ft.Column([
                    ft.Row([ft.Column([p1_display, score_p1, action_col(1)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER), ft.Container(width=1, bgcolor=C_BORDER, height=300, margin=ft.margin.symmetric(horizontal=8)), ft.Column([p2_display, score_p2, action_col(2)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START),
                    ft.Container(expand=True), SecondaryBtn("Resetar Placar", reset, width=float("inf"), icon=ft.Icons.REFRESH) if can_judge else ft.Container()
                ]))
            ])
        )

    # --- TELA 3: TORNEIO ---
    def build_tournament_view():
        tourn = get_tournament()
        if not tourn: 
            return ft.Container(content=ft.Column([ft.Icon(ft.Icons.EMOJI_EVENTS_OUTLINED, size=64, color=C_BORDER), ft.Text("Nenhum torneio em andamento.", color=C_TEXT_SEC, size=16)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True, alignment=ft.Alignment(0,0))

        bladers_map = get_snapshot_map(tourn)
        
        if tourn_state["sub_tab"] is None:
            tourn_state["sub_tab"] = "matamata" if tourn.get("status") == "knockout" else "grupos"
            
        def open_admin_panel(e):
            if not is_pro():
                page.snack_bar = ft.SnackBar(ft.Text("Apenas admins/pro podem modificar a tabela."), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return
            safe_cloud_sync()
            fresh_tourn = get_tournament()
            in_tourn = [{"id": k, "name": v} for k, v in fresh_tourn.get("participants", {}).items()]
            all_bladers = get_bladers()
            out_tourn = [b for b in all_bladers if b["id"] not in fresh_tourn.get("participants", {})]

            dd_sai = ft.Dropdown(options=[ft.dropdown.Option(key=b["id"], text=b["name"]) for b in in_tourn], label="Quem saiu?", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI)
            if not out_tourn:
                content_ui = ft.Text("⚠️ Você não tem Reservas no Banco.", color=C_ERROR, size=14, text_align="center")
                actions_ui = [SecondaryBtn("Fechar", lambda _: hide_dialog(admin_dlg))]
            else:
                dd_entra = ft.Dropdown(options=[ft.dropdown.Option(key=b["id"], text=b["name"]) for b in out_tourn], label="Quem entra?", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI)
                content_ui = ft.Column([ft.Text("O reserva herda a vaga e os pontos de quem saiu.", color=C_TEXT_SEC, size=13), dd_sai, ft.Icon(ft.Icons.SWAP_VERT, color=C_PRIMARY), dd_entra], tight=True, horizontal_alignment="center")
                
                def perform_swap(e):
                    if not dd_sai.value or not dd_entra.value: return
                    id_sai, id_entra = dd_sai.value, dd_entra.value
                    nome_entra = next((b["name"] for b in out_tourn if b["id"] == id_entra), "Reserva")
                    
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
                    
                    save_tournament(fresh_tourn)
                    hide_dialog(admin_dlg)
                    refresh_current_tab()
                
                actions_ui = [SecondaryBtn("Cancelar", lambda _: hide_dialog(admin_dlg)), PrimaryBtn("Substituir", perform_swap)]

            admin_dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Troca Oficial", color=C_TEXT_PRI, weight=ft.FontWeight.BOLD), content=content_ui, actions=actions_ui)
            show_dialog(admin_dlg)

        def get_group_standings(group):
            standings = {b_id: {"id": b_id, "name": bladers_map.get(b_id, "Blader Removido"), "j":0, "v":0, "d":0, "pf":0, "ps":0, "saldo":0, "xtreme":0} for b_id in group.get("bladerIds", [])}
            for match in group.get("matches", []):
                if match.get("completed"):
                    res = match.get("result", {})
                    b1, b2, w = res.get("blader1Result", {}), res.get("blader2Result", {}), res.get("winner")
                    if not b1 or not b2: continue
                    for bx, bx_data in [(b1, standings.get(b1.get("bladerId"))), (b2, standings.get(b2.get("bladerId")))]:
                        if bx_data is None: continue
                        bx_data["j"] += 1; bx_data["pf"] += bx.get("totalPoints", 0); bx_data["xtreme"] += bx.get("finishes", {}).get("xtreme", 0)
                        if w == bx.get("bladerId"): bx_data["v"] += 1
                        else: bx_data["d"] += 1
                    if standings.get(b1.get("bladerId")): standings[b1["bladerId"]]["ps"] += b2.get("totalPoints", 0)
                    if standings.get(b2.get("bladerId")): standings[b2["bladerId"]]["ps"] += b1.get("totalPoints", 0)
            
            for s in standings.values(): s["saldo"] = s["pf"] - s["ps"]
            return sorted(standings.values(), key=lambda x: (x["saldo"], x["xtreme"], x["pf"]), reverse=True)

        def advance_to_knockout(e):
            if not is_pro(): return
            safe_cloud_sync() 
            fresh_tourn = get_tournament()
            
            for g in fresh_tourn.get("groups", []):
                if not all(m.get("completed") for m in g.get("matches", [])):
                    page.snack_bar = ft.SnackBar(ft.Text(f"⚠️ Finalize todas as partidas do {g.get('name', 'Grupo')} antes de avançar!"), bgcolor=C_ERROR); page.snack_bar.open = True; page.update(); return

            adv_per_group = int(fresh_tourn.get("advancing_per_group", 2))
            
            seeded_players = []
            for pos in range(adv_per_group):
                for g in fresh_tourn.get("groups", []):
                    st = get_group_standings(g)
                    if pos < len(st):
                        seeded_players.append(st[pos]["id"])
            
            n = len(seeded_players)
            if n < 2: return 
            
            p2 = 1
            while p2 < n: p2 *= 2
            
            padded = seeded_players + [None] * (p2 - n)
            
            def get_seeds(size):
                if size == 1: return [0]
                half = get_seeds(size // 2)
                res = []
                for x in half: res.append(x); res.append(size - 1 - x)
                return res
                
            order = get_seeds(p2)
            ordered_players = [padded[i] for i in order]
            
            knockout = []
            rounds = int(math.log2(p2))
            round_names = {1: "Grande Final", 2: "Semifinais", 3: "Quartas de Final", 4: "Oitavas de Final", 5: "16 avos"}
            
            judges_pool = ["juiz_1", "juiz_2"]
            curr_matches = []
            for i in range(0, p2, 2):
                p1 = ordered_players[i]
                p2_id = ordered_players[i+1]
                is_bye = p1 is None or p2_id is None
                winner = p1 if p2_id is None else p2_id if p1 is None else None
                
                m = {
                    "id": f"r0-m{i//2}-{int(time.time()*1000)}", "blader1": p1, "blader2": p2_id, "completed": is_bye, "judge": random.choice(judges_pool)
                }
                if is_bye and winner is not None:
                    m["result"] = {"blader1Result": {"bladerId": p1, "totalPoints": 0, "finishes": {}}, "blader2Result": {"bladerId": p2_id, "totalPoints": 0, "finishes": {}}, "winner": winner}
                curr_matches.append(m)
                
            knockout.append({"name": round_names.get(rounds, f"Rodada {1}"), "matches": curr_matches})
            
            for r in range(1, rounds):
                next_matches = []
                prev_matches = knockout[r-1].get("matches", [])
                for i in range(len(prev_matches) // 2):
                    m1 = prev_matches[i*2]
                    m2 = prev_matches[i*2 + 1]
                    b1 = m1.get("result", {}).get("winner") if m1.get("completed") else None
                    b2 = m2.get("result", {}).get("winner") if m2.get("completed") else None
                    
                    next_matches.append({"id": f"r{r}-m{i}-{int(time.time()*1000)}", "blader1": b1, "blader2": b2, "completed": False, "judge": random.choice(judges_pool)})
                knockout.append({"name": round_names.get(rounds - r, f"Rodada {r+1}"), "matches": next_matches})

            if rounds >= 2:
                knockout[-1]["matches"].append({
                    "id": f"r{rounds-1}-m1-{int(time.time()*1000)}", "name": "Disputa de 3º Lugar", "blader1": None, "blader2": None, "completed": False, "judge": random.choice(judges_pool)
                })

            fresh_tourn["knockout"] = knockout
            fresh_tourn["status"] = "knockout"
            save_tournament(fresh_tourn)
            
            tourn_state["sub_tab"] = "matamata"
            refresh_current_tab()

        view_grupos = ft.ListView(expand=True, spacing=16, padding=ft.padding.only(top=16))
        view_partidas = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))
        view_matamata = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))

        def go_to_match(e):
            set_active_match(e.control.data)
            nav_to_tab("Combate")

        def get_match_action_ui(match_data, b1_n, b2_n, is_ko=False, r_idx=0):
            if match_data.get("completed"):
                res = match_data.get("result", {})
                if match_data.get("blader1") is None or match_data.get("blader2") is None:
                    return ft.Text("Avançou (W.O.)", color=C_TEXT_SEC, size=12)
                pts1 = res.get("blader1Result", {}).get("totalPoints", 0)
                pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                return ft.Row([ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=match_data: open_match_details(md, tourn))])
            else:
                if is_ko and (match_data.get("blader1") is None or match_data.get("blader2") is None):
                    return ft.Text("Aguardando...", color=C_TEXT_SEC, size=12)
                
                assigned_judge = match_data.get("judge")
                if is_pro() or (is_judge() and assigned_judge == get_username()):
                    action_data = {"is_knockout": is_ko, "round_idx": r_idx, "match_id": match_data.get("id"), "group_id": match_data.get("groupId"), "b1_id": match_data.get("blader1"), "b1_name": b1_n, "b2_id": match_data.get("blader2"), "b2_name": b2_n, "judge": assigned_judge}
                    return PrimaryBtn("Jogar", go_to_match, height=36, width=80, data=action_data)
                else:
                    return ft.Row([ft.Icon(ft.Icons.LOCK, size=14, color=C_TEXT_SEC), ft.Text(f"Apito: {assigned_judge or 'Admin'}", color=C_TEXT_SEC, size=11)])

        for group in tourn.get("groups", []):
            sorted_st = get_group_standings(group)
            g_col = ft.Column([ft.Text(group.get("name", "Grupo"), size=16, weight=ft.FontWeight.W_600, color=C_TEXT_PRI)])
            
            g_col.controls.append(ft.Container(content=ft.Row([
                ft.Text("#", width=20, size=12, color=C_TEXT_SEC), ft.Text("Blader", expand=True, size=12, color=C_TEXT_SEC), ft.Text("J", width=25, size=12, color=C_TEXT_SEC, text_align="center"), ft.Text("V", width=25, size=12, color=C_TEXT_SEC, text_align="center"), ft.Text("PF", width=25, size=12, color=C_TEXT_SEC, text_align="center"), ft.Text("Sld", width=30, size=12, color=C_TEXT_SEC, text_align="center")
            ]), padding=8, border=ft.border.only(bottom=ft.BorderSide(1, C_BORDER))))
            
            adv_limit = int(tourn.get("advancing_per_group", 2))
            
            for idx, st in enumerate(sorted_st):
                is_top = idx < adv_limit 
                g_col.controls.append(ft.Container(content=ft.Row([
                    ft.Text(str(idx+1), width=20, size=14, color=C_TEXT_PRI if is_top else C_TEXT_SEC, weight=ft.FontWeight.W_600 if is_top else ft.FontWeight.NORMAL), ft.Text(st["name"], expand=True, size=14, color=C_TEXT_PRI, overflow=ft.TextOverflow.ELLIPSIS), ft.Text(str(st["j"]), width=25, size=14, color=C_TEXT_SEC, text_align="center"), ft.Text(str(st["v"]), width=25, size=14, color=C_TEXT_SEC, text_align="center"), ft.Text(str(st["pf"]), width=25, size=14, color=C_TEXT_SEC, text_align="center"), ft.Text(str(st["saldo"]), width=30, size=14, color=C_SUCCESS if st["saldo"] > 0 else C_ERROR, text_align="center", weight=ft.FontWeight.W_500)
                ]), padding=8, bgcolor=C_SURFACE_SEC if is_top else "transparent", border_radius=8))
            view_grupos.controls.append(AppCard(g_col))

            view_partidas.controls.append(ft.Text(group.get("name", ""), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC, margin=ft.margin.only(top=8)))
            
            for match in group.get("matches", []):
                b1_name = bladers_map.get(match.get("blader1"), "Blader Removido")
                b2_name = bladers_map.get(match.get("blader2"), "Blader Removido")
                status_ui = get_match_action_ui(match, b1_name, b2_name)
                view_partidas.controls.append(AppCard(ft.Row([ft.Column([ft.Text(b1_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI), ft.Text("vs", size=10, color=C_TEXT_SEC), ft.Text(b2_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI)]), status_ui], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

        if tourn.get("status") == "groups" and is_pro():
            view_grupos.controls.append(PrimaryBtn("Avançar para Mata-Mata", advance_to_knockout, width=float("inf")))
        
        if tourn.get("knockout"):
            for r_idx, round_data in enumerate(tourn.get("knockout", [])):
                view_matamata.controls.append(ft.Text(round_data.get("name", ""), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC, margin=ft.margin.only(top=8)))
                for match in round_data.get("matches", []):
                    b1_id = match.get("blader1")
                    b2_id = match.get("blader2")
                    b1_name = bladers_map.get(b1_id, "A definir") if b1_id else "A definir"
                    b2_name = bladers_map.get(b2_id, "A definir") if b2_id else "A definir"
                    
                    match_title = match.get("name")
                    if match_title: view_matamata.controls.append(ft.Text(match_title, size=12, color=C_PRIMARY, text_align="center"))

                    status_ui = get_match_action_ui(match, b1_name, b2_name, is_ko=True, r_idx=r_idx)
                    view_matamata.controls.append(AppCard(ft.Row([ft.Column([ft.Text(b1_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI), ft.Text("vs", size=10, color=C_TEXT_SEC), ft.Text(b2_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI)]), status_ui], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

        tab_nav_container = ft.Container(padding=ft.padding.symmetric(horizontal=24))
        content_switcher = ft.Container(content=view_matamata if tourn_state["sub_tab"] == "matamata" else (view_partidas if tourn_state["sub_tab"] == "partidas" else view_grupos), expand=True)

        def build_tab_row():
            is_g = tourn_state["sub_tab"] == "grupos"
            is_p = tourn_state["sub_tab"] == "partidas"
            is_m = tourn_state["sub_tab"] == "matamata"

            tabs = [
                ft.Container(content=ft.Text("Grupos", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_g else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_g else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_sub_tab("grupos")),
                ft.Container(content=ft.Text("Partidas", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_p else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_p else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_sub_tab("partidas"))
            ]
            if tourn.get("status") == "knockout":
                tabs.append(ft.Container(content=ft.Text("Mata-Mata", size=13, weight=ft.FontWeight.W_600, color=C_PRIMARY if is_m else C_TEXT_SEC), expand=True, bgcolor=f"{C_PRIMARY}15" if is_m else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_sub_tab("matamata")))
            
            tab_nav_container.content = ft.Container(content=ft.Row(tabs, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BORDER), border_radius=10, padding=4)

        def switch_sub_tab(tab_name):
            tourn_state["sub_tab"] = tab_name; build_tab_row()
            if tab_name == "grupos": content_switcher.content = view_grupos
            elif tab_name == "partidas": content_switcher.content = view_partidas
            elif tab_name == "matamata": content_switcher.content = view_matamata
            page.update()

        build_tab_row() 

        def prompt_end_tourn(e):
            if not is_pro(): return
            def handle_action(action):
                safe_cloud_sync() 
                if action == "salvar": add_to_history(tourn)
                save_tournament(None); set_active_match(None)
                hide_dialog(dlg); refresh_current_tab()

            dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Encerrar Torneio", color=C_TEXT_PRI, size=18, weight=ft.FontWeight.BOLD), content=ft.Text("O que deseja fazer com os dados?", color=C_TEXT_SEC, size=14), actions=[SecondaryBtn("Excluir", lambda _: handle_action("excluir")), PrimaryBtn("Salvar no Histórico", lambda _: handle_action("salvar"))])
            show_dialog(dlg)
            
        def manual_refresh(e):
            def _do_refresh():
                safe_cloud_sync()
                refresh_current_tab()
            threading.Thread(target=_do_refresh, daemon=True).start()

        actions_row = [IconButton(ft.Icons.REFRESH, manual_refresh, color=C_PRIMARY)]
        if is_pro():
            actions_row.extend([IconButton(ft.Icons.SWAP_HORIZ, open_admin_panel, color=C_PRIMARY), IconButton(ft.Icons.POWER_SETTINGS_NEW, prompt_end_tourn, color=C_ERROR)])

        return ft.Container(
            padding=0,
            content=ft.Column([
                ft.Container(content=ft.Row([
                    ft.Column([ft.Text(tourn.get("name",""), size=20, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), ft.Text("Em andamento", size=12, color=C_PRIMARY)], spacing=0),
                    ft.Row(actions_row)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=24),
                tab_nav_container,
                ft.Container(content=content_switcher, padding=ft.padding.symmetric(horizontal=24), expand=True)
            ])
        )

    # --- TELA 4: HISTÓRICO ---
    def build_history_view():
        if history_state["active_tourn"]:
            t_data = history_state["active_tourn"]
            bladers_map = get_snapshot_map(t_data) 
            
            stats = {}
            def process_stats(m):
                if m.get("completed"):
                    res = m.get("result", {}); w = res.get("winner")
                    for b_key in ["blader1Result", "blader2Result"]:
                        b_res = res.get(b_key, {}); bid = b_res.get("bladerId")
                        if not bid: continue
                        if bid not in stats:
                            stats[bid] = {"name": bladers_map.get(bid, "Blader Removido"), "j":0, "v":0, "pts":0, "spin":0, "over":0, "burst":0, "xtreme":0, "flag":0}
                        stats[bid]["j"] += 1; stats[bid]["pts"] += b_res.get("totalPoints", 0)
                        f_data = b_res.get("finishes", {})
                        stats[bid]["spin"] += f_data.get("spin", 0); stats[bid]["over"] += f_data.get("over", 0)
                        stats[bid]["burst"] += f_data.get("burst", 0); stats[bid]["xtreme"] += f_data.get("xtreme", 0)
                        stats[bid]["flag"] += f_data.get("flag", 0)
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
                        res = m.get("result", {}); 
                        b1_n = bladers_map.get(m.get("blader1"), "Blader Removido")
                        b2_n = bladers_map.get(m.get("blader2"), "Blader Removido")
                        pts1 = res.get("blader1Result", {}).get("totalPoints", 0)
                        pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                        status_ui = ft.Row([ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=m: open_match_details(md, t_data))])
                        view_tabelas.controls.append(AppCard(ft.Row([ft.Text(b1_n, size=14, color=C_TEXT_PRI), status_ui, ft.Text(b2_n, size=14, color=C_TEXT_PRI)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))
            
            for r in t_data.get("knockout", []):
                view_tabelas.controls.append(ft.Text(r.get("name", ""), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC, margin=ft.margin.only(top=8)))
                for match in r.get("matches", []):
                    match_title = match.get("name")
                    if match_title: view_tabelas.controls.append(ft.Text(match_title, size=12, color=C_PRIMARY, text_align="center"))
                    
                    b1_id = match.get("blader1")
                    b2_id = match.get("blader2")
                    b1_name = bladers_map.get(b1_id, "A definir") if b1_id else "A definir"
                    b2_name = bladers_map.get(b2_id, "A definir") if b2_id else "A definir"

                    if match.get("completed"):
                        res = match.get("result", {})
                        if b1_id is None or b2_id is None: status_ui = ft.Text("Avançou (W.O.)", color=C_TEXT_SEC, size=12)
                        else:
                            pts1 = res.get("blader1Result", {}).get("totalPoints", 0)
                            pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                            status_ui = ft.Row([ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=match: open_match_details(md, t_data))])
                        view_tabelas.controls.append(AppCard(ft.Row([ft.Text(b1_name, size=14, color=C_TEXT_PRI), status_ui, ft.Text(b2_name, size=14, color=C_TEXT_PRI)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

            view_stats = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))
            for st in sorted_stats:
                view_stats.controls.append(AppCard(ft.Column([ft.Row([ft.Text(st["name"], weight=ft.FontWeight.BOLD, size=16, color=C_TEXT_PRI, expand=True), ft.Text(f"{st['pts']} Pts", weight=ft.FontWeight.BOLD, size=16, color=C_PRIMARY)]), ft.Text(f"{st['v']} Vitórias em {st['j']} Jogos", size=12, color=C_TEXT_SEC), ft.Container(height=4), ft.Row([Badge(f"XT: {st['xtreme']}", C_XTREME), Badge(f"BU: {st['burst']}", C_BURST), Badge(f"OV: {st['over']}", C_OVER), Badge(f"SP: {st['spin']}", C_SPIN), Badge(f"FL: {st['flag']}", C_FLAG)], spacing=6, wrap=True)], spacing=4), padding=16))

            hist_nav_container = ft.Container(padding=ft.padding.symmetric(horizontal=24))
            content_switcher = ft.Container(content=view_tabelas if history_state["sub_tab"] == "tabelas" else view_stats, expand=True)

            def build_hist_tab_row():
                is_t = history_state["sub_tab"] == "tabelas"
                tabs = [ft.Container(content=ft.Text("Chaves", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_t else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_t else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_det_tab("tabelas")), ft.Container(content=ft.Text("Estatísticas", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if not is_t else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if not is_t else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_det_tab("estatisticas"))]
                hist_nav_container.content = ft.Container(content=ft.Row(tabs, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BORDER), border_radius=10, padding=4)

            def switch_det_tab(tab_name):
                history_state["sub_tab"] = tab_name; build_hist_tab_row()
                content_switcher.content = view_tabelas if tab_name == "tabelas" else view_stats; page.update()
                
            build_hist_tab_row()

            def close_detail(e): history_state["active_tourn"] = None; refresh_current_tab()

            return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Row([IconButton(ft.Icons.ARROW_BACK, close_detail), ft.Text(t_data.get("name", ""), size=18, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI, expand=True, text_align="right")]), padding=24), hist_nav_container, ft.Container(content=content_switcher, padding=ft.padding.symmetric(horizontal=24), expand=True)]))

        hist = get_history()
        if not hist: return ft.Container(content=ft.Column([ft.Icon(ft.Icons.HISTORY, size=64, color=C_BORDER), ft.Text("Histórico vazio.", color=C_TEXT_SEC, size=16)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True, alignment=ft.Alignment(0,0))

        list_ui = ft.ListView(expand=True, spacing=12, padding=24)
        list_ui.controls.append(ft.Text("Torneios Anteriores", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI, margin=ft.margin.only(bottom=8)))
        def open_history_detail(t_data): history_state["active_tourn"] = t_data; history_state["sub_tab"] = "tabelas"; refresh_current_tab()
        for t in hist: list_ui.controls.append(AppCard(ft.Row([ft.Column([ft.Text(t.get("name", ""), weight=ft.FontWeight.W_600, size=16, color=C_TEXT_PRI), ft.Text(f"{t.get('date', '')}", size=12, color=C_TEXT_SEC)], spacing=2, expand=True), ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C_BORDER)]), padding=16, on_click=lambda e, data=t: open_history_detail(data)))
        return ft.Container(content=list_ui, expand=True)

    # --- TELA 5: PAINEL ADMIN MAX (COM PESQUISA E BOTÃO DE SALVAR) ---
    def build_admin_view():
        if not is_admin_max():
            return ft.Container(content=ft.Text("Acesso Negado.", color=C_ERROR), padding=24)
            
        users_db = get_users()
        admin_state = {"search_query": ""}
        
        search_input = ft.TextField(
            hint_text="Buscar usuário...", 
            prefix_icon=ft.Icons.SEARCH,
            bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12,
            content_padding=10
        )
        
        users_list_ui = ft.ListView(expand=True, spacing=12)

        def render_users():
            users_list_ui.controls.clear()
            query = admin_state["search_query"].lower()

            for u_name, u_data in users_db.items():
                if query and query not in u_name.lower():
                    continue 

                role_dd = ft.Dropdown(
                    value=u_data.get('role', 'basic'),
                    options=[
                        ft.dropdown.Option("basic", "Básico"),
                        ft.dropdown.Option("pro", "Pro"),
                        ft.dropdown.Option("judge", "Juiz")
                    ],
                    width=120, height=40, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, text_size=12
                )

                # 👑 AÇÃO CONGELADA EM LAMBDA (Garante que salve o usuário certo)
                def save_user_role(e, un=u_name, dd=role_dd):
                    safe_cloud_sync()
                    db = get_users()
                    if un in db:
                        db[un]["role"] = dd.value
                        save_users(db)
                        users_db[un]["role"] = dd.value # Atualiza visual local
                        page.snack_bar = ft.SnackBar(ft.Text(f"Cargo de {un} salvo com sucesso!"), bgcolor=C_SUCCESS)
                        page.snack_bar.open = True
                        page.update()

                def delete_user(e, un=u_name):
                    def confirm(e):
                        safe_cloud_sync()
                        db = get_users()
                        if un in db: del db[un]
                        save_users(db)
                        hide_dialog(dlg)
                        refresh_current_tab()
                    dlg = ft.AlertDialog(bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Excluir", color=C_TEXT_PRI), content=ft.Text(f"Deletar usuário '{un}'?", color=C_TEXT_SEC), actions=[SecondaryBtn("Cancelar", lambda _: hide_dialog(dlg)), PrimaryBtn("Excluir", confirm, color=C_ERROR)])
                    show_dialog(dlg)

                btn_save = IconButton(ft.Icons.SAVE, lambda e, un=u_name, dd=role_dd: save_user_role(e, un, dd), color=C_SUCCESS, tooltip="Salvar Cargo")
                btn_del = IconButton(ft.Icons.DELETE, lambda e, un=u_name: delete_user(e, un), color=C_ERROR, tooltip="Excluir Usuário")

                users_list_ui.controls.append(AppCard(ft.Row([
                    ft.Text(u_name, weight=ft.FontWeight.W_600, size=16, color=C_TEXT_PRI, expand=True),
                    role_dd,
                    btn_save,
                    btn_del
                ]), padding=12))

            if not users_list_ui.controls:
                users_list_ui.controls.append(ft.Text("Nenhum usuário encontrado.", color=C_TEXT_SEC))
            
            page.update()

        def on_search_change(e):
            admin_state["search_query"] = e.control.value
            render_users()
            
        search_input.on_change = on_search_change
        render_users() # Chamada inicial

        return ft.Container(
            padding=24,
            content=ft.Column([
                ft.Text("Gerenciamento de Usuários", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI),
                search_input,
                ft.Container(height=8),
                ft.Container(content=users_list_ui, expand=True)
            ])
        )

    # ==========================================
    # LÓGICA DE NAVEGAÇÃO DINÂMICA
    # ==========================================
    content_area = ft.Container(expand=True)

    TABS_MAP = {
        "Bladers": build_home_view,
        "Combate": build_quick_match_view,
        "Torneio": build_tournament_view,
        "Histórico": build_history_view,
        "Admin": build_admin_view,
        "Perfil": build_profile_view 
    }

    def change_tab_programmatic(index):
        if not bottom_nav.destinations: return
        selected_label = bottom_nav.destinations[index].label
        content_area.content = None
        page.update()
        build_func = TABS_MAP.get(selected_label)
        if build_func: content_area.content = build_func()
        page.update()

    def nav_to_tab(tab_label):
        for i, dest in enumerate(bottom_nav.destinations):
            if dest.label == tab_label:
                bottom_nav.selected_index = i
                bottom_nav.update() 
                change_tab_programmatic(i)
                break

    def change_tab(e): 
        try: new_idx = int(e.data) 
        except: new_idx = e.control.selected_index
        bottom_nav.selected_index = new_idx
        bottom_nav.update()
        change_tab_programmatic(new_idx)
    
    def refresh_current_tab(): 
        if bottom_nav.visible and bottom_nav.destinations:
            change_tab_programmatic(bottom_nav.selected_index)

    def start_main_app():
        login_container.visible = False
        main_app_container.visible = True
        bottom_nav.visible = True
        
        role = app_state["current_user"]["role"]
        dests = []
        
        if role in ["admin_max", "pro"]:
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.PEOPLE_OUTLINE, label="Bladers"))
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.FLASH_ON_OUTLINED, label="Combate"))
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.EMOJI_EVENTS_OUTLINED, label="Torneio"))
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.HISTORY_OUTLINED, label="Histórico"))
            if role == "admin_max":
                dests.append(ft.NavigationBarDestination(icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED, label="Admin"))
        elif role == "judge":
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.FLASH_ON_OUTLINED, label="Combate"))
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.EMOJI_EVENTS_OUTLINED, label="Torneio"))
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.HISTORY_OUTLINED, label="Histórico"))
        else: 
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.FLASH_ON_OUTLINED, label="Combate"))
            dests.append(ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINE, label="Perfil"))
            
        bottom_nav.destinations = dests
        bottom_nav.selected_index = 0
        bottom_nav.on_change = change_tab
        page.update()
        change_tab_programmatic(0)

    main_app_container.content = ft.Column([content_area], expand=True)
    page.add(login_container, main_app_container, bottom_nav)

    # ==========================================
    # 🔄 MOTOR DE ATUALIZAÇÃO SIMULTÂNEA OTIMIZADO
    # ==========================================
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
                            local_ts = app_data.get("last_updated", 0)
                            remote_ts = nuvem.get("last_updated", 0)
                            
                            if remote_ts > local_ts:
                                app_data.clear()
                                app_data.update(nuvem)
                                if "users" not in app_data: app_data["users"] = {}
                                if "last_updated" not in app_data: app_data["last_updated"] = 0
                                needs_refresh = True
                            else:
                                needs_refresh = False
                                
                        if needs_refresh and bottom_nav.destinations:
                            current_label = bottom_nav.destinations[bottom_nav.selected_index].label
                            if current_label != "Bladers":
                                refresh_current_tab()
            except Exception:
                pass 

    threading.Thread(target=auto_sync_loop, daemon=True).start()

ft.run(main)
