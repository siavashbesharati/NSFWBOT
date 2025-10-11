"""
Multi-language translation system for the AI Bot
Supporting: English, Persian, Turkish, Arabic, Russian, Spanish
"""

# Language codes and their display names with flags
LANGUAGES = {
    'en': {'name': 'English', 'flag': '🇺🇸', 'native': 'English'},
    'fa': {'name': 'Persian', 'flag': '🇮🇷', 'native': 'فارسی'},
    'tr': {'name': 'Turkish', 'flag': '🇹🇷', 'native': 'Türkçe'},
    'ar': {'name': 'Arabic', 'flag': '🇸🇦', 'native': 'العربية'},
    'ru': {'name': 'Russian', 'flag': '🇷🇺', 'native': 'Русский'},
    'es': {'name': 'Spanish', 'flag': '🇪🇸', 'native': 'Español'}
}

# Translation dictionary
TRANSLATIONS = {
    # Welcome messages
    'welcome_title': {
        'en': '🤖 Welcome to the Uncensored AI Bot',
        'fa': '🤖 به ربات هوش مصنوعی بدون سانسور خوش آمدید',
        'tr': '🤖 Sansürsüz AI Botuna Hoş Geldiniz',
        'ar': '🤖 مرحباً بك في بوت الذكاء الاصطناعي غير المقيد',
        'ru': '🤖 Добро пожаловать в бота ИИ без цензуры',
        'es': '🤖 Bienvenido al Bot de IA Sin Censura'
    },
    
    'welcome_description': {
        'en': '''🚀 **Experience True AI Freedom!**

🔥 **What makes this bot special:**
• 💬 **Uncensored conversations** - No topic restrictions
• 🧠 **Advanced AI models** - Latest technology
• 🎯 **Honest answers** - Raw, unfiltered responses
• 🌍 **Multi-language support** - Your language, your way
• ⚡ **Instant responses** - No waiting

🎁 **Free starter credits included!**

Choose your language to continue:''',
        'fa': '''🚀 **آزادی واقعی هوش مصنوعی را تجربه کنید!**

🔥 **ویژگی‌های منحصر به فرد:**
• 💬 **گفتگوی بدون سانسور** - هیچ محدودیت موضوعی
• 🧠 **مدل‌های پیشرفته AI** - آخرین تکنولوژی
• 🎯 **پاسخ‌های صادقانه** - پاسخ‌های خام و بدون فیلتر
• 🌍 **پشتیبانی چند زبانه** - زبان شما، روش شما
• ⚡ **پاسخ فوری** - بدون انتظار

🎁 **اعتبار رایگان شروع گنجانده شده!**

زبان خود را برای ادامه انتخاب کنید:''',
        'tr': '''🚀 **Gerçek AI Özgürlüğünü Yaşayın!**

🔥 **Bu botu özel kılan özellikler:**
• 💬 **Sansürsüz sohbetler** - Konu kısıtlaması yok
• 🧠 **Gelişmiş AI modelleri** - En son teknoloji
• 🎯 **Dürüst cevaplar** - Ham, filtresiz yanıtlar
• 🌍 **Çok dil desteği** - Diliniz, yönteminiz
• ⚡ **Anında yanıtlar** - Bekleme yok

🎁 **Ücretsiz başlangıç kredileri dahil!**

Devam etmek için dilinizi seçin:''',
        'ar': '''🚀 **اختبر حرية الذكاء الاصطناعي الحقيقية!**

🔥 **ما يجعل هذا البوت مميزاً:**
• 💬 **محادثات غير مقيدة** - لا توجد قيود على المواضيع
• 🧠 **نماذج ذكاء اصطناعي متقدمة** - أحدث التقنيات
• 🎯 **إجابات صادقة** - ردود خام وغير مفلترة
• 🌍 **دعم متعدد اللغات** - لغتك، طريقتك
• ⚡ **ردود فورية** - بلا انتظار

🎁 **أرصدة مجانية للبداية مضمنة!**

اختر لغتك للمتابعة:''',
        'ru': '''🚀 **Испытайте истинную свободу ИИ!**

🔥 **Что делает этого бота особенным:**
• 💬 **Разговоры без цензуры** - Никаких ограничений тем
• 🧠 **Продвинутые модели ИИ** - Новейшие технологии
• 🎯 **Честные ответы** - Сырые, нефильтрованные ответы
• 🌍 **Многоязычная поддержка** - Ваш язык, ваш способ
• ⚡ **Мгновенные ответы** - Без ожидания

🎁 **Бесплатные стартовые кредиты включены!**

Выберите свой язык для продолжения:''',
        'es': '''🚀 **¡Experimenta la Verdadera Libertad de IA!**

🔥 **Lo que hace especial a este bot:**
• 💬 **Conversaciones sin censura** - Sin restricciones de tema
• 🧠 **Modelos de IA avanzados** - Última tecnología
• 🎯 **Respuestas honestas** - Respuestas crudas y sin filtrar
• 🌍 **Soporte multiidioma** - Tu idioma, tu manera
• ⚡ **Respuestas instantáneas** - Sin espera

🎁 **¡Créditos gratuitos de inicio incluidos!**

Elige tu idioma para continuar:'''
    },
    
    'language_selection_prompt': {
        'en': '🌍 Please select your preferred language:',
        'fa': '🌍 لطفاً زبان مورد نظر خود را انتخاب کنید:',
        'tr': '🌍 Lütfen tercih ettiğiniz dili seçin:',
        'ar': '🌍 يرجى اختيار لغتك المفضلة:',
        'ru': '🌍 Пожалуйста, выберите предпочитаемый язык:',
        'es': '🌍 Por favor, selecciona tu idioma preferido:'
    },
    
    'language_set': {
        'en': '✅ Language set to English! Welcome to the uncensored AI experience.',
        'fa': '✅ زبان به فارسی تنظیم شد! به تجربه هوش مصنوعی بدون سانسور خوش آمدید.',
        'tr': '✅ Dil Türkçe olarak ayarlandı! Sansürsüz AI deneyimine hoş geldiniz.',
        'ar': '✅ تم تعيين اللغة إلى العربية! مرحباً بك في تجربة الذكاء الاصطناعي غير المقيد.',
        'ru': '✅ Язык установлен на русский! Добро пожаловать в опыт ИИ без цензуры.',
        'es': '✅ ¡Idioma establecido en español! Bienvenido a la experiencia de IA sin censura.'
    },
    
    # Menu commands
    'help': {
        'en': 'Help',
        'fa': 'راهنما',
        'tr': 'Yardım',
        'ar': 'مساعدة',
        'ru': 'Помощь',
        'es': 'Ayuda'
    },
    
    'dashboard': {
        'en': 'Dashboard',
        'fa': 'داشبورد',
        'tr': 'Panel',
        'ar': 'لوحة التحكم',
        'ru': 'Панель',
        'es': 'Panel'
    },
    
    'packages': {
        'en': 'Packages',
        'fa': 'بسته‌ها',
        'tr': 'Paketler',
        'ar': 'الباقات',
        'ru': 'Пакеты',
        'es': 'Paquetes'
    },
    
    'reset': {
        'en': 'Reset',
        'fa': 'بازنشانی',
        'tr': 'Sıfırla',
        'ar': 'إعادة تعيين',
        'ru': 'Сброс',
        'es': 'Reiniciar'
    },
    
    # Help messages
    'help_text': {
        'en': '''🆘 **Uncensored AI Bot Commands**

🔥 **What makes us different:**
• No topic restrictions or content filters
• Raw, honest AI responses
• Advanced conversation capabilities

📋 **Available Commands:**
• Send any message for AI conversation
• Send images for AI analysis
• Send videos for AI response

💳 **Payment Methods:**
• Telegram Stars ⭐
• TON Coin 💎

🌍 **Multi-language support** - Switch anytime!

💡 Ready to explore unrestricted AI? Just start chatting!''',
        'fa': '''🆘 **دستورات ربات هوش مصنوعی بدون سانسور**

🔥 **چه چیزی ما را متفاوت می‌کند:**
• هیچ محدودیت موضوعی یا فیلتر محتوا
• پاسخ‌های خام و صادقانه AI
• قابلیت‌های مکالمه پیشرفته

📋 **دستورات موجود:**
• هر پیامی برای گفتگو با AI ارسال کنید
• عکس برای تجزیه و تحلیل AI ارسال کنید
• ویدیو برای پاسخ AI ارسال کنید

💳 **روش‌های پرداخت:**
• Telegram Stars ⭐
• TON Coin 💎

🌍 **پشتیبانی چند زبانه** - هر زمان تغییر دهید!

💡 آماده کاوش AI بدون محدودیت؟ فقط شروع به چت کردن!''',
        'tr': '''🆘 **Sansürsüz AI Bot Komutları**

🔥 **Bizi farklı kılan özellikler:**
• Konu kısıtlaması veya içerik filtreleri yok
• Ham, dürüst AI yanıtları
• Gelişmiş sohbet yetenekleri

📋 **Mevcut Komutlar:**
• AI sohbeti için herhangi bir mesaj gönderin
• AI analizi için resim gönderin
• AI yanıtı için video gönderin

💳 **Ödeme Yöntemleri:**
• Telegram Stars ⭐
• TON Coin 💎

🌍 **Çok dil desteği** - İstediğiniz zaman değiştirin!

💡 Kısıtlanmamış AI'yi keşfetmeye hazır mısınız? Sohbete başlayın!''',
        'ar': '''🆘 **أوامر بوت الذكاء الاصطناعي غير المقيد**

🔥 **ما يجعلنا مختلفين:**
• لا توجد قيود موضوعية أو مرشحات المحتوى
• إجابات ذكاء اصطناعي خام وصادقة
• قدرات محادثة متقدمة

📋 **الأوامر المتاحة:**
• أرسل أي رسالة لمحادثة الذكاء الاصطناعي
• أرسل صوراً لتحليل الذكاء الاصطناعي
• أرسل فيديوهات لاستجابة الذكاء الاصطناعي

💳 **طرق الدفع:**
• Telegram Stars ⭐
• TON Coin 💎

🌍 **دعم متعدد اللغات** - غيّر في أي وقت!

💡 مستعد لاستكشاف الذكاء الاصطناعي غير المقيد؟ ابدأ المحادثة!''',
        'ru': '''🆘 **Команды бота ИИ без цензуры**

🔥 **Что делает нас особенными:**
• Никаких ограничений тем или фильтров контента
• Сырые, честные ответы ИИ
• Продвинутые возможности разговора

📋 **Доступные команды:**
• Отправьте любое сообщение для беседы с ИИ
• Отправьте изображения для анализа ИИ
• Отправьте видео для ответа ИИ

💳 **Способы оплаты:**
• Telegram Stars ⭐
• TON Coin 💎

🌍 **Многоязычная поддержка** - переключайтесь в любое время!

💡 Готовы исследовать неограниченный ИИ? Начните общение!''',
        'es': '''🆘 **Comandos del Bot de IA Sin Censura**

🔥 **Lo que nos hace diferentes:**
• Sin restricciones temáticas o filtros de contenido
• Respuestas de IA crudas y honestas
• Capacidades de conversación avanzadas

📋 **Comandos Disponibles:**
• Envía cualquier mensaje para conversación con IA
• Envía imágenes para análisis de IA
• Envía videos para respuesta de IA

💳 **Métodos de Pago:**
• Telegram Stars ⭐
• TON Coin 💎

🌍 **Soporte multiidioma** - ¡Cambia en cualquier momento!

💡 ¿Listo para explorar IA sin restricciones? ¡Empieza a chatear!'''
    }
}

