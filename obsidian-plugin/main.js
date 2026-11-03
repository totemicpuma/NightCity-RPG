const { Plugin, Notice, Modal, PluginSettingTab, Setting, TFile, TFolder, MarkdownRenderChild } = require("obsidian");

/* =========================================================================
   NIGHT CITY RPG — Gamificação de tarefas e aprendizado para o Obsidian
   - Toda tarefa marcada como concluída (- [x]) em qualquer nota gera XP
   - A cada 10 níveis você evolui de classe (referências de games)
   - Atributos estilo Cyberpunk 2077 (INT, TEC, REF, COOL, CORPO)
   - Conquistas, streaks, boss fights (provas) e daily quests
   ========================================================================= */

const TIERS = [
  { min: 1, name: "Street Kid", rank: "Iniciante", game: "Cyberpunk 2077", icon: "🛹", color: "#f3e600", quote: "Todo mundo começa nas ruas de Night City." },
  { min: 10, name: "Netrunner Aprendiz", rank: "Aprendiz", game: "Cyberpunk 2077", icon: "💾", color: "#00f0ff", quote: "Jack in. A Rede é sua nova sala de aula." },
  { min: 20, name: "Hacker da DedSec", rank: "Intermediário", game: "Watch Dogs", icon: "📱", color: "#39ff14", quote: "Todo sistema pode ser entendido... e hackeado." },
  { min: 30, name: "Bruxo da Escola do Lobo", rank: "Avançado", game: "The Witcher 3", icon: "🐺", color: "#cfd8dc", quote: "Monstros, contratos e provas: tudo tem um ponto fraco." },
  { min: 40, name: "Cavaleiro de Hallownest", rank: "Veterano", game: "Hollow Knight", icon: "🗡️", color: "#8ab4ff", quote: "Nenhum boss é impossível com paciência e prática." },
  { min: 50, name: "Spartan-II", rank: "Elite", game: "Halo", icon: "🪖", color: "#7cb342", quote: "Termine o que começou, Master Chief." },
  { min: 60, name: "Dragonborn", rank: "Mestre", game: "The Elder Scrolls V: Skyrim", icon: "🐉", color: "#ff8c00", quote: "FUS RO DAH nas pendências!" },
  { min: 70, name: "Comandante N7", rank: "Grão-Mestre", game: "Mass Effect", icon: "🚀", color: "#ff3b3b", quote: "Eu sou o Comandante Shepard, e esta é minha tarefa favorita." },
  { min: 80, name: "Augmentado", rank: "Lendário", game: "Deus Ex", icon: "🦾", color: "#ffb000", quote: "Eu nunca pedi por isso... mas aceitei o desafio." },
  { min: 90, name: "Lenda de Night City", rank: "Mítico", game: "Cyberpunk 2077", icon: "🌃", color: "#ff003c", quote: "Seu nome já é falado no Afterlife." },
  { min: 100, name: "Rockerboy Imortal", rank: "Ascendido", game: "Cyberpunk 2077 — Johnny Silverhand", icon: "🎸", color: "#ff00ff", quote: "Wake up, Samurai. Temos uma cidade para queimar." }
];

const ATTRS = {
  INT: { name: "Inteligência", icon: "🧠", color: "#00f0ff", desc: "Estudos, aulas, provas e leituras" },
  TEC: { name: "Técnica", icon: "🛠️", color: "#f3e600", desc: "Código, projetos, diagramas e sistemas" },
  REF: { name: "Reflexos", icon: "⚡", color: "#ff003c", desc: "Entregas rápidas e tarefas gerais" },
  COOL: { name: "Sangue-Frio", icon: "😎", color: "#b388ff", desc: "Rotina, organização e planejamento" },
  CORPO: { name: "Corpo", icon: "💪", color: "#39ff14", desc: "Saúde, treino e bem-estar" }
};

const TYPES = {
  boss: { label: "BOSS", icon: "☠️", order: 0, xp: 150 },
  main: { label: "MAIN", icon: "⚔️", order: 1, xp: 50 },
  side: { label: "SIDE", icon: "🧭", order: 2, xp: 30 },
  weekly: { label: "WEEKLY", icon: "📅", order: 3, xp: 25 },
  daily: { label: "DAILY", icon: "🔁", order: 4, xp: 10 },
  comum: { label: "GIG", icon: "📌", order: 5, xp: 15 }
};

const BASE_ACHIEVEMENTS = [
  { id: "first", icon: "🩸", name: "Primeiro Sangue", desc: "Complete sua primeira tarefa", xp: 25, check: (s) => s.tasks >= 1 },
  { id: "t10", icon: "🤝", name: "Choom Confiável", desc: "Complete 10 tarefas", xp: 50, check: (s) => s.tasks >= 10 },
  { id: "t50", icon: "🔫", name: "Mercenário Profissional", desc: "Complete 50 tarefas", xp: 100, check: (s) => s.tasks >= 50 },
  { id: "t100", icon: "🕴️", name: "Fixer Lendário", desc: "Complete 100 tarefas", xp: 200, check: (s) => s.tasks >= 100 },
  { id: "t250", icon: "🏙️", name: "Dono de Night City", desc: "Complete 250 tarefas", xp: 400, check: (s) => s.tasks >= 250 },
  { id: "boss1", icon: "☠️", name: "Matador de Chefes", desc: "Derrote seu primeiro Boss (prova)", xp: 50, check: (s) => s.bosses >= 1 },
  { id: "boss5", icon: "🔥", name: "Prepare to Die", desc: "Derrote 5 Bosses — Dark Souls", xp: 150, check: (s) => s.bosses >= 5 },
  { id: "boss15", icon: "👑", name: "Lorde das Cinzas", desc: "Derrote 15 Bosses — Dark Souls III", xp: 300, check: (s) => s.bosses >= 15 },
  { id: "streak3", icon: "🔥", name: "Em Chamas", desc: "3 dias seguidos completando tarefas", xp: 50, check: (s) => s.bestStreak >= 3 },
  { id: "streak7", icon: "📅", name: "Semana Perfeita", desc: "7 dias seguidos completando tarefas", xp: 120, check: (s) => s.bestStreak >= 7 },
  { id: "streak30", icon: "🧬", name: "Implante de Disciplina", desc: "30 dias seguidos completando tarefas", xp: 500, check: (s) => s.bestStreak >= 30 },
  { id: "combo5", icon: "💥", name: "Combo x5", desc: "Complete 5 tarefas no mesmo dia", xp: 40, check: (s) => s.bestDay >= 5 },
  { id: "combo15", icon: "🌪️", name: "Sandevistan", desc: "Complete 15 tarefas no mesmo dia — Cyberpunk 2077", xp: 120, check: (s) => s.bestDay >= 15 },
  { id: "owl", icon: "🦉", name: "Coruja de Night City", desc: "Complete uma tarefa entre 0h e 5h", xp: 30, check: (s) => s.nightOwl },
  { id: "int10", icon: "🧠", name: "Cérebro Overclockado", desc: "Inteligência no nível 10", xp: 150, check: (s) => s.attrs.INT.level >= 10 },
  { id: "tec10", icon: "🛠️", name: "Techie de Elite", desc: "Técnica no nível 10", xp: 150, check: (s) => s.attrs.TEC.level >= 10 },
  { id: "cool10", icon: "😎", name: "Gelo nas Veias", desc: "Sangue-Frio no nível 10", xp: 150, check: (s) => s.attrs.COOL.level >= 10 },
  { id: "corpo10", icon: "💪", name: "Cromado até os Ossos", desc: "Corpo no nível 10", xp: 150, check: (s) => s.attrs.CORPO.level >= 10 }
];

const ACHIEVEMENTS = BASE_ACHIEVEMENTS.concat(
  TIERS.slice(1).map((t, i) => ({
    id: `tier${i + 2}`,
    icon: t.icon,
    name: `Evolução: ${t.name}`,
    desc: `Alcance o nível ${t.min} (${t.game})`,
    xp: 100,
    check: (s) => s.level >= t.min
  }))
);

const DEFAULTS = {
  playerName: "Netrunner V",
  baseXP: 15,
  revokeOnUncheck: true,
  ignoreFolders: ["99 - Templates", "Excalidraw"],
  questBoardExclude: ["00 - Início/🏠 Página Inicial.md"],
  questBoardLimit: 30,
  questsNotePath: "00 - Início/🎮 Central de Quests.md",
  ledger: {},
  bonusXP: 0,
  achievements: {},
  log: [],
  lastLevel: null,
  lastDailyReset: "",
  lastWeeklyReset: "",
  initialized: false
};

