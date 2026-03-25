import flet as ft
import time
import math
import json
import threading 
import requests  
import random # 🎲 Biblioteca de sorteio importada!
from datetime import datetime

# ==========================================
# 1. DESIGN SYSTEM - PALETA CLEAN PREMIUM
# ==========================================
C_BG = "#0B0B0F"          
C_SURFACE = "#15161A"     
C_SURFACE_SEC = "#1C1D22" 
C_BORDER = "#2A2C33"      
C_TEXT_PRI = "#F5F7FA"    
C_TEXT_SEC = "#A7ADB7"    
C_PRIMARY = "#FF7A00"     
C_PRIMARY_HOVER = "#FF9326" 
C_SUCCESS = "#22C55E"
C_ERROR = "#EF4444"

C_XTREME = C_PRIMARY
C_BURST = "#A855F7"       
C_OVER = "#3B82F6"        
C_SPIN = "#22C55E"        
C_FLAG = "#EAB308"        

# ==========================================
# 2. BASE DE DADOS (MOTOR DA NUVEM)
# ==========================================
FIREBASE_URL = "https://beybladeapp-c303a-default-rtdb.firebaseio.com/beyblade_data.json"

app_data = {"bladers": [], "tournament": None, "active_match": None, "history": []}
is_syncing = False 

def safe_cloud_sync():
    try:
        res = requests.get(FIREBASE_URL, timeout=5)
        if res.status_code == 200 and res.json() is not None:
            app_data.clear()
            app_data.update(res.json())
    except:
        pass

def load_db():
    safe_cloud_sync()
    return app_data

def save_db(data):
    global is_syncing
    is_syncing = True
    def _background_save(dados_para_salvar):
        global is_syncing
        for _ in range(3):
            try:
                res = requests.put(FIREBASE_URL, json=dados_para_salvar, timeout=5)
                if res.status_code == 200: break
            except:
                time.sleep(1.5)
        is_syncing = False

    dados_copia = json.loads(json.dumps(data))
    threading.Thread(target=_background_save, args=(dados_copia,), daemon=True).start()

load_db()

def get_bladers(): return app_data.get("bladers", [])
def save_bladers(bladers_list): 
    app_data["bladers"] = bladers_list; save_db(app_data)
def get_tournament(): return app_data.get("tournament")
def save_tournament(tourn_data):
    app_data["tournament"] = tourn_data; save_db(app_data)
def get_active_match(): return app_data.get("active_match")
def set_active_match(match_data):
    app_data["active_match"] = match_data; save_db(app_data)
def get_history(): return app_data.get("history", [])
def add_to_history(tourn_data):
    hist = get_history(); hist.insert(0, tourn_data)
    app_data["history"] = hist; save_db(app_data)

# ==========================================
# 3. COMPONENTES UI
# ==========================================
def AppCard(content, padding=16, on_click=None, data=None):
    return ft.Container(
        content=content, padding=padding, bgcolor=C_SURFACE,
        border_radius=16, border=ft.border.all(1, C_BORDER),
        on_click=on_click, data=data
    )

def PrimaryBtn(text, on_click, width=None, height=48, icon=None, data=None, color=C_PRIMARY, expand=False):
    items = []
    if icon: items.append(ft.Icon(icon, color=C_TEXT_PRI, size=20))
    items.append(ft.Text(text, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, size=14))
    return ft.Container(
        content=ft.Row(items, alignment=ft.MainAxisAlignment.CENTER, spacing=8) if icon else items[0],
        bgcolor=color, padding=8,
        border_radius=12, alignment=ft.Alignment(0, 0), width=width, height=height,
        on_click=on_click, data=data, expand=expand
    )

def SecondaryBtn(text, on_click, width=None, height=48, icon=None, data=None, expand=False):
    items = []
    if icon: items.append(ft.Icon(icon, color=C_TEXT_SEC, size=20))
    items.append(ft.Text(text, color=C_TEXT_SEC, weight=ft.FontWeight.W_500, size=13))
    return ft.Container(
        content=ft.Row(items, alignment=ft.MainAxisAlignment.CENTER, spacing=8) if icon else items[0],
        bgcolor=C_SURFACE_SEC, padding=8,
        border_radius=12, border=ft.border.all(1, C_BORDER),
        alignment=ft.Alignment(0, 0), width=width, height=height,
        on_click=on_click, data=data, expand=expand
    )

def IconButton(icon, on_click, color=C_TEXT_SEC):
    return ft.Container(
        content=ft.Icon(icon, color=color, size=22),
        padding=10, border_radius=10, bgcolor=C_SURFACE_SEC,
        border=ft.border.all(1, C_BORDER), on_click=on_click
    )

def Badge(text, color):
    return ft.Container(
        content=ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=color),
        padding=6,
        bgcolor=f"{color}15", border_radius=6, border=ft.border.all(1, f"{color}40")
    )

