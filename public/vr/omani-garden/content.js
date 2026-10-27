// Content: a standalone garden experience (ازرع واحصد الثمرة), not tied to a numbered Grade-1
// science lesson. Every spoken line has a key. audio/manifest.json maps keys to recordings;
// lines without a recording fall back to the browser's Arabic speech synthesis.
window.LESSON = {
  character: { name: 'سَالِم' },

  // One pot per crop. angle: position in the front arc (degrees, 0 = straight ahead).
  // stage0: the growth stage (1-6) the pot already shows when the child first explores it —
  // matches the reference video/photos, where different pots were at different stages.
  pots: [
    { id: 'tomato', kind: 'bush', angle: -60, accent: '#d6172b', icon: '🍅', name: 'الطَّمَاطِمُ', stage0: 4,
      fruit: '#d63a2a', flower: '#f4e14a', about: 'الطَّمَاطِمُ نَبَاتٌ يَنْمُو سَرِيعًا، وَثِمَارُهُ حَمْرَاءُ عِنْدَ النُّضْجِ.' },
    { id: 'strawberry', kind: 'bush', angle: -20, accent: '#c8186a', icon: '🍓', name: 'الْفَرَاوْلَةُ', stage0: 4,
      fruit: '#e8355f', flower: '#ffffff', about: 'الْفَرَاوْلَةُ نَبَاتٌ قَصِيرٌ، وَثِمَارُهُ حَمْرَاءُ صَغِيرَةٌ لَذِيذَةٌ.' },
    { id: 'lemon', kind: 'tree', angle: 20, accent: '#e9c13a', icon: '🍋', name: 'اللَّيْمُونُ الْعُمَانِيُّ', stage0: 1,
      fruit: '#e9c13a', flower: '#ffffff', about: 'اللَّيْمُونُ الْعُمَانِيُّ شَجَرَةٌ مَشْهُورَةٌ فِي عُمَانَ، وَثِمَارُهُ تُجَفَّفُ وَتُسْتَخْدَمُ فِي الطَّبْخِ.' },
    { id: 'apple', kind: 'tree', angle: 60, accent: '#c8372a', icon: '🍎', name: 'التُّفَّاحُ', stage0: 3,
      fruit: '#c8372a', flower: '#f6c6d0', about: 'شَجَرَةُ التُّفَّاحِ تَحْتَاجُ وَقْتًا طَوِيلًا لِتُثْمِرَ، أَطْوَلَ مِنْ نَبَاتِ الطَّمَاطِمِ.' },
  ],

  // 6 growth stages, named generically (used for every crop's HUD/fact text).
  stages: ['بَذْرَةٌ', 'إِنْبَاتٌ', 'شَتْلَةٌ', 'نَبَاتٌ صَغِيرٌ', 'إِزْهَارٌ', 'ثِمَارٌ نَاضِجَةٌ'],

  // care rounds for mission 2 — which pot, and which of the 3 chips is correct for it this round
  careRounds: [
    { pot: 'lemon', need: 'water' },
    { pot: 'apple', need: 'sun' },
    { pot: 'strawberry', need: 'water' },
    { pot: 'tomato', need: 'soil' },
    { pot: 'strawberry', need: 'sun' },
    { pot: 'tomato', need: 'water' },
  ],

  lines: {
    hello: 'هلا والله فيكم يا أبطال! حيّاكم الله في المشتل العماني. اليوم بنتعلم نزرع ونعتني بالنباتات لين تكبر!',
    m1: 'شوف حولك! في أربع أصص فيها نباتات مختلفة. المس كل أصيص عشان تعرف وش فيه.',
    praise1: 'ما شاء الله عليك!',
    praise2: 'زين زين! كمّل.',
    praise3: 'شاطر! تعرّفت على نبتة جديدة.',
    half: 'نص الطريق! كمّل اكتشاف.',
    m1done: 'عفيه عليك! تعرّفت على كل النباتات. الحين خلّنا نعتني فيها عشان تكبر وتثمر!',
    m2: 'كل نبتة تحتاج عناية. انظر وش تحتاج، وامسك الإجابة الصحيحة.',
    right1: 'صح! ما شاء الله عليك!',
    right2: 'كفو! كبرت النبتة شوي!',
    right3: 'أحسنت يا بطل!',
    wrong1: 'قريب! فكّر شوي وجرّب مرة ثانية.',
    wrong2: 'ما عليه، شوف وش تحتاج النبتة زين.',
    harvestReady: 'واو! ثمارها نضجت! اقطفها حطها بالسلة.',
    harvestDone: 'عفيه عليك! قطفتها بوقتها الصح!',
    end: 'ما شاء الله عليك! تذكّر: النباتات تحتاج ماء وشمس وتربة عشان تكبر، والأشجار تاخذ وقت أطول من الخضار.',
    free: 'استمر تعتني بالنباتات على راحتك!',
    companionHatch: 'واو! فقس البيض! تعال شوف رفيقك الجديد!',
    companionGrow: 'رفيقك كبر شوي! استمر تكتشف عشان يكبر أكثر!',
    companionFull: 'ما شاء الله! رفيقك صار طير كامل يطير بقوة!',
    companionIntro: 'هذا رفيقك! يكبر كل ما تكتشف أشياء جديدة معي.',
    journalIntro: 'هذا دفترك! فيه كل شي اكتشفته بمغامراتك.',
    portalLine: 'تبي تطلع تزور البيئات المحلية؟ امشِ خلال البوابة!',
    need_water: 'الْمَاءُ', need_sun: 'الشَّمْسُ', need_soil: 'التُّرْبَةُ',
    // fact lines keyed f_<potId>, said when a pot is first discovered
    f_tomato: 'الطَّمَاطِمُ نَبَاتٌ يَنْمُو سَرِيعًا، وَثِمَارُهُ حَمْرَاءُ عِنْدَ النُّضْجِ.',
    f_strawberry: 'الْفَرَاوْلَةُ نَبَاتٌ قَصِيرٌ، وَثِمَارُهُ حَمْرَاءُ صَغِيرَةٌ لَذِيذَةٌ.',
    f_lemon: 'اللَّيْمُونُ الْعُمَانِيُّ شَجَرَةٌ مَشْهُورَةٌ فِي عُمَانَ، وَثِمَارُهُ تُسْتَخْدَمُ فِي الطَّبْخِ بَعْدَ أَنْ تُجَفَّفَ.',
    f_apple: 'شَجَرَةُ التُّفَّاحِ تَحْتَاجُ وَقْتًا طَوِيلًا لِتُثْمِرَ، أَطْوَلَ مِنْ نَبَاتِ الطَّمَاطِمِ.',
    falaj: 'هَذَا الْفَلَجُ! يُوَصِّلُ الْمَاءَ لِلنَّبَاتَاتِ، وَيَجِبُ أَنْ لَا نُسْرِفَ فِي اسْتِخْدَامِ مَائِهِ.',
    tools: 'هَذِهِ أَدَوَاتُ الزِّرَاعَةِ: مِجْرَفَةٌ لِحَفْرِ التُّرْبَةِ، وَبُذُورٌ مُلَوَّنَةٌ لِكُلِّ نَبْتَةٍ.',
  },
};