// Notas geradas automaticamente pelo sincronizador SUAP/Classroom: nunca removem XP
const GENERATED_RE = /Sincronizado automaticamente|Sincronizado com SUAP|Última sincronização automática/i;

// ---------------------------------------------------------------------------
// Utilitários
// ---------------------------------------------------------------------------
function pad(n) {
  return String(n).padStart(2, "0");
}

function todayStr(d = new Date()) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function weekStr(d = new Date()) {
  const dt = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const day = dt.getDay(); // 0 = Dom, 1 = Seg, ...
  const diff = (day === 0 ? -6 : 1) - day;
  dt.setDate(dt.getDate() + diff);
  return todayStr(dt);
}

function parseDay(s) {
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function shiftDay(s, delta) {
  const d = parseDay(s);
  d.setDate(d.getDate() + delta);
  return todayStr(d);
}

function dayDiff(a, b) {
  return Math.round((parseDay(b) - parseDay(a)) / 86400000);
}

function xpToNext(level) {
  return 80 + (level - 1) * 15;
}

function levelFromXP(xp) {
  let level = 1;
  let rem = Math.max(0, xp);
  while (rem >= xpToNext(level) && level < 999) {
    rem -= xpToNext(level);
    level++;
  }
  return { level, cur: rem, next: xpToNext(level) };
}

function tierIndex(level) {
  let idx = 0;
  TIERS.forEach((t, i) => {
    if (level >= t.min) idx = i;
  });
  return idx;
}

function cleanText(t) {
  return t
    .replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, "$2")
    .replace(/\[\[([^\]]+)\]\]/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[*_`]/g, "")
    .replace(/#(xp\/\d+|boss|main|epica|side|weekly|semanal|daily|int|ref|tec|corpo|cool)\b/gi, "")
    .replace(/\s+/g, " ")
    .trim();
}

function formatTime(ts) {
  const d = new Date(ts);
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ---------------------------------------------------------------------------
// Modal de evolução de classe
// ---------------------------------------------------------------------------
class EvolutionModal extends Modal {
  constructor(app, tier, level) {
    super(app);
    this.tier = tier;
    this.level = level;
  }

  onOpen() {
    const { contentEl, modalEl } = this;
    modalEl.addClass("rpg-evolution-modal");
    modalEl.style.setProperty("--tier-color", this.tier.color);
    contentEl.createDiv({ cls: "rpg-evo-glitch", text: "// EVOLUÇÃO DE CLASSE DESBLOQUEADA" });
    contentEl.createDiv({ cls: "rpg-evo-icon", text: this.tier.icon });
    contentEl.createEl("h2", { cls: "rpg-evo-title", text: this.tier.name });
    contentEl.createDiv({ cls: "rpg-evo-sub", text: `${this.tier.rank} · ${this.tier.game} · Nível ${this.level}` });
    contentEl.createDiv({ cls: "rpg-evo-quote", text: `“${this.tier.quote}”` });
    const btn = contentEl.createEl("button", { cls: "mod-cta rpg-evo-btn", text: "Continuar a jornada ⚡" });
    btn.onclick = () => this.close();
  }

  onClose() {
    this.contentEl.empty();
  }
}

// ---------------------------------------------------------------------------
// Modal de Criação / Edição Rápida de Quest
// ---------------------------------------------------------------------------
const QUEST_DESTINATIONS = [
  { id: "both", label: "🏠 Página Inicial + 🎮 Central de Quests (Recomendado)" },
  { id: "quests", label: "🎮 Central de Quests (00 - Início/🎮 Central de Quests.md)" },
  { id: "home", label: "🏠 Apenas Página Inicial (00 - Início/🏠 Página Inicial.md)" },
  { id: "semanal", label: "📅 Planejamento Semanal (02 - Rotina & Diário/📅 Planejamento Semanal.md)" },
  { id: "rna", label: "☢️ Projeto 01: RNA Reator Nuclear PWR" },
  { id: "soma", label: "🌐 Projeto 02: Plataforma SOMA" },
  { id: "faculdade", label: "🎓 Trabalhos da Faculdade (IFF)" }
];

class QuestEditorModal extends Modal {
  constructor(app, plugin, existingQuest = null, onSaved = null) {
    super(app);
    this.plugin = plugin;
    this.existing = existingQuest; // { file, line, text, clean, type, attr }
    this.onSaved = onSaved;
  }

  onOpen() {
    const { contentEl, modalEl } = this;
    modalEl.addClass("rpg-quest-modal");
    contentEl.empty();

    const isEdit = Boolean(this.existing);
    contentEl.createDiv({
      cls: "rpg-evo-glitch",
      text: isEdit ? "// TERMINAL NCPD · EDITAR REGISTRO DE QUEST" : "// TERMINAL NCPD · NOVO CONTRATO / QUEST"
    });
    contentEl.createEl("h2", {
      cls: "rpg-modal-title",
      text: isEdit ? "✏️ Editar Quest / Tarefa" : "➕ Nova Quest / Trabalho"
    });

    let titleVal = isEdit ? this.existing.clean : "";
    let dueVal = "";
    if (isEdit) {
      const mDue = this.existing.text.match(/\*\((?:Prazo:\s*|Limite:\s*)?([^)]+)\)\*/i);
      if (mDue) {
        dueVal = mDue[1].trim();
        titleVal = titleVal.replace(mDue[0], "").replace(/\((?:Prazo:\s*|Limite:\s*)?[^)]+\)/, "").trim();
      }
    }
    let typeVal = isEdit && this.existing.type !== "comum" ? this.existing.type : "side";
    let attrVal = isEdit && this.existing.attr ? this.existing.attr : "INT";
    let destVal = "both";

    const form = contentEl.createDiv({ cls: "rpg-form" });

    // 1. Nome / Descrição
    const grpTitle = form.createDiv({ cls: "rpg-form-group" });
    grpTitle.createEl("label", { text: "📌 Descrição da Tarefa, Trabalho ou Prova:" });
    const inputTitle = grpTitle.createEl("input", {
      type: "text",
      cls: "rpg-input",
      placeholder: "Ex: Entregar relatório parcial da RNA C05 / Prova A1 de Banco de Dados..."
    });
    inputTitle.value = titleVal;
    setTimeout(() => inputTitle.focus(), 50);

    // 2. Prazo / Data opcional
    const grpDue = form.createDiv({ cls: "rpg-form-group" });
    grpDue.createEl("label", { text: "📅 Prazo ou Data (opcional):" });
    const inputDue = grpDue.createEl("input", {
      type: "text",
      cls: "rpg-input",
      placeholder: "Ex: 30/10/2026 ou Sexta-feira (deixe em branco se for rotina)"
    });
    inputDue.value = dueVal;

    // 3. Categoria / Dificuldade (XP)
    const grpType = form.createDiv({ cls: "rpg-form-group" });
    grpType.createEl("label", { text: "⚔️ Categoria da Quest (define o XP e o card):" });
    const selectType = grpType.createEl("select", { cls: "rpg-select" });
    [
      ["daily", "🔁 Daily Quest (+10 XP — Reseta todo dia à meia-noite)"],
      ["weekly", "📅 Weekly Quest (+25 XP — Reseta toda segunda-feira / Cronograma semanal)"],
      ["side", "🧭 Side Quest (+30 XP — Tarefa, Estudo, Exercício ou Código)"],
      ["main", "⚔️ Main Quest (+50 XP — Trabalho de Disciplina, Etapa RNA ou SOMA)"],
      ["boss", "☠️ Boss Fight (+150 XP — Prova A1/A2/PF ou Entrega Final)"]
    ].forEach(([val, label]) => {
      const opt = selectType.createEl("option", { value: val, text: label });
      if (val === typeVal) opt.selected = true;
    });
    selectType.onchange = () => {
      typeVal = selectType.value;
    };

    // 4. Atributo
    const grpAttr = form.createDiv({ cls: "rpg-form-group" });
    grpAttr.createEl("label", { text: "🧬 Atributo do Personagem que vai subir:" });
    const selectAttr = grpAttr.createEl("select", { cls: "rpg-select" });
    [
      ["INT", "🧠 INT — Inteligência (Estudos, IA, RNA Nuclear, Provas, Leitura)"],
      ["TEC", "🛠️ TEC — Técnica (Código Python, UML, Excalidraw, Sistemas)"],
      ["COOL", "😎 COOL — Sangue-Frio (Gestão de Projetos, SOMA, Organização)"],
      ["REF", "⚡ REF — Reflexos (Entregas Rápidas, Urgências)"],
      ["CORPO", "💪 CORPO — Corpo (Treino, Água, Saúde, Descanso)"]
    ].forEach(([val, label]) => {
      const opt = selectAttr.createEl("option", { value: val, text: label });
      if (val === attrVal) opt.selected = true;
    });
    selectAttr.onchange = () => {
      attrVal = selectAttr.value;
    };

    // 5. Destino (apenas ao criar nova quest)
    if (!isEdit) {
      const grpDest = form.createDiv({ cls: "rpg-form-group" });
      grpDest.createEl("label", { text: "📂 Onde salvar esta Quest:" });
      const selectDest = grpDest.createEl("select", { cls: "rpg-select" });
      QUEST_DESTINATIONS.forEach((d) => {
        const opt = selectDest.createEl("option", { value: d.id, text: d.label });
        if (d.id === destVal) opt.selected = true;
      });
      selectDest.onchange = () => {
        destVal = selectDest.value;
      };
    } else {
      const infoFile = form.createDiv({ cls: "rpg-form-hint" });
      infoFile.setText(`📄 Arquivo: ${this.existing.file} (Linha ${this.existing.line + 1})`);
    }

    const actions = contentEl.createDiv({ cls: "rpg-modal-actions" });
    const btnCancel = actions.createEl("button", { cls: "rpg-btn-secondary", text: "Cancelar" });
    btnCancel.onclick = () => this.close();

    const btnSave = actions.createEl("button", {
      cls: "mod-cta rpg-btn-primary",
      text: isEdit ? "💾 Salvar Alterações" : "⚡ Registrar Quest"
    });

    const submit = async () => {
      const cleanTitle = inputTitle.value.trim();
      if (!cleanTitle) {
        new Notice("⚠️ Digite a descrição da Quest!");
        inputTitle.focus();
        return;
      }
      const duePart = inputDue.value.trim() ? ` *(Prazo: ${inputDue.value.trim()})*` : "";
      const tagType = `#${typeVal}`;
      const tagAttr = `#${attrVal.toLowerCase()}`;
      const formattedTaskText = `${cleanTitle}${duePart} ${tagType} ${tagAttr}`;

      if (isEdit) {
        await this.plugin.updateQuestInFile(this.existing.file, this.existing.line, formattedTaskText);
        new Notice(`✅ Quest atualizada com sucesso!`);
      } else {
        await this.plugin.createNewQuest(formattedTaskText, typeVal, destVal);
        new Notice(`⚡ Nova Quest adicionada (+${TYPES[typeVal].xp} XP ao concluir)!`);
      }
      if (this.onSaved) this.onSaved();
      this.close();
    };

    btnSave.onclick = submit;
    inputTitle.addEventListener("keydown", (e) => {
      if (e.key === "Enter") submit();
    });
    inputDue.addEventListener("keydown", (e) => {
      if (e.key === "Enter") submit();
    });
  }

  onClose() {
    this.contentEl.empty();
  }
}

