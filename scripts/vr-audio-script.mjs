// Regenerates public/vr/<lesson>/audio/SCRIPT.md from the lesson's content.js.
// Usage: node scripts/vr-audio-script.mjs lesson-01-local-habitats
import { readFileSync, writeFileSync } from 'node:fs';
import vm from 'node:vm';

const lesson = process.argv[2] || 'lesson-01-local-habitats';
const dir = new URL(`../public/vr/${lesson}/`, import.meta.url);
const ctx = { window: {} };
vm.runInNewContext(readFileSync(new URL('content.js', dir), 'utf8'), ctx);
const L = ctx.window.LESSON;

const groups = [
  ['Salem (Omani dialect, child voice)', k => !/^((q|a|f|z|g|c|it)_|n\d)/.test(k)],
  ['Questions — Salem (dialect)', k => k.startsWith('q_')],
  ['Answers — clear Fusha', k => k.startsWith('a_')],
  ['Animal and plant facts — clear Fusha', k => k.startsWith('f_')],
  ['Habitat descriptions — clear Fusha', k => k.startsWith('z_')],
  ['Growing up — clear Fusha', k => k.startsWith('g_')],
  ['Counting — clear Fusha', k => k.startsWith('c_') || /^n\d$/.test(k)],
  ['Enclosure items — clear Fusha', k => k.startsWith('it_')],
];
let md = `# Voice script — ${lesson}\n\n` +
  'Record each line as `<key>.mp3` in this folder, then add the key to `manifest.json` ' +
  '(e.g. `["hello", "m1"]`). Lines not listed in the manifest fall back to the browser\'s speech synthesis.\n\n' +
  'Tips: one line per file, a short silence at both ends, mono 44.1 kHz, about 96 kbps MP3.\n' +
  'Educational lines (answers, facts, habitats) should be read in clear Fusha exactly as written;\n' +
  'Salem\'s lines are in Omani dialect — adjust wording to natural Omani speech before recording.\n';
for (const [title, test] of groups) {
  if (!Object.keys(L.lines).some(test)) continue;
  md += `\n## ${title}\n\n| key | text |\n|---|---|\n`;
  for (const [k, v] of Object.entries(L.lines)) if (test(k)) md += `| \`${k}\` | ${v} |\n`;
}
writeFileSync(new URL('audio/SCRIPT.md', dir), md);
console.log(`wrote ${Object.keys(L.lines).length} lines`);
