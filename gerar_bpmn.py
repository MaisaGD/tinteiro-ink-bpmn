# Gera o BPMN 2.0 (com diagrama) do fluxo Tinteiro INK
# Uso: python gerar_bpmn.py  -> cria tinteiro-ink.bpmn na mesma pasta
import os
from xml.sax.saxutils import escape

POOL_X, POOL_Y, POOL_W = 30, 30, 2210
LABEL_W = 30
LANES = [  # id, nome, y_top, altura
    ("L_coord", "Coordenação / Gerência", 30, 200),
    ("L_estoque", "Equipe de Estoque", 230, 220),
    ("L_sistema", "Sistema Tinteiro (Supabase + Render)", 450, 320),
    ("L_operador", "Operador de Impressão", 770, 160),
]
SIZE = {"task": (110, 70), "start": (36, 36), "timer": (36, 36), "msg": (36, 36), "cond": (36, 36), "end": (36, 36), "xor": (50, 50)}

# id: (tipo, nome, cx, cy, lane)
E = {
    # Fluxo 1 — Entrada de tintas e insumos
    "S1": ("msg", "Tintas e insumos recebidos", 125, 340, "L_estoque"),
    "T1": ("task", "Lançar nota fiscal e lote de compra", 230, 340, "L_estoque"),
    "T2": ("task", "Gerar QR code para cada garrafa", 380, 530, "L_sistema"),
    "T3": ("task", "Imprimir etiquetas e identificar garrafas", 530, 340, "L_estoque"),
    "G1": ("xor", "Destino da garrafa?", 670, 340, "L_estoque"),
    "T4": ("task", "Armazenar no almoxarifado RJ", 790, 280, "L_estoque"),
    "T5": ("task", "Registrar transferência para SP", 790, 400, "L_estoque"),
    "T6": ("task", "Conferir recebimento da transferência", 930, 400, "L_estoque"),
    "G2": ("xor", "", 1060, 340, "L_estoque"),
    "E1": ("end", "Garrafa disponível em estoque", 1160, 340, "L_estoque"),
    # Fluxo 2 — Consumo na máquina
    "S2": ("cond", "Garrafa acaba na impressora", 125, 850, "L_operador"),
    "T7": ("task", "Trocar garrafa na impressora", 240, 850, "L_operador"),
    "T8": ("task", "Ler QR code da garrafa", 390, 850, "L_operador"),
    "T9": ("task", "Dar baixa da garrafa no estoque", 540, 690, "L_sistema"),
    "G3": ("xor", "Estoque abaixo do mínimo?", 690, 690, "L_sistema"),
    "T10": ("task", "Enviar alerta de estoque mínimo", 840, 690, "L_sistema"),
    "EB1": ("end", "Reposição sinalizada", 990, 690, "L_sistema"),
    "EB2": ("end", "Baixa concluída", 840, 610, "L_sistema"),
    # Fluxo 3 — Coleta diária da API Kornit
    "S3": ("timer", "Todo dia", 1330, 530, "L_sistema"),
    "T12": ("task", "Coletar consumo na API Kornit Konnect", 1450, 530, "L_sistema"),
    "G4": ("xor", "Coleta concluída?", 1590, 530, "L_sistema"),
    "T13": ("task", "Enviar alerta de falha na coleta", 1590, 690, "L_sistema"),
    "EC1": ("end", "Falha comunicada", 1730, 690, "L_sistema"),
    "T14": ("task", "Gravar consumo por máquina", 1720, 530, "L_sistema"),
    "T15": ("task", "Verificar garrafas próximas do vencimento", 1870, 530, "L_sistema"),
    "G5": ("xor", "Há garrafas a vencer?", 2010, 530, "L_sistema"),
    "T16": ("task", "Enviar alerta de vencimento", 2010, 690, "L_sistema"),
    "EC3": ("end", "Vencimento comunicado", 2150, 690, "L_sistema"),
    "EC2": ("end", "Consumo do dia registrado", 2150, 530, "L_sistema"),
    # Fluxo 4 — Acompanhamento semanal
    "S4": ("timer", "Toda semana", 1330, 105, "L_coord"),
    "T17": ("task", "Receber resumo semanal por e-mail", 1450, 105, "L_coord"),
    "T18": ("task", "Analisar consumo, custo e desperdício no dashboard", 1600, 105, "L_coord"),
    "G6": ("xor", "Precisa de ação?", 1740, 105, "L_coord"),
    "T19": ("task", "Definir ação (compra, ajuste ou desperdício)", 1880, 105, "L_coord"),
    "ED1": ("end", "Ação definida", 2020, 105, "L_coord"),
    "ED2": ("end", "Semana acompanhada", 1880, 190, "L_coord"),
    # Fluxo 5 — Inventário físico
    "S5": ("timer", "Inventário periódico", 1330, 340, "L_estoque"),
    "T20": ("task", "Fazer contagem física das garrafas", 1450, 340, "L_estoque"),
    "T21": ("task", "Registrar contagem no Tinteiro", 1600, 340, "L_estoque"),
    "G7": ("xor", "Há divergência?", 1740, 340, "L_estoque"),
    "T22": ("task", "Ajustar saldo e registrar o motivo", 1880, 340, "L_estoque"),
    "EE1": ("end", "Saldo ajustado", 2020, 340, "L_estoque"),
    "EE2": ("end", "Inventário conferido", 1880, 415, "L_estoque"),
}

