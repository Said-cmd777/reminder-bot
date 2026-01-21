
"""Telegram bot handlers for homework reminder system."""
import html
import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any

import telebot
from telebot import types

from config import ADMIN_IDS
from utils import is_cancel_text, parse_dt
from db import (
    ensure_tables,
    insert_homework, get_homework, get_all_homeworks, delete_homework,
    mark_done, mark_undone, is_homework_done_for_user, update_field, register_user, update_user_display_name,
    is_user_registered, is_user_registration_complete, get_all_registered_user_ids,
    insert_custom_reminder, get_custom_reminder, get_all_custom_reminders_for_user, delete_custom_reminder,
    mark_custom_reminder_done, mark_custom_reminder_undone, is_custom_reminder_done_for_user,
    get_notification_setting, set_notification_setting, enable_all_notifications, disable_all_notifications,
    get_notification_settings
)
from db_utils import db_connection, safe_get
from validators import (
    validate_text_input, validate_datetime, validate_user_id,
    validate_reminders, validate_url
)
from constants import (
    CALLBACK_HW_DONE, CALLBACK_HW_UNDONE, CALLBACK_HW_PDF, CALLBACK_HW_VIEW, CALLBACK_HW_EDIT_ID,
    CALLBACK_HW_DELETE_ID, CALLBACK_HW_CONFIRM_DELETE, CALLBACK_HW_EDIT_FIELD,
    CALLBACK_HW_CANCEL, CALLBACK_HW_BACK, CALLBACK_HW_LIST, CALLBACK_HW_ADD,
    CALLBACK_HW_EDIT, CALLBACK_HW_DELETE, CALLBACK_MANUAL_REMINDER,
    CALLBACK_MANUAL_SEND_NOW, CALLBACK_MANUAL_SCHEDULE, CALLBACK_MANUAL_TARGET_ALL,
    CALLBACK_MANUAL_TARGET_USER, CALLBACK_MANUAL_TARGET_CHAT,
    CALLBACK_MANUAL_TARGET_CHAT_TOPIC, DEFAULT_REMINDERS,
    PENDING_STEP_TARGET_TYPE, PENDING_STEP_ENTER_TARGET, PENDING_STEP_ENTER_TEXT,
    PENDING_STEP_ENTER_CONTENT, PENDING_STEP_ENTER_CHAT, PENDING_STEP_ENTER_THREAD, PENDING_STEP_ENTER_DATETIME,
    MAX_INPUT_LENGTH, MAX_DESCRIPTION_LENGTH,
    CALLBACK_CUSTOM_REMINDER, CALLBACK_CUSTOM_REMINDER_ADD, CALLBACK_CUSTOM_REMINDER_LIST,
    CALLBACK_CUSTOM_REMINDER_DELETE, CALLBACK_CUSTOM_REMINDER_CONFIRM_DELETE,
    CALLBACK_CUSTOM_REMINDER_DONE, CALLBACK_CUSTOM_REMINDER_UNDONE,
    CALLBACK_WEEKLY_SCHEDULE, CALLBACK_WEEKLY_SCHEDULE_GROUP_01, CALLBACK_WEEKLY_SCHEDULE_GROUP_02,
    CALLBACK_WEEKLY_SCHEDULE_GROUP_03, CALLBACK_WEEKLY_SCHEDULE_GROUP_04,
    CALLBACK_WEEKLY_SCHEDULE_TODAY, CALLBACK_WEEKLY_SCHEDULE_TOMORROW, CALLBACK_WEEKLY_SCHEDULE_WEEK,
    CALLBACK_WEEKLY_SCHEDULE_ADMIN, CALLBACK_WEEKLY_SCHEDULE_ADMIN_GROUP, CALLBACK_WEEKLY_SCHEDULE_ADMIN_DAY,
    CALLBACK_WEEKLY_SCHEDULE_ADMIN_VIEW, CALLBACK_WEEKLY_SCHEDULE_ADMIN_ADD, CALLBACK_WEEKLY_SCHEDULE_ADMIN_EDIT,
    CALLBACK_WEEKLY_SCHEDULE_ADMIN_DELETE, CALLBACK_WEEKLY_SCHEDULE_ADMIN_CONFIRM_DELETE,
    CALLBACK_WEEKLY_SCHEDULE_ADMIN_LOCATIONS, CALLBACK_WEEKLY_SCHEDULE_ADMIN_ALTERNATING,
    CALLBACK_SCHEDULE_EDIT_TIME_START, CALLBACK_SCHEDULE_EDIT_TIME_END,
    CALLBACK_SCHEDULE_EDIT_COURSE, CALLBACK_SCHEDULE_EDIT_LOCATION,
    CALLBACK_SCHEDULE_EDIT_TYPE, CALLBACK_SCHEDULE_EDIT_ALTERNATING,
    CALLBACK_ALTERNATING_LIST, CALLBACK_ALTERNATING_EDIT, CALLBACK_ALTERNATING_EDIT_DATE, CALLBACK_ALTERNATING_ADD,
    CALLBACK_NOTIFICATION_SETTINGS, CALLBACK_NOTIFICATION_DISABLE_HOMEWORK, CALLBACK_NOTIFICATION_ENABLE_HOMEWORK,
    CALLBACK_NOTIFICATION_DISABLE_MANUAL, CALLBACK_NOTIFICATION_ENABLE_MANUAL,
    CALLBACK_NOTIFICATION_DISABLE_CUSTOM, CALLBACK_NOTIFICATION_ENABLE_CUSTOM,
    CALLBACK_NOTIFICATION_DISABLE_ALL, CALLBACK_NOTIFICATION_ENABLE_ALL,
    REGISTRATION_GROUP_NORMALIZATION, REGISTRATION_GROUP_OPTIONS
)

logger = logging.getLogger(__name__)


from bot_handlers.base import BotHandlers, StateManager, StateType
from bot_handlers.helpers import (
    is_admin, format_homework_text, main_menu_kb, cancel_inline_kb, registration_kb,
    hw_item_kb, hw_main_kb, try_get_chat_variants,
    custom_reminder_main_kb, custom_reminder_item_kb,
    weekly_schedule_group_kb, weekly_schedule_time_kb,
    notification_settings_kb, is_main_menu_button
)
from bot_handlers.schedule_admin_helpers import (
    schedule_admin_groups_kb, schedule_admin_days_kb, schedule_admin_day_menu_kb,
    schedule_admin_classes_list_kb, schedule_admin_class_actions_kb, format_class_for_display,
    schedule_admin_edit_class_menu_kb, format_alternating_config_for_display,
    alternating_configs_list_kb, alternating_config_actions_kb,
    DAY_NAMES_AR, DAY_ORDER
)




global_bot: Optional[telebot.TeleBot] = None




def _job_send_to_chat(chat_id: int, text: str, message_thread_id: Optional[int] = None):
    """دالة سطحية (module:function) تُستخدم من قبل APScheduler بالاسم النصي."""
    try:
        if not global_bot:
            logger.error("_job_send_to_chat: global_bot غير مضبوط")
            return
        if message_thread_id:
            global_bot.send_message(chat_id, text, message_thread_id=message_thread_id)
        else:
            global_bot.send_message(chat_id, text)
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 403:
            logger.warning(f"Bot was blocked by user/chat {chat_id}")
        else:
            logger.exception("فشل إرسال رسالة مجدولة إلى chat %s (thread %s)", chat_id, message_thread_id)
    except Exception:
        logger.exception("فشل إرسال رسالة مجدولة إلى chat %s (thread %s)", chat_id, message_thread_id)


def _job_send_to_user(user_id: int, text: str):
    """دالة سطحية لإرسال رسالة خاصة مجدولة."""
    try:
        if not global_bot:
            logger.error("_job_send_to_user: global_bot غير مضبوط")
            return
        
        
        with db_connection() as conn:
            if not get_notification_setting(conn, user_id, 'manual_reminders'):
                logger.info("_job_send_to_user: user_id=%s disabled manual_reminders, skipping", user_id)
                return
        
        global_bot.send_message(user_id, text)
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 403:
            logger.warning(f"Bot was blocked by user {user_id}")
        else:
            logger.exception("فشل إرسال رسالة مجدولة إلى user %s", user_id)
    except Exception:
        logger.exception("فشل إرسال رسالة مجدولة إلى user %s", user_id)


def _job_send_custom_reminder(reminder_id: int, user_id: int):
    """دالة سطحية لإرسال تذكير مخصص مجدول."""
    try:
        if not global_bot:
            logger.error("_job_send_custom_reminder: global_bot غير مضبوط")
            return
        
        from db import get_custom_reminder, is_custom_reminder_done_for_user
        from bot_handlers.helpers import custom_reminder_item_kb
        
        with db_connection() as conn:
            
            if not get_notification_setting(conn, user_id, 'custom_reminders'):
                logger.info("_job_send_custom_reminder: user_id=%s disabled custom_reminders, skipping", user_id)
                return
            
            reminder = get_custom_reminder(conn, reminder_id)
            if not reminder:
                logger.warning("_job_send_custom_reminder: reminder_id=%s not found", reminder_id)
                return
            
            
            if is_custom_reminder_done_for_user(conn, reminder_id, user_id):
                logger.info("_job_send_custom_reminder: user_id=%s already completed reminder_id=%s, skipping", user_id, reminder_id)
                return
            
            text = f"🔔 تذكير مخصص\n\n{reminder['text']}\n\n⏰ الموعد: {reminder['reminder_datetime']}\nID: {reminder_id}"
            is_done = is_custom_reminder_done_for_user(conn, reminder_id, user_id)
            kb = custom_reminder_item_kb(reminder_id, is_done=is_done)
            global_bot.send_message(user_id, text, reply_markup=kb)
            logger.info("_job_send_custom_reminder: sent reminder_id=%s to user_id=%s", reminder_id, user_id)
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 403:
            logger.warning(f"Bot was blocked by user {user_id}")
        else:
            logger.exception("فشل إرسال تذكير مخصص reminder_id=%s إلى user_id=%s", reminder_id, user_id)
    except Exception:
        logger.exception("فشل إرسال تذكير مخصص reminder_id=%s إلى user_id=%s", reminder_id, user_id)


def _job_send_media_to_user(user_id: int, text: str, media_type: str, media_file_id: str, caption: Optional[str] = None):
    """دالة سطحية لإرسال ملف مجدول إلى مستخدم."""
    try:
        if not global_bot:
            logger.error("_job_send_media_to_user: global_bot غير مضبوط")
            return
        
        
        with db_connection() as conn:
            if not get_notification_setting(conn, user_id, 'manual_reminders'):
                logger.info("_job_send_media_to_user: user_id=%s disabled manual_reminders, skipping", user_id)
                return
        
        
        if text:
            global_bot.send_message(user_id, text)
        
        
        if media_type == "photo":
            global_bot.send_photo(user_id, media_file_id, caption=caption)
        elif media_type == "audio":
            global_bot.send_audio(user_id, media_file_id, caption=caption)
        elif media_type == "voice":
            global_bot.send_voice(user_id, media_file_id, caption=caption)
        elif media_type == "video":
            global_bot.send_video(user_id, media_file_id, caption=caption)
        elif media_type == "document":
            global_bot.send_document(user_id, media_file_id, caption=caption)
        elif media_type == "video_note":
            global_bot.send_video_note(user_id, media_file_id)
        elif media_type == "sticker":
            global_bot.send_sticker(user_id, media_file_id)
        else:
            logger.warning("_job_send_media_to_user: unknown media_type=%s", media_type)
            
        logger.info("_job_send_media_to_user: sent media_type=%s to user_id=%s", media_type, user_id)
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 403:
            logger.warning(f"Bot was blocked by user {user_id}")
        else:
            logger.exception("فشل إرسال ملف media_type=%s إلى user_id=%s", media_type, user_id)
    except Exception:
        logger.exception("فشل إرسال ملف media_type=%s إلى user_id=%s", media_type, user_id)


def _job_send_media_to_chat(chat_id: int, text: str, media_type: str, media_file_id: str, caption: Optional[str] = None, message_thread_id: Optional[int] = None):
    """دالة سطحية لإرسال ملف مجدول إلى محادثة."""
    try:
        if not global_bot:
            logger.error("_job_send_media_to_chat: global_bot غير مضبوط")
            return
        
        
        if text:
            if message_thread_id:
                global_bot.send_message(chat_id, text, message_thread_id=message_thread_id)
            else:
                global_bot.send_message(chat_id, text)
        
        
        send_kwargs = {"caption": caption} if caption else {}
        if message_thread_id:
            send_kwargs["message_thread_id"] = message_thread_id
            
        if media_type == "photo":
            global_bot.send_photo(chat_id, media_file_id, **send_kwargs)
        elif media_type == "audio":
            global_bot.send_audio(chat_id, media_file_id, **send_kwargs)
        elif media_type == "voice":
            global_bot.send_voice(chat_id, media_file_id, **send_kwargs)
        elif media_type == "video":
            global_bot.send_video(chat_id, media_file_id, **send_kwargs)
        elif media_type == "document":
            global_bot.send_document(chat_id, media_file_id, **send_kwargs)
        elif media_type == "video_note":
            if message_thread_id:
                send_kwargs.pop("caption", None)  
            global_bot.send_video_note(chat_id, media_file_id, **send_kwargs)
        elif media_type == "sticker":
            if message_thread_id:
                send_kwargs.pop("caption", None)  
            global_bot.send_sticker(chat_id, media_file_id, **send_kwargs)
        else:
            logger.warning("_job_send_media_to_chat: unknown media_type=%s", media_type)
            
        logger.info("_job_send_media_to_chat: sent media_type=%s to chat_id=%s", media_type, chat_id)
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 403:
            logger.warning(f"Bot was blocked by chat {chat_id}")
        else:
            logger.exception("فشل إرسال ملف media_type=%s إلى chat_id=%s", media_type, chat_id)
    except Exception:
        logger.exception("فشل إرسال ملف media_type=%s إلى chat_id=%s", media_type, chat_id)





_pending_add = {}
_pending_manual = {}
_pending_registration = {}
_pending_schedule_admin = {}  
_pending_lock = threading.Lock()
_pending_registration_lock = threading.Lock()
_pending_schedule_admin_lock = threading.Lock()


_state_mgr: Optional[StateManager] = None


def start_pending_add(chat_id):
    """Start pending add state (backward compatibility)."""
    with _pending_lock:
        _pending_add[chat_id] = True
    if _state_mgr:
        _state_mgr.start(chat_id, StateType.ADD_HOMEWORK)


def cancel_pending_add(chat_id):
    """Cancel pending add state (backward compatibility)."""
    with _pending_lock:
        _pending_add.pop(chat_id, None)
    if _state_mgr:
        _state_mgr.clear(chat_id)


def is_pending_add(chat_id):
    """Check if pending add state is active (backward compatibility)."""
    with _pending_lock:
        return _pending_add.get(chat_id, False)
    
    if _state_mgr:
        return _state_mgr.is_active(chat_id, StateType.ADD_HOMEWORK)
    return False


def start_pending_manual(chat_id):
    """Start pending manual reminder state (backward compatibility)."""
    with _pending_lock:
        _pending_manual[chat_id] = {"step": "target_type"}
    if _state_mgr:
        _state_mgr.start(chat_id, StateType.MANUAL_REMINDER, {"step": "target_type"})


def cancel_pending_manual(chat_id):
    """Cancel pending manual reminder state (backward compatibility)."""
    with _pending_lock:
        _pending_manual.pop(chat_id, None)
    if _state_mgr:
        _state_mgr.clear(chat_id)


def get_pending_manual(chat_id):
    """Get pending manual reminder state (backward compatibility)."""
    with _pending_lock:
        pm = _pending_manual.get(chat_id)
        if pm:
            return dict(pm)
    
    if _state_mgr:
        state = _state_mgr.get(chat_id)
        if state and state.state_type == StateType.MANUAL_REMINDER:
            return {"step": state.step, **state.data}
    return None






def cancel_operation(chat_id: int, message_id: Optional[int] = None):
    """Cancel any pending operations and clear state."""
    cancel_pending_add(chat_id)
    cancel_pending_manual(chat_id)
    with _pending_registration_lock:
        _pending_registration.pop(chat_id, None)
    
    with _pending_schedule_admin_lock:
        _pending_schedule_admin.pop(chat_id, None)
    
    if message_id and global_bot:
        try:
            global_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
        except Exception:
            pass



