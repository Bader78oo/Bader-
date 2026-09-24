// Render overlay.html into a transparent PNG sequence (ov/0000.png ...).
// Usage (from the work dir, which holds overlay.html, brand/, icons/, sb.json, words.json):
//   NODE_PATH=$(npm root -g) node frames.js sb.json
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const sb = JSON.parse(fs.readFileSync(process.argv[2] || 'sb.json', 'utf8'));
  const words = sb.words ? JSON.parse(fs.readFileSync(sb.words, 'utf8')) : [];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: sb.width, height: sb.height } });
  await p.addInitScript(({ SB, W }) => { window.SB = SB; window.WORDS = W; }, { SB: sb, W: words });
  await p.goto('file://' + process.cwd() + '/overlay.html', { waitUntil: 'networkidle' });
  await p.evaluate(async () => { await document.fonts.ready; });
  if (!(await p.evaluate(() => document.fonts.check('900 50px Cairo')))) console.warn('WARN: Cairo font not loaded, falling back');

  // Pre-decode every icon so no frame renders a half-loaded image.
  const icons = new Set(['circle-check']);
  (sb.captions || []).forEach(c => c.icon && icons.add(c.icon));
  ((sb.checklist || {}).items || []).forEach(c => icons.add(c.icon));
  if (sb.cta && sb.cta.icon) icons.add(sb.cta.icon);
  await p.evaluate(async names => {
    await Promise.all(names.map(n => new Promise(r => { const i = new Image(); i.onload = i.onerror = r; i.src = 'icons/' + n + '.svg'; })));
  }, [...icons]);

  fs.mkdirSync('ov', { recursive: true });
  const n = Math.round(sb.duration * sb.fps);
  for (let i = 0; i < n; i++) {
    await p.evaluate(t => window.render(t), i / sb.fps);
    await p.screenshot({ path: `ov/${String(i).padStart(4, '0')}.png`, omitBackground: true });
  }
  await b.close();
  console.log('overlay frames:', n);
})();
