# -*- coding: utf-8 -*-
import flet as ft, time, math, json, threading, requests, random, csv, os
from datetime import datetime
from functools import cmp_to_key

C_BG, C_SUR, C_SURS, C_BOR = "#0B0B0F", "#15161A", "#1C1D22", "#2A2C33"
C_TXT, C_TXTS, C_PRI, C_SUC, C_ERR = "#F5F7FA", "#A7ADB7", "#FF7A00", "#22C55E", "#EF4444"
C_XT, C_BU, C_OV, C_SP, C_FL = C_PRI, "#A855F7", "#3B82F6", "#22C55E", "#EAB308"        
PTS_WIN, PTS_MAP = 4, {"xtreme":3, "burst":2, "over":2, "spin":1, "flag":1}
FB_URL = "https://beybladeapp-c303a-default-rtdb.firebaseio.com/beyblade_data_v2.json"

db = {"bladers":[], "tournaments":{}, "active_matches":{}, "history":[], "training_history":[], "users":{}, "last_updated":0}
is_s, dblk, on_s_st, on_s_en = False, threading.RLock(), None, None

def s_sync():
    if on_s_st: on_s_st()
    try:
        r = requests.get(FB_URL, timeout=5)
        if r.status_code == 200 and r.json():
            with dblk: 
                db.clear(); db.update(r.json())
                for k in ["users", "tournaments", "active_matches"]: db.setdefault(k, {})
                db.setdefault("training_history", []); db.setdefault("last_updated", 0)
    except: pass
    finally:
        if on_s_en: on_s_en()

def sv_db(dt):
    global is_s; is_s = True
    with dblk: dt["last_updated"] = int(time.time() * 1000); c = json.loads(json.dumps(dt)) 
    if on_s_st: on_s_st()
    def _bg(d):
        global is_s
        for _ in range(3):
            try:
                if requests.put(FB_URL, json=d, timeout=5).status_code == 200: break
            except: time.sleep(1.5)
        is_s = False
        if on_s_en: on_s_en()
    threading.Thread(target=_bg, args=(c,), daemon=True).start()
s_sync()

def gb(org):
    with dblk: return [b for b in json.loads(json.dumps(db.get("bladers", []))) if b.get("org", "admin") == org]
def sb(l, org): 
    for b in l: b["org"] = org
    with dblk: db["bladers"] = [b for b in db.get("bladers", []) if b.get("org", "admin") != org] + l
    sv_db(db)
def gt(org):
    with dblk: return json.loads(json.dumps(db.get("tournaments", {}).get(org)))
def st(dt, org): 
    with dblk:
        if dt is None: db.get("tournaments", {}).pop(org, None)
        else: db.setdefault("tournaments", {})[org] = dt
    sv_db(db)
def gh(org):
    with dblk: return [h for h in json.loads(json.dumps(db.get("history", []))) if h.get("org", "admin") == org]
def ah(dt, org):
    dt["org"] = org; 
    with dblk: db.setdefault("history", []).insert(0, dt)
    sv_db(db)
def gth(org):
    with dblk: return [h for h in json.loads(json.dumps(db.get("training_history", []))) if h.get("org", "admin") == org]
def ath(dt, org):
    dt["org"] = org; 
    with dblk: db.setdefault("training_history", []).insert(0, dt)
    sv_db(db)
def gu():
    with dblk: return json.loads(json.dumps(db.get("users", {})))
def su(ud):
    with dblk: db["users"] = ud; sv_db(db)

HC_U = {
    "themonc08": {"password": "150217bR*", "role": "admin_max", "org": "admin"}, 
    "caruso": {"password": "bladerbey01", "role": "pro", "org": "FBRJ"}, 
    "juiz_1": {"password": "beyjuiz1", "role": "organizador", "org": "FBRJ"}, 
    "juiz_2": {"password": "beyjuiz2", "role": "organizador", "org": "FBRJ"},
    "juiz_3": {"password": "beyjuiz3", "role": "organizador", "org": "FBRJ"},
    "juiz_4": {"password": "beyjuiz4", "role": "organizador", "org": "FBRJ"}
}

def gsg(grp, bm):
    stnd = {b: {"id":b, "name":bm.get(b, "Removido"), "j":0, "v":0, "d":0, "pf":0, "ps":0, "saldo":0, "xt":0} for b in grp.get("bladerIds", [])}
    h2h = {b: [] for b in grp.get("bladerIds", [])}
    for m in grp.get("matches", []):
        if m.get("completed"):
            r = m.get("result", {}); b1, b2, w = r.get("blader1Result", {}), r.get("blader2Result", {}), r.get("winner")
            if not b1 or not b2: continue
            id1, id2 = b1.get("bladerId"), b2.get("bladerId")
            if w == id1: h2h[id1].append(id2)
            elif w == id2: h2h[id2].append(id1)
            for bx, bd in [(b1, stnd.get(id1)), (b2, stnd.get(id2))]:
                if not bd: continue
                bd["j"]+=1; bd["pf"]+=bx.get("totalPoints", 0); bd["xt"]+=bx.get("finishes", {}).get("xtreme", 0)
                if w == bx.get("bladerId"): bd["v"]+=1
                else: bd["d"]+=1
            if stnd.get(id1): stnd[id1]["ps"] += b2.get("totalPoints", 0)
            if stnd.get(id2): stnd[id2]["ps"] += b1.get("totalPoints", 0)
    for s in stnd.values(): s["saldo"] = s["pf"] - s["ps"]
    def cmp_s(a, b):
        if a["v"] != b["v"]: return b["v"] - a["v"]
        if a["saldo"] != b["saldo"]: return b["saldo"] - a["saldo"]
        if b["id"] in h2h.get(a["id"], []): return -1
        if a["id"] in h2h.get(b["id"], []): return 1
        if a["xt"] != b["xt"]: return b["xt"] - a["xt"]
        return b["pf"] - a["pf"]
    return sorted(stnd.values(), key=cmp_to_key(cmp_s))

# COMPONENTES BLINDADOS DE DESIGN (ACEITAM NOMES ANTIGOS E NOVOS DE ARGUMENTOS)
def AC(c, p=16, clk=None, dt=None, bc=C_BOR, **k): return ft.Container(content=c, padding=k.get('padding', p), bgcolor=C_SUR, border_radius=16, border=ft.border.all(1, bc), on_click=clk, data=k.get('data', dt))
def PB(t, clk, w=None, h=48, ic=None, dt=None, c=C_PRI, exp=False, **k): return ft.Container(content=ft.Row([ft.Icon(k.get('icon', ic), color=C_TXT, size=20)] + [ft.Text(t, color=C_TXT, weight="w600", size=14)], alignment="center", spacing=8) if k.get('icon', ic) else ft.Text(t, color=C_TXT, weight="w600", size=14), bgcolor=k.get('color', c), padding=8, border_radius=12, alignment=ft.Alignment(0, 0), width=k.get('width', w), height=k.get('height', h), on_click=clk, data=k.get('data', dt), expand=k.get('expand', exp))
def SB(t, clk, w=None, h=48, ic=None, dt=None, exp=False, **k): return ft.Container(content=ft.Row([ft.Icon(k.get('icon', ic), color=C_TXTS, size=20)] + [ft.Text(t, color=C_TXTS, weight="w500", size=13)], alignment="center", spacing=8) if k.get('icon', ic) else ft.Text(t, color=C_TXTS, weight="w500", size=13), bgcolor=C_SURS, padding=8, border_radius=12, border=ft.border.all(1, C_BOR), alignment=ft.Alignment(0, 0), width=k.get('width', w), height=k.get('height', h), on_click=clk, data=k.get('data', dt), expand=k.get('expand', exp))
def IB(ic, clk, c=C_TXTS, tp=None, **k): return ft.Container(content=ft.Icon(ic, color=c, size=22), padding=10, border_radius=10, bgcolor=C_SURS, border=ft.border.all(1, C_BOR), on_click=clk, tooltip=k.get('tooltip', tp), data=k.get('data'))
def BDG(t, c): return ft.Container(content=ft.Text(t, size=11, weight="w600", color=c), padding=6, bgcolor=f"{c}15", border_radius=6, border=ft.border.all(1, f"{c}40"))
def CF(): return ft.Container(content=ft.Column([ft.Text("IDEALIZADO POR: GUILHERME CARUSO", size=10, color=C_TXTS, weight="bold", text_align="center"), ft.Text("DESENVOLVIDO POR: GUILHERME MONÇÃO", size=10, color=C_TXTS, weight="bold", text_align="center")], spacing=2, horizontal_alignment="center"), margin=ft.margin.only(top=24, bottom=12), width=float("inf"), alignment=ft.Alignment(0, 0))

