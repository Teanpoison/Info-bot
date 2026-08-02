import telebot
import requests

TOKEN = '8773653442:AAFKqLfghw-DSY1hAVkFZRwYbnTPqYNd9oo'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Namaste! 🙏\nMujhe koi bhi mobile number bhejein, aur main uski details nikal kar dunga.")

@bot.message_handler(func=lambda message: True)
def fetch_sim_info(message):
    number = message.text.strip()
    bot.reply_to(message, "🔍 Details nikal raha hoon, please wait...")
    
    try:
        api_url = f"https://numtolnfo.suryajasoos-4fe.workers.dev/?mobile={number}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(api_url, headers=headers)
        
        try:
            data = response.json()
        except:
            bot.send_message(message.chat.id, "❌ API ne sahi format mein data nahi bheja.")
            return

        # API ke data me se records dhundhna
        records = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            for val in data.values():
                if isinstance(val, list):
                    records = val
                    break
            if not records:
                records = [data]

        if not records or len(records) == 0:
            bot.send_message(message.chat.id, "❌ Is number ki koi details nahi mili.")
            return

        # Message ko sundar format dena
        final_msg = f"📱 **Search Result For: {number}** 📱\n━━━━━━━━━━━━━━━━\n"
        
        # Har ek record ko line by line set karna
        for idx, rec in enumerate(records):
            if isinstance(rec, dict) and 'name' in rec:
                final_msg += f"🔹 **Record {idx+1}** 🔹\n"
                final_msg += f"👤 **Name:** {rec.get('name', 'N/A')}\n"
                final_msg += f"👨‍👦 **Father Name:** {rec.get('fname', 'N/A')}\n"
                final_msg += f"📍 **Address:** {rec.get('address', 'N/A')}\n"
                final_msg += f"🗼 **Circle/SIM:** {rec.get('circle', 'N/A')}\n"
                final_msg += f"📞 **Alt Number:** {rec.get('alt', 'N/A')}\n"
                
                # ⬇️ यहाँ बस यह 1 लाइन डाली है
                final_msg += f"🆔 **ID:** {rec.get('id', 'N/A')}\n"
                
                final_msg += "━━━━━━━━━━━━━━━━\n"

        # Agar message bahut bada ho jaye toh usko trim karna
        if len(final_msg) > 4000:
            final_msg = final_msg[:4000] + "\n... (Data bahut bada hai isliye cut ho gaya)"

        bot.send_message(message.chat.id, final_msg)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

print("✅ Bot ekdum ready hai! Ab Telegram par check karein...")

if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling()