# ==========================================
# 4. O APLICATIVO PRINCIPAL
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

    history_state = {"active_tourn": None, "sub_tab": "tabelas"}
    home_state = {"sub_tab": "cadastro", "selected_ids": []}

    def show_dialog(dlg):
        if dlg not in page.overlay: page.overlay.append(dlg)
        dlg.open = True; page.update()

    def hide_dialog(dlg):
        dlg.open = False; page.update()

    def get_snapshot_map(tourn_data):
        b_map = {b["id"]: b["name"] for b in get_bladers()}
        if tourn_data and "participants" in tourn_data:
            b_map.update(tourn_data["participants"])
        return b_map

    def open_match_details(m_data, tourn_context=None):
        b_map = get_snapshot_map(tourn_context)
        res = m_data.get("result", {})
        b1_name = b_map.get(m_data.get("blader1"), "Blader Removido")
        b2_name = b_map.get(m_data.get("blader2"), "Blader Removido")
        f1 = res.get("blader1Result", {}).get("finishes", {})
        f2 = res.get("blader2Result", {}).get("finishes", {})

        def f_row(label, key, color):
            return ft.Row([
                ft.Text(str(f1.get(key, 0)), color=color, weight=ft.FontWeight.BOLD, size=16, width=30, text_align="center"),
                ft.Text(label, color=C_TEXT_SEC, expand=True, text_align="center", size=13),
                ft.Text(str(f2.get(key, 0)), color=color, weight=ft.FontWeight.BOLD, size=16, width=30, text_align="center"),
            ])

        dlg = ft.AlertDialog(
            bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), content_padding=24,
            title=ft.Text("Raio-X da Partida", color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, size=18, text_align="center"),
            content=ft.Column([
                ft.Row([
                    ft.Text(b1_name, weight=ft.FontWeight.W_600, color=C_TEXT_PRI, expand=True, text_align="center", size=14),
                    ft.Text("VS", size=11, color=C_TEXT_SEC),
                    ft.Text(b2_name, weight=ft.FontWeight.W_600, color=C_TEXT_PRI, expand=True, text_align="center", size=14),
                ]),
                ft.Divider(color=C_BORDER, height=20),
                f_row("XTREME", "xtreme", C_XTREME),
                f_row("BURST", "burst", C_BURST),
                f_row("OVER", "over", C_OVER),
                f_row("SPIN", "spin", C_SPIN),
                f_row("FLAG", "flag", C_FLAG),
                ft.Divider(color=C_BORDER, height=20),
                ft.Row([
                    ft.Text(str(res.get("blader1Result", {}).get("totalPoints", 0)), size=24, color=C_PRIMARY, weight=ft.FontWeight.BOLD, width=30, text_align="center"),
                    ft.Text("PONTOS", color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, expand=True, text_align="center", size=14),
                    ft.Text(str(res.get("blader2Result", {}).get("totalPoints", 0)), size=24, color=C_PRIMARY, weight=ft.FontWeight.BOLD, width=30, text_align="center"),
                ])
            ], tight=True),
            actions=[SecondaryBtn("Fechar", lambda _: hide_dialog(dlg))]
        )
        show_dialog(dlg)

    # --- TELA 1: INÍCIO (BLADERS + CONFIGURAÇÃO NATIVA) ---
    def build_home_view():
        bladers = get_bladers()
        
        blader_input = ft.TextField(
            hint_text="Nome do Blader...", expand=True, bgcolor=C_SURFACE_SEC, 
            border_color=C_BORDER, color=C_TEXT_PRI, text_size=14, border_radius=12,
            content_padding=16, cursor_color=C_PRIMARY
        )
        
        def add_blader(e):
            if blader_input.value.strip():
                safe_cloud_sync() 
                b_list = get_bladers()
                b_list.append({"id": str(int(time.time())), "name": blader_input.value.strip()})
                save_bladers(b_list)
                blader_input.value = ""
                refresh_current_tab()

        def remove_blader(b_id):
            safe_cloud_sync() 
            if b_id in home_state["selected_ids"]:
                home_state["selected_ids"].remove(b_id)
            save_bladers([b for b in get_bladers() if b["id"] != b_id])
            refresh_current_tab()

        bladers_list_ui = ft.ListView(expand=True, spacing=12)
        for b in bladers:
            bladers_list_ui.controls.append(
                AppCard(ft.Row([
                    ft.Text(b["name"], weight=ft.FontWeight.W_500, color=C_TEXT_PRI, size=15, expand=True),
                    IconButton(ft.Icons.DELETE_OUTLINE, lambda e, bid=b["id"]: remove_blader(bid), color=C_ERROR)
                ]), padding=12)
            )

        view_cadastro = ft.Column([
            ft.Text("Adicionar Participantes", size=14, color=C_TEXT_SEC),
            ft.Row([blader_input, PrimaryBtn("Add", add_blader, width=80, height=52)]),
            ft.Container(height=12),
            ft.Container(content=bladers_list_ui, expand=True)
        ])

        selection_list_ui = ft.ListView(expand=True, spacing=12)
        
        def toggle_selection(e, b_id):
            if e.control.value:
                if b_id not in home_state["selected_ids"]: home_state["selected_ids"].append(b_id)
            else:
                if b_id in home_state["selected_ids"]: home_state["selected_ids"].remove(b_id)
            btn_criar.content.controls[1].value = f"Avançar para Passo 2 ({len(home_state['selected_ids'])})"
            page.update()

        for b in bladers:
            selection_list_ui.controls.append(
                AppCard(
                    ft.Checkbox(
                        label=b["name"], value=(b["id"] in home_state["selected_ids"]),
                        on_change=lambda e, bid=b["id"]: toggle_selection(e, bid),
                        fill_color=C_PRIMARY, check_color=C_BG, label_style=ft.TextStyle(color=C_TEXT_PRI, size=15, weight=ft.FontWeight.W_500)
                    ), padding=8
                )
            )

        view_config_container = ft.Container(expand=True)

        def open_config_view(e):
            selected_bladers = [b for b in get_bladers() if b["id"] in home_state["selected_ids"]]
            total_b = len(selected_bladers)
            
            if total_b < 2:
                page.snack_bar = ft.SnackBar(ft.Text("Selecione pelo menos 2 Bladers!"), bgcolor=C_ERROR)
                page.snack_bar.open = True; page.update()
                return 
            
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

                    dist_col.controls.append(
                        ft.Row([
                            ft.Text(f"Grupo {chr(65+i)}", color=C_TEXT_PRI, width=65, size=14, weight=ft.FontWeight.BOLD),
                            make_btn(i, -1),
                            ft.Text(str(config_state["sizes"][i]), color=C_TEXT_PRI, weight=ft.FontWeight.BOLD, width=20, text_align="center"),
                            make_btn(i, 1)
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=12)
                    )
                
                diff = total_b - current_sum
                if diff == 0:
                    sum_text.value = f"✅ Total perfeito: {total_b} participantes"
                    sum_text.color = C_SUCCESS
                elif diff > 0:
                    sum_text.value = f"⚠️ Faltam alocar {diff} participante(s)"
                    sum_text.color = C_ERROR
                else:
                    sum_text.value = f"⚠️ Sobrando {-diff} vaga(s). Reduza."
                    sum_text.color = C_ERROR
                
                page.update() 

            def on_group_count_change(e=None):
                new_count = int(dd_groups.value)
                config_state["num_groups"] = new_count
                base = total_b // new_count
                rem = total_b % new_count
                config_state["sizes"] = [base + (1 if i < rem else 0) for i in range(new_count)]
                update_dist_ui()

            dd_groups = ft.Dropdown(
                options=[ft.dropdown.Option(key=str(i), text=f"{i} Grupo(s)") for i in range(1, max_groups + 1)], 
                value="1", expand=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12
            )
            dd_groups.on_change = on_group_count_change 
            
            btn_refresh = ft.Container(
                content=ft.Icon(ft.Icons.SYNC, color=C_PRIMARY),
                bgcolor=C_SURFACE_SEC, padding=12, border_radius=12, border=ft.border.all(1, C_BORDER),
                on_click=on_group_count_change
            )
            
            dd_advances = ft.Dropdown(options=[ft.dropdown.Option(key=str(i), text=f"{i} por Grupo") for i in range(1, 5)], value="2", expand=True, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            name_input = ft.TextField(label="Nome do Torneio", value=f"Torneio {datetime.now().strftime('%d/%m')}", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)

            def confirm_create(e):
                if sum(config_state["sizes"]) != total_b:
                    page.snack_bar = ft.SnackBar(ft.Text("⚠️ Ajuste as vagas! A soma dos grupos deve ser igual ao número de participantes."), bgcolor=C_ERROR)
                    page.snack_bar.open = True; page.update()
                    return

                safe_cloud_sync() 
                groups = []
                participants_snapshot = {b["id"]: b["name"] for b in selected_bladers}

                # 🎲 LÓGICA DE SORTEIO ADICIONADA AQUI!
                shuffled_bladers = list(selected_bladers)
                random.shuffle(shuffled_bladers) # Embaralha os bladers antes de distribuir

                blader_idx = 0
                for i, size in enumerate(config_state["sizes"]):
                    # Pega os bladers já sorteados/embaralhados
                    group_bladers = shuffled_bladers[blader_idx : blader_idx + size]
                    blader_idx += size
                    
                    matches = [{"id": f"{i}-{j}-{k}-{int(time.time())}", "groupId": f"group-{i}", "blader1": group_bladers[j]["id"], "blader2": group_bladers[k]["id"], "completed": False} for j in range(len(group_bladers)) for k in range(j + 1, len(group_bladers))]
                    groups.append({"id": f"group-{i}", "name": f"Grupo {chr(65 + i)}", "bladerIds": [b["id"] for b in group_bladers], "matches": matches})

                save_tournament({
                    "id": str(int(time.time())), 
                    "name": name_input.value.strip() or "Torneio X", 
                    "date": datetime.now().strftime('%d/%m/%Y %H:%M'), 
                    "groups": groups, 
                    "status": "groups", 
                    "knockout": [],
                    "participants": participants_snapshot,
                    "advancing_per_group": int(dd_advances.value)
                })
                
                home_state["selected_ids"].clear()
                switch_home_tab("selecao") 
                bottom_nav.selected_index = 2
                change_tab_programmatic(2)
            
            update_dist_ui()

            view_config_container.content = ft.Column([
                ft.Text("Passo 2: Definir Grupos e Vagas", size=14, color=C_TEXT_SEC),
                AppCard(ft.Column([
                    name_input, 
                    ft.Text("Quantidade de Grupos: (Se falhar, clique no ícone 🔄)", color=C_TEXT_SEC, size=13), 
                    ft.Row([dd_groups, btn_refresh]), 
                    ft.Text("Avançam por Grupo (Mata-Mata):", color=C_TEXT_SEC, size=13), 
                    ft.Row([dd_advances]),
                    ft.Divider(color=C_BORDER, height=20),
                    ft.Text("Ajuste manual de vagas:", color=C_TEXT_SEC, size=13), dist_col,
                    ft.Container(content=sum_text, alignment=ft.Alignment(0,0))
                ], spacing=16)),
                ft.Row([
                    SecondaryBtn("Voltar", lambda _: switch_home_tab("selecao"), expand=True),
                    PrimaryBtn("Sortear e Criar", confirm_create, expand=True) # Botão renomeado para refletir o sorteio
                ], spacing=12)
            ], scroll=ft.ScrollMode.AUTO)

            switch_home_tab("config")

        btn_criar = PrimaryBtn(f"Avançar para Passo 2 ({len(home_state['selected_ids'])})", open_config_view, width=float("inf"), icon=ft.Icons.ROCKET_LAUNCH)
        
        view_selecao = ft.Column([
            ft.Text("Passo 1: Marque os Bladers participantes", size=14, color=C_TEXT_SEC),
            ft.Container(content=selection_list_ui, expand=True),
            ft.Divider(color=C_BORDER, height=12),
            btn_criar
        ])

        tab_nav_container = ft.Container()
        content_switcher = ft.Container(expand=True)

        def build_home_tab_row():
            is_c = home_state["sub_tab"] == "cadastro"
            is_s = home_state["sub_tab"] in ["selecao", "config"]
            tabs = [
                ft.Container(content=ft.Text("Banco Geral", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_c else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_c else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_home_tab("cadastro")),
                ft.Container(content=ft.Text("Criar Torneio", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_s else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_s else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_home_tab("selecao"))
            ]
            tab_nav_container.content = ft.Container(content=ft.Row(tabs, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BORDER), border_radius=10, padding=4, margin=ft.margin.only(bottom=16))

        def switch_home_tab(tab_name):
            home_state["sub_tab"] = tab_name
            build_home_tab_row()
            if tab_name == "cadastro":
                content_switcher.content = view_cadastro
            elif tab_name == "selecao":
                content_switcher.content = view_selecao
            elif tab_name == "config":
                content_switcher.content = view_config_container
            page.update()

        switch_home_tab("cadastro")

        return ft.Container(padding=24, content=ft.Column([ft.Text("Gestão de Bladers", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), tab_nav_container, content_switcher]))

    # --- TELA 2: PARTIDA RÁPIDA (BLINDADA E OTIMIZADA) ---
    def build_quick_match_view():
        active_match = get_active_match()
        is_tournament = active_match is not None

        state = {
            "p1_score": 0, "p2_score": 0,
            "p1_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0},
            "p2_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0},
            "match_ended": False
        }
        
        score_p1 = ft.Text("0", size=64, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI)
        score_p2 = ft.Text("0", size=64, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI)

        if is_tournament:
            p1_display = ft.Text(active_match.get("b1_name", ""), size=16, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, text_align="center", overflow=ft.TextOverflow.ELLIPSIS)
            p2_display = ft.Text(active_match.get("b2_name", ""), size=16, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, text_align="center", overflow=ft.TextOverflow.ELLIPSIS)
            get_p1_name = lambda: active_match.get("b1_name", "")
            get_p2_name = lambda: active_match.get("b2_name", "")
        else:
            p1_input = ft.TextField(value="Jogador 1", text_align=ft.TextAlign.CENTER, bgcolor="transparent", border_color="transparent", color=C_TEXT_PRI, text_size=16, content_padding=0)
            p2_input = ft.TextField(value="Jogador 2", text_align=ft.TextAlign.CENTER, bgcolor="transparent", border_color="transparent", color=C_TEXT_PRI, text_size=16, content_padding=0)
            p1_display, p2_display = p1_input, p2_input
            get_p1_name = lambda: p1_input.value.strip() or "Jogador 1"
            get_p2_name = lambda: p2_input.value.strip() or "Jogador 2"

        def process_win():
            state["match_ended"] = True
            winner = get_p1_name() if state["p1_score"] > state["p2_score"] else get_p2_name()
            
            def finish_match(e):
                hide_dialog(dlg)
                
                if is_tournament:
                    change_tab_programmatic(2)
                    page.snack_bar = ft.SnackBar(ft.Text("Sincronizando resultado em segundo plano..."), bgcolor=C_SURFACE_SEC, duration=2000)
                    page.snack_bar.open = True
                    page.update()

                    def async_save_match():
                        safe_cloud_sync() 
                        tourn = get_tournament()
                        if not tourn: return
                        
                        w_id = active_match.get("b1_id") if state["p1_score"] > state["p2_score"] else active_match.get("b2_id")
                        
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
                                if is_p1:
                                    tourn["knockout"][r_idx + 1]["matches"][next_m_idx]["blader1"] = w_id
                                else:
                                    tourn["knockout"][r_idx + 1]["matches"][next_m_idx]["blader2"] = w_id
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

            dlg = ft.AlertDialog(
                modal=True, 
                bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16),
                title=ft.Text(f"🏆 Vitória de {winner}!", color=C_PRIMARY, weight=ft.FontWeight.BOLD),
                content=ft.Text("A partida foi concluída. O resultado será registrado no sistema.", color=C_TEXT_SEC),
                actions=[PrimaryBtn("Confirmar e Voltar", finish_match, width=float("inf"))]
            )
            show_dialog(dlg)

        def add_points(player, pts, type_finish):
            if state["match_ended"]: return 
            if player == 1:
                state["p1_score"] += pts
                state["p1_finishes"][type_finish] += 1
                score_p1.value = str(state["p1_score"])
            else:
                state["p2_score"] += pts
                state["p2_finishes"][type_finish] += 1
                score_p2.value = str(state["p2_score"])
            page.update()
            if state["p1_score"] >= 4 or state["p2_score"] >= 4: process_win()

        def reset(e=None):
            state["p1_score"], state["p2_score"] = 0, 0
            state["p1_finishes"] = {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}
            state["p2_finishes"] = {"spin": 0, "over": 0, "burst": 0, "xtreme": 0, "flag": 0}
            state["match_ended"] = False
            score_p1.value, score_p2.value = "0", "0"
            page.update()

        def action_col(p):
            return ft.Column([
                PrimaryBtn("XTREME (+3)", lambda _: add_points(p, 3, "xtreme"), width=145, height=44),
                SecondaryBtn("BURST (+2)", lambda _: add_points(p, 2, "burst"), width=145, height=44),
                SecondaryBtn("OVER (+2)", lambda _: add_points(p, 2, "over"), width=145, height=44),
                SecondaryBtn("SPIN (+1)", lambda _: add_points(p, 1, "spin"), width=145, height=44),
                SecondaryBtn("FLAG (+1)", lambda _: add_points(p, 1, "flag"), width=145, height=44),
            ], spacing=12, alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        if is_tournament:
            header_txt = "ELIMINATÓRIAS" if active_match.get("is_knockout") else "FASE DE GRUPOS"
            header_col = C_ERROR if active_match.get("is_knockout") else C_PRIMARY
        else:
            header_txt = "PARTIDA CASUAL"
            header_col = C_SURFACE_SEC

        return ft.Container(
            padding=0,
            content=ft.Column([
                ft.Container(
                    content=ft.Text(header_txt, color=C_TEXT_PRI if is_tournament else C_TEXT_SEC, weight=ft.FontWeight.W_600, size=13, text_align="center"),
                    bgcolor=header_col if is_tournament else "transparent", padding=12, width=float("inf"),
                    border=ft.border.only(bottom=ft.BorderSide(1, C_BORDER)) if not is_tournament else None
                ),
                ft.Container(padding=24, expand=True, content=ft.Column([
                    ft.Row([
                        ft.Column([p1_display, score_p1, action_col(1)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Container(width=1, bgcolor=C_BORDER, height=300, margin=ft.margin.symmetric(horizontal=8)),
                        ft.Column([p2_display, score_p2, action_col(2)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START),
                    ft.Container(expand=True),
                    SecondaryBtn("Resetar Placar", reset, width=float("inf"), icon=ft.Icons.REFRESH)
                ]))
            ])
        )

    # --- TELA 3: TORNEIO ---
    def build_tournament_view():
        tourn = get_tournament()
        if not tourn: 
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.EMOJI_EVENTS_OUTLINED, size=64, color=C_BORDER),
                    ft.Text("Nenhum torneio em andamento.", color=C_TEXT_SEC, size=16)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True, alignment=ft.Alignment(0,0)
            )

        bladers_map = get_snapshot_map(tourn)
        t_state = {"tab": "matamata" if tourn.get("status") == "knockout" else "grupos"}
        
        def open_admin_panel(e):
            safe_cloud_sync()
            fresh_tourn = get_tournament()
            
            in_tourn = [{"id": k, "name": v} for k, v in fresh_tourn.get("participants", {}).items()]
            all_bladers = get_bladers()
            
            out_tourn = [b for b in all_bladers if b["id"] not in fresh_tourn.get("participants", {})]

            dd_sai = ft.Dropdown(options=[ft.dropdown.Option(key=b["id"], text=b["name"]) for b in in_tourn], label="Quem saiu?", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI)
            
            if not out_tourn:
                content_ui = ft.Text("⚠️ Você não tem Reservas no Banco.\n\nVá até a aba 'Bladers', cadastre o substituto, e volte aqui.", color=C_ERROR, size=14, text_align="center")
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
                                if res.get("blader1Result", {}).get("bladerId") == id_sai: 
                                    res["blader1Result"]["bladerId"] = id_entra
                                if res.get("blader2Result", {}).get("bladerId") == id_sai: 
                                    res["blader2Result"]["bladerId"] = id_entra
                                if res.get("winner") == id_sai: 
                                    res["winner"] = id_entra
                                
                    for rd in fresh_tourn.get("knockout", []):
                        for m in rd.get("matches", []):
                            if m.get("blader1") == id_sai: m["blader1"] = id_entra
                            if m.get("blader2") == id_sai: m["blader2"] = id_entra
                            if m.get("completed"):
                                res = m.get("result", {})
                                if res.get("blader1Result", {}).get("bladerId") == id_sai: 
                                    res["blader1Result"]["bladerId"] = id_entra
                                if res.get("blader2Result", {}).get("bladerId") == id_sai: 
                                    res["blader2Result"]["bladerId"] = id_entra
                                if res.get("winner") == id_sai: 
                                    res["winner"] = id_entra
                    
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
            safe_cloud_sync() 
            fresh_tourn = get_tournament()
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
                for x in half:
                    res.append(x)
                    res.append(size - 1 - x)
                return res
                
            order = get_seeds(p2)
            ordered_players = [padded[i] for i in order]
            
            knockout = []
            rounds = int(math.log2(p2))
            round_names = {1: "Grande Final", 2: "Semifinais", 3: "Quartas de Final", 4: "Oitavas de Final", 5: "16 avos"}
            
            curr_matches = []
            for i in range(0, p2, 2):
                p1 = ordered_players[i]
                p2_id = ordered_players[i+1]
                is_bye = p1 is None or p2_id is None
                winner = p1 if p2_id is None else p2_id if p1 is None else None
                
                m = {
                    "id": f"r0-m{i//2}-{int(time.time())}",
                    "blader1": p1,
                    "blader2": p2_id,
                    "completed": is_bye,
                }
                if is_bye and winner is not None:
                    m["result"] = {
                        "blader1Result": {"bladerId": p1, "totalPoints": 0, "finishes": {}},
                        "blader2Result": {"bladerId": p2_id, "totalPoints": 0, "finishes": {}},
                        "winner": winner
                    }
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
                    
                    next_matches.append({
                        "id": f"r{r}-m{i}-{int(time.time())}",
                        "blader1": b1,
                        "blader2": b2,
                        "completed": False
                    })
                knockout.append({"name": round_names.get(rounds - r, f"Rodada {r+1}"), "matches": next_matches})

            fresh_tourn["knockout"] = knockout
            fresh_tourn["status"] = "knockout"
            save_tournament(fresh_tourn)
            refresh_current_tab()

        view_grupos = ft.ListView(expand=True, spacing=16, padding=ft.padding.only(top=16))
        view_partidas = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))
        view_matamata = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))

        def go_to_match(e):
            set_active_match(e.control.data)
            bottom_nav.selected_index = 1
            change_tab_programmatic(1)

        for group in tourn.get("groups", []):
            sorted_st = get_group_standings(group)
            g_col = ft.Column([ft.Text(group.get("name", "Grupo"), size=16, weight=ft.FontWeight.W_600, color=C_TEXT_PRI)])
            
            g_col.controls.append(ft.Container(content=ft.Row([
                ft.Text("#", width=20, size=12, color=C_TEXT_SEC), 
                ft.Text("Blader", expand=True, size=12, color=C_TEXT_SEC), 
                ft.Text("J", width=25, size=12, color=C_TEXT_SEC, text_align="center"), 
                ft.Text("V", width=25, size=12, color=C_TEXT_SEC, text_align="center"), 
                ft.Text("PF", width=25, size=12, color=C_TEXT_SEC, text_align="center"), 
                ft.Text("Sld", width=30, size=12, color=C_TEXT_SEC, text_align="center")
            ]), padding=8, border=ft.border.only(bottom=ft.BorderSide(1, C_BORDER))))
            
            adv_limit = int(tourn.get("advancing_per_group", 2))
            
            for idx, st in enumerate(sorted_st):
                is_top = idx < adv_limit 
                g_col.controls.append(ft.Container(content=ft.Row([
                    ft.Text(str(idx+1), width=20, size=14, color=C_TEXT_PRI if is_top else C_TEXT_SEC, weight=ft.FontWeight.W_600 if is_top else ft.FontWeight.NORMAL), 
                    ft.Text(st["name"], expand=True, size=14, color=C_TEXT_PRI, overflow=ft.TextOverflow.ELLIPSIS), 
                    ft.Text(str(st["j"]), width=25, size=14, color=C_TEXT_SEC, text_align="center"), 
                    ft.Text(str(st["v"]), width=25, size=14, color=C_TEXT_SEC, text_align="center"), 
                    ft.Text(str(st["pf"]), width=25, size=14, color=C_TEXT_SEC, text_align="center"), 
                    ft.Text(str(st["saldo"]), width=30, size=14, color=C_SUCCESS if st["saldo"] > 0 else C_ERROR, text_align="center", weight=ft.FontWeight.W_500)
                ]), padding=8, bgcolor=C_SURFACE_SEC if is_top else "transparent", border_radius=8))
            view_grupos.controls.append(AppCard(g_col))

            view_partidas.controls.append(ft.Text(group.get("name", ""), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC, margin=ft.margin.only(top=8)))
            
            for match in group.get("matches", []):
                b1_name = bladers_map.get(match.get("blader1"), "Blader Removido")
                b2_name = bladers_map.get(match.get("blader2"), "Blader Removido")
                
                if match.get("completed"):
                    res = match.get("result", {})
                    pts1 = res.get("blader1Result", {}).get("totalPoints", 0)
                    pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                    status_ui = ft.Row([
                        ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), 
                        IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=match: open_match_details(md, tourn))
                    ])
                else:
                    status_ui = SecondaryBtn("Jogar", go_to_match, height=36, width=80, data={"match_id": match.get("id"), "group_id": group.get("id"), "b1_id": match.get("blader1"), "b1_name": b1_name, "b2_id": match.get("blader2"), "b2_name": b2_name})
                view_partidas.controls.append(AppCard(ft.Row([ft.Column([ft.Text(b1_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI), ft.Text("vs", size=10, color=C_TEXT_SEC), ft.Text(b2_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI)]), status_ui], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

        if tourn.get("status") == "groups":
            view_grupos.controls.append(PrimaryBtn("Avançar para Mata-Mata", advance_to_knockout, width=float("inf")))
        
        if tourn.get("knockout"):
            for r_idx, round_data in enumerate(tourn.get("knockout", [])):
                view_matamata.controls.append(ft.Text(round_data.get("name", ""), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC, margin=ft.margin.only(top=8)))
                for match in round_data.get("matches", []):
                    b1_id = match.get("blader1")
                    b2_id = match.get("blader2")
                    b1_name = bladers_map.get(b1_id, "A definir") if b1_id else "A definir"
                    b2_name = bladers_map.get(b2_id, "A definir") if b2_id else "A definir"
                    
                    if match.get("completed"):
                        res = match.get("result", {})
                        if b1_id is None or b2_id is None:
                            status_ui = ft.Text("Avançou (W.O.)", color=C_TEXT_SEC, size=12)
                        else:
                            pts1 = res.get("blader1Result", {}).get("totalPoints", 0)
                            pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                            status_ui = ft.Row([
                                ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), 
                                IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=match: open_match_details(md, tourn))
                            ])
                        view_matamata.controls.append(AppCard(ft.Row([ft.Text(b1_name, size=14, color=C_TEXT_PRI), status_ui, ft.Text(b2_name, size=14, color=C_TEXT_PRI)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))
                    else:
                        if b1_id is None or b2_id is None:
                            status_ui = ft.Text("Aguardando...", color=C_TEXT_SEC, size=12)
                        else:
                            status_ui = PrimaryBtn("Jogar", go_to_match, height=36, width=80, data={"is_knockout": True, "round_idx": r_idx, "match_id": match.get("id"), "b1_id": b1_id, "b1_name": b1_name, "b2_id": b2_id, "b2_name": b2_name})
                        view_matamata.controls.append(AppCard(ft.Row([ft.Column([ft.Text(b1_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI), ft.Text("vs", size=10, color=C_TEXT_SEC), ft.Text(b2_name, size=14, weight=ft.FontWeight.W_500, color=C_TEXT_PRI)]), status_ui], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

        tab_nav_container = ft.Container(padding=ft.padding.symmetric(horizontal=24))
        
        initial_view = view_matamata if t_state["tab"] == "matamata" else view_grupos
        content_switcher = ft.Container(content=initial_view, expand=True)

        def build_tab_row():
            is_g = t_state["tab"] == "grupos"
            is_p = t_state["tab"] == "partidas"
            is_m = t_state["tab"] == "matamata"

            tabs = [
                ft.Container(content=ft.Text("Grupos", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_g else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_g else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_sub_tab("grupos")),
                ft.Container(content=ft.Text("Partidas", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_p else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_p else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_sub_tab("partidas"))
            ]
            if tourn.get("status") == "knockout":
                tabs.append(ft.Container(content=ft.Text("Mata-Mata", size=13, weight=ft.FontWeight.W_600, color=C_PRIMARY if is_m else C_TEXT_SEC), expand=True, bgcolor=f"{C_PRIMARY}15" if is_m else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_sub_tab("matamata")))
            
            tab_nav_container.content = ft.Container(content=ft.Row(tabs, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BORDER), border_radius=10, padding=4)

        def switch_sub_tab(tab_name):
            t_state["tab"] = tab_name; build_tab_row()
            if tab_name == "grupos": content_switcher.content = view_grupos
            elif tab_name == "partidas": content_switcher.content = view_partidas
            elif tab_name == "matamata": content_switcher.content = view_matamata
            page.update()

        build_tab_row() 

        def prompt_end_tourn(e):
            def handle_action(action):
                safe_cloud_sync() 
                if action == "salvar": add_to_history(tourn)
                save_tournament(None); set_active_match(None)
                hide_dialog(dlg); refresh_current_tab()

            dlg = ft.AlertDialog(
                bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Encerrar Torneio", color=C_TEXT_PRI, size=18, weight=ft.FontWeight.BOLD),
                content=ft.Text("O que deseja fazer com os dados?", color=C_TEXT_SEC, size=14),
                actions=[SecondaryBtn("Excluir", lambda _: handle_action("excluir")), PrimaryBtn("Salvar no Histórico", lambda _: handle_action("salvar"))]
            )
            show_dialog(dlg)

        return ft.Container(
            padding=0,
            content=ft.Column([
                ft.Container(content=ft.Row([
                    ft.Column([ft.Text(tourn.get("name",""), size=20, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI), ft.Text("Em andamento", size=12, color=C_PRIMARY)], spacing=0),
                    ft.Row([
                        IconButton(ft.Icons.SWAP_HORIZ, open_admin_panel, color=C_PRIMARY),
                        IconButton(ft.Icons.POWER_SETTINGS_NEW, prompt_end_tourn, color=C_ERROR)
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=24),
                tab_nav_container,
                ft.Container(content=content_switcher, padding=ft.padding.symmetric(horizontal=24), expand=True)
            ])
        )

    # --- TELA 4: HISTÓRICO E ESTATÍSTICAS ---
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
                        status_ui = ft.Row([
                            ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), 
                            IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=m: open_match_details(md, t_data))
                        ])
                        view_tabelas.controls.append(AppCard(ft.Row([ft.Text(b1_n, size=14, color=C_TEXT_PRI), status_ui, ft.Text(b2_n, size=14, color=C_TEXT_PRI)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))
            
            for r in t_data.get("knockout", []):
                view_tabelas.controls.append(ft.Text(r.get("name", ""), size=14, weight=ft.FontWeight.W_600, color=C_TEXT_SEC, margin=ft.margin.only(top=8)))
                for match in r.get("matches", []):
                    b1_id = match.get("blader1")
                    b2_id = match.get("blader2")
                    b1_name = bladers_map.get(b1_id, "A definir") if b1_id else "A definir"
                    b2_name = bladers_map.get(b2_id, "A definir") if b2_id else "A definir"

                    if match.get("completed"):
                        res = match.get("result", {})
                        if b1_id is None or b2_id is None:
                            status_ui = ft.Text("Avançou (W.O.)", color=C_TEXT_SEC, size=12)
                        else:
                            pts1 = res.get("blader1Result", {}).get("totalPoints", 0)
                            pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                            status_ui = ft.Row([
                                ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), 
                                IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=match: open_match_details(md, t_data))
                            ])
                        view_tabelas.controls.append(AppCard(ft.Row([ft.Text(b1_name, size=14, color=C_TEXT_PRI), status_ui, ft.Text(b2_name, size=14, color=C_TEXT_PRI)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

            view_stats = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))
            for st in sorted_stats:
                view_stats.controls.append(
                    AppCard(
                        ft.Column([
                            ft.Row([
                                ft.Text(st["name"], weight=ft.FontWeight.BOLD, size=16, color=C_TEXT_PRI, expand=True),
                                ft.Text(f"{st['pts']} Pts", weight=ft.FontWeight.BOLD, size=16, color=C_PRIMARY)
                            ]),
                            ft.Text(f"{st['v']} Vitórias em {st['j']} Jogos", size=12, color=C_TEXT_SEC),
                            ft.Container(height=4),
                            ft.Row([
                                Badge(f"XT: {st['xtreme']}", C_XTREME),
                                Badge(f"BU: {st['burst']}", C_BURST),
                                Badge(f"OV: {st['over']}", C_OVER),
                                Badge(f"SP: {st['spin']}", C_SPIN),
                                Badge(f"FL: {st['flag']}", C_FLAG),
                            ], spacing=6, wrap=True)
                        ], spacing=4), padding=16
                    )
                )

            hist_nav_container = ft.Container(padding=ft.padding.symmetric(horizontal=24))
            content_switcher = ft.Container(content=view_tabelas if history_state["sub_tab"] == "tabelas" else view_stats, expand=True)

            def build_hist_tab_row():
                is_t = history_state["sub_tab"] == "tabelas"
                tabs = [
                    ft.Container(content=ft.Text("Chaves", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if is_t else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if is_t else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_det_tab("tabelas")),
                    ft.Container(content=ft.Text("Estatísticas", size=13, weight=ft.FontWeight.W_600, color=C_TEXT_PRI if not is_t else C_TEXT_SEC), expand=True, bgcolor=C_SURFACE_SEC if not is_t else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: switch_det_tab("estatisticas"))
                ]
                hist_nav_container.content = ft.Container(content=ft.Row(tabs, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BORDER), border_radius=10, padding=4)

            def switch_det_tab(tab_name):
                history_state["sub_tab"] = tab_name; build_hist_tab_row()
                content_switcher.content = view_tabelas if tab_name == "tabelas" else view_stats; page.update()
                
            build_hist_tab_row()

            def close_detail(e):
                history_state["active_tourn"] = None; refresh_current_tab()

            return ft.Container(
                padding=0,
                content=ft.Column([
                    ft.Container(content=ft.Row([
                        IconButton(ft.Icons.ARROW_BACK, close_detail),
                        ft.Text(t_data.get("name", ""), size=18, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI, expand=True, text_align="right"),
                    ]), padding=24),
                    hist_nav_container,
                    ft.Container(content=content_switcher, padding=ft.padding.symmetric(horizontal=24), expand=True)
                ])
            )

        hist = get_history()
        if not hist: return ft.Container(content=ft.Column([ft.Icon(ft.Icons.HISTORY, size=64, color=C_BORDER), ft.Text("Histórico vazio.", color=C_TEXT_SEC, size=16)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True, alignment=ft.Alignment(0,0))

        list_ui = ft.ListView(expand=True, spacing=12, padding=24)
        list_ui.controls.append(ft.Text("Torneios Anteriores", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI, margin=ft.margin.only(bottom=8)))
        
        def open_history_detail(t_data):
            history_state["active_tourn"] = t_data; history_state["sub_tab"] = "tabelas"; refresh_current_tab()

        for t in hist:
            list_ui.controls.append(
                AppCard(
                    ft.Row([
                        ft.Column([ft.Text(t.get("name", ""), weight=ft.FontWeight.W_600, size=16, color=C_TEXT_PRI), ft.Text(f"{t.get('date', '')}", size=12, color=C_TEXT_SEC)], spacing=2, expand=True),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C_BORDER)
                    ]), 
                    padding=16, on_click=lambda e, data=t: open_history_detail(data)
                )
            )

        return ft.Container(content=list_ui, expand=True)

    # --- NAVEGAÇÃO PRINCIPAL ---
    content_area = ft.Container(expand=True)

    def change_tab_programmatic(index):
        content_area.content = None; page.update()
        if index == 0: content_area.content = build_home_view()
        elif index == 1: content_area.content = build_quick_match_view()
        elif index == 2: content_area.content = build_tournament_view()
        elif index == 3: content_area.content = build_history_view()
        page.update()

    def change_tab(e): change_tab_programmatic(e.control.selected_index)
    def refresh_current_tab(): change_tab_programmatic(bottom_nav.selected_index)

    bottom_nav = ft.NavigationBar(
        bgcolor=C_BG, selected_index=0, on_change=change_tab,
        indicator_color=C_SURFACE_SEC,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.PEOPLE_OUTLINE, selected_icon=ft.Icons.PEOPLE, label="Bladers"),
            ft.NavigationBarDestination(icon=ft.Icons.FLASH_ON_OUTLINED, selected_icon=ft.Icons.FLASH_ON, label="Combate"),
            ft.NavigationBarDestination(icon=ft.Icons.EMOJI_EVENTS_OUTLINED, selected_icon=ft.Icons.EMOJI_EVENTS, label="Torneio"),
            ft.NavigationBarDestination(icon=ft.Icons.HISTORY_OUTLINED, selected_icon=ft.Icons.HISTORY, label="Histórico"),
        ]
    )

    page.add(content_area, bottom_nav)
    change_tab_programmatic(0)

    # ==========================================
    # 🔄 MOTOR DE ATUALIZAÇÃO SIMULTÂNEA
    # ==========================================
    def auto_sync_loop():
        global is_syncing
        while True:
            time.sleep(5) 
            
            if is_syncing:
                continue 
                
            try:
                res = requests.get(FIREBASE_URL, timeout=5)
                if res.status_code == 200:
                    nuvem = res.json()
                    
                    if nuvem and json.dumps(nuvem) != json.dumps(app_data):
                        app_data.clear()
                        app_data.update(nuvem)
                        
                        if bottom_nav.selected_index in [0, 2, 3]:
                            refresh_current_tab()
            except:
                pass

    threading.Thread(target=auto_sync_loop, daemon=True).start()

ft.run(main)
