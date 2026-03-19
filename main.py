import flet as ft
import time
import math
import json
import os
from datetime import datetime

# Cores Oficiais
C_PRIMARY = "#ff6b00"
C_BG = "#0a0a0a"
C_SURFACE = "#1a1a1a"
C_SPIN = "#4CAF50"
C_OVER = "#2196F3"
C_BURST = "#9C27B0"

# ==========================================
# 1. BASE DE DADOS (Nativo do Python)
# ==========================================
DB_FILE = "beyblade_data.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"bladers": [], "tournament": None, "active_match": None, "history": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

app_data = load_db()

def get_bladers(): return app_data.get("bladers", [])
def save_bladers(bladers_list): 
    app_data["bladers"] = bladers_list
    save_db(app_data)

def get_tournament(): return app_data.get("tournament")
def save_tournament(tourn_data):
    app_data["tournament"] = tourn_data
    save_db(app_data)

def get_active_match(): return app_data.get("active_match")
def set_active_match(match_data):
    app_data["active_match"] = match_data
    save_db(app_data)

def get_history(): return app_data.get("history", [])
def add_to_history(tourn_data):
    hist = get_history()
    hist.insert(0, tourn_data)
    app_data["history"] = hist
    save_db(app_data)

# ==========================================
# 2. COMPONENTES BLINDADOS 
# ==========================================
def border_all(width, color):
    return ft.border.only(
        top=ft.BorderSide(width, color), bottom=ft.BorderSide(width, color),
        left=ft.BorderSide(width, color), right=ft.BorderSide(width, color)
    )

def CustomBtn(text, on_click, bgcolor=C_PRIMARY, color="white", width=None, height=None, data=None, icon=None):
    content_items = []
    if icon:
        content_items.append(ft.Icon(icon, color=color, size=18))
    content_items.append(ft.Text(text, color=color, weight=ft.FontWeight.BOLD))
    
    return ft.Container(
        content=ft.Row(content_items, alignment=ft.MainAxisAlignment.CENTER, spacing=5) if icon else ft.Text(text, color=color, weight=ft.FontWeight.BOLD),
        bgcolor=bgcolor,
        padding=ft.padding.symmetric(horizontal=15, vertical=10),
        border_radius=8,
        alignment=ft.Alignment(0, 0),
        width=width,
        height=height,
        on_click=on_click,
        data=data
    )

def IconBtn(icon, on_click, color=C_PRIMARY):
    return ft.Container(content=ft.Icon(icon, color=color), padding=ft.padding.all(8), on_click=on_click)

