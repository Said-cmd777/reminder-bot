# test_config.py - اختبار بسيط للتحقق من متغيرات البيئة
"""اختبار سريع للتحقق من أن متغيرات البيئة تعمل بشكل صحيح."""
import os

print("=" * 50)
print("اختبار متغيرات البيئة")
print("=" * 50)

# التحقق من BOT_TOKEN
bot_token = os.getenv("BOT_TOKEN")
if bot_token:
    print(f"✅ BOT_TOKEN: موجود ({bot_token[:10]}...)")
else:
    print("❌ BOT_TOKEN: غير موجود")
    print("   قم بتعيينه باستخدام: $env:BOT_TOKEN='your_token'")

# التحقق من ADMIN_IDS
admin_ids_env = os.getenv("ADMIN_IDS")
if admin_ids_env:
    print(f"✅ ADMIN_IDS: موجود ({admin_ids_env})")
    try:
        admin_ids = [int(uid.strip()) for uid in admin_ids_env.split(",") if uid.strip()]
        print(f"   تم تحليل {len(admin_ids)} معرف أدمن: {admin_ids}")
    except ValueError as e:
        print(f"❌ خطأ في تحليل ADMIN_IDS: {e}")
else:
    print("❌ ADMIN_IDS: غير موجود")
    print("   قم بتعيينه باستخدام: $env:ADMIN_IDS='123456789'")

print("=" * 50)

# محاولة استيراد config
try:
    from config import BOT_TOKEN, ADMIN_IDS
    print("\n✅ تم تحميل config.py بنجاح!")
    print(f"   BOT_TOKEN: {'✅ موجود' if BOT_TOKEN else '❌ غير موجود'}")
    print(f"   ADMIN_IDS: {ADMIN_IDS if ADMIN_IDS else '❌ قائمة فارغة'}")
except Exception as e:
    print(f"\n❌ خطأ في تحميل config.py: {e}")

print("=" * 50)