// ---------------------------------------------------------------------------
// Modal Gerenciador Geral de Quests (Concluir, Editar, Excluir, Filtrar)
// ---------------------------------------------------------------------------
class QuestManagerModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
    this.filterType = "all";
  }

  onOpen() {
    this.modalEl.addClass("rpg-quest-manager-modal");
    this.render();
  }

  render() {
    const { contentEl } = this;
    contentEl.empty();

    const header = contentEl.createDiv({ cls: "rpg-qm-header" });
    const titleWrap = header.createDiv();
    titleWrap.createDiv({ cls: "rpg-evo-glitch", text: "// GERENCIADOR TÁTICO DE MISSÕES" });
    titleWrap.createEl("h2", { cls: "rpg-modal-title", text: "📋 Adicionar, Editar ou Excluir Quests" });

    const btnAdd = header.createEl("button", { cls: "mod-cta rpg-btn-primary", text: "➕ Nova Quest / Trabalho" });
    btnAdd.onclick = () => {
      new QuestEditorModal(this.app, this.plugin, null, () => {
        setTimeout(() => this.render(), 300);
      }).open();
    };

    // Filtros rápidos
    const filters = contentEl.createDiv({ cls: "rpg-qm-filters" });
    [
      ["all", "🌐 Todas"],
      ["daily", "🔁 Daily (10 XP)"],
      ["weekly", "📅 Weekly (25 XP)"],
      ["main", "⚔️ Main (50 XP)"],
      ["side", "🧭 Side (30 XP)"],
      ["boss", "☠️ Boss (150 XP)"]
    ].forEach(([id, label]) => {
      const b = filters.createEl("button", {
        cls: "rpg-filter-btn" + (this.filterType === id ? " is-active" : ""),
        text: label
      });
      b.onclick = () => {
        this.filterType = id;
        this.render();
      };
    });

    const allQuests = [];
    for (const [path, list] of Object.entries(this.plugin.openTasks)) {
      for (const q of list) {
        if (this.filterType !== "all" && q.type !== this.filterType) continue;
        allQuests.push(q);
      }
    }
    allQuests.sort((a, b) => TYPES[a.type].order - TYPES[b.type].order || b.xp - a.xp);

    const listEl = contentEl.createDiv({ cls: "rpg-qm-list" });
    if (!allQuests.length) {
      listEl.createDiv({ cls: "rpg-empty", text: "Nenhuma quest encontrada neste filtro." });
      return;
    }

    for (const q of allQuests) {
      const row = listEl.createDiv({ cls: `rpg-quest rpg-type-${q.type} rpg-qm-row` });

      const btnDone = row.createEl("button", { cls: "rpg-quest-done", text: "✔" });
      btnDone.setAttr("title", "Concluir Quest e ganhar XP");
      btnDone.onclick = async () => {
        await this.plugin.completeQuestInFile(q.file, q.line);
        setTimeout(() => this.render(), 250);
      };

      row.createSpan({ cls: "rpg-quest-badge", text: `${TYPES[q.type].icon} ${TYPES[q.type].label}` });
      row.createSpan({ cls: "rpg-quest-text", text: q.clean });
      row.createSpan({ cls: "rpg-quest-xp", text: `+${q.xp} XP` });

      const noteShort = q.file.split("/").pop().replace(/\.md$/, "");
      const link = row.createEl("a", { cls: "rpg-quest-file", text: noteShort });
      link.onclick = (ev) => {
        ev.preventDefault();
        this.close();
        this.app.workspace.openLinkText(q.file, "", false);
      };

      const actWrap = row.createDiv({ cls: "rpg-quest-actions" });
      const btnEdit = actWrap.createEl("button", { cls: "rpg-quest-action-btn", text: "✏️" });
      btnEdit.setAttr("title", "Editar texto, prazo, tipo ou atributo");
      btnEdit.onclick = () => {
        new QuestEditorModal(this.app, this.plugin, q, () => {
          setTimeout(() => this.render(), 300);
        }).open();
      };

      const btnDel = actWrap.createEl("button", { cls: "rpg-quest-action-btn is-danger", text: "🗑️" });
      btnDel.setAttr("title", "Excluir esta quest da nota");
      btnDel.onclick = async () => {
        await this.plugin.deleteQuestInFile(q.file, q.line);
        new Notice("🗑️ Quest removida!");
        setTimeout(() => this.render(), 250);
      };
    }
  }

  onClose() {
    this.contentEl.empty();
  }
}

