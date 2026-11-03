#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
NIGHT CITY RPG MOBILE — SERVIDOR DE SINCRONIZAÇÃO (OBSIDIAN <-> ANDROID)
=============================================================================
Sincroniza em tempo real:
- Cofre do Obsidian (configurável via variável de ambiente OBSIDIAN_VAULT_DIR)
- Progresso do RPG (XP, Nível, Classe, Atributos, Conquistas, Streak)
- Quests (Daily Quests, Weekly Quests, Main Quests, Side Quests, Boss Fights)
- Configuração de Pop-ups e Notificações (Geral e Individual por Daily Quest)
- Integração opcional com Boletim Acadêmico e Google Classroom
- Estado de demonstração (Demo State) integrado caso nenhum cofre seja apontado
=============================================================================
"""

import json
import math
import os
import re
import socket
import subprocess
import sys
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

MOBILE_DIR = Path(__file__).resolve().parent
VAULT_DIR = Path(os.environ.get("OBSIDIAN_VAULT_DIR", str(MOBILE_DIR / "vault_demo")))
RPG_PLUGIN_DIR = VAULT_DIR / ".obsidian" / "plugins" / "night-city-rpg"
RPG_DATA_FILE = RPG_PLUGIN_DIR / "data.json"
ACAD_PLUGIN_DIR = VAULT_DIR / ".obsidian" / "plugins" / "academic-sync"
ACAD_DATA_FILE = ACAD_PLUGIN_DIR / "data.json"
HISTORICO_CACHE_FILE = ACAD_PLUGIN_DIR / "historico_cache.json"
CLASSROOM_CACHE_FILE = ACAD_PLUGIN_DIR / "classroom_cache.json"
NOTIF_SETTINGS_FILE = MOBILE_DIR / "notification_settings.json"
SYNC_SCRIPT_FILE = VAULT_DIR / "99 - Templates" / "sincronizar_academico.py"

PORT = int(os.environ.get("NIGHTCITY_PORT", "8077"))

TIERS = [
    {"min": 1, "name": "Street Kid", "rank": "Iniciante", "game": "Cyberpunk 2077", "icon": "🛹", "color": "#f3e600", "quote": "Todo mundo começa nas ruas de Night City."},
    {"min": 10, "name": "Netrunner Aprendiz", "rank": "Aprendiz", "game": "Cyberpunk 2077", "icon": "💾", "color": "#00f0ff", "quote": "Jack in. A Rede é sua nova sala de aula."},
    {"min": 20, "name": "Hacker da DedSec", "rank": "Intermediário", "game": "Watch Dogs", "icon": "📱", "color": "#39ff14", "quote": "Todo sistema pode ser entendido... e hackeado."},
    {"min": 30, "name": "Bruxo da Escola do Lobo", "rank": "Avançado", "game": "The Witcher 3", "icon": "🐺", "color": "#cfd8dc", "quote": "Monstros, contratos e provas: tudo tem um ponto fraco."},
    {"min": 40, "name": "Cavaleiro de Hallownest", "rank": "Veterano", "game": "Hollow Knight", "icon": "🗡️", "color": "#8ab4ff", "quote": "Nenhum boss é impossível com paciência e prática."},
    {"min": 50, "name": "Spartan-II", "rank": "Elite", "game": "Halo", "icon": "🪖", "color": "#7cb342", "quote": "Termine o que começou, Master Chief."},
    {"min": 60, "name": "Dragonborn", "rank": "Mestre", "game": "The Elder Scrolls V: Skyrim", "icon": "🐉", "color": "#ff8c00", "quote": "FUS RO DAH nas pendências!"},
    {"min": 70, "name": "Comandante N7", "rank": "Grão-Mestre", "game": "Mass Effect", "icon": "🚀", "color": "#ff3b3b", "quote": "Eu sou o Comandante Shepard, e esta é minha tarefa favorita."},
    {"min": 80, "name": "Augmentado", "rank": "Lendário", "game": "Deus Ex", "icon": "🦾", "color": "#ffb000", "quote": "Eu nunca pedi por isso... mas aceitei o desafio."},
    {"min": 90, "name": "Lenda de Night City", "rank": "Mítico", "game": "Cyberpunk 2077", "icon": "🌃", "color": "#ff003c", "quote": "Seu nome já é falado no Afterlife."},
    {"min": 100, "name": "Rockerboy Imortal", "rank": "Ascendido", "game": "Cyberpunk 2077 — Johnny Silverhand", "icon": "🎸", "color": "#ff00ff", "quote": "Wake up, Samurai. Temos uma cidade para queimar."},
]

ATTRS = {
    "INT": {"name": "Inteligência", "icon": "🧠", "color": "#00f0ff", "desc": "Estudos, IA, modelagem matemática, provas e leituras"},
    "TEC": {"name": "Técnica", "icon": "🛠️", "color": "#f3e600", "desc": "Código Python/JS, projetos, arquitetura e sistemas"},
    "REF": {"name": "Reflexos", "icon": "⚡", "color": "#ff003c", "desc": "Entregas rápidas e resolução ágil de pendências"},
    "COOL": {"name": "Sangue-Frio", "icon": "😎", "color": "#b388ff", "desc": "Gestão de projetos, planejamento e organização"},
    "CORPO": {"name": "Corpo", "icon": "💪", "color": "#39ff14", "desc": "Saúde, treino físico, hidratação e bem-estar"},
}

TYPES = {
    "boss": {"label": "BOSS", "icon": "☠️", "order": 0, "xp": 150},
    "main": {"label": "MAIN", "icon": "⚔️", "order": 1, "xp": 50},
    "side": {"label": "SIDE", "icon": "🧭", "order": 2, "xp": 30},
    "weekly": {"label": "WEEKLY", "icon": "📅", "order": 3, "xp": 25},
    "daily": {"label": "DAILY", "icon": "🔁", "order": 4, "xp": 10},
    "comum": {"label": "GIG", "icon": "📌", "order": 5, "xp": 15},
}

DEFAULT_NOTIF_SETTINGS = {
    "masterEnabled": True,
    "inAppPopupBanner": True,
    "persistentHudNotification": True,
    "soundEffects": True,
    "reminderTimes": ["09:00", "14:00", "20:00"],
    "bossAlertEnabled": True,
    "disabledQuestKeys": {},
}

DEMO_DAILY_QUESTS = [
    {
        "id": "revisar_algoritmos_e_estruturas_de_dados_30_min",
        "key": "demo::daily::1",
        "file": "00 - Início/🎮 Central de Quests.md",
        "noteName": "Central de Quests",
        "line": 10,
        "rawText": "Revisar algoritmos e estruturas de dados (30 min) #daily #int",
        "clean": "Revisar algoritmos e estruturas de dados (30 min)",
        "completed": False,
        "type": "daily",
        "typeLabel": "DAILY",
        "typeIcon": "🔁",
        "xp": 10,
        "attr": "INT",
        "attrIcon": "🧠",
        "attrName": "Inteligência",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
    {
        "id": "commit_diario_e_revisao_de_codigo_no_git",
        "key": "demo::daily::2",
        "file": "00 - Início/🎮 Central de Quests.md",
        "noteName": "Central de Quests",
        "line": 11,
        "rawText": "Commit diário e revisão de código no Git #daily #tec",
        "clean": "Commit diário e revisão de código no Git",
        "completed": False,
        "type": "daily",
        "typeLabel": "DAILY",
        "typeIcon": "🔁",
        "xp": 10,
        "attr": "TEC",
        "attrIcon": "🛠️",
        "attrName": "Técnica",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
    {
        "id": "leitura_de_documentacao_ou_artigo_tecnico",
        "key": "demo::daily::3",
        "file": "00 - Início/🎮 Central de Quests.md",
        "noteName": "Central de Quests",
        "line": 12,
        "rawText": "Leitura de documentação ou artigo técnico #daily #int",
        "clean": "Leitura de documentação ou artigo técnico",
        "completed": False,
        "type": "daily",
        "typeLabel": "DAILY",
        "typeIcon": "🔁",
        "xp": 10,
        "attr": "INT",
        "attrIcon": "🧠",
        "attrName": "Inteligência",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
    {
        "id": "sessao_de_treino_fisico_mobilidade_e_hidratacao_2l",
        "key": "demo::daily::4",
        "file": "00 - Início/🎮 Central de Quests.md",
        "noteName": "Central de Quests",
        "line": 13,
        "rawText": "Sessão de treino físico / mobilidade e hidratação (2L) #daily #corpo",
        "clean": "Sessão de treino físico / mobilidade e hidratação (2L)",
        "completed": False,
        "type": "daily",
        "typeLabel": "DAILY",
        "typeIcon": "🔁",
        "xp": 10,
        "attr": "CORPO",
        "attrIcon": "💪",
        "attrName": "Corpo",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
    {
        "id": "organizar_backlog_e_metas_prioritarias_do_dia",
        "key": "demo::daily::5",
        "file": "00 - Início/🎮 Central de Quests.md",
        "noteName": "Central de Quests",
        "line": 14,
        "rawText": "Organizar backlog e metas prioritárias do dia #daily #cool",
        "clean": "Organizar backlog e metas prioritárias do dia",
        "completed": True,
        "type": "daily",
        "typeLabel": "DAILY",
        "typeIcon": "🔁",
        "xp": 10,
        "attr": "COOL",
        "attrIcon": "😎",
        "attrName": "Sangue-Frio",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
]

DEMO_QUESTS = [
    {
        "id": "derrotar_avaliacao_final_de_arquitetura_de_sistemas",
        "key": "demo::boss::1",
        "file": "00 - Início/🎮 Central de Quests.md",
        "noteName": "Central de Quests",
        "line": 20,
        "rawText": "Derrotar Avaliação Final de Arquitetura de Sistemas (Prazo: Sexta) #boss #int",
        "clean": "Derrotar Avaliação Final de Arquitetura de Sistemas (Prazo: Sexta)",
        "completed": False,
        "type": "boss",
        "typeLabel": "BOSS",
        "typeIcon": "☠️",
        "xp": 150,
        "attr": "INT",
        "attrIcon": "🧠",
        "attrName": "Inteligência",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
    {
        "id": "entrega_e_defesa_do_prototipo_de_engenharia_de_software",
        "key": "demo::boss::2",
        "file": "00 - Início/🎮 Central de Quests.md",
        "noteName": "Central de Quests",
        "line": 21,
        "rawText": "Entrega e Defesa do Protótipo de Engenharia de Software #boss #tec",
        "clean": "Entrega e Defesa do Protótipo de Engenharia de Software",
        "completed": False,
        "type": "boss",
        "typeLabel": "BOSS",
        "typeIcon": "☠️",
        "xp": 150,
        "attr": "TEC",
        "attrIcon": "🛠️",
        "attrName": "Técnica",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
    {
        "id": "implementar_autenticacao_jwt_e_rotas_rest_no_backend",
        "key": "demo::main::1",
        "file": "00 - Início/🎮 Central de Quests.md",
        "noteName": "Central de Quests",
        "line": 25,
        "rawText": "Implementar autenticação JWT e rotas REST no backend #main #tec",
        "clean": "Implementar autenticação JWT e rotas REST no backend",
        "completed": False,
        "type": "main",
        "typeLabel": "MAIN",
        "typeIcon": "⚔️",
        "xp": 50,
        "attr": "TEC",
        "attrIcon": "🛠️",
        "attrName": "Técnica",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
    {
        "id": "redigir_relatorio_tecnico_de_modelagem_e_simulacao",
        "key": "demo::main::2",
        "file": "00 - Início/🎮 Central de Quests.md",
        "noteName": "Central de Quests",
        "line": 26,
        "rawText": "Redigir relatório técnico de modelagem e simulação #main #int",
        "clean": "Redigir relatório técnico de modelagem e simulação",
        "completed": False,
        "type": "main",
        "typeLabel": "MAIN",
        "typeIcon": "⚔️",
        "xp": 50,
        "attr": "INT",
        "attrIcon": "🧠",
        "attrName": "Inteligência",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
    {
        "id": "resolver_lista_de_exercicios_de_calculo_numerico",
        "key": "demo::side::1",
        "file": "00 - Início/🎮 Central de Quests.md",
        "noteName": "Central de Quests",
        "line": 30,
        "rawText": "Resolver lista de exercícios de Cálculo Numérico #side #int",
        "clean": "Resolver lista de exercícios de Cálculo Numérico",
        "completed": False,
        "type": "side",
        "typeLabel": "SIDE",
        "typeIcon": "🧭",
        "xp": 30,
        "attr": "INT",
        "attrIcon": "🧠",
        "attrName": "Inteligência",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
    {
        "id": "configurar_pipeline_de_linting_e_formatacao_automatica",
        "key": "demo::side::2",
        "file": "00 - Início/🎮 Central de Quests.md",
        "noteName": "Central de Quests",
        "line": 31,
        "rawText": "Configurar pipeline de linting e formatação automática #side #ref",
        "clean": "Configurar pipeline de linting e formatação automática",
        "completed": False,
        "type": "side",
        "typeLabel": "SIDE",
        "typeIcon": "🧭",
        "xp": 30,
        "attr": "REF",
        "attrIcon": "⚡",
        "attrName": "Reflexos",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
    {
        "id": "treino_a_membros_superiores_e_core",
        "key": "demo::weekly::1",
        "file": "02 - Rotina & Diário/📅 Planejamento Semanal.md",
        "noteName": "Planejamento Semanal",
        "line": 40,
        "rawText": "Treino A — Membros Superiores e Core (Segunda/Quinta) #weekly #corpo",
        "clean": "Treino A — Membros Superiores e Core (Segunda/Quinta)",
        "completed": False,
        "type": "weekly",
        "typeLabel": "WEEKLY",
        "typeIcon": "📅",
        "xp": 25,
        "attr": "CORPO",
        "attrIcon": "💪",
        "attrName": "Corpo",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
    {
        "id": "treino_b_membros_inferiores_e_cardio",
        "key": "demo::weekly::2",
        "file": "02 - Rotina & Diário/📅 Planejamento Semanal.md",
        "noteName": "Planejamento Semanal",
        "line": 41,
        "rawText": "Treino B — Membros Inferiores e Cardio (Terça/Sexta) #weekly #corpo",
        "clean": "Treino B — Membros Inferiores e Cardio (Terça/Sexta)",
        "completed": False,
        "type": "weekly",
        "typeLabel": "WEEKLY",
        "typeIcon": "📅",
        "xp": 25,
        "attr": "CORPO",
        "attrIcon": "💪",
        "attrName": "Corpo",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
    {
        "id": "revisao_semanal_de_sprint_e_limpeza_de_notas",
        "key": "demo::weekly::3",
        "file": "02 - Rotina & Diário/📅 Planejamento Semanal.md",
        "noteName": "Planejamento Semanal",
        "line": 42,
        "rawText": "Revisão semanal de sprint e limpeza de notas #weekly #cool",
        "clean": "Revisão semanal de sprint e limpeza de notas",
        "completed": True,
        "type": "weekly",
        "typeLabel": "WEEKLY",
        "typeIcon": "📅",
        "xp": 25,
        "attr": "COOL",
        "attrIcon": "😎",
        "attrName": "Sangue-Frio",
        "popupEnabled": True,
        "individualPopupEnabled": True,
    },
]

DEMO_PROJECTS = [
    {
        "id": "neural-core",
        "code": "PROJETO 01 // IA & SIMULAÇÃO",
        "title": "🤖 NeuralCore — Monitoramento Preditivo com Redes Neurais",
        "status": "🟢 Em Desenvolvimento Ativo (Validação Cruzada & Fine-Tuning)",
        "color": "#f3e600",
        "summary": "Pipeline de aprendizado profundo (MLP) para reconstrução espacial de sinais e detecção de anomalias operacionais em tempo real.",
        "specs": [
            "Arquitetura: Rede Perceptron Multicamadas com ativação tanh/linear",
            "Transfer Learning: Congelamento de camadas base e ajuste fino com Adam (lr=1e-4)",
            "Validação Estatística: Leave-One-Out (LOO) e métricas MAE, RMSE e R²",
        ],
        "notePath": "01 - Projetos & Trabalhos/🤖 Projeto NeuralCore.md",
    },
    {
        "id": "nexus-hub",
        "code": "PROJETO 02 // FULL-STACK & GESTÃO",
        "title": "🌐 NexusHub — Plataforma Colaborativa de Pesquisa & Dev",
        "status": "🟡 Arquitetura de Software & Prototipação MVP",
        "color": "#00f0ff",
        "summary": "Aplicação web e mobile para integração de equipes técnicas, gestão de tarefas gamificadas e acompanhamento de metas de engenharia.",
        "specs": [
            "Sincronização bidirecional offline-first via JSON e API REST",
            "Dashboard responsivo com telemetria de produtividade e streaks",
            "Integração modular com agendas (.ics) e cofres Markdown",
        ],
        "notePath": "01 - Projetos & Trabalhos/🌐 Projeto NexusHub.md",
    },
]

DEMO_ACADEMIC = {
    "boletimWeb": [
        {"diario": "101", "disciplina": "ENG01 - Engenharia de Software", "chAulas": "60", "aulasDadas": "40", "faltas": "2", "frequencia": "97%", "situacao": "Cursando", "e1Nota": "N1: 9.2", "e2Nota": "-"},
        {"diario": "102", "disciplina": "IA02 - Inteligência Artificial", "chAulas": "60", "aulasDadas": "38", "faltas": "0", "frequencia": "100%", "situacao": "Cursando", "e1Nota": "N1: 9.5", "e2Nota": "-"},
        {"diario": "103", "disciplina": "CALC03 - Cálculo Numérico Computacional", "chAulas": "60", "aulasDadas": "42", "faltas": "2", "frequencia": "97%", "situacao": "Cursando", "e1Nota": "N1: 8.8", "e2Nota": "-"},
        {"diario": "104", "disciplina": "ARQ04 - Arquitetura de Sistemas", "chAulas": "60", "aulasDadas": "36", "faltas": "0", "frequencia": "100%", "situacao": "Cursando", "e1Nota": "N1: 9.0", "e2Nota": "-"},
    ],
    "requisitos": [
        {"requisito": "Disciplinas Obrigatórias", "prevista": 2400, "cumprida": 1500, "pendente": "900h"},
        {"requisito": "Disciplinas Optativas", "prevista": 300, "cumprida": 180, "pendente": "120h"},
        {"requisito": "Atividades Complementares", "prevista": 300, "cumprida": 120, "pendente": "180h"},
    ],
    "historicoItens": [
        {"codigo": "ALG01", "disciplina": "Algoritmos e Estruturas de Dados", "periodoCurso": 1, "anoLetivo": "Semestre 1", "chTexto": "80", "notaTexto": "9.4", "frequencia": "98%", "situacao": "Aprovado"},
        {"codigo": "POO02", "disciplina": "Programação Orientada a Objetos", "periodoCurso": 2, "anoLetivo": "Semestre 2", "chTexto": "80", "notaTexto": "9.1", "frequencia": "100%", "situacao": "Aprovado"},
        {"codigo": "BD03", "disciplina": "Banco de Dados Relacionais", "periodoCurso": 3, "anoLetivo": "Semestre 3", "chTexto": "60", "notaTexto": "8.9", "frequencia": "96%", "situacao": "Aprovado"},
        {"codigo": "RED04", "disciplina": "Redes de Computadores e Protocolos", "periodoCurso": 4, "anoLetivo": "Semestre 4", "chTexto": "60", "notaTexto": "9.0", "frequencia": "100%", "situacao": "Aprovado"},
        {"codigo": "SO05", "disciplina": "Sistemas Operacionais", "periodoCurso": 5, "anoLetivo": "Semestre 5", "chTexto": "60", "notaTexto": "-", "frequencia": "-", "situacao": "-"},
    ],
}

DEMO_CLASSROOM = {
    "coursesCount": 4,
    "pendingWork": [
        {"id": "cw1", "courseName": "Inteligência Artificial", "title": "Implementação de Rede Neural MLP em Python", "dueDate": "Sexta-feira", "alternateLink": "", "isTurnedIn": False},
        {"id": "cw2", "courseName": "Engenharia de Software", "title": "Modelagem de Arquitetura e Diagrama C4", "dueDate": "Próxima Semana", "alternateLink": "", "isTurnedIn": False},
    ],
    "completedWork": [],
    "announcements": [],
}


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return json.loads(json.dumps(default))


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_notif_settings() -> dict:
    saved = load_json(NOTIF_SETTINGS_FILE, DEFAULT_NOTIF_SETTINGS)
    merged = dict(DEFAULT_NOTIF_SETTINGS)
    merged.update(saved)
    if not isinstance(merged.get("disabledQuestKeys"), dict):
        merged["disabledQuestKeys"] = {}
    return merged


def clean_text(t: str) -> str:
    t = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", t)
    t = re.sub(r"\[\[([^\]]+)\]\]", r"\1", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"[*_`]", "", t)
    t = re.sub(r"#(xp/\d+|boss|main|epica|side|weekly|semanal|daily|int|ref|tec|corpo|cool|estudo|codigo|projeto|organizacao|saude|faculdade|prova|urgente)\b", "", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip()


def classify_task(text: str, rel_path: str, base_xp: int = 15) -> dict:
    qtype = "comum"
    if re.search(r"#boss\b", text, re.I):
        qtype = "boss"
    elif re.search(r"#(main|epica)\b", text, re.I):
        qtype = "main"
    elif re.search(r"#side\b", text, re.I):
        qtype = "side"
    elif re.search(r"#(weekly|semanal)\b", text, re.I):
        qtype = "weekly"
    elif re.search(r"#daily\b", text, re.I):
        qtype = "daily"
    elif re.search(r"\b(prova|avalia[çc][ãa]o|exame)\b", text, re.I):
        qtype = "boss"
    elif re.search(r"\b(trabalho|relat[óo]rio|projetos?|semin[áa]rio|entrega)\b", text, re.I):
        qtype = "main"
    elif re.search(r"\b(atividades?|exerc[íi]cios?|lista|tarefa|resumo|estudar)\b", text, re.I):
        qtype = "side"

    xp = base_xp if qtype == "comum" else TYPES[qtype]["xp"]
    m_xp = re.search(r"#xp/(\d+)", text, re.I) or re.search(r"\[xp::\s*(\d+)\]", text, re.I)
    if m_xp:
        xp = int(m_xp.group(1))

    attr = "REF"
    m_attr = re.search(r"#(int|ref|tec|corpo|cool)\b", text, re.I)
    if m_attr:
        attr = m_attr.group(1).upper()
    elif re.search(r"c[óo]digo|code|program|\bpoo\b|software|compilador|banco de dados|python|java|diagrama|\buml\b|\bgit\b|\bapi\b|sistema|excalidraw|circuito|#codigo", text, re.I):
        attr = "TEC"
    elif re.search(r"prova|estud|aula|resumo|leitura|\bler\b|livro|exerc|lista|revis|disciplina|mat[ée]ria|cap[íi]tulo|\bcap\b|rna|reator|pwr|#estudo", text, re.I):
        attr = "INT"
    elif re.search(r"treino|academia|corrida|caminhada|sa[úu]de|dormir|[áa]gua|alonga|muscula|biomonitor|#saude", text, re.I):
        attr = "CORPO"
    elif re.search(r"rotina|organiz|backup|limp|planej|meta|agenda|di[áa]ri|escopo|reuni|soma|#projeto|#organizacao", text, re.I):
        attr = "COOL"
    elif rel_path.startswith("03 - "):
        attr = "INT"
    elif rel_path.startswith("01 - "):
        attr = "TEC"
    elif rel_path.startswith("02 - "):
        attr = "COOL"

    return {"type": qtype, "xp": xp, "attr": attr}


def xp_to_next(level: int) -> int:
    return 80 + (level - 1) * 15


def level_from_xp(xp: int) -> dict:
    level = 1
    rem = max(0, int(xp))
    while rem >= xp_to_next(level) and level < 999:
        rem -= xp_to_next(level)
        level += 1
    return {"level": level, "cur": rem, "next": xp_to_next(level)}


def tier_index(level: int) -> int:
    idx = 0
    for i, t in enumerate(TIERS):
        if level >= t["min"]:
            idx = i
    return idx


def scan_vault_and_compute_state() -> dict:
    rpg_data = load_json(
        RPG_DATA_FILE,
        {
            "playerName": "Netrunner V",
            "baseXP": 15,
            "revokeOnUncheck": True,
            "ignoreFolders": ["99 - Templates", "Excalidraw"],
            "questBoardExclude": ["00 - Início/🏠 Página Inicial.md"],
            "ledger": {},
            "bonusXP": 1450,
            "achievements": {},
            "log": [
                {"ts": int(datetime.now().timestamp() * 1000) - 3600000, "text": "Estruturar diagrama de classes UML do módulo principal", "xp": 30, "type": "side", "attr": "TEC"},
                {"ts": int(datetime.now().timestamp() * 1000) - 7200000, "text": "Revisão semanal de sprint e limpeza de notas", "xp": 25, "type": "weekly", "attr": "COOL"},
                {"ts": int(datetime.now().timestamp() * 1000) - 10800000, "text": "Organizar backlog e metas prioritárias do dia", "xp": 10, "type": "daily", "attr": "COOL"},
            ],
            "lastLevel": 12,
            "lastDailyReset": "",
            "initialized": True,
        },
    )
    notif_cfg = get_notif_settings()
    now_dt = datetime.now()
    today = now_dt.strftime("%Y-%m-%d")
    monday_dt = now_dt - timedelta(days=now_dt.weekday())
    week_str = monday_dt.strftime("%Y-%m-%d")
    ignore_folders = [f.strip().rstrip("/") for f in (rpg_data.get("ignoreFolders") or []) if f.strip()]
    base_xp = int(rpg_data.get("baseXP") or 15)
    ledger = rpg_data.get("ledger") or {}

    all_quests = []
    daily_quests = []
    weekly_quests = []
    seen_daily_clean = set()
    seen_weekly_clean = set()
    seen_quest_clean = set()
    ledger_changed = False

    if VAULT_DIR.exists():
        for md_file in sorted(VAULT_DIR.rglob("*.md")):
            rel_path = md_file.relative_to(VAULT_DIR).as_posix()
            if rel_path.startswith(".obsidian/"):
                continue
            if any(rel_path == ig or rel_path.startswith(ig + "/") for ig in ignore_folders):
                continue

            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            generated = bool(re.search(r"Sincronizado automaticamente|Sincronizado com SUAP|Última sincronização automática|Telemetria sincronizada", content, re.I))
            lines = content.split("\n")
            in_code = False
            seen_keys = {}

            for i, raw_line in enumerate(lines):
                stripped = re.sub(r"^[\s>]*", "", raw_line.rstrip("\r"))
                if re.match(r"^(```|~~~)", stripped):
                    in_code = not in_code
                    continue
                if in_code:
                    continue

                m = re.match(r"^[-*+]\s+\[(.)\]\s+(.+)$", stripped)
                if not m:
                    continue

                status = m.group(1)
                text = re.sub(r"\s+", " ", m.group(2).strip())
                is_daily = bool(re.search(r"#daily\b", text, re.I))
                is_weekly = bool(re.search(r"#(weekly|semanal)\b", text, re.I))
                cycle_suffix = f"::{today}" if is_daily else (f"::W{week_str}" if is_weekly else "")
                base_key = f"{rel_path}::{text}{cycle_suffix}"
                seen_keys[base_key] = seen_keys.get(base_key, 0) + 1
                key = f"{base_key}::{seen_keys[base_key]}" if seen_keys[base_key] > 1 else base_key
                cls = classify_task(text, rel_path, base_xp)
                cln = clean_text(text)
                quest_id = re.sub(r"[^a-z0-9]+", "_", cln.lower()).strip("_")[:64]

                is_done = status.lower() == "x"
                if is_done and key not in ledger:
                    now = datetime.now()
                    entry = {
                        "xp": cls["xp"],
                        "type": cls["type"],
                        "attr": cls["attr"],
                        "date": today,
                        "hour": now.hour,
                        "ts": int(now.timestamp() * 1000),
                        "text": cln,
                        "file": rel_path,
                    }
                    ledger[key] = entry
                    rpg_data.setdefault("log", []).insert(
                        0,
                        {"ts": entry["ts"], "text": cln, "xp": cls["xp"], "type": cls["type"], "attr": cls["attr"]},
                    )
                    ledger_changed = True
                elif status == " " and key in ledger and not generated and rpg_data.get("revokeOnUncheck", True):
                    old = ledger.pop(key)
                    rpg_data.setdefault("log", []).insert(
                        0,
                        {"ts": int(datetime.now().timestamp() * 1000), "text": cln, "xp": -old.get("xp", 10), "type": "revoke", "attr": cls["attr"]},
                    )
                    ledger_changed = True

                popup_enabled = notif_cfg["masterEnabled"] and not notif_cfg["disabledQuestKeys"].get(quest_id, False)
                item_obj = {
                    "id": quest_id,
                    "key": key,
                    "file": rel_path,
                    "noteName": Path(rel_path).stem,
                    "line": i,
                    "rawText": text,
                    "clean": cln,
                    "completed": is_done,
                    "type": cls["type"],
                    "typeLabel": TYPES[cls["type"]]["label"],
                    "typeIcon": TYPES[cls["type"]]["icon"],
                    "xp": cls["xp"],
                    "attr": cls["attr"],
                    "attrIcon": ATTRS[cls["attr"]]["icon"],
                    "attrName": ATTRS[cls["attr"]]["name"],
                    "popupEnabled": popup_enabled,
                    "individualPopupEnabled": not notif_cfg["disabledQuestKeys"].get(quest_id, False),
                }

                if "Página Inicial" in rel_path:
                    continue

                if cls["type"] == "daily":
                    if quest_id not in seen_daily_clean:
                        seen_daily_clean.add(quest_id)
                        daily_quests.append(item_obj)
                elif cls["type"] == "weekly":
                    if quest_id not in seen_weekly_clean:
                        seen_weekly_clean.add(quest_id)
                        weekly_quests.append(item_obj)
                    dedup_k = f"{quest_id}::{is_done}"
                    if dedup_k not in seen_quest_clean:
                        seen_quest_clean.add(dedup_k)
                        all_quests.append(item_obj)
                else:
                    dedup_k = f"{quest_id}::{is_done}"
                    if dedup_k not in seen_quest_clean:
                        seen_quest_clean.add(dedup_k)
                        all_quests.append(item_obj)

    if ledger_changed and VAULT_DIR.exists():
        rpg_data["ledger"] = ledger
        rpg_data["log"] = (rpg_data.get("log") or [])[:80]
        save_json(RPG_DATA_FILE, rpg_data)

    # Fallback para missões genéricas de demonstração caso o cofre esteja vazio ou não configurado
    if not daily_quests and not all_quests:
        daily_quests = json.loads(json.dumps(DEMO_DAILY_QUESTS))
        all_quests = json.loads(json.dumps(DEMO_QUESTS))
        weekly_quests = [q for q in all_quests if q["type"] == "weekly"]

    entries = list(ledger.values())
    total_xp = int(rpg_data.get("bonusXP") or 1450)
    bosses = 2
    attr_xp = {"INT": 780, "TEC": 920, "REF": 450, "COOL": 410, "CORPO": 400}
    per_day = {}

    for e in entries:
        xp_v = int(e.get("xp") or 0)
        total_xp += xp_v
        at = e.get("attr") or "REF"
        if at in attr_xp:
            attr_xp[at] += xp_v
        if e.get("type") == "boss":
            bosses += 1
        d_str = e.get("date")
        if d_str:
            per_day[d_str] = per_day.get(d_str, 0) + 1

    lv_info = level_from_xp(total_xp)
    t_idx = tier_index(lv_info["level"])
    cur_tier = TIERS[t_idx]
    next_tier = TIERS[t_idx + 1] if t_idx + 1 < len(TIERS) else None

    streak = 7 if not per_day else 0
    if per_day:
        probe = datetime.now().date()
        if per_day.get(probe.strftime("%Y-%m-%d"), 0) == 0:
            probe = probe - timedelta(days=1)
        while per_day.get(probe.strftime("%Y-%m-%d"), 0) > 0:
            streak += 1
            probe = probe - timedelta(days=1)

    attrs_computed = {}
    for k, meta in ATTRS.items():
        xp_k = attr_xp.get(k, 0)
        lvl_k = min(20, 1 + int(math.floor(math.sqrt(xp_k / 25.0))))
        attrs_computed[k] = {
            "key": k,
            "name": meta["name"],
            "icon": meta["icon"],
            "color": meta["color"],
            "desc": meta["desc"],
            "xp": xp_k,
            "level": lvl_k,
            "pct": round((lvl_k / 20.0) * 100),
        }

    all_quests.sort(key=lambda q: (1 if q["completed"] else 0, TYPES[q["type"]]["order"], -q["xp"]))

    historico_cache = load_json(HISTORICO_CACHE_FILE, DEMO_ACADEMIC)
    classroom_cache = load_json(CLASSROOM_CACHE_FILE, {})
    acad_sync_settings = load_json(ACAD_DATA_FILE, {})

    classroom_payload = DEMO_CLASSROOM
    if classroom_cache.get("courses") or classroom_cache.get("courseWork"):
        classroom_payload = {
            "coursesCount": len(classroom_cache.get("courses") or []),
            "pendingWork": [w for w in (classroom_cache.get("courseWork") or []) if not w.get("isTurnedIn")][:15],
            "completedWork": [w for w in (classroom_cache.get("courseWork") or []) if w.get("isTurnedIn")][:10],
            "announcements": (classroom_cache.get("announcements") or [])[:8],
        }

    return {
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "syncPluginSettings": acad_sync_settings,
        "player": {
            "name": rpg_data.get("playerName") or "Netrunner V",
            "course": "Engenharia de Computação",
            "matricula": "",
            "ira": "9,0",
            "totalXP": total_xp,
            "level": lv_info["level"],
            "curXP": lv_info["cur"],
            "nextXP": lv_info["next"],
            "xpPct": min(100, round((lv_info["cur"] / max(1, lv_info["next"])) * 100)),
            "tier": cur_tier,
            "nextTier": next_tier,
            "tiers": TIERS,
            "tierIdx": t_idx,
            "tasksCompleted": max(38, len(entries)),
            "bossesDefeated": bosses,
            "streak": streak,
            "todayCount": per_day.get(today, 1),
            "attrs": attrs_computed,
            "log": (rpg_data.get("log") or [])[:25],
        },
        "notifications": notif_cfg,
        "lastMobileDailyReset": today,
        "lastMobileWeeklyReset": week_str,
        "dailyQuests": daily_quests,
        "weeklyQuests": weekly_quests,
        "quests": all_quests,
        "academic": historico_cache,
        "classroom": classroom_payload,
        "projects": DEMO_PROJECTS,
    }


def toggle_quest_across_vault(clean_target: str, file_path: str, line_idx: int, desired_done: bool):
    if not VAULT_DIR.exists():
        return
    target_norm = clean_target.strip().lower()
    for md_file in VAULT_DIR.rglob("*.md"):
        rel = md_file.relative_to(VAULT_DIR).as_posix()
        if rel.startswith(".obsidian/"):
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        lines = content.split("\n")
        modified = False
        for i, ln in enumerate(lines):
            stripped = re.sub(r"^[\s>]*", "", ln.rstrip("\r"))
            m = re.match(r"^([-*+]\s+\[)(.)(\]\s+)(.+)$", stripped)
            if not m:
                continue
            cln = clean_text(m.group(4)).lower()
            if (rel == file_path and i == line_idx) or (target_norm and cln == target_norm):
                new_box = "[x]" if desired_done else "[ ]"
                lines[i] = re.sub(r"\[[ xX]\]", new_box, ln, count=1)
                modified = True
        if modified:
            md_file.write_text("\n".join(lines), encoding="utf-8")


def insert_quest_into_note(rel_path: str, formatted_task: str, qtype: str):
    md_file = VAULT_DIR / rel_path
    if not md_file.exists():
        return
    content = md_file.read_text(encoding="utf-8")
    lines = content.split("\n")

    if qtype == "daily":
        pat = re.compile(r"\[!postit-verde\].*Daily|Daily Quests", re.I)
    elif qtype == "weekly":
        pat = re.compile(r"\[!postit-(roxo|laranja)\].*(Weekly|Semanal|Contratos da Semana)|Weekly Quests|Cronograma Semanal", re.I)
    elif qtype == "boss":
        pat = re.compile(r"\[!postit-rosa\].*(Boss|Alerta|Entregas)|Boss Fights", re.I)
    elif qtype == "main":
        pat = re.compile(r"\[!postit-(amarelo|rosa|azul)\].*(Main Quests|Entregas|Deck Netrunner|Trabalhos)|### 🔥 Main Quests", re.I)
    else:
        pat = re.compile(r"\[!postit-azul\].*(Side Quests|Deck Netrunner)|### 🧭 Side Quests", re.I)

    header_idx = next((idx for idx, l in enumerate(lines) if pat.search(l)), -1)
    if header_idx == -1:
        header_idx = next((idx for idx, l in enumerate(lines) if "[!postit-" in l or l.startswith("### ")), -1)

    if header_idx != -1:
        is_callout = lines[header_idx].lstrip().startswith(">")
        prefix = "> > - [ ] " if is_callout else "- [ ] "
        insert_at = header_idx + 1
        for i in range(header_idx + 1, len(lines)):
            ln = lines[i]
            if is_callout:
                if not ln.lstrip().startswith(">") or re.match(r"^>\s*>\s*\[!postit-", ln) or re.match(r"^>\s*$", ln.strip()):
                    break
                if re.match(r"^>\s*>\s*[-*+]\s+\[.\]", ln):
                    insert_at = i + 1
            else:
                if ln.startswith("##") or ln.startswith("---"):
                    break
                if re.match(r"^[-*+]\s+\[.\]", ln.strip()):
                    insert_at = i + 1
        lines.insert(insert_at, f"{prefix}{formatted_task}")
    else:
        lines.append(f"- [ ] {formatted_task}")

    md_file.write_text("\n".join(lines), encoding="utf-8")


def create_quest(title: str, due: str, qtype: str, attr: str, dest: str, popup_enabled: bool = True):
    due_part = f" *(Prazo: {due.strip()})*" if due and due.strip() else ""
    formatted = f"{title.strip()}{due_part} #{qtype} #{attr.lower()}"

    targets = ["00 - Início/🎮 Central de Quests.md", "00 - Início/🏠 Página Inicial.md"]
    if dest == "quests":
        targets = ["00 - Início/🎮 Central de Quests.md"]
    elif dest == "home":
        targets = ["00 - Início/🏠 Página Inicial.md"]
    elif dest == "semanal":
        targets = ["02 - Rotina & Diário/📅 Planejamento Semanal.md"]

    for t in targets:
        insert_quest_into_note(t, formatted, qtype)

    quest_id = re.sub(r"[^a-z0-9]+", "_", clean_text(formatted).lower()).strip("_")[:64]
    notif_cfg = get_notif_settings()
    if not popup_enabled:
        notif_cfg["disabledQuestKeys"][quest_id] = True
    else:
        notif_cfg["disabledQuestKeys"].pop(quest_id, None)
    save_json(NOTIF_SETTINGS_FILE, notif_cfg)


def update_quest_line(rel_path: str, line_idx: int, old_clean: str, title: str, due: str, qtype: str, attr: str):
    if not VAULT_DIR.exists():
        return
    due_part = f" *(Prazo: {due.strip()})*" if due and due.strip() else ""
    new_task = f"{title.strip()}{due_part} #{qtype} #{attr.lower()}"
    old_norm = (old_clean or "").strip().lower()

    for md_file in VAULT_DIR.rglob("*.md"):
        rel = md_file.relative_to(VAULT_DIR).as_posix()
        if rel.startswith(".obsidian/"):
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        lines = content.split("\n")
        changed = False
        for i, ln in enumerate(lines):
            m = re.match(r"^([\s>]*[-*+]\s+\[.\]\s+)(.+)$", ln.rstrip("\r"))
            if not m:
                continue
            cln = clean_text(m.group(2)).lower()
            if (rel == rel_path and i == line_idx) or (old_norm and cln == old_norm):
                lines[i] = f"{m.group(1)}{new_task}"
                changed = True
        if changed:
            md_file.write_text("\n".join(lines), encoding="utf-8")


def delete_quest_line(rel_path: str, line_idx: int, old_clean: str):
    if not VAULT_DIR.exists():
        return
    old_norm = (old_clean or "").strip().lower()
    for md_file in VAULT_DIR.rglob("*.md"):
        rel = md_file.relative_to(VAULT_DIR).as_posix()
        if rel.startswith(".obsidian/"):
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        lines = content.split("\n")
        new_lines = []
        changed = False
        for i, ln in enumerate(lines):
            m = re.match(r"^([\s>]*[-*+]\s+\[.\]\s+)(.+)$", ln.rstrip("\r"))
            if m:
                cln = clean_text(m.group(2)).lower()
                if (rel == rel_path and i == line_idx) or (old_norm and cln == old_norm):
                    changed = True
                    continue
            new_lines.append(ln)
        if changed:
            md_file.write_text("\n".join(new_lines), encoding="utf-8")


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class NightCityMobileHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_json(self, payload: dict, status: int = 200):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_file(self, file_path: Path, content_type: str):
        if not file_path.exists():
            self.send_error(404, "File not found")
            return
        raw = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        p = parsed.path

        if p in ("/", "/index.html"):
            return self._send_file(MOBILE_DIR / "www" / "index.html", "text/html; charset=utf-8")
        if p == "/manifest.json":
            return self._send_file(MOBILE_DIR / "www" / "manifest.json", "application/manifest+json; charset=utf-8")
        if p == "/sw.js":
            return self._send_file(MOBILE_DIR / "www" / "sw.js", "application/javascript; charset=utf-8")
        if p == "/icon.svg":
            return self._send_file(MOBILE_DIR / "www" / "icon.svg", "image/svg+xml")
        if p == "/api/state":
            state = scan_vault_and_compute_state()
            state["serverInfo"] = {"ip": get_local_ip(), "port": PORT}
            return self._send_json(state)

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        p = parsed.path
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}

        if p == "/api/quest/toggle":
            toggle_quest_across_vault(
                body.get("clean", ""),
                body.get("file", ""),
                int(body.get("line", -1)),
                bool(body.get("completed", True)),
            )
            return self._send_json({"ok": True, "state": scan_vault_and_compute_state()})

        if p == "/api/quest/create":
            create_quest(
                body.get("title", ""),
                body.get("due", ""),
                body.get("type", "side"),
                body.get("attr", "INT"),
                body.get("dest", "both"),
                bool(body.get("popupEnabled", True)),
            )
            return self._send_json({"ok": True, "state": scan_vault_and_compute_state()})

        if p == "/api/quest/update":
            update_quest_line(
                body.get("file", ""),
                int(body.get("line", -1)),
                body.get("oldClean", ""),
                body.get("title", ""),
                body.get("due", ""),
                body.get("type", "side"),
                body.get("attr", "INT"),
            )
            return self._send_json({"ok": True, "state": scan_vault_and_compute_state()})

        if p == "/api/quest/delete":
            delete_quest_line(
                body.get("file", ""),
                int(body.get("line", -1)),
                body.get("oldClean", ""),
            )
            return self._send_json({"ok": True, "state": scan_vault_and_compute_state()})

        if p == "/api/notifications/settings":
            cfg = get_notif_settings()
            if "masterEnabled" in body:
                cfg["masterEnabled"] = bool(body["masterEnabled"])
            if "inAppPopupBanner" in body:
                cfg["inAppPopupBanner"] = bool(body["inAppPopupBanner"])
            if "persistentHudNotification" in body:
                cfg["persistentHudNotification"] = bool(body["persistentHudNotification"])
            if "soundEffects" in body:
                cfg["soundEffects"] = bool(body["soundEffects"])
            if "bossAlertEnabled" in body:
                cfg["bossAlertEnabled"] = bool(body["bossAlertEnabled"])
            if "reminderTimes" in body and isinstance(body["reminderTimes"], list):
                cfg["reminderTimes"] = [str(x).strip() for x in body["reminderTimes"] if str(x).strip()]
            if "questId" in body and "questPopupEnabled" in body:
                qid = str(body["questId"])
                if bool(body["questPopupEnabled"]):
                    cfg["disabledQuestKeys"].pop(qid, None)
                else:
                    cfg["disabledQuestKeys"][qid] = True
            save_json(NOTIF_SETTINGS_FILE, cfg)
            return self._send_json({"ok": True, "state": scan_vault_and_compute_state()})

        if p == "/api/sync/suap":
            if SYNC_SCRIPT_FILE.exists():
                try:
                    subprocess.run([sys.executable, str(SYNC_SCRIPT_FILE)], cwd=str(VAULT_DIR), timeout=60, check=False)
                except Exception as e:
                    return self._send_json({"ok": False, "error": str(e)}, status=500)
            return self._send_json({"ok": True, "state": scan_vault_and_compute_state()})

        if p == "/api/sync/merge":
            actions = body.get("pendingActions") or []
            for act in actions:
                kind = act.get("kind")
                if kind == "toggle":
                    toggle_quest_across_vault(
                        act.get("clean", ""),
                        act.get("file", ""),
                        int(act.get("line", -1)),
                        bool(act.get("completed", True)),
                    )
                elif kind == "create":
                    create_quest(
                        act.get("title", ""),
                        act.get("due", ""),
                        act.get("type", "side"),
                        act.get("attr", "INT"),
                        act.get("dest", "both"),
                        bool(act.get("popupEnabled", True)),
                    )
                elif kind == "update":
                    update_quest_line(
                        act.get("file", ""),
                        int(act.get("line", -1)),
                        act.get("oldClean", ""),
                        act.get("title", ""),
                        act.get("due", ""),
                        act.get("type", "side"),
                        act.get("attr", "INT"),
                    )
                elif kind == "delete":
                    delete_quest_line(
                        act.get("file", ""),
                        int(act.get("line", -1)),
                        act.get("oldClean", ""),
                    )

            for q in (body.get("dailyQuests") or []) + (body.get("quests") or []):
                if q.get("touchedOffline"):
                    toggle_quest_across_vault(
                        q.get("clean", ""),
                        q.get("file", ""),
                        int(q.get("line", -1)),
                        bool(q.get("completed", False)),
                    )

            if isinstance(body.get("notifications"), dict):
                cfg = get_notif_settings()
                cfg.update(body["notifications"])
                save_json(NOTIF_SETTINGS_FILE, cfg)

            return self._send_json({"ok": True, "mergedCount": len(actions), "state": scan_vault_and_compute_state()})

        self.send_error(404, "Endpoint not found")


if __name__ == "__main__":
    ip = get_local_ip()
    print("=" * 68)
    print(" ⚡ NIGHT CITY RPG MOBILE — SERVIDOR ANDROID & OBSIDIAN ATIVO ⚡")
    print("=" * 68)
    print(f" 📱 Acesse no Android (mesmo Wi-Fi): http://{ip}:{PORT}")
    print(f" 💻 Acesse no PC:                    http://localhost:{PORT}")
    print("=" * 68)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), NightCityMobileHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