# ==========================================
# 3. O APLICATIVO PRINCIPAL
# ==========================================
def main(page: ft.Page):
    page.title = "Beyblade X Counter"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = C_BG
    page.padding = 0
    page.window.width = 450
    page.window.height = 800

    history_state = {"active_tourn": None, "sub_tab": "tabelas"}

    def show_dialog(dlg):
        if dlg not in page.overlay: page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def hide_dialog(dlg):
        dlg.open = False
        page.update()

    def show_alert(message, is_error=False):
        color = "red" if is_error else C_PRIMARY
        dlg = ft.AlertDialog(title=ft.Text(message, color=color, size=18))
        dlg.actions = [CustomBtn("OK", lambda _: hide_dialog(dlg), bgcolor="transparent", color=C_PRIMARY)]
        show_dialog(dlg)

    # --- TELA 1: INÍCIO ---
    def build_home_view():
        bladers = get_bladers()
        blader_input = ft.TextField(hint_text="Nome do Blader", expand=True, bgcolor=C_BG, border_color="#333")
        
        def add_blader(e):
            if blader_input.value.strip():
                b_list = get_bladers()
                b_list.append({"id": str(int(time.time())), "name": blader_input.value.strip()})
                save_bladers(b_list)
                blader_input.value = ""
                refresh_current_tab()

        def remove_blader(b_id):
            b_list = [b for b in get_bladers() if b["id"] != b_id]
            save_bladers(b_list)
            refresh_current_tab()

        bladers_list_ui = ft.ListView(expand=True, spacing=10)
        for b in bladers:
            bladers_list_ui.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(b["name"], weight=ft.FontWeight.BOLD, expand=True),
                        IconBtn(ft.Icons.DELETE, lambda e, bid=b["id"]: remove_blader(bid), color="red")
                    ]),
                    padding=10, bgcolor=C_SURFACE, border_radius=8, border=border_all(1, "#333")
                )
            )

        def open_create_tourn_dialog(e):
            b_list = get_bladers()
            if len(b_list) < 2:
                show_alert("Cadastre pelo menos 2 bladers!", is_error=True)
                return 
            
            max_groups = max(1, len(b_list) // 2)
            options = [ft.dropdown.Option(key=str(i), text=f"{i} Grupo(s)") for i in range(1, max_groups + 1)]
            dd_groups = ft.Dropdown(options=options, value="1", width=200, bgcolor=C_BG, color="white")
            
            default_name = f"Torneio {datetime.now().strftime('%d/%m/%Y')}"
            name_input = ft.TextField(label="Nome do Torneio", value=default_name, bgcolor=C_BG, border_color="#333", width=float("inf"))

            def confirm_create(e):
                group_count = int(dd_groups.value)
                groups = []
                bladers_per_group = math.ceil(len(b_list) / group_count)

                for i in range(group_count):
                    group_bladers = b_list[i * bladers_per_group : (i + 1) * bladers_per_group]
                    matches = []
                    for j in range(len(group_bladers)):
                        for k in range(j + 1, len(group_bladers)):
                            matches.append({
                                "id": f"{i}-{j}-{k}-{int(time.time())}",
                                "groupId": f"group-{i}",
                                "blader1": group_bladers[j]["id"],
                                "blader2": group_bladers[k]["id"],
                                "completed": False
                            })
                    groups.append({
                        "id": f"group-{i}",
                        "name": f"Grupo {chr(65 + i)}",
                        "bladerIds": [b["id"] for b in group_bladers],
                        "matches": matches
                    })

                t_name = name_input.value.strip() or "Torneio Beyblade X"
                tournament = {
                    "id": str(int(time.time())), "name": t_name, "date": datetime.now().strftime('%d/%m/%Y %H:%M'),
                    "groups": groups, "status": "groups", "knockout": []
                }
                save_tournament(tournament)
                hide_dialog(dlg)
                bottom_nav.selected_index = 2
                change_tab_programmatic(2)
            
            dlg = ft.AlertDialog(
                title=ft.Text("Configurar Torneio", color=C_PRIMARY),
                content=ft.Column([name_input, ft.Text("Quantos grupos deseja criar?", margin=ft.margin.only(top=10)), dd_groups], tight=True),
                actions=[CustomBtn("Cancelar", lambda _: hide_dialog(dlg), bgcolor="transparent", color="#999"), CustomBtn("Criar Torneio", confirm_create)]
            )
            show_dialog(dlg)

        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("BEYBLADE X", size=32, weight=ft.FontWeight.BOLD, color=C_PRIMARY),
                ft.Text("Gerenciar Bladers", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([blader_input, CustomBtn("ADD", add_blader)]),
                ft.Container(height=200, content=bladers_list_ui),
                ft.Divider(color="#333"),
                CustomBtn("CRIAR NOVO TORNEIO", open_create_tourn_dialog, bgcolor=C_SPIN, width=float("inf"), height=50)
            ])
        )

    # --- TELA 2: PARTIDA RÁPIDA (Com Inputs para Modo Casual) ---
    def build_quick_match_view():
        active_match = get_active_match()
        is_tournament = active_match is not None

        state = {
            "p1_score": 0, "p2_score": 0,
            "p1_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0},
            "p2_finishes": {"spin": 0, "over": 0, "burst": 0, "xtreme": 0},
            "match_ended": False
        }
        
        score_p1 = ft.Text("0", size=72, weight=ft.FontWeight.BOLD, color=C_PRIMARY)
        score_p2 = ft.Text("0", size=72, weight=ft.FontWeight.BOLD, color=C_PRIMARY)

        # Lógica de Nomes (Travado no Torneio, Editável no Casual)
        if is_tournament:
            p1_display = ft.Text(active_match["b1_name"], size=18, color="white", weight=ft.FontWeight.BOLD, text_align="center")
            p2_display = ft.Text(active_match["b2_name"], size=18, color="white", weight=ft.FontWeight.BOLD, text_align="center")
            get_p1_name = lambda: active_match["b1_name"]
            get_p2_name = lambda: active_match["b2_name"]
        else:
            p1_input = ft.TextField(value="Jogador 1", text_align=ft.TextAlign.CENTER, border_color=C_PRIMARY, color="white", width=150, text_size=16)
            p2_input = ft.TextField(value="Jogador 2", text_align=ft.TextAlign.CENTER, border_color=C_PRIMARY, color="white", width=150, text_size=16)
            p1_display = p1_input
            p2_display = p2_input
            get_p1_name = lambda: p1_input.value.strip() or "Jogador 1"
            get_p2_name = lambda: p2_input.value.strip() or "Jogador 2"

        def close_and_redirect(dlg):
            hide_dialog(dlg)
            bottom_nav.selected_index = 2
            change_tab_programmatic(2)

        def process_win():
            state["match_ended"] = True
            n1 = get_p1_name()
            n2 = get_p2_name()
            winner = n1 if state["p1_score"] > state["p2_score"] else n2
            
            dlg = ft.AlertDialog(title=ft.Text(f"🏆 {winner} Venceu!", color=C_PRIMARY))

            if is_tournament:
                tourn = get_tournament()
                w_id = active_match["b1_id"] if state["p1_score"] > state["p2_score"] else active_match["b2_id"]
                
                if active_match.get("is_knockout"):
                    r_idx = active_match["round_idx"]
                    round_data = tourn["knockout"][r_idx]
                    for m in round_data["matches"]:
                        if m["id"] == active_match["match_id"]:
                            m["completed"] = True
                            m["result"] = {"blader1Result": {"bladerId": active_match["b1_id"], "totalPoints": state["p1_score"], "finishes": state["p1_finishes"]}, "blader2Result": {"bladerId": active_match["b2_id"], "totalPoints": state["p2_score"], "finishes": state["p2_finishes"]}, "winner": w_id}
                    
                    all_completed = all(m.get("completed") for m in round_data["matches"])
                    if all_completed and r_idx + 1 < len(tourn["knockout"]):
                        winners = [m["result"]["winner"] for m in round_data["matches"]]
                        next_round = tourn["knockout"][r_idx + 1]
                        if len(next_round["matches"]) == 1 and len(winners) == 2:
                            next_round["matches"][0]["blader1"] = winners[0]
                            next_round["matches"][0]["blader2"] = winners[1]
                else:
                    for g in tourn["groups"]:
                        if g["id"] == active_match["group_id"]:
                            for m in g["matches"]:
                                if m["id"] == active_match["match_id"]:
                                    m["completed"] = True
                                    m["result"] = {"blader1Result": {"bladerId": active_match["b1_id"], "totalPoints": state["p1_score"], "finishes": state["p1_finishes"]}, "blader2Result": {"bladerId": active_match["b2_id"], "totalPoints": state["p2_score"], "finishes": state["p2_finishes"]}, "winner": w_id}
                
                save_tournament(tourn)
                set_active_match(None) 
                
                dlg.content = ft.Text("O resultado foi salvo automaticamente na tabela.")
                dlg.actions = [CustomBtn("VOLTAR AO TORNEIO", lambda _: close_and_redirect(dlg))]
            else:
                # Partida Casual (Fora do Torneio)
                dlg.content = ft.Text("Partida Amistosa finalizada!")
                dlg.actions = [CustomBtn("Ok", lambda _: hide_dialog(dlg))]

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
            state["p1_finishes"] = {"spin": 0, "over": 0, "burst": 0, "xtreme": 0}
            state["p2_finishes"] = {"spin": 0, "over": 0, "burst": 0, "xtreme": 0}
            state["match_ended"] = False
            score_p1.value, score_p2.value = "0", "0"
            page.update()

        def create_buttons(p):
            return ft.Column([
                CustomBtn("XTREME (+3)", lambda _: add_points(p, 3, "xtreme"), width=150, height=45),
                CustomBtn("BURST (+2)", lambda _: add_points(p, 2, "burst"), bgcolor=C_BURST, width=150, height=45),
                CustomBtn("OVER (+2)", lambda _: add_points(p, 2, "over"), bgcolor=C_OVER, width=150, height=45),
                CustomBtn("SPIN (+1)", lambda _: add_points(p, 1, "spin"), bgcolor=C_SPIN, width=150, height=45),
            ], alignment=ft.MainAxisAlignment.CENTER)

        banner_txt = "🔥 PARTIDA DE MATA-MATA" if is_tournament and active_match.get("is_knockout") else "🏆 PARTIDA DE TORNEIO"
        tourn_banner = ft.Container(content=ft.Text(banner_txt, color=C_BG, weight=ft.FontWeight.BOLD, text_align="center"), bgcolor=C_PRIMARY if not (is_tournament and active_match.get("is_knockout")) else "red", width=float("inf"), padding=5) if is_tournament else ft.Container(content=ft.Text("⚡ PARTIDA CASUAL", color=C_BG, weight=ft.FontWeight.BOLD, text_align="center"), bgcolor=C_SPIN, width=float("inf"), padding=5)

        return ft.Container(
            padding=0,
            content=ft.Column([
                tourn_banner,
                ft.Container(padding=20, content=ft.Column([
                    ft.Row([ft.Column([p1_display, score_p1], horizontal_alignment=ft.CrossAxisAlignment.CENTER), create_buttons(1)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(content=ft.Text("VS", size=24, weight=ft.FontWeight.BOLD, color="white"), alignment=ft.Alignment(0,0), margin=ft.margin.symmetric(vertical=15)),
                    ft.Row([ft.Column([p2_display, score_p2], horizontal_alignment=ft.CrossAxisAlignment.CENTER), create_buttons(2)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(color="#333"),
                    CustomBtn("🔄 RESETAR PLACAR", reset, bgcolor=C_SURFACE, color=C_PRIMARY, width=float("inf"), height=50)
                ]))
            ])
        )

    # --- TELA 3: TORNEIO E MATA-MATA ---
    def build_tournament_view():
        tourn = get_tournament()
        if not tourn: return ft.Container(content=ft.Text("Nenhum Torneio Ativo.", color="white54", size=18), alignment=ft.Alignment(0,0), expand=True)

        bladers_map = {b["id"]: b["name"] for b in get_bladers()}
        t_state = {"tab": "grupos"}
        
        def get_group_standings(group):
            standings = {b_id: {"id": b_id, "name": bladers_map.get(b_id, "???"), "j":0, "v":0, "d":0, "pf":0, "ps":0, "saldo":0, "xtreme":0} for b_id in group["bladerIds"]}
            for match in group["matches"]:
                if match.get("completed"):
                    res = match["result"]
                    b1, b2, w = res["blader1Result"], res["blader2Result"], res["winner"]
                    for bx, bx_data in [(b1, standings[b1["bladerId"]]), (b2, standings[b2["bladerId"]])]:
                        bx_data["j"] += 1
                        bx_data["pf"] += bx["totalPoints"]
                        bx_data["xtreme"] += bx["finishes"].get("xtreme", 0)
                        if w == bx["bladerId"]: bx_data["v"] += 1
                        else: bx_data["d"] += 1
                    standings[b1["bladerId"]]["ps"] += b2["totalPoints"]
                    standings[b2["bladerId"]]["ps"] += b1["totalPoints"]
            for s in standings.values(): s["saldo"] = s["pf"] - s["ps"]
            return sorted(standings.values(), key=lambda x: (x["saldo"], x["xtreme"], x["pf"]), reverse=True)

        def advance_to_knockout(e):
            group_tops = []
            for g in tourn["groups"]:
                st = get_group_standings(g)
                if len(st) >= 2: group_tops.append([st[0]["id"], st[1]["id"]])
                elif len(st) == 1: group_tops.append([st[0]["id"], None])
            
            knockout = []
            if len(tourn["groups"]) == 1:
                knockout.append({"name": "Grande Final", "matches": [{"id": f"final-{int(time.time())}", "blader1": group_tops[0][0], "blader2": group_tops[0][1], "completed": False}]})
            else:
                knockout.append({"name": "Semifinais", "matches": [{"id": f"semi1-{int(time.time())}", "blader1": group_tops[0][0], "blader2": group_tops[1][1], "completed": False}, {"id": f"semi2-{int(time.time())}", "blader1": group_tops[1][0], "blader2": group_tops[0][1], "completed": False}]})
                knockout.append({"name": "Grande Final", "matches": [{"id": f"final-{int(time.time())}", "blader1": None, "blader2": None, "completed": False}]})
            
            tourn["knockout"] = knockout
            tourn["status"] = "knockout"
            save_tournament(tourn)
            switch_sub_tab("matamata")

        view_grupos = ft.ListView(expand=True, spacing=15, padding=ft.padding.only(top=10))
        view_partidas = ft.ListView(expand=True, spacing=10, padding=ft.padding.only(top=10))
        view_matamata = ft.ListView(expand=True, spacing=10, padding=ft.padding.only(top=10))

        def go_to_match(e):
            set_active_match(e.control.data)
            bottom_nav.selected_index = 1
            change_tab_programmatic(1)

        for group in tourn["groups"]:
            sorted_st = get_group_standings(group)
            group_container = ft.Column([ft.Text(group["name"], size=20, weight=ft.FontWeight.BOLD, color=C_PRIMARY)])
            group_container.controls.append(ft.Container(content=ft.Row([ft.Text("#", width=20, weight=ft.FontWeight.BOLD, color=C_PRIMARY), ft.Text("Blader", width=90, weight=ft.FontWeight.BOLD, color=C_PRIMARY), ft.Text("J", width=25, weight=ft.FontWeight.BOLD, color=C_PRIMARY), ft.Text("V", width=25, weight=ft.FontWeight.BOLD, color=C_PRIMARY), ft.Text("PF", width=25, weight=ft.FontWeight.BOLD, color=C_PRIMARY), ft.Text("Sld", width=40, weight=ft.FontWeight.BOLD, color=C_PRIMARY)]), bgcolor=C_BG, padding=ft.padding.symmetric(vertical=8, horizontal=5)))
            for idx, st in enumerate(sorted_st):
                group_container.controls.append(ft.Container(content=ft.Row([ft.Text(str(idx+1), width=20, color="white"), ft.Text(st["name"], width=90, color="white", overflow=ft.TextOverflow.ELLIPSIS), ft.Text(str(st["j"]), width=25, color="white"), ft.Text(str(st["v"]), width=25, color="white"), ft.Text(str(st["pf"]), width=25, color="white"), ft.Text(str(st["saldo"]), width=40, color=C_SPIN if st["saldo"] > 0 else "red", weight=ft.FontWeight.BOLD)]), padding=ft.padding.symmetric(vertical=8, horizontal=5), bgcolor="#0d2818" if idx < 2 else None))
            view_grupos.controls.append(ft.Container(content=group_container, bgcolor=C_SURFACE, padding=15, border_radius=10))

            view_partidas.controls.append(ft.Text(group["name"], size=18, weight=ft.FontWeight.BOLD, color=C_PRIMARY, margin=ft.margin.only(top=10)))
            for match in group["matches"]:
                b1_name, b2_name = bladers_map.get(match["blader1"], "???"), bladers_map.get(match["blader2"], "???")
                if match.get("completed"):
                    res = match["result"]
                    status_ui = ft.Row([ft.Text(f"{res['blader1Result']['totalPoints']} - {res['blader2Result']['totalPoints']}", color=C_SPIN, weight=ft.FontWeight.BOLD, size=18), ft.Icon(ft.Icons.CHECK_CIRCLE, color=C_SPIN)])
                else:
                    status_ui = CustomBtn("JOGAR", go_to_match, icon=ft.Icons.PLAY_ARROW, data={"match_id": match["id"], "group_id": group["id"], "b1_id": match["blader1"], "b1_name": b1_name, "b2_id": match["blader2"], "b2_name": b2_name})
                view_partidas.controls.append(ft.Container(content=ft.Row([ft.Column([ft.Text(b1_name, weight=ft.FontWeight.BOLD), ft.Text("VS", size=10, color="white54"), ft.Text(b2_name, weight=ft.FontWeight.BOLD)]), status_ui], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), bgcolor=C_SURFACE, padding=15, border_radius=10, border=border_all(1, "#333")))

        if tourn.get("status") == "groups":
            view_grupos.controls.append(CustomBtn("🔥 AVANÇAR PARA MATA-MATA", advance_to_knockout, bgcolor="red", width=float("inf"), height=50))
        
        if tourn.get("knockout"):
            for r_idx, round_data in enumerate(tourn["knockout"]):
                view_matamata.controls.append(ft.Text(round_data["name"], size=18, weight=ft.FontWeight.BOLD, color="red", margin=ft.margin.only(top=10)))
                for match in round_data["matches"]:
                    if match["blader1"] is None or match["blader2"] is None:
                        view_matamata.controls.append(ft.Container(content=ft.Text("Aguardando Vencedores...", color="white54", weight=ft.FontWeight.BOLD, text_align="center"), bgcolor=C_SURFACE, padding=15, border_radius=10, border=border_all(1, "#333")))
                    else:
                        b1_name, b2_name = bladers_map.get(match["blader1"], "???"), bladers_map.get(match["blader2"], "???")
                        if match.get("completed"):
                            res = match["result"]
                            status_ui = ft.Row([ft.Text(f"{res['blader1Result']['totalPoints']} - {res['blader2Result']['totalPoints']}", color=C_SPIN, weight=ft.FontWeight.BOLD, size=18), ft.Icon(ft.Icons.EMOJI_EVENTS, color=C_SPIN)])
                        else:
                            status_ui = CustomBtn("JOGAR", go_to_match, icon=ft.Icons.PLAY_ARROW, bgcolor="red", data={"is_knockout": True, "round_idx": r_idx, "match_id": match["id"], "b1_id": match["blader1"], "b1_name": b1_name, "b2_id": match["blader2"], "b2_name": b2_name})
                        view_matamata.controls.append(ft.Container(content=ft.Row([ft.Column([ft.Text(b1_name, weight=ft.FontWeight.BOLD), ft.Text("VS", size=10, color="white54"), ft.Text(b2_name, weight=ft.FontWeight.BOLD)]), status_ui], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), bgcolor=C_SURFACE, padding=15, border_radius=10, border=border_all(1, "red" if not match.get("completed") else C_SPIN)))

        tab_nav_container = ft.Container(padding=ft.padding.symmetric(horizontal=20))
        content_switcher = ft.Container(content=view_grupos, expand=True)

        def build_tab_row():
            uid = str(time.time())
            is_g = t_state["tab"] == "grupos"
            is_p = t_state["tab"] == "partidas"
            is_m = t_state["tab"] == "matamata"

            tabs = [
                ft.Container(key=f"cg_{uid}", content=ft.Text("🏆 GRUPOS", key=f"tg_{uid}", weight=ft.FontWeight.BOLD, color="white" if is_g else "white54"), expand=True, bgcolor=C_PRIMARY if is_g else C_SURFACE, padding=10, alignment=ft.Alignment(0,0), on_click=lambda _: switch_sub_tab("grupos")),
                ft.Container(key=f"cp_{uid}", content=ft.Text("⚔️ PARTIDAS", key=f"tp_{uid}", weight=ft.FontWeight.BOLD, color="white" if is_p else "white54"), expand=True, bgcolor=C_PRIMARY if is_p else C_SURFACE, padding=10, alignment=ft.Alignment(0,0), on_click=lambda _: switch_sub_tab("partidas"))
            ]
            
            if tourn.get("status") == "knockout":
                tabs.append(ft.Container(key=f"cm_{uid}", content=ft.Text("🔥 MATA-MATA", key=f"tm_{uid}", weight=ft.FontWeight.BOLD, color="white" if is_m else "white54"), expand=True, bgcolor="red" if is_m else C_SURFACE, padding=10, alignment=ft.Alignment(0,0), on_click=lambda _: switch_sub_tab("matamata")))
            
            tab_nav_container.content = ft.Row(tabs, spacing=5, key=f"row_{uid}")

        def switch_sub_tab(tab_name):
            t_state["tab"] = tab_name
            build_tab_row()
            if tab_name == "grupos": content_switcher.content = view_grupos
            elif tab_name == "partidas": content_switcher.content = view_partidas
            elif tab_name == "matamata": content_switcher.content = view_matamata
            page.update()

        build_tab_row() 

        def prompt_end_tourn(e):
            def handle_action(action):
                if action == "salvar": add_to_history(tourn)
                save_tournament(None)
                set_active_match(None)
                hide_dialog(dlg)
                refresh_current_tab()

            dlg = ft.AlertDialog(
                title=ft.Text("Encerrar Torneio", color=C_PRIMARY),
                content=ft.Text("O que deseja fazer com este torneio?"),
                actions=[
                    CustomBtn("Excluir", lambda _: handle_action("excluir"), bgcolor="red"),
                    CustomBtn("Salvar Histórico", lambda _: handle_action("salvar"), bgcolor=C_SPIN),
                    CustomBtn("Cancelar", lambda _: hide_dialog(dlg), bgcolor="transparent", color="white54")
                ]
            )
            show_dialog(dlg)

        return ft.Container(
            padding=0,
            content=ft.Column([
                ft.Container(content=ft.Row([
                    ft.Column([ft.Text(tourn["name"], size=24, weight=ft.FontWeight.BOLD, color=C_PRIMARY), ft.Text("Gestão", color="white54")]),
                    IconBtn(ft.Icons.STOP_CIRCLE, prompt_end_tourn, color="red")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=ft.padding.only(left=20, right=20, top=20)),
                tab_nav_container,
                ft.Container(content=content_switcher, padding=ft.padding.only(left=20, right=20, bottom=20), expand=True)
            ])
        )

    # --- TELA 4: HISTÓRICO ---
    def build_history_view():
        if history_state["active_tourn"]:
            t_data = history_state["active_tourn"]
            bladers_map = {b["id"]: b["name"] for b in get_bladers()}
            
            stats = {}
            def process_stats(m):
                if m.get("completed"):
                    res = m["result"]
                    w = res["winner"]
                    for b_key in ["blader1Result", "blader2Result"]:
                        b_res = res[b_key]
                        bid = b_res["bladerId"]
                        if bid not in stats:
                            stats[bid] = {"name": bladers_map.get(bid, "Deletado"), "j":0, "v":0, "pts":0, "spin":0, "over":0, "burst":0, "xtreme":0}
                        stats[bid]["j"] += 1
                        stats[bid]["pts"] += b_res["totalPoints"]
                        f_data = b_res.get("finishes", {})
                        stats[bid]["spin"] += f_data.get("spin", 0)
                        stats[bid]["over"] += f_data.get("over", 0)
                        stats[bid]["burst"] += f_data.get("burst", 0)
                        stats[bid]["xtreme"] += f_data.get("xtreme", 0)
                        if w == bid: stats[bid]["v"] += 1

            for g in t_data.get("groups", []):
                for m in g.get("matches", []): process_stats(m)
            for r in t_data.get("knockout", []):
                for m in r.get("matches", []): process_stats(m)
                
            sorted_stats = sorted(stats.values(), key=lambda x: (x["v"], x["pts"], x["xtreme"]), reverse=True)

            view_tabelas = ft.ListView(expand=True, spacing=15, padding=ft.padding.only(top=10))
            for g in t_data.get("groups", []):
                view_tabelas.controls.append(ft.Text(f"Tabela - {g['name']}", size=18, weight=ft.FontWeight.BOLD, color=C_PRIMARY))
                for m in g.get("matches", []):
                    if m.get("completed"):
                        res = m["result"]
                        b1_n, b2_n = bladers_map.get(m["blader1"], "???"), bladers_map.get(m["blader2"], "???")
                        pts_str = f"{res['blader1Result']['totalPoints']} - {res['blader2Result']['totalPoints']}"
                        view_tabelas.controls.append(ft.Container(content=ft.Row([ft.Text(b1_n), ft.Text(pts_str, color=C_SPIN, weight=ft.FontWeight.BOLD), ft.Text(b2_n)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), bgcolor=C_SURFACE, padding=10, border_radius=5))
            
            for r in t_data.get("knockout", []):
                view_tabelas.controls.append(ft.Text(r["name"], size=18, weight=ft.FontWeight.BOLD, color="red", margin=ft.margin.only(top=10)))
                for m in r.get("matches", []):
                    if m.get("completed"):
                        res = m["result"]
                        b1_n, b2_n = bladers_map.get(m["blader1"], "???"), bladers_map.get(m["blader2"], "???")
                        pts_str = f"{res['blader1Result']['totalPoints']} - {res['blader2Result']['totalPoints']}"
                        view_tabelas.controls.append(ft.Container(content=ft.Row([ft.Text(b1_n), ft.Text(pts_str, color=C_SPIN, weight=ft.FontWeight.BOLD), ft.Text(b2_n)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), bgcolor=C_SURFACE, padding=10, border_radius=5))

            view_stats = ft.ListView(expand=True, spacing=10, padding=ft.padding.only(top=10))
            stats_header = ft.Container(content=ft.Row([
                ft.Text("Blader", width=90, weight=ft.FontWeight.BOLD, color=C_PRIMARY),
                ft.Text("J", width=25, weight=ft.FontWeight.BOLD, color=C_PRIMARY),
                ft.Text("V", width=25, weight=ft.FontWeight.BOLD, color=C_PRIMARY),
                ft.Text("Pts", width=30, weight=ft.FontWeight.BOLD, color=C_PRIMARY),
                ft.Text("SP", width=25, weight=ft.FontWeight.BOLD, color=C_SPIN),
                ft.Text("OV", width=25, weight=ft.FontWeight.BOLD, color=C_OVER),
                ft.Text("BU", width=25, weight=ft.FontWeight.BOLD, color=C_BURST),
                ft.Text("XT", width=25, weight=ft.FontWeight.BOLD, color=C_PRIMARY),
            ]), bgcolor=C_BG, padding=10, border_radius=5)
            view_stats.controls.append(stats_header)

            for st in sorted_stats:
                view_stats.controls.append(ft.Container(content=ft.Row([
                    ft.Text(st["name"], width=90, color="white", overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(str(st["j"]), width=25, color="white"),
                    ft.Text(str(st["v"]), width=25, color="white"),
                    ft.Text(str(st["pts"]), width=30, color="white", weight=ft.FontWeight.BOLD),
                    ft.Text(str(st["spin"]), width=25, color=C_SPIN),
                    ft.Text(str(st["over"]), width=25, color=C_OVER),
                    ft.Text(str(st["burst"]), width=25, color=C_BURST),
                    ft.Text(str(st["xtreme"]), width=25, color=C_PRIMARY),
                ]), padding=ft.padding.symmetric(horizontal=10, vertical=8), border=ft.border.only(bottom=ft.BorderSide(1, "#333"))))
            view_stats.controls.append(ft.Text("Legenda: J=Jogos | V=Vitórias | Pts=Pontos | SP=Spin | OV=Over | BU=Burst | XT=Xtreme", size=11, color="white54", margin=ft.margin.only(top=10)))

            hist_nav_container = ft.Container(padding=ft.padding.symmetric(horizontal=20))
            content_switcher = ft.Container(content=view_tabelas if history_state["sub_tab"] == "tabelas" else view_stats, expand=True)

            def build_hist_tab_row():
                uid = str(time.time())
                is_t = history_state["sub_tab"] == "tabelas"
                
                tabs = [
                    ft.Container(
                        key=f"hc_t_{uid}",
                        content=ft.Text("CHAVES", key=f"ht_t_{uid}", weight=ft.FontWeight.BOLD, color="white" if is_t else "white54"),
                        expand=True, bgcolor=C_PRIMARY if is_t else C_SURFACE, padding=10, alignment=ft.Alignment(0,0), 
                        on_click=lambda _: switch_det_tab("tabelas")
                    ),
                    ft.Container(
                        key=f"hc_s_{uid}",
                        content=ft.Text("ESTATÍSTICAS", key=f"ht_s_{uid}", weight=ft.FontWeight.BOLD, color="white" if not is_t else "white54"),
                        expand=True, bgcolor=C_PRIMARY if not is_t else C_SURFACE, padding=10, alignment=ft.Alignment(0,0), 
                        on_click=lambda _: switch_det_tab("estatisticas")
                    )
                ]
                hist_nav_container.content = ft.Row(tabs, spacing=5, key=f"hrow_{uid}")

            def switch_det_tab(tab_name):
                history_state["sub_tab"] = tab_name
                build_hist_tab_row()
                content_switcher.content = view_tabelas if tab_name == "tabelas" else view_stats
                page.update()
                
            build_hist_tab_row()

            def close_detail(e):
                history_state["active_tourn"] = None
                refresh_current_tab()

            return ft.Container(
                padding=0,
                content=ft.Column([
                    ft.Container(content=ft.Row([
                        IconBtn(ft.Icons.ARROW_BACK, close_detail, color="white"),
                        ft.Text(t_data["name"], size=20, weight=ft.FontWeight.BOLD, color=C_PRIMARY, expand=True),
                    ]), padding=ft.padding.only(left=10, right=20, top=20)),
                    hist_nav_container,
                    ft.Container(content=content_switcher, padding=ft.padding.only(left=20, right=20, bottom=20), expand=True)
                ])
            )

        hist = get_history()
        if not hist: return ft.Container(content=ft.Text("Nenhum torneio salvo.", color="white54", size=18), alignment=ft.Alignment(0,0), expand=True)

        list_ui = ft.ListView(expand=True, spacing=15, padding=20)
        list_ui.controls.append(ft.Text("HISTÓRICO", size=24, weight=ft.FontWeight.BOLD, color=C_PRIMARY))
        list_ui.controls.append(ft.Divider(color="#333"))
        
        def open_history_detail(t_data):
            history_state["active_tourn"] = t_data
            history_state["sub_tab"] = "tabelas"
            refresh_current_tab()

        for t in hist:
            list_ui.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([ft.Text(t["name"], weight=ft.FontWeight.BOLD, size=20, color="white"), ft.Text(f"Data: {t.get('date', '')}", color="white54")], expand=True),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C_PRIMARY)
                    ]), 
                    padding=15, bgcolor=C_SURFACE, border_radius=8, border=border_all(1, "#333"),
                    on_click=lambda e, data=t: open_history_detail(data)
                )
            )

        return ft.Container(content=list_ui, expand=True)

    # --- SISTEMA DE NAVEGAÇÃO PRINCIPAL ---
    content_area = ft.Container(expand=True)

    def change_tab_programmatic(index):
        content_area.content = None
        page.update()
        if index == 0: content_area.content = build_home_view()
        elif index == 1: content_area.content = build_quick_match_view()
        elif index == 2: content_area.content = build_tournament_view()
        elif index == 3: content_area.content = build_history_view()
        page.update()

    def change_tab(e): change_tab_programmatic(e.control.selected_index)
    def refresh_current_tab(): change_tab_programmatic(bottom_nav.selected_index)

    bottom_nav = ft.NavigationBar(
        bgcolor=C_BG, selected_index=0, on_change=change_tab,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Início"),
            ft.NavigationBarDestination(icon=ft.Icons.FLASH_ON_OUTLINED, selected_icon=ft.Icons.FLASH_ON, label="Partida"),
            ft.NavigationBarDestination(icon=ft.Icons.EMOJI_EVENTS_OUTLINED, selected_icon=ft.Icons.EMOJI_EVENTS, label="Torneio"),
            ft.NavigationBarDestination(icon=ft.Icons.HISTORY_OUTLINED, selected_icon=ft.Icons.HISTORY, label="Histórico"),
        ]
    )

    page.add(content_area, bottom_nav)
    change_tab_programmatic(0)

ft.run(main)