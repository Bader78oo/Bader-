// Content: a standalone garden experience (ازرع واحصد الثمرة), not tied to a numbered Grade-1
// science lesson. Every spoken line has a key. audio/manifest.json maps keys to recordings;
// lines without a recording fall back to the browser's Arabic speech synthesis.
window.LESSON = {
  character: { name: 'سَالِم' },

  // One pot per crop. angle: position in the front arc (degrees, 0 = straight ahead).
  // Every pot starts empty — the child digs, plants and waters it themself before it grows.
  pots: [
    { id: 'tomato', kind: 'bush', angle: -60, accent: '#d6172b', icon: '🍅', name: 'الطَّمَاطِمُ',
      fruit: '#d63a2a', flower: '#f4e14a', about: 'الطَّمَاطِمُ نَبَاتٌ يَنْمُو سَرِيعًا، وَثِمَارُهُ حَمْرَاءُ عِنْدَ النُّضْجِ.' },
    { id: 'strawberry', kind: 'bush', angle: -20, accent: '#c8186a', icon: '🍓', name: 'الْفَرَاوْلَةُ',
      fruit: '#e8355f', flower: '#ffffff', about: 'الْفَرَاوْلَةُ نَبَاتٌ قَصِيرٌ، وَثِمَارُهُ حَمْرَاءُ صَغِيرَةٌ لَذِيذَةٌ.' },
    { id: 'lemon', kind: 'tree', angle: 20, accent: '#e9c13a', icon: '🍋', name: 'اللَّيْمُونُ الْعُمَانِيُّ',
      fruit: '#e9c13a', flower: '#ffffff', about: 'اللَّيْمُونُ الْعُمَانِيُّ شَجَرَةٌ مَشْهُورَةٌ فِي عُمَانَ، وَثِمَارُهُ تُجَفَّفُ وَتُسْتَخْدَمُ فِي الطَّبْخِ.' },
    { id: 'apple', kind: 'tree', angle: 60, accent: '#c8372a', icon: '🍎', name: 'التُّفَّاحُ',
      fruit: '#c8372a', flower: '#f6c6d0', about: 'شَجَرَةُ التُّفَّاحِ تَحْتَاجُ وَقْتًا طَوِيلًا لِتُثْمِرَ، أَطْوَلَ مِنْ نَبَاتِ الطَّمَاطِمِ.' },
  ],

  // 6 growth stages, named generically (used for every crop's HUD/fact text).
  stages: ['بَذْرَةٌ', 'إِنْبَاتٌ', 'شَتْلَةٌ', 'نَبَاتٌ صَغِيرٌ', 'إِزْهَارٌ', 'ثِمَارٌ نَاضِجَةٌ'],

  lines: {
    hello: 'هلا والله فيكم يا أبطال! حيّاكم الله في المشتل العماني. اليوم بنتعلم نزرع ونعتني بالنباتات لين تكبر!',
    m1: 'هذي طاولة الأدوات! خذ المجرفة واحفر في أول أصيص، ثم ازرع بذرة واسقها بالماء.',
    praise1: 'ما شاء الله عليك!',
    praise2: 'زين زين! كمّل.',
    praise3: 'شاطر! تعرّفت على نبتة جديدة.',
    half: 'زرعت نص الأصص! كمّل الباقي بنفس الطريقة: احفر، ازرع، اسقِ.',
    m1done: 'عفيه عليك! زرعت كل النباتات! الحين راقبها تكبر شوي شوي.',
    right1: 'صح! ما شاء الله عليك!',
    right2: 'كفو! زرعتها زين!',
    right3: 'أحسنت يا بطل!',
    harvestReady: 'واو! ثمارها نضجت! اقطفها حطها بالسلة.',
    harvestDone: 'عفيه عليك! قطفتها بوقتها الصح!',
    end: 'ما شاء الله عليك! تذكّر: النباتات تحتاج ماء وشمس وتربة عشان تكبر، والأشجار تاخذ وقت أطول من الخضار.',
    free: 'استمر تعتني بالنباتات على راحتك!',
    rewaterPrompt: 'عطشانة مرة ثانية! اسقها عشان تكمل تكبر.',
    portalLine: 'تبي تطلع تزور البيئات المحلية؟ امشِ خلال البوابة!',
    // fact lines keyed f_<potId>, said the moment the child plants that seed
    f_tomato: 'الطَّمَاطِمُ نَبَاتٌ يَنْمُو سَرِيعًا، وَثِمَارُهُ حَمْرَاءُ عِنْدَ النُّضْجِ.',
    f_strawberry: 'الْفَرَاوْلَةُ نَبَاتٌ قَصِيرٌ، وَثِمَارُهُ حَمْرَاءُ صَغِيرَةٌ لَذِيذَةٌ.',
    f_lemon: 'اللَّيْمُونُ الْعُمَانِيُّ شَجَرَةٌ مَشْهُورَةٌ فِي عُمَانَ، وَثِمَارُهُ تُسْتَخْدَمُ فِي الطَّبْخِ بَعْدَ أَنْ تُجَفَّفَ.',
    f_apple: 'شَجَرَةُ التُّفَّاحِ تَحْتَاجُ وَقْتًا طَوِيلًا لِتُثْمِرَ، أَطْوَلَ مِنْ نَبَاتِ الطَّمَاطِمِ.',
    falaj: 'هَذَا الْفَلَجُ! يُوَصِّلُ الْمَاءَ لِلنَّبَاتَاتِ، وَيَجِبُ أَنْ لَا نُسْرِفَ فِي اسْتِخْدَامِ مَائِهِ.',
    tools: 'هَذِهِ أَدَوَاتُ الزِّرَاعَةِ: مِجْرَفَةٌ لِحَفْرِ التُّرْبَةِ، وَبُذُورٌ مُلَوَّنَةٌ لِكُلِّ نَبْتَةٍ، وَإِبْرِيقُ مَاءٍ لِلسَّقْيِ.',
  },
};
