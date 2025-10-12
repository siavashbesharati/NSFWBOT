import json
from pathlib import Path

UPDATES = {
    "en": {
        "general": {
            "start_bot_first": "Please start the bot first with /start",
            "bot_offline": "🚫 Bot is currently offline. Please try again later.",
            "unknown_user": "User",
            "unknown_value": "Unknown"
        },
        "buttons": {
            "buy_packages": "📦 Buy Packages",
            "refresh": "🔄 Refresh",
            "back_to_referrals": "🔙 Back to Referrals",
            "buy_with_stars": "⭐ Buy with Stars ({price})",
            "buy_with_ton": "💎 Buy with TON ({price})",
            "pay_with_tonkeeper": "🔗 Pay with Tonkeeper",
            "check_payment_status": "🔍 Check Payment Status",
            "view_dashboard": "📊 View Dashboard",
            "buy_more": "🛒 Buy More",
            "check_again": "🔍 Check Again"
        },
        "credits": {
            "not_enough_text": "❌ You don't have enough text message credits!\n\nUse /packages to buy more credits.",
            "not_enough_image": "❌ You don't have enough image message credits!\n\nUse /packages to buy more credits.",
            "not_enough_video": "❌ You don't have enough video message credits!\n\nUse /packages to buy more credits."
        },
        "media": {
            "default_image_caption": "What do you see in this image?",
            "default_video_caption": "User sent a video"
        },
        "errors": {
            "referral_system_disabled": "🚫 Referral system is currently disabled.",
            "package_not_found": "❌ Package not found.",
            "transaction_not_found": "❌ Transaction not found.",
            "transaction_not_owner": "❌ This transaction doesn't belong to you.",
            "payment_status_error": "❌ Error checking payment status. Please try again.",
            "ton_only_feature": "ℹ️ This feature is only available for TON payments.",
            "referral_already_used": "❌ You have already been referred by someone else.",
            "referral_apply_failed": "❌ Failed to apply referral. Please try again later.",
            "referral_invalid_code": "❌ Invalid referral code. Please check and try again.",
            "payment_verification_failed": "❌ Payment verification failed. Please contact support.",
            "api_general_error": "Sorry, I encountered an error. Please try again.",
            "image_processing_error": "Sorry, I encountered an error processing your image. Please try again.",
            "video_processing_error": "Sorry, I encountered an error processing your video. Please try again.",
            "unsupported_language": "❌ Unsupported language: {language}"
        },
        "status": {
            "payment_already_completed": "✅ Payment already completed! Your credits have been added.",
            "checking_blockchain": "🔍 Checking blockchain for your payment..."
        },
        "packages": {
            "select": "📦 Select a package:"
        },
        "referral": {
            "share_referral_link": "📤 Share Referral Link",
            "my_referrals": "📊 My Referrals",
            "no_referrals_message": "👥 **Your Referrals**\n\nYou haven't referred anyone yet. Share your referral link to start earning rewards!",
            "referrals_header": "👥 **Your Referrals** ({count} total)\n\n",
            "referrals_entry": "{index}. @{username} - {date}\n",
            "referrals_more": "\n... and {count} more",
            "applied_success": "✅ **Referral Applied Successfully!**\n\n🎉 You and your friend both received:\n📝 +{text} text messages\n🖼️ +{image} image generations\n🎥 +{video} video generations\n\nEnjoy your free messages!",
            "enter_code_instructions": "🔗 **Enter Referral Code**\n\nPlease send me the referral code you want to use.\nThe code should be sent as a regular message (not a command).\n\n💡 *Tip: You can copy and paste the code from your friend's message.*",
            "enter_command_help": "📝 **Enter Referral Code**\n\nTo use a referral code, send:\n`/enterreferral YOUR_CODE`\n\nExample: `/enterreferral ABC12345`\n\n💡 You can only use a referral code once, and only if you haven't been referred before."
        },
        "payment": {
            "ton_instructions_title": "💎 TON Payment Instructions {network}",
            "ton_instructions_package": "📦 Package: {package}",
            "ton_instructions_amount": "💰 Amount: {amount} TON",
            "ton_instructions_address": "🏦 Address: `{address}`",
            "ton_instructions_comment": "💬 Comment: `{comment}`",
            "ton_instructions_quick": "📱 Quick Payment:",
            "ton_instructions_open": "[Open in Tonkeeper]({url})",
            "ton_instructions_auto_verify": "⏰ Your payment will be verified automatically within a few minutes.",
            "ton_network_mainnet": "🌐 MAINNET",
            "ton_network_testnet": "🧪 Note: This is TESTNET - you will receive test TON only!",
            "ton_payment_verified_title": "✅ **Payment Verified!**",
            "ton_payment_verified_details": "💰 Amount: {amount} TON\n📦 Package: {package}\n📅 Date: {date}",
            "ton_payment_verified_footer": "🎉 Your credits have been added to your account!",
            "ton_payment_pending_title": "⏳ **Payment Pending**",
            "ton_payment_pending_details": "💰 Amount: {amount} TON\n📅 Created: {date}\n🆔 Transaction ID: {transaction}",
            "ton_payment_pending_body": "❌ Payment not found on blockchain yet.\n\n**Please make sure you:**\n✅ Sent exactly {amount} TON\n✅ Used the correct comment: `Payment_{transaction}`\n✅ Sent to the correct wallet address\n\n⏰ It may take a few minutes for the transaction to appear on the blockchain."
        }
    },
    "ar": {
        "general": {
            "start_bot_first": "يرجى بدء البوت أولاً باستخدام /start",
            "bot_offline": "🚫 البوت غير متصل حالياً. يرجى المحاولة لاحقاً.",
            "unknown_user": "مستخدم",
            "unknown_value": "غير معروف"
        },
        "buttons": {
            "buy_packages": "📦 شراء الباقات",
            "refresh": "🔄 تحديث",
            "back_to_referrals": "🔙 العودة إلى الإحالات",
            "buy_with_stars": "⭐ اشترِ بالنجوم ({price})",
            "buy_with_ton": "💎 اشترِ بـ TON ({price})",
            "pay_with_tonkeeper": "🔗 الدفع عبر Tonkeeper",
            "check_payment_status": "🔍 التحقق من حالة الدفع",
            "view_dashboard": "📊 عرض لوحة التحكم",
            "buy_more": "🛒 شراء المزيد",
            "check_again": "🔍 التحقق مرة أخرى"
        },
        "credits": {
            "not_enough_text": "❌ لا تملك رصيداً كافياً لرسائل النص!\n\nاستخدم /packages لشراء المزيد من الرصيد.",
            "not_enough_image": "❌ لا تملك رصيداً كافياً لرسائل الصور!\n\nاستخدم /packages لشراء المزيد من الرصيد.",
            "not_enough_video": "❌ لا تملك رصيداً كافياً لرسائل الفيديو!\n\nاستخدم /packages لشراء المزيد من الرصيد."
        },
        "media": {
            "default_image_caption": "ماذا ترى في هذه الصورة؟",
            "default_video_caption": "قام المستخدم بإرسال فيديو"
        },
        "errors": {
            "referral_system_disabled": "🚫 نظام الإحالات معطل حالياً.",
            "package_not_found": "❌ لم يتم العثور على الباقة.",
            "transaction_not_found": "❌ لم يتم العثور على المعاملة.",
            "transaction_not_owner": "❌ هذه المعاملة لا تخصك.",
            "payment_status_error": "❌ خطأ في التحقق من حالة الدفع. يرجى المحاولة لاحقاً.",
            "ton_only_feature": "ℹ️ هذه الميزة متاحة فقط لمدفوعات TON.",
            "referral_already_used": "❌ لقد تم إحالتك بالفعل من قبل شخص آخر.",
            "referral_apply_failed": "❌ فشل تطبيق الإحالة. يرجى المحاولة لاحقاً.",
            "referral_invalid_code": "❌ رمز الإحالة غير صالح. يرجى التحقق والمحاولة مرة أخرى.",
            "payment_verification_failed": "❌ فشل التحقق من الدفع. يرجى التواصل مع الدعم.",
            "api_general_error": "عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.",
            "image_processing_error": "عذراً، حدث خطأ أثناء معالجة صورتك. يرجى المحاولة مرة أخرى.",
            "video_processing_error": "عذراً، حدث خطأ أثناء معالجة الفيديو الخاص بك. يرجى المحاولة مرة أخرى.",
            "unsupported_language": "❌ لغة غير مدعومة: {language}"
        },
        "status": {
            "payment_already_completed": "✅ تم إكمال الدفع بالفعل! تمت إضافة رصيدك.",
            "checking_blockchain": "🔍 جارٍ التحقق من البلوك تشين لدفعك..."
        },
        "packages": {
            "select": "📦 اختر باقة:"
        },
        "referral": {
            "share_referral_link": "📤 مشاركة رابط الإحالة",
            "my_referrals": "📊 إحالاتي",
            "no_referrals_message": "👥 **إحالاتك**\n\nلم تقم بإحالة أي شخص بعد. شارك رابط الإحالة لبدء كسب المكافآت!",
            "referrals_header": "👥 **إحالاتك** ({count} إجماليًا)\n\n",
            "referrals_entry": "{index}. @{username} - {date}\n",
            "referrals_more": "\n... و {count} أخرى",
            "applied_success": "✅ **تم تطبيق الإحالة بنجاح!**\n\n🎉 أنت وصديقك حصلتما على:\n📝 +{text} رسائل نصية\n🖼️ +{image} توليد صور\n🎥 +{video} توليد فيديوهات\n\nاستمتع برسائلك المجانية!",
            "enter_code_instructions": "🔗 **إدخال رمز الإحالة**\n\nيرجى إرسال رمز الإحالة الذي تريد استخدامه.\nيجب إرسال الرمز كرسالة عادية (ليس كأمر).\n\n💡 *نصيحة: يمكنك نسخ ولصق الرمز من رسالة صديقك.*",
            "enter_command_help": "📝 **إدخال رمز الإحالة**\n\نلاستخدام رمز إحالة، أرسل:\n`/enterreferral YOUR_CODE`\n\nمثال: `/enterreferral ABC12345`\n\n💡 يمكنك استخدام رمز إحالة مرة واحدة فقط، وفقط إذا لم تتم إحالتك من قبل."
        },
        "payment": {
            "ton_instructions_title": "💎 تعليمات الدفع بـ TON {network}",
            "ton_instructions_package": "📦 الباقة: {package}",
            "ton_instructions_amount": "💰 المبلغ: {amount} TON",
            "ton_instructions_address": "🏦 العنوان: `{address}`",
            "ton_instructions_comment": "💬 التعليق: `{comment}`",
            "ton_instructions_quick": "📱 دفع سريع:",
            "ton_instructions_open": "[فتح في Tonkeeper]({url})",
            "ton_instructions_auto_verify": "⏰ سيتم التحقق من دفعتك تلقائياً خلال بضع دقائق.",
            "ton_network_mainnet": "🌐 الشبكة الرئيسية",
            "ton_network_testnet": "🧪 ملاحظة: هذه شبكة اختبار - ستحصل فقط على TON تجريبي!",
            "ton_payment_verified_title": "✅ **تم التحقق من الدفع!**",
            "ton_payment_verified_details": "💰 المبلغ: {amount} TON\n📦 الباقة: {package}\n📅 التاريخ: {date}",
            "ton_payment_verified_footer": "🎉 تمت إضافة رصيدك إلى حسابك!",
            "ton_payment_pending_title": "⏳ **الدفع قيد الانتظار**",
            "ton_payment_pending_details": "💰 المبلغ: {amount} TON\n📅 تم الإنشاء: {date}\n🆔 رقم المعاملة: {transaction}",
            "ton_payment_pending_body": "❌ لم يتم العثور على الدفع على البلوك تشين بعد.\n\n**يرجى التأكد من أنك:**\n✅ أرسلت بالضبط {amount} TON\n✅ استخدمت التعليق الصحيح: `Payment_{transaction}`\n✅ أرسلت إلى عنوان المحفظة الصحيح\n\n⏰ قد يستغرق ظهور المعاملة على البلوك تشين بضع دقائق."
        }
    },
    "fa": {
        "general": {
            "start_bot_first": "لطفاً ابتدا ربات را با دستور /start شروع کنید",
            "bot_offline": "🚫 ربات در حال حاضر آفلاین است. لطفاً بعداً دوباره تلاش کنید.",
            "unknown_user": "کاربر",
            "unknown_value": "نامشخص"
        },
        "buttons": {
            "buy_packages": "📦 خرید بسته‌ها",
            "refresh": "🔄 به‌روزرسانی",
            "back_to_referrals": "🔙 بازگشت به معرفی‌ها",
            "buy_with_stars": "⭐ خرید با ستاره ({price})",
            "buy_with_ton": "💎 خرید با TON ({price})",
            "pay_with_tonkeeper": "🔗 پرداخت با Tonkeeper",
            "check_payment_status": "🔍 بررسی وضعیت پرداخت",
            "view_dashboard": "📊 مشاهده داشبورد",
            "buy_more": "🛒 خرید بیشتر",
            "check_again": "🔍 بررسی دوباره"
        },
        "credits": {
            "not_enough_text": "❌ اعتبار کافی برای پیام متنی ندارید!\n\nاز /packages برای خرید اعتبار بیشتر استفاده کنید.",
            "not_enough_image": "❌ اعتبار کافی برای پیام تصویری ندارید!\n\nاز /packages برای خرید اعتبار بیشتر استفاده کنید.",
            "not_enough_video": "❌ اعتبار کافی برای پیام ویدیویی ندارید!\n\nاز /packages برای خرید اعتبار بیشتر استفاده کنید."
        },
        "media": {
            "default_image_caption": "در این تصویر چه می‌بینید؟",
            "default_video_caption": "کاربر یک ویدیو ارسال کرد"
        },
        "errors": {
            "referral_system_disabled": "🚫 سیستم معرفی در حال حاضر غیرفعال است.",
            "package_not_found": "❌ بسته پیدا نشد.",
            "transaction_not_found": "❌ تراکنش پیدا نشد.",
            "transaction_not_owner": "❌ این تراکنش متعلق به شما نیست.",
            "payment_status_error": "❌ خطا در بررسی وضعیت پرداخت. لطفاً بعداً دوباره تلاش کنید.",
            "ton_only_feature": "ℹ️ این ویژگی فقط برای پرداخت‌های TON در دسترس است.",
            "referral_already_used": "❌ شما قبلاً توسط شخص دیگری معرفی شده‌اید.",
            "referral_apply_failed": "❌ اعمال معرفی ناموفق بود. لطفاً بعداً دوباره تلاش کنید.",
            "referral_invalid_code": "❌ کد معرفی نامعتبر است. لطفاً بررسی و دوباره تلاش کنید.",
            "payment_verification_failed": "❌ تأیید پرداخت ناموفق بود. لطفاً با پشتیبانی تماس بگیرید.",
            "api_general_error": "متأسفیم، خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            "image_processing_error": "متأسفیم، هنگام پردازش تصویر شما خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            "video_processing_error": "متأسفیم، هنگام پردازش ویدیوي شما خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            "unsupported_language": "❌ زبان پشتیبانی نمی‌شود: {language}"
        },
        "status": {
            "payment_already_completed": "✅ پرداخت قبلاً تکمیل شده است! اعتبارات شما اضافه شد.",
            "checking_blockchain": "🔍 در حال بررسی بلاک‌چین برای پرداخت شما..."
        },
        "packages": {
            "select": "📦 یک بسته را انتخاب کنید:"
        },
        "referral": {
            "share_referral_link": "📤 اشتراک لینک معرفی",
            "my_referrals": "📊 معرفی‌های من",
            "no_referrals_message": "👥 **معرفی‌های شما**\n\nهنوز کسی را معرفی نکرده‌اید. لینک معرفی خود را به اشتراک بگذارید تا شروع به دریافت پاداش کنید!",
            "referrals_header": "👥 **معرفی‌های شما** ({count} مورد)\n\n",
            "referrals_entry": "{index}. @{username} - {date}\n",
            "referrals_more": "\n... و {count} مورد دیگر",
            "applied_success": "✅ **کد معرفی با موفقیت اعمال شد!**\ن\n🎉 شما و دوستتان دریافت کردید:\ن📝 +{text} پیام متنی\ن🖼️ +{image} تولید تصویر\ن🎥 +{video} تولید ویدیو\ن\ناز پیام‌های رایگان خود لذت ببرید!",
            "enter_code_instructions": "🔗 **وارد کردن کد معرفی**\ن\نلطفاً کد معرفی موردنظر خود را ارسال کنید.\نكد باید به صورت پیام عادی (نه دستور) ارسال شود.\ن\ن*نکته: می‌توانید کد را از پیام دوستتان کپی و جای‌گذاری کنید.*",
            "enter_command_help": "📝 **وارد کردن کد معرفی**\ن\نبرای استفاده از کد معرفی، این‌گونه ارسال کنید:\n`/enterreferral YOUR_CODE`\n\nمثال: `/enterreferral ABC12345`\n\n💡 شما فقط یک‌بار می‌توانید از کد معرفی استفاده کنید و تنها در صورتی که قبلاً معرفی نشده باشید."
        },
        "payment": {
            "ton_instructions_title": "💎 دستورالعمل پرداخت TON {network}",
            "ton_instructions_package": "📦 بسته: {package}",
            "ton_instructions_amount": "💰 مبلغ: {amount} TON",
            "ton_instructions_address": "🏦 آدرس: `{address}`",
            "ton_instructions_comment": "💬 توضیح: `{comment}`",
            "ton_instructions_quick": "📱 پرداخت سریع:",
            "ton_instructions_open": "[باز کردن در Tonkeeper]({url})",
            "ton_instructions_auto_verify": "⏰ پرداخت شما ظرف چند دقیقه به‌صورت خودکار تأیید می‌شود.",
            "ton_network_mainnet": "🌐 شبکه اصلی",
            "ton_network_testnet": "🧪 توجه: این شبکه تست است - فقط TON آزمایشی دریافت می‌کنید!",
            "ton_payment_verified_title": "✅ **پرداخت تأیید شد!**",
            "ton_payment_verified_details": "💰 مبلغ: {amount} TON\n📦 بسته: {package}\n📅 تاریخ: {date}",
            "ton_payment_verified_footer": "🎉 اعتبار شما به حساب‌تان اضافه شد!",
            "ton_payment_pending_title": "⏳ **پرداخت در انتظار**",
            "ton_payment_pending_details": "💰 مبلغ: {amount} TON\n📅 ایجاد شده: {date}\n🆔 شناسه تراکنش: {transaction}",
            "ton_payment_pending_body": "❌ پرداخت هنوز در بلاک‌چین پیدا نشده است.\n\n**لطفاً مطمئن شوید که:**\n✅ دقیقاً {amount} TON ارسال کرده‌اید\n✅ از توضیح صحیح استفاده کرده‌اید: `Payment_{transaction}`\n✅ به آدرس صحیح کیف پول ارسال کرده‌اید\n\n⏰ ممکن است چند دقیقه طول بکشد تا تراکنش در بلاک‌چین نمایش داده شود."
        }
    },
    "tr": {
        "general": {
            "start_bot_first": "Lütfen önce /start komutuyla botu başlatın",
            "bot_offline": "🚫 Bot şu anda çevrimdışı. Lütfen daha sonra tekrar deneyin.",
            "unknown_user": "Kullanıcı",
            "unknown_value": "Bilinmiyor"
        },
        "buttons": {
            "buy_packages": "📦 Paket Satın Al",
            "refresh": "🔄 Yenile",
            "back_to_referrals": "🔙 Referanslara Dön",
            "buy_with_stars": "⭐ Yıldız ile Satın Al ({price})",
            "buy_with_ton": "💎 TON ile Satın Al ({price})",
            "pay_with_tonkeeper": "🔗 Tonkeeper ile Öde",
            "check_payment_status": "🔍 Ödeme Durumunu Kontrol Et",
            "view_dashboard": "📊 Panoyu Görüntüle",
            "buy_more": "🛒 Daha Fazla Satın Al",
            "check_again": "🔍 Tekrar Kontrol Et"
        },
        "credits": {
            "not_enough_text": "❌ Yeterli metin mesaj krediniz yok!\n\nDaha fazla kredi almak için /packages komutunu kullanın.",
            "not_enough_image": "❌ Yeterli görsel mesaj krediniz yok!\n\nDaha fazla kredi almak için /packages komutunu kullanın.",
            "not_enough_video": "❌ Yeterli video mesaj krediniz yok!\n\nDaha fazla kredi almak için /packages komutunu kullanın."
        },
        "media": {
            "default_image_caption": "Bu görüntüde ne görüyorsun?",
            "default_video_caption": "Kullanıcı bir video gönderdi"
        },
        "errors": {
            "referral_system_disabled": "🚫 Referans sistemi şu anda devre dışı.",
            "package_not_found": "❌ Paket bulunamadı.",
            "transaction_not_found": "❌ İşlem bulunamadı.",
            "transaction_not_owner": "❌ Bu işlem size ait değil.",
            "payment_status_error": "❌ Ödeme durumu kontrol edilirken hata oluştu. Lütfen tekrar deneyin.",
            "ton_only_feature": "ℹ️ Bu özellik yalnızca TON ödemeleri için kullanılabilir.",
            "referral_already_used": "❌ Zaten başka biri tarafından referans gösterildiniz.",
            "referral_apply_failed": "❌ Referans uygulanamadı. Lütfen daha sonra tekrar deneyin.",
            "referral_invalid_code": "❌ Referans kodu geçersiz. Lütfen kontrol edip tekrar deneyin.",
            "payment_verification_failed": "❌ Ödeme doğrulaması başarısız oldu. Lütfen destekle iletişime geçin.",
            "api_general_error": "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.",
            "image_processing_error": "Üzgünüm, görüntünüz işlenirken bir hata oluştu. Lütfen tekrar deneyin.",
            "video_processing_error": "Üzgünüm, videonuz işlenirken bir hata oluştu. Lütfen tekrar deneyin.",
            "unsupported_language": "❌ Desteklenmeyen dil: {language}"
        },
        "status": {
            "payment_already_completed": "✅ Ödeme zaten tamamlanmış! Kredileriniz eklendi.",
            "checking_blockchain": "🔍 Ödemeniz için blok zinciri kontrol ediliyor..."
        },
        "packages": {
            "select": "📦 Bir paket seçin:"
        },
        "referral": {
            "share_referral_link": "📤 Referans Bağlantısını Paylaş",
            "my_referrals": "📊 Referanslarım",
            "no_referrals_message": "👥 **Referanslarınız**\n\nHenüz kimseyi referans göstermediniz. Ödül kazanmaya başlamak için referans bağlantınızı paylaşın!",
            "referrals_header": "👥 **Referanslarınız** (toplam {count})\n\n",
            "referrals_entry": "{index}. @{username} - {date}\n",
            "referrals_more": "\n... ve {count} tane daha",
            "applied_success": "✅ **Referans Başarıyla Uygulandı!**\n\n🎉 Siz ve arkadaşınız şu ödülleri aldınız:\n📝 +{text} metin mesajı\n🖼️ +{image} görsel üretimi\n🎥 +{video} video üretimi\n\nÜcretsiz mesajlarınızın tadını çıkarın!",
            "enter_code_instructions": "🔗 **Referанс Kodu Gir**\n\nLütfen kullanmak istediğiniz referans kodunu gönderin.\nKodu normal bir mesaj olarak gönderin (komut olarak değil).\n\n*İpucu: Kodu arkadaşınızın mesajından kopyalayıp yapıştırabilirsiniz.*",
            "enter_command_help": "📝 **Referанс Kodu Gir**\n\nReferанс kodunu kullanmak için şunu gönderin:\n`/enterreferral YOUR_CODE`\n\nÖrnek: `/enterreferral ABC12345`\n\n💡 Referанс kodunu yalnızca bir kez ve daha önce referанс gösterilmediyseniz kullanabilirsiniz."
        },
        "payment": {
            "ton_instructions_title": "💎 TON Ödeme Talimatları {network}",
            "ton_instructions_package": "📦 Paket: {package}",
            "ton_instructions_amount": "💰 Tutar: {amount} TON",
            "ton_instructions_address": "🏦 Adres: `{address}`",
            "ton_instructions_comment": "💬 Açıklama: `{comment}`",
            "ton_instructions_quick": "📱 Hızlı Ödeme:",
            "ton_instructions_open": "[Tonkeeper'da Aç]({url})",
            "ton_instructions_auto_verify": "⏰ Ödemeniz birkaç dakika içinde otomatik olarak doğrulanacaktır.",
            "ton_network_mainnet": "🌐 ANA AĞ",
            "ton_network_testnet": "🧪 Not: Bu TESTNET - yalnızca deneme TON alırsınız!",
            "ton_payment_verified_title": "✅ **Ödeme Doğrulandı!**",
            "ton_payment_verified_details": "💰 Tutar: {amount} TON\n📦 Paket: {package}\n📅 Tarih: {date}",
            "ton_payment_verified_footer": "🎉 Kredileriniz hesabınıza eklendi!",
            "ton_payment_pending_title": "⏳ **Ödeme Beklemede**",
            "ton_payment_pending_details": "💰 Tutar: {amount} TON\n📅 Oluşturulma: {date}\n🆔 İşlem Kimliği: {transaction}",
            "ton_payment_pending_body": "❌ Ödeme henüz blok zincирinde bulunamadı.\n\n**Lütfen emin olun ki:**\n✅ Tam olarak {amount} TON gönderdiniz\n✅ Doğru açıklamayı kullandınız: `Payment_{transaction}`\n✅ Doğru cüzdan adresine gönderdiniz\n\n⏰ İşleмин блок zincирinde görünmesi birkaç dakika sürebilir."
        }
    },
    "ru": {
        "general": {
            "start_bot_first": "Пожалуйста, сначала запустите бота командой /start",
            "bot_offline": "🚫 Бот сейчас офлайн. Пожалуйста, попробуйте позже.",
            "unknown_user": "Пользователь",
            "unknown_value": "Неизвестно"
        },
        "buttons": {
            "buy_packages": "📦 Купить пакеты",
            "refresh": "🔄 Обновить",
            "back_to_referrals": "🔙 Назад к рефералам",
            "buy_with_stars": "⭐ Купить за звёзды ({price})",
            "buy_with_ton": "💎 Купить за TON ({price})",
            "pay_with_tonkeeper": "🔗 Оплатить через Tonkeeper",
            "check_payment_status": "🔍 Проверить платеж",
            "view_dashboard": "📊 Открыть панель",
            "buy_more": "🛒 Купить ещё",
            "check_again": "🔍 Проверить снова"
        },
        "credits": {
            "not_enough_text": "❌ У вас недостаточно кредитов на текстовые сообщения!\n\nИспользуйте /packages, чтобы купить больше.",
            "not_enough_image": "❌ У вас недостаточно кредитов на сообщения с изображениями!\n\нИспользуйте /packages, чтобы купить больше.",
            "not_enough_video": "❌ У вас недостаточно кредитов на видео сообщения!\n\нИспользуйте /packages, чтобы купить больше."
        },
        "media": {
            "default_image_caption": "Что вы видите на этом изображении?",
            "default_video_caption": "Пользователь отправил видео"
        },
        "errors": {
            "referral_system_disabled": "🚫 Реферальная система сейчас отключена.",
            "package_not_found": "❌ Пакет не найден.",
            "transaction_not_found": "❌ Транзакция не найдена.",
            "transaction_not_owner": "❌ Эта транзакция не принадлежит вам.",
            "payment_status_error": "❌ Ошибка при проверке статуса платежа. Попробуйте снова.",
            "ton_only_feature": "ℹ️ Эта функция доступна только для платежей TON.",
            "referral_already_used": "❌ Вас уже пригласил другой пользователь.",
            "referral_apply_failed": "❌ Не удалось применить реферальный код. Попробуйте позже.",
            "referral_invalid_code": "❌ Неверный реферальный код. Проверьте и попробуйте снова.",
            "payment_verification_failed": "❌ Не удалось подтвердить платеж. Свяжитесь с поддержкой.",
            "api_general_error": "Извините, произошла ошибка. Попробуйте ещё раз.",
            "image_processing_error": "Извините, при обработке вашего изображения произошла ошибка. Попробуйте ещё раз.",
            "video_processing_error": "Извините, при обработке вашего видео произошла ошибка. Попробуйте ещё раз.",
            "unsupported_language": "❌ Неподдерживаемый язык: {language}"
        },
        "status": {
            "payment_already_completed": "✅ Платёж уже завершён! Ваши кредиты добавлены.",
            "checking_blockchain": "🔍 Проверяем блокчейн на наличие платежа..."
        },
        "packages": {
            "select": "📦 Выберите пакет:"
        },
        "referral": {
            "share_referral_link": "📤 Поделиться реферальной ссылкой",
            "my_referrals": "📊 Мои рефералы",
            "no_referrals_message": "👥 **Ваши рефералы**\n\нВы ещё никого не пригласили. Поделитесь своей ссылкой, чтобы начать получать награды!",
            "referrals_header】: ...