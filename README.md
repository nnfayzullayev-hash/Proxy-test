# 📚 Test Telegram Bot (v2 — PDF asosida)

Testlarni PDF fayl sifatida tarqatuvchi, chiptalarni admin qo'lda/avtomatik beradigan Telegram bot.

## 🧩 Yangi ish jarayoni

- **📰 Yangiliklar** — barcha foydalanuvchilar ko'radi; admin istalgan payt qo'shadi/o'chiradi
- **🎫 Chipta sotib olish** — foydalanuvchiga faqat karta raqami va admin niki ko'rsatiladi; to'lovni shaxsan admin bilan kelishadi
- **📝 Testlar** — foydalanuvchi kod kiritadi → vaqti kelgan test PDF holida yuboriladi → yechib, javobini **istalgan ko'rinishda** (rasm/hujjat/matn) qaytaradi → admin(lar)ga avtomatik yo'naltiriladi

## 👨‍💼 Admin buyruqlari

| Buyruq | Vazifasi |
|---|---|
| `/addnews` | Yangilik qo'shish |
| `/delnews` | Yangilikni o'chirish (ro'yxatdan tanlab) |
| `/addtests` | Yangi test qo'shish (nomi, tavsifi, PDF fayl) |
| `/addtesttime` | Mavjud testga boshlanish sanasi/vaqtini belgilash |
| `/addtickets` | Foydalanuvchiga **qo'lda** yozilgan kod berish |
| `/addusers` | Foydalanuvchiga **avtomatik** generatsiya qilingan kod berish |
| `/addcardnumber` | To'lov uchun karta raqamini o'zgartirish |
| `/addnickname` | To'lov uchun ko'rsatiladigan Telegram nikni o'zgartirish |
| `/javoblar` | Yuborilgan javoblar ro'yxati (audit uchun) |

⚠️ **Muhim cheklov:** `/addtickets` yoki `/addusers` bilan kod berish uchun, o'sha foydalanuvchi avvaldan botga hech bo'lmasa bir marta **`/start`** yozgan bo'lishi shart — aks holda bot unga xabar yubora olmaydi (Telegram qoidasi).

## 🛠️ Texnologiyalar

```
Python 3.12.7
├── aiogram        → Telegram bot freymvorki
├── aiohttp        → keep-alive veb-server (Render bepul tarifi uchun)
├── PostgreSQL     → ma'lumotlar bazasi
├── asyncpg        → PostgreSQL bilan asinxron aloqa
└── python-dotenv  → .env orqali maxfiy sozlamalar
```

## 📁 Loyiha tuzilishi

```
.
├── bot.py                    — botni ishga tushiruvchi asosiy fayl (+ keep-alive server)
├── config.py                 — .env dan sozlamalarni o'qiydi
├── database.py                — PostgreSQL jadvallari va so'rovlar
├── requirements.txt
├── .python-version             — 3.12.7
├── .env.example
├── .gitignore
│
├── handlers/
│   ├── start.py                 — /start, asosiy menyu, admin uchun buyruqlar ro'yxati
│   ├── news.py                  — yangiliklarni ko'rsatish
│   ├── tickets.py                — "Chipta sotib olish" — karta+nik ko'rsatish
│   ├── tests.py                   — kod kiritish → PDF yuborish → javob qabul qilish
│   └── admin.py                    — barcha /add... buyruqlari
│
└── services/
    ├── ticket_service.py           — kod generatsiyasi/tekshiruvi
    ├── test_service.py              — test yaratish, vaqt tekshiruvi
    └── settings_service.py           — karta raqami / nik
```

## ⚙️ O'rnatish

```bash
python3.12 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`.env` faylini `.env.example`dan nusxalab, o'z ma'lumotlaringizni kiriting:

```bash
cp .env.example .env
```

| O'zgaruvchi | Tavsif |
|---|---|
| `BOT_TOKEN` | @BotFather'dan olingan token |
| `ADMIN_IDS` | Admin(lar)ning Telegram ID(lari), vergul bilan: `111,222` |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL ulanish ma'lumotlari |

⚠️ **Baza haqida eslatma:** Agar avvalgi (eski) tuzilishdagi bazadan foydalanayotgan bo'lsangiz, jadvallar tuzilishi butunlay o'zgargani uchun **yangi, bo'sh PostgreSQL baza** yarating (yoki eski jadvallarni `DROP TABLE`qiling) — aks holda `column does not exist` kabi xatolar chiqishi mumkin.

Ishga tushirish:

```bash
python bot.py
```

## ☁️ Render'da deploy qilish

1. GitHub'ga yuklang — fayllar repo tugida to'g'ridan-to'g'ri turishi kerak
2. Render'da **New → Web Service**
3. Sozlamalar:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Root Directory:** bo'sh
   - **Auto-Deploy:** **On** (muhim — aks holda GitHub'dagi o'zgarishlar avtomatik yetib bormaydi)
4. **Environment** bo'limiga `BOT_TOKEN`, `ADMIN_IDS`, `DB_*`ni kiriting
5. PostgreSQL bazasini ulang (yangi, bo'sh baza tavsiya etiladi)
6. Bepul tarifda uxlab qolmasligi uchun [UptimeRobot](https://uptimerobot.com) orqali xizmat manzilingizga har 5 daqiqada ping yuboradigan monitor sozlang

## 📌 Ishlatish tartibi (qisqacha)

1. Admin `/addtests` orqali test qo'shadi (nom, tavsif, PDF)
2. Admin `/addtesttime` orqali testga vaqt belgilaydi
3. Admin `/addcardnumber` va `/addnickname` orqali to'lov ma'lumotlarini kiritadi
4. Foydalanuvchi botga yozadi, "🎫 Chipta sotib olish" orqali karta+nikni ko'radi, to'lovni admin bilan shaxsan kelishadi
5. Admin to'lovni tasdiqlagach, `/addtickets` (qo'lda kod) yoki `/addusers` (avtomatik kod) orqali foydalanuvchiga kod beradi
6. Foydalanuvchi belgilangan vaqtda "📝 Testlar" orqali kodni kiritadi, PDF testni oladi, yechib, javobini yuboradi
7. Admin `/javoblar` orqali kelgan javoblarni kuzatadi (har bir javob kelganda ham darhol xabar keladi)