// ---------------------------------------------------------------------------
// Plugin principal
// ---------------------------------------------------------------------------
module.exports = class NightCityRPG extends Plugin {
  async onload() {
    const saved = (await this.loadData()) || {};
    this.data = Object.assign(JSON.parse(JSON.stringify(DEFAULTS)), saved);
    this.data.ledger = this.data.ledger || {};
    this.data.achievements = this.data.achievements || {};
    this.data.log = this.data.log || [];

    this.openTasks = {};
    this.views = new Set();
    this.timers = {};
    this.ready = false;

    this.statusEl = this.addStatusBarItem();
    this.statusEl.addClass("rpg-statusbar");
    this.statusEl.onClickEvent(() => this.openQuests());

    this.addRibbonIcon("swords", "Night City RPG — Central de Quests", () => this.openQuests());
    this.addRibbonIcon("plus-circle", "Night City RPG — Nova Quest / Trabalho", () => {
      new QuestEditorModal(this.app, this).open();
    });

    this.addCommand({ id: "open-quests", name: "Abrir Central de Quests", callback: () => this.openQuests() });
    this.addCommand({
      id: "new-quest",
      name: "➕ Criar Nova Quest / Trabalho / Tarefa",
      callback: () => new QuestEditorModal(this.app, this).open()
    });
    this.addCommand({
      id: "manage-quests",
      name: "📋 Gerenciar, Editar ou Excluir Quests",
      callback: () => new QuestManagerModal(this.app, this).open()
    });
    this.addCommand({
      id: "rescan",
      name: "Recalcular XP (varrer todas as notas)",
      callback: async () => {
        await this.fullScan("manual");
      }
    });

    this.registerMarkdownCodeBlockProcessor("rpg", (src, el, ctx) => this.mountView("hud", el, ctx));
    this.registerMarkdownCodeBlockProcessor("rpg-quests", (src, el, ctx) => this.mountView("quests", el, ctx));
    this.registerMarkdownCodeBlockProcessor("rpg-achievements", (src, el, ctx) => this.mountView("achievements", el, ctx));
    this.registerMarkdownCodeBlockProcessor("rpg-log", (src, el, ctx) => this.mountView("log", el, ctx));
    this.registerMarkdownCodeBlockProcessor("rpg-classes", (src, el, ctx) => this.mountView("classes", el, ctx));

    this.registerEvent(this.app.vault.on("modify", (f) => this.queueScan(f)));
    this.registerEvent(this.app.vault.on("create", (f) => this.queueScan(f)));
    this.registerEvent(
      this.app.vault.on("delete", (f) => {
        delete this.openTasks[f.path];
        this.refreshViews();
      })
    );
    this.registerEvent(this.app.vault.on("rename", (f, oldPath) => this.handleRename(f, oldPath)));

    this.addSettingTab(new RPGSettingTab(this.app, this));

    this.app.workspace.onLayoutReady(async () => {
      await this.dailyReset();
      await this.weeklyReset();
      await this.fullScan(this.data.initialized ? "startup" : "initial");
      this.ready = true;
    });

    this.registerInterval(
      window.setInterval(() => {
        this.dailyReset();
        this.weeklyReset();
      }, 10 * 60 * 1000)
    );
    this.updateStatusBar();
  }

  onunload() {
    Object.values(this.timers).forEach((t) => clearTimeout(t));
  }

  async save() {
    await this.saveData(this.data);
  }

  isIgnored(path) {
    return (this.data.ignoreFolders || []).some((f) => {
      const folder = (f || "").trim().replace(/\/$/, "");
      return folder && (path === folder || path.startsWith(folder + "/"));
    });
  }

  // -------------------------------------------------------------------------
  // Classificação da tarefa: tipo (boss/main/side/daily/gig), XP e atributo
  // -------------------------------------------------------------------------
  classify(text, path) {
    let type = "comum";
    if (/#boss\b/i.test(text)) type = "boss";
    else if (/#(main|epica)\b/i.test(text)) type = "main";
    else if (/#side\b/i.test(text)) type = "side";
    else if (/#(weekly|semanal)\b/i.test(text)) type = "weekly";
    else if (/#daily\b/i.test(text)) type = "daily";
    else if (/\b(prova|avalia[çc][ãa]o|exame)\b/i.test(text)) type = "boss";
    else if (/\b(trabalho|relat[óo]rio|projetos?|semin[áa]rio|entrega)\b/i.test(text)) type = "main";
    else if (/\b(atividades?|exerc[íi]cios?|lista|tarefa|resumo|estudar)\b/i.test(text)) type = "side";

    let xp = type === "comum" ? Number(this.data.baseXP) || 15 : TYPES[type].xp;
    const custom = text.match(/#xp\/(\d+)/i) || text.match(/\[xp::\s*(\d+)\]/i);
    if (custom) xp = parseInt(custom[1], 10);

    let attr = null;
    const tag = text.match(/#(int|ref|tec|corpo|cool)\b/i);
    if (tag) attr = tag[1].toUpperCase();
    else if (/c[óo]digo|code|program|\bpoo\b|software|compilador|banco de dados|python|java|diagrama|\buml\b|\bgit\b|\bapi\b|sistema|excalidraw|circuito/i.test(text)) attr = "TEC";
    else if (/prova|estud|aula|resumo|leitura|\bler\b|livro|exerc|lista|revis|disciplina|mat[ée]ria|cap[íi]tulo|\bcap\b/i.test(text)) attr = "INT";
    else if (/treino|academia|corrida|caminhada|sa[úu]de|dormir|[áa]gua|alonga|muscula/i.test(text)) attr = "CORPO";
    else if (/rotina|organiz|backup|limp|planej|meta|agenda|di[áa]ri|escopo|reuni/i.test(text)) attr = "COOL";
    else if (path.startsWith("03 - ")) attr = "INT";
    else if (path.startsWith("01 - ")) attr = "TEC";
    else if (path.startsWith("02 - ")) attr = "COOL";
    else attr = "REF";

    return { type, xp, attr };
  }

  // -------------------------------------------------------------------------
  // Varredura das notas
  // -------------------------------------------------------------------------
  queueScan(file) {
    if (!this.ready || !(file instanceof TFile) || file.extension !== "md") return;
    clearTimeout(this.timers[file.path]);
    this.timers[file.path] = setTimeout(async () => {
      delete this.timers[file.path];
      const result = { awarded: [], revoked: [] };
      await this.scanFile(file, result);
      if (result.awarded.length || result.revoked.length) await this.afterChange(result, false);
      else this.refreshViews();
    }, 700);
  }

  async fullScan(mode) {
    const result = { awarded: [], revoked: [] };
    for (const f of this.app.vault.getMarkdownFiles()) {
      await this.scanFile(f, result);
    }
    const gained = result.awarded.reduce((a, e) => a + e.xp, 0);

    if (mode === "initial") {
      this.data.initialized = true;
      new Notice(
        `🎮 Night City RPG ativado!\nXP retroativo: +${gained} XP de ${result.awarded.length} tarefas já concluídas.`,
        9000
      );
      await this.afterChange(result, true);
    } else {
      if (result.awarded.length && mode !== "manual") {
        new Notice(`🎮 +${gained} XP de ${result.awarded.length} tarefas concluídas fora do Obsidian (sincronização).`, 6000);
      }
      if (mode === "manual") new Notice("🔄 XP recalculado com sucesso!");
      await this.afterChange(result, mode === "startup");
    }
  }

  async scanFile(file, result) {
    if (!(file instanceof TFile) || file.extension !== "md") return;
    if (this.isIgnored(file.path)) {
      delete this.openTasks[file.path];
      return;
    }

    let content;
    try {
      content = await this.app.vault.read(file);
    } catch (e) {
      return;
    }

    const generated = GENERATED_RE.test(content);
    const lines = content.split("\n");
    const seen = {};
    const open = [];
    const today = todayStr();
    const week = weekStr();
    let inCode = false;

    for (let i = 0; i < lines.length; i++) {
      const stripped = lines[i].replace(/\r$/, "").replace(/^[\s>]*/, "");
      if (/^(```|~~~)/.test(stripped)) {
        inCode = !inCode;
        continue;
      }
      if (inCode) continue;

      const m = stripped.match(/^[-*+]\s+\[(.)\]\s+(.+)$/);
      if (!m) continue;

      const status = m[1];
      const text = m[2].trim().replace(/\s+/g, " ");
      const isDaily = /#daily\b/i.test(text);
      const isWeekly = /#(weekly|semanal)\b/i.test(text);
      const cycleSuffix = isDaily ? "::" + today : isWeekly ? "::W" + week : "";
      const base = `${file.path}::${text}${cycleSuffix}`;
      seen[base] = (seen[base] || 0) + 1;
      const key = seen[base] > 1 ? `${base}::${seen[base]}` : base;
      const cls = this.classify(text, file.path);

      if (status === "x" || status === "X") {
        if (!this.data.ledger[key]) {
          const now = new Date();
          const entry = {
            xp: cls.xp,
            type: cls.type,
            attr: cls.attr,
            date: today,
            hour: now.getHours(),
            ts: now.getTime(),
            text: cleanText(text),
            file: file.path
          };
          this.data.ledger[key] = entry;
          result.awarded.push(entry);
        }
      } else if (status === " ") {
        open.push({ text, clean: cleanText(text), line: i, file: file.path, type: cls.type, xp: cls.xp, attr: cls.attr });
        const entry = this.data.ledger[key];
        if (entry && !generated && this.data.revokeOnUncheck) {
          delete this.data.ledger[key];
          result.revoked.push(entry);
        }
      }
    }

    this.openTasks[file.path] = open;
  }

  handleRename(file, oldPath) {
    const ledger = this.data.ledger;
    const isFolder = file instanceof TFolder;
    for (const k of Object.keys(ledger)) {
      let nk = null;
      if (!isFolder && k.startsWith(oldPath + "::")) nk = file.path + k.slice(oldPath.length);
      if (isFolder && k.startsWith(oldPath + "/")) nk = file.path + k.slice(oldPath.length);
      if (nk) {
        ledger[nk] = Object.assign({}, ledger[k], { file: nk.split("::")[0] });
        delete ledger[k];
      }
    }
    for (const p of Object.keys(this.openTasks)) {
      if (p === oldPath || p.startsWith(oldPath + "/")) {
        const np = file.path + p.slice(oldPath.length);
        this.openTasks[np] = this.openTasks[p].map((q) => Object.assign({}, q, { file: np }));
        delete this.openTasks[p];
      }
    }
    this.save();
    this.refreshViews();
  }

  // Desmarca automaticamente as tarefas #daily a cada novo dia
  async dailyReset() {
    const today = todayStr();
    if (this.data.lastDailyReset === today) return;
    this.data.lastDailyReset = today;
    for (const f of this.app.vault.getMarkdownFiles()) {
      if (this.isIgnored(f.path)) continue;
      const c = await this.app.vault.read(f);
      if (!/#daily\b/i.test(c)) continue;
      const n = c.replace(/^([\s>]*[-*+]\s+)\[[xX]\](\s+.*#daily\b.*)$/gim, "$1[ ]$2");
      if (n !== c) await this.app.vault.modify(f, n);
    }
    await this.save();
  }

  // Desmarca automaticamente as tarefas #weekly / #semanal a cada nova semana (toda segunda-feira)
  async weeklyReset() {
    const week = weekStr();
    if (this.data.lastWeeklyReset === week) return;
    this.data.lastWeeklyReset = week;
    for (const f of this.app.vault.getMarkdownFiles()) {
      if (this.isIgnored(f.path)) continue;
      const c = await this.app.vault.read(f);
      if (!/#(weekly|semanal)\b/i.test(c)) continue;
      const n = c.replace(/^([\s>]*[-*+]\s+)\[[xX]\](\s+.*#(?:weekly|semanal)\b.*)$/gim, "$1[ ]$2");
      if (n !== c) await this.app.vault.modify(f, n);
    }
    await this.save();
  }

  // -------------------------------------------------------------------------
  // Estatísticas, níveis e conquistas
  // -------------------------------------------------------------------------
  getStats() {
    const entries = Object.values(this.data.ledger);
    let total = this.data.bonusXP || 0;
    let bosses = 0;
    let nightOwl = false;
    const attrXP = { INT: 0, TEC: 0, REF: 0, COOL: 0, CORPO: 0 };
    const perDay = {};

    for (const e of entries) {
      total += e.xp || 0;
      if (attrXP[e.attr] !== undefined) attrXP[e.attr] += e.xp || 0;
      if (e.type === "boss") bosses++;
      if (typeof e.hour === "number" && e.hour < 5) nightOwl = true;
      if (e.date) perDay[e.date] = (perDay[e.date] || 0) + 1;
    }

    const lv = levelFromXP(total);
    const tIdx = tierIndex(lv.level);

    const days = Object.keys(perDay).sort();
    let best = 0;
    let run = 0;
    let prev = null;
    for (const d of days) {
      run = prev && dayDiff(prev, d) === 1 ? run + 1 : 1;
      best = Math.max(best, run);
      prev = d;
    }

    let streak = 0;
    let probe = todayStr();
    if (!perDay[probe]) probe = shiftDay(probe, -1);
    while (perDay[probe]) {
      streak++;
      probe = shiftDay(probe, -1);
    }

    const attrs = {};
    for (const k of Object.keys(attrXP)) {
      attrs[k] = { xp: attrXP[k], level: Math.min(20, 1 + Math.floor(Math.sqrt(attrXP[k] / 25))) };
    }

    return {
      total,
      level: lv.level,
      cur: lv.cur,
      next: lv.next,
      tierIdx: tIdx,
      tier: TIERS[tIdx],
      nextTier: TIERS[tIdx + 1] || null,
      tasks: entries.length,
      bosses,
      nightOwl,
      streak,
      bestStreak: best,
      bestDay: Math.max(0, ...Object.values(perDay)),
      todayCount: perDay[todayStr()] || 0,
      attrs
    };
  }

  checkAchievements() {
    const unlocked = [];
    for (let pass = 0; pass < 6; pass++) {
      const s = this.getStats();
      let any = false;
      for (const a of ACHIEVEMENTS) {
        if (this.data.achievements[a.id]) continue;
        let ok = false;
        try {
          ok = a.check(s);
        } catch (e) {
          ok = false;
        }
        if (ok) {
          this.data.achievements[a.id] = todayStr();
          this.data.bonusXP = (this.data.bonusXP || 0) + a.xp;
          this.pushLog({ ts: Date.now(), text: `Conquista: ${a.icon} ${a.name}`, xp: a.xp, type: "achievement" });
          unlocked.push(a);
          any = true;
        }
      }
      if (!any) break;
    }
    return unlocked;
  }

  pushLog(item) {
    this.data.log.unshift(item);
    this.data.log = this.data.log.slice(0, 80);
  }

  async afterChange(result, silent) {
    const hadLevel = this.data.lastLevel !== null && this.data.lastLevel !== undefined;
    const prevLevel = hadLevel ? this.data.lastLevel : 1;
    const prevTier = tierIndex(prevLevel);

    for (const e of result.awarded) this.pushLog({ ts: e.ts, text: e.text, xp: e.xp, type: e.type, attr: e.attr });
    for (const e of result.revoked) this.pushLog({ ts: Date.now(), text: e.text, xp: -e.xp, type: "revoke", attr: e.attr });

    const unlocked = this.checkAchievements();
    const s = this.getStats();

    if (!silent) {
      if (result.awarded.length === 1) {
        const e = result.awarded[0];
        new Notice(`${TYPES[e.type].icon} +${e.xp} XP  ·  ${ATTRS[e.attr].icon} ${ATTRS[e.attr].name}\n${e.text}`, 4500);
      } else if (result.awarded.length > 1) {
        const xp = result.awarded.reduce((a, e) => a + e.xp, 0);
        new Notice(`⚡ +${xp} XP — ${result.awarded.length} quests concluídas!`, 4500);
      }
      for (const e of result.revoked) new Notice(`↩️ -${e.xp} XP (tarefa desmarcada): ${e.text}`, 3500);
    }

    if (hadLevel) {
      for (const a of unlocked) new Notice(`🏆 CONQUISTA DESBLOQUEADA\n${a.icon} ${a.name} (+${a.xp} XP)\n${a.desc}`, 7000);
      if (s.level > prevLevel) {
        if (s.tierIdx > prevTier) {
          new EvolutionModal(this.app, s.tier, s.level).open();
        } else {
          new Notice(`⬆️ LEVEL UP! Nível ${s.level}\n${s.tier.icon} ${s.tier.name} — ${s.tier.game}`, 6000);
        }
      }
    }

    this.data.lastLevel = s.level;
    await this.save();
    this.refreshViews();
  }

  // -------------------------------------------------------------------------
  // Views (blocos de código ```rpg```)
  // -------------------------------------------------------------------------
  mountView(type, el, ctx) {
    const entry = { type, el };
    this.views.add(entry);
    const child = new MarkdownRenderChild(el);
    child.onunload = () => this.views.delete(entry);
    ctx.addChild(child);
    this.renderView(entry);
  }

  renderView(entry) {
    try {
      if (entry.type === "hud") this.renderHUD(entry.el);
      else if (entry.type === "quests") this.renderQuests(entry.el);
      else if (entry.type === "achievements") this.renderAchievements(entry.el);
      else if (entry.type === "log") this.renderLog(entry.el);
      else if (entry.type === "classes") this.renderClasses(entry.el);
    } catch (e) {
      console.error("Night City RPG render error", e);
    }
  }

  refreshViews() {
    for (const v of this.views) this.renderView(v);
    this.updateStatusBar();
  }

  updateStatusBar() {
    if (!this.statusEl) return;
    const s = this.getStats();
    this.statusEl.setText(`⚡ Lv ${s.level} · ${s.tier.icon} ${s.tier.name} · ${s.cur}/${s.next} XP`);
    this.statusEl.setAttr("aria-label", "Night City RPG — abrir Central de Quests");
  }

  async openQuests() {
    const f = this.app.vault.getAbstractFileByPath(this.data.questsNotePath);
    if (f instanceof TFile) await this.app.workspace.getLeaf(false).openFile(f);
    else new Notice(`Nota de quests não encontrada: ${this.data.questsNotePath}`);
  }

  renderHUD(el) {
    el.empty();
    const s = this.getStats();
    const t = s.tier;
    const hud = el.createDiv({ cls: "rpg-hud" });
    hud.style.setProperty("--tier-color", t.color);

    const top = hud.createDiv({ cls: "rpg-hud-top" });
    top.createDiv({ cls: "rpg-avatar", text: t.icon });
    const id = top.createDiv({ cls: "rpg-identity" });
    id.createDiv({ cls: "rpg-glitch-label", text: "// NIGHT CITY ACADEMY · PERFIL DO MERC" });
    id.createDiv({ cls: "rpg-player", text: this.data.playerName || "V" });
    id.createDiv({ cls: "rpg-class", text: `${t.name} · ${t.rank}` });
    id.createDiv({ cls: "rpg-game", text: `🎮 ${t.game} — “${t.quote}”` });
    const lvl = top.createDiv({ cls: "rpg-level" });
    lvl.createDiv({ cls: "rpg-level-label", text: "LVL" });
    lvl.createDiv({ cls: "rpg-level-num", text: String(s.level) });

    const pct = Math.min(100, Math.round((s.cur / s.next) * 100));
    const xpWrap = hud.createDiv({ cls: "rpg-xp" });
    const xpHead = xpWrap.createDiv({ cls: "rpg-xp-head" });
    xpHead.createSpan({ text: `XP ${s.cur} / ${s.next}` });
    xpHead.createSpan({ text: `faltam ${s.next - s.cur} XP para o nível ${s.level + 1}` });
    const bar = xpWrap.createDiv({ cls: "rpg-bar" });
    bar.createDiv({ cls: "rpg-bar-fill" }).style.width = `${pct}%`;

    const grid = hud.createDiv({ cls: "rpg-stats" });
    const unlockedCount = Object.keys(this.data.achievements).length;
    [
      ["💠", "XP Total", s.total],
      ["✅", "Gigs Concluídas", s.tasks],
      ["☠️", "Bosses Derrotados", s.bosses],
      ["🔥", "Streak Atual", `${s.streak}d`],
      ["⚡", "Hoje", s.todayCount],
      ["🏆", "Conquistas", `${unlockedCount}/${ACHIEVEMENTS.length}`]
    ].forEach(([icon, label, val]) => {
      const c = grid.createDiv({ cls: "rpg-stat" });
      c.createDiv({ cls: "rpg-stat-val", text: `${icon} ${val}` });
      c.createDiv({ cls: "rpg-stat-label", text: label });
    });

    const attrsEl = hud.createDiv({ cls: "rpg-attrs" });
    attrsEl.createDiv({ cls: "rpg-section-title", text: "ATRIBUTOS · MÁX 20" });
    for (const [k, a] of Object.entries(ATTRS)) {
      const v = s.attrs[k];
      const row = attrsEl.createDiv({ cls: "rpg-attr" });
      row.style.setProperty("--attr-color", a.color);
      row.setAttr("title", `${a.desc} — ${v.xp} XP`);
      row.createDiv({ cls: "rpg-attr-name", text: `${a.icon} ${a.name}` });
      const b = row.createDiv({ cls: "rpg-attr-bar" });
      b.createDiv({ cls: "rpg-attr-fill" }).style.width = `${(v.level / 20) * 100}%`;
      row.createDiv({ cls: "rpg-attr-lvl", text: String(v.level) });
    }

    const path = hud.createDiv({ cls: "rpg-path" });
    TIERS.forEach((tt, i) => {
      const n = path.createDiv({
        cls: "rpg-path-node" + (i <= s.tierIdx ? " is-unlocked" : "") + (i === s.tierIdx ? " is-current" : "")
      });
      n.style.setProperty("--node-color", tt.color);
      n.setAttr("title", `Nível ${tt.min}+ · ${tt.name} (${tt.game})`);
      n.setText(i <= s.tierIdx ? tt.icon : "🔒");
    });

    const evo = hud.createDiv({ cls: "rpg-evo" });
    if (s.nextTier) {
      evo.setText(
        `🧬 Próxima evolução no Nível ${s.nextTier.min}: ${s.nextTier.icon} ${s.nextTier.name} (${s.nextTier.game}) — faltam ${
          s.nextTier.min - s.level
        } níveis`
      );
    } else {
      evo.setText("🎸 Você chegou ao topo da cadeia alimentar de Night City. Wake up, Samurai.");
    }

    // Barra de Ações Rápidas no HUD (Nova Quest, Editar Quests, Central)
    const hudToolbar = hud.createDiv({ cls: "rpg-hud-toolbar" });
    const btnNewQuest = hudToolbar.createEl("button", {
      cls: "rpg-hud-btn rpg-hud-btn-primary",
      text: "➕ Nova Quest / Trabalho"
    });
    btnNewQuest.onclick = () => new QuestEditorModal(this.app, this).open();

    const btnManage = hudToolbar.createEl("button", {
      cls: "rpg-hud-btn",
      text: "✏️ Editar / Gerenciar Quests"
    });
    btnManage.onclick = () => new QuestManagerModal(this.app, this).open();

    const btnOpenHub = hudToolbar.createEl("button", {
      cls: "rpg-hud-btn",
      text: "🎮 Central de Quests"
    });
    btnOpenHub.onclick = () => this.openQuests();

    const btnMobile = hudToolbar.createEl("button", {
      cls: "rpg-hud-btn",
      text: "📱 App Android (Pop-ups)"
    });
    btnMobile.onclick = () => new MobileAppModal(this.app, this).open();
  }

  // -------------------------------------------------------------------------
  // Operações de CRUD de Quests nas Notas Markdown
  // -------------------------------------------------------------------------
  async completeQuestInFile(filePath, lineIdx) {
    const f = this.app.vault.getAbstractFileByPath(filePath);
    if (!(f instanceof TFile)) return;
    const c = await this.app.vault.read(f);
    const lines = c.split("\n");
    const ln = lines[lineIdx];
    if (ln && ln.includes("[ ]")) {
      lines[lineIdx] = ln.replace("[ ]", "[x]");
      await this.app.vault.modify(f, lines.join("\n"));
    }
  }

  async updateQuestInFile(filePath, lineIdx, newTaskText) {
    const f = this.app.vault.getAbstractFileByPath(filePath);
    if (!(f instanceof TFile)) return;
    const c = await this.app.vault.read(f);
    const lines = c.split("\n");
    const ln = lines[lineIdx];
    if (ln === undefined) return;
    const m = ln.match(/^([\s>]*[-*+]\s+\[.\]\s+)(.*)$/);
    if (m) {
      lines[lineIdx] = `${m[1]}${newTaskText}`;
      await this.app.vault.modify(f, lines.join("\n"));
    }
  }

  async deleteQuestInFile(filePath, lineIdx) {
    const f = this.app.vault.getAbstractFileByPath(filePath);
    if (!(f instanceof TFile)) return;
    const c = await this.app.vault.read(f);
    const lines = c.split("\n");
    if (lineIdx >= 0 && lineIdx < lines.length) {
      lines.splice(lineIdx, 1);
      await this.app.vault.modify(f, lines.join("\n"));
    }
  }

  async createNewQuest(formattedTaskText, typeVal, destVal) {
    const targets = [];
    if (destVal === "both") {
      targets.push("00 - Início/🎮 Central de Quests.md");
      targets.push("00 - Início/🏠 Página Inicial.md");
    } else if (destVal === "quests") {
      targets.push("00 - Início/🎮 Central de Quests.md");
    } else if (destVal === "home") {
      targets.push("00 - Início/🏠 Página Inicial.md");
    } else if (destVal === "semanal") {
      targets.push("02 - Rotina & Diário/📅 Planejamento Semanal.md");
    } else if (destVal === "rna") {
      targets.push("01 - Projetos & Trabalhos/☢️ Projeto RNA - Reator Nuclear PWR (Angra 1).md");
    } else if (destVal === "soma") {
      targets.push("01 - Projetos & Trabalhos/🌐 Projeto SOMA - Plataforma Acadêmica (PMC & Pitch).md");
    } else if (destVal === "faculdade") {
      targets.push("01 - Projetos & Trabalhos/🎓 Trabalhos da Faculdade (IFF).md");
    }

    for (const filePath of targets) {
      await this.insertTaskIntoNote(filePath, formattedTaskText, typeVal);
    }
  }

  async insertTaskIntoNote(filePath, formattedTaskText, typeVal) {
    const f = this.app.vault.getAbstractFileByPath(filePath);
    if (!(f instanceof TFile)) return;
    const c = await this.app.vault.read(f);
    const lines = c.split("\n");

    // Define padrões de cabeçalho de seção/post-it conforme o tipo da quest
    let headerRegex;
    if (typeVal === "daily") {
      headerRegex = /\[!postit-verde\].*Daily|Daily Quests/i;
    } else if (typeVal === "weekly") {
      headerRegex = /\[!postit-(roxo|laranja)\].*(Weekly|Semanal|Contratos da Semana)|Weekly Quests|Cronograma Semanal/i;
    } else if (typeVal === "boss") {
      headerRegex = /\[!postit-rosa\].*(Boss|Alerta|Entregas)|Boss Fights/i;
    } else if (typeVal === "main") {
      headerRegex = /\[!postit-(amarelo|rosa|azul)\].*(Main Quests|Entregas|Deck Netrunner|Trabalhos)|### 🔥 Main Quests/i;
    } else {
      headerRegex = /\[!postit-azul\].*(Side Quests|Deck Netrunner)|### 🧭 Side Quests/i;
    }

    let headerIdx = lines.findIndex((l) => headerRegex.test(l));
    if (headerIdx === -1) {
      // Fallback: primeiro post-it ou primeira lista de tasks na nota
      headerIdx = lines.findIndex((l) => /\[!postit-/.test(l) || /^###\s+/.test(l));
    }

    if (headerIdx !== -1) {
      const isCallout = lines[headerIdx].trim().startsWith(">");
      const prefix = isCallout ? "> > - [ ] " : "- [ ] ";
      let insertAt = headerIdx + 1;
      for (let i = headerIdx + 1; i < lines.length; i++) {
        const ln = lines[i];
        if (isCallout) {
          if (!ln.trim().startsWith(">") || /^>\s*>\s*\[!postit-/.test(ln) || /^>\s*$/.test(ln.trim())) {
            break;
          }
          if (/^>\s*>\s*[-*+]\s+\[.\]/.test(ln)) {
            insertAt = i + 1;
          }
        } else {
          if (/^##/.test(ln) || /^---/.test(ln)) break;
          if (/^[-*+]\s+\[.\]/.test(ln.trim())) {
            insertAt = i + 1;
          }
        }
      }
      lines.splice(insertAt, 0, `${prefix}${formattedTaskText}`);
    } else {
      lines.push(`- [ ] ${formattedTaskText}`);
    }

    await this.app.vault.modify(f, lines.join("\n"));
  }

  renderQuests(el) {
    el.empty();
    const exclude = this.data.questBoardExclude || [];
    const all = [];
    const seenTxt = new Set();
    for (const [path, list] of Object.entries(this.openTasks)) {
      if (exclude.includes(path)) continue;
      for (const q of list) {
        const k = q.clean.toLowerCase();
        if (!k || seenTxt.has(k)) continue;
        seenTxt.add(k);
        all.push(q);
      }
    }
    all.sort((a, b) => TYPES[a.type].order - TYPES[b.type].order || b.xp - a.xp);

    const box = el.createDiv({ cls: "rpg-quests" });
    const headerBar = box.createDiv({ cls: "rpg-quests-header" });
    const totalXP = all.reduce((a, q) => a + q.xp, 0);
    headerBar.createDiv({
      cls: "rpg-section-title",
      text: `📡 ${all.length} QUESTS ABERTAS · ${totalXP} XP DISPONÍVEL`
    });
    const headerBtns = headerBar.createDiv({ cls: "rpg-quests-header-btns" });
    const btnAdd = headerBtns.createEl("button", { cls: "rpg-hud-btn rpg-hud-btn-primary", text: "➕ Nova Quest" });
    btnAdd.onclick = () => new QuestEditorModal(this.app, this).open();
    const btnMgr = headerBtns.createEl("button", { cls: "rpg-hud-btn", text: "📋 Gerenciar Todas" });
    btnMgr.onclick = () => new QuestManagerModal(this.app, this).open();

    if (!all.length) {
      box.createDiv({ cls: "rpg-empty", text: "Nenhuma quest aberta. Night City está calma... por enquanto." });
      return;
    }

    for (const q of all.slice(0, this.data.questBoardLimit || 30)) {
      const row = box.createDiv({ cls: `rpg-quest rpg-type-${q.type}` });
      const btn = row.createEl("button", { cls: "rpg-quest-done", text: "✔" });
      btn.setAttr("aria-label", "Concluir quest");
      btn.onclick = async () => {
        await this.completeQuestInFile(q.file, q.line);
      };
      row.createSpan({ cls: "rpg-quest-badge", text: `${TYPES[q.type].icon} ${TYPES[q.type].label}` });
      row.createSpan({ cls: "rpg-quest-text", text: q.clean });
      row.createSpan({ cls: "rpg-quest-attr", text: ATTRS[q.attr].icon, attr: { title: ATTRS[q.attr].name } });
      row.createSpan({ cls: "rpg-quest-xp", text: `+${q.xp} XP` });
      const link = row.createEl("a", { cls: "rpg-quest-file", text: q.file.split("/").pop().replace(/\.md$/, "") });
      link.onclick = (ev) => {
        ev.preventDefault();
        this.app.workspace.openLinkText(q.file, "", false);
      };

      const actWrap = row.createDiv({ cls: "rpg-quest-actions" });
      const btnEdit = actWrap.createEl("button", { cls: "rpg-quest-action-btn", text: "✏️" });
      btnEdit.setAttr("title", "Editar esta quest");
      btnEdit.onclick = () => {
        new QuestEditorModal(this.app, this, q).open();
      };
      const btnDel = actWrap.createEl("button", { cls: "rpg-quest-action-btn is-danger", text: "🗑️" });
      btnDel.setAttr("title", "Excluir esta quest");
      btnDel.onclick = async () => {
        await this.deleteQuestInFile(q.file, q.line);
        new Notice("🗑️ Quest excluída!");
      };
    }
  }

  renderAchievements(el) {
    el.empty();
    const box = el.createDiv({ cls: "rpg-achievements" });
    const got = Object.keys(this.data.achievements).length;
    box.createDiv({ cls: "rpg-section-title", text: `🏆 CONQUISTAS · ${got}/${ACHIEVEMENTS.length}` });
    const grid = box.createDiv({ cls: "rpg-ach-grid" });
    for (const a of ACHIEVEMENTS) {
      const date = this.data.achievements[a.id];
      const card = grid.createDiv({ cls: "rpg-ach" + (date ? " is-unlocked" : "") });
      card.createDiv({ cls: "rpg-ach-icon", text: date ? a.icon : "🔒" });
      const info = card.createDiv({ cls: "rpg-ach-info" });
      info.createDiv({ cls: "rpg-ach-name", text: a.name });
      info.createDiv({ cls: "rpg-ach-desc", text: `${a.desc} · +${a.xp} XP` });
      if (date) info.createDiv({ cls: "rpg-ach-date", text: `Desbloqueada em ${date.split("-").reverse().join("/")}` });
    }
  }

  renderLog(el) {
    el.empty();
    const box = el.createDiv({ cls: "rpg-log" });
    box.createDiv({ cls: "rpg-section-title", text: "📜 LOG DE COMBATE" });
    const items = this.data.log.slice(0, 20);
    if (!items.length) {
      box.createDiv({ cls: "rpg-empty", text: "Nenhuma ação registrada ainda. Marque uma tarefa como concluída!" });
      return;
    }
    for (const it of items) {
      const row = box.createDiv({ cls: "rpg-log-row" + (it.xp < 0 ? " is-negative" : "") });
      row.createSpan({ cls: "rpg-log-time", text: formatTime(it.ts) });
      const icon =
        it.type === "achievement" ? "🏆" : it.type === "revoke" ? "↩️" : TYPES[it.type] ? TYPES[it.type].icon : "📌";
      row.createSpan({ cls: "rpg-log-text", text: `${icon} ${it.text}` });
      row.createSpan({ cls: "rpg-log-xp", text: `${it.xp > 0 ? "+" : ""}${it.xp} XP` });
    }
  }

  renderClasses(el) {
    el.empty();
    const s = this.getStats();
    const box = el.createDiv({ cls: "rpg-classes" });
    box.createDiv({ cls: "rpg-section-title", text: "🧬 ÁRVORE DE EVOLUÇÃO DE CLASSES" });
    TIERS.forEach((t, i) => {
      const row = box.createDiv({ cls: "rpg-class-row" + (i <= s.tierIdx ? " is-unlocked" : "") + (i === s.tierIdx ? " is-current" : "") });
      row.style.setProperty("--tier-color", t.color);
      row.createDiv({ cls: "rpg-class-icon", text: t.icon });
      const info = row.createDiv({ cls: "rpg-class-info" });
      const max = TIERS[i + 1] ? `${TIERS[i + 1].min - 1}` : "∞";
      info.createDiv({ cls: "rpg-class-name", text: `${t.name} — ${t.rank}` });
      info.createDiv({ cls: "rpg-class-meta", text: `Níveis ${t.min}–${max} · ${t.game}` });
      info.createDiv({ cls: "rpg-class-quote", text: `“${t.quote}”` });
      row.createDiv({ cls: "rpg-class-status", text: i === s.tierIdx ? "◉ ATUAL" : i < s.tierIdx ? "✔" : "🔒" });
    });
  }
};

// ---------------------------------------------------------------------------
// Configurações
// ---------------------------------------------------------------------------
class RPGSettingTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    const d = this.plugin.data;
    containerEl.empty();
    containerEl.createEl("h2", { text: "🎮 Night City RPG — Gamificação" });

    new Setting(containerEl)
      .setName("Nome do personagem")
      .addText((t) =>
        t.setValue(d.playerName).onChange(async (v) => {
          d.playerName = v;
          await this.plugin.save();
          this.plugin.refreshViews();
        })
      );

    new Setting(containerEl)
      .setName("XP base de uma tarefa comum (Gig)")
      .setDesc("Boss = 150 · Main = 50 · Side = 30 · Daily = 10 · ou use #xp/NN na tarefa")
      .addText((t) =>
        t.setValue(String(d.baseXP)).onChange(async (v) => {
          d.baseXP = parseInt(v, 10) || 15;
          await this.plugin.save();
        })
      );

    new Setting(containerEl)
      .setName("Remover XP ao desmarcar uma tarefa")
      .setDesc("Evita farm de XP. Notas geradas pelo sincronizador SUAP/Classroom nunca removem XP.")
      .addToggle((t) =>
        t.setValue(d.revokeOnUncheck).onChange(async (v) => {
          d.revokeOnUncheck = v;
          await this.plugin.save();
        })
      );

    new Setting(containerEl)
      .setName("Pastas ignoradas")
      .setDesc("Separadas por vírgula")
      .addText((t) =>
        t.setValue(d.ignoreFolders.join(", ")).onChange(async (v) => {
          d.ignoreFolders = v.split(",").map((x) => x.trim()).filter(Boolean);
          await this.plugin.save();
        })
      );

    new Setting(containerEl)
      .setName("Notas fora do Quadro de Quests")
      .setDesc("Caminhos separados por vírgula (evita duplicatas da Página Inicial)")
      .addText((t) =>
        t.setValue(d.questBoardExclude.join(", ")).onChange(async (v) => {
          d.questBoardExclude = v.split(",").map((x) => x.trim()).filter(Boolean);
          await this.plugin.save();
          this.plugin.refreshViews();
        })
      );

    new Setting(containerEl)
      .setName("Recalcular XP")
      .setDesc("Varre todas as notas novamente procurando tarefas concluídas.")
      .addButton((b) => b.setButtonText("🔄 Recalcular").onClick(() => this.plugin.fullScan("manual")));

    new Setting(containerEl)
      .setName("Resetar progresso")
      .setDesc("Zera XP, conquistas e log, e recalcula a partir das tarefas já concluídas.")
      .addButton((b) =>
        b
          .setButtonText("⚠️ Resetar")
          .setWarning()
          .onClick(async () => {
            if (!confirm("Tem certeza que deseja resetar todo o progresso do RPG?")) return;
            Object.assign(d, { ledger: {}, bonusXP: 0, achievements: {}, log: [], lastLevel: null, initialized: false });
            await this.plugin.save();
            await this.plugin.fullScan("initial");
          })
      );
  }
}

class MobileAppModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass("rpg-quest-editor-modal");

    contentEl.createEl("h2", {
      cls: "rpg-modal-header",
      text: "📱 NIGHT CITY RPG // APK STANDALONE & SINCRONIZAÇÃO"
    });
    contentEl.createDiv({
      cls: "rpg-modal-subtitle",
      text: "Use o APK Standalone 100% offline no celular (ideal para o alojamento) e sincronize com o Obsidian quando quiser."
    });

    const apkCard = contentEl.createDiv({ cls: "rpg-preview-box" });
    apkCard.createDiv({ cls: "rpg-preview-label", text: "📦 1. ARQUIVO APK STANDALONE (INSTALAÇÃO OFFLINE NO ANDROID):" });
    apkCard.createDiv({
      cls: "rpg-preview-text",
      text: "./dist/NightCityRPG-Standalone.apk"
    });

    const syncGroup = contentEl.createDiv({ cls: "rpg-form-group" });
    syncGroup.createEl("label", {
      cls: "rpg-form-label",
      text: "🔄 2. SINCRONIZAÇÃO OFFLINE (COLE AQUI O CÓDIGO DE SYNC DO CELULAR OU EXPORTE DO PC)"
    });
    const syncTextarea = syncGroup.createEl("textarea", {
      cls: "rpg-form-input",
      attr: {
        rows: "4",
        placeholder: "Cole aqui o código JSON copiado na aba [🔄 Sync] do aplicativo Android para atualizar suas quests e XP no Obsidian sem precisar de Wi-Fi..."
      }
    });

    const syncBtns = contentEl.createDiv({ cls: "rpg-modal-footer", attr: { style: "margin-top:8px;" } });
    const btnApplySync = syncBtns.createEl("button", {
      cls: "rpg-hud-btn rpg-hud-btn-primary",
      text: "📥 Aplicar Código do Celular no Obsidian"
    });
    btnApplySync.onclick = async () => {
      const raw = syncTextarea.value.trim();
      if (!raw) {
        new Notice("⚠️ Cole primeiro o código de sincronização gerado no aplicativo do celular!");
        return;
      }
      try {
        const payload = JSON.parse(raw);
        const actions = payload.pendingActions || [];
        let count = 0;
        for (const act of actions) {
          if (act.kind === "toggle" && act.file) {
            const f = this.app.vault.getAbstractFileByPath(act.file);
            if (f instanceof TFile) {
              const c = await this.app.vault.read(f);
              const lines = c.split("\n");
              for (let i = 0; i < lines.length; i++) {
                if (act.clean && lines[i].toLowerCase().includes(act.clean.toLowerCase().slice(0, 24))) {
                  lines[i] = lines[i].replace(/\[[ xX]\]/, act.completed ? "[x]" : "[ ]");
                  count++;
                }
              }
              await this.app.vault.modify(f, lines.join("\n"));
            }
          } else if (act.kind === "create" && act.title) {
            const duePart = act.due ? ` *(Prazo: ${act.due})*` : "";
            const fmt = `${act.title}${duePart} #${act.type || "side"} #${(act.attr || "INT").toLowerCase()}`;
            await this.plugin.createNewQuest(fmt, act.type || "side", act.dest || "both");
            count++;
          }
        }
        await this.plugin.fullScan("manual");
        new Notice(`✅ Sincronização concluída! ${count} alterações do celular aplicadas ao Obsidian!`);
        this.close();
      } catch (e) {
        new Notice("❌ Código de sincronização inválido: " + e.message);
      }
    };

    const btnOpenFolder = syncBtns.createEl("button", {
      cls: "rpg-hud-btn",
      text: "📂 Abrir Pasta do APK"
    });
    btnOpenFolder.onclick = () => {
      try {
        require("child_process").exec('explorer.exe /select,"dist\\NightCityRPG-Standalone.apk"');
      } catch (e) {
        new Notice("Pasta: ./dist");
      }
    };

    const footer = contentEl.createDiv({ cls: "rpg-modal-footer" });
    const btnStart = footer.createEl("button", {
      cls: "rpg-hud-btn",
      text: "🚀 Ligar Servidor Wi-Fi/Hotspot (8077)"
    });
    btnStart.onclick = () => {
      try {
        const cp = require("child_process");
        cp.spawn("python", ["server.py"], {
          detached: true,
          stdio: "ignore"
        }).unref();
        new Notice("🟢 Servidor Night City RPG Mobile ativo na porta 8077!");
      } catch (e) {
        new Notice("Erro ao iniciar servidor: " + e.message);
      }
    };

    const btnRebuildApk = footer.createEl("button", {
      cls: "rpg-hud-btn",
      text: "🔨 Atualizar APK com Dados Atuais"
    });
    btnRebuildApk.onclick = () => {
      try {
        const cp = require("child_process");
        cp.exec('python "build_standalone_apk.py"', (err) => {
          if (err) new Notice("Erro ao regerar APK: " + err.message);
          else new Notice("✅ APK Standalone atualizado em dist/NightCityRPG-Standalone.apk!");
        });
      } catch (e) {
        new Notice("Erro: " + e.message);
      }
    };
  }
}