F = [  # origem, destino, rótulo
    ("S1", "T1", ""), ("T1", "T2", ""), ("T2", "T3", ""), ("T3", "G1", ""),
    ("G1", "T4", "RJ"), ("G1", "T5", "SP"), ("T5", "T6", ""), ("T4", "G2", ""), ("T6", "G2", ""), ("G2", "E1", ""),
    ("S2", "T7", ""), ("T7", "T8", ""), ("T8", "T9", ""), ("T9", "G3", ""),
    ("G3", "T10", "Sim"), ("G3", "EB2", "Não"), ("T10", "EB1", ""),
    ("S3", "T12", ""), ("T12", "G4", ""), ("G4", "T14", "Sim"), ("G4", "T13", "Não"), ("T13", "EC1", ""),
    ("T14", "T15", ""), ("T15", "G5", ""), ("G5", "T16", "Sim"), ("G5", "EC2", "Não"), ("T16", "EC3", ""),
    ("S4", "T17", ""), ("T17", "T18", ""), ("T18", "G6", ""), ("G6", "T19", "Sim"), ("G6", "ED2", "Não"), ("T19", "ED1", ""),
    ("S5", "T20", ""), ("T20", "T21", ""), ("T21", "G7", ""), ("G7", "T22", "Sim"), ("G7", "EE2", "Não"), ("T22", "EE1", ""),
]


def box(i):
    t, _, cx, cy, _ = E[i]
    w, h = SIZE[t]
    return cx - w / 2, cy - h / 2, w, h


def waypoints(a, b):
    ta, _, ax, ay, _ = E[a]
    tb, _, bx, by, _ = E[b]
    wa, ha = SIZE[ta]
    wb, hb = SIZE[tb]
    if ay == by:
        return [(ax + wa / 2, ay), (bx - wb / 2, by)]
    if ax == bx:
        if by > ay:
            return [(ax, ay + ha / 2), (bx, by - hb / 2)]
        return [(ax, ay - ha / 2), (bx, by + hb / 2)]
    if ta == "xor":  # sai na vertical, entra na horizontal
        y0 = ay + ha / 2 if by > ay else ay - ha / 2
        return [(ax, y0), (ax, by), (bx - wb / 2, by)]
    # sai na horizontal, entra na vertical
    y1 = by - hb / 2 if by > ay else by + hb / 2
    return [(ax + wa / 2, ay), (bx, ay), (bx, y1)]


tag = {"task": "task", "start": "startEvent", "timer": "startEvent", "msg": "startEvent", "cond": "startEvent", "end": "endEvent", "xor": "exclusiveGateway"}
inc = {k: [] for k in E}
out = {k: [] for k in E}
for n, (a, b, _) in enumerate(F, 1):
    out[a].append(f"F{n}")
    inc[b].append(f"F{n}")

x = ['<?xml version="1.0" encoding="UTF-8"?>',
     '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" '
     'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
     'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
     'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
     'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
     'id="Def_Tinteiro" targetNamespace="https://github.com/MaisaGD/tinteiro-ink-bpmn">',
     '  <collaboration id="Collab_Tinteiro">',
     '    <participant id="Pool_Tinteiro" name="Tinteiro INK — Controle de estoque e consumo de tintas" processRef="Proc_Tinteiro"/>',
     '  </collaboration>',
     '  <process id="Proc_Tinteiro" name="Tinteiro INK" isExecutable="false">',
     '    <laneSet id="LaneSet_1">']
