# خلاصه یکپارچه پروژه NSFWBOT

## 1) این اپ چیست؟

این پروژه یک ربات تلگرام مبتنی بر هوش مصنوعی است که این اجزا را با هم ارائه می‌دهد:

- ربات گفتگو در تلگرام (متن/تصویر/ویدیو)
- پنل ادمین وب (Flask) برای مدیریت کامل
- سیستم پرداخت (Telegram Stars و TON)
- سیستم شخصیت (Character) برای سبک پاسخ‌دهی متفاوت
- تاریخچه گفتگو در دیتابیس (SQLite)

---

## 2) چه ویژگی‌هایی دارد؟

### هسته ربات
- پاسخ‌دهی AI با Venice API
- پشتیبانی از پیام متنی، عکس، و ویدیو
- منوی تعاملی داخل تلگرام
- مدیریت زبان/ترجمه

### سیستم شخصیت (Character)
- هر کاربر می‌تواند کاراکتر دلخواه انتخاب/تعویض کند (از منوی ربات)
- هر کاراکتر شامل:
  - نام
  - شرح (مثلاً سن، جنسیت، شغل، لحن)
  - System Prompt اختصاصی
- هنگام چت، System Prompt همان کاراکتر همراه تاریخچه ارسال می‌شود

### حافظه گفتگو
- حافظه به‌صورت per-user و per-character ثبت می‌شود
- برای هر `(user, character)` فقط 50 رکورد آخر نگه داشته می‌شود
- رکوردهای قدیمی‌تر به‌صورت خودکار prune می‌شوند

### پنل ادمین
- مدیریت کاربران، پکیج‌ها، تنظیمات، تراکنش‌ها
- ساخت/ویرایش/حذف کاراکتر
- تست اتصال Bot/API

### پرداخت
- Stars و TON
- حالت تست/شبیه‌سازی
- مانیتورینگ وضعیت تراکنش

---

## 3) چه تنظیماتی لازم است؟

> منطق فعلی پروژه DB-Only برای تنظیمات اپ است (توکن‌ها/مدل/API از دیتابیس خوانده می‌شوند).

### تنظیمات کلیدی داخل دیتابیس (`admin_settings`)
- `bot_token`
- `ai_api_key` یا `venice_inference_key`
- `ai_model` (پیشنهادی: `venice-uncensored`)
- `ai_base_url` (پیش‌فرض: `https://api.venice.ai/api/v1`)
- `admin_username` / `admin_password`
- `dashboard_host` / `dashboard_port`

### تنها ENV هایی که بهتر است نگه دارید
- `DATABASE_PATH` (مسیر فایل دیتابیس)
- `PORT` (فقط برای محیط‌های هاستی مثل Railway)

---

## 4) چطور اجرا شود (Run) در محیط‌های مختلف؟

## لوکال (Windows/Linux)
1. نصب وابستگی‌ها:
   - `pip install -r requirements.txt`
2. اجرا:
   - کل استک: `python start_bot.py start`
   - فقط بات: `python start_bot.py bot-only`
   - فقط داشبورد: `python start_bot.py dashboard-only`
3. ورود به داشبورد و ست‌کردن تنظیمات در DB

## PythonAnywhere
- Dashboard را به‌صورت Web App بالا بیاور
- Bot را به‌صورت Always-on Task اجرا کن:
  - `python start_bot.py bot-only`
- `DATABASE_PATH` را روی مسیر DB واقعی در هاست تنظیم کن

## Railway
- سرویس را deploy کن
- Volume به مسیر دیتابیس mount کن
- `DATABASE_PATH=/app/data/bot_database.db`
- چون `PORT` توسط Railway تزریق می‌شود، داشبورد روی همان پورت bind می‌شود

---

## 5) چطور دیپلوی شود در محیط‌های مختلف؟

## A) Railway (پیشنهادی برای شروع سریع)
1. Push به GitHub
2. Deploy از GitHub در Railway
3. Volume اضافه کن
4. `DATABASE_PATH` را روی مسیر volume تنظیم کن
5. سرویس را ری‌استارت کن
6. تنظیمات را از داشبورد ذخیره کن

## B) PythonAnywhere
1. پروژه را clone/upload کن
2. venv بساز و dependencies نصب کن
3. Web App را به `admin_dashboard.app` وصل کن
4. Always-on Task برای bot-only تعریف کن
5. `DATABASE_PATH` را تنظیم کن

## C) Docker / VPS
1. ایمیج را build/run کن
2. فایل دیتابیس را روی persistent storage نگه دار
3. لاگ و health check را مانیتور کن

---

## پیشنهاد ساختار عملیاتی (Production)

- لوکال: کانفیگ کامل در داشبورد + تست
- انتقال `bot_database.db` به سرور
- ست‌کردن فقط `DATABASE_PATH` (و `PORT` در هاست‌های لازم)
- اجرای سرویس و بررسی لاگ‌ها

---

## چک‌لیست نهایی قبل پابلیش

- [ ] `bot_token` در DB ذخیره شده
- [ ] `ai_api_key/venice_inference_key` در DB ذخیره شده
- [ ] حداقل یک کاراکتر فعال موجود است
- [ ] داشبورد login امن (پسورد پیش‌فرض تغییر کند)
- [ ] مسیر دیتابیس persistent است
- [ ] ربات در تلگرام با `/start` پاسخ می‌دهد

