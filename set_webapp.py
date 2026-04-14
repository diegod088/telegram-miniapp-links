import asyncio
import os
from telegram import Bot, MenuButtonWebApp, WebAppInfo
from dotenv import load_dotenv

async def set_url():
    load_dotenv()
    token = os.getenv('BOT_TOKEN')
    webapp_url = os.getenv('WEBAPP_URL')
    
    if not token or not webapp_url:
        print("Error: BOT2_TOKEN o WEBAPP_URL no encontrados en .env")
        return

    import time
    timestamp = int(time.time())
    if '?' in webapp_url:
        final_url = f"{webapp_url}&v={timestamp}"
    else:
        final_url = f"{webapp_url}?v={timestamp}"

    bot = Bot(token=token)
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text='🔍 Abrir Explorador',
                web_app=WebAppInfo(url=final_url)
            )
        )
        print(f"✅ URL '{final_url}' configurada con éxito en el Bot #2.")
    except Exception as e:
        print(f"❌ Error al configurar el botón: {e}")

if __name__ == '__main__':
    asyncio.run(set_url())
