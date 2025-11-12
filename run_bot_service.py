# run_bot_service.py
"""
Service runner for the Telegram Bot - يدير تشغيل البوت 24/7 مع إعادة التشغيل التلقائي
"""
import sys
import os
import time
import traceback
import logging
from datetime import datetime

# إعداد المسار الصحيح
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# تهيئة اللوجر
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_service.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# إعدادات إعادة التشغيل
MAX_RESTART_ATTEMPTS = 10  # عدد محاولات إعادة التشغيل قبل التوقف
RESTART_DELAY = 5  # وقت الانتظار قبل إعادة التشغيل (بالثواني)
MIN_UPTIME = 60  # الحد الأدنى لوقت التشغيل قبل اعتبارها إعادة تشغيل ناجحة (بالثواني)

# متغيرات للتتبع
restart_count = 0
last_restart_time = None
start_time = None


def run_bot():
    """تشغيل البوت - دالة منفصلة لسهولة إعادة التشغيل"""
    global start_time
    start_time = time.time()
    
    try:
        # استيراد وتشغيل البوت
        logger.info("=" * 70)
        logger.info("Starting Telegram Bot Service")
        logger.info("=" * 70)
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Script directory: {script_dir}")
        
        # في بيئة استضافة سحابية (مثل Render.com)، نستخدم subprocess
        # لكن بطريقة محسّنة لتوفير الموارد
        # لأن bot.py يستخدم if __name__ == "__main__" ونحتاج تشغيله كسكريبت منفصل
        return _run_bot_subprocess()
        
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received - stopping service")
        return False
    except SystemExit as e:
        exit_code = getattr(e, 'code', 0)
        logger.info(f"SystemExit received with code {exit_code}")
        if exit_code == 0:
            return False  # إيقاف ناجح
        else:
            return True  # إعادة التشغيل مطلوبة
    except Exception as e:
        logger.exception(f"Fatal error in bot runner: {e}")
        traceback.print_exc()
        return True  # إعادة التشغيل مطلوبة


def _run_bot_subprocess():
    """تشغيل البوت باستخدام subprocess (fallback method)"""
    try:
        import subprocess
        
        bot_script = os.path.join(script_dir, "bot.py")
        if not os.path.exists(bot_script):
            logger.error(f"bot.py not found at {bot_script}")
            return True  # إعادة التشغيل مطلوبة
        
        python_exe = sys.executable
        logger.info(f"Running via subprocess: {python_exe} {bot_script}")
        
        process = subprocess.Popen(
            [python_exe, bot_script],
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # مراقبة الإخراج في thread منفصل
        import threading
        def read_output():
            try:
                for line in process.stdout:
                    logger.debug(line.rstrip())
            except Exception:
                pass
        
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()
        
        # انتظار انتهاء العملية
        return_code = process.wait()
        
        if return_code == 0:
            logger.info("Bot stopped gracefully (exit code 0)")
            return False  # لا حاجة لإعادة التشغيل
        else:
            logger.warning(f"Bot stopped with exit code {return_code}")
            return True  # إعادة التشغيل مطلوبة
            
    except Exception as e:
        logger.exception(f"Error in subprocess method: {e}")
        return True  # إعادة التشغيل مطلوبة


def main():
    """الدالة الرئيسية - تدير إعادة التشغيل التلقائي"""
    global restart_count, last_restart_time, start_time
    
    logger.info("=" * 70)
    logger.info("Telegram Bot Service Manager")
    logger.info("=" * 70)
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Script directory: {script_dir}")
    logger.info("=" * 70)
    
    while True:
        try:
            # التحقق من عدد محاولات إعادة التشغيل
            if restart_count >= MAX_RESTART_ATTEMPTS:
                logger.critical(f"[ERROR] Maximum restart attempts ({MAX_RESTART_ATTEMPTS}) reached. Stopping service.")
                logger.critical("Please check the logs and fix the issues before restarting.")
                sys.exit(1)
            
            # إذا كانت هناك محاولة إعادة تشغيل سابقة، ننتظر قليلاً
            if restart_count > 0:
                if last_restart_time:
                    time_since_last_restart = time.time() - last_restart_time
                    if time_since_last_restart < MIN_UPTIME:
                        logger.warning(f"Bot restarted too quickly ({time_since_last_restart:.1f}s). "
                                     f"This might indicate a startup issue.")
                
                logger.info(f"Waiting {RESTART_DELAY} seconds before restart...")
                time.sleep(RESTART_DELAY)
            
            # تسجيل محاولة التشغيل
            if restart_count > 0:
                logger.info(f"[RESTART] Restarting bot (attempt {restart_count + 1}/{MAX_RESTART_ATTEMPTS})")
            else:
                logger.info("[START] Starting bot for the first time")
            
            # تشغيل البوت
            start_time = time.time()
            should_restart = run_bot()
            
            # حساب وقت التشغيل
            if start_time:
                uptime = time.time() - start_time
                logger.info(f"Bot ran for {uptime:.1f} seconds")
                
                # إذا توقف البوت بعد وقت قصير، نعتبره فشل
                if uptime < MIN_UPTIME and restart_count > 0:
                    logger.warning(f"Bot stopped too quickly ({uptime:.1f}s < {MIN_UPTIME}s). "
                                 f"This might indicate a configuration issue.")
            
            # إذا كان الإيقاف ناجحاً (KeyboardInterrupt أو SystemExit مع code 0)
            if not should_restart:
                logger.info("Bot stopped gracefully. Exiting service.")
                break
            
            # زيادة عداد إعادة التشغيل (سيتم إعادة التشغيل)
            restart_count += 1
            last_restart_time = time.time()
            logger.warning(f"Bot stopped unexpectedly. Restart count: {restart_count}")
            
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received in service manager - stopping")
            break
        except Exception as e:
            logger.exception(f"Unexpected error in service manager: {e}")
            restart_count += 1
            last_restart_time = time.time()
            # التحقق من عدد المحاولات قبل المتابعة
            if restart_count >= MAX_RESTART_ATTEMPTS:
                logger.critical(f"Maximum restart attempts ({MAX_RESTART_ATTEMPTS}) reached. Stopping service.")
                sys.exit(1)
            continue
    
    logger.info("Service manager stopped.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Service manager interrupted.")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error in service manager: {e}")
        sys.exit(1)

