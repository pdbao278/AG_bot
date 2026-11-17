import sys
import os
import socket
import threading
from pathlib import Path

# Đảm bảo terminal Windows luôn hiển thị đúng tiếng Việt có dấu (UTF-8)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Đảm bảo thư mục gốc dự án luôn nằm trong sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_SINGLE_INSTANCE_SOCKET = None


def ensure_single_instance(port: int = 49281) -> bool:
    """Đảm bảo chỉ có duy nhất 1 tiến trình bot chạy trên máy tính để tránh lỗi Telegram Conflict."""
    global _SINGLE_INSTANCE_SOCKET
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", port))
        s.listen(1)
        _SINGLE_INSTANCE_SOCKET = s
        return True
    except OSError:
        return False


from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from src.config import settings
from src.core.logger import logger
from src.handlers.command_handler import (
    start_handler,
    menu_handler,
    status_handler,
    help_handler,
    log_handler,
)
from src.handlers.agy_handler import (
    new_session_handler,
    model_menu_handler,
    model_callback_handler,
    ask_command_handler,
    folder_command_handler,
    message_handler,
)
from src.handlers.screen_handler import screen_handler
from src.handlers.power_handler import (
    lock_handler,
    shutdown_request_handler,
    abort_handler,
    power_callback_handler,
)


# Danh sách lệnh kèm mô tả gợi ý hiển thị tự động khi người dùng gõ / trên Telegram
BOT_COMMANDS = [
    BotCommand("start", "Khởi động bot và hiển thị menu"),
    BotCommand("menu", "Mở lại bàn phím điều khiển nhanh"),
    BotCommand("ask", "Gửi câu lệnh prompt cho Antigravity AI"),
    BotCommand("screen", "Chụp ảnh màn hình máy tính gửi về điện thoại"),
    BotCommand("new", "Bắt đầu phiên làm việc mới (xóa ngữ cảnh cũ)"),
    BotCommand("model", "Đổi model AI và kiểm tra Quota"),
    BotCommand("status", "Xem trạng thái CPU, RAM, ổ đĩa C, Uptime"),
    BotCommand("cd", "Xem hoặc đổi thư mục làm việc (/cd <path>)"),
    BotCommand("log", "Xem 25 dòng nhật ký log gần nhất (/log file)"),
    BotCommand("lock", "Khóa màn hình máy tính ngay lập tức"),
    BotCommand("shutdown", "Tắt máy tính từ xa (yêu cầu mã PIN)"),
    BotCommand("abort", "Hủy lệnh tắt máy đang đếm ngược"),
    BotCommand("help", "Xem hướng dẫn chi tiết các lệnh"),
]