class Translator:
    def __init__(self, database):
        self.db = database
    
    def get(self, key: str, user_id: int = None, lang: str = None) -> str:
        """Get translated text for user's language"""
        if lang is None and user_id is not None:
            lang = self.db.get_user_language(user_id)
        elif lang is None:
            lang = 'en'  # Default to English
        
        if key in TRANSLATIONS and lang in TRANSLATIONS[key]:
            return TRANSLATIONS[key][lang]
        elif key in TRANSLATIONS and 'en' in TRANSLATIONS[key]:
            # Fallback to English if translation not available
            return TRANSLATIONS[key]['en']
        else:
            return key  # Return key if no translation found
    
    def get_language_keyboard(self):
        """Get inline keyboard for language selection"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = []
        row = []
        
        for lang_code, lang_info in LANGUAGES.items():
            button = InlineKeyboardButton(
                f"{lang_info['flag']} {lang_info['native']}", 
                callback_data=f"lang_{lang_code}"
            )
            row.append(button)
            
            # Create new row after every 2 buttons
            if len(row) == 2:
                keyboard.append(row)
                row = []
        
        # Add remaining buttons if any
        if row:
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_language_name(self, lang_code: str) -> str:
        """Get language display name"""
        if lang_code in LANGUAGES:
            return f"{LANGUAGES[lang_code]['flag']} {LANGUAGES[lang_code]['native']}"
        return lang_code