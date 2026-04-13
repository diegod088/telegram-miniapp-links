import os
import datetime
import re
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler
from telegram.constants import ParseMode
from models import SessionLocal, Usuario, Categoria, Enlace, Publicacion, CalificacionReporte

AWAITING_URL, AWAITING_TITLE, AWAITING_DESC, AWAITING_CAT, AWAITING_CONFIRM = range(5)
LIMIT_PER_DAY = 5
LIMIT_DAYS_DUPLICATE = 7

async def register_user(update: Update, db_session):
    user = update.effective_user
    db_user = db_session.query(Usuario).filter_by(telegram_user_id=user.id).first()
    today = datetime.datetime.now(datetime.UTC).date()
    
    if not db_user:
        db_user = Usuario(
            telegram_user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            daily_count=0,
            last_reset=datetime.datetime.now(datetime.UTC)
        )
        db_session.add(db_user)
        db_session.commit()
    else:
        if db_user.last_reset and db_user.last_reset.date() != today:
            db_user.daily_count = 0
            db_user.last_reset = datetime.datetime.now(datetime.UTC)
            db_session.commit()
            
    return db_user

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Soy El Publicador. Envía la palabra 'publicar' o el comando /publicar para enviar un enlace.")

async def cmd_publicar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_session = SessionLocal()
    db_user = await register_user(update, db_session)
    
    if db_user.baneado:
        await update.message.reply_text(f"Estás baneado y no puedes usar el bot. Motivo: {db_user.motivo_baneo}")
        db_session.close()
        return ConversationHandler.END

    if db_user.daily_count >= LIMIT_PER_DAY:
        await update.message.reply_text(f"Has alcanzado tu límite de {LIMIT_PER_DAY} enlaces por día. Intenta mañana.")
        db_session.close()
        return ConversationHandler.END
        
    db_session.close()
    await update.message.reply_text("Por favor, envíame el ENLACE (URL) que deseas publicar.")
    return AWAITING_URL

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.startswith("http"):
        await update.message.reply_text("Envía un URL válido (empezando con http/https).")
        return AWAITING_URL
        
    db_session = SessionLocal()
    
    # Validation 7 days duplicate
    limit_date = datetime.datetime.utcnow() - datetime.timedelta(days=LIMIT_DAYS_DUPLICATE)
    dup = db_session.query(Publicacion).join(Enlace).filter(Enlace.url == text, Publicacion.fecha_hora_publicacion >= limit_date).first()
    
    db_session.close()
    
    if dup:
        await update.message.reply_text(f"Este enlace ya fue publicado en los últimos {LIMIT_DAYS_DUPLICATE} días. Usa otro.")
        return ConversationHandler.END
        
    context.user_data['url'] = text
    await update.message.reply_text("Enlace aceptado.\nAhora, envíame el **TÍTULO** para este enlace, o envía la palabra 'omitir'.", parse_mode='Markdown')
    return AWAITING_TITLE

async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower() != 'omitir':
        context.user_data['title'] = text
    else:
        context.user_data['title'] = None
    
    await update.message.reply_text("Perfecto. Ahora, envíame una breve **DESCRIPCIÓN**, o envía 'omitir'.", parse_mode='Markdown')
    return AWAITING_DESC

async def handle_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower() != 'omitir':
        context.user_data['desc'] = text
    else:
        context.user_data['desc'] = None

    db_session = SessionLocal()
    categorias = db_session.query(Categoria).all()
    db_session.close()
    
    keyboard = []
    row = []
    for c in categorias:
        row.append(InlineKeyboardButton(c.nombre_categoria, callback_data=f"cat_{c.id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    await update.message.reply_text("Selecciona la **Categoría** a la que pertenece:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return AWAITING_CAT

async def handle_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    cat_id = int(query.data.split('_')[1])
    context.user_data['cat_id'] = cat_id
    
    db_session = SessionLocal()
    cat = db_session.query(Categoria).filter_by(id=cat_id).first()
    db_session.close()
    
    url = context.user_data.get('url')
    titulo = context.user_data.get('title') or '-'
    desc = context.user_data.get('desc') or '-'

    msg = f"<b>Confirmación de Publicación</b>\n" \
          f"URL: {html.escape(url)}\n" \
          f"Título: {html.escape(titulo)}\n" \
          f"Descripción: {html.escape(desc)}\n" \
          f"Categoría: {html.escape(cat.nombre_categoria)}\n\n" \
          f"¿Deseas publicarlo ahora?"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Sí, publicar", callback_data="confirm_pub"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancel_pub")
        ]
    ]
    
    await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    return AWAITING_CONFIRM

