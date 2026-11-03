import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  Switch,
  TextInput,
  Modal,
  StatusBar,
  RefreshControl,
  Alert,
  Platform,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Notifications from 'expo-notifications';

// Configuração de Handler Nativo de Pop-ups Android (Heads-up Notification)
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    priority: Notifications.AndroidNotificationPriority.MAX,
  }),
});

const DEFAULT_API = 'http://localhost:8077';

export default function App() {
  const [apiHost, setApiHost] = useState(DEFAULT_API);
  const [state, setState] = useState(null);
  const [online, setOnline] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [popupQuest, setPopupQuest] = useState(null);

  // Modal Nova Quest
  const [modalVisible, setModalVisible] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDue, setNewDue] = useState('');
  const [newCategory, setNewCategory] = useState('daily');
  const [newAttr, setNewAttr] = useState('INT');
  const [newPopupEnabled, setNewPopupEnabled] = useState(true);

  useEffect(() => {
    setupAndroidChannel();
    loadInitialState();
  }, []);

  async function setupAndroidChannel() {
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('daily-quests-cyber', {
        name: 'Daily Quests // Night City RPG',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 200, 100, 200],
        lightColor: '#fcee0a',
      });
    }
    await Notifications.requestPermissionsAsync();
  }

  async function loadInitialState() {
    const savedHost = await AsyncStorage.getItem('nc_api_host');
    const hostToUse = savedHost || DEFAULT_API;
    setApiHost(hostToUse);
    await fetchState(hostToUse);
  }

  const fetchState = useCallback(async (hostOverride) => {
    const targetHost = hostOverride || apiHost;
    try {
      const res = await fetch(`${targetHost}/api/state`);
      const data = await res.json();
      setState(data);
      setOnline(true);
      await AsyncStorage.setItem('nc_cached_state', JSON.stringify(data));
      await syncNativeAndroidNotifications(data);
    } catch (err) {
      setOnline(false);
      const cached = await AsyncStorage.getItem('nc_cached_state');
      if (cached) setState(JSON.parse(cached));
    }
  }, [apiHost]);

  // Agenda ou cancela notificações nativas Android conforme chave geral + chave individual de cada Daily Quest
  async function syncNativeAndroidNotifications(currentState) {
    try {
      await Notifications.cancelAllScheduledNotificationsAsync();
      const notif = currentState?.notifications;
      if (!notif || !notif.masterEnabled) return;

      const pendingDailies = (currentState?.dailyQuests || []).filter(
        (q) => !q.completed && q.individualPopupEnabled
      );
      if (pendingDailies.length === 0) return;

      const times = notif.reminderTimes || ['09:00', '14:00', '20:00'];
      for (const timeStr of times) {
        const [hour, minute] = timeStr.split(':').map(Number);
        if (isNaN(hour) || isNaN(minute)) continue;

        for (const q of pendingDailies) {
          await Notifications.scheduleNotificationAsync({
            content: {
              title: `⚡ DAILY QUEST [${q.attr}] (+10 XP)`,
              body: q.clean,
              data: { questId: q.id, file: q.file, line: q.line },
              sound: true,
              priority: Notifications.AndroidNotificationPriority.MAX,
            },
            trigger: {
              hour,
              minute,
              repeats: true,
              channelId: 'daily-quests-cyber',
            },
          });
        }
      }
    } catch (e) {
      console.warn('Erro ao agendar notificações Android:', e);
    }
  }

  // Disparo imediato de Pop-up Nativo + In-App
  async function triggerDailyQuestPopup(questOverride) {
    if (!state) return;
    const notif = state.notifications || {};
    if (!notif.masterEnabled && !questOverride) {
      Alert.alert(
        'Pop-ups Desativados',
        'A Chave Geral de Pop-ups de Daily Quests está OFF. Ative-a para receber notificações.'
      );
      return;
    }

    const activeDailies = (state.dailyQuests || []).filter(
      (q) => !q.completed && q.individualPopupEnabled
    );
    const chosen =
      questOverride ||
      activeDailies[Math.floor(Math.random() * activeDailies.length)];

    if (!chosen) {
      Alert.alert(
        'Sem Daily Quests com Pop-up',
        'Todas as Daily Quests com pop-up ativo já foram concluídas hoje!'
      );
      return;
    }

    setPopupQuest(chosen);

    await Notifications.scheduleNotificationAsync({
      content: {
        title: `⚡ DAILY QUEST PENDENTE // +10 XP [${chosen.attr}]`,
        body: chosen.clean,
        data: { questId: chosen.id },
      },
      trigger: null, // imediato
    });
  }

  async function toggleQuestCompletion(quest) {
    try {
      await fetch(`${apiHost}/api/quest/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clean: quest.clean,
          file: quest.file,
          line: quest.line,
          completed: !quest.completed,
        }),
      });
      await fetchState();
    } catch (e) {
      Alert.alert('Modo Offline', 'Conecte-se à mesma rede Wi-Fi do PC para sincronizar com o Obsidian.');
    }
  }

  async function toggleMasterPopups(enabled) {
    try {
      await fetch(`${apiHost}/api/notifications/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ masterEnabled: enabled }),
      });
      await fetchState();
    } catch (e) {
      Alert.alert('Erro', 'Não foi possível salvar no servidor.');
    }
  }

  async function toggleSingleQuestPopup(quest) {
    const newStatus = !quest.individualPopupEnabled;
    try {
      await fetch(`${apiHost}/api/notifications/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          questId: quest.id,
          questPopupEnabled: newStatus,
        }),
      });
      await fetchState();
    } catch (e) {
      Alert.alert('Erro', 'Não foi possível atualizar o pop-up desta Daily Quest.');
    }
  }

  async function createNewQuest() {
    if (!newTitle.trim()) return;
    try {
      await fetch(`${apiHost}/api/quest/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newTitle.trim(),
          due: newDue.trim(),
          type: newCategory,
          attr: newAttr,
          dest: 'both',
          popupEnabled: newPopupEnabled,
        }),
      });
      setNewTitle('');
      setNewDue('');
      setModalVisible(false);
      await fetchState();
    } catch (e) {
      Alert.alert('Erro', 'Falha ao criar quest no Obsidian.');
    }
  }

  const player = state?.player || { level: 5, curXP: 0, nextXP: 100, xpPct: 0, tier: { icon: '🦾', name: 'Street Kid' } };
  const masterOn = state?.notifications?.masterEnabled !== false;
  const dailies = state?.dailyQuests || [];
  const quests = state?.quests || [];

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#06070b" />

      {/* POP-UP HOLOGRÁFICO DE DAILY QUEST */}
      {popupQuest && (
        <View style={styles.popupBanner}>
          <View style={styles.popupHeader}>
            <Text style={styles.popupBadge}>🔔 POP-UP DE DAILY QUEST // [{popupQuest.attr}]</Text>
            <TouchableOpacity onPress={() => setPopupQuest(null)}>
              <Text style={styles.closeBtn}>✕</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.popupTitle}>{popupQuest.clean}</Text>
          <View style={styles.popupActions}>
            <TouchableOpacity
              style={[styles.btn, styles.btnGreen]}
              onPress={async () => {
                const q = popupQuest;
                setPopupQuest(null);
                await toggleQuestCompletion(q);
              }}
            >
              <Text style={styles.btnTextDark}>✔ CONCLUIR (+10 XP)</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.btn, styles.btnPink]}
              onPress={async () => {
                const q = popupQuest;
                setPopupQuest(null);
                await toggleSingleQuestPopup(q);
              }}
            >
              <Text style={styles.btnTextLight}>🔕 SILENCIAR ESTA</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* TOPBAR */}
      <View style={styles.topbar}>
        <View>
          <Text style={styles.brandTitle}>⚡ NIGHT CITY OS // CYBERDECK</Text>
          <Text style={styles.brandSub}>
            {online ? '🟢 SYNC OBSIDIAN ATIVO' : '🔴 MODO CACHE OFFLINE'} • HUD MOBILE
          </Text>
        </View>
        <TouchableOpacity style={styles.addBtn} onPress={() => setModalVisible(true)}>
          <Text style={styles.addBtnText}>➕ QUEST</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scroll}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={async () => {
              setRefreshing(true);
              await fetchState();
              setRefreshing(false);
            }}
            tintColor="#fcee0a"
          />
        }
      >
        {/* CARD DE NÍVEL E XP */}
        <View style={styles.heroCard}>
          <View style={styles.heroRow}>
            <View style={styles.lvlBox}>
              <Text style={styles.lvlNum}>{player.level}</Text>
              <Text style={styles.lvlLbl}>NÍVEL</Text>
            </View>
            <View style={{ flex: 1, marginLeft: 12 }}>
              <Text style={styles.classBadge}>{player.tier?.icon} {player.tier?.name}</Text>
              <Text style={styles.xpText}>
                XP: {player.curXP} / {player.nextXP} ({player.xpPct}%)
              </Text>
              <View style={styles.xpTrack}>
                <View style={[styles.xpFill, { width: `${player.xpPct || 0}%` }]} />
              </View>
            </View>
          </View>
        </View>

        {/* CENTRAL DE POP-UPS DE DAILY QUESTS (CHAVE GERAL + INDIVIDUAIS) */}
        <View style={styles.notifCard}>
          <View style={styles.notifRow}>
            <View style={{ flex: 1, paddingRight: 10 }}>
              <Text style={styles.notifTitle}>🔔 POP-UPS DE DAILY QUESTS</Text>
              <Text style={styles.notifSub}>
                Ative/desative todos os pop-ups ou escolha abaixo quais Daily Quests podem enviar alerta no celular.
              </Text>
            </View>
            <Switch
              value={masterOn}
              onValueChange={toggleMasterPopups}
              trackColor={{ false: '#333', true: '#00ff66' }}
              thumbColor={masterOn ? '#fcee0a' : '#888'}
            />
          </View>
          <TouchableOpacity
            style={styles.testPopupBtn}
            onPress={() => triggerDailyQuestPopup()}
          >
            <Text style={styles.testPopupText}>⚡ TESTAR POP-UP DE DAILY QUEST AGORA</Text>
          </TouchableOpacity>
        </View>

        {/* LISTA DE DAILY QUESTS COM SWITCH INDIVIDUAL DE POP-UP */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>🔄 DAILY QUESTS (+10 XP)</Text>
          <Text style={styles.sectionCount}>
            {dailies.filter((d) => d.completed).length}/{dailies.length}
          </Text>
        </View>

        {dailies.map((q) => (
          <View
            key={q.id}
            style={[styles.questCard, q.completed && styles.questCardDone]}
          >
            <TouchableOpacity
              style={styles.checkbox}
              onPress={() => toggleQuestCompletion(q)}
            >
              <Text style={styles.checkboxText}>{q.completed ? '✔' : ''}</Text>
            </TouchableOpacity>

            <View style={{ flex: 1 }}>
              <Text style={[styles.questTitle, q.completed && styles.questTitleDone]}>
                {q.clean}
              </Text>
              <View style={styles.tagRow}>
                <Text style={styles.tagAttr}>{q.attrIcon} {q.attr}</Text>
                <Text style={styles.tagXp}>+10 XP</Text>
              </View>
            </View>

            {/* Botão Individual para Ativar/Desativar Pop-up desta Daily Quest */}
            <TouchableOpacity
              style={[
                styles.bellChip,
                q.individualPopupEnabled && masterOn ? styles.bellOn : styles.bellOff,
              ]}
              onPress={() => toggleSingleQuestPopup(q)}
            >
              <Text
                style={[
                  styles.bellChipText,
                  q.individualPopupEnabled && masterOn ? { color: '#00ff66' } : { color: '#8892b0' },
                ]}
              >
                {q.individualPopupEnabled ? '🔔 POP-UP ON' : '🔕 SILENCIADA'}
              </Text>
            </TouchableOpacity>
          </View>
        ))}

        {/* BOSS FIGHTS & MAIN QUESTS */}
        <View style={[styles.sectionHeader, { marginTop: 18 }]}>
          <Text style={[styles.sectionTitle, { color: '#ff0055' }]}>
            👹 BOSS FIGHTS & MAIN QUESTS ({quests.filter((q) => !q.completed).length})
          </Text>
        </View>
        {quests.slice(0, 35).map((q) => (
          <View key={q.key} style={[styles.questCard, q.completed && styles.questCardDone]}>
            <TouchableOpacity
              style={styles.checkbox}
              onPress={() => toggleQuestCompletion(q)}
            >
              <Text style={styles.checkboxText}>{q.completed ? '✔' : ''}</Text>
            </TouchableOpacity>
            <View style={{ flex: 1 }}>
              <Text style={[styles.questTitle, q.completed && styles.questTitleDone]}>
                {q.clean}
              </Text>
              <View style={styles.tagRow}>
                <Text style={styles.tagAttr}>{q.typeIcon} {q.typeLabel} · {q.attr}</Text>
                <Text style={styles.tagXp}>+{q.xp} XP</Text>
              </View>
            </View>
          </View>
        ))}
      </ScrollView>

      {/* MODAL NOVA QUEST */}
      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalBox}>
            <Text style={styles.modalHeader}>➕ NOVA QUEST // OBSIDIAN SYNC</Text>
            <TextInput
              style={styles.input}
              placeholder="Descrição da tarefa ou quest..."
              placeholderTextColor="#666"
              value={newTitle}
              onChangeText={setNewTitle}
            />
            <TextInput
              style={styles.input}
              placeholder="Prazo opcional (ex: 15/11/2026)"
              placeholderTextColor="#666"
              value={newDue}
              onChangeText={setNewDue}
            />
            <View style={styles.notifRow}>
              <Text style={{ color: '#e8f0ff', fontSize: 13 }}>
                🔔 Permitir Pop-up de Notificação para esta Daily
              </Text>
              <Switch
                value={newPopupEnabled}
                onValueChange={setNewPopupEnabled}
                trackColor={{ false: '#333', true: '#00ff66' }}
              />
            </View>
            <View style={[styles.popupActions, { marginTop: 14 }]}>
              <TouchableOpacity
                style={[styles.btn, styles.btnPink]}
                onPress={() => setModalVisible(false)}
              >
                <Text style={styles.btnTextLight}>CANCELAR</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.btn, styles.btnGreen]}
                onPress={createNewQuest}
              >
                <Text style={styles.btnTextDark}>SALVAR QUEST</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#06070b' },
  topbar: {
    paddingTop: 44,
    paddingBottom: 12,
    paddingHorizontal: 16,
    backgroundColor: '#0d1018',
    borderBottomWidth: 2,
    borderBottomColor: '#fcee0a',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  brandTitle: { color: '#fcee0a', fontWeight: '900', fontSize: 15, letterSpacing: 1 },
  brandSub: { color: '#00f0ff', fontSize: 10, marginTop: 2 },
  addBtn: {
    backgroundColor: '#fcee0a',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 4,
  },
  addBtnText: { color: '#000', fontWeight: '900', fontSize: 11 },
  scroll: { flex: 1, padding: 14 },
  heroCard: {
    backgroundColor: '#0e121b',
    borderWidth: 1,
    borderColor: '#fcee0a',
    padding: 14,
    borderRadius: 6,
    marginBottom: 14,
  },
  heroRow: { flexDirection: 'row', alignItems: 'center' },
  lvlBox: {
    width: 60,
    height: 60,
    backgroundColor: '#fcee0a',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 4,
  },
  lvlNum: { color: '#000', fontSize: 26, fontWeight: '900' },
  lvlLbl: { color: '#000', fontSize: 9, fontWeight: '800' },
  classBadge: { color: '#00f0ff', fontWeight: '800', fontSize: 14, marginBottom: 4 },
  xpText: { color: '#e8f0ff', fontSize: 11, marginBottom: 6 },
  xpTrack: { height: 10, backgroundColor: '#1b2234', borderRadius: 3, overflow: 'hidden' },
  xpFill: { height: '100%', backgroundColor: '#00ff66' },
  notifCard: {
    backgroundColor: '#101521',
    borderWidth: 1,
    borderColor: '#00f0ff',
    padding: 12,
    borderRadius: 6,
    marginBottom: 16,
  },
  notifRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  notifTitle: { color: '#fcee0a', fontWeight: '900', fontSize: 13 },
  notifSub: { color: '#8892b0', fontSize: 11, marginTop: 2 },
  testPopupBtn: {
    marginTop: 10,
    backgroundColor: 'rgba(252,238,10,0.15)',
    borderWidth: 1,
    borderColor: '#fcee0a',
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 4,
  },
  testPopupText: { color: '#fcee0a', fontWeight: '800', fontSize: 11 },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
    alignItems: 'center',
  },
  sectionTitle: { color: '#00f0ff', fontWeight: '900', fontSize: 13 },
  sectionCount: { color: '#fcee0a', fontWeight: '800', fontSize: 12 },
  questCard: {
    backgroundColor: '#0f131d',
    borderLeftWidth: 3,
    borderLeftColor: '#00f0ff',
    padding: 12,
    marginBottom: 8,
    borderRadius: 4,
    flexDirection: 'row',
    alignItems: 'center',
  },
  questCardDone: { opacity: 0.5, borderLeftColor: '#00ff66' },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: '#00f0ff',
    marginRight: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxText: { color: '#00ff66', fontWeight: '900' },
  questTitle: { color: '#e8f0ff', fontSize: 13, fontWeight: '600' },
  questTitleDone: { textDecorationLine: 'line-through', color: '#8892b0' },
  tagRow: { flexDirection: 'row', marginTop: 4, gap: 6 },
  tagAttr: {
    color: '#00f0ff',
    fontSize: 10,
    fontWeight: '800',
    marginRight: 8,
  },
  tagXp: { color: '#fcee0a', fontSize: 10, fontWeight: '800' },
  bellChip: {
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 4,
    borderWidth: 1,
    marginLeft: 8,
  },
  bellOn: { borderColor: '#00ff66', backgroundColor: 'rgba(0,255,102,0.12)' },
  bellOff: { borderColor: '#444', backgroundColor: 'rgba(255,255,255,0.04)' },
  bellChipText: { fontSize: 10, fontWeight: '900' },
  popupBanner: {
    backgroundColor: '#121521',
    borderBottomWidth: 3,
    borderBottomColor: '#fcee0a',
    paddingTop: 42,
    paddingHorizontal: 16,
    paddingBottom: 14,
  },
  popupHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  popupBadge: { color: '#fcee0a', fontWeight: '900', fontSize: 11 },
  closeBtn: { color: '#ff0055', fontWeight: '900', fontSize: 16 },
  popupTitle: { color: '#fff', fontSize: 14, fontWeight: '700', marginBottom: 10 },
  popupActions: { flexDirection: 'row', gap: 10 },
  btn: { flex: 1, paddingVertical: 9, alignItems: 'center', borderRadius: 4 },
  btnGreen: { backgroundColor: '#00ff66' },
  btnPink: { backgroundColor: '#ff0055' },
  btnTextDark: { color: '#000', fontWeight: '900', fontSize: 11 },
  btnTextLight: { color: '#fff', fontWeight: '900', fontSize: 11 },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'center',
    padding: 20,
  },
  modalBox: {
    backgroundColor: '#0f131d',
    borderWidth: 2,
    borderColor: '#fcee0a',
    padding: 18,
    borderRadius: 6,
  },
  modalHeader: { color: '#fcee0a', fontWeight: '900', fontSize: 15, marginBottom: 12 },
  input: {
    backgroundColor: '#06070b',
    borderWidth: 1,
    borderColor: '#00f0ff',
    color: '#fff',
    padding: 10,
    borderRadius: 4,
    marginBottom: 12,
  },
});
