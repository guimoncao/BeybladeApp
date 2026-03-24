import flet as ft
import time
import math
import json
import os
import threading 
import requests  
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
# 2. BASE DE DADOS (MOTOR DA NUVEM À PROVA DE FALHAS)
# ==========================================
FIREBASE_URL = "https://beybladeapp-c303a-default-rtdb.firebaseio.com/beyblade_data.json"

app_data = {"bladers": [], "tournament": None, "active_match": None, "history": []}

# 🚦 O SEMÁFORO GLOBAL: Impede que a nuvem sobrescreva seus dados enquanto você está salvando
is_syncing = False

def load_db():
    try:
        res = requests.get(FIREBASE_URL, timeout=5)
        if res.status_code == 200 and res.json() is not None:
            app_data.clear()
            app_data.update(res.json())
    except:
        pass

def save_db(data):
    """Salva os dados de forma instantânea na tela, e envia para a nuvem escondido"""
    global is_syncing
    is_syncing = True # Acende a luz vermelha para o motor de atualização
    
    def _background_save(dados_para_salvar):
        global is_syncing
        for _ in range(3): # Tenta salvar até 3 vezes se a internet piscar
            try:
                res = requests.put(FIREBASE_URL, json=dados_para_salvar, timeout=5)
                if res.status_code == 200:
                    break 
            except:
                time.sleep(1.5)
        is_syncing = False # Acende a luz verde, liberação concluída

    dados_copia = json.loads(json.dumps(data))
    threading.Thread(target=_background_save, args=(dados_copia,), daemon=True).start()

# Carrega o banco assim que o app abre
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

def PrimaryBtn(text, on_click, width=None, height=48, icon=None, data=None, color=C_PRIMARY):
    items = []
    if icon: items.append(ft.Icon(icon, color=C_TEXT_PRI, size=20))
    items.append(ft.Text(text, color=C_TEXT_PRI, weight=ft.FontWeight.W_600, size=14))
    return ft.Container(
        content=ft.Row(items, alignment=ft.MainAxisAlignment.CENTER, spacing=8) if icon else items[0],
        bgcolor=color, padding=ft.padding.symmetric(horizontal=8, vertical=0),
        border_radius=12, alignment=ft.Alignment(0, 0), width=width, height=height,
        on_click=on_click, data=data
    )