async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_pub":
        await query.edit_message_text("Publicación cancelada.")
        context.user_data.clear()
        return ConversationHandler.END
        
    # confirm_pub
    db_session = SessionLocal()
    user = await register_user(update, db_session)
    
    url = context.user_data.get('url')
    titulo = context.user_data.get('title')
    desc = context.user_data.get('desc')
    cat_id = context.user_data.get('cat_id')
    
    enlace = db_session.query(Enlace).filter_by(url=url).first()
    if not enlace:
        enlace = Enlace(url=url, titulo=titulo, descripcion=desc, categoria_id=cat_id)
        db_session.add(enlace)
        db_session.flush() # get ID
        
    cat = db_session.query(Categoria).filter_by(id=cat_id).first()
    
    # Modificar contador usuario
    user.daily_count += 1
    
    channel_id = os.getenv('CHANNEL_ID')
    if not channel_id:
        await query.edit_message_text("Error: CHANNEL_ID no configurado")
        db_session.close()
        return ConversationHandler.END

    username_str = f"@{update.effective_user.username}" if update.effective_user.username else update.effective_user.first_name
    
    msg_text = f"🔗 <b>Nuevo Enlace: {html.escape(titulo or 'Visitar Enlace')}</b>\n\n" \
               f"📂 Categoría: {html.escape(cat.nombre_categoria)}\n" \
               f"{f'📝 {html.escape(desc)}' if desc else ''}\n" \
               f"👤 Por: {html.escape(username_str)}\n\n" \
               f"👉 {html.escape(url)}"

    try:
        sent_msg = await context.bot.send_message(
            chat_id=channel_id,
            text=msg_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False
        )
        
        pub = Publicacion(enlace_id=enlace.id, usuario_publicador_id=user.id, mensaje_id_canal=sent_msg.message_id)
        db_session.add(pub)
        db_session.commit()
        
        # update keyboard
        kb = [
            [
                InlineKeyboardButton("👍", callback_data=f"r_like_{pub.id}"),
                InlineKeyboardButton("👎", callback_data=f"r_dislike_{pub.id}")
            ],
            [
                InlineKeyboardButton("⚠️ Reportar", callback_data=f"r_report_inap_{pub.id}")
            ]
        ]
        
        await context.bot.edit_message_reply_markup(
            chat_id=channel_id,
            message_id=sent_msg.message_id,
            reply_markup=InlineKeyboardMarkup(kb)
        )
        
        await query.edit_message_text("¡Publicado con éxito en el canal principal!")
        
    except Exception as e:
        print(f"Error publishing: {e}")
        await query.edit_message_text("Ocurrió un error publicando en el canal. Revisa los permisos e IDs.")
        db_session.rollback()

    db_session.close()
    context.user_data.clear()
    return ConversationHandler.END

async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    parts = query.data.split('_')
    t = parts[1] # like, dislike, report
    if parts[2] == 'inap':
        tipo = 'report_inap'
        pub_id = int(parts[3])
    else:
        tipo = t
        pub_id = int(parts[2])
        
    db_session = SessionLocal()
    user = await register_user(update, db_session)
    
    # check existing
    exist = db_session.query(CalificacionReporte).filter_by(publicacion_id=pub_id, usuario_calificador_id=user.id, tipo=tipo).first()
    if exist:
        await query.answer("Ya has registrado este evento.")
        db_session.close()
        return
        
    cr = CalificacionReporte(publicacion_id=pub_id, usuario_calificador_id=user.id, tipo=tipo)
    db_session.add(cr)
    db_session.commit()
    
    await query.answer("Evento registrado." if tipo == 'like' else "Evento guardado.")
    
    # limit check for report_inap
    if tipo == 'report_inap':
        count = db_session.query(CalificacionReporte).filter_by(publicacion_id=pub_id, tipo='report_inap').count()
        if count >= 5:
            pub = db_session.query(Publicacion).filter_by(id=pub_id).first()
            if pub:
                # Ban user
                pub.publicador.baneado = True
                pub.publicador.motivo_baneo = "Demasiados reportes en una sola publicación"
                db_session.commit()
                
                # Try delete msg
                if pub.mensaje_id_canal:
                    try:
                        await context.bot.delete_message(chat_id=os.getenv('CHANNEL_ID'), message_id=pub.mensaje_id_canal)
                    except Exception as e:
                        print("Could not delete:", e)
                        
    db_session.close()

def main():
    token = os.getenv('BOT1_TOKEN')
    if not token:
        print("BOT1_TOKEN NO ENCONTRADO")
        return
    app = ApplicationBuilder().token(token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('publicar', cmd_publicar),
            MessageHandler(filters.Regex(re.compile(r'^publicar$', re.IGNORECASE)), cmd_publicar)
        ],
        states={
            AWAITING_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url)],
            AWAITING_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url) if False else MessageHandler(filters.TEXT & ~filters.COMMAND, handle_title)], # using handle_title
            AWAITING_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_desc)],
            AWAITING_CAT: [CallbackQueryHandler(handle_cat, pattern='^cat_')],
            AWAITING_CONFIRM: [CallbackQueryHandler(handle_confirm, pattern='^(confirm_pub|cancel_pub)$')]
        },
        fallbacks=[CommandHandler('start', cmd_start)]
    )
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_reaction, pattern='^r_'))
    
    print("Iniciando El Publicador (Bot #1)...")
    app.run_polling()

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    main()
