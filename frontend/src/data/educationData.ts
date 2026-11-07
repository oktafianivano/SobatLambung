import { EducationArticle, FoodCategory } from '../types';

export const EDUCATION_ARTICLES: EducationArticle[] = [
  {
    id: 'gastritis',
    title: 'Gastritis (Penyakit Maag)',
    subtitle: 'Peradangan pada Lapisan Mukosa Lambung',
    definition:
      'Gastritis terjadi ketika lapisan pelindung lambung (mukosa) mengalami iritasi atau peradangan. Asam lambung yang pekat kemudian langsung mengikis dinding lambung, menimbulkan rasa nyeri yang khas.',
    studentCauses: [
      'Sering melewatkan sarapan pagi karena terburu-buru kuliah jam 07:00.',
      'Konsumsi kopi pekat / minuman berkafein saat lambung masih kosong.',
      'Stres akademik tinggi saat pekan ujian (UTS/UAS), tugas akhir, atau praktikum.',
      'Sering mengonsumsi mie instan pedas atau gorengan berminyak saat larut malam.',
    ],
    symptoms: [
      'Nyeri perih atau sensasi panas menggerus pada area ulu hati (epigastrium).',
      'Rasa begah, kembung, dan cepat kenyang meski baru makan sedikit.',
      'Mual, terkadang disertai muntah cairan bening/kekuningan.',
      'Sering bersendawa dengan rasa asam di mulut.',
    ],
    medicalTips: [
      'Terapkan pola makan "Small Frequent Meals" (porsi sedang tetapi teratur 3 kali sehari diselingi camilan sehat).',
      'Hindari perut kosong lebih dari 4-5 jam di siang hari.',
      'Kendalikan stres dengan manajemen waktu istirahat dan teknik relaksasi pernapasan.',
    ],
  },
  {
    id: 'gerd',
    title: 'GERD (Gastroesophageal Reflux Disease)',
    subtitle: 'Asam Lambung Naik Membalik ke Kerongkongan',
    definition:
      'GERD adalah gangguan pencernaan kronis ketika asam lambung mengalir balik ke kerongkongan karena melemahnya cincin otot pemisah (sfingter esofagus bawah / LES). Akibatnya, kerongkongan teriritasi oleh zat asam.',
    studentCauses: [
      'Kebiasaan langsung rebahan atau tidur setelah makan mie instan/nasi padang di kos.',
      'Pola tidur berantakan (begadang semalaman lalu tidur siang dengan perut terisi makanan berat).',
      'Kebiasaan memakai celana atau sabuk yang terlalu ketat menekan lambung.',
      'Konsumsi minuman bersoda dan makanan berlemak tinggi saat begadang.',
    ],
    symptoms: [
      'Sensasi panas terbakar di dada (Heartburn) yang menjalar ke leher.',
      'Regurgitasi: cairan asam atau pahit naik tiba-tiba ke kerongkongan dan mulut.',
      'Sensasi seperti ada makanan atau lendir mengganjal di tenggorokan (Globus hystericus).',
      'Batuk kering kronis, suara serak di pagi hari, atau erosi enamel gigi.',
    ],
    medicalTips: [
      'Wajib beri jeda minimal 2 hingga 3 jam antara selesai makan malam dan waktu berbaring/tidur.',
      'Tinggikan posisi kepala dan punggung atas sekitar 15-20 cm menggunakan bantal baji saat tidur.',
      'Hindari pemicu relaksasi katup LES: cokelat, peppermint, kopi, alkohol, dan makanan pedas berlemak.',
    ],
  },
];

export const FOOD_CATEGORIES: FoodCategory[] = [
  {
    id: 'safe-carbs',
    title: 'Karbohidrat Ramah & Menenangkan Lambung',
    type: 'recommended',
    description: 'Mudah dicerna lambung dan menyerap kelebihan asam lambung tanpa memicu gas.',
    items: [
      { name: 'Bubur Ayam & Nasi Tim Hangat', reason: 'Tekstur lembut tidak membebani kerja mekanik lambung yang sedang meradang.' },
      { name: 'Oatmeal (Havermut)', reason: 'Mengandung serat larut beta-glukan yang melapisi dinding lambung dan memberi rasa kenyang stabil.' },
      { name: 'Kentang Rebus / Tumbuk', reason: 'Memiliki sifat basa alami yang menetralkan keasaman cairan lambung.' },
      { name: 'Roti Gandum Utuh Rendah Gula', reason: 'Menyerap asam berlebih di rongga lambung.' },
    ],
  },
  {
    id: 'safe-protein',
    title: 'Protein Rendah Lemak & Mudah Dicerna',
    type: 'recommended',
    description: 'Membantu regenerasi sel mukosa lambung tanpa memperlambat pengosongan lambung.',
    items: [
      { name: 'Dada Ayam Kukus / Rebus', reason: 'Tinggi protein murni dan sangat rendah lemak jenuh.' },
      { name: 'Tahu & Tempe Kukus / Bacem', reason: 'Protein nabati fermentasi yang ramah mikrobioma usus dan mudah diserap.' },
      { name: 'Ikan Air Tawar (Nila/Gabus/Gurame)', reason: 'Ikan gabus kaya albumin yang mempercepat penyembuhan luka tukak lambung.' },
      { name: 'Putih Telur Rebus', reason: 'Sumber protein murni tanpa lemak yang memicu pengeluaran empedu berlebih.' },
    ],
  },
  {
    id: 'avoid-spicy-fatty',
    title: 'Makanan Pantangan Utama Mahasiswa',
    type: 'avoid',
    description: 'Memicu sekresi asam lambung ekstrem dan mengendurkan katup pemisah kerongkongan.',
    items: [
      { name: 'Makanan Super Pedas (Seblak, Mie Level, Sambal Korek)', reason: 'Capsaicin mengiritasi langsung mukosa lambung dan memicu kram lambung.' },
      { name: 'Gorengan Berminyak / Santan Kental', reason: 'Lemak memperlambat pengosongan lambung (gastric emptying) sehingga memicu reflux naik.' },
      { name: 'Kopi Hitam / Minuman Energi saat Perut Kosong', reason: 'Kafein merangsang produksi hormon gastrin yang memacu produksi asam HCl.' },
      { name: 'Minuman Bersoda & Berkarbonasi', reason: 'Menghasilkan gas CO2 yang meregangkan lambung dan memaksa katup LES terbuka.' },
    ],
  },
];
