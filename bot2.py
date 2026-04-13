import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = os.getenv('WEBAPP_URL', 'https://example.com')
    kbd = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Abrir Explorador", web_app=WebAppInfo(url=url))]
    ])
    await update.message.reply_text("¡Hola! Soy El Explorador del Centro de Enlaces. Abre la Mini App para buscar y navegar.", reply_markup=kbd)

def main():
    token = os.getenv('BOT2_TOKEN')
    if not token:
        print("BOT2_TOKEN NO ENCONTRADO")
        return
        
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    
    print("Iniciando El Explorador (Bot #2)...")
    app.run_polling()

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    main()
