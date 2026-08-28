import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import AsyncOpenAI

# ====== KONFIGURASI ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
USER_ID = int(os.environ.get("USER_ID", "0"))

# ====== SETUP AI ======
client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# ====== CEK USER ======
def is_authorized(user_id):
    """Hanya izinkan pemilik bot"""
    return user_id == USER_ID

# ====== FUNGSI AI ======
async def ask_deepseek(prompt, history=[]):
    """Kirim pertanyaan ke DeepSeek"""
    messages = [
        {"role": "system", "content": "Kamu adalah asisten AI yang pintar, ramah, dan membantu. Jawab dalam bahasa Indonesia kecuali diminta bahasa lain."}
    ]
    
    # Tambahkan riwayat percakapan (maksimal 10 pesan terakhir)
    for msg in history[-10:]:
        messages.append(msg)
    
    # Tambahkan pertanyaan baru
    messages.append({"role": "user", "content": prompt})
    
    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.7,
        max_tokens=2000
    )
    
    return response.choices[0].message.content

# ====== HANDLER ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /start"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Tidak melayani Anda!")
        return
    
    welcome_text = """
🤖 *Bot AI Pribadi Siap!*

Halo! Saya asisten AI pribadimu.
Silakan chat apa saja, saya akan bantu jawab.

📝 *Perintah:*
/start - Mulai bot
/help - Bantuan
/new - Mulai percakapan baru
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /help"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Tidak melayani Anda!")
        return
    
    help_text = """
📚 *Bantuan Bot AI*

Bot ini menggunakan DeepSeek AI.
Fitur:
- 💬 Chat bebas
- 🧠 Ingat konteks percakapan
- 🇮🇩 Bahasa Indonesia

Perintah:
/start - Mulai
/help - Bantuan ini
/new - Reset percakapan
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /new - reset percakapan"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Tidak melayani Anda!")
        return
    
    context.user_data['history'] = []
    await update.message.reply_text("🔄 Percakapan baru dimulai! Silakan chat.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk semua pesan"""
    user_id = update.effective_user.id
    
    # Cek apakah user diizinkan
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Tidak melayani Anda!")
        return
    
    # Ambil pesan
    user_message = update.message.text
    
    # Tampilkan status mengetik
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Ambil riwayat percakapan
    history = context.user_data.get('history', [])
    
    try:
        # Tanya AI
        ai_response = await ask_deepseek(user_message, history)
        
        # Simpan ke riwayat
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_response})
        context.user_data['history'] = history
        
        # Kirim jawaban
        await update.message.reply_text(ai_response)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")

# ====== MAIN ======
def main():
    """Fungsi utama"""
    if not TELEGRAM_TOKEN or not DEEPSEEK_API_KEY:
        print("Error: Token tidak ditemukan!")
        return
    
    # Buat aplikasi
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Tambahkan handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new", new_chat))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Jalankan bot
    print("🤖 Bot AI berjalan...")
    application.run_polling()

if __name__ == "__main__":
    main()
