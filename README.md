# 🌃 Night City RPG — Sistema Gamificado de Gestão Acadêmica e P&D (Obsidian Plugin + App Mobile & Sync Server)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/Obsidian%20Plugin-ES6%2B-7C3AED?logo=obsidian&logoColor=white)
![Android](https://img.shields.io/badge/Mobile-Android%20%26%20PWA-3DDC84?logo=android&logoColor=white)
![React Native](https://img.shields.io/badge/Expo-React%20Native-000020?logo=expo&logoColor=white)

---

## 📌 Visão Geral

O **Night City RPG** é um ecossistema completo de **gamificação de produtividade acadêmica, estudos e projetos de Pesquisa & Desenvolvimento (P&D)** inspirado em elementos de RPG (*Cyberpunk 2077, The Witcher 3, Dark Souls, Halo, Mass Effect*).

O sistema integra diretamente o cofre de conhecimento no **Obsidian** (Desktop) a um **Servidor de Sincronização em Tempo Real** em Python e um **Aplicativo Mobile (Android APK Standalone / PWA / Expo)**, transformando disciplinas universitárias, entregas de laboratório, leituras científicas e metas diárias em **Quests**, **Boss Fights**, **Atributos** e **Conquistas**.

---

## ✨ Principais Recursos e Mecânicas

### 🎮 1. Motor de RPG e Progressão (`obsidian-plugin/` & `server.py`)
- **Sistema de Classes e Tiers (Níveis 1 a 100+):** Evolução automática a cada 10 níveis (*Street Kid* → *Netrunner Aprendiz* → *Hacker da DedSec* → *Bruxo da Escola do Lobo* → *Spartan-II* → *Comandante N7* → *Lenda de Night City*).
- **5 Atributos estilo Cyberpunk 2077:**
  - 🧠 **INT (Inteligência):** Estudos, IA, Física Nuclear, provas e leituras científicas.
  - 🛠️ **TEC (Técnica):** Desenvolvimento de código Python/JS, arquitetura de software e modelagem UML.
  - ⚡ **REF (Reflexos):** Entregas rápidas e resolução ágil de pendências.
  - 😎 **COOL (Sangue-Frio):** Gestão de projetos, planejamento semanal e organização.
  - 💪 **CORPO (Corpo):** Saúde, treino físico, hidratação e rotina.
- **Hierarquia de Missões (Quests):**
  - `☠️ BOSS (+150 XP)` — Provas, defesas de projetos e entregas críticas.
  - `⚔️ MAIN (+50 XP)` — Metas principais de pesquisa e trabalhos acadêmicos.
  - `🧭 SIDE (+30 XP)` — Tarefas complementares e experimentos técnicos.
  - `📅 WEEKLY (+25 XP)` & `🔁 DAILY (+10 XP)` — Hábitos recorrentes com reset automático e contagem de *Streak*.
- **Sistema de Conquistas (*Achievements*):** Mais de 25 conquistas desbloqueáveis por streaks, combos diários, chefes derrotados e níveis de atributo.

### 📱 2. Aplicativo Mobile & Sincronização Bidirecional
- **Servidor HTTP Multithread (`server.py`):** Sincroniza em tempo real as notas Markdown do Obsidian, o progresso do jogador, dados acadêmicos (SUAP / Google Classroom) e projetos de P&D.
- **Interface Mobile HUD (`www/index.html` & `expo-android-app/`):**
  - Painel de status do personagem, barra de XP, streak e atributos.
  - Marcação/desmarcação instantânea de Quests sincronizada direto nos arquivos `.md` do cofre.
  - Sistema configurável de notificações e alertas de *Boss Fight* e *Daily Quests* (geral e individual por tarefa).
- **Builder de APK Standalone (`build_standalone_apk.py`):** Pipeline automatizado em Python para empacotamento e assinatura de APK Android nativo sem necessidade de Android Studio completo.

---

## 🏗️ Arquitetura do Repositório

```text
├── obsidian-plugin/                # Plugin nativo para Obsidian Desktop/Mobile
│   ├── main.js                     # Lógica de parsing Markdown, cálculo de XP, modais e HUD
│   ├── manifest.json               # Metadados do plugin Obsidian
│   └── styles.css                  # Estilização Cyberpunk / Neon UI para o Obsidian
├── server.py                       # Servidor HTTP REST em Python para sincronização bidirecional
├── build_standalone_apk.py         # Gerador e empacotador automatizado do APK Android Standalone
├── www/                            # Aplicação Web Progressiva (PWA) / Frontend Mobile HUD
│   ├── index.html                  # Interface responsiva completa do Night City RPG Mobile
│   ├── manifest.json               # Web App Manifest
│   └── sw.js                       # Service Worker para suporte offline e cache
├── expo-android-app/               # Wrapper React Native / Expo para Android
│   ├── App.js                      # WebView bridge, notificações nativas e sincronização
│   ├── app.json                    # Configurações do projeto Expo
│   └── package.json                # Dependências Node/Expo
├── smali_src/                      # Código Smali para compilação do WebView Android nativo
├── Iniciar_Servidor_Mobile.bat     # Script de inicialização rápida do servidor local
└── Atualizar_APK_Standalone.bat    # Script de build rápido do APK
```

---

## 🚀 Como Executar

### 1. Instalar o Plugin no Obsidian
1. Copie a pasta `obsidian-plugin/` para dentro do seu cofre em `.obsidian/plugins/night-city-rpg/`.
2. Ative o plugin **Night City RPG — Gamificação** nas configurações de plugins da comunidade do Obsidian.

### 2. Iniciar o Servidor de Sincronização Mobile
Requer apenas **Python 3.10+** (utiliza biblioteca padrão `http.server`, `json`, `pathlib`):

```bash
python server.py
```

O servidor iniciará na porta `8077` (`http://localhost:8077` ou via IP da rede local para acesso no smartphone).

### 3. Gerar o APK Android (Opcional)
```bash
python build_standalone_apk.py
```

---

## 👤 Autor

Desenvolvido por **[@totemicpuma](https://github.com/totemicpuma)**