def register_handlers(bot: telebot.TeleBot, sch_mgr):
    """
    تسجيل المعالجات على كائن bot.
    sch_mgr يجب أن يملك:
      - schedule_homework_reminders(row)
      - remove_hw_jobs(hw_id)
      - scheduler (APScheduler instance)
    
    Note: This function maintains backward compatibility.
    For new code, consider using BotHandlers class from handlers.base
    """
    global global_bot, _state_mgr
    
    
    global_bot = bot
    
    
    _state_mgr = StateManager()
    
    
    from bot_handlers.base import RateLimiter
    rate_limiter = RateLimiter(max_calls=5, period=60)

    def ensure_registration(chat_id: int, user_id: int) -> bool:
        with db_connection() as conn_local:
            if is_user_registration_complete(conn_local, user_id):
                return True
        with _pending_registration_lock:
            if chat_id in _pending_registration:
                return False
            _pending_registration[chat_id] = {"step": "name"}
        try:
            msg = bot.send_message(
                chat_id,
                "📝 لإكمال التسجيل:\n\nيرجى إرسال الاسم واللقب (مثال: خالد السعيد) ثم اختيار المجموعة من الخيارات المتاحة.\n\nأرسل الاسم الآن:",
                reply_markup=registration_kb()
            )
            bot.register_next_step_handler(msg, handle_name_input)
        except Exception:
            logger.exception("Failed to request registration details")
            bot.send_message(chat_id, "حدث خطأ أثناء طلب بيانات التسجيل. حاول مرة أخرى بـ /start.")
        return False

    
    @bot.message_handler(commands=["start"])
    def cmd_start(m):
        
        if not rate_limiter.is_allowed(m.from_user.id):
            try:
                bot.send_message(m.chat.id, "⏳ انتظر قليلاً قبل المحاولة مرة أخرى")
            except Exception:
                pass
            return
        with db_connection() as conn_local:
            ensure_tables(conn_local)
            ts = datetime.now().isoformat()
            username = getattr(m.from_user, "username", None)
            first_name = getattr(m.from_user, "first_name", None)
            last_name = getattr(m.from_user, "last_name", None)
            try:
                register_user(conn_local, m.from_user.id, username, first_name, last_name, ts)
                logger.info(f"Registered user: id={m.from_user.id} username={username} name={first_name} {last_name}")
            except Exception:
                logger.exception("Failed register_user in /start")

            registration_complete = is_user_registration_complete(conn_local, m.from_user.id)
            welcome_kb = main_menu_kb() if registration_complete else registration_kb()

            
            welcome_text = """🎉 **مرحباً بك في Reminder Bot!**

أهلاً وسهلاً بك في بوت التذكيرات والجداول الأسبوعية. أنا هنا لمساعدتك في إدارة واجباتك ومتابعة جدولك الأسبوعي.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 **الأوامر المتاحة:**

• `/start` - بدء استخدام البوت
• `/chatid` - عرض معرف المحادثة
• `/gettopic` - عرض معرف الموضوع (للمجموعات)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **الميزات الرئيسية:**

**1️⃣ إدارة الواجبات (Homeworks)**
   • عرض جميع الواجبات المضافة
   • وضع علامة "تم" على الواجبات المكتملة
   • عرض تفاصيل الواجب (المادة، الوصف، الموعد، الملفات)
   • فتح ملفات PDF المرفقة

**2️⃣ الجدول الأسبوعي (Weekly Schedule)**
   • عرض جدول اليوم الحالي
   • عرض جدول الغد
   • عرض الجدول الأسبوعي الكامل (مع PDF)
   • عرض معلومات الحصة مع رابط Google Maps
   • دعم 4 مجموعات (Group 1, 2, 3, 4)

**3️⃣ التذكيرات المخصصة**
   • إضافة تذكير شخصي
   • جدولة تذكير في وقت محدد
   • تتبع التذكيرات المكتملة

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 **دليل الاستخدام:**

**🔹 للوصول إلى الواجبات:**
   1. اضغط على زر "Homeworks" في القائمة الرئيسية
   2. اختر "📋 قائمة الواجبات" لعرض جميع الواجبات
   3. اضغط على أي واجب لعرض تفاصيله
   4. استخدم زر "✅ تم" لتسجيل إنجاز الواجب

**🔹 للوصول إلى الجدول الأسبوعي:**
   1. اضغط على زر "Weekly Schedule" في القائمة الرئيسية
   2. اختر مجموعتك (Group 1, 2, 3, أو 4)
   3. اختر نوع العرض:
      • 📅 اليوم - حصص اليوم الحالي
      • 📅 الغد - حصص الغد
      • 📅 الأسبوع الكامل - الجدول الكامل مع PDF
   4. اضغط على أي حصة لعرض تفاصيلها ورابط الموقع

**🔹 لإضافة تذكير مخصص:**
   1. من قائمة "Homeworks" → "🔔 تذكيراتي المخصصة"
   2. اضغط "➕ إضافة تذكير"
   3. أدخل نص التذكير
   4. أدخل التاريخ والوقت بصيغة: YYYY-MM-DD HH:MM

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **نصائح للاستخدام الأمثل:**

✓ استخدم زر "✅ تم" لتتبع الواجبات المكتملة
✓ راجع الجدول الأسبوعي يومياً لمعرفة الحصص القادمة
✓ استخدم التذكيرات المخصصة لتذكير نفسك بأمور مهمة
✓ اضغط على أي حصة لعرض رابط Google Maps للموقع
✓ يمكنك إلغاء أي عملية بالضغط على زر "إلغاء"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **ملاحظة مهمة:**
لإكمال التسجيل، يرجى إدخال الاسم واللقب ثم اختيار المجموعة من الخيارات المتاحة كما سيُطلب منك أدناه.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
            
            
            try:
                bot.send_message(m.chat.id, welcome_text, parse_mode='Markdown', reply_markup=welcome_kb)
            except Exception:
                
                try:
                    welcome_text_plain = welcome_text.replace('**', '').replace('`', '')
                    bot.send_message(m.chat.id, welcome_text_plain, reply_markup=welcome_kb)
                except Exception:
                    logger.exception("Failed to send welcome message")

            
            ensure_registration(m.chat.id, m.from_user.id)

    
    @bot.message_handler(commands=['chatid'])
    def cmd_chatid(m):
        if not ensure_registration(m.chat.id, m.from_user.id):
            return
        try:
            bot.send_message(m.chat.id, f"هذا chat.id لهذه المحادثة: {m.chat.id}")
        except Exception:
            logger.exception("Failed to reply to /chatid")

    
    @bot.message_handler(commands=['gettopic'])
    def cmd_gettopic(m):
        if not ensure_registration(m.chat.id, m.from_user.id):
            return
        try:
            thread_id = getattr(m, "message_thread_id", None)
            if thread_id is None and getattr(m, "reply_to_message", None):
                thread_id = getattr(m.reply_to_message, "message_thread_id", None)
            bot.send_message(m.chat.id, f"chat_id: {m.chat.id}\nmessage_thread_id: {thread_id}")
        except Exception:
            logger.exception("Failed in /gettopic")
            bot.send_message(m.chat.id, "فشل الحصول على معلومات الموضوع — راجع اللوغ.")

    
    @bot.message_handler(func=lambda msg: msg.text == "Homeworks")
    def open_hw_menu(m):
        if not ensure_registration(m.chat.id, m.from_user.id):
            return
        kb = hw_main_kb(m.from_user.id)
        bot.send_message(m.chat.id, "قائمة Homeworks:", reply_markup=kb)
        logger.info(f"Opened Homeworks menu for user {m.from_user.id} in chat {m.chat.id}")

    
    @bot.message_handler(func=lambda msg: msg.text == "Weekly Schedule")
    def open_weekly_schedule_menu(m):
        if not ensure_registration(m.chat.id, m.from_user.id):
            return
        kb = weekly_schedule_group_kb()
        bot.send_message(m.chat.id, "Select your Group", reply_markup=kb)
        logger.info(f"Opened Weekly Schedule menu for user {m.from_user.id} in chat {m.chat.id}")

    
    

    
    @bot.callback_query_handler(func=lambda c: True)
    def callbacks(c):
        uid = c.from_user.id
        data = c.data
        chat_id = c.message.chat.id if c.message else None
        logger.info(f"[DEBUG CALLBACK] {datetime.now().isoformat()} | from={uid} | chat={chat_id} | data={data}")

        if data != CALLBACK_HW_CANCEL and chat_id is not None:
            if not ensure_registration(chat_id, uid):
                bot.answer_callback_query(c.id)
                bot.send_message(chat_id, "يرجى إكمال التسجيل أولاً باستخدام /start.", reply_markup=main_menu_kb())
                return

        
        if data == CALLBACK_HW_CANCEL:
            
            cancel_operation(chat_id, c.message.message_id if c.message else None)
            bot.send_message(chat_id, "تم إلغاء العملية.", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return
        
        
        
        
        is_location_callback = (
            data == "schedule_location_add" or
            data.startswith("schedule_location_edit:") or
            data.startswith("schedule_location_edit_url:") or
            data.startswith("schedule_location_delete:") or
            data.startswith("schedule_location_confirm_delete:") or
            data == CALLBACK_WEEKLY_SCHEDULE_ADMIN_LOCATIONS
        )
        is_edit_callback = (
            data.startswith("schedule_edit_type_select:") or
            data.startswith(CALLBACK_SCHEDULE_EDIT_TIME_START) or
            data.startswith(CALLBACK_SCHEDULE_EDIT_TIME_END) or
            data.startswith(CALLBACK_SCHEDULE_EDIT_COURSE) or
            data.startswith(CALLBACK_SCHEDULE_EDIT_LOCATION) or
            data.startswith(CALLBACK_SCHEDULE_EDIT_TYPE) or
            data.startswith(CALLBACK_SCHEDULE_EDIT_ALTERNATING)
        )
        is_alternating_config_callback = (
            data == CALLBACK_ALTERNATING_LIST or
            data.startswith(CALLBACK_ALTERNATING_EDIT) or
            data.startswith(CALLBACK_ALTERNATING_EDIT_DATE) or
            data == CALLBACK_ALTERNATING_ADD or
            data == CALLBACK_WEEKLY_SCHEDULE_ADMIN_ALTERNATING
        )
        
        with _pending_schedule_admin_lock:
            if chat_id in _pending_schedule_admin and not (is_location_callback or is_edit_callback or is_alternating_config_callback):
                pm = _pending_schedule_admin.get(chat_id)
                
                if pm and pm.get("action") not in ["add_location", "edit_location_url", "edit_class", "edit_alternating_config", "add_alternating_config"]:
                    logger.info(f"[SCHEDULE ADMIN] Found pending operation for chat {chat_id}, clearing it due to callback: {data}")
                    _pending_schedule_admin.pop(chat_id, None)
                    

        
        if data == CALLBACK_HW_BACK:
            try:
                if c.message:
                    bot.edit_message_reply_markup(chat_id=chat_id, message_id=c.message.message_id, reply_markup=None)
            except Exception:
                pass
            bot.send_message(chat_id, "عاد للقائمة الرئيسية.", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_HW_LIST:
            with db_connection() as conn_local:
                rows = get_all_homeworks(conn_local)

            if not rows:
                try:
                    bot.edit_message_reply_markup(chat_id=chat_id, message_id=c.message.message_id, reply_markup=None)
                except Exception:
                    pass
                bot.send_message(chat_id, "لا توجد واجبات محفوظة.", reply_markup=main_menu_kb())
                bot.answer_callback_query(c.id)
                return

            try:
                bot.edit_message_reply_markup(chat_id=chat_id, message_id=c.message.message_id, reply_markup=None)
            except Exception:
                pass

            for r in rows:
                text = format_homework_text(r)
                with db_connection() as conn_check:
                    is_done = is_homework_done_for_user(conn_check, r['id'], uid)
                kb = hw_item_kb(uid, r['id'], is_done=is_done)
                bot.send_message(chat_id, text, reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_HW_ADD:
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            start_pending_add(chat_id)
            msg = bot.send_message(chat_id, "أرسل اسم المادة (أو اكتب 'إلغاء'):", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg, hw_add_step_subject, chat_id, uid)
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_HW_VIEW):
            hw_id = int(data.split(":", 1)[1])
            with db_connection() as conn_local:
                r = get_homework(conn_local, hw_id)
            if not r:
                bot.answer_callback_query(c.id, "لم أجد هذا الواجب.", show_alert=True)
                return
            text = format_homework_text(r)
            with db_connection() as conn_check:
                is_done = is_homework_done_for_user(conn_check, r['id'], uid)
            kb = hw_item_kb(uid, r['id'], is_done=is_done)
            try:
                if c.message:
                    bot.edit_message_text(chat_id=chat_id, message_id=c.message.message_id, text=text, reply_markup=kb)
                else:
                    bot.send_message(chat_id, text, reply_markup=kb)
            except Exception:
                bot.send_message(chat_id, text, reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_HW_DONE):
            hw_id = int(data.split(":", 1)[1])
            with db_connection() as conn_local:
                mark_done(conn_local, hw_id, uid)
                
                r = get_homework(conn_local, hw_id)
                is_done = is_homework_done_for_user(conn_local, hw_id, uid)
            if r:
                
                try:
                    if c.message:
                        text = format_homework_text(r)
                        kb = hw_item_kb(uid, hw_id, is_done=is_done)
                        bot.edit_message_text(chat_id=chat_id, message_id=c.message.message_id, text=text, reply_markup=kb)
                    bot.send_message(chat_id, f"✅ تم وسم الواجب (ID:{hw_id}) كـ 'تم' بالنسبة لك.")
                except Exception:
                    bot.send_message(chat_id, f"✅ تم وسم الواجب (ID:{hw_id}) كـ 'تم' بالنسبة لك.")
            else:
                bot.send_message(chat_id, f"✅ تم وسم الواجب (ID:{hw_id}) كـ 'تم' بالنسبة لك.")
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_HW_UNDONE):
            hw_id = int(data.split(":", 1)[1])
            with db_connection() as conn_local:
                mark_undone(conn_local, hw_id, uid)
                
                r = get_homework(conn_local, hw_id)
                is_done = is_homework_done_for_user(conn_local, hw_id, uid)
            if r:
                
                try:
                    if c.message:
                        text = format_homework_text(r)
                        kb = hw_item_kb(uid, hw_id, is_done=is_done)
                        bot.edit_message_text(chat_id=chat_id, message_id=c.message.message_id, text=text, reply_markup=kb)
                    bot.send_message(chat_id, f"❌ تم إلغاء وضع 'تم' للواجب (ID:{hw_id}) بالنسبة لك.")
                except Exception:
                    bot.send_message(chat_id, f"❌ تم إلغاء وضع 'تم' للواجب (ID:{hw_id}) بالنسبة لك.")
            else:
                bot.send_message(chat_id, f"❌ تم إلغاء وضع 'تم' للواجب (ID:{hw_id}) بالنسبة لك.")
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_HW_PDF):
            hw_id = int(data.split(":", 1)[1])
            with db_connection() as conn_local:
                r = get_homework(conn_local, hw_id)
            if not r:
                bot.answer_callback_query(c.id, "لم أجد هذا الواجب.", show_alert=True)
                return
            if r["pdf_type"] == "file_id":
                try:
                    bot.send_document(chat_id, r["pdf_value"])
                except Exception:
                    bot.send_message(chat_id, "فشل إرسال الملف.")
            elif r["pdf_type"] == "url" and r["pdf_value"]:
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("فتح رابط الملف", url=r["pdf_value"]))
                bot.send_message(chat_id, "ملف الواجب:", reply_markup=kb)
            else:
                bot.send_message(chat_id, "لا يوجد ملف مرفق لهذا الواجب.")
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_HW_EDIT:
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            with db_connection() as conn_local:
                rows = get_all_homeworks(conn_local)
            if not rows:
                bot.answer_callback_query(c.id, "لا توجد واجبات.", show_alert=False)
                return
            kb = types.InlineKeyboardMarkup()
            for r in rows:
                kb.add(types.InlineKeyboardButton(f"{r['id']} | {r['subject']} | {r['due_at']}", 
                                                  callback_data=f"{CALLBACK_HW_EDIT_ID}{r['id']}"))
            kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_HW_BACK))
            try:
                if c.message:
                    bot.edit_message_reply_markup(chat_id=chat_id, message_id=c.message.message_id, reply_markup=None)
            except Exception:
                pass
            bot.send_message(chat_id, "اختر واجبًا للتعديل:", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_HW_DELETE:
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            with db_connection() as conn_local:
                rows = get_all_homeworks(conn_local)
            if not rows:
                bot.answer_callback_query(c.id, "لا توجد واجبات.", show_alert=False)
                return
            kb = types.InlineKeyboardMarkup()
            for r in rows:
                kb.add(types.InlineKeyboardButton(f"{r['id']} | {r['subject']} | {r['due_at']}", 
                                                  callback_data=f"{CALLBACK_HW_DELETE_ID}{r['id']}"))
            kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_HW_BACK))
            try:
                if c.message:
                    bot.edit_message_reply_markup(chat_id=chat_id, message_id=c.message.message_id, reply_markup=None)
            except Exception:
                pass
            bot.send_message(chat_id, "اختر واجبًا للحذف:", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_HW_DELETE_ID):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            hw_id = int(data.split(":", 1)[1])
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("نعم احذف", callback_data=f"{CALLBACK_HW_CONFIRM_DELETE}{hw_id}"))
            kb.add(types.InlineKeyboardButton("إلغاء", callback_data=CALLBACK_HW_BACK))
            bot.send_message(chat_id, f"هل أنت متأكد من حذف الواجب ID:{hw_id} ؟", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_HW_CONFIRM_DELETE):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            hw_id = int(data.split(":", 1)[1])
            with db_connection() as conn_local:
                delete_homework(conn_local, hw_id)
            sch_mgr.remove_hw_jobs(hw_id)
            bot.send_message(chat_id, f"حُذف الواجب (ID:{hw_id}).")
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_HW_EDIT_ID):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            hw_id = int(data.split(":", 1)[1])
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("تعديل المادة", callback_data=f"{CALLBACK_HW_EDIT_FIELD}{hw_id}:subject"))
            kb.add(types.InlineKeyboardButton("تعديل الوصف", callback_data=f"{CALLBACK_HW_EDIT_FIELD}{hw_id}:description"))
            kb.add(types.InlineKeyboardButton("تعديل الموعد", callback_data=f"{CALLBACK_HW_EDIT_FIELD}{hw_id}:due_at"))
            kb.add(types.InlineKeyboardButton("تعديل ملف PDF", callback_data=f"{CALLBACK_HW_EDIT_FIELD}{hw_id}:pdf"))
            kb.add(types.InlineKeyboardButton("تعديل الشروط", callback_data=f"{CALLBACK_HW_EDIT_FIELD}{hw_id}:conditions"))
            kb.add(types.InlineKeyboardButton("تعديل التذكيرات", callback_data=f"{CALLBACK_HW_EDIT_FIELD}{hw_id}:reminders"))
            kb.add(types.InlineKeyboardButton("رجوع", callback_data=CALLBACK_HW_BACK))
            bot.send_message(chat_id, "اختر الحقل الذي تريد تعديله:", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_HW_EDIT_FIELD):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            parts = data.split(":")
            hw_id = int(parts[1])
            field = parts[2]
            prompt_map = {
                "subject": "أرسل المادة الجديدة (أو اكتب 'إلغاء'):",
                "description": "أرسل الوصف الجديد (أو اكتب 'إلغاء'):",
                "due_at": "أرسل الموعد الجديد بصيغة YYYY-MM-DD HH:MM (أو 'إلغاء'):",
                "pdf": "أرسل الآن ملف PDF كملف أو رابط URL أو اكتب 'none' لإزالته أو 'إلغاء' لإيقاف:",
                "conditions": "أرسل الشروط الجديدة أو 'none' أو 'إلغاء':",
                "reminders": "أرسل التذكيرات (مثال: default أو 7,3,1) أو 'إلغاء':"
            }
            msg = bot.send_message(chat_id, prompt_map.get(field, "أرسل القيمة الجديدة (أو 'إلغاء'):"), reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg, hw_edit_handle_field, hw_id, field)
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_MANUAL_REMINDER:
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            start_pending_manual(chat_id)
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("أرسل الآن", callback_data=CALLBACK_MANUAL_SEND_NOW))
            kb.add(types.InlineKeyboardButton("جدولة", callback_data=CALLBACK_MANUAL_SCHEDULE))
            kb.add(types.InlineKeyboardButton("إلغاء", callback_data=CALLBACK_HW_CANCEL))
            bot.send_message(chat_id, "هل تريد إرسال التذكير الآن أم جدولة؟", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        if data == CALLBACK_MANUAL_SEND_NOW or data == CALLBACK_MANUAL_SCHEDULE:
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            mode = "now" if data == CALLBACK_MANUAL_SEND_NOW else "schedule"
            with _pending_lock:
                _pending_manual[chat_id] = {"mode": mode, "step": PENDING_STEP_TARGET_TYPE}
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("إلى الجميع", callback_data=CALLBACK_MANUAL_TARGET_ALL))
            kb.add(types.InlineKeyboardButton("إلى user_id", callback_data=CALLBACK_MANUAL_TARGET_USER))
            kb.add(types.InlineKeyboardButton("إلى chat", callback_data=CALLBACK_MANUAL_TARGET_CHAT))
            kb.add(types.InlineKeyboardButton("إلى chat topic (موضوع)", callback_data=CALLBACK_MANUAL_TARGET_CHAT_TOPIC))
            kb.add(types.InlineKeyboardButton("إلغاء", callback_data=CALLBACK_HW_CANCEL))
            bot.send_message(chat_id, "اختر نوع المستهدف:", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        if data.startswith("manual_target_"):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            t = data.split("manual_target_")[1]
            with _pending_lock:
                pm = _pending_manual.get(chat_id) or {}
                pm["target_type"] = t
                
                if t == "all":
                    pm["step"] = PENDING_STEP_ENTER_CONTENT
                elif t == "chat_topic":
                    pm["step"] = PENDING_STEP_ENTER_CHAT
                else:
                    pm["step"] = PENDING_STEP_ENTER_TARGET
                _pending_manual[chat_id] = pm

            if pm["step"] == PENDING_STEP_ENTER_CONTENT:
                msg = bot.send_message(chat_id, "أرسل نص التذكير أو ملف (صورة، صوت، PDF، فيديو، إلخ) أو كليهما:\nيمكنك إرسال ملف أولاً ثم النص، أو النص فقط، أو الملف فقط.", reply_markup=cancel_inline_kb())
                bot.register_next_step_handler(msg, _manual_next_step_handler, chat_id)
            elif pm["step"] == PENDING_STEP_ENTER_TARGET:
                msg = bot.send_message(chat_id, "أدخل قيمة المستهدف (مثلاً user_id أو chat_id) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
                bot.register_next_step_handler(msg, _manual_next_step_handler, chat_id)
            elif pm["step"] == PENDING_STEP_ENTER_CHAT:
                msg = bot.send_message(chat_id, "أدخل chat_id للمجموعة (يمكنك أيضًا الرد داخل الـ topic برسالة). ثم اضغط إرسال:", reply_markup=cancel_inline_kb())
                bot.register_next_step_handler(msg, _manual_next_step_handler, chat_id)
            bot.answer_callback_query(c.id)
            return

        
        
        if data == CALLBACK_CUSTOM_REMINDER:
            bot.send_message(chat_id, "🔔 تذكيراتي المخصصة:", reply_markup=custom_reminder_main_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_CUSTOM_REMINDER_ADD:
            with _pending_lock:
                _pending_manual[chat_id] = {"step": "custom_text", "type": "custom_reminder"}
            msg = bot.send_message(chat_id, "أرسل نص التذكير (أو اكتب 'إلغاء'):", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg, _custom_reminder_step_text, chat_id, uid)
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_CUSTOM_REMINDER_LIST:
            with db_connection() as conn_local:
                reminders = get_all_custom_reminders_for_user(conn_local, uid)
            if not reminders:
                bot.send_message(chat_id, "لا توجد تذكيرات مخصصة.", reply_markup=custom_reminder_main_kb())
                bot.answer_callback_query(c.id)
                return
            for r in reminders:
                with db_connection() as conn_check:
                    is_done = is_custom_reminder_done_for_user(conn_check, r['id'], uid)
                text = f"🔔 تذكير مخصص\n\n{r['text']}\n\n⏰ الموعد: {r['reminder_datetime']}\nID: {r['id']}"
                kb = custom_reminder_item_kb(r['id'], is_done=is_done)
                bot.send_message(chat_id, text, reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_CUSTOM_REMINDER_DELETE):
            reminder_id = int(data.split(":", 1)[1])
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("نعم احذف", callback_data=f"{CALLBACK_CUSTOM_REMINDER_CONFIRM_DELETE}{reminder_id}"))
            kb.add(types.InlineKeyboardButton("إلغاء", callback_data=CALLBACK_CUSTOM_REMINDER_LIST))
            bot.send_message(chat_id, f"هل أنت متأكد من حذف التذكير المخصص ID:{reminder_id}؟", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_CUSTOM_REMINDER_CONFIRM_DELETE):
            reminder_id = int(data.split(":", 1)[1])
            with db_connection() as conn_local:
                deleted = delete_custom_reminder(conn_local, reminder_id, uid)
            if deleted:
                
                try:
                    job_id = f"custom_reminder-{reminder_id}"
                    sch_mgr.scheduler.remove_job(job_id)
                except Exception:
                    pass
                bot.send_message(chat_id, f"تم حذف التذكير المخصص (ID:{reminder_id}).")
            else:
                bot.send_message(chat_id, "لم أجد هذا التذكير أو ليس لديك صلاحية لحذفه.")
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_CUSTOM_REMINDER_DONE):
            reminder_id = int(data.split(":", 1)[1])
            with db_connection() as conn_local:
                mark_custom_reminder_done(conn_local, reminder_id, uid)
                r = get_custom_reminder(conn_local, reminder_id)
                is_done = is_custom_reminder_done_for_user(conn_local, reminder_id, uid)
            if r and r['user_id'] == uid:
                try:
                    if c.message:
                        text = f"🔔 تذكير مخصص\n\n{r['text']}\n\n⏰ الموعد: {r['reminder_datetime']}\nID: {r['id']}"
                        kb = custom_reminder_item_kb(reminder_id, is_done=is_done)
                        bot.edit_message_text(chat_id=chat_id, message_id=c.message.message_id, text=text, reply_markup=kb)
                    bot.send_message(chat_id, f"✅ تم وسم التذكير المخصص (ID:{reminder_id}) كـ 'تم' بالنسبة لك.")
                except Exception:
                    bot.send_message(chat_id, f"✅ تم وسم التذكير المخصص (ID:{reminder_id}) كـ 'تم' بالنسبة لك.")
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_CUSTOM_REMINDER_UNDONE):
            reminder_id = int(data.split(":", 1)[1])
            with db_connection() as conn_local:
                mark_custom_reminder_undone(conn_local, reminder_id, uid)
                r = get_custom_reminder(conn_local, reminder_id)
                is_done = is_custom_reminder_done_for_user(conn_local, reminder_id, uid)
            if r and r['user_id'] == uid:
                try:
                    if c.message:
                        text = f"🔔 تذكير مخصص\n\n{r['text']}\n\n⏰ الموعد: {r['reminder_datetime']}\nID: {r['id']}"
                        kb = custom_reminder_item_kb(reminder_id, is_done=is_done)
                        bot.edit_message_text(chat_id=chat_id, message_id=c.message.message_id, text=text, reply_markup=kb)
                    bot.send_message(chat_id, f"❌ تم إلغاء وضع 'تم' للتذكير المخصص (ID:{reminder_id}) بالنسبة لك.")
                except Exception:
                    bot.send_message(chat_id, f"❌ تم إلغاء وضع 'تم' للتذكير المخصص (ID:{reminder_id}) بالنسبة لك.")
            bot.answer_callback_query(c.id)
            return

        
        
        if data == CALLBACK_WEEKLY_SCHEDULE_ADMIN:
            logger.info(f"[SCHEDULE ADMIN] Callback received: data={data}, uid={uid}, chat_id={chat_id}")
            if not is_admin(uid):
                logger.warning(f"[SCHEDULE ADMIN] User {uid} is not admin")
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            
            reply_chat_id = chat_id
            if not reply_chat_id:
                reply_chat_id = c.from_user.id  
            logger.info(f"[SCHEDULE ADMIN] Using reply_chat_id={reply_chat_id}")
            
            try:
                from db_schedule import get_all_groups
                groups = []
                try:
                    with db_connection() as conn:
                        groups = get_all_groups(conn)
                        logger.info(f"[SCHEDULE ADMIN] Loaded {len(groups)} groups from database: {groups}")
                except Exception as db_error:
                    logger.warning(f"[SCHEDULE ADMIN] Could not load groups from DB: {db_error}, using defaults")
                
                if not groups:
                    groups = ["01", "02", "03", "04"]  
                    logger.info(f"[SCHEDULE ADMIN] Using default groups: {groups}")
                
                kb = schedule_admin_groups_kb(groups)
                logger.info(f"[SCHEDULE ADMIN] Created keyboard with {len(groups)} groups")
                bot.send_message(reply_chat_id, "⚙️ إدارة الجداول الأسبوعية\n\nاختر المجموعة:", reply_markup=kb)
                logger.info(f"[SCHEDULE ADMIN] Sent schedule admin menu to chat {reply_chat_id} for user {uid}")
            except Exception as e:
                logger.exception(f"[SCHEDULE ADMIN] Failed to load schedule admin: {e}")
                error_msg = f"حدث خطأ في تحميل إدارة الجداول.\nالخطأ: {str(e)}"
                try:
                    bot.send_message(reply_chat_id, error_msg, reply_markup=main_menu_kb())
                except Exception as send_error:
                    logger.exception(f"[SCHEDULE ADMIN] Failed to send error message: {send_error}")
                    
                    bot.answer_callback_query(c.id, "حدث خطأ. راجع اللوغ.", show_alert=True)
            finally:
                bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_WEEKLY_SCHEDULE_ADMIN_GROUP):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            group_number = data.split(":", 1)[1]
            if group_number == "new":
                
                bot.send_message(reply_chat_id, "إضافة مجموعة جديدة (سيتم إضافتها لاحقاً)", reply_markup=main_menu_kb())
                bot.answer_callback_query(c.id)
                return
            kb = schedule_admin_days_kb(group_number)
            bot.send_message(reply_chat_id, f"Group {group_number} - اختر اليوم:", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_WEEKLY_SCHEDULE_ADMIN_DAY):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            parts = data.split(":", 1)[1].split(":")
            group_number = parts[0]
            day = parts[1] if len(parts) > 1 else None
            if day:
                kb = schedule_admin_day_menu_kb(group_number, day)
                day_ar = DAY_NAMES_AR.get(day, day)
                bot.send_message(reply_chat_id, f"Group {group_number} - {day_ar}\n\nاختر الإجراء:", reply_markup=kb)
            else:
                kb = schedule_admin_days_kb(group_number)
                bot.send_message(reply_chat_id, f"Group {group_number} - اختر اليوم:", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_WEEKLY_SCHEDULE_ADMIN_VIEW):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            parts = data.split(":", 1)[1].split(":")
            group_number = parts[0]
            day = parts[1] if len(parts) > 1 else None
            try:
                from db_schedule import get_schedule_classes
                with db_connection() as conn:
                    if day:
                        classes = get_schedule_classes(conn, group_number, day)
                        day_ar = DAY_NAMES_AR.get(day, day)
                        if not classes:
                            bot.send_message(reply_chat_id, f"Group {group_number} - {day_ar}\n\nلا توجد حصص في هذا اليوم.", reply_markup=schedule_admin_day_menu_kb(group_number, day))
                        else:
                            text = f"Group {group_number} - {day_ar}\n\n"
                            for cls in classes:
                                text += format_class_for_display(dict(cls)) + "\n\n"
                            kb = schedule_admin_classes_list_kb(group_number, day, [dict(c) for c in classes])
                            bot.send_message(reply_chat_id, text, reply_markup=kb)
                    else:
                        
                        classes = get_schedule_classes(conn, group_number)
                        if not classes:
                            bot.send_message(reply_chat_id, f"Group {group_number}\n\nلا توجد حصص.", reply_markup=schedule_admin_days_kb(group_number))
                        else:
                            text = f"Group {group_number} - الجدول الأسبوعي الكامل\n\n"
                            current_day = None
                            for cls in classes:
                                if cls['day_name'] != current_day:
                                    current_day = cls['day_name']
                                    day_ar = DAY_NAMES_AR.get(current_day, current_day)
                                    text += f"\n📅 {day_ar}:\n"
                                text += format_class_for_display(dict(cls)) + "\n"
                            bot.send_message(reply_chat_id, text, reply_markup=schedule_admin_days_kb(group_number))
            except Exception as e:
                logger.exception("Failed to view schedule")
                bot.send_message(reply_chat_id, f"حدث خطأ في عرض الجدول. راجع اللوغ. الخطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_WEEKLY_SCHEDULE_ADMIN_ADD):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            parts = data.split(":", 1)[1].split(":")
            group_number = parts[0]
            day = parts[1]
            
            with _pending_schedule_admin_lock:
                _pending_schedule_admin[reply_chat_id] = {
                    "action": "add",
                    "group_number": group_number,
                    "day": day,
                    "step": "time_start"
                }
            msg = bot.send_message(reply_chat_id, "أرسل وقت البداية (مثال: 08:00) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg, schedule_admin_add_step_time_start, reply_chat_id)
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_WEEKLY_SCHEDULE_ADMIN_EDIT):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            class_id = int(data.split(":", 1)[1])
            try:
                from db_schedule import get_schedule_class
                with db_connection() as conn:
                    cls = get_schedule_class(conn, class_id)
                    if not cls:
                        bot.send_message(reply_chat_id, "لم أجد هذه الحصة.", reply_markup=main_menu_kb())
                        bot.answer_callback_query(c.id)
                        return
                    cls_dict = dict(cls)
                    text = format_class_for_display(cls_dict)
                    kb = schedule_admin_class_actions_kb(class_id, cls_dict['group_number'], cls_dict['day_name'])
                    bot.send_message(reply_chat_id, text, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to edit schedule class")
                bot.send_message(reply_chat_id, f"حدث خطأ في عرض الحصة. راجع اللوغ. الخطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_WEEKLY_SCHEDULE_ADMIN_DELETE):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            class_id = int(data.split(":", 1)[1])
            try:
                from db_schedule import get_schedule_class
                with db_connection() as conn:
                    cls = get_schedule_class(conn, class_id)
                    if cls:
                        kb = types.InlineKeyboardMarkup()
                        kb.add(types.InlineKeyboardButton("نعم احذف", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_CONFIRM_DELETE}{class_id}"))
                        kb.add(types.InlineKeyboardButton("إلغاء", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_EDIT}{class_id}"))
                        bot.send_message(reply_chat_id, f"هل أنت متأكد من حذف الحصة:\n{format_class_for_display(dict(cls))}", reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to delete schedule class")
                bot.send_message(reply_chat_id, f"حدث خطأ. راجع اللوغ. الخطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_WEEKLY_SCHEDULE_ADMIN_CONFIRM_DELETE):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            class_id = int(data.split(":", 1)[1])
            try:
                from db_schedule import delete_schedule_class, get_schedule_class
                with db_connection() as conn:
                    cls = get_schedule_class(conn, class_id)
                    if cls:
                        delete_schedule_class(conn, class_id)
                        bot.send_message(reply_chat_id, f"تم حذف الحصة (ID: {class_id}).")
                        
                        cls_dict = dict(cls)
                        kb = schedule_admin_day_menu_kb(cls_dict['group_number'], cls_dict['day_name'])
                        bot.send_message(reply_chat_id, f"Group {cls_dict['group_number']} - {DAY_NAMES_AR.get(cls_dict['day_name'], cls_dict['day_name'])}", reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to delete schedule class")
                bot.send_message(reply_chat_id, f"حدث خطأ في حذف الحصة. راجع اللوغ. الخطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_WEEKLY_SCHEDULE_ADMIN_LOCATIONS:
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            try:
                from db_schedule import get_schedule_locations
                with db_connection() as conn:
                    locations = get_schedule_locations(conn)
                    if not locations:
                        text = "📍 إدارة المواقع\n\nلا توجد مواقع مسجلة."
                        kb = types.InlineKeyboardMarkup()
                        kb.add(types.InlineKeyboardButton("➕ إضافة موقع", callback_data="schedule_location_add"))
                        kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN))
                        bot.send_message(reply_chat_id, text, reply_markup=kb)
                    else:
                        text = "📍 إدارة المواقع\n\nالمواقع المسجلة:\n\n"
                        kb = types.InlineKeyboardMarkup()
                        for loc_name, maps_url in sorted(locations.items()):
                            text += f"📍 {loc_name}\n   🔗 {maps_url[:50]}...\n\n"
                            kb.add(types.InlineKeyboardButton(f"✏️ {loc_name}", callback_data=f"schedule_location_edit:{loc_name}"))
                        kb.add(types.InlineKeyboardButton("➕ إضافة موقع", callback_data="schedule_location_add"))
                        kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN))
                        bot.send_message(reply_chat_id, text, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to load locations")
                bot.send_message(reply_chat_id, f"حدث خطأ في تحميل المواقع. راجع اللوغ. الخطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        if data == "schedule_location_add":
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            with _pending_schedule_admin_lock:
                _pending_schedule_admin[reply_chat_id] = {
                    "action": "add_location",
                    "step": "location_name"
                }
            msg = bot.send_message(reply_chat_id, "أرسل اسم الموقع (مثال: Amphi H) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg, schedule_admin_location_step_name, reply_chat_id)
            bot.answer_callback_query(c.id)
            return

        if data.startswith("schedule_location_edit:"):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            location_name = data.split(":", 1)[1]
            try:
                from db_schedule import get_schedule_location
                with db_connection() as conn:
                    maps_url = get_schedule_location(conn, location_name)
                    if maps_url:
                        kb = types.InlineKeyboardMarkup()
                        kb.add(types.InlineKeyboardButton("✏️ تعديل رابط الخريطة", callback_data=f"schedule_location_edit_url:{location_name}"))
                        kb.add(types.InlineKeyboardButton("🗑️ حذف الموقع", callback_data=f"schedule_location_delete:{location_name}"))
                        kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN_LOCATIONS))
                        text = f"📍 الموقع: {location_name}\n\n🔗 رابط الخريطة:\n{maps_url}"
                        bot.send_message(reply_chat_id, text, reply_markup=kb)
                    else:
                        bot.send_message(reply_chat_id, "لم أجد هذا الموقع.", reply_markup=main_menu_kb())
            except Exception as e:
                logger.exception("Failed to load location")
                bot.send_message(reply_chat_id, f"حدث خطأ. راجع اللوغ. الخطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        if data.startswith("schedule_location_edit_url:"):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            location_name = data.split(":", 1)[1]
            with _pending_schedule_admin_lock:
                _pending_schedule_admin[reply_chat_id] = {
                    "action": "edit_location_url",
                    "location_name": location_name,
                    "step": "maps_url"
                }
            msg = bot.send_message(reply_chat_id, f"أرسل رابط Google Maps الجديد للموقع '{location_name}' أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg, schedule_admin_location_step_url, reply_chat_id, location_name)
            bot.answer_callback_query(c.id)
            return

        if data.startswith("schedule_location_delete:"):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            location_name = data.split(":", 1)[1]
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("نعم احذف", callback_data=f"schedule_location_confirm_delete:{location_name}"))
            kb.add(types.InlineKeyboardButton("إلغاء", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN_LOCATIONS))
            bot.send_message(reply_chat_id, f"هل أنت متأكد من حذف الموقع '{location_name}'؟", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        if data.startswith("schedule_location_confirm_delete:"):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            location_name = data.split(":", 1)[1]
            try:
                from db_schedule import delete_schedule_location
                with db_connection() as conn:
                    if delete_schedule_location(conn, location_name):
                        bot.send_message(reply_chat_id, f"✅ تم حذف الموقع '{location_name}'.")
                        
                        from db_schedule import get_schedule_locations
                        locations = get_schedule_locations(conn)
                        if not locations:
                            text = "📍 إدارة المواقع\n\nلا توجد مواقع مسجلة."
                            kb = types.InlineKeyboardMarkup()
                            kb.add(types.InlineKeyboardButton("➕ إضافة موقع", callback_data="schedule_location_add"))
                            kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN))
                            bot.send_message(reply_chat_id, text, reply_markup=kb)
                        else:
                            text = "📍 إدارة المواقع\n\nالمواقع المسجلة:\n\n"
                            kb = types.InlineKeyboardMarkup()
                            for loc_name, maps_url in sorted(locations.items()):
                                text += f"📍 {loc_name}\n   🔗 {maps_url[:50]}...\n\n"
                                kb.add(types.InlineKeyboardButton(f"✏️ {loc_name}", callback_data=f"schedule_location_edit:{loc_name}"))
                            kb.add(types.InlineKeyboardButton("➕ إضافة موقع", callback_data="schedule_location_add"))
                            kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN))
                            bot.send_message(reply_chat_id, text, reply_markup=kb)
                    else:
                        bot.send_message(reply_chat_id, f"لم أجد الموقع '{location_name}'.", reply_markup=main_menu_kb())
            except Exception as e:
                logger.exception("Failed to delete location")
                bot.send_message(reply_chat_id, f"حدث خطأ في حذف الموقع. راجع اللوغ. الخطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        
        if data.startswith(CALLBACK_SCHEDULE_EDIT_TIME_START):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            class_id = int(data.split(":", 1)[1])
            with _pending_schedule_admin_lock:
                _pending_schedule_admin[reply_chat_id] = {
                    "action": "edit_class",
                    "class_id": class_id,
                    "field": "time_start",
                    "step": "enter_value"
                }
            msg = bot.send_message(reply_chat_id, "أرسل وقت البداية الجديد (مثال: 08:00) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg, schedule_admin_edit_class_field_step, reply_chat_id)
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_SCHEDULE_EDIT_TIME_END):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            class_id = int(data.split(":", 1)[1])
            with _pending_schedule_admin_lock:
                _pending_schedule_admin[reply_chat_id] = {
                    "action": "edit_class",
                    "class_id": class_id,
                    "field": "time_end",
                    "step": "enter_value"
                }
            msg = bot.send_message(reply_chat_id, "أرسل وقت الانتهاء الجديد (مثال: 09:30) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg, schedule_admin_edit_class_field_step, reply_chat_id)
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_SCHEDULE_EDIT_COURSE):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            class_id = int(data.split(":", 1)[1])
            with _pending_schedule_admin_lock:
                _pending_schedule_admin[reply_chat_id] = {
                    "action": "edit_class",
                    "class_id": class_id,
                    "field": "course",
                    "step": "enter_value"
                }
            msg = bot.send_message(reply_chat_id, "أرسل اسم المادة الجديد (مثال: Analysis1) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg, schedule_admin_edit_class_field_step, reply_chat_id)
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_SCHEDULE_EDIT_LOCATION):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            class_id = int(data.split(":", 1)[1])
            with _pending_schedule_admin_lock:
                _pending_schedule_admin[reply_chat_id] = {
                    "action": "edit_class",
                    "class_id": class_id,
                    "field": "location",
                    "step": "enter_value"
                }
            msg = bot.send_message(reply_chat_id, "أرسل المكان الجديد (مثال: Amphi H) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg, schedule_admin_edit_class_field_step, reply_chat_id)
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_SCHEDULE_EDIT_TYPE):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            class_id = int(data.split(":", 1)[1])
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Course", callback_data=f"schedule_edit_type_select:{class_id}:Course"))
            kb.add(types.InlineKeyboardButton("Tutorial Session", callback_data=f"schedule_edit_type_select:{class_id}:Tutorial Session"))
            kb.add(types.InlineKeyboardButton("Laboratory Session", callback_data=f"schedule_edit_type_select:{class_id}:Laboratory Session"))
            kb.add(types.InlineKeyboardButton("Online Session", callback_data=f"schedule_edit_type_select:{class_id}:Online Session"))
            kb.add(types.InlineKeyboardButton("إلغاء", callback_data=CALLBACK_HW_CANCEL))
            bot.send_message(reply_chat_id, "اختر نوع الحصة الجديد:", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith("schedule_edit_type_select:"):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            parts = data.split(":", 2)
            class_id = int(parts[1])
            class_type = parts[2]
            try:
                from db_schedule import update_schedule_class_field, get_schedule_class
                with db_connection() as conn:
                    if update_schedule_class_field(conn, class_id, "class_type", class_type):
                        cls = get_schedule_class(conn, class_id)
                        if cls:
                            cls_dict = dict(cls)
                            text = format_class_for_display(cls_dict)
                            kb = schedule_admin_class_actions_kb(class_id, cls_dict['group_number'], cls_dict['day_name'])
                            bot.send_message(reply_chat_id, f"✅ تم تحديث نوع الحصة.\n\n{text}", reply_markup=kb)
                        else:
                            bot.send_message(reply_chat_id, "✅ تم تحديث نوع الحصة.", reply_markup=main_menu_kb())
                    else:
                        bot.send_message(reply_chat_id, "❌ فشل تحديث نوع الحصة.", reply_markup=main_menu_kb())
            except Exception as e:
                logger.exception("Failed to update class type")
                bot.send_message(reply_chat_id, f"حدث خطأ في تحديث نوع الحصة: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_SCHEDULE_EDIT_ALTERNATING):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            class_id = int(data.split(":", 1)[1])
            try:
                from db_schedule import get_schedule_class, update_schedule_class_field
                with db_connection() as conn:
                    cls = get_schedule_class(conn, class_id)
                    if not cls:
                        bot.send_message(reply_chat_id, "لم أجد هذه الحصة.", reply_markup=main_menu_kb())
                        bot.answer_callback_query(c.id)
                        return
                    
                    cls_dict = dict(cls)
                    is_alternating = bool(cls_dict.get('is_alternating', 0))
                    
                    
                    new_alternating = not is_alternating
                    if new_alternating:
                        
                        with _pending_schedule_admin_lock:
                            _pending_schedule_admin[reply_chat_id] = {
                                "action": "edit_class",
                                "class_id": class_id,
                                "field": "alternating",
                                "step": "enter_alternating_key",
                                "is_alternating": True
                            }
                        msg = bot.send_message(reply_chat_id, "أرسل مفتاح الحصة الدورية (مثال: algorithm1) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
                        bot.register_next_step_handler(msg, schedule_admin_edit_class_field_step, reply_chat_id)
                    else:
                        
                        if update_schedule_class_field(conn, class_id, "is_alternating", False):
                            update_schedule_class_field(conn, class_id, "alternating_key", None)
                            cls = get_schedule_class(conn, class_id)
                            if cls:
                                cls_dict = dict(cls)
                                text = format_class_for_display(cls_dict)
                                kb = schedule_admin_class_actions_kb(class_id, cls_dict['group_number'], cls_dict['day_name'])
                                bot.send_message(reply_chat_id, f"✅ تم تعطيل الحالة الدورية.\n\n{text}", reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to update alternating status")
                bot.send_message(reply_chat_id, f"حدث خطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_WEEKLY_SCHEDULE_ADMIN_ALTERNATING:
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            try:
                from db_schedule import get_all_alternating_week_configs
                with db_connection() as conn:
                    configs = get_all_alternating_week_configs(conn)
                    if not configs:
                        text = "🔄 إدارة الحصص الدورية\n\nلا توجد إعدادات للحصص الدورية."
                        kb = types.InlineKeyboardMarkup()
                        kb.add(types.InlineKeyboardButton("➕ إضافة إعداد جديد", callback_data=CALLBACK_ALTERNATING_ADD))
                        kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN))
                        bot.send_message(reply_chat_id, text, reply_markup=kb)
                    else:
                        text = "🔄 إدارة الحصص الدورية\n\nالإعدادات الموجودة:\n\n"
                        configs_list = []
                        for config in configs:
                            config_dict = {
                                'alternating_key': safe_get(config, 'alternating_key', ''),
                                'reference_date': safe_get(config, 'reference_date', ''),
                                'description': safe_get(config, 'description')
                            }
                            configs_list.append(config_dict)
                            text += format_alternating_config_for_display(config_dict) + "\n"
                        kb = alternating_configs_list_kb(configs_list)
                        bot.send_message(reply_chat_id, text, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to load alternating configs")
                bot.send_message(reply_chat_id, f"حدث خطأ في تحميل إعدادات الحصص الدورية: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        if data == CALLBACK_ALTERNATING_LIST:
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            try:
                from db_schedule import get_all_alternating_week_configs
                with db_connection() as conn:
                    configs = get_all_alternating_week_configs(conn)
                    if not configs:
                        text = "🔄 إدارة الحصص الدورية\n\nلا توجد إعدادات للحصص الدورية."
                        kb = types.InlineKeyboardMarkup()
                        kb.add(types.InlineKeyboardButton("➕ إضافة إعداد جديد", callback_data=CALLBACK_ALTERNATING_ADD))
                        kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN))
                        bot.send_message(reply_chat_id, text, reply_markup=kb)
                    else:
                        text = "🔄 إدارة الحصص الدورية\n\nالإعدادات الموجودة:\n\n"
                        configs_list = []
                        for config in configs:
                            config_dict = {
                                'alternating_key': safe_get(config, 'alternating_key', ''),
                                'reference_date': safe_get(config, 'reference_date', ''),
                                'description': safe_get(config, 'description')
                            }
                            configs_list.append(config_dict)
                            text += format_alternating_config_for_display(config_dict) + "\n"
                        kb = alternating_configs_list_kb(configs_list)
                        bot.send_message(reply_chat_id, text, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to load alternating configs")
                bot.send_message(reply_chat_id, f"حدث خطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_ALTERNATING_EDIT):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            alternating_key = data.split(":", 1)[1]
            try:
                from db_schedule import get_alternating_week_config
                with db_connection() as conn:
                    config = get_alternating_week_config(conn, alternating_key)
                    if not config:
                        bot.send_message(reply_chat_id, "لم أجد هذا الإعداد.", reply_markup=main_menu_kb())
                        bot.answer_callback_query(c.id)
                        return
                    config_dict = {
                        'alternating_key': safe_get(config, 'alternating_key', ''),
                        'reference_date': safe_get(config, 'reference_date', ''),
                        'description': safe_get(config, 'description')
                    }
                    text = format_alternating_config_for_display(config_dict)
                    kb = alternating_config_actions_kb(alternating_key)
                    bot.send_message(reply_chat_id, text, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to load alternating config")
                bot.send_message(reply_chat_id, f"حدث خطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        if data.startswith(CALLBACK_ALTERNATING_EDIT_DATE):
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            alternating_key = data.split(":", 1)[1]
            with _pending_schedule_admin_lock:
                _pending_schedule_admin[reply_chat_id] = {
                    "action": "edit_alternating_config",
                    "alternating_key": alternating_key,
                    "field": "reference_date",
                    "step": "enter_value"
                }
            msg = bot.send_message(reply_chat_id, f"أرسل تاريخ المرجع الجديد بصيغة YYYY-MM-DD (مثال: 2024-11-11) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg, schedule_admin_edit_alternating_config_step, reply_chat_id)
            bot.answer_callback_query(c.id)
            return

        if data == CALLBACK_ALTERNATING_ADD:
            if not is_admin(uid):
                bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
                return
            
            reply_chat_id = chat_id or c.from_user.id
            with _pending_schedule_admin_lock:
                _pending_schedule_admin[reply_chat_id] = {
                    "action": "add_alternating_config",
                    "step": "enter_key"
                }
            msg = bot.send_message(reply_chat_id, "أرسل مفتاح الحصة الدورية (مثال: algorithm1) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg, schedule_admin_add_alternating_config_step_key, reply_chat_id)
            bot.answer_callback_query(c.id)
            return

        
        
        if data == CALLBACK_WEEKLY_SCHEDULE:
            kb = weekly_schedule_group_kb()
            try:
                if c.message:
                    bot.edit_message_text(chat_id=chat_id, message_id=c.message.message_id, text="Select your Group", reply_markup=kb)
                else:
                    bot.send_message(chat_id, "Select your Group", reply_markup=kb)
            except Exception:
                bot.send_message(chat_id, "Select your Group", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_WEEKLY_SCHEDULE_GROUP_01:
            kb = weekly_schedule_time_kb("01")
            bot.send_message(chat_id, "Group 01 - اختر التوقيت:", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        if data == CALLBACK_WEEKLY_SCHEDULE_GROUP_02:
            kb = weekly_schedule_time_kb("02")
            bot.send_message(chat_id, "Group 02 - اختر التوقيت:", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        if data == CALLBACK_WEEKLY_SCHEDULE_GROUP_03:
            kb = weekly_schedule_time_kb("03")
            bot.send_message(chat_id, "Group 03 - اختر التوقيت:", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        if data == CALLBACK_WEEKLY_SCHEDULE_GROUP_04:
            kb = weekly_schedule_time_kb("04")
            bot.send_message(chat_id, "Group 4 - اختر التوقيت:", reply_markup=kb)
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_WEEKLY_SCHEDULE_TODAY):
            group_number = data.split(":", 1)[1]
            try:
                from weekly_schedule import get_today_schedule_entries, format_single_class_message
                from bot_handlers.weekly_schedule_helpers import class_entry_keyboard
                
                entries = get_today_schedule_entries(group_number)
                
                if not entries:
                    bot.send_message(chat_id, "📅 اليوم\n\nلا توجد حصص في هذا اليوم.", reply_markup=main_menu_kb())
                else:
                    
                    for entry in entries:
                        message_text = format_single_class_message(entry)
                        kb = class_entry_keyboard(entry, group_number, entry.get("day_ar", ""))
                        if kb:
                            bot.send_message(chat_id, message_text, reply_markup=kb)
                        else:
                            bot.send_message(chat_id, message_text)
            except Exception as e:
                logger.exception("Failed to get today's schedule")
                bot.send_message(chat_id, f"حدث خطأ في جلب جدول اليوم. راجع اللوغ.", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_WEEKLY_SCHEDULE_TOMORROW):
            group_number = data.split(":", 1)[1]
            try:
                from weekly_schedule import get_tomorrow_schedule_entries, format_single_class_message
                from bot_handlers.weekly_schedule_helpers import class_entry_keyboard
                
                entries = get_tomorrow_schedule_entries(group_number)
                
                if not entries:
                    bot.send_message(chat_id, "📅 الغد\n\nلا توجد حصص في هذا اليوم.", reply_markup=main_menu_kb())
                else:
                    
                    for entry in entries:
                        message_text = format_single_class_message(entry)
                        kb = class_entry_keyboard(entry, group_number, entry.get("day_ar", ""))
                        if kb:
                            bot.send_message(chat_id, message_text, reply_markup=kb)
                        else:
                            bot.send_message(chat_id, message_text)
            except Exception as e:
                logger.exception("Failed to get tomorrow's schedule")
                bot.send_message(chat_id, f"حدث خطأ في جلب جدول الغد. راجع اللوغ.", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data.startswith(CALLBACK_WEEKLY_SCHEDULE_WEEK):
            group_number = data.split(":", 1)[1]
            try:
                from weekly_schedule import format_weekly_schedule
                schedule_text = format_weekly_schedule(group_number)
                
                
                if not schedule_text or not schedule_text.strip():
                    logger.warning(f"format_weekly_schedule returned empty text for group {group_number}")
                    schedule_text = f"📅 الجدول الأسبوعي الكامل - Group {group_number}\n\nلا توجد حصص مسجلة لهذه المجموعة.\n\nيرجى إضافة الحصص من قائمة الإدارة (Admin)."
                
                bot.send_message(chat_id, schedule_text, reply_markup=main_menu_kb())
                
                
                try:
                    from config import SCHEDULES_DIR
                    import os
                    if SCHEDULES_DIR and os.path.exists(SCHEDULES_DIR):
                        
                        pdf_filename = f"weekly_schedule_group_{group_number}.pdf"
                        pdf_path = os.path.join(SCHEDULES_DIR, pdf_filename)
                        
                        if os.path.exists(pdf_path):
                            
                            with open(pdf_path, 'rb') as pdf_file:
                                bot.send_document(chat_id, pdf_file, caption=f"📄 الجدول الأسبوعي الكامل - Group {group_number}")
                            logger.info(f"Sent PDF schedule for Group {group_number}")
                        else:
                            
                            pdf_all_path = os.path.join(SCHEDULES_DIR, "weekly_schedule_all.pdf")
                            if os.path.exists(pdf_all_path):
                                with open(pdf_all_path, 'rb') as pdf_file:
                                    bot.send_document(chat_id, pdf_file, caption=f"📄 الجدول الأسبوعي الكامل - Group {group_number}")
                                logger.info(f"Sent general PDF schedule for Group {group_number}")
                            else:
                                logger.debug(f"PDF schedule file not found for Group {group_number}")
                except Exception as pdf_error:
                    
                    logger.warning(f"Failed to send PDF schedule: {pdf_error}")
                    
            except Exception as e:
                logger.exception(f"Failed to get weekly schedule for group {group_number}: {e}")
                error_msg = f"حدث خطأ في جلب الجدول الأسبوعي لمجموعة {group_number}.\n\nالخطأ: {str(e)}\n\nيرجى التحقق من قاعدة البيانات أو الاتصال بالأدمين."
                try:
                    bot.send_message(chat_id, error_msg, reply_markup=main_menu_kb())
                except Exception as send_error:
                    logger.exception(f"Failed to send error message: {send_error}")
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_NOTIFICATION_SETTINGS:
            reply_chat_id = chat_id or c.from_user.id
            try:
                with db_connection() as conn:
                    settings = get_notification_settings(conn, uid)
                    if settings:
                        
                        homework_enabled = bool(safe_get(settings, 'homework_reminders_enabled', 1))
                        manual_enabled = bool(safe_get(settings, 'manual_reminders_enabled', 1))
                        custom_enabled = bool(safe_get(settings, 'custom_reminders_enabled', 1))
                    else:
                        
                        homework_enabled = True
                        manual_enabled = True
                        custom_enabled = True
                    
                    text = "🔕 **إعدادات الإشعارات**\n\n"
                    text += "يمكنك اختيار أنواع الإشعارات التي تريد استقبالها:\n\n"
                    text += f"• تذكيرات الواجبات: {'✅ مفعّلة' if homework_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيرات الأدمين: {'✅ مفعّلة' if manual_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيراتي المخصصة: {'✅ مفعّلة' if custom_enabled else '❌ معطّلة'}\n\n"
                    text += "اضغط على الزر لتغيير الإعداد."
                    
                    kb = notification_settings_kb(homework_enabled, manual_enabled, custom_enabled)
                    try:
                        bot.send_message(reply_chat_id, text, parse_mode='Markdown', reply_markup=kb)
                    except Exception:
                        
                        text_plain = text.replace('**', '').replace('`', '')
                        bot.send_message(reply_chat_id, text_plain, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to load notification settings")
                bot.send_message(reply_chat_id, f"حدث خطأ في تحميل إعدادات الإشعارات: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_NOTIFICATION_DISABLE_HOMEWORK:
            reply_chat_id = chat_id or c.from_user.id
            try:
                with db_connection() as conn:
                    set_notification_setting(conn, uid, 'homework_reminders', False)
                    
                    settings = get_notification_settings(conn, uid)
                    if settings:
                        homework_enabled = bool(safe_get(settings, 'homework_reminders_enabled', 1))
                        manual_enabled = bool(safe_get(settings, 'manual_reminders_enabled', 1))
                        custom_enabled = bool(safe_get(settings, 'custom_reminders_enabled', 1))
                    else:
                        homework_enabled = False
                        manual_enabled = True
                        custom_enabled = True
                    text = "🔕 **إعدادات الإشعارات**\n\n✅ تم إيقاف تذكيرات الواجبات.\n\n"
                    text += "يمكنك اختيار أنواع الإشعارات التي تريد استقبالها:\n\n"
                    text += f"• تذكيرات الواجبات: {'✅ مفعّلة' if homework_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيرات الأدمين: {'✅ مفعّلة' if manual_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيراتي المخصصة: {'✅ مفعّلة' if custom_enabled else '❌ معطّلة'}\n\n"
                    text += "اضغط على الزر لتغيير الإعداد."
                    kb = notification_settings_kb(homework_enabled, manual_enabled, custom_enabled)
                    try:
                        bot.send_message(reply_chat_id, text, parse_mode='Markdown', reply_markup=kb)
                    except Exception:
                        text_plain = text.replace('**', '').replace('`', '')
                        bot.send_message(reply_chat_id, text_plain, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to disable homework reminders")
                bot.send_message(reply_chat_id, f"حدث خطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_NOTIFICATION_ENABLE_HOMEWORK:
            reply_chat_id = chat_id or c.from_user.id
            try:
                with db_connection() as conn:
                    set_notification_setting(conn, uid, 'homework_reminders', True)
                    
                    settings = get_notification_settings(conn, uid)
                    if settings:
                        homework_enabled = bool(safe_get(settings, 'homework_reminders_enabled', 1))
                        manual_enabled = bool(safe_get(settings, 'manual_reminders_enabled', 1))
                        custom_enabled = bool(safe_get(settings, 'custom_reminders_enabled', 1))
                    else:
                        homework_enabled = True
                        manual_enabled = True
                        custom_enabled = True
                    text = "🔕 **إعدادات الإشعارات**\n\n✅ تم تفعيل تذكيرات الواجبات.\n\n"
                    text += "يمكنك اختيار أنواع الإشعارات التي تريد استقبالها:\n\n"
                    text += f"• تذكيرات الواجبات: {'✅ مفعّلة' if homework_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيرات الأدمين: {'✅ مفعّلة' if manual_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيراتي المخصصة: {'✅ مفعّلة' if custom_enabled else '❌ معطّلة'}\n\n"
                    text += "اضغط على الزر لتغيير الإعداد."
                    kb = notification_settings_kb(homework_enabled, manual_enabled, custom_enabled)
                    try:
                        bot.send_message(reply_chat_id, text, parse_mode='Markdown', reply_markup=kb)
                    except Exception:
                        text_plain = text.replace('**', '').replace('`', '')
                        bot.send_message(reply_chat_id, text_plain, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to enable homework reminders")
                bot.send_message(reply_chat_id, f"حدث خطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_NOTIFICATION_DISABLE_MANUAL:
            reply_chat_id = chat_id or c.from_user.id
            try:
                with db_connection() as conn:
                    set_notification_setting(conn, uid, 'manual_reminders', False)
                    
                    settings = get_notification_settings(conn, uid)
                    if settings:
                        homework_enabled = bool(safe_get(settings, 'homework_reminders_enabled', 1))
                        manual_enabled = bool(safe_get(settings, 'manual_reminders_enabled', 1))
                        custom_enabled = bool(safe_get(settings, 'custom_reminders_enabled', 1))
                    else:
                        homework_enabled = True
                        manual_enabled = False
                        custom_enabled = True
                    text = "🔕 **إعدادات الإشعارات**\n\n✅ تم إيقاف تذكيرات الأدمين.\n\n"
                    text += "يمكنك اختيار أنواع الإشعارات التي تريد استقبالها:\n\n"
                    text += f"• تذكيرات الواجبات: {'✅ مفعّلة' if homework_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيرات الأدمين: {'✅ مفعّلة' if manual_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيراتي المخصصة: {'✅ مفعّلة' if custom_enabled else '❌ معطّلة'}\n\n"
                    text += "اضغط على الزر لتغيير الإعداد."
                    kb = notification_settings_kb(homework_enabled, manual_enabled, custom_enabled)
                    try:
                        bot.send_message(reply_chat_id, text, parse_mode='Markdown', reply_markup=kb)
                    except Exception:
                        text_plain = text.replace('**', '').replace('`', '')
                        bot.send_message(reply_chat_id, text_plain, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to disable manual reminders")
                bot.send_message(reply_chat_id, f"حدث خطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_NOTIFICATION_ENABLE_MANUAL:
            reply_chat_id = chat_id or c.from_user.id
            try:
                with db_connection() as conn:
                    set_notification_setting(conn, uid, 'manual_reminders', True)
                    
                    settings = get_notification_settings(conn, uid)
                    if settings:
                        homework_enabled = bool(safe_get(settings, 'homework_reminders_enabled', 1))
                        manual_enabled = bool(safe_get(settings, 'manual_reminders_enabled', 1))
                        custom_enabled = bool(safe_get(settings, 'custom_reminders_enabled', 1))
                    else:
                        homework_enabled = True
                        manual_enabled = True
                        custom_enabled = True
                    text = "🔕 **إعدادات الإشعارات**\n\n✅ تم تفعيل تذكيرات الأدمين.\n\n"
                    text += "يمكنك اختيار أنواع الإشعارات التي تريد استقبالها:\n\n"
                    text += f"• تذكيرات الواجبات: {'✅ مفعّلة' if homework_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيرات الأدمين: {'✅ مفعّلة' if manual_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيراتي المخصصة: {'✅ مفعّلة' if custom_enabled else '❌ معطّلة'}\n\n"
                    text += "اضغط على الزر لتغيير الإعداد."
                    kb = notification_settings_kb(homework_enabled, manual_enabled, custom_enabled)
                    try:
                        bot.send_message(reply_chat_id, text, parse_mode='Markdown', reply_markup=kb)
                    except Exception:
                        text_plain = text.replace('**', '').replace('`', '')
                        bot.send_message(reply_chat_id, text_plain, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to enable manual reminders")
                bot.send_message(reply_chat_id, f"حدث خطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_NOTIFICATION_DISABLE_CUSTOM:
            reply_chat_id = chat_id or c.from_user.id
            try:
                with db_connection() as conn:
                    set_notification_setting(conn, uid, 'custom_reminders', False)
                    
                    settings = get_notification_settings(conn, uid)
                    if settings:
                        homework_enabled = bool(safe_get(settings, 'homework_reminders_enabled', 1))
                        manual_enabled = bool(safe_get(settings, 'manual_reminders_enabled', 1))
                        custom_enabled = bool(safe_get(settings, 'custom_reminders_enabled', 1))
                    else:
                        homework_enabled = True
                        manual_enabled = True
                        custom_enabled = False
                    text = "🔕 **إعدادات الإشعارات**\n\n✅ تم إيقاف تذكيراتي المخصصة.\n\n"
                    text += "يمكنك اختيار أنواع الإشعارات التي تريد استقبالها:\n\n"
                    text += f"• تذكيرات الواجبات: {'✅ مفعّلة' if homework_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيرات الأدمين: {'✅ مفعّلة' if manual_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيراتي المخصصة: {'✅ مفعّلة' if custom_enabled else '❌ معطّلة'}\n\n"
                    text += "اضغط على الزر لتغيير الإعداد."
                    kb = notification_settings_kb(homework_enabled, manual_enabled, custom_enabled)
                    try:
                        bot.send_message(reply_chat_id, text, parse_mode='Markdown', reply_markup=kb)
                    except Exception:
                        text_plain = text.replace('**', '').replace('`', '')
                        bot.send_message(reply_chat_id, text_plain, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to disable custom reminders")
                bot.send_message(reply_chat_id, f"حدث خطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_NOTIFICATION_ENABLE_CUSTOM:
            reply_chat_id = chat_id or c.from_user.id
            try:
                with db_connection() as conn:
                    set_notification_setting(conn, uid, 'custom_reminders', True)
                    
                    settings = get_notification_settings(conn, uid)
                    if settings:
                        homework_enabled = bool(safe_get(settings, 'homework_reminders_enabled', 1))
                        manual_enabled = bool(safe_get(settings, 'manual_reminders_enabled', 1))
                        custom_enabled = bool(safe_get(settings, 'custom_reminders_enabled', 1))
                    else:
                        homework_enabled = True
                        manual_enabled = True
                        custom_enabled = True
                    text = "🔕 **إعدادات الإشعارات**\n\n✅ تم تفعيل تذكيراتي المخصصة.\n\n"
                    text += "يمكنك اختيار أنواع الإشعارات التي تريد استقبالها:\n\n"
                    text += f"• تذكيرات الواجبات: {'✅ مفعّلة' if homework_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيرات الأدمين: {'✅ مفعّلة' if manual_enabled else '❌ معطّلة'}\n"
                    text += f"• تذكيراتي المخصصة: {'✅ مفعّلة' if custom_enabled else '❌ معطّلة'}\n\n"
                    text += "اضغط على الزر لتغيير الإعداد."
                    kb = notification_settings_kb(homework_enabled, manual_enabled, custom_enabled)
                    try:
                        bot.send_message(reply_chat_id, text, parse_mode='Markdown', reply_markup=kb)
                    except Exception:
                        text_plain = text.replace('**', '').replace('`', '')
                        bot.send_message(reply_chat_id, text_plain, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to enable custom reminders")
                bot.send_message(reply_chat_id, f"حدث خطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_NOTIFICATION_DISABLE_ALL:
            reply_chat_id = chat_id or c.from_user.id
            try:
                with db_connection() as conn:
                    disable_all_notifications(conn, uid)
                    text = "🔕 **إعدادات الإشعارات**\n\n✅ تم إيقاف جميع الإشعارات.\n\n"
                    text += "يمكنك اختيار أنواع الإشعارات التي تريد استقبالها:\n\n"
                    text += "• تذكيرات الواجبات: ❌ معطّلة\n"
                    text += "• تذكيرات الأدمين: ❌ معطّلة\n"
                    text += "• تذكيراتي المخصصة: ❌ معطّلة\n\n"
                    text += "اضغط على الزر لتغيير الإعداد."
                    kb = notification_settings_kb(False, False, False)
                    try:
                        bot.send_message(reply_chat_id, text, parse_mode='Markdown', reply_markup=kb)
                    except Exception:
                        text_plain = text.replace('**', '').replace('`', '')
                        bot.send_message(reply_chat_id, text_plain, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to disable all notifications")
                bot.send_message(reply_chat_id, f"حدث خطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        
        if data == CALLBACK_NOTIFICATION_ENABLE_ALL:
            reply_chat_id = chat_id or c.from_user.id
            try:
                with db_connection() as conn:
                    enable_all_notifications(conn, uid)
                    text = "🔕 **إعدادات الإشعارات**\n\n✅ تم استعادة جميع الإشعارات.\n\n"
                    text += "يمكنك اختيار أنواع الإشعارات التي تريد استقبالها:\n\n"
                    text += "• تذكيرات الواجبات: ✅ مفعّلة\n"
                    text += "• تذكيرات الأدمين: ✅ مفعّلة\n"
                    text += "• تذكيراتي المخصصة: ✅ مفعّلة\n\n"
                    text += "اضغط على الزر لتغيير الإعداد."
                    kb = notification_settings_kb(True, True, True)
                    try:
                        bot.send_message(reply_chat_id, text, parse_mode='Markdown', reply_markup=kb)
                    except Exception:
                        text_plain = text.replace('**', '').replace('`', '')
                        bot.send_message(reply_chat_id, text_plain, reply_markup=kb)
            except Exception as e:
                logger.exception("Failed to enable all notifications")
                bot.send_message(reply_chat_id, f"حدث خطأ: {e}", reply_markup=main_menu_kb())
            bot.answer_callback_query(c.id)
            return

        bot.answer_callback_query(c.id)

    
    def hw_add_step_subject(msg, chat_id, admin_id):
        if not is_pending_add(chat_id) or is_cancel_text(getattr(msg, "text", "")):
            cancel_pending_add(chat_id)
            bot.send_message(chat_id, "تم إلغاء إضافة الواجب.", reply_markup=main_menu_kb())
            return
        subject = (msg.text or "").strip()
        is_valid, error = validate_text_input(subject)
        if not is_valid:
            m = bot.send_message(chat_id, f"خطأ: {error}. أرسل اسم المادة مرة أخرى (أو 'إلغاء'):", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, hw_add_step_subject, chat_id, admin_id)
            return
        m = bot.send_message(chat_id, "أرسل وصفًا مختصرًا للواجب (أو اكتب 'إلغاء'):", reply_markup=cancel_inline_kb())
        bot.register_next_step_handler(m, hw_add_step_description, subject, chat_id, admin_id)

    def hw_add_step_description(msg, subject, chat_id, admin_id):
        if not is_pending_add(chat_id) or is_cancel_text(getattr(msg, "text", "")):
            cancel_pending_add(chat_id)
            bot.send_message(chat_id, "تم إلغاء إضافة الواجب.", reply_markup=main_menu_kb())
            return
        description = (msg.text or "").strip()
        is_valid, error = validate_text_input(description, MAX_DESCRIPTION_LENGTH)
        if not is_valid:
            m = bot.send_message(chat_id, f"خطأ: {error}. أرسل الوصف مرة أخرى (أو 'إلغاء'):", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, hw_add_step_description, subject, chat_id, admin_id)
            return
        m = bot.send_message(chat_id, "أرسل الموعد بصيغة: YYYY-MM-DD HH:MM (أو اكتب 'إلغاء')", reply_markup=cancel_inline_kb())
        bot.register_next_step_handler(m, hw_add_step_due, subject, description, chat_id, admin_id)

    def hw_add_step_due(msg, subject, description, chat_id, admin_id):
        if not is_pending_add(chat_id):
            cancel_pending_add(chat_id)
            bot.send_message(chat_id, "تم إلغاء إضافة الواجب.", reply_markup=main_menu_kb())
            return
        text = (msg.text or "").strip()
        is_valid, error, due_str = validate_datetime(text)
        if not is_valid:
            if error == "تم الإلغاء":
                cancel_pending_add(chat_id)
                bot.send_message(chat_id, "تم إلغاء إضافة الواجب.", reply_markup=main_menu_kb())
                return
            m = bot.send_message(chat_id, f"خطأ: {error}. أرسل الموعد مرة أخرى (أو 'إلغاء'):", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, hw_add_step_due, subject, description, chat_id, admin_id)
            return
        m = bot.send_message(chat_id, "أرسل ملف الـ PDF كملف (document) أو رابط URL، أو اكتب 'none'، أو 'إلغاء':", reply_markup=cancel_inline_kb())
        bot.register_next_step_handler(m, hw_add_step_pdf, subject, description, due_str, chat_id, admin_id)

    def hw_add_step_pdf(msg, subject, description, due_str, chat_id, admin_id):
        if not is_pending_add(chat_id):
            cancel_pending_add(chat_id)
            bot.send_message(chat_id, "تم إلغاء إضافة الواجب.", reply_markup=main_menu_kb())
            return
        
        pdf_type = None
        pdf_value = None
        
        if msg.content_type == 'document':
            pdf_type = "file_id"
            pdf_value = msg.document.file_id
        else:
            txt = (msg.text or "").strip()
            if is_cancel_text(txt):
                cancel_pending_add(chat_id)
                bot.send_message(chat_id, "تم إلغاء إضافة الواجب.", reply_markup=main_menu_kb())
                return
            if txt.lower() == "none":
                pdf_type = None
                pdf_value = None
            else:
                is_valid, url, error = validate_url(txt)
                if not is_valid:
                    m = bot.send_message(chat_id, f"خطأ: {error}. أرسل رابط URL صحيح أو 'none' أو 'إلغاء':", reply_markup=cancel_inline_kb())
                    bot.register_next_step_handler(m, hw_add_step_pdf, subject, description, due_str, chat_id, admin_id)
                    return
                pdf_type = "url"
                pdf_value = url
        
        m = bot.send_message(chat_id, "لمن التذكير؟ اكتب 'all' للجميع أو اكتب رقم (user_id) للمستخدم المستهدف، أو اكتب 'none' للجميع:", reply_markup=cancel_inline_kb())
        bot.register_next_step_handler(m, hw_add_step_target, subject, description, due_str, pdf_type, pdf_value, chat_id, admin_id)

    def hw_add_step_target(msg, subject, description, due_str, pdf_type, pdf_value, chat_id, admin_id):
        if not is_pending_add(chat_id) or is_cancel_text(getattr(msg, "text", "")):
            cancel_pending_add(chat_id)
            bot.send_message(chat_id, "تم إلغاء إضافة الواجب.", reply_markup=main_menu_kb())
            return
        
        target_text = (msg.text or "").strip()
        is_valid, target_user_id, error = validate_user_id(target_text)
        
        if not is_valid:
            m2 = bot.send_message(chat_id, f"خطأ: {error}. اكتب 'all' أو رقم user_id أو 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m2, hw_add_step_target, subject, description, due_str, pdf_type, pdf_value, chat_id, admin_id)
            return

        
        if target_user_id is not None:
            with db_connection() as conn_local:
                if not is_user_registered(conn_local, target_user_id):
                    bot.send_message(chat_id, f"تنبيه: المستخدم (ID:{target_user_id}) لم يبدأ محادثة خاصة مع البوت. اطلب منه إرسال /start في الخاص أو اكتب 'all'.")
        
        m = bot.send_message(chat_id, "اختر التذكيرات: اترك 'default' (3,2,1) أو اكتب قائمة أيام مفصولة بفواصل (مثال: 7,3,1) أو 'إلغاء':", reply_markup=cancel_inline_kb())
        
        conditions = ""
        bot.register_next_step_handler(m, hw_add_step_finalize, subject, description, due_str, pdf_type, pdf_value, conditions, chat_id, admin_id, target_user_id)

    def hw_add_step_finalize(msg, subject, description, due_str, pdf_type, pdf_value, cond, chat_id, admin_id, target_user_id):
        if not is_pending_add(chat_id) or is_cancel_text(getattr(msg, "text", "")):
            cancel_pending_add(chat_id)
            bot.send_message(chat_id, "تم إلغاء إضافة الواجب.", reply_markup=main_menu_kb())
            return
        
        choice = (msg.text or "").strip()
        is_valid, reminders, error = validate_reminders(choice)
        if not is_valid:
            m = bot.send_message(chat_id, f"خطأ: {error}. أرسل التذكيرات مرة أخرى (أو 'إلغاء'):", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, hw_add_step_finalize, subject, description, due_str, pdf_type, pdf_value, cond, chat_id, admin_id, target_user_id)
            return

        with db_connection() as conn_local:
            hid = insert_homework(conn_local, subject, description, due_str, pdf_type, pdf_value, cond, admin_id, chat_id, reminders, target_user_id)
        
        cancel_pending_add(chat_id)
        bot.send_message(chat_id, f"تم إضافة الواجب (ID: {hid}). سيتم تذكير الجهة المحددة حسب الإعداد.", reply_markup=main_menu_kb())
        
        
        with db_connection() as conn_local2:
            row = get_homework(conn_local2, hid)
        try:
            sch_mgr.schedule_homework_reminders(row)
        except Exception:
            logger.exception("Failed scheduling reminders after insert")

    
    def _prompt_registration_input(chat_id: int, message: str, handler, include_groups: bool = False):
        try:
            msg_retry = bot.send_message(chat_id, message, reply_markup=registration_kb(include_groups=include_groups))
            bot.register_next_step_handler(msg_retry, handler)
        except Exception:
            logger.exception("Failed to prompt for registration input")
            bot.send_message(chat_id, "حدث خطأ أثناء طلب بيانات التسجيل. حاول مرة أخرى بـ /start.")

    def handle_name_input(msg):
        chat_id = msg.chat.id
        text = (msg.text or "").strip()
        if is_main_menu_button(text):
            _prompt_registration_input(chat_id, "يرجى إدخال الاسم واللقب أولاً لإكمال التسجيل.", handle_name_input)
            return
        with _pending_registration_lock:
            pending = _pending_registration.get(chat_id)
        if is_cancel_text(text) or not pending or not isinstance(pending, dict):
            with _pending_registration_lock:
                _pending_registration.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء إدخال الاسم.", reply_markup=main_menu_kb())
            return
        if pending.get("step") != "name":
            bot.send_message(chat_id, "رجاءً اكتب /start لإعادة بدء التسجيل.", reply_markup=main_menu_kb())
            return

        is_valid, error = validate_text_input(text, MAX_INPUT_LENGTH)
        if not is_valid:
            bot.send_message(chat_id, f"خطأ: {error}. أرسل الاسم مرة أخرى (أو 'إلغاء'):", reply_markup=registration_kb())
            bot.register_next_step_handler(msg, handle_name_input)
            return

        display_name = text
        user_id = msg.from_user.id

        with _pending_registration_lock:
            _pending_registration[chat_id] = {"step": "group", "display_name": display_name}
        msg_group = bot.send_message(
            chat_id,
            "✅ تم حفظ الاسم.\n\nالآن اختر مجموعتك من الخيارات المتاحة:",
            reply_markup=registration_kb(include_groups=True)
        )
        bot.register_next_step_handler(msg_group, handle_group_input)

    def handle_group_input(msg):
        chat_id = msg.chat.id
        text = (msg.text or "").strip()
        if is_main_menu_button(text):
            _prompt_registration_input(chat_id, "يرجى اختيار رقم المجموعة لإكمال التسجيل.", handle_group_input, include_groups=True)
            return
        with _pending_registration_lock:
            pending = _pending_registration.get(chat_id)
        if is_cancel_text(text) or not pending or not isinstance(pending, dict):
            with _pending_registration_lock:
                _pending_registration.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء إدخال المجموعة.", reply_markup=main_menu_kb())
            return
        if pending.get("step") != "group":
            bot.send_message(chat_id, "رجاءً أرسل اسمك أولاً عبر /start.", reply_markup=main_menu_kb())
            return

        is_valid, error = validate_text_input(text, MAX_INPUT_LENGTH)
        if not is_valid:
            msg_retry = bot.send_message(chat_id, f"خطأ: {error}. اختر المجموعة مرة أخرى (أو 'إلغاء'):", reply_markup=registration_kb(include_groups=True))
            bot.register_next_step_handler(msg_retry, handle_group_input)
            return

        normalized_group = REGISTRATION_GROUP_NORMALIZATION.get(text.casefold())
        if not normalized_group:
            options_text = ", ".join(REGISTRATION_GROUP_OPTIONS)
            msg_retry = bot.send_message(
                chat_id,
                f"يرجى اختيار المجموعة فقط من الخيارات: {options_text}.",
                reply_markup=registration_kb(include_groups=True)
            )
            bot.register_next_step_handler(msg_retry, handle_group_input)
            return

        display_name = pending.get("display_name")
        group_number = normalized_group
        user_id = msg.from_user.id

        with db_connection() as conn_local:
            update_user_display_name(conn_local, user_id, display_name, group_number=group_number)

        with _pending_registration_lock:
            _pending_registration.pop(chat_id, None)

        bot.send_message(chat_id, f"شكرًا — تم حفظ بياناتك: {display_name} (المجموعة {group_number}).", reply_markup=main_menu_kb())
        logger.info(f"User {user_id} set display_name={display_name} group={group_number}")

        if ADMIN_IDS:
            safe_display_name = html.escape(display_name or "")
            safe_group_number = html.escape(group_number or "")
            admin_message = (
                "🆕 تسجيل مستخدم جديد\n"
                f"الاسم: {safe_display_name}\n"
                f"المجموعة: {safe_group_number}\n"
                f"user_id: {user_id}"
            )
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(admin_id, admin_message, parse_mode="HTML")
                except Exception:
                    logger.exception("Failed to notify admin about registration")

    
    def hw_edit_handle_field(msg, hw_id, field):
        if is_cancel_text(getattr(msg, "text", "")):
            bot.reply_to(msg, "تم إلغاء التعديل.")
            return
        try:
            with db_connection() as conn_local:
                row = get_homework(conn_local, hw_id)
            if not row:
                bot.reply_to(msg, "لم أجد هذا الواجب.")
                return

            if field == "subject":
                new = (msg.text or "").strip()
                is_valid, error = validate_text_input(new)
                if not is_valid:
                    bot.reply_to(msg, f"خطأ: {error}")
                    return
                with db_connection() as conn_local:
                    update_field(conn_local, hw_id, "subject", new)
            elif field == "description":
                new = (msg.text or "").strip()
                is_valid, error = validate_text_input(new, MAX_DESCRIPTION_LENGTH)
                if not is_valid:
                    bot.reply_to(msg, f"خطأ: {error}")
                    return
                with db_connection() as conn_local:
                    update_field(conn_local, hw_id, "description", new)
            elif field == "due_at":
                text = (msg.text or "").strip()
                is_valid, error, due_str = validate_datetime(text)
                if not is_valid:
                    bot.reply_to(msg, f"خطأ: {error}")
                    return
                with db_connection() as conn_local:
                    update_field(conn_local, hw_id, "due_at", due_str)
                with db_connection() as conn_local2:
                    row2 = get_homework(conn_local2, hw_id)
                try:
                    sch_mgr.schedule_homework_reminders(row2)
                except Exception:
                    logger.exception("Failed rescheduling after due_at edit")
                bot.reply_to(msg, f"تم تعديل الموعد للواجب ID:{hw_id}")
                return
            elif field == "pdf":
                if msg.content_type == 'document':
                    pdf_type = "file_id"
                    pdf_value = msg.document.file_id
                    with db_connection() as conn_local:
                        update_field(conn_local, hw_id, "pdf_type", pdf_type)
                        update_field(conn_local, hw_id, "pdf_value", pdf_value)
                else:
                    text = (msg.text or "").strip()
                    if text.lower() == "none":
                        with db_connection() as conn_local:
                            update_field(conn_local, hw_id, "pdf_type", None)
                            update_field(conn_local, hw_id, "pdf_value", None)
                    else:
                        is_valid, url, error = validate_url(text)
                        if not is_valid:
                            bot.reply_to(msg, f"خطأ: {error}")
                            return
                        with db_connection() as conn_local:
                            update_field(conn_local, hw_id, "pdf_type", "url")
                            update_field(conn_local, hw_id, "pdf_value", url)
            elif field == "conditions":
                text = (msg.text or "").strip()
                if text.lower() == "none":
                    text = ""
                is_valid, error = validate_text_input(text, MAX_DESCRIPTION_LENGTH)
                if not is_valid:
                    bot.reply_to(msg, f"خطأ: {error}")
                    return
                with db_connection() as conn_local:
                    update_field(conn_local, hw_id, "conditions", text)
            elif field == "reminders":
                choice = (msg.text or "").strip()
                is_valid, reminders, error = validate_reminders(choice)
                if not is_valid:
                    bot.reply_to(msg, f"خطأ: {error}")
                    return
                with db_connection() as conn_local:
                    update_field(conn_local, hw_id, "reminders", reminders)
                with db_connection() as conn_local2:
                    row3 = get_homework(conn_local2, hw_id)
                try:
                    sch_mgr.schedule_homework_reminders(row3)
                except Exception:
                    logger.exception("Failed rescheduling after reminders edit")
                bot.reply_to(msg, f"تم تحديث تذكيرات الواجب ID:{hw_id}")
                return
            else:
                bot.reply_to(msg, "حقل غير معروف.")
                return

            bot.reply_to(msg, f"تم تعديل الحقل بنجاح (ID:{hw_id}).")
        except Exception as e:
            logger.exception("Error in hw_edit_handle_field")
            bot.reply_to(msg, f"خطأ أثناء التعديل: {e}")

    
    def _manual_next_step_handler(msg, originating_chat_id):
        chat_id = originating_chat_id
        text = (msg.text or "").strip()
        with _pending_lock:
            pm = _pending_manual.get(chat_id)
        if not pm:
            bot.send_message(chat_id, "لا توجد عملية يدوية معلقة.", reply_markup=main_menu_kb())
            return
        if is_cancel_text(text):
            cancel_pending_manual(chat_id)
            bot.send_message(chat_id, "تم إلغاء العملية.", reply_markup=main_menu_kb())
            return

        step = pm.get("step")
        mode = pm.get("mode")

        
        if step == PENDING_STEP_ENTER_TARGET:
            try:
                val = int(text)
                pm["target_value"] = val
                pm["step"] = PENDING_STEP_ENTER_CONTENT
                _pending_manual[chat_id] = pm
                msg2 = bot.send_message(chat_id, "أرسل نص التذكير أو ملف (صورة، صوت، PDF، فيديو، إلخ) أو كليهما:", reply_markup=cancel_inline_kb())
                bot.register_next_step_handler(msg2, _manual_next_step_handler, chat_id)
                return
            except Exception:
                bot.send_message(chat_id, "قيمة غير مفهومة. أدخل user_id أو chat_id صالح أو اكتب 'إلغاء'.")
                return

        
        if step == PENDING_STEP_ENTER_CONTENT:
            media_type = None
            media_file_id = None
            caption = None
            
            
            content_type = msg.content_type
            if content_type == "photo":
                media_type = "photo"
                
                media_file_id = msg.photo[-1].file_id
                caption = msg.caption
            elif content_type == "audio":
                media_type = "audio"
                media_file_id = msg.audio.file_id
                caption = msg.caption
            elif content_type == "voice":
                media_type = "voice"
                media_file_id = msg.voice.file_id
                caption = msg.caption
            elif content_type == "video":
                media_type = "video"
                media_file_id = msg.video.file_id
                caption = msg.caption
            elif content_type == "document":
                media_type = "document"
                media_file_id = msg.document.file_id
                caption = msg.caption
            elif content_type == "video_note":
                media_type = "video_note"
                media_file_id = msg.video_note.file_id
            elif content_type == "sticker":
                media_type = "sticker"
                media_file_id = msg.sticker.file_id
            elif content_type == "text":
                
                pm["text"] = text
                pm["media_type"] = None
                pm["media_file_id"] = None
                pm["caption"] = None
            else:
                bot.send_message(chat_id, "نوع المحتوى غير مدعوم. يرجى إرسال نص أو ملف (صورة، صوت، PDF، فيديو، إلخ) أو اكتب 'إلغاء'.", reply_markup=cancel_inline_kb())
                return
            
            
            if media_type:
                pm["media_type"] = media_type
                pm["media_file_id"] = media_file_id
                pm["caption"] = caption
                
                if caption:
                    pm["text"] = caption
                elif "text" not in pm:
                    pm["text"] = ""
                
                
                msg2 = bot.send_message(chat_id, f"✅ تم استلام {media_type}. هل تريد إضافة نص إضافي؟\nأرسل النص أو اكتب 'تم' أو 'إلغاء' للمتابعة بدون نص إضافي:", reply_markup=cancel_inline_kb())
                bot.register_next_step_handler(msg2, _manual_content_finalize_handler, chat_id)
                _pending_manual[chat_id] = pm
                return
            else:
                
                pm["text"] = text
                pm["media_type"] = None
                pm["media_file_id"] = None
                pm["caption"] = None
            
            _pending_manual[chat_id] = pm
            
            
            if mode == "schedule":
                pm["step"] = PENDING_STEP_ENTER_DATETIME
                _pending_manual[chat_id] = pm
                msg2 = bot.send_message(chat_id, "أدخل التاريخ والوقت للإرسال بصيغة YYYY-MM-DD HH:MM أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
                bot.register_next_step_handler(msg2, _manual_next_step_handler, chat_id)
                return
            else:
                target_type = pm.get("target_type")
                target_value = pm.get("target_value", None)
                thread_id = pm.get("thread_id")
                _do_manual_send(
                    chat_id, mode="now", 
                    text=pm.get("text", ""), 
                    target_type=target_type, 
                    target_value=target_value, 
                    thread_id=thread_id,
                    media_type=pm.get("media_type"),
                    media_file_id=pm.get("media_file_id"),
                    caption=pm.get("caption")
                )
                cancel_pending_manual(chat_id)
                return

        
        if step == PENDING_STEP_ENTER_TEXT:
            pm["text"] = text
            if mode == "schedule":
                pm["step"] = PENDING_STEP_ENTER_DATETIME
                _pending_manual[chat_id] = pm
                msg2 = bot.send_message(chat_id, "أدخل التاريخ والوقت للإرسال بصيغة YYYY-MM-DD HH:MM أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
                bot.register_next_step_handler(msg2, _manual_next_step_handler, chat_id)
                return
            else:
                target_type = pm.get("target_type")
                target_value = pm.get("target_value", None)
                thread_id = pm.get("thread_id")
                _do_manual_send(chat_id, mode="now", text=pm["text"], target_type=target_type, target_value=target_value, thread_id=thread_id)
                cancel_pending_manual(chat_id)
                return

        
        if step == PENDING_STEP_ENTER_DATETIME:
            try:
                dt = parse_dt(text)
            except Exception:
                msg2 = bot.send_message(chat_id, "صيغة غير صحيحة. أرسل التاريخ بصيغة: YYYY-MM-DD HH:MM أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
                bot.register_next_step_handler(msg2, _manual_next_step_handler, chat_id)
                return
            target_type = pm.get("target_type")
            target_value = pm.get("target_value", None)
            thread_id = pm.get("thread_id")
            _do_manual_send(
                chat_id, mode="schedule", 
                text=pm.get("text", ""), 
                target_type=target_type, 
                target_value=target_value, 
                when=dt, 
                thread_id=thread_id,
                media_type=pm.get("media_type"),
                media_file_id=pm.get("media_file_id"),
                caption=pm.get("caption")
            )
            cancel_pending_manual(chat_id)
            return

        
        if step == PENDING_STEP_ENTER_CHAT:
            
            thread_id = None
            chat_id_val = None

            
            if getattr(msg, "reply_to_message", None):
                thread_id = getattr(msg.reply_to_message, "message_thread_id", None)
                chat_id_val = msg.chat.id  
                
                pm["target_value"] = chat_id_val
                pm["thread_id"] = thread_id
                pm["step"] = PENDING_STEP_ENTER_CONTENT
                _pending_manual[chat_id] = pm
                msg2 = bot.send_message(chat_id, f"تم التقاط topic thread_id={thread_id} تلقائياً. الآن أرسل نص التذكير أو ملف:", reply_markup=cancel_inline_kb())
                bot.register_next_step_handler(msg2, _manual_next_step_handler, chat_id)
                return

            
            try:
                chat_id_val = int(text)
                pm["target_value"] = chat_id_val
                
                pm["step"] = PENDING_STEP_ENTER_THREAD
                _pending_manual[chat_id] = pm
                msg2 = bot.send_message(chat_id, "أدخل message_thread_id للـ topic (رقم) أو قم بالرد على رسالة داخل الموضوع ثم أرسل هنا:", reply_markup=cancel_inline_kb())
                bot.register_next_step_handler(msg2, _manual_next_step_handler, chat_id)
                return
            except Exception:
                bot.send_message(chat_id, "قيمة chat_id غير صالحة. أدخل chat_id رقميًا (مثال: -1001234567890) أو اكتب 'إلغاء'.")
                return

        
        if step == PENDING_STEP_ENTER_THREAD:
            
            thread_id = None
            if getattr(msg, "reply_to_message", None):
                thread_id = getattr(msg.reply_to_message, "message_thread_id", None)
            else:
                try:
                    thread_id = int(text)
                except Exception:
                    thread_id = None

            if thread_id is None:
                bot.send_message(chat_id, "لم أحصل على thread_id صالح. ضع رقمًا صحيحًا أو قم بالرد على رسالة داخل الموضوع.", reply_markup=cancel_inline_kb())
                return

            pm["thread_id"] = thread_id
            pm["step"] = PENDING_STEP_ENTER_CONTENT
            _pending_manual[chat_id] = pm
            msg2 = bot.send_message(chat_id, f"تم حفظ thread_id={thread_id}. الآن أرسل نص التذكير أو ملف:", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg2, _manual_next_step_handler, chat_id)
            return

    
    def _manual_content_finalize_handler(msg, originating_chat_id):
        """معالج للنص الإضافي بعد استلام الملف."""
        chat_id = originating_chat_id
        text = (msg.text or "").strip()
        with _pending_lock:
            pm = _pending_manual.get(chat_id)
        if not pm:
            bot.send_message(chat_id, "لا توجد عملية يدوية معلقة.", reply_markup=main_menu_kb())
            return
        
        if is_cancel_text(text):
            cancel_pending_manual(chat_id)
            bot.send_message(chat_id, "تم إلغاء العملية.", reply_markup=main_menu_kb())
            return
        
        mode = pm.get("mode")
        
        
        if text.lower() in ["تم", "done", "skip"] or not text:
            pm["text"] = pm.get("caption", "") or ""
        else:
            
            existing_caption = pm.get("caption", "")
            if existing_caption:
                pm["text"] = f"{existing_caption}\n\n{text}"
            else:
                pm["text"] = text
        
        _pending_manual[chat_id] = pm
        
        
        if mode == "schedule":
            pm["step"] = PENDING_STEP_ENTER_DATETIME
            _pending_manual[chat_id] = pm
            msg2 = bot.send_message(chat_id, "أدخل التاريخ والوقت للإرسال بصيغة YYYY-MM-DD HH:MM أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(msg2, _manual_next_step_handler, chat_id)
        else:
            target_type = pm.get("target_type")
            target_value = pm.get("target_value", None)
            thread_id = pm.get("thread_id")
            _do_manual_send(
                chat_id, mode="now", 
                text=pm.get("text", ""), 
                target_type=target_type, 
                target_value=target_value, 
                thread_id=thread_id,
                media_type=pm.get("media_type"),
                media_file_id=pm.get("media_file_id"),
                caption=pm.get("caption")
            )
            cancel_pending_manual(chat_id)

    
    def _do_manual_send(origin_chat_id, mode, text, target_type, target_value=None, when: Optional[datetime] = None, thread_id: Optional[int] = None, media_type: Optional[str] = None, media_file_id: Optional[str] = None, caption: Optional[str] = None):
        """
        mode: 'now' أو 'schedule'
        target_type: 'all'|'user'|'chat'|'chat_topic'
        target_value: int or None (لـ 'user' و 'chat')
        thread_id: int أو None (للـ topic)
        media_type: نوع الملف (photo, audio, video, document, etc.)
        media_file_id: file_id للملف
        caption: caption للملف (إن وجد)
        """
        try:
            def parse_target_val(val):
                if val is None:
                    return None
                if isinstance(val, int):
                    return val
                s = str(val).strip()
                s = s.replace(" ", "")
                if s.lower().startswith("chat_id:"):
                    s = s.split(":", 1)[1]
                try:
                    return int(s)
                except Exception:
                    return None

            if target_type in ("user", "chat", "chat_topic"):
                tid = parse_target_val(target_value)
                if tid is None:
                    bot.send_message(origin_chat_id, "قيمة المستهدف غير صالحة. أدخل user_id أو chat_id صحيح (مثال: -1001234567890).", reply_markup=main_menu_kb())
                    return

            
            if target_type == "all":
                with db_connection() as conn_local:
                    uids = get_all_registered_user_ids(conn_local)
                failures = 0
                skipped = 0
                for uid in uids:
                    try:
                        if mode == "now":
                            
                            with db_connection() as conn_check:
                                if not get_notification_setting(conn_check, uid, 'manual_reminders'):
                                    logger.info("_do_manual_send: user_id=%s disabled manual_reminders, skipping", uid)
                                    skipped += 1
                                    continue
                            if media_type and media_file_id:
                                
                                if text:
                                    bot.send_message(uid, text)
                                if media_type == "photo":
                                    bot.send_photo(uid, media_file_id, caption=caption)
                                elif media_type == "audio":
                                    bot.send_audio(uid, media_file_id, caption=caption)
                                elif media_type == "voice":
                                    bot.send_voice(uid, media_file_id, caption=caption)
                                elif media_type == "video":
                                    bot.send_video(uid, media_file_id, caption=caption)
                                elif media_type == "document":
                                    bot.send_document(uid, media_file_id, caption=caption)
                                elif media_type == "video_note":
                                    bot.send_video_note(uid, media_file_id)
                                elif media_type == "sticker":
                                    bot.send_sticker(uid, media_file_id)
                            else:
                                
                                if text:
                                    bot.send_message(uid, text)
                        else:
                            
                            job_id = f"manual_all_{uid}_{int(datetime.now().timestamp())}"
                            try:
                                if media_type and media_file_id:
                                    callable_ref = "handlers:_job_send_media_to_user"
                                    sch_mgr.scheduler.add_job(callable_ref, 'date', args=[uid, text or "", media_type, media_file_id, caption], run_date=when, id=job_id)
                                else:
                                    callable_ref = "handlers:_job_send_to_user"
                                    sch_mgr.scheduler.add_job(callable_ref, 'date', args=[uid, text or ""], run_date=when, id=job_id)
                            except Exception:
                                logger.exception("Failed to schedule manual reminder job for user")
                    except Exception:
                        logger.exception(f"Failed to send manual message to {uid}")
                        failures += 1
                skipped_msg = f" (تم تخطي {skipped} مستخدم بسبب إعدادات الإشعارات)" if skipped > 0 else ""
                bot.send_message(origin_chat_id, f"تم معالجة التذكير اليدوي (إلى الجميع). فشل الإرسال لعدد: {failures}{skipped_msg}", reply_markup=main_menu_kb())
                return

            
            if target_type == "user":
                uid = parse_target_val(target_value)
                if uid is None:
                    bot.send_message(origin_chat_id, "قيمة user_id غير صحيحة.", reply_markup=main_menu_kb())
                    return
                try:
                    if mode == "now":
                        
                        with db_connection() as conn_check:
                            if not get_notification_setting(conn_check, uid, 'manual_reminders'):
                                logger.info("_do_manual_send: user_id=%s disabled manual_reminders, skipping", uid)
                                bot.send_message(origin_chat_id, f"المستخدم (ID:{uid}) أوقف تذكيرات الأدمين. لن يتم إرسال الرسالة.", reply_markup=main_menu_kb())
                                return
                        if media_type and media_file_id:
                            
                            if text:
                                bot.send_message(uid, text)
                            if media_type == "photo":
                                bot.send_photo(uid, media_file_id, caption=caption)
                            elif media_type == "audio":
                                bot.send_audio(uid, media_file_id, caption=caption)
                            elif media_type == "voice":
                                bot.send_voice(uid, media_file_id, caption=caption)
                            elif media_type == "video":
                                bot.send_video(uid, media_file_id, caption=caption)
                            elif media_type == "document":
                                bot.send_document(uid, media_file_id, caption=caption)
                            elif media_type == "video_note":
                                bot.send_video_note(uid, media_file_id)
                            elif media_type == "sticker":
                                bot.send_sticker(uid, media_file_id)
                        else:
                            
                            if text:
                                bot.send_message(uid, text)
                    else:
                        
                        job_id = f"manual_user_{uid}_{int(datetime.now().timestamp())}"
                        try:
                            if media_type and media_file_id:
                                callable_ref = "handlers:_job_send_media_to_user"
                                sch_mgr.scheduler.add_job(callable_ref, 'date', args=[uid, text or "", media_type, media_file_id, caption], run_date=when, id=job_id)
                            else:
                                callable_ref = "handlers:_job_send_to_user"
                                sch_mgr.scheduler.add_job(callable_ref, 'date', args=[uid, text or ""], run_date=when, id=job_id)
                        except Exception:
                            logger.exception("Failed to schedule manual reminder job for user")
                    bot.send_message(origin_chat_id, f"تمت معالجة التذكير لِـ user_id={uid}.", reply_markup=main_menu_kb())
                except Exception as e:
                    logger.exception("Failed to send manual reminder to user")
                    bot.send_message(origin_chat_id, f"فشل إرسال الرسالة للمستخدم (ID:{uid}). قد يكون لم يبدأ البوت أو حظر البوت. الخطأ: {e}", reply_markup=main_menu_kb())
                return

            
            if target_type in ("chat", "chat_topic"):
                raw_chat = target_value
                chatid_parsed = parse_target_val(raw_chat)
                if chatid_parsed is None:
                    bot.send_message(origin_chat_id, "قيمة chat_id غير صحيحة. يجب أن تكون رقماً (مثال: -1001234567890).", reply_markup=main_menu_kb())
                    return

                info, used = try_get_chat_variants(chatid_parsed, bot)
                if info is None:
                    logger.warning("try_get_chat_variants failed for %s -> %s", chatid_parsed, used)
                    bot.send_message(origin_chat_id, f"البوت لا يستطيع الوصول لهذه المحادثة (الادخل: {raw_chat}). تأكد أن البوت مضاف للمجموعة وأن المعرف صحيح. خطأ: {used}", reply_markup=main_menu_kb())
                    return

                real_chat_id = used

                try:
                    if target_type == "chat":
                        if mode == "now":
                            if media_type and media_file_id:
                                
                                if text:
                                    bot.send_message(real_chat_id, text)
                                if media_type == "photo":
                                    bot.send_photo(real_chat_id, media_file_id, caption=caption)
                                elif media_type == "audio":
                                    bot.send_audio(real_chat_id, media_file_id, caption=caption)
                                elif media_type == "voice":
                                    bot.send_voice(real_chat_id, media_file_id, caption=caption)
                                elif media_type == "video":
                                    bot.send_video(real_chat_id, media_file_id, caption=caption)
                                elif media_type == "document":
                                    bot.send_document(real_chat_id, media_file_id, caption=caption)
                                elif media_type == "video_note":
                                    bot.send_video_note(real_chat_id, media_file_id)
                                elif media_type == "sticker":
                                    bot.send_sticker(real_chat_id, media_file_id)
                            else:
                                
                                if text:
                                    bot.send_message(real_chat_id, text)
                            bot.send_message(origin_chat_id, f"تم الإرسال إلى المحادثة {real_chat_id}.", reply_markup=main_menu_kb())
                        else:
                            
                            job_id = f"manual_chat_{real_chat_id}_{int(datetime.now().timestamp())}"
                            try:
                                if media_type and media_file_id:
                                    callable_ref = "handlers:_job_send_media_to_chat"
                                    sch_mgr.scheduler.add_job(callable_ref, 'date', args=[real_chat_id, text or "", media_type, media_file_id, caption, None], run_date=when, id=job_id)
                                else:
                                    callable_ref = "handlers:_job_send_to_chat"
                                    sch_mgr.scheduler.add_job(callable_ref, 'date', args=[real_chat_id, text or "", None], run_date=when, id=job_id)
                                bot.send_message(origin_chat_id, f"تم جدولة التذكير للمحادثة {real_chat_id} بتاريخ {when}.", reply_markup=main_menu_kb())
                            except Exception:
                                logger.exception("Failed to schedule manual reminder job for chat")
                                bot.send_message(origin_chat_id, "فشل جدولة التذكير للمحادثة. راجع اللوغ.", reply_markup=main_menu_kb())
                    else:  
                        
                        real_thread = thread_id
                        if real_thread is None:
                            bot.send_message(origin_chat_id, "لم يتم تحديد thread_id للموضوع. يجب أن تحدد thread_id أو ترد على رسالة داخل الـ topic.", reply_markup=main_menu_kb())
                            return
                        if mode == "now":
                            if media_type and media_file_id:
                                
                                if text:
                                    bot.send_message(real_chat_id, text, message_thread_id=real_thread)
                                if media_type == "photo":
                                    bot.send_photo(real_chat_id, media_file_id, caption=caption, message_thread_id=real_thread)
                                elif media_type == "audio":
                                    bot.send_audio(real_chat_id, media_file_id, caption=caption, message_thread_id=real_thread)
                                elif media_type == "voice":
                                    bot.send_voice(real_chat_id, media_file_id, caption=caption, message_thread_id=real_thread)
                                elif media_type == "video":
                                    bot.send_video(real_chat_id, media_file_id, caption=caption, message_thread_id=real_thread)
                                elif media_type == "document":
                                    bot.send_document(real_chat_id, media_file_id, caption=caption, message_thread_id=real_thread)
                                elif media_type == "video_note":
                                    bot.send_video_note(real_chat_id, media_file_id, message_thread_id=real_thread)
                                elif media_type == "sticker":
                                    bot.send_sticker(real_chat_id, media_file_id, message_thread_id=real_thread)
                            else:
                                
                                if text:
                                    bot.send_message(real_chat_id, text, message_thread_id=real_thread)
                            bot.send_message(origin_chat_id, f"تم الإرسال داخل الموضوع (thread={real_thread}) بالمحادثة {real_chat_id}.", reply_markup=main_menu_kb())
                        else:
                            
                            job_id = f"manual_chattopic_{real_chat_id}_{real_thread}_{int(datetime.now().timestamp())}"
                            try:
                                if media_type and media_file_id:
                                    callable_ref = "handlers:_job_send_media_to_chat"
                                    sch_mgr.scheduler.add_job(callable_ref, 'date', args=[real_chat_id, text or "", media_type, media_file_id, caption, real_thread], run_date=when, id=job_id)
                                else:
                                    callable_ref = "handlers:_job_send_to_chat"
                                    sch_mgr.scheduler.add_job(callable_ref, 'date', args=[real_chat_id, text or "", real_thread], run_date=when, id=job_id)
                                bot.send_message(origin_chat_id, f"تم جدولة التذكير داخل الموضوع (thread={real_thread}) بتاريخ {when}.", reply_markup=main_menu_kb())
                            except Exception:
                                logger.exception("Failed to schedule manual reminder job for chat topic")
                                bot.send_message(origin_chat_id, "فشل جدولة التذكير داخل الموضوع. راجع اللوغ.", reply_markup=main_menu_kb())
                except Exception:
                    logger.exception("Failed to process manual reminder to chat/topic")
                    bot.send_message(origin_chat_id, "فشل أثناء معالجة التذكير اليدوي.", reply_markup=main_menu_kb())
                return

            bot.send_message(origin_chat_id, "نوع المستهدف غير معروف.", reply_markup=main_menu_kb())
        except Exception:
            logger.exception("Error in _do_manual_send")
            bot.send_message(origin_chat_id, "فشل أثناء معالجة التذكير اليدوي.", reply_markup=main_menu_kb())

    
    def _custom_reminder_step_text(msg, chat_id, user_id):
        text = (msg.text or "").strip()
        if is_cancel_text(text):
            with _pending_lock:
                _pending_manual.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء إضافة التذكير المخصص.", reply_markup=main_menu_kb())
            return
        
        is_valid, error = validate_text_input(text, MAX_DESCRIPTION_LENGTH)
        if not is_valid:
            m = bot.send_message(chat_id, f"خطأ: {error}. أرسل النص مرة أخرى (أو 'إلغاء'):", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, _custom_reminder_step_text, chat_id, user_id)
            return
        
        with _pending_lock:
            _pending_manual[chat_id] = {"step": "custom_datetime", "type": "custom_reminder", "text": text}
        
        m = bot.send_message(chat_id, "أرسل التاريخ والوقت للتذكير بصيغة YYYY-MM-DD HH:MM (أو 'إلغاء'):", reply_markup=cancel_inline_kb())
        bot.register_next_step_handler(m, _custom_reminder_step_datetime, chat_id, user_id, text)

    def _custom_reminder_step_datetime(msg, chat_id, user_id, reminder_text):
        text = (msg.text or "").strip()
        if is_cancel_text(text):
            with _pending_lock:
                _pending_manual.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء إضافة التذكير المخصص.", reply_markup=main_menu_kb())
            return
        
        is_valid, error, dt_str = validate_datetime(text)
        if not is_valid:
            m = bot.send_message(chat_id, f"خطأ: {error}. أرسل التاريخ والوقت مرة أخرى (أو 'إلغاء'):", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, _custom_reminder_step_datetime, chat_id, user_id, reminder_text)
            return
        
        
        with db_connection() as conn_local:
            reminder_id = insert_custom_reminder(conn_local, user_id, reminder_text, dt_str)
        
        with _pending_lock:
            _pending_manual.pop(chat_id, None)
        
        bot.send_message(chat_id, f"✅ تم إضافة التذكير المخصص (ID: {reminder_id}). سيتم إرسال التذكير في الوقت المحدد.", reply_markup=main_menu_kb())
        
        
        try:
            from datetime import datetime
            reminder_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            if reminder_dt > datetime.now():
                job_id = f"custom_reminder-{reminder_id}"
                
                callable_ref = "handlers:_job_send_custom_reminder"
                sch_mgr.scheduler.add_job(callable_ref, 'date', run_date=reminder_dt, args=[reminder_id, user_id], id=job_id, replace_existing=True)
                logger.info("Scheduled custom reminder %s at %s", reminder_id, reminder_dt)
        except Exception:
            logger.exception("Failed to schedule custom reminder")

    
    def schedule_admin_add_step_time_start(msg, chat_id):
        """Step 1: Get time start."""
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                
                return
        
        
        if not hasattr(msg, 'text') or not msg.text:
            
            return
        
        text = msg.text.strip()
        if is_cancel_text(text):
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء إضافة الحصة.", reply_markup=main_menu_kb())
            return
        
        
        import re
        if not re.match(r'^\d{1,2}:\d{2}$', text):
            
            with _pending_schedule_admin_lock:
                if chat_id not in _pending_schedule_admin:
                    return
            m = bot.send_message(chat_id, "صيغة الوقت غير صحيحة. استخدم HH:MM (مثال: 08:00). أرسل مرة أخرى أو 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, schedule_admin_add_step_time_start, chat_id)
            return
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                bot.send_message(chat_id, "انتهت الجلسة.", reply_markup=main_menu_kb())
                return
            pm["time_start"] = text
            pm["step"] = "time_end"
        
        m = bot.send_message(chat_id, "أرسل وقت الانتهاء (مثال: 09:30) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
        bot.register_next_step_handler(m, schedule_admin_add_step_time_end, chat_id)

    def schedule_admin_add_step_time_end(msg, chat_id):
        """Step 2: Get time end."""
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                return
        
        
        if not hasattr(msg, 'text') or not msg.text:
            return
        
        text = msg.text.strip()
        if is_cancel_text(text):
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء إضافة الحصة.", reply_markup=main_menu_kb())
            return
        
        import re
        if not re.match(r'^\d{1,2}:\d{2}$', text):
            with _pending_schedule_admin_lock:
                if chat_id not in _pending_schedule_admin:
                    return
            m = bot.send_message(chat_id, "صيغة الوقت غير صحيحة. استخدم HH:MM (مثال: 09:30). أرسل مرة أخرى أو 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, schedule_admin_add_step_time_end, chat_id)
            return
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                bot.send_message(chat_id, "انتهت الجلسة.", reply_markup=main_menu_kb())
                return
            pm["time_end"] = text
            pm["step"] = "course"
        
        m = bot.send_message(chat_id, "أرسل اسم المادة (مثال: Analysis1) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
        bot.register_next_step_handler(m, schedule_admin_add_step_course, chat_id)

    def schedule_admin_add_step_course(msg, chat_id):
        """Step 3: Get course name."""
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                return
        
        
        if not hasattr(msg, 'text') or not msg.text:
            return
        
        text = msg.text.strip()
        if is_cancel_text(text):
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء إضافة الحصة.", reply_markup=main_menu_kb())
            return
        
        if not text:
            with _pending_schedule_admin_lock:
                if chat_id not in _pending_schedule_admin:
                    return
            m = bot.send_message(chat_id, "اسم المادة مطلوب. أرسل اسم المادة أو 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, schedule_admin_add_step_course, chat_id)
            return
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                bot.send_message(chat_id, "انتهت الجلسة.", reply_markup=main_menu_kb())
                return
            pm["course"] = text
            pm["step"] = "location"
        
        m = bot.send_message(chat_id, "أرسل المكان (مثال: Amphi H أو Room C206) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
        bot.register_next_step_handler(m, schedule_admin_add_step_location, chat_id)

    def schedule_admin_add_step_location(msg, chat_id):
        """Step 4: Get location."""
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                return
        
        
        if not hasattr(msg, 'text') or not msg.text:
            return
        
        text = msg.text.strip()
        if is_cancel_text(text):
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء إضافة الحصة.", reply_markup=main_menu_kb())
            return
        
        if not text:
            with _pending_schedule_admin_lock:
                if chat_id not in _pending_schedule_admin:
                    return
            m = bot.send_message(chat_id, "المكان مطلوب. أرسل المكان أو 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, schedule_admin_add_step_location, chat_id)
            return
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                bot.send_message(chat_id, "انتهت الجلسة.", reply_markup=main_menu_kb())
                return
            pm["location"] = text
            pm["step"] = "class_type"
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Course", callback_data=f"schedule_type:Course"))
        kb.add(types.InlineKeyboardButton("Tutorial Session", callback_data=f"schedule_type:Tutorial Session"))
        kb.add(types.InlineKeyboardButton("Laboratory Session", callback_data=f"schedule_type:Laboratory Session"))
        kb.add(types.InlineKeyboardButton("Online Session", callback_data=f"schedule_type:Online Session"))
        kb.add(types.InlineKeyboardButton("إلغاء", callback_data=CALLBACK_HW_CANCEL))
        bot.send_message(chat_id, "اختر نوع الحصة:", reply_markup=kb)
        

    def schedule_admin_add_step_alternating(msg, chat_id):
        """Step 6: Ask if alternating."""
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                return
        
        
        if not hasattr(msg, 'text') or not msg.text:
            return
        
        text = msg.text.strip().lower()
        if is_cancel_text(text):
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء إضافة الحصة.", reply_markup=main_menu_kb())
            return
        
        is_alternating = text in ["نعم", "yes", "y", "دورية"]
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                bot.send_message(chat_id, "انتهت الجلسة.", reply_markup=main_menu_kb())
                return
            pm["is_alternating"] = is_alternating
            if is_alternating:
                pm["step"] = "alternating_key"
                m = bot.send_message(chat_id, "أرسل مفتاح الحصة الدورية (مثال: algorithm1 أو statistics1) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
                bot.register_next_step_handler(m, schedule_admin_add_step_alternating_key, chat_id)
            else:
                
                schedule_admin_finalize_add(chat_id)

    def schedule_admin_add_step_alternating_key(msg, chat_id):
        """Step 7: Get alternating key if alternating."""
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                return
        
        
        if not hasattr(msg, 'text') or not msg.text:
            return
        
        text = msg.text.strip()
        if is_cancel_text(text):
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء إضافة الحصة.", reply_markup=main_menu_kb())
            return
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                bot.send_message(chat_id, "انتهت الجلسة.", reply_markup=main_menu_kb())
                return
            pm["alternating_key"] = text
            schedule_admin_finalize_add(chat_id)

    def schedule_admin_finalize_add(chat_id):
        """Finalize adding schedule class."""
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                bot.send_message(chat_id, "انتهت الجلسة.", reply_markup=main_menu_kb())
                return
            
            try:
                from db_schedule import insert_schedule_class
                with db_connection() as conn:
                    class_id = insert_schedule_class(
                        conn,
                        group_number=pm["group_number"],
                        day_name=pm["day"],
                        time_start=pm["time_start"],
                        time_end=pm["time_end"],
                        course=pm["course"],
                        location=pm["location"],
                        class_type=pm.get("class_type", "Course"),
                        is_alternating=pm.get("is_alternating", False),
                        alternating_key=pm.get("alternating_key"),
                        display_order=pm.get("display_order", 0)
                    )
                    bot.send_message(chat_id, f"✅ تم إضافة الحصة (ID: {class_id}).", reply_markup=main_menu_kb())
            except Exception as e:
                logger.exception("Failed to add schedule class")
                bot.send_message(chat_id, f"حدث خطأ في إضافة الحصة: {e}", reply_markup=main_menu_kb())
            finally:
                _pending_schedule_admin.pop(chat_id, None)

    
    def schedule_admin_location_step_name(msg, chat_id):
        """Step 1: Get location name."""
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm or pm.get("action") != "add_location":
                return
        
        
        if not hasattr(msg, 'text') or not msg.text:
            return
        
        text = msg.text.strip()
        if is_cancel_text(text):
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء إضافة الموقع.", reply_markup=main_menu_kb())
            return
        
        if not text:
            with _pending_schedule_admin_lock:
                if chat_id not in _pending_schedule_admin:
                    return
            m = bot.send_message(chat_id, "اسم الموقع مطلوب. أرسل اسم الموقع أو 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, schedule_admin_location_step_name, chat_id)
            return
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                bot.send_message(chat_id, "انتهت الجلسة.", reply_markup=main_menu_kb())
                return
            pm["location_name"] = text
            pm["step"] = "maps_url"
        
        m = bot.send_message(chat_id, f"أرسل رابط Google Maps للموقع '{text}' أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
        bot.register_next_step_handler(m, schedule_admin_location_step_url, chat_id, text)

    def schedule_admin_location_step_url(msg, chat_id, location_name=None):
        """Step 2: Get maps URL."""
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                return
            action = pm.get("action")
            
            if location_name is None:
                location_name = pm.get("location_name")
        
        
        if not hasattr(msg, 'text') or not msg.text:
            return
        
        text = msg.text.strip()
        if is_cancel_text(text):
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء العملية.", reply_markup=main_menu_kb())
            return
        
        if not location_name:
            bot.send_message(chat_id, "انتهت الجلسة.", reply_markup=main_menu_kb())
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            return
        
        
        if not text.startswith(("http://", "https://")):
            with _pending_schedule_admin_lock:
                if chat_id not in _pending_schedule_admin:
                    return
            m = bot.send_message(chat_id, "الرابط يجب أن يبدأ بـ http:// أو https://. أرسل الرابط مرة أخرى أو 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, schedule_admin_location_step_url, chat_id, location_name)
            return
        
        
        try:
            from db_schedule import insert_schedule_location
            with db_connection() as conn:
                if insert_schedule_location(conn, location_name, text):
                    if action == "edit_location_url":
                        bot.send_message(chat_id, f"✅ تم تحديث رابط الخريطة للموقع '{location_name}'.", reply_markup=main_menu_kb())
                    else:
                        bot.send_message(chat_id, f"✅ تم إضافة الموقع '{location_name}' برابط الخريطة.", reply_markup=main_menu_kb())
        except Exception as e:
            logger.exception("Failed to save location")
            bot.send_message(chat_id, f"حدث خطأ في حفظ الموقع: {e}", reply_markup=main_menu_kb())
        finally:
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)

    
    @bot.callback_query_handler(func=lambda c: c.data.startswith("schedule_type:"))
    def schedule_admin_class_type_handler(c):
        if not is_admin(c.from_user.id):
            bot.answer_callback_query(c.id, "غير مصرح.", show_alert=True)
            return
        
        class_type = c.data.split(":", 1)[1]
        chat_id = c.message.chat.id
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                bot.send_message(chat_id, "انتهت الجلسة.", reply_markup=main_menu_kb())
                bot.answer_callback_query(c.id)
                return
            pm["class_type"] = class_type
            pm["step"] = "alternating"
        
        msg = bot.send_message(chat_id, "هل هذه الحصة دورية (تظهر في أسبوع وتختفي في الأسبوع التالي)؟\nأرسل 'نعم' أو 'لا' أو 'إلغاء':", reply_markup=cancel_inline_kb())
        bot.register_next_step_handler(msg, schedule_admin_add_step_alternating, chat_id)
        bot.answer_callback_query(c.id)

    
    def schedule_admin_edit_class_field_step(msg, chat_id):
        """Handle editing a class field."""
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm or pm.get("action") != "edit_class":
                return
        
        
        if not hasattr(msg, 'text') or not msg.text:
            return
        
        text = msg.text.strip()
        if is_cancel_text(text):
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء التعديل.", reply_markup=main_menu_kb())
            return
        
        field = pm.get("field")
        class_id = pm.get("class_id")
        
        if not field or not class_id:
            bot.send_message(chat_id, "خطأ في البيانات.", reply_markup=main_menu_kb())
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            return
        
        try:
            from db_schedule import update_schedule_class_field, get_schedule_class
            import re
            
            
            if field in ["time_start", "time_end"]:
                
                if not re.match(r'^\d{1,2}:\d{2}$', text):
                    with _pending_schedule_admin_lock:
                        if chat_id not in _pending_schedule_admin:
                            return
                    m = bot.send_message(chat_id, "صيغة الوقت غير صحيحة. استخدم HH:MM (مثال: 08:00). أرسل مرة أخرى أو 'إلغاء':", reply_markup=cancel_inline_kb())
                    bot.register_next_step_handler(m, schedule_admin_edit_class_field_step, chat_id)
                    return
                value = text
            elif field == "alternating":
                
                if pm.get("step") == "enter_alternating_key":
                    value = text
                    field_to_update = "alternating_key"
                    with db_connection() as conn:
                        update_schedule_class_field(conn, class_id, "is_alternating", True)
                        update_schedule_class_field(conn, class_id, field_to_update, value)
                        cls = get_schedule_class(conn, class_id)
                        if cls:
                            cls_dict = dict(cls)
                            text_display = format_class_for_display(cls_dict)
                            kb = schedule_admin_class_actions_kb(class_id, cls_dict['group_number'], cls_dict['day_name'])
                            bot.send_message(chat_id, f"✅ تم تفعيل الحالة الدورية.\n\n{text_display}", reply_markup=kb)
                        else:
                            bot.send_message(chat_id, "✅ تم تفعيل الحالة الدورية.", reply_markup=main_menu_kb())
                    with _pending_schedule_admin_lock:
                        _pending_schedule_admin.pop(chat_id, None)
                    return
            else:
                
                if not text:
                    with _pending_schedule_admin_lock:
                        if chat_id not in _pending_schedule_admin:
                            return
                    m = bot.send_message(chat_id, "القيمة مطلوبة. أرسل القيمة مرة أخرى أو 'إلغاء':", reply_markup=cancel_inline_kb())
                    bot.register_next_step_handler(m, schedule_admin_edit_class_field_step, chat_id)
                    return
                value = text
            
            
            with db_connection() as conn:
                if update_schedule_class_field(conn, class_id, field, value):
                    cls = get_schedule_class(conn, class_id)
                    if cls:
                        cls_dict = dict(cls)
                        text_display = format_class_for_display(cls_dict)
                        kb = schedule_admin_class_actions_kb(class_id, cls_dict['group_number'], cls_dict['day_name'])
                        bot.send_message(chat_id, f"✅ تم تحديث {field}.\n\n{text_display}", reply_markup=kb)
                    else:
                        bot.send_message(chat_id, f"✅ تم تحديث {field}.", reply_markup=main_menu_kb())
                else:
                    bot.send_message(chat_id, f"❌ فشل تحديث {field}.", reply_markup=main_menu_kb())
        except Exception as e:
            logger.exception("Failed to update class field")
            bot.send_message(chat_id, f"حدث خطأ في التحديث: {e}", reply_markup=main_menu_kb())
        finally:
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)

    
    def schedule_admin_edit_alternating_config_step(msg, chat_id):
        """Handle editing alternating config reference date."""
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm or pm.get("action") != "edit_alternating_config":
                return
        
        
        if not hasattr(msg, 'text') or not msg.text:
            return
        
        text = msg.text.strip()
        if is_cancel_text(text):
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء التعديل.", reply_markup=main_menu_kb())
            return
        
        alternating_key = pm.get("alternating_key")
        field = pm.get("field")
        
        if not alternating_key or field != "reference_date":
            bot.send_message(chat_id, "خطأ في البيانات.", reply_markup=main_menu_kb())
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            return
        
        
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', text):
            with _pending_schedule_admin_lock:
                if chat_id not in _pending_schedule_admin:
                    return
            m = bot.send_message(chat_id, "صيغة التاريخ غير صحيحة. استخدم YYYY-MM-DD (مثال: 2024-11-11). أرسل مرة أخرى أو 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, schedule_admin_edit_alternating_config_step, chat_id)
            return
        
        try:
            from db_schedule import set_alternating_week_config, get_alternating_week_config
            with db_connection() as conn:
                
                existing_config = get_alternating_week_config(conn, alternating_key)
                if existing_config:
                    description = safe_get(existing_config, 'description')
                else:
                    description = None
                
                if set_alternating_week_config(conn, alternating_key, text, description):
                    config = get_alternating_week_config(conn, alternating_key)
                    if config:
                        config_dict = {
                            'alternating_key': safe_get(config, 'alternating_key', ''),
                            'reference_date': safe_get(config, 'reference_date', ''),
                            'description': safe_get(config, 'description')
                        }
                        text_display = format_alternating_config_for_display(config_dict)
                        kb = alternating_config_actions_kb(alternating_key)
                        bot.send_message(chat_id, f"✅ تم تحديث تاريخ المرجع.\n\n{text_display}", reply_markup=kb)
                    else:
                        bot.send_message(chat_id, "✅ تم تحديث تاريخ المرجع.", reply_markup=main_menu_kb())
                else:
                    bot.send_message(chat_id, "❌ فشل تحديث تاريخ المرجع.", reply_markup=main_menu_kb())
        except Exception as e:
            logger.exception("Failed to update alternating config")
            bot.send_message(chat_id, f"حدث خطأ في التحديث: {e}", reply_markup=main_menu_kb())
        finally:
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)

    def schedule_admin_add_alternating_config_step_key(msg, chat_id):
        """Step 1: Get alternating key."""
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm or pm.get("action") != "add_alternating_config":
                return
        
        
        if not hasattr(msg, 'text') or not msg.text:
            return
        
        text = msg.text.strip()
        if is_cancel_text(text):
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء الإضافة.", reply_markup=main_menu_kb())
            return
        
        if not text:
            with _pending_schedule_admin_lock:
                if chat_id not in _pending_schedule_admin:
                    return
            m = bot.send_message(chat_id, "مفتاح الحصة الدورية مطلوب. أرسل المفتاح أو 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, schedule_admin_add_alternating_config_step_key, chat_id)
            return
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm:
                bot.send_message(chat_id, "انتهت الجلسة.", reply_markup=main_menu_kb())
                return
            pm["alternating_key"] = text
            pm["step"] = "enter_reference_date"
        
        m = bot.send_message(chat_id, f"أرسل تاريخ المرجع بصيغة YYYY-MM-DD (مثال: 2024-11-11) أو اكتب 'إلغاء':", reply_markup=cancel_inline_kb())
        bot.register_next_step_handler(m, schedule_admin_add_alternating_config_step_date, chat_id)

    def schedule_admin_add_alternating_config_step_date(msg, chat_id):
        """Step 2: Get reference date."""
        
        with _pending_schedule_admin_lock:
            pm = _pending_schedule_admin.get(chat_id)
            if not pm or pm.get("action") != "add_alternating_config":
                return
        
        
        if not hasattr(msg, 'text') or not msg.text:
            return
        
        text = msg.text.strip()
        if is_cancel_text(text):
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            bot.send_message(chat_id, "تم إلغاء الإضافة.", reply_markup=main_menu_kb())
            return
        
        
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', text):
            with _pending_schedule_admin_lock:
                if chat_id not in _pending_schedule_admin:
                    return
            m = bot.send_message(chat_id, "صيغة التاريخ غير صحيحة. استخدم YYYY-MM-DD (مثال: 2024-11-11). أرسل مرة أخرى أو 'إلغاء':", reply_markup=cancel_inline_kb())
            bot.register_next_step_handler(m, schedule_admin_add_alternating_config_step_date, chat_id)
            return
        
        alternating_key = pm.get("alternating_key")
        if not alternating_key:
            bot.send_message(chat_id, "خطأ في البيانات.", reply_markup=main_menu_kb())
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)
            return
        
        try:
            from db_schedule import set_alternating_week_config
            with db_connection() as conn:
                if set_alternating_week_config(conn, alternating_key, text, None):
                    bot.send_message(chat_id, f"✅ تم إضافة إعداد الحصة الدورية '{alternating_key}'.", reply_markup=main_menu_kb())
                else:
                    bot.send_message(chat_id, "❌ فشل إضافة الإعداد.", reply_markup=main_menu_kb())
        except Exception as e:
            logger.exception("Failed to add alternating config")
            bot.send_message(chat_id, f"حدث خطأ في الإضافة: {e}", reply_markup=main_menu_kb())
        finally:
            with _pending_schedule_admin_lock:
                _pending_schedule_admin.pop(chat_id, None)

    
