from flask import Flask
from threading import Thread
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
import requests
import logging
import os
import re
import json

# =====================================================
# 📋 CONFIGURATION
# =====================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8773653442:AAFKqLfghw-DSY1hAVkFZRwYbnTPqYNd9oo")
API_URL = "https://numtolnfo.suryajasoos-4fe.workers.dev/?mobile={}"
MAX_RESULTS = 5
REQUEST_TIMEOUT = 20

app = Flask(__name__)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =====================================================
# 🛠️ HELPER FUNCTIONS
# =====================================================

def clean_mobile_number(number: str) -> str:
    return ''.join(filter(str.isdigit, number))

def validate_mobile(number: str) -> bool:
    return 10 <= len(number) <= 15

def format_address(address: str) -> str:
    if not address or address == "NA":
        return "N/A"
    formatted = address.replace('!', ', ')
    formatted = re.sub(r',\s*,', ',', formatted)
    formatted = re.sub(r',\s*$', '', formatted)
    return formatted

def format_response(data: dict, mobile: str) -> str:
    if not data.get("success"):
        return "❌ *API Error:* Request was not successful."
    
    records = data.get("response", [])
    if not records:
        return f"❌ *No information found* for number *{mobile}*."
    
    result = f"📱 *Number Information:* `{mobile}`\n"
    result += f"🔹 *Owner:* {data.get('owner', 'N/A')}\n"
    result += f"🔹 *Powered By:* {data.get('powered_by', 'N/A')}\n"
    result += "═" * 30 + "\n\n"
    
    for idx, entry in enumerate(records[:MAX_RESULTS], 1):
        result += f"📌 *Record #{idx}*\n"
        result += f"👤 *Name:* {entry.get('name', 'N/A')}\n"
        result += f"👨 *Father:* {entry.get('fname', 'N/A')}\n"
        result += f"📍 *Address:* {format_address(entry.get('address'))}\n"
        result += f"📞 *Alternate:* {entry.get('alt', 'N/A')}\n"
        result += f"📡 *Circle:* {entry.get('circle', 'N/A')}\n"
        result += f"🆔 *ID:* {entry.get('id', 'N/A')}\n"
        result += "─" * 25 + "\n"
    
    if len(records) > MAX_RESULTS:
        result += f"\n⚠️ *Showing first {MAX_RESULTS} of {len(records)} records.*"
    
    return result

async def fetch_number_info(mobile: str) -> dict:
    try:
        logger.info(f"Fetching info for: {mobile}")
        response = requests.get(API_URL.format(mobile), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Received {len(data.get('response', []))} records")
        return {"success": True, "data": data}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "⏰ *Timeout.* Server taking too long."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "🌐 *Network error.* Check internet."}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"⚠️ *API Error:* {str(e)}"}
    except json.JSONDecodeError:
        return {"success": False, "error": "⚠️ *Invalid response from server.*"}
    except Exception as e:
        return {"success": False, "error": f"⚠️ *Error:* {str(e)}"}

# =====================================================
# 🤖 BOT COMMAND HANDLERS
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 *Welcome to Number Info Bot!*\n\n"
        "🔍 Send me any mobile number (10-15 digits)\n"
        "Example: `9720294892` or `+919720294892`\n\n"
        "*Commands:*\n"
        "/start - Show this message\n"
        "/help - Detailed help\n"
        "/about - About this bot\n\n"
        "⚠️ *Use responsibly and for legal purposes only.*",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 *Help Guide*\n\n"
        "*How to use:*\n"
        "1. Send any 10-15 digit mobile number\n"
        "2. Bot will fetch and display information\n\n"
        "*Formats accepted:*\n"
        "• `9720294892` (10 digits)\n"
        "• `+919720294892` (with country code)\n\n"
        "*Information shown:*\n"
        "✅ Name & Father's Name\n"
        "✅ Address\n"
        "✅ Alternate Numbers\n"
        "✅ Network Operator\n\n"
        "*Contact:* @suryajasoos",
        parse_mode="Markdown"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ *About This Bot*\n\n"
        "🤖 *Name:* Number Info Bot\n"
        "⚡ *Version:* 1.0\n"
        "👨‍💻 *Developer:* @suryajasoos\n"
        "🔗 *API:* Surya Hacker API\n"
        "🌐 *Hosted on:* Render\n\n"
        "*Tech Stack:*\n"
        "• Python 3.8+\n"
        "• python-telegram-bot v20.0+\n"
        "• Flask + Requests",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text.strip()
    clean_number = clean_mobile_number(user_message)
    
    if not clean_number:
        await update.message.reply_text(
            "❌ *Invalid Input*\n\nPlease send a valid mobile number.\nExample: `9720294892`",
            parse_mode="Markdown"
        )
        return
    
    if not validate_mobile(clean_number):
        await update.message.reply_text(
            f"❌ *Invalid Length*\n\nNumber `{clean_number}` has {len(clean_number)} digits.\nPlease send 10-15 digits.",
            parse_mode="Markdown"
        )
        return

    await update.message.chat.send_action(action="typing")
    
    status = await update.message.reply_text(
        f"🔍 *Searching for:* `{clean_number}`\n⏳ Please wait...",
        parse_mode="Markdown"
    )
    
    result = await fetch_number_info(clean_number)
    
    if not result["success"]:
        await status.edit_text(result["error"], parse_mode="Markdown")
        return
    
    formatted = format_response(result["data"], clean_number)
    
    if len(formatted) > 4000:
        parts = [formatted[i:i+4000] for i in range(0, len(formatted), 4000)]
        await status.edit_text(parts[0], parse_mode="Markdown")
        for part in parts[1:]:
            await update.message.reply_text(part, parse_mode="Markdown")
    else:
        await status.edit_text(formatted, parse_mode="Markdown")

# =====================================================
# 🏥 FLASK WEB SERVER
# =====================================================

@app.route('/')
@app.route('/health')
def health_check():
    return "🤖 Bot is running!", 200

@app.route('/ping')
def ping():
    return {"status": "alive", "timestamp": __import__('time').time()}, 200

# =====================================================
# 🚀 MAIN APPLICATION
# =====================================================

def run_bot():
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        logger.info("Bot started successfully!")
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port)
