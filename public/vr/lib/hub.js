// Salem's Hub: small shared state that persists across lessons and days (localStorage, same
// origin for every /public/vr/<lesson>/ page). Powers the growing companion, the field journal,
// and the visit streak. No lesson needs to know its internals beyond this API.
window.SalemHub = (() => {
  const KEY = 'salemHub_v1';
  const STAGES = [0, 3, 8, 15]; // xp thresholds for companion stages 0..3
  const today = () => new Date().toISOString().slice(0, 10);

  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) { /* private mode / storage blocked */ }
    return { xp: 0, journal: {}, visits: {} };
  }
  function save(s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) { /* ignore */ } }

  let state = load();

  function addXp(n) { state.xp = Math.max(0, (state.xp || 0) + n); save(state); return state.xp; }
  function stage() { let s = 0; for (let i = 0; i < STAGES.length; i++) if (state.xp >= STAGES[i]) s = i; return s; }
  function xpToNext() { const s = stage(); return s >= STAGES.length - 1 ? null : STAGES[s + 1] - state.xp; }

  function recordDiscovery(lessonId, key, icon, label) {
    const k = lessonId + ':' + key;
    const isNew = !state.journal[k];
    state.journal[k] = { lessonId, key, icon, label, ts: Date.now() };
    save(state);
    if (isNew) addXp(1);
    return isNew;
  }
  function journalList() { return Object.values(state.journal).sort((a, b) => a.ts - b.ts); }
  function journalCount() { return Object.keys(state.journal).length; }

  function recordVisit(lessonId) {
    const list = state.visits[lessonId] || (state.visits[lessonId] = []);
    const t = today();
    if (!list.includes(t)) { list.push(t); save(state); addXp(2); return true; }
    return false;
  }
  function daysVisited() { const days = new Set(); for (const l of Object.values(state.visits)) for (const d of l) days.add(d); return days.size; }

  return { addXp, stage, xpToNext, xp: () => state.xp, recordDiscovery, journalList, journalCount, recordVisit, daysVisited, STAGES };
})();