async def post_init(application) -> None:
    """Đăng ký danh sách lệnh gợi ý và thông báo online khi bot khởi động."""
    try:
        await application.bot.set_my_commands(BOT_COMMANDS)
        logger.info("Đã đăng ký danh sách lệnh gợi ý (Bot Commands) với Telegram thành công.")
    except Exception as e:
        logger.warning(f"Không thể đăng ký Bot Commands với Telegram: {e}")

    # Thông báo online đến tất cả user được phép
    from datetime import datetime
    from src.config import settings
    now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    msg = (
        f"✅ *Bot vừa online lại!*\n"
        f"🕐 `{now}`\n\n"
        f"_Các lệnh gửi lúc bot offline đã bị bỏ qua._"
    )
    for user_id in settings.ALLOWED_USER_IDS:
        try:
            await application.bot.send_message(
                chat_id=user_id,
                text=msg,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Không thể gửi thông báo online đến {user_id}: {e}")


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ghi log ngoại lệ nếu có lỗi trong quá trình xử lý bot."""
    logger.error(f"Lỗi ngoại lệ phát sinh: {context.error}", exc_info=context.error)


def create_bot_application():
    """Khởi tạo và đăng ký các route xử lý cho Bot Telegram."""
    settings.validate()

    application = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    application.add_error_handler(global_error_handler)

    # 1. Các lệnh điều hướng cơ bản
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("menu", menu_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("status", status_handler))
    application.add_handler(CommandHandler(["log", "logs"], log_handler))

    # 2. Các lệnh tương tác Antigravity
    application.add_handler(CommandHandler("new", new_session_handler))
    application.add_handler(CommandHandler("model", model_menu_handler))  # tích hợp quota
    application.add_handler(CommandHandler("ask", ask_command_handler))
    application.add_handler(CommandHandler(["cd", "folder", "pwd"], folder_command_handler))

    # 3. Lệnh chụp ảnh màn hình
    application.add_handler(CommandHandler("screen", screen_handler))

    # 4. Các lệnh nguồn máy tính
    application.add_handler(CommandHandler("lock", lock_handler))
    application.add_handler(CommandHandler("shutdown", shutdown_request_handler))
    application.add_handler(CommandHandler("abort", abort_handler))

    # 5. Xử lý Callback nút bấm (Inline Keyboard)
    application.add_handler(CallbackQueryHandler(model_callback_handler, pattern=r"^(set_model:|refresh_quota)"))
    application.add_handler(CallbackQueryHandler(power_callback_handler, pattern=r"^power:"))

    # 6. Xử lý tin nhắn văn bản tự do và phím bấm Reply Keyboard
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    return application


def _watch_antigravity(stop_event: threading.Event) -> None:
    """
    Theo dõi tiến trình Antigravity. Khi tất cả cửa sổ Antigravity đóng,
    tự động dừng bot sau 5 giây (đủ thời gian để phân biệt restart nhanh).
    """
    import psutil

    AG_PROCESS_NAMES = {"antigravity", "antigravity ide"}

    # Chờ Antigravity khởi động lên trước (tối đa 30 giây)
    for _ in range(30):
        if stop_event.wait(timeout=1):
            return
        procs = [p for p in psutil.process_iter(["name"]) if p.info["name"] and p.info["name"].lower().rstrip(".exe") in AG_PROCESS_NAMES]
        if procs:
            logger.info(f"Phát hiện Antigravity đang chạy ({len(procs)} tiến trình). Bắt đầu theo dõi.")
            break
    else:
        logger.info("Không tìm thấy Antigravity sau 30 giây — bot chạy độc lập, không tự tắt.")
        return

    # Vòng lặp theo dõi
    while not stop_event.is_set():
        stop_event.wait(timeout=30)
        if stop_event.is_set():
            return
        procs = [p for p in psutil.process_iter(["name"]) if p.info["name"] and p.info["name"].lower().rstrip(".exe") in AG_PROCESS_NAMES]
        if not procs:
            logger.info("Antigravity đã đóng. Bot sẽ tắt sau 5 giây...")
            stop_event.wait(timeout=5)
            logger.info("Tắt bot theo Antigravity.")
            os.kill(os.getpid(), 2)  # SIGINT — dừng run_polling sạch
            return


def main():
    """Hàm chạy chính của chương trình AG-Telebot."""
    if not ensure_single_instance():
        logger.warning("Đã có một phiên bản bot khác đang chạy trên máy tính! Thoát để tránh xung đột.")
        sys.exit(0)

    logger.info("=========================================")
    logger.info("Khởi động ANTIGRAVITY TELEGRAM REMOTE BOT")
    logger.info(f"Model mặc định: {settings.DEFAULT_MODEL}")
    logger.info(f"Đường dẫn CLI: {settings.AGY_PATH}")
    logger.info(f"Số lượng User ID được phép: {len(settings.ALLOWED_USER_IDS)}")
    logger.info("=========================================")

    stop_event = threading.Event()
    watcher = threading.Thread(target=_watch_antigravity, args=(stop_event,), daemon=True)
    watcher.start()

    try:
        app = create_bot_application()
        logger.info("Bot đang chạy ở chế độ Long Polling an toàn. Nhấn Ctrl+C để dừng.")
        app.run_polling(drop_pending_updates=True)
    except ValueError as val_err:
        logger.critical(f"Lỗi khởi động: {val_err}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Lỗi không xác định: {e}", exc_info=True)
        sys.exit(1)
    finally:
        stop_event.set()


if __name__ == "__main__":
    main()