def main(pg: ft.Page):
    pg.title, pg.theme_mode, pg.bgcolor, pg.padding = "Beyblade X System", ft.ThemeMode.DARK, C_BG, 0
    pg.fonts = {"Inter": "https://raw.githubusercontent.com/rsms/inter/master/docs/font-files/Inter-Regular.woff2"}
    pg.theme = ft.Theme(font_family="Inter")

    ast = {"cu": None, "avo": "admin", "uo": [], "ao": "default", "stk": None}
    def cu(): return ast["cu"]
    def adm(): return cu() and cu()["role"] == "admin_max"
    def htr(): return cu() and cu()["role"] in ["admin_max", "pro", "treinador"]
    def hto(): return cu() and cu()["role"] in ["admin_max", "pro", "organizador", "judge"]
    def co(): return ast["avo"] if adm() and ast.get("avo") != "admin" else (ast.get("ao") or cu().get("org", cu()["username"]))

    def lo(e=None, frc=False):
        ast.update({"cu": None, "avo": "admin", "stk": None})
        mac.visible, bn.visible, lc.visible = False, False, True; lc.content = bav(True)
        if frc: pg.snack_bar = ft.SnackBar(ft.Text("Conectado em outro lugar!"), bgcolor=C_ERR); pg.snack_bar.open = True
        pg.update()

    sr = ft.ProgressRing(width=16, height=16, color=C_PRI, stroke_width=2, visible=False)
    pg.appbar = ft.AppBar(title=ft.Text("Beyblade X", size=16, weight="bold", color=C_TXT), bgcolor=C_BG)
    
    def uab():
        ac = [ft.Container(content=sr, padding=ft.padding.only(right=10))]
        if adm() and ast.get("avo") != "admin": ac.append(ft.Container(content=ft.Text(f"SAIR: {ast['avo'].upper()}", color=C_TXT, weight="bold", size=11), bgcolor=C_ERR, padding=6, border_radius=8, margin=ft.margin.only(right=10), on_click=lambda _: [ast.update({"avo": "admin"}), uab(), rct()]))
        elif len(ast.get("uo", [])) > 1 and not adm(): ac.append(ft.Container(content=ft.Text(f"ORG: {co().upper()}", color=C_TXT, weight="bold", size=11), bgcolor=C_PRI, padding=6, border_radius=8, margin=ft.margin.only(right=10)))
        ac.append(ft.IconButton(ft.Icons.LOGOUT, icon_color=C_ERR, on_click=lo)); pg.appbar.actions = ac; pg.update()

    global on_s_st, on_s_en
    on_s_st = lambda: setattr(sr, 'visible', True) or pg.update(); on_s_en = lambda: setattr(sr, 'visible', False) or pg.update()
    def sdl(d): pg.overlay.append(d) if d not in pg.overlay else None; d.open = True; pg.update()
    def hdl(d): d.open = False; pg.update()

    def gsm(tc=None):
        bm = {b["id"]: b["name"] for b in gb(co())}
        if tc and "participants" in tc: bm.update(tc["participants"])
        return bm

    def omd(m, tc=None):
        bm = gsm(tc); r = m.get("result", {}); f1, f2 = r.get("blader1Result", {}).get("finishes", {}), r.get("blader2Result", {}).get("finishes", {})
        def fr(l, k, c): return ft.Row([ft.Text(str(f1.get(k,0)), color=c, weight="bold", size=16, width=30, text_align="center"), ft.Text(l, color=C_TXTS, expand=True, text_align="center", size=13), ft.Text(str(f2.get(k,0)), color=c, weight="bold", size=16, width=30, text_align="center")])
        d = ft.AlertDialog(bgcolor=C_SUR, shape=ft.RoundedRectangleBorder(radius=16), content_padding=24, title=ft.Text("Raio-X da Partida", color=C_TXT, weight="bold", size=18, text_align="center"), content=ft.Column([ft.Row([ft.Text(bm.get(m.get("blader1"),"W.O."), weight="w600", color=C_TXT, expand=True, text_align="center", size=14), ft.Text("VS", size=11, color=C_TXTS), ft.Text(bm.get(m.get("blader2"),"W.O."), weight="w600", color=C_TXT, expand=True, text_align="center", size=14)]), ft.Divider(color=C_BOR, height=20), fr("XTREME", "xtreme", C_XT), fr("BURST", "burst", C_BU), fr("OVER", "over", C_OV), fr("SPIN", "spin", C_SP), fr("FLAG", "flag", C_FL), ft.Divider(color=C_BOR, height=20), ft.Row([ft.Text(str(r.get("blader1Result", {}).get("totalPoints", 0)), size=24, color=C_PRI, weight="bold", width=30, text_align="center"), ft.Text("PONTOS GERAIS", color=C_TXT, weight="bold", expand=True, text_align="center", size=12), ft.Text(str(r.get("blader2Result", {}).get("totalPoints", 0)), size=24, color=C_PRI, weight="bold", width=30, text_align="center")])], tight=True), actions=[SB("Fechar", lambda _: hdl(d))]); sdl(d)

    lc = ft.Container(expand=True, padding=24)
    def bav(il=True):
        ui, pi, ei = ft.TextField(label="Usuário", bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, border_radius=12), ft.TextField(label="Senha", password=True, can_reveal_password=True, bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, border_radius=12), ft.TextField(label="Email", bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, border_radius=12, visible=not il)
        def au(e):
            u, p = ui.value.strip(), pi.value.strip()
            if not u or not p: pg.snack_bar = ft.SnackBar(ft.Text("Preencha tudo!"), bgcolor=C_ERR); pg.snack_bar.open = True; pg.update(); return
            s_sync(); du = gu(); ud = None
            if il:
                if u in du and (du[u].get("password")==p or (u in HC_U and HC_U[u]["password"]==p)): ud = du[u]; ud["password"] = p; su(du)
                elif u in HC_U and HC_U[u]["password"]==p: ud = HC_U[u].copy(); du[u] = ud; su(du)
                if ud:
                    tk = str(int(time.time()*1000))+str(random.randint(1000,9999)); ud["session_token"] = tk; du[u] = ud; su(du)
                    os = [o.strip() for o in ud.get("org", u).split(",") if o.strip()]
                    ast.update({"cu": {"username": u, "role": ud.get("role", "basic"), "org": ud.get("org", u)}, "uo": os, "ao": os[0] if os else u, "stk": tk}); sma(); return
                pg.snack_bar = ft.SnackBar(ft.Text("Login inválido!"), bgcolor=C_ERR); pg.snack_bar.open = True; pg.update()
            else:
                if u in HC_U or u in du: pg.snack_bar = ft.SnackBar(ft.Text("Usuário já existe!"), bgcolor=C_ERR); pg.snack_bar.open = True; pg.update(); return
                tk = str(int(time.time() * 1000)) + str(random.randint(1000, 9999))
                du[u] = {"password": p, "email": ei.value.strip(), "role": "basic", "org": u, "session_token": tk}; su(du)
                ast.update({"cu": {"username": u, "role": "basic", "org": u}, "uo": [u], "ao": u, "stk": tk}); sma()
        return ft.Column([ft.Container(height=40), ft.Icon(ft.Icons.SECURITY, size=64, color=C_PRI), ft.Text("Bem-vindo", size=24, weight="bold", color=C_TXT), ft.Container(height=20), ui, pi, PB("Entrar", au, width=float("inf")), ft.Container(expand=True)], horizontal_alignment="center")
    lc.content = bav()

    mac, bn = ft.Container(expand=True, visible=False), ft.NavigationBar(bgcolor=C_BG, indicator_color=C_SURS, visible=False, destinations=[ft.NavigationBarDestination(icon=ft.Icons.ABC, label="1"), ft.NavigationBarDestination(icon=ft.Icons.ABC, label="2")])
    hst, hos, tst, vst, trs = {"t": None, "sub": "tabelas"}, {"sub": "selecao", "ids": [], "tn": ""}, {"sub": None, "m": None, "ms": {}}, {"sub": "matamata"}, {"sub": "setup", "md": None, "p1s": 0, "p2s": 0, "p1f": {"spin":0,"over":0,"burst":0,"xtreme":0,"flag":0}, "p2f": {"spin":0,"over":0,"burst":0,"xtreme":0,"flag":0}, "ended": False}

    def bpv():
        uo = ast.get("uo", [co()]); cl = [ft.Container(height=50), ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color=C_TXTS), ft.Text(f"Olá, {cu()['username']}!", size=24, weight="bold", color=C_TXT)]
        if len(uo) > 1 and not adm():
            dd = ft.Dropdown(label="Ambiente", value=co(), options=[ft.dropdown.Option(o) for o in uo], bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, border_radius=12, width=200)
            def apl(e):
                if dd.value: ast["ao"] = str(dd.value); uab(); tst["sub"] = None; hst["t"] = None; hos["ids"].clear(); rct()
            cl.extend([ft.Container(height=10), ft.Row([dd, PB("OK", apl, width=120)], alignment="center")])
        else: cl.append(ft.Text(f"Ambiente: {co().upper()}", color=C_PRI, size=14, weight="bold"))
        cl.extend([ft.Container(height=10), BDG(cu().get("role", "basic").upper(), C_PRI), ft.Container(expand=True), ft.Divider(color=C_BOR), CF()])
        return ft.Container(padding=24, content=ft.Column(cl, horizontal_alignment="center", scroll="auto"))

    def btrv():
        if not htr(): return ft.Container(content=ft.Text("Restrito.", color=C_ERR), padding=24)
        if trs["sub"] == "combat":
            md, s1, s2 = trs["md"], ft.Text(str(trs["p1s"]), size=64, weight="bold", color=C_TXT), ft.Text(str(trs["p2s"]), size=64, weight="bold", color=C_TXT)
            def pw():
                if trs["ended"]: return 
                trs["ended"] = True
                def fm(e):
                    hdl(dlg)
                    def asc(): s_sync(); ath({"id": str(int(time.time()*1000)), "DATA": datetime.now().strftime('%d/%m/%Y %H:%M'), "NOME_TREINO": md["tn"], "COMBO_TESTADO": md["ct"], "COMBO_ADVERSARIO": md["ca"], "LADO_ARENA": md["la"], "MEU_XTREME": trs["p1f"]["xtreme"], "MEU_BURST": trs["p1f"]["burst"], "MEU_OVER": trs["p1f"]["over"], "MEU_SPIN": trs["p1f"]["spin"], "MEU_FLAG": trs["p1f"]["flag"], "ADV_XTREME": trs["p2f"]["xtreme"], "ADV_BURST": trs["p2f"]["burst"], "ADV_OVER": trs["p2f"]["over"], "ADV_SPIN": trs["p2f"]["spin"], "ADV_FLAG": trs["p2f"]["flag"], "PLACAR": f'{trs["p1s"]} x {trs["p2s"]}', "RESULTADO": "Vitória" if trs["p1s"] > trs["p2s"] else "Derrota"}, co()); trs["sub"] = "setup"; rct()
                    threading.Thread(target=asc, daemon=True).start()
                dlg = ft.AlertDialog(modal=True, bgcolor=C_SUR, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text(f"Treino Concluído!", color=C_SUC, weight="bold"), actions=[PB("Salvar e Voltar", fm, width=float("inf"))]); sdl(dlg)
            def ap(pl, p, t):
                if trs["ended"]: return 
                if pl == 1: trs["p1s"]+=p; trs["p1f"][t]+=1; s1.value = str(trs["p1s"])
                else: trs["p2s"]+=p; trs["p2f"][t]+=1; s2.value = str(trs["p2s"])
                pg.update(); pw() if trs["p1s"] >= PTS_WIN or trs["p2s"] >= PTS_WIN else None
            def ac(p): return ft.Column([PB(f"XTREME (+3)", lambda _: ap(p, 3, "xtreme"), width=145, height=44, c=C_PRI), SB(f"BURST (+2)", lambda _: ap(p, 2, "burst"), width=145, height=44), SB(f"OVER (+2)", lambda _: ap(p, 2, "over"), width=145, height=44), SB(f"SPIN (+1)", lambda _: ap(p, 1, "spin"), width=145, height=44), SB(f"FLAG (+1)", lambda _: ap(p, 1, "flag"), width=145, height=44)], spacing=12, alignment="start", horizontal_alignment="center")
            return ft.Container(padding=0, expand=True, content=ft.Column([ft.Container(content=ft.Row([IB(ft.Icons.ARROW_BACK, lambda _: [trs.update({"sub": "setup"}), rct()]), ft.Text(f"TREINO: {md['tn'].upper()}", color=C_TXT, weight="w600", size=13, expand=True, text_align="center"), ft.Container(width=42)]), bgcolor=C_SUC, padding=12), ft.Container(padding=24, expand=True, content=ft.Column([ft.Row([ft.Column([ft.Text(md["ct"], size=16, color=C_TXT, weight="w600", text_align="center", overflow="ellipsis"), s1, ac(1)], expand=True, horizontal_alignment="center"), ft.Container(width=1, bgcolor=C_BOR, height=300, margin=ft.margin.symmetric(horizontal=8)), ft.Column([ft.Text(md["ca"], size=16, color=C_TXT, weight="w600", text_align="center", overflow="ellipsis"), s2, ac(2)], expand=True, horizontal_alignment="center")], alignment="center", vertical_alignment="start"), ft.Container(height=24), SB("Resetar", lambda _: [trs.update({"p1s":0,"p2s":0,"p1f":{"spin":0,"over":0,"burst":0,"xtreme":0,"flag":0},"p2f":{"spin":0,"over":0,"burst":0,"xtreme":0,"flag":0},"ended":False}), setattr(s1,'value','0'), setattr(s2,'value','0'), pg.update()], width=float("inf"), ic=ft.Icons.REFRESH)], scroll="auto"))]))
        else:
            hs = gth(co() if not adm() or ast.get("avo")=="admin" else ast["avo"])
            def gr(k): r = []; [r.append(h.get(k)) for h in hs if h.get(k) and h.get(k) not in r]; return r[:6]
            ti, cti, cai, ldd = ft.TextField(label="Nome", bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, border_radius=12), ft.TextField(label="Seu Combo", bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, border_radius=12), ft.TextField(label="Adv", bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, border_radius=12), ft.Dropdown(label="Lado", options=[ft.dropdown.Option("B Side"), ft.dropdown.Option("X Side")], bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, border_radius=12)
            def ms(v, tgi): return ft.Row([ft.Container(content=ft.Text(x, size=11, color=C_PRI, weight="w600"), padding=ft.padding.symmetric(horizontal=10, vertical=4), bgcolor=f"{C_PRI}15", border_radius=12, border=ft.border.all(1, f"{C_PRI}40"), on_click=lambda e, val=x: [setattr(tgi, 'value', val), pg.update()]) for x in v], wrap=True, spacing=6, run_spacing=6) if v else ft.Container()
            def strt(e):
                if not all([ti.value, cti.value, cai.value, ldd.value]): return
                trs.update({"md": {"tn": ti.value.strip(), "ct": cti.value.strip(), "ca": cai.value.strip(), "la": ldd.value}, "p1s":0, "p2s":0, "p1f":{"spin":0,"over":0,"burst":0,"xtreme":0,"flag":0}, "p2f":{"spin":0,"over":0,"burst":0,"xtreme":0,"flag":0}, "ended":False, "sub":"combat"}); rct()
            def ep(e):
                if not hs: return
                p = f"treino_{int(time.time())}.csv"
                with open(p, 'w', newline='', encoding='utf-8') as f:
                    w = csv.writer(f); w.writerow(["DATA", "NOME", "CT", "CA", "LADO", "RES", "PLACAR", "XT", "BU", "OV", "SP", "FL", "AXT", "ABU", "AOV", "ASP", "AFL"])
                    for h in hs: w.writerow([h.get("DATA",""), h.get("NOME_TREINO",""), h.get("COMBO_TESTADO",""), h.get("COMBO_ADVERSARIO",""), h.get("LADO_ARENA",""), h.get("RESULTADO",""), h.get("PLACAR",""), h.get("MEU_XTREME",0), h.get("MEU_BURST",0), h.get("MEU_OVER",0), h.get("MEU_SPIN",0), h.get("MEU_FLAG",0), h.get("ADV_XTREME",0), h.get("ADV_BURST",0), h.get("ADV_OVER",0), h.get("ADV_SPIN",0), h.get("ADV_FLAG",0)])
                pg.snack_bar = ft.SnackBar(ft.Text(f"Salvo: {p}"), bgcolor=C_SUC); pg.snack_bar.open = True; pg.update()
            def cd(td):
                def dd(e):
                    with dblk: db["training_history"] = [h for h in db.get("training_history", []) if h.get("id") != td]; sv_db(db)
                    hdl(dlg); rct()
                dlg = ft.AlertDialog(bgcolor=C_SUR, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Excluir", color=C_TXT), actions=[SB("Cancelar", lambda _: hdl(dlg)), PB("Excluir", dd, c=C_ERR)]); sdl(dlg)
            hl = ft.ListView(expand=True, spacing=10)
            for h in hs: hl.controls.append(AC(ft.Column([ft.Row([ft.Row([ft.Text(h.get("DATA",""), color=C_TXTS, size=12), ft.Text(h.get("RESULTADO",""), color=C_SUC if h.get("RESULTADO")=="Vitória" else C_ERR, weight="bold")], spacing=8), IB(ft.Icons.DELETE_OUTLINE, lambda e, t=h.get("id"): cd(t), color=C_ERR)], alignment="spaceBetween"), ft.Text(f"Treino: {h.get('NOME_TREINO', '')}", color=C_PRI, weight="bold", size=14), ft.Text(f"Meu: {h.get('COMBO_TESTADO')}  VS  Adv: {h.get('COMBO_ADVERSARIO')}", color=C_TXT, weight="w500"), ft.Text(f"Placar: {h.get('PLACAR')} | Lado: {h.get('LADO_ARENA')}", color=C_TXTS, size=13)], spacing=4), p=12))
            return ft.Container(padding=24, content=ft.Column([ft.Text("Lab de Combos", size=24, weight="bold", color=C_PRI), ti, ms(gr("NOME_TREINO"), ti), cti, ms(gr("COMBO_TESTADO"), cti), cai, ms(gr("COMBO_ADVERSARIO"), cai), ldd, PB("Arena", strt, width=float("inf"), ic=ft.Icons.PLAY_ARROW), ft.Divider(color=C_BOR, height=20), ft.Row([ft.Text("Histórico", size=18, weight="bold", color=C_TXT, expand=True), SB("CSV", ep, ic=ft.Icons.DOWNLOAD, h=36)]), ft.Container(content=hl, expand=True)], scroll="auto"))

    def bhv():
        if not hto(): return ft.Container(content=ft.Text("Restrito.", color=C_ERR), padding=24)
        bds = gb(co())
        bi = ft.TextField(value=hos["tn"], hint_text="Nome...", expand=True, bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, text_size=14, border_radius=12); bi.on_change = lambda e: hos.update({"tn": e.control.value})
        def ab(e):
            if bi.value.strip(): bl = gb(co()); bl.append({"id": str(int(time.time()*1000)), "name": bi.value.strip()}); sb(bl, co()); hos["tn"] = ""; rct()
        def crb(bd):
            if bd in hos["ids"]: hos["ids"].remove(bd)
            sb([b for b in gb(co()) if b["id"] != bd], co()); rct()
        blu, slu = ft.ListView(expand=True, spacing=12), ft.ListView(expand=True, spacing=12)
        for b in bds: 
            blu.controls.append(AC(ft.Row([ft.Text(b["name"], weight="w500", color=C_TXT, size=15, expand=True), IB(ft.Icons.DELETE_OUTLINE, lambda e, bd=b["id"]: crb(bd), c=C_ERR)]), p=12))
            def ts(e, bd):
                if e.control.value: hos["ids"].append(bd) if bd not in hos["ids"] else None
                else: hos["ids"].remove(bd) if bd in hos["ids"] else None
                bcr.content.controls[1].value = f"Avançar ({len(hos['ids'])})"; pg.update()
            slu.controls.append(AC(ft.Checkbox(label=b["name"], value=(b["id"] in hos["ids"]), on_change=lambda e, bd=b["id"]: ts(e, bd), fill_color=C_PRI, check_color=C_BG, label_style=ft.TextStyle(color=C_TXT, size=15, weight="w500")), p=8))
        
        vcd = ft.Column([ft.Row([bi, PB("Add", ab, w=80, h=52)]), ft.Container(height=12), ft.Container(content=blu, expand=True)]); vcf = ft.Container(expand=True)
        
        def opc(e):
            s_bds = [b for b in gb(co()) if b["id"] in hos["ids"]]; tb = len(s_bds)
            if tb < 16:
                pg.snack_bar = ft.SnackBar(ft.Text("Requer no mínimo 16 Bladers para o formato Oficial!"), bgcolor=C_ERR); pg.snack_bar.open = True; pg.update(); return 
            ni = ft.TextField(label="Nome do Torneio", value=f"Torneio {datetime.now().strftime('%d/%m')}", bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, border_radius=12)
            def cc(e):
                sh = list(s_bds); random.shuffle(sh); b_ids = [b["id"] for b in sh]; n = len(b_ids); m = []
                if n % 2 != 0: b_ids.append("BYE"); n += 1
                jp = ["juiz_1", "juiz_2", "juiz_3", "juiz_4"]
                for rnd in range(4):
                    for i in range(n // 2):
                        p1, p2 = b_ids[i], b_ids[n - 1 - i]
                        cp = (p1 == "BYE" or p2 == "BYE"); wn = p2 if p1 == "BYE" else p1; rs = {"winner": wn} if cp else {}
                        m.append({"id": f"r{rnd}-{i}-{int(time.time()*1000)}", "name": f"Rodada {rnd+1}", "groupId": "fi", "blader1": p1, "blader2": p2, "completed": cp, "result": rs, "judge": jp[len(m) % 4]})
                    b_ids.insert(1, b_ids.pop())
                st({"id": str(int(time.time())), "name": ni.value.strip(), "date": datetime.now().strftime('%d/%m/%Y %H:%M'), "groups": [{"id": "fi", "name": "Fase Suíça (4 Partidas)", "bladerIds": [b["id"] for b in s_bds], "matches": m}], "status": "groups", "knockout": [], "participants": {b["id"]: b["name"] for b in s_bds}, "advancing_per_group": 16}, co())
                hos["ids"].clear(); sht("selecao"); tst["sub"] = "grupos"; ntt("Torneio") 
            
            vcf.content = ft.Column([ft.Text("Passo 2: Confirmar Oficial", size=14, color=C_TXTS), AC(ft.Column([ni, ft.Text("Oficial FBRJ: Fase Suíça (4 partidas) ➔ Corte Top 16 (Winner/Lower).", color=C_PRI, size=13)], spacing=16)), ft.Row([SB("Voltar", lambda _: sht("selecao"), exp=True), PB("Gerar 1ª Fase", cc, exp=True)], spacing=12)], scroll="auto"); sht("config")

        bcr = PB(f"Avançar ({len(hos['ids'])})", opc, w=float("inf"), ic=ft.Icons.ROCKET_LAUNCH)
        tnc, csw = ft.Container(), ft.Container(expand=True)
        def sht(tn):
            hos["sub"] = tn; is_c = tn == "cadastro"
            tb = [ft.Container(content=ft.Text("Banco Geral", size=13, weight="w600", color=C_TXT if is_c else C_TXTS), expand=True, bgcolor=C_SURS if is_c else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: sht("cadastro")), ft.Container(content=ft.Text("Criar Torneio", size=13, weight="w600", color=C_TXT if not is_c else C_TXTS), expand=True, bgcolor=C_SURS if not is_c else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: sht("selecao"))]
            tnc.content, csw.content = ft.Container(content=ft.Row(tb, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BOR), border_radius=10, padding=4, margin=ft.margin.only(bottom=16)), (vcd if is_c else (ft.Column([ft.Text("Passo 1: Marque os Bladers", size=14, color=C_TXTS), ft.Container(content=slu, expand=True), bcr]) if tn == "selecao" else vcf)); pg.update()
        sht(hos["sub"]); return ft.Container(padding=24, content=ft.Column([ft.Text("Gestão de Bladers", size=24, weight="bold", color=C_TXT), tnc, csw]))

    def bqmv():
        s = {"p1": 0, "p2": 0, "p1f": {"spin":0,"over":0,"burst":0,"xtreme":0,"flag":0}, "p2f": {"spin":0,"over":0,"burst":0,"xtreme":0,"flag":0}, "end": False}
        s1, s2 = ft.Text("0", size=64, weight="bold", color=C_TXT), ft.Text("0", size=64, weight="bold", color=C_TXT)
        i1, i2 = ft.TextField(value="Jogador 1", text_align="center", bgcolor="transparent", border_color="transparent", color=C_TXT, text_size=16, content_padding=0), ft.TextField(value="Jogador 2", text_align="center", bgcolor="transparent", border_color="transparent", color=C_TXT, text_size=16, content_padding=0)
        def pw():
            if s["end"]: return 
            s["end"] = True; w = i1.value.strip() if s["p1"] > s["p2"] else i2.value.strip()
            dlg = ft.AlertDialog(modal=True, bgcolor=C_SUR, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text(f"🏆 Vitória de {w}!", color=C_PRI, weight="bold"), actions=[PB("Limpar", lambda _: hdl(dlg) or res(), w=float("inf"))]); sdl(dlg)
        def ap(pl, pt, tf):
            if s["end"]: return 
            if pl == 1: s["p1"]+=pt; s["p1f"][tf]+=1; s1.value = str(s["p1"])
            else: s["p2"]+=pt; s["p2f"][tf]+=1; s2.value = str(s["p2"])
            pg.update(); pw() if s["p1"] >= PTS_WIN or s["p2"] >= PTS_WIN else None
        def res(e=None): s.update({"p1":0, "p2":0, "end":False}); s1.value, s2.value = "0", "0"; pg.update()
        def ac(p): return ft.Column([PB(f"XTREME (+3)", lambda _: ap(p, 3, "xtreme"), w=145, h=44, c=C_PRI), SB(f"BURST (+2)", lambda _: ap(p, 2, "burst"), w=145, h=44), SB(f"OVER (+2)", lambda _: ap(p, 2, "over"), w=145, h=44), SB(f"SPIN (+1)", lambda _: ap(p, 1, "spin"), w=145, h=44), SB(f"FLAG (+1)", lambda _: ap(p, 1, "flag"), w=145, h=44)], spacing=12, alignment="start", horizontal_alignment="center")
        return ft.Container(padding=0, expand=True, content=ft.Column([ft.Container(content=ft.Text("PARTIDA CASUAL", color=C_TXTS, weight="w600", size=13, text_align="center"), bgcolor=C_SURS, padding=12, width=float("inf")), ft.Container(padding=24, expand=True, content=ft.Column([ft.Row([ft.Column([i1, s1, ac(1)], expand=True, horizontal_alignment="center"), ft.Container(width=1, bgcolor=C_BOR, height=300, margin=ft.margin.symmetric(horizontal=8)), ft.Column([i2, s2, ac(2)], expand=True, horizontal_alignment="center")], alignment="center", vertical_alignment="start"), ft.Container(height=24), SB("Resetar Placar", res, w=float("inf"), ic=ft.Icons.REFRESH)], scroll="auto"))]))
    def btmv():
        if not hto(): return ft.Container(content=ft.Text("Acesso Restrito.", color=C_ERR), padding=24)
        if adm() and ast.get("avo") == "admin":
            s_sync(); tns = db.get("tournaments", {}); hui = ft.ListView(expand=True, spacing=12)
            for oi, td in tns.items(): hui.controls.append(AC(ft.Row([ft.Column([ft.Text(f"ORG: {oi.upper()}", color=C_PRI, weight="bold", size=12), ft.Text(td.get("name", "Torneio"), color=C_TXT, size=18, weight="w600")], expand=True), PB("Inspecionar", lambda e, o=oi: [ast.update({"avo": o}), uab(), rct()], ic=ft.Icons.VISIBILITY)])))
            return ft.Container(padding=24, content=ft.Column([ft.Text("Painel Global", size=24, weight="bold", color=C_TXT), ft.Container(content=hui, expand=True)]))

        t = gt(co())
        if not t: return ft.Container(content=ft.Column([ft.Icon(ft.Icons.EMOJI_EVENTS_OUTLINED, size=64, color=C_BOR), ft.Text("Nenhum torneio.", color=C_TXTS, size=16)], alignment="center", horizontal_alignment="center"), expand=True, alignment=ft.Alignment(0,0))
        bm = gsm(t)
        if tst["sub"] is None or (tst["sub"] == "matamata" and t.get("status") != "knockout"): tst["sub"] = "matamata" if t.get("status") == "knockout" else "grupos"
            
        if tst["sub"] == "combat":
            md, s = tst["m"], tst["ms"]; im3 = md.get("is_md3", False)
            sp1, sp2 = ft.Text(str(s["p1s"]), size=64, weight="bold", color=C_TXT), ft.Text(str(s["p2s"]), size=64, weight="bold", color=C_TXT)
            st1, st2 = (ft.Text(f"Sets: {s.get('p1t', 0)}", size=18, color=C_PRI, weight="bold") if im3 else ft.Container()), (ft.Text(f"Sets: {s.get('p2t', 0)}", size=18, color=C_PRI, weight="bold") if im3 else ft.Container())

            def pw():
                if s["ended"]: return 
                s["ended"] = True; wid = md["b1_id"] if (s.get("p1t", 0) > s.get("p2t", 0) if im3 else s["p1s"] > s["p2s"]) else md["b2_id"]
                def fm(e):
                    hdl(dlg)
                    def asv():
                        s_sync(); ft_t = gt(co()); lid = md["b2_id"] if wid == md["b1_id"] else md["b1_id"]
                        def tp(f): return f.get("xtreme",0)*3 + f.get("burst",0)*2 + f.get("over",0)*2 + f.get("spin",0)*1 + f.get("flag",0)*1
                        fr = {"blader1Result": {"bladerId": md["b1_id"], "totalPoints": tp(s["p1f"]), "finishes": s["p1f"]}, "blader2Result": {"bladerId": md["b2_id"], "totalPoints": tp(s["p2f"]), "finishes": s["p2f"]}, "winner": wid}

                        if md["is_knockout"]:
                            tw, tl = None, None
                            for r in ft_t.get("knockout", []):
                                for m in r.get("matches", []):
                                    if m.get("id") == md["match_id"]:
                                        m["completed"], m["result"], tw, tl = True, fr, m.get("target_w"), m.get("target_l")
                                        break
                            for rr in ft_t.get("knockout", []):
                                for mm in rr.get("matches", []):
                                    if tw and mm.get("id") == tw:
                                        if mm.get("blader1") is None: mm["blader1"] = wid
                                        elif mm.get("blader2") is None: mm["blader2"] = wid
                                    if tl and mm.get("id") == tl:
                                        if mm.get("blader1") is None: mm["blader1"] = lid
                                        elif mm.get("blader2") is None: mm["blader2"] = lid
                            cng = True
                            while cng:
                                cng = False
                                for r in ft_t.get("knockout", []):
                                    for m in r.get("matches", []):
                                        if not m.get("completed") and (m.get("blader1") == "BYE" or m.get("blader2") == "BYE"):
                                            if m.get("blader1") and m.get("blader2"):
                                                rw = m.get("blader1") if m.get("blader2") == "BYE" else m.get("blader2")
                                                m["completed"], m["result"] = True, {"winner": rw}
                                                twx, tlx = m.get("target_w"), m.get("target_l")
                                                for rx in ft_t.get("knockout", []):
                                                    for mx in rx.get("matches", []):
                                                        if twx and mx.get("id") == twx:
                                                            if mx.get("blader1") is None: mx["blader1"] = rw
                                                            elif mx.get("blader2") is None: mx["blader2"] = rw
                                                        if tlx and mx.get("id") == tlx:
                                                            if mx.get("blader1") is None: mx["blader1"] = "BYE"
                                                            elif mx.get("blader2") is None: mx["blader2"] = "BYE"
                                                cng = True
                        else:
                            for g in ft_t.get("groups", []):
                                if g.get("id") == md["group_id"]:
                                    for m in g.get("matches", []):
                                        if m.get("id") == md["match_id"]: m["completed"], m["result"] = True, fr
                        st(ft_t, co()); tst["sub"], tst["m"] = "partidas", None; rct() 
                    threading.Thread(target=asv, daemon=True).start()
                dlg = ft.AlertDialog(modal=True, bgcolor=C_SUR, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text(f"Vitória!", color=C_SUC), actions=[PB("Confirmar", fm)]); sdl(dlg)

            def ap(pl, pt, tf):
                if s["ended"]: return 
                if pl == 1: s["p1s"] += pt; s["p1f"][tf] += 1; sp1.value = str(s["p1s"])
                else: s["p2s"] += pt; s["p2f"][tf] += 1; sp2.value = str(s["p2s"])
                pg.update(); 
                if s["p1s"] >= PTS_WIN or s["p2s"] >= PTS_WIN:
                    if im3:
                        if s["p1s"] >= PTS_WIN: s["p1t"] = s.get("p1t", 0) + 1
                        else: s["p2t"] = s.get("p2t", 0) + 1
                        if s.get("p1t", 0) >= 2 or s.get("p2t", 0) >= 2: pw()
                        else:
                            s["p1s"], s["p2s"] = 0, 0; sp1.value, sp2.value = "0", "0"
                            st1.value, st2.value = f"Sets: {s['p1t']}", f"Sets: {s['p2t']}"
                            pg.snack_bar = ft.SnackBar(ft.Text("Fim do Set!"), bgcolor=C_SUC); pg.snack_bar.open = True; pg.update()
                    else: pw()

            def ac(p): return ft.Column([PB(f"XTREME (+3)", lambda _: ap(p, 3, "xtreme"), w=145, h=44, c=C_PRI), SB(f"BURST (+2)", lambda _: ap(p, 2, "burst"), w=145, h=44), SB(f"OVER (+2)", lambda _: ap(p, 2, "over"), w=145, h=44), SB(f"SPIN (+1)", lambda _: ap(p, 1, "spin"), w=145, h=44), SB(f"FLAG (+1)", lambda _: ap(p, 1, "flag"), w=145, h=44)], spacing=12, horizontal_alignment="center")
            return ft.Container(padding=0, expand=True, content=ft.Column([ft.Container(content=ft.Row([IB(ft.Icons.ARROW_BACK, lambda _: [tst.update({"sub": "partidas", "m": None}), rct()]), ft.Text(f"PARTIDA OFICIAL {'(MD3)' if im3 else ''}", color=C_TXT, weight="w600", size=13, expand=True, text_align="center"), ft.Container(width=42)]), bgcolor=C_ERR if md["is_knockout"] else C_PRI, padding=12), ft.Container(padding=24, expand=True, content=ft.Column([ft.Row([ft.Column([ft.Text(md["b1_name"]), st1, sp1, ac(1)], expand=True, horizontal_alignment="center"), ft.Container(width=1, bgcolor=C_BOR, height=300), ft.Column([ft.Text(md["b2_name"]), st2, sp2, ac(2)], expand=True, horizontal_alignment="center")], alignment="center", vertical_alignment="start"), ft.Container(height=24)], scroll="auto"))]))
            
        else:
            def pak(e):
                s_sync(); ft_t = gt(co())
                if not all(m.get("completed") for g in ft_t.get("groups", []) for m in g.get("matches", [])): pg.snack_bar = ft.SnackBar(ft.Text("Finalize a Fase Suíça!"), bgcolor=C_ERR); pg.snack_bar.open = True; pg.update(); return
                
                def da(e):
                    hdl(dlg); sdd = gsg(ft_t.get("groups", [])[0], bm) if ft_t.get("groups") else []
                    sds = [sx["id"] for sx in sdd if sx["id"] != "BYE"]
                    if len(sds) < 16: sds += ["BYE"] * (16 - len(sds))
                    fl = {}
                    def nd(nid, n, p1, p2, tw, tl, m3=False):
                        # FASE FINAL: Apenas Juízes 1 e 2 são escalados para o Mata-Mata
                        nx = {"id": nid, "name": n, "blader1": p1, "blader2": p2, "completed": False, "judge": random.choice(["juiz_1", "juiz_2"]), "is_md3": m3, "target_w": tw, "target_l": tl}
                        fl[nid] = nx; return nx

                    w1, w2, w3, w4 = nd("w1", "WB QF 1", sds[0], sds[7], "w5", "l5"), nd("w2", "WB QF 2", sds[3], sds[4], "w5", "l6"), nd("w3", "WB QF 3", sds[1], sds[6], "w6", "l7"), nd("w4", "WB QF 4", sds[2], sds[5], "w6", "l8")
                    l1, l2, l3, l4 = nd("l1", "LB R1", sds[8], sds[15], "l5", None), nd("l2", "LB R1", sds[11], sds[12], "l6", None), nd("l3", "LB R1", sds[9], sds[14], "l7", None), nd("l4", "LB R1", sds[10], sds[13], "l8", None)
                    l5, l6, l7, l8 = nd("l5", "LB R2", None, None, "l9", None), nd("l6", "LB R2", None, None, "l9", None), nd("l7", "LB R2", None, None, "l10", None), nd("l8", "LB R2", None, None, "l10", None)
                    w5, w6 = nd("w5", "WB Semi 1", None, None, "w7", "l11"), nd("w6", "WB Semi 2", None, None, "w7", "l12")
                    l9, l10 = nd("l9", "LB R3", None, None, "l11", None), nd("l10", "LB R3", None, None, "l12", None)
                    l11, l12 = nd("l11", "LB QF", None, None, "l13", None), nd("l12", "LB QF", None, None, "l13", None)
                    l13 = nd("l13", "LB Semi", None, None, "l14", None)
                    w7 = nd("w7", "Winner Final", None, None, "gf", "l14")
                    l14 = nd("l14", "Lower Final", None, None, "gf", None)
                    gf = nd("gf", "Grande Final", None, None, None, None, True)

                    ko = [{"name": "WB QF & LB R1", "matches": [w1, w2, w3, w4, l1, l2, l3, l4]}, {"name": "WB SF & LB R2", "matches": [w5, w6, l5, l6, l7, l8]}, {"name": "LB R3", "matches": [l9, l10]}, {"name": "WB Final & LB QF", "matches": [w7, l11, l12]}, {"name": "LB Semi", "matches": [l13]}, {"name": "Lower Final", "matches": [l14]}, {"name": "Grande Final", "matches": [gf]}]

                    def ptg(tid, pid):
                        if tid and tid in fl:
                            if fl[tid]["blader1"] is None: fl[tid]["blader1"] = pid
                            elif fl[tid]["blader2"] is None: fl[tid]["blader2"] = pid

                    cng = True
                    while cng:
                        cng = False
                        for r in ko:
                            for m in r["matches"]:
                                if not m["completed"] and (m["blader1"] == "BYE" or m["blader2"] == "BYE"):
                                    if m["blader1"] and m["blader2"]:
                                        win = m["blader1"] if m["blader2"] == "BYE" else m["blader2"]
                                        m["completed"], m["result"] = True, {"winner": win}
                                        ptg(m["target_w"], win); ptg(m["target_l"], "BYE"); cng = True
                                        
                    ft_t["knockout"], ft_t["status"] = ko, "knockout"
                    st(ft_t, co()); tst["sub"] = "matamata"; rct()

                dlg = ft.AlertDialog(bgcolor=C_SUR, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Mata-Mata Top 16", color=C_TXT), content=ft.Text("Gerar Chave Oficial FBRJ?", color=C_TXTS), actions=[SB("Cancelar", lambda _: hdl(dlg)), PB("Gerar", da)]); sdl(dlg)

            vg, vp, vm = ft.ListView(expand=True, spacing=16, padding=ft.padding.only(top=16)), ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16)), ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))

            def gma(md, b1n, b2n, ik=False, ri=0):
                if md.get("completed"):
                    rs = md.get("result", {})
                    if rs.get("winner") == "BYE" or md.get("blader1") == "BYE" or md.get("blader2") == "BYE": return ft.Text("Avançou (BYE)", color=C_TXTS, size=12, weight="bold")
                    pt1, pt2 = rs.get("blader1Result", {}).get("totalPoints", 0), rs.get("blader2Result", {}).get("totalPoints", 0)
                    return ft.Row([ft.Text(f"{pt1} - {pt2}", color=C_PRI, weight="bold", size=16), IB(ft.Icons.INFO_OUTLINE, lambda e, mdt=md: omd(mdt, t))])
                else:
                    if ik and (md.get("blader1") is None or md.get("blader2") is None): return ft.Text("Aguardando...", color=C_TXTS, size=12)
                    j = md.get("judge")
                    if hto() or j == cu()["username"]:
                        act = {"is_knockout": ik, "round_idx": ri, "match_id": md.get("id"), "group_id": md.get("groupId"), "b1_id": md.get("blader1"), "b1_name": b1n, "b2_id": md.get("blader2"), "b2_name": b2n, "judge": j, "is_md3": md.get("is_md3", False)}
                        return PB("Jogar", lambda e: [tst.update({"m": e.control.data, "ms": {"p1s": 0, "p2s": 0, "p1t": 0, "p2t": 0, "p1f": {"spin":0,"over":0,"burst":0,"xtreme":0,"flag":0}, "p2f": {"spin":0,"over":0,"burst":0,"xtreme":0,"flag":0}, "ended": False}, "sub": "combat"}), rct()], h=36, w=80, dt=act)
                    return ft.Row([ft.Icon(ft.Icons.LOCK, size=14, color=C_TXTS), ft.Text(f"Apito: {j or 'Admin'}", color=C_TXTS, size=11)])

            for g in t.get("groups", []):
                sst = gsg(g, bm)
                gc = ft.Column([ft.Text(g.get("name", ""), size=16, weight="w600", color=C_TXT), ft.Container(content=ft.Row([ft.Text("#", width=20, size=12, color=C_TXTS), ft.Text("Blader", expand=True, size=12, color=C_TXTS), ft.Text("J", width=25, size=12, color=C_TXTS), ft.Text("V", width=25, size=12, color=C_TXTS), ft.Text("PF", width=25, size=12, color=C_TXTS), ft.Text("PS", width=25, size=12, color=C_TXTS), ft.Text("Sld", width=30, size=12, color=C_TXTS)]), padding=8, border=ft.border.only(bottom=ft.BorderSide(1, C_BOR)))])
                for idx, std in enumerate(sst): 
                    c = C_PRI if idx < 8 else (C_SUC if idx < 16 else C_TXTS)
                    bg = f"{C_PRI}15" if idx < 8 else (f"{C_SUC}15" if idx < 16 else "transparent")
                    gc.controls.append(ft.Container(content=ft.Row([ft.Text(str(idx+1), width=20, size=14, color=c, weight="bold"), ft.Text(std["name"], expand=True, size=14, color=C_TXT), ft.Text(str(std["j"]), width=25, size=14, color=C_TXTS), ft.Text(str(std["v"]), width=25, size=14, color=C_TXTS), ft.Text(str(std["pf"]), width=25, size=14, color=C_TXTS), ft.Text(str(std["ps"]), width=25, size=14, color=C_TXTS), ft.Text(str(std["saldo"]), width=30, size=14, color=C_SUC if std["saldo"] > 0 else C_ERR)]), padding=8, bgcolor=bg, border_radius=8))
                vg.controls.append(AC(gc))

                rnd_dict = {}
                for m in g.get("matches", []): rnd_dict.setdefault(m.get("name", "Rodada"), []).append(m)
                for r_name in sorted(rnd_dict.keys()):
                    vp.controls.append(ft.Text(r_name, size=18, weight="bold", color=C_PRI, margin=ft.margin.only(top=16)))
                    j_dict = {}
                    for m in rnd_dict[r_name]: j_dict.setdefault(m.get("judge", "Admin"), []).append(m)
                    for j in sorted(j_dict.keys()):
                        vp.controls.append(ft.Text(f"ARENA: {j.replace('_', ' ').upper()}", size=12, weight="bold", color=C_TXTS, margin=ft.margin.only(top=8)))
                        for m in j_dict[j]:
                            b1n, b2n = bm.get(m.get("blader1"), "BYE"), bm.get(m.get("blader2"), "BYE")
                            vp.controls.append(AC(ft.Row([ft.Column([ft.Text(b1n, size=14, weight="w500", color=C_TXT), ft.Text("vs", size=10, color=C_TXTS), ft.Text(b2n, size=14, weight="w500", color=C_TXT)]), gma(m, b1n, b2n)], alignment="spaceBetween"), p=12))

            if t.get("status") == "groups" and hto(): vg.controls.append(PB("Avançar para Mata-Mata Top 16", pak, w=float("inf")))
            
            if t.get("knockout"):
                for ri, r in enumerate(t.get("knockout", [])):
                    vm.controls.append(ft.Text(r.get("name", ""), size=16, weight="bold", color=C_PRI, margin=ft.margin.only(top=12)))
                    j_dict = {}
                    for m in r.get("matches", []): j_dict.setdefault(m.get("judge", "Admin"), []).append(m)
                    for j in sorted(j_dict.keys()):
                        vm.controls.append(ft.Text(f"ARENA: {j.replace('_', ' ').upper()}", size=12, weight="bold", color=C_TXTS, margin=ft.margin.only(top=4)))
                        for m in j_dict[j]:
                            b1id, b2id = m.get("blader1"), m.get("blader2")
                            b1n = bm.get(b1id, "A def") if b1id and b1id != "BYE" else "BYE" if b1id == "BYE" else "A def"
                            b2n = bm.get(b2id, "A def") if b2id and b2id != "BYE" else "BYE" if b2id == "BYE" else "A def"
                            if m.get("name"): vm.controls.append(ft.Text(m.get("name"), size=12, color=C_TXTS, text_align="center"))
                            vm.controls.append(AC(ft.Row([ft.Column([ft.Text(b1n, size=14, weight="w500", color=C_TXT), ft.Text("vs", size=10, color=C_TXTS), ft.Text(b2n, size=14, weight="w500", color=C_TXT)]), gma(m, b1n, b2n, True, ri)], alignment="spaceBetween"), p=12))

            tnc, csw = ft.Container(padding=ft.padding.symmetric(horizontal=24)), ft.Container(expand=True)
            def sut(tn):
                tst["sub"] = tn; ig, ip, im = tn == "grupos", tn == "partidas", tn == "matamata"
                tb = [ft.Container(content=ft.Text("Fase Suíça", size=13, weight="w600", color=C_TXT if ig else C_TXTS), expand=True, bgcolor=C_SURS if ig else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: sut("grupos")), ft.Container(content=ft.Text("Partidas", size=13, weight="w600", color=C_TXT if ip else C_TXTS), expand=True, bgcolor=C_SURS if ip else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: sut("partidas"))]
                if t.get("status") == "knockout": tb.append(ft.Container(content=ft.Text("Mata-Mata", size=13, weight="w600", color=C_PRI if im else C_TXTS), expand=True, bgcolor=f"{C_PRI}15" if im else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: sut("matamata")))
                tnc.content, csw.content = ft.Container(content=ft.Row(tb, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BOR), border_radius=10, padding=4), (vg if ig else (vp if ip else vm)); pg.update()
            sut(tst["sub"])

            ar = [IB(ft.Icons.REFRESH, lambda _: [s_sync(), rct()], c=C_PRI)]
            if hto():
                def oed(e):
                    dlg = ft.AlertDialog(bgcolor=C_SUR, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Encerrar", color=C_TXT), actions=[SB("Excluir", lambda _: [st(None, co()), hdl(dlg), rct()]), PB("Salvar Histórico", lambda _: [ah(t, co()), st(None, co()), hdl(dlg), rct()])]); sdl(dlg)
                ar.append(IB(ft.Icons.POWER_SETTINGS_NEW, oed, c=C_ERR))

            return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Row([ft.Column([ft.Text(t.get("name",""), size=20, weight="bold", color=C_TXT), ft.Text(f"Ambiente: {co().upper()}", size=12, color=C_PRI)], spacing=0), ft.Row(ar)], alignment="spaceBetween"), padding=24), tnc, ft.Container(content=csw, padding=ft.padding.symmetric(horizontal=24), expand=True)]))

    def build_viewer_view():
        t = gt(co())
        if not t: return ft.Container(content=ft.Column([ft.Icon(ft.Icons.CAST_CONNECTED, size=64, color=C_BOR), ft.Text("Nenhum torneio ao vivo.", color=C_TXTS, size=16)], alignment="center", horizontal_alignment="center"), expand=True, alignment=ft.Alignment(0,0))
        bm = gsm(t); vst["sub"] = "matamata" if t.get("status") == "knockout" else "grupos"
        vg = ft.ListView(expand=True, spacing=16, padding=ft.padding.only(top=16))
        for g in t.get("groups", []):
            sst = gsg(g, bm); gc = ft.Column([ft.Text(g.get("name", "Classificação Suíça"), size=18, weight="bold", color=C_PRI), ft.Container(content=ft.Row([ft.Text("#", width=30, size=14, color=C_TXTS), ft.Text("Blader", expand=True, size=14, color=C_TXTS), ft.Text("J", width=30, size=14, color=C_TXTS), ft.Text("V", width=30, size=14, color=C_TXTS), ft.Text("PF", width=30, size=14, color=C_TXTS), ft.Text("PS", width=30, size=14, color=C_TXTS), ft.Text("Sld", width=40, size=14, color=C_TXTS)]), padding=12, border=ft.border.only(bottom=ft.BorderSide(1, C_BOR)))])
            for i, sd in enumerate(sst): 
                c = C_PRI if i < 8 else (C_SUC if i < 16 else C_TXTS)
                bg = f"{C_PRI}15" if i < 8 else (f"{C_SUC}15" if i < 16 else "transparent")
                gc.controls.append(ft.Container(content=ft.Row([ft.Text(str(i+1), width=30, size=16, color=c, weight="bold"), ft.Text(sd["name"], expand=True, size=16, color=C_TXT, weight="bold"), ft.Text(str(sd["j"]), width=30, size=16, color=C_TXTS), ft.Text(str(sd["v"]), width=30, size=16, color=C_TXT), ft.Text(str(sd["pf"]), width=30, size=16, color=C_TXTS), ft.Text(str(sd["ps"]), width=30, size=16, color=C_TXTS), ft.Text(str(sd["saldo"]), width=40, size=16, color=C_SUC if sd["saldo"] > 0 else C_ERR, weight="bold")]), padding=12, bgcolor=bg, border_radius=8))
            vg.controls.append(AC(gc))

        def mrc(m):
            id1, id2 = m.get("blader1"), m.get("blader2")
            n1 = bm.get(id1, "A def") if id1 and id1 != "BYE" else "BYE" if id1 == "BYE" else "A def"
            n2 = bm.get(id2, "A def") if id2 and id2 != "BYE" else "BYE" if id2 == "BYE" else "A def"
            p1, p2, w = "-", "-", None
            if m.get("completed"):
                r = m.get("result", {}); w = r.get("winner")
                if w == "BYE" or id1 == "BYE" or id2 == "BYE": p1, p2 = "BYE", "BYE"
                else: p1, p2 = str(r.get("blader1Result", {}).get("totalPoints", 0)), str(r.get("blader2Result", {}).get("totalPoints", 0))
            c1, c2 = C_PRI if w == id1 else C_TXT, C_PRI if w == id2 else C_TXT
            return ft.Container(content=ft.Column([ft.Text(m.get("name", ""), size=11, color=C_TXTS, weight="bold"), ft.Row([ft.Text(n1, size=16, color=c1, weight="bold" if w==id1 else "w400", expand=True), ft.Text(p1, size=18, color=c1, weight="bold")]), ft.Container(height=1, bgcolor=C_BOR), ft.Row([ft.Text(n2, size=16, color=c2, weight="bold" if w==id2 else "w400", expand=True), ft.Text(p2, size=18, color=c2, weight="bold")])], spacing=6), width=240, padding=16, bgcolor=C_SUR, border_radius=12, border=ft.border.all(2, C_PRI if m.get("completed") else C_BOR))

        vm = ft.Row(expand=True, scroll="auto", spacing=40, vertical_alignment="start")
        for r in t.get("knockout", []):
            c = ft.Column(spacing=20); c.controls.append(ft.Text(r.get("name", ""), size=18, weight="bold", color=C_PRI))
            for m in r.get("matches", []): c.controls.append(mrc(m))
            vm.controls.append(c)

        tnc, csw = ft.Container(padding=ft.padding.symmetric(horizontal=24)), ft.Container(expand=True)
        def sst(tn):
            vst["sub"] = tn; ig = tn == "grupos"
            tb = [ft.Container(content=ft.Text("Fase Suíça", size=14, weight="w600", color=C_TXT if ig else C_TXTS), expand=True, bgcolor=C_SURS if ig else "transparent", padding=12, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: sst("grupos"))]
            if t.get("status") == "knockout": tb.append(ft.Container(content=ft.Text("Chaveamento (Top 16)", size=14, weight="w600", color=C_PRI if not ig else C_TXTS), expand=True, bgcolor=f"{C_PRI}15" if not ig else "transparent", padding=12, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: sst("matamata")))
            tnc.content, csw.content = ft.Container(content=ft.Row(tb, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BOR), border_radius=10, padding=4), (vg if ig else vm); pg.update()
        sst(vst["sub"]); return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Row([ft.Column([ft.Text("TRANSMISSÃO AO VIVO", size=12, color=C_ERR, weight="bold"), ft.Text(t.get("name",""), size=24, weight="bold", color=C_TXT)], spacing=0), ft.Icon(ft.Icons.TV, color=C_TXTS, size=32)], alignment="spaceBetween"), padding=24), tnc, ft.Container(content=csw, padding=ft.padding.symmetric(horizontal=24), expand=True)]))

    def build_history_view():
        if not hto(): return ft.Container(content=ft.Text("Acesso Restrito.", color=C_ERR), padding=24)
        if hst["t"]:
            t = hst["t"]; bm = gsm(t); st = {}
            for p in [t.get("groups", []), t.get("knockout", [])]:
                for px in p:
                    for m in px.get("matches", []):
                        if m.get("completed") and m.get("result", {}).get("winner") != "BYE":
                            r = m.get("result", {})
                            for k in ["blader1Result", "blader2Result"]:
                                bid = r.get(k, {}).get("bladerId")
                                if not bid or bid == "BYE": continue
                                if bid not in st: st[bid] = {"name": bm.get(bid, "Removido"), "j":0, "v":0, "pts":0, "spin":0, "over":0, "burst":0, "xtreme":0, "flag":0}
                                s = st[bid]; s["j"]+=1; s["pts"]+=r.get(k,{}).get("totalPoints",0)
                                f = r.get(k,{}).get("finishes", {}); s["spin"]+=f.get("spin",0); s["over"]+=f.get("over",0); s["burst"]+=f.get("burst",0); s["xtreme"]+=f.get("xtreme",0); s["flag"]+=f.get("flag",0)
                                if r.get("winner") == bid: s["v"]+=1
            ss = sorted(st.values(), key=lambda x: (x["v"], x["pts"], x["xtreme"]), reverse=True)
            vt, vs = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16)), ft.ListView(expand=True, spacing=12, padding=ft.padding.only(top=16))
            for g in t.get("groups", []):
                vt.controls.append(ft.Text(g.get('name', ''), size=14, weight="w600", color=C_TXTS))
                for m in g.get("matches", []):
                    if m.get("completed"):
                        r = m.get("result", {}); b1n, b2n = bm.get(m.get("blader1"), ""), bm.get(m.get("blader2"), "")
                        sui = ft.Row([ft.Text(f"{r.get('blader1Result',{}).get('totalPoints',0)} - {r.get('blader2Result',{}).get('totalPoints',0)}", color=C_PRI, weight="bold", size=16), IB(ft.Icons.INFO_OUTLINE, lambda e, md=m: omd(md, t))])
                        vt.controls.append(AC(ft.Row([ft.Text(b1n, size=14, color=C_TXT), sui, ft.Text(b2n, size=14, color=C_TXT)], alignment="spaceBetween"), p=12))
            for r in t.get("knockout", []):
                vt.controls.append(ft.Text(r.get("name", ""), size=14, weight="w600", color=C_TXTS, margin=ft.margin.only(top=8)))
                for m in r.get("matches", []):
                    if m.get("name"): vt.controls.append(ft.Text(m.get("name"), size=12, color=C_PRI, text_align="center"))
                    id1, id2 = m.get("blader1"), m.get("blader2"); b1n = bm.get(id1, "A def") if id1 and id1 != "BYE" else "W.O." if id1 == "BYE" else "A def"; b2n = bm.get(id2, "A def") if id2 and id2 != "BYE" else "W.O." if id2 == "BYE" else "A def"
                    if m.get("completed"):
                        rs = m.get("result", {})
                        if rs.get("winner") == "BYE" or id1 == "BYE" or id2 == "BYE": sui = ft.Text("Avançou (W.O.)", color=C_TXTS, size=12, weight="bold")
                        else: sui = ft.Row([ft.Text(f"{rs.get('blader1Result',{}).get('totalPoints',0)} - {rs.get('blader2Result',{}).get('totalPoints',0)}", color=C_PRI, weight="bold", size=16), IB(ft.Icons.INFO_OUTLINE, lambda e, md=m: omd(md, t))])
                        vt.controls.append(AC(ft.Row([ft.Text(b1n, size=14, color=C_TXT), sui, ft.Text(b2n, size=14, color=C_TXT)], alignment="spaceBetween"), p=12))
            for s in ss: vs.controls.append(AC(ft.Column([ft.Row([ft.Text(s["name"], weight="bold", size=16, color=C_TXT, expand=True), ft.Text(f"{s['pts']} Pts", weight="bold", size=16, color=C_PRI)]), ft.Text(f"{s['v']} Vitórias em {s['j']} Jogos", size=12, color=C_TXTS), ft.Container(height=4), ft.Row([BDG(f"XT: {s['xtreme']}", C_XT), BDG(f"BU: {s['burst']}", C_BU), BDG(f"OV: {s['over']}", C_OV), BDG(f"SP: {s['spin']}", C_SP), BDG(f"FL: {s['flag']}", C_FL)], spacing=6, wrap=True)], spacing=4), p=16))
            tnc, csw = ft.Container(padding=ft.padding.symmetric(horizontal=24)), ft.Container(expand=True)
            def sdt(tn): 
                hst["sub"] = tn; ist = tn == "tabelas"
                tb = [ft.Container(content=ft.Text("Chaves", size=13, weight="w600", color=C_TXT if ist else C_TXTS), expand=True, bgcolor=C_SURS if ist else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: sdt("tabelas")), ft.Container(content=ft.Text("Estatísticas", size=13, weight="w600", color=C_TXT if not ist else C_TXTS), expand=True, bgcolor=C_SURS if not ist else "transparent", padding=8, alignment=ft.Alignment(0,0), border_radius=8, on_click=lambda _: sdt("estatisticas"))]
                tnc.content, csw.content = ft.Container(content=ft.Row(tb, spacing=4), bgcolor=C_BG, border=ft.border.all(1, C_BOR), border_radius=10, padding=4), (vt if ist else vs); pg.update()
            sdt(hst["sub"])
            return ft.Container(padding=0, content=ft.Column([ft.Container(content=ft.Row([IB(ft.Icons.ARROW_BACK, lambda _: [hst.update({"t": None}), rct()]), ft.Text(f"[{t.get('org', 'admin').upper()}] " if adm() and ast.get("avo") == "admin" else "" + t.get('name', ''), size=18, weight="bold", color=C_TXT, expand=True, text_align="right")]), padding=24), tnc, ft.Container(content=csw, padding=ft.padding.symmetric(horizontal=24), expand=True)]))

        h = gh(co())
        if not h: return ft.Container(content=ft.Column([ft.Icon(ft.Icons.HISTORY, size=64, color=C_BOR), ft.Text("Vazio.", color=C_TXTS, size=16)], alignment="center", horizontal_alignment="center"), expand=True, alignment=ft.Alignment(0,0))
        lu = ft.ListView(expand=True, spacing=12, padding=24); lu.controls.append(ft.Text("Anteriores", size=24, weight="bold", color=C_TXT, margin=ft.margin.only(bottom=8)))
        def cdh(tid, org):
            def dd(e):
                s_sync(); 
                with dblk: db["history"] = [hx for hx in db.get("history", []) if not(hx.get("id") == tid and hx.get("org", "admin") == org)]
                sv_db(db); hdl(dlg); rct(); pg.snack_bar = ft.SnackBar(ft.Text("Apagado!"), bgcolor=C_SUC); pg.snack_bar.open = True; pg.update()
            dlg = ft.AlertDialog(bgcolor=C_SUR, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Excluir", color=C_TXT), actions=[SB("Cancelar", lambda _: hdl(dlg)), PB("Excluir", dd, c=C_ERR)]); sdl(dlg)
        for t in h: lu.controls.append(AC(ft.Row([ft.Column([ft.Text(f"[{t.get('org', 'admin').upper()}] " if adm() and ast.get("avo") == "admin" else "" + t.get('name', ''), weight="w600", size=16, color=C_TXT), ft.Text(f"{t.get('date', '')}", size=12, color=C_TXTS)], spacing=2, expand=True), IB(ft.Icons.VISIBILITY, lambda e, dt=t: [hst.update({"t": dt, "sub": "tabelas"}), rct()], c=C_PRI), IB(ft.Icons.DELETE_OUTLINE, lambda e, tid=t.get("id"), o=t.get("org", "admin"): cdh(tid, o), c=C_ERR)], spacing=12), p=16))
        return ft.Container(content=lu, expand=True)

    def build_admin_view():
        if not adm(): return ft.Container()
        ads = {"sq": ""}; si = ft.TextField(hint_text="Buscar...", prefix_icon=ft.Icons.SEARCH, bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, border_radius=12, content_padding=10)
        ulu = ft.ListView(expand=True, spacing=12)
        def ru():
            ulu.controls.clear(); q = ads["sq"].lower(); au = {k: v.copy() for k, v in HC_U.items()}; au.update(gu())
            for un, ud in au.items():
                if q and q not in un.lower(): continue 
                rd = ft.Dropdown(value=ud.get('role', 'basic'), options=[ft.dropdown.Option(k, text=t) for k,t in [("basic","Básico"),("treinador","Treinador"),("organizador","Org"),("pro","Pro"),("admin_max","Admin")]], width=110, height=40, bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, text_size=12)
                oi = ft.TextField(value=ud.get('org', un), hint_text="org1", label="ORG", width=80, height=40, bgcolor=C_SURS, border_color=C_BOR, color=C_TXT, text_size=12, content_padding=10)
                def sur(e, u=un, d=rd, o=oi, dt=ud):
                    s_sync(); du = gu(); pw = dt.get("password") or (HC_U[u]["password"] if u in HC_U else "123")
                    du[u] = {"password": pw, "role": d.value, "org": o.value.strip()}; su(du); pg.snack_bar = ft.SnackBar(ft.Text(f"Salvo!"), bgcolor=C_SUC); pg.snack_bar.open = True; pg.update()
                def cdu(u):
                    def dd(e):
                        s_sync(); du = gu()
                        if u in du: del du[u]; su(du); pg.snack_bar = ft.SnackBar(ft.Text(f"Excluído!"), bgcolor=C_SUC)
                        else: pg.snack_bar = ft.SnackBar(ft.Text("Não excluir admins."), bgcolor=C_ERR)
                        pg.snack_bar.open = True; hdl(dlg); ru()
                    dlg = ft.AlertDialog(bgcolor=C_SUR, shape=ft.RoundedRectangleBorder(radius=16), title=ft.Text("Excluir", color=C_TXT), actions=[SB("Cancelar", lambda _: hdl(dlg)), PB("Excluir", dd, c=C_ERR)]); sdl(dlg)
                ulu.controls.append(AC(ft.Row([ft.Text(un, weight="w600", size=14, color=C_TXT, expand=True), oi, rd, IB(ft.Icons.SAVE, sur, c=C_SUC), IB(ft.Icons.DELETE_OUTLINE, lambda e, x=un: cdu(x), c=C_ERR)], spacing=8), p=12))
            pg.update()
        si.on_change = lambda e: [ads.update({"sq": e.control.value}), ru()]; ru() 
        return ft.Container(padding=24, content=ft.Column([ft.Text("Painel", size=24, weight="bold", color=C_TXT), si, ft.Container(height=8), ft.Container(content=ulu, expand=True)]))

    ca = ft.Container(expand=True)
    TM = {"Bladers": bhv, "Treino": btrv, "Combate": bqmv, "Torneio": btmv, "Telão": build_viewer_view, "Histórico": build_history_view, "Admin": build_admin_view, "Perfil": bpv}
    def ctp(idx):
        if not bn.destinations: return
        ca.content = None; pg.update()
        if bf := TM.get(bn.destinations[idx].label): ca.content = bf()
        pg.update()
    def ntt(tl):
        for i, d in enumerate(bn.destinations):
            if d.label == tl: bn.selected_index = i; bn.update(); ctp(i); break
    def ct(e): bn.selected_index = int(e.data) if hasattr(e, 'data') and str(e.data).isdigit() else e.control.selected_index; bn.update(); ctp(bn.selected_index)
    def rct(): ctp(bn.selected_index) if bn.visible and bn.destinations else None
    def sma():
        lc.visible, mac.visible, bn.visible = False, True, True; ast["avo"] = "admin"; uab()
        r = cu().get("role", "basic"); ds = []
        if r in ["admin_max", "pro", "organizador", "judge"]: ds.append(ft.NavigationBarDestination(icon=ft.Icons.PEOPLE_OUTLINE, label="Bladers"))
        if r in ["admin_max", "pro", "treinador"]: ds.append(ft.NavigationBarDestination(icon=ft.Icons.FITNESS_CENTER_OUTLINED, label="Treino"))
        ds.append(ft.NavigationBarDestination(icon=ft.Icons.FLASH_ON_OUTLINED, label="Combate"))
        if r in ["admin_max", "pro", "organizador", "judge"]: ds.append(ft.NavigationBarDestination(icon=ft.Icons.EMOJI_EVENTS_OUTLINED, label="Torneio"))
        ds.append(ft.NavigationBarDestination(icon=ft.Icons.CAST_CONNECTED, label="Telão"))
        if r in ["admin_max", "pro", "organizador", "judge"]: ds.append(ft.NavigationBarDestination(icon=ft.Icons.HISTORY_OUTLINED, label="Histórico"))
        if r == "admin_max": ds.append(ft.NavigationBarDestination(icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED, label="Admin"))
        ds.append(ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINE, label="Perfil"))
        bn.destinations.clear(); bn.destinations.extend(ds)
        bn.selected_index, bn.on_change = 0, ct; pg.update(); ctp(0)

    mac.content = ft.Column([ca], expand=True); pg.add(lc, mac, bn)
    def asl():
        while True:
            time.sleep(5) 
            if is_s or lc.visible: continue 
            try:
                r = requests.get(FB_URL, timeout=5)
                if r.status_code == 200 and r.json():
                    n = r.json()
                    if isinstance(n, dict): # Trava de segurança para evitar erro vermelho na tela
                        with dblk:
                            if ast.get("cu"):
                                u = ast["cu"]["username"]
                                if u in n.get("users", {}):
                                    tk = n["users"][u].get("session_token")
                                    if tk and ast.get("stk") and tk != ast.get("stk"): lo(frc=True); continue
                            if n.get("last_updated", 0) > db.get("last_updated", 0): db.clear(); db.update(n); nr = True
                            else: nr = False
                        if nr and bn.destinations and bn.destinations[bn.selected_index].label not in ["Bladers", "Treino", "Combate", "Admin"]: rct()
            except: pass 
    threading.Thread(target=asl, daemon=True).start()

ft.run(main)
