import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import os
TOKEN = os.getenv("TOKEN")
ADMIN_ID = 8695861346

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

usuarios_paquetes = {}

# ================== PRECIOS ==================

PRECIOS = {
    "basico": "10.000",
    "medio": "15.000",
    "premium": "20.000",
    "suscripcion": "30.000"
}

# ================== ARCHIVOS ==================

ARCHIVOS = {
    "basico": ["basico1.jpeg","basico2.jpeg","basico3.jpeg","basico1.mp4"],
    "medio": ["medio1.jpeg","medio2.jpeg","medio3.jpeg","medio1.mp4","medio2.mp4"],
    "premium": ["premium1.jpeg","premium2.jpeg","premium3.jpeg","premium4.jpeg","premium1.mp4","premium2.mp4"]
}

# ================== START ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    bienvenida_path = os.path.join(BASE_DIR, "bienvenida.jpeg")

    if os.path.exists(bienvenida_path):
        with open(bienvenida_path, "rb") as photo:
            await update.message.reply_photo(photo=photo)

    texto = (
        "Hola mi amor 😘🔥\n\n"
        "Estos son mis paquetes disponibles:\n\n"
        "💎 *BÁSICO*\n"
        "• 3 fotos + 1 video\n"
        "• Precio: *$10.000 COP*\n\n"
        "🔥 *MEDIO*\n"
        "• 3 fotos + 2 videos\n"
        "• Precio: *$15.000 COP*\n\n"
        "👑 *PREMIUM*\n"
        "• 4 fotos + 2 videos\n"
        "• Precio: *$20.000 COP*\n\n"
        "💖 *SUSCRIPCIÓN MENSUAL*\n"
        "• Todo el contenido (Básico + Medio + Premium)\n"
        "• Precio: *$30.000 COP*\n\n"
        "Elige el que quieras abajo 😏👇"
    )

    keyboard = [
        [InlineKeyboardButton("💎 Básico - $10.000", callback_data="paquete_basico")],
        [InlineKeyboardButton("🔥 Medio - $15.000", callback_data="paquete_medio")],
        [InlineKeyboardButton("👑 Premium - $20.000", callback_data="paquete_premium")],
        [InlineKeyboardButton("💖 Suscripción - $30.000", callback_data="paquete_suscripcion")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        texto,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# ================== SELECCIONAR PAQUETE ==================

async def seleccionar_paquete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    paquete = query.data.split("_")[1]
    user_id = query.from_user.id

    usuarios_paquetes[user_id] = paquete

    keyboard = [
        [InlineKeyboardButton("💜 Nequi", callback_data="pago_nequi")],
        [InlineKeyboardButton("🏦 Bancolombia", callback_data="pago_bancolombia")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Elegiste *{paquete.upper()}* 😏🔥\n"
        f"Valor: *${PRECIOS[paquete]} COP*\n\n"
        "Elige tu método de pago:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# ================== METODO DE PAGO ==================

async def metodo_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    metodo = query.data.split("_")[1]

    if metodo == "nequi":
        cuenta = "Nequi: 3001234567"
    else:
        cuenta = "Bancolombia Ahorros: 12345678901"

    await query.edit_message_text(
        f"Perfecto mi amor 💕\n\n"
        f"Envía el pago a:\n\n*{cuenta}*\n\n"
        "Cuando pagues mándame el comprobante aquí 📸",
        parse_mode="Markdown"
    )

# ================== RECIBIR COMPROBANTE ==================

async def recibir_comprobante(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message.photo:
        return

    user_id = update.message.from_user.id

    if user_id not in usuarios_paquetes:
        await update.message.reply_text("Primero elige un paquete con /start 💕")
        return

    paquete = usuarios_paquetes[user_id]

    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=user_id,
        message_id=update.message.message_id
    )

    keyboard = [
        [InlineKeyboardButton(
            "✅ Confirmar Pago",
            callback_data=f"confirmar_{user_id}"
        )]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Comprobante recibido\nUsuario: {user_id}\nPaquete: {paquete}",
        reply_markup=reply_markup
    )

    await update.message.reply_text(
        "Recibí tu comprobante mi amor 💕\n"
        "Estoy verificando el pago 😘"
    )

# ================== CONFIRMAR PAGO ==================

async def confirmar_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    if user_id not in usuarios_paquetes:
        await query.edit_message_text("Usuario no encontrado.")
        return

    paquete = usuarios_paquetes[user_id]

    await query.edit_message_text("Pago confirmado ✅")

    await context.bot.send_message(
        chat_id=user_id,
        text="Ya confirmamos tu comprobante mi amor 😘💖\n"
             "Aquí está tu contenido 🔥"
    )

    await enviar_contenido(user_id, paquete, context)

# ================== ENVIAR CONTENIDO ==================

async def enviar_contenido(user_id, paquete, context):

    packs_dir = BASE_DIR

    # Si es suscripción manda TODO junto
    if paquete == "suscripcion":
        lista_final = (
            ARCHIVOS["basico"] +
            ARCHIVOS["medio"] +
            ARCHIVOS["premium"]
        )
    else:
        lista_final = ARCHIVOS[paquete]

    for archivo in lista_final:
        path = os.path.join(packs_dir, archivo)

        if not os.path.exists(path):
            print("NO EXISTE:", path)
            continue

        with open(path, "rb") as f:
            if archivo.endswith(".mp4"):
                await context.bot.send_video(chat_id=user_id, video=f)
            else:
                await context.bot.send_photo(chat_id=user_id, photo=f)

# ================== MAIN ==================

import asyncio

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(seleccionar_paquete, pattern="^paquete_"))
    app.add_handler(CallbackQueryHandler(metodo_pago, pattern="^pago_"))
    app.add_handler(CallbackQueryHandler(confirmar_pago, pattern="^confirmar_"))
    app.add_handler(MessageHandler(filters.PHOTO, recibir_comprobante))

    print("Bot encendido 🔥")

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
