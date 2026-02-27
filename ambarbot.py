import random
import sqlite3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8581605737:AAFwEA0SrrwqkAtujaEE2wqquwz1znDG2rM"
ADMIN_ID = 8695861346

# -------- RUTA BASE -------- #

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# -------- BASE DE DATOS -------- #

conn = sqlite3.connect(os.path.join(BASE_DIR, "clientes.db"), check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    nombre TEXT,
    paquete TEXT,
    precio INTEGER,
    estado TEXT,
    fecha TEXT
)
""")
conn.commit()

def guardar_cliente(user_id, nombre, paquete, precio, estado):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO clientes (user_id, nombre, paquete, precio, estado, fecha)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, nombre, paquete, precio, estado, fecha))
    conn.commit()

def marcar_pagado(user_id):
    cursor.execute("""
    UPDATE clientes
    SET estado = 'Pagado'
    WHERE id = (
        SELECT id FROM clientes
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    )
    """, (user_id,))
    conn.commit()

# -------- PAQUETES -------- #

paquetes = {
    "basico": {"precio": 10000},
    "medio": {"precio": 15000},
    "premium": {"precio": 20000}
}

# -------- MENUS -------- #

def menu_edad():
    keyboard = [
        [InlineKeyboardButton("🔞 Soy mayor de 18", callback_data="mayor")],
        [InlineKeyboardButton("❌ Salir", callback_data="salir")]
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_paquetes():
    keyboard = [
        [InlineKeyboardButton("🔥 Básico - 3 fotos + 2 videos ($10.000)", callback_data="basico")],
        [InlineKeyboardButton("🔥 Medio - 4 fotos + 2 videos ($15.000)", callback_data="medio")],
        [InlineKeyboardButton("🔥 Premium - 3 fotos + 2 videos ($20.000)", callback_data="premium")]
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_pago():
    keyboard = [
        [InlineKeyboardButton("💜 Nequi", callback_data="nequi")],
        [InlineKeyboardButton("🏦 Bancolombia", callback_data="bancolombia")]
    ]
    return InlineKeyboardMarkup(keyboard)

# -------- START -------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.from_user.first_name

    mensajes = [
        f"Hola {nombre} 😊 gracias por estar aquí.\n\nMira los paquetes y dime cuál te gusta más 💕",
        f"{nombre} hola... qué bueno verte por aquí 😌\n\nRevisa lo que tengo preparado y elige tranquilo 😉",
        f"Bienvenido {nombre} 💋\n\nPasa, mira los paquetes y dime cuál prefieres."
    ]

    texto = random.choice(mensajes)

    await update.message.reply_photo(
        photo=open(os.path.join(BASE_DIR, "bienvenida.jpeg"), "rb"),
        caption=texto,
        reply_markup=menu_edad(),
        protect_content=True
    )

# -------- VERIFICAR EDAD -------- #

async def verificar_edad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "mayor":
        await query.message.reply_text(
            "Perfecto 💕 elige el paquete:",
            reply_markup=menu_paquetes()
        )
    else:
        await query.message.reply_text("Cuando quieras volver aquí estaré 😊")

# -------- SELECCIONAR PAQUETE -------- #

async def seleccionar_paquete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    paquete = query.data
    context.user_data["paquete"] = paquete
    precio = paquetes[paquete]["precio"]

    await query.message.reply_text(
        f"Total: ${precio} COP 💰\n\nSelecciona método de pago:",
        reply_markup=menu_pago()
    )

# -------- SELECCIONAR PAGO -------- #

async def seleccionar_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    metodo = query.data
    paquete = context.user_data["paquete"]
    precio = paquetes[paquete]["precio"]
    user_id = query.from_user.id
    nombre = query.from_user.first_name

    guardar_cliente(user_id, nombre, paquete, precio, "Pendiente")

    if metodo == "nequi":
        texto = f"💜 Nequi\nNúmero: 3204967458\nValor: ${precio}\n\nEnvía el comprobante."
    else:
        texto = f"🏦 Bancolombia\nCuenta: 1001211111111\nValor: ${precio}\n\nEnvía el comprobante."

    await query.message.reply_text(texto)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🆕 Nuevo comprador\nNombre: {nombre}\nID: {user_id}\nPaquete: {paquete}\nMétodo: {metodo}"
    )

# -------- RECIBIR COMPROBANTE -------- #

async def recibir_comprobante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        user_id = update.message.from_user.id
        paquete = context.user_data.get("paquete")

        keyboard = [
            [InlineKeyboardButton("✅ Confirmar Pago", callback_data=f"confirmar_{user_id}")]
        ]

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=f"📸 Comprobante\nID: {user_id}\nPaquete: {paquete}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text("Comprobante recibido 💕 confirmo en breve.")

# -------- CONFIRMAR Y ENTREGAR -------- #

async def confirmar_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    user_id = int(query.data.split("_")[1])
    paquete = context.user_data.get("paquete")

    marcar_pagado(user_id)

    if paquete == "basico":
        fotos = ["basico1.jpeg", "basico2.jpeg", "basico3.jpeg"]
        videos = ["basico1.mp4", "basico2.mp4"]
    elif paquete == "medio":
        fotos = ["medio1.jpeg", "medio2.jpeg", "medio3.jpeg", "medio4.jpeg"]
        videos = ["medio1.mp4", "medio2.mp4"]
    else:
        fotos = ["premium1.jpeg", "premium2.jpeg", "premium3.jpeg"]
        videos = ["premium1.mp4", "premium2.mp4"]

    media = [
        InputMediaPhoto(open(os.path.join(BASE_DIR, "packs", f), "rb"))
        for f in fotos
    ]

    await context.bot.send_media_group(
        chat_id=user_id,
        media=media,
        protect_content=True
    )

    for v in videos:
        await context.bot.send_video(
            chat_id=user_id,
            video=open(os.path.join(BASE_DIR, "packs", v), "rb"),
            protect_content=True
        )

    await context.bot.send_message(
        chat_id=user_id,
        text="Pago confirmado 💕 aquí tienes tu contenido.",
        protect_content=True
    )

    await query.edit_message_caption(
        caption=query.message.caption + "\n\n✅ Entregado"
    )

# -------- APP -------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(verificar_edad, pattern="^(mayor|salir)$"))
app.add_handler(CallbackQueryHandler(seleccionar_paquete, pattern="^(basico|medio|premium)$"))
app.add_handler(CallbackQueryHandler(seleccionar_pago, pattern="^(nequi|bancolombia)$"))
app.add_handler(CallbackQueryHandler(confirmar_pago, pattern="^confirmar_"))
app.add_handler(MessageHandler(filters.PHOTO, recibir_comprobante))

app.run_polling(drop_pending_updates=True)