for lid, ln, _, _ in LANES:
    x.append(f'      <lane id="{lid}" name="{escape(ln)}">')
    for k, v in E.items():
        if v[4] == lid:
            x.append(f"        <flowNodeRef>{k}</flowNodeRef>")
    x.append("      </lane>")
x.append("    </laneSet>")
for k, (t, nm, *_ ) in E.items():
    attrs = f'id="{k}" name="{escape(nm, {chr(34): "&quot;"})}"'
    x.append(f"    <{tag[t]} {attrs}>")
    for f in inc[k]:
        x.append(f"      <incoming>{f}</incoming>")
    for f in out[k]:
        x.append(f"      <outgoing>{f}</outgoing>")
    if t == "timer":
        x.append(f'      <timerEventDefinition id="TD_{k}"/>')
    if t == "msg":
        x.append(f'      <messageEventDefinition id="MD_{k}"/>')
    if t == "cond":
        x.append(f'      <conditionalEventDefinition id="CD_{k}"><condition xsi:type="tFormalExpression">Garrafa vazia</condition></conditionalEventDefinition>')
    x.append(f"    </{tag[t]}>")
for n, (a, b, lb) in enumerate(F, 1):
    x.append(f'    <sequenceFlow id="F{n}" name="{lb}" sourceRef="{a}" targetRef="{b}"/>')
x.append("  </process>")

x.append('  <bpmndi:BPMNDiagram id="Diag_1" name="Tinteiro INK">')
x.append('    <bpmndi:BPMNPlane id="Plane_1" bpmnElement="Collab_Tinteiro">')
pool_h = sum(h for *_, h in LANES)
x.append(f'      <bpmndi:BPMNShape id="Pool_Tinteiro_di" bpmnElement="Pool_Tinteiro" isHorizontal="true">'
         f'<dc:Bounds x="{POOL_X}" y="{POOL_Y}" width="{POOL_W}" height="{pool_h}"/></bpmndi:BPMNShape>')
for lid, _, y, h in LANES:
    x.append(f'      <bpmndi:BPMNShape id="{lid}_di" bpmnElement="{lid}" isHorizontal="true">'
             f'<dc:Bounds x="{POOL_X + LABEL_W}" y="{y}" width="{POOL_W - LABEL_W}" height="{h}"/></bpmndi:BPMNShape>')
for k, v in E.items():
    bx, by, w, h = box(k)
    extra = ' isMarkerVisible="true"' if v[0] == "xor" else ""
    lab = ""
    if v[0] in ("start", "timer", "msg", "cond", "end", "xor") and v[1]:
        ly = (by + h + 4 if k in ("G1", "G3") else by - 32) if v[0] == "xor" else by + h + 4
        lab = (f'<bpmndi:BPMNLabel><dc:Bounds x="{bx - 32}" y="{ly}" width="{w + 64}" height="28"/></bpmndi:BPMNLabel>')
    x.append(f'      <bpmndi:BPMNShape id="{k}_di" bpmnElement="{k}"{extra}>'
             f'<dc:Bounds x="{bx}" y="{by}" width="{w}" height="{h}"/>{lab}</bpmndi:BPMNShape>')
for n, (a, b, lb) in enumerate(F, 1):
    pts = waypoints(a, b)
    wp = "".join(f'<di:waypoint x="{px}" y="{py}"/>' for px, py in pts)
    lab = ""
    if lb:
        px, py = pts[0]
        vert = pts[0][0] == pts[1][0]
        lx, ly = (px + 6, py + 2 if pts[1][1] > py else py - 18) if vert else (px + 4, py - 20)
        lab = f'<bpmndi:BPMNLabel><dc:Bounds x="{lx}" y="{ly}" width="30" height="16"/></bpmndi:BPMNLabel>'
    x.append(f'      <bpmndi:BPMNEdge id="F{n}_di" bpmnElement="F{n}">{wp}{lab}</bpmndi:BPMNEdge>')
x += ["    </bpmndi:BPMNPlane>", "  </bpmndi:BPMNDiagram>", "</definitions>"]

destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tinteiro-ink.bpmn")
with open(destino, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(x))
print("ok", len(E), "elementos", len(F), "fluxos")