def SecondaryBtn(text, on_click, width=None, height=48, icon=None, data=None):
    items = []
    if icon: items.append(ft.Icon(icon, color=C_TEXT_SEC, size=20))
    items.append(ft.Text(text, color=C_TEXT_SEC, weight=ft.FontWeight.W_500, size=13))
    return ft.Container(
        content=ft.Row(items, alignment=ft.MainAxisAlignment.CENTER, spacing=8) if icon else items[0],
        bgcolor=C_SURFACE_SEC, padding=ft.padding.symmetric(horizontal=8, vertical=0),
        border_radius=12, border=ft.border.all(1, C_BORDER),
        alignment=ft.Alignment(0, 0), width=width, height=height,
        on_click=on_click, data=data
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
        padding=ft.padding.symmetric(horizontal=6, vertical=2),
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

    # --- TELA 1: INÍCIO (BLADERS) ---
    def build_home_view():
        bladers = get_bladers()
        blader_input = ft.TextField(
            hint_text="Nome do Blader...", expand=True, bgcolor=C_SURFACE_SEC, 
            border_color=C_BORDER, color=C_TEXT_PRI, text_size=14, border_radius=12,
            content_padding=16, cursor_color=C_PRIMARY
        )
        
        def add_blader(e):
            if blader_input.value.strip():
                b_list = get_bladers()
                b_list.append({"id": str(int(time.time())), "name": blader_input.value.strip()})
                save_bladers(b_list)
                blader_input.value = ""
                refresh_current_tab()

        def remove_blader(b_id):
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

        def open_create_tourn_dialog(e):
            b_list = get_bladers()
            if len(b_list) < 2: return 
            
            max_groups = max(1, len(b_list) // 2)
            options = [ft.dropdown.Option(key=str(i), text=f"{i} Grupo(s)") for i in range(1, max_groups + 1)]
            dd_groups = ft.Dropdown(options=options, value="1", width=200, bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)
            name_input = ft.TextField(label="Nome do Torneio", value=f"Torneio {datetime.now().strftime('%d/%m')}", bgcolor=C_SURFACE_SEC, border_color=C_BORDER, color=C_TEXT_PRI, border_radius=12)

            def confirm_create(e):
                group_count = int(dd_groups.value)
                groups = []
                bladers_per_group = math.ceil(len(b_list) / group_count)
                participants_snapshot = {b["id"]: b["name"] for b in b_list}

                for i in range(group_count):
                    group_bladers = b_list[i * bladers_per_group : (i + 1) * bladers_per_group]
                    matches = [{"id": f"{i}-{j}-{k}-{int(time.time())}", "groupId": f"group-{i}", "blader1": group_bladers[j]["id"], "blader2": group_bladers[k]["id"], "completed": False} for j in range(len(group_bladers)) for k in range(j + 1, len(group_bladers))]
                    groups.append({"id": f"group-{i}", "name": f"Grupo {chr(65 + i)}", "bladerIds": [b["id"] for b in group_bladers], "matches": matches})

                save_tournament({
                    "id": str(int(time.time())), 
                    "name": name_input.value.strip() or "Torneio X", 
                    "date": datetime.now().strftime('%d/%m/%Y %H:%M'), 
                    "groups": groups, 
                    "status": "groups", 
                    "knockout": [],
                    "participants": participants_snapshot 
                })
                hide_dialog(dlg)
                bottom_nav.selected_index = 2
                change_tab_programmatic(2)
            
            dlg = ft.AlertDialog(
                bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16),
                title=ft.Text("Novo Torneio", color=C_TEXT_PRI, size=18, weight=ft.FontWeight.BOLD),
                content=ft.Column([name_input, ft.Text("Distribuição:", color=C_TEXT_SEC, size=13), dd_groups], tight=True, spacing=16),
                actions=[SecondaryBtn("Cancelar", lambda _: hide_dialog(dlg)), PrimaryBtn("Criar", confirm_create)]
            )
            show_dialog(dlg)

        return ft.Container(
            padding=ft.padding.all(24),
            content=ft.Column([
                ft.Text("Gestão de Bladers", size=24, weight=ft.FontWeight.BOLD, color=C_TEXT_PRI),
                ft.Text("Adicione os participantes antes de iniciar o torneio.", size=14, color=C_TEXT_SEC, margin=ft.margin.only(bottom=16)),
                ft.Row([blader_input, PrimaryBtn("Add", add_blader, width=80, height=52)]),
                ft.Container(height=24),
                ft.Container(content=bladers_list_ui, expand=True),
                ft.Divider(color=C_BORDER, height=32),
                PrimaryBtn("Iniciar Novo Torneio", open_create_tourn_dialog, width=float("inf"), icon=ft.Icons.ROCKET_LAUNCH)
            ])
        )

    # --- TELA 2: PARTIDA RÁPIDA ---
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
            
            if is_tournament:
                tourn = get_tournament()
                w_id = active_match.get("b1_id") if state["p1_score"] > state["p2_score"] else active_match.get("b2_id")
                
                if active_match.get("is_knockout"):
                    r_idx = active_match.get("round_idx")
                    for m in tourn["knockout"][r_idx]["matches"]:
                        if m.get("id") == active_match.get("match_id"):
                            m["completed"] = True
                            m["result"] = {"blader1Result": {"bladerId": active_match.get("b1_id"), "totalPoints": state["p1_score"], "finishes": state["p1_finishes"]}, "blader2Result": {"bladerId": active_match.get("b2_id"), "totalPoints": state["p2_score"], "finishes": state["p2_finishes"]}, "winner": w_id}
                    if all(m.get("completed") for m in tourn["knockout"][r_idx]["matches"]) and r_idx + 1 < len(tourn["knockout"]):
                        winners = [m["result"]["winner"] for m in tourn["knockout"][r_idx]["matches"]]
                        if len(tourn["knockout"][r_idx + 1]["matches"]) == 1 and len(winners) == 2:
                            tourn["knockout"][r_idx + 1]["matches"][0]["blader1"] = winners[0]
                            tourn["knockout"][r_idx + 1]["matches"][0]["blader2"] = winners[1]
                else:
                    for g in tourn.get("groups", []):
                        if g.get("id") == active_match.get("group_id"):
                            for m in g.get("matches", []):
                                if m.get("id") == active_match.get("match_id"):
                                    m["completed"] = True
                                    m["result"] = {"blader1Result": {"bladerId": active_match.get("b1_id"), "totalPoints": state["p1_score"], "finishes": state["p1_finishes"]}, "blader2Result": {"bladerId": active_match.get("b2_id"), "totalPoints": state["p2_score"], "finishes": state["p2_finishes"]}, "winner": w_id}
                
                save_tournament(tourn) # O salvamento invisível é disparado aqui
                set_active_match(None) 
                
                dlg = ft.AlertDialog(
                    bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16),
                    title=ft.Text(f"🏆 Vitória de {winner}!", color=C_PRIMARY, weight=ft.FontWeight.BOLD),
                    content=ft.Text("Resultado computado na tabela oficial.", color=C_SUCCESS),
                    actions=[PrimaryBtn("Voltar ao Torneio", lambda _: [hide_dialog(dlg), change_tab_programmatic(2)])]
                )
            else:
                dlg = ft.AlertDialog(
                    bgcolor=C_SURFACE, shape=ft.RoundedRectangleBorder(radius=16),
                    title=ft.Text(f"Vitória de {winner}!", color=C_PRIMARY, weight=ft.FontWeight.BOLD),
                    content=ft.Text("Partida amistosa finalizada.", color=C_TEXT_SEC),
                    actions=[PrimaryBtn("Concluir", lambda _: hide_dialog(dlg))]
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
            fresh_tourn = get_tournament()
            
            group_tops = []
            for g in fresh_tourn.get("groups", []):
                st = get_group_standings(g)
                if len(st) >= 2: group_tops.append([st[0]["id"], st[1]["id"]])
                elif len(st) == 1: group_tops.append([st[0]["id"], None])
            
            knockout = []
            if len(fresh_tourn.get("groups", [])) == 1:
                knockout.append({"name": "Grande Final", "matches": [{"id": f"final-{int(time.time())}", "blader1": group_tops[0][0] if len(group_tops)>0 else None, "blader2": group_tops[0][1] if len(group_tops)>0 else None, "completed": False}]})
            else:
                if len(group_tops) >= 2:
                    knockout.append({"name": "Semifinais", "matches": [{"id": f"semi1-{int(time.time())}", "blader1": group_tops[0][0], "blader2": group_tops[1][1], "completed": False}, {"id": f"semi2-{int(time.time())}", "blader1": group_tops[1][0], "blader2": group_tops[0][1], "completed": False}]})
                    knockout.append({"name": "Grande Final", "matches": [{"id": f"final-{int(time.time())}", "blader1": None, "blader2": None, "completed": False}]})
            
            fresh_tourn["knockout"] = knockout; fresh_tourn["status"] = "knockout"; save_tournament(fresh_tourn)
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
            ]), padding=ft.padding.symmetric(vertical=4, horizontal=8), border=ft.border.only(bottom=ft.BorderSide(1, C_BORDER))))
            
            for idx, st in enumerate(sorted_st):
                is_top = idx < 2
                g_col.controls.append(ft.Container(content=ft.Row([
                    ft.Text(str(idx+1), width=20, size=14, color=C_TEXT_PRI if is_top else C_TEXT_SEC, weight=ft.FontWeight.W_600 if is_top else ft.FontWeight.NORMAL), 
                    ft.Text(st["name"], expand=True, size=14, color=C_TEXT_PRI, overflow=ft.TextOverflow.ELLIPSIS), 
                    ft.Text(str(st["j"]), width=25, size=14, color=C_TEXT_SEC, text_align="center"), 
                    ft.Text(str(st["v"]), width=25, size=14, color=C_TEXT_SEC, text_align="center"), 
                    ft.Text(str(st["pf"]), width=25, size=14, color=C_TEXT_SEC, text_align="center"), 
                    ft.Text(str(st["saldo"]), width=30, size=14, color=C_SUCCESS if st["saldo"] > 0 else C_ERROR, text_align="center", weight=ft.FontWeight.W_500)
                ]), padding=ft.padding.symmetric(vertical=8, horizontal=8), bgcolor=C_SURFACE_SEC if is_top else "transparent", border_radius=8))
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
                    if match.get("blader1") is None or match.get("blader2") is None:
                        view_matamata.controls.append(AppCard(ft.Text("Aguardando definição...", color=C_TEXT_SEC, size=13, text_align="center"), padding=16))
                    else:
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
                            status_ui = PrimaryBtn("Jogar", go_to_match, height=36, width=80, data={"is_knockout": True, "round_idx": r_idx, "match_id": match.get("id"), "b1_id": match.get("blader1"), "b1_name": b1_name, "b2_id": match.get("blader2"), "b2_name": b2_name})
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
                    IconButton(ft.Icons.POWER_SETTINGS_NEW, prompt_end_tourn, color=C_ERROR)
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
                for m in r.get("matches", []):
                    if m.get("completed"):
                        res = m.get("result", {})
                        b1_n = bladers_map.get(m.get("blader1"), "Blader Removido")
                        b2_n = bladers_map.get(m.get("blader2"), "Blader Removido")
                        pts1 = res.get("blader1Result", {}).get("totalPoints", 0)
                        pts2 = res.get("blader2Result", {}).get("totalPoints", 0)
                        status_ui = ft.Row([
                            ft.Text(f"{pts1} - {pts2}", color=C_PRIMARY, weight=ft.FontWeight.BOLD, size=16), 
                            IconButton(ft.Icons.INFO_OUTLINE, lambda e, md=m: open_match_details(md, t_data))
                        ])
                        view_tabelas.controls.append(AppCard(ft.Row([ft.Text(b1_n, size=14, color=C_TEXT_PRI), status_ui, ft.Text(b2_n, size=14, color=C_TEXT_PRI)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12))

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
        """Motor que roda em segundo plano para manter as telas de todos os celulares iguais"""
        global is_syncing
        while True:
            time.sleep(5) 
            
            # Se o aplicativo estiver salvando algum dado importante, o motor ESPERA.
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
