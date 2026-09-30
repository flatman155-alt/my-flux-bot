import os
import zipfile
import telebot
import requests
import io
import urllib.parse
from PIL import Image
from threading import Thread
from flask import Flask
from telebot import types

# --- МИНИ ВЕБ-СЕРВЕР ДЛЯ ОБХОДА ТАЙМАУТА RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "🤖 Бот успешно запущен и работает в облаке!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web_server).start()
# --------------------------------------------------

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

user_settings = {}

# Художественные стили под стабильную модель
STYLES = {
    '📸 Реалистичный': 'photorealistic, ultra detailed, hyper-realistic, 8k resolution, cinematic lighting, photoreal, photo taken on camera, 35mm lens, sharp focus',
    '🍿 Документальный': 'cinematic documentary shot, national geographic style, dramatic atmosphere, realistic lighting, raw photo, historical look, highly detailed 4k',
    '🏮 Аниме': 'anime style, beautiful digital illustration, makoto shinkai aesthetic, vibrant colors, detailed anime background, studio ghibli look',
    '🎨 Мультфильм': '3D Pixar style cartoon, cute character design, vibrant colors, claymation aesthetic, disney look, volumetric lighting, unreal engine 5 render',
    '🎮 Киберпанк': 'cyberpunk style, neon lights, futuristic high-tech city, glowing details, dark synthwave atmosphere, highly detailed',
    '🛸 Научная фантастика': 'epic sci-fi concept art, space exploration, futuristic technology, alien planet landscape, intricate details, star wars aesthetic'
}

print("🤖 Бот запущен через стабильный Pollinations HD Engine...")

def get_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_16_9 = types.KeyboardButton("🎬 Формат 16:9")
    btn_9_16 = types.KeyboardButton("📱 Формат 9:16")
    btn_style = types.KeyboardButton("🎨 Выбрать стиль")
    btn_status = types.KeyboardButton("⚙️ Мои настройки")
    keyboard.add(btn_16_9, btn_9_16, btn_style, btn_status)
    return keyboard

def get_style_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_real = types.KeyboardButton("📸 Реалистичный")
    btn_doc = types.KeyboardButton("🍿 Документальный")
    btn_anime = types.KeyboardButton("🏮 Аниме")
    btn_cart = types.KeyboardButton("🎨 Мультфильм")
    btn_cyber = types.KeyboardButton("🎮 Киберпанк")
    btn_scifi = types.KeyboardButton("🛸 Научная фантастика")
    btn_back = types.KeyboardButton("⬅️ Назад в меню")
    keyboard.add(btn_real, btn_doc, btn_anime, btn_cart, btn_cyber, btn_scifi, btn_back)
    return keyboard

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id not in user_settings:
        user_settings[chat_id] = {'width': 1280, 'height': 720, 'style': '📸 Реалистичный', 'size_name': '🎬 Горизонтальный (16:9)'}
    
    text = ("Привет! 🎬 Я твой массовый генератор картинок ПРЕМИУМ качества.\n\n"
            "Переключай формат (16:9 или 9:16) и стили прямо кнопками внизу экрана.\n\n"
            "🚀 Как настроишь, просто пришли мне текстовый файл (.txt) с промптами, и я сгенерирую пачку чистых изображений!\n"
            "⚠️ **Важно:** В одном файле должно быть не более 50 промптов.")
    
    bot.send_message(chat_id, text, reply_markup=get_main_menu_keyboard())

@bot.message_handler(content_types=['text'])
def handle_text_buttons(message):
    chat_id = message.chat.id
    if chat_id not in user_settings:
        user_settings[chat_id] = {'width': 1280, 'height': 720, 'style': '📸 Реалистичный', 'size_name': '🎬 Горизонтальный (16:9)'}

    if message.text == "🎬 Формат 16:9":
        user_settings[chat_id]['width'] = 1280
        user_settings[chat_id]['height'] = 720
        user_settings[chat_id]['size_name'] = "🎬 Горизонтальный (16:9)"
        bot.send_message(chat_id, "📐 Сохранено! Теперь картинки будут горизонтальными **16:9**.", parse_mode="Markdown", reply_markup=get_main_menu_keyboard())

    elif message.text == "📱 Формат 9:16":
        user_settings[chat_id]['width'] = 720
        user_settings[chat_id]['height'] = 1280
        user_settings[chat_id]['size_name'] = "📱 Вертикальный (9:16)"
        bot.send_message(chat_id, "📐 Сохранено! Теперь картинки будут вертикальными **9:16** (для Shorts/Reels).", parse_mode="Markdown", reply_markup=get_main_menu_keyboard())

    elif message.text == "🎨 Выбрать стиль":
        bot.send_message(chat_id, "Выбери художественный стиль для твоей пачки картинок:", reply_markup=get_style_menu_keyboard())

    elif message.text in STYLES:
        user_settings[chat_id]['style'] = message.text
        bot.send_message(chat_id, f"✅ Стиль успешно изменен на: **{message.text}**", parse_mode="Markdown", reply_markup=get_main_menu_keyboard())

    elif message.text == "⚙️ Мои настройки" or message.text == "⬅️ Назад в меню":
        current = user_settings[chat_id]
        status_text = (f"⚙️ **Твои active настройки:**\n\n"
                       f"📐 Формат: {current['size_name']} ({current['width']}x{current['height']})\n"
                       f"🎨 Стиль: {current['style']}\n\n"
                       f"Отправь файл .txt для генерации пачки!")
        bot.send_message(chat_id, status_text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    chat_id = message.chat.id
    if not message.document.file_name.endswith('.txt'):
        bot.reply_to(message, "❌ Пожалуйста, пришли файл именно в формате .txt")
        return

    if chat_id not in user_settings:
        user_settings[chat_id] = {'width': 1280, 'height': 720, 'style': '📸 Реалистичный', 'size_name': '🎬 Горизонтальный (16:9)'}
        
    current = user_settings[chat_id]
    status_msg = bot.reply_to(message, f"📥 Файл принят!\n📐 Формат: {current['width']}x{current['height']}\n🎨 Стиль: {current['style']}\n\nПроверяю данные...")
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        lines = downloaded_file.decode('utf-8').splitlines()
        prompts = [p.strip() for p in lines if p.strip()]
        
        if not prompts:
            bot.edit_message_text("❌ Файл пустой!", message.chat.id, status_msg.message_id)
            return

        # 🛡️ УМНЫЙ ЛИМИТ НА ПАЧКИ (Защита от перегрузки серверов)
        MAX_LIMIT = 50
        if len(prompts) > MAX_LIMIT:
            bot.edit_message_text(
                f"⚠️ **Превышен лимит!**\n\n"
                f"В вашем файле обнаружено {len(prompts)} строк.\n"
                f"Максимальный размер бесплатной пачки — **{MAX_LIMIT} картинок**.\n\n"
                f"Пожалуйста, разбейте файл на части или купите Premium-подписку!", 
                message.chat.id, status_msg.message_id, parse_mode="Markdown"
            )
            return

        generated_images = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        
        for idx, prompt in enumerate(prompts):
            bot.edit_message_text(f"🎨 Генерирую премиум HD-картинку {idx + 1} из {len(prompts)}...", message.chat.id, status_msg.message_id)
            
            style_tags = STYLES[current['style']]
            full_prompt = f"{prompt.strip()}, {style_tags}"
            encoded_text = urllib.parse.quote(full_prompt)
            
            # 🔥 ОБНОВЛЕННЫЙ ПРЯМОЙ И СВЕРХБЫСТРЫЙ ИИ-ДВИЖОК POLLINATIONS AI
            api_link = f"https://pollinations.ai{encoded_text}?width={current['width']}&height={current['height']}&nologo=true&seed={idx + 42}"
            
            try:
                # Скачиваем саму картинку напрямую, без лишних проверок JSON шлюзов
                response = requests.get(api_link, headers=headers, timeout=60)
                if response.content:
                    img_data = response.content
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Финальный ресайз для идеальной четкости под формат видео
                    img = img.resize((current['width'], current['height']))
                    generated_images.append((f"image_{idx + 1}.png", img))
            except Exception as e:
                print(f"Ошибка на картинке {idx+1}: {e}")
                continue

        if not generated_images:
            bot.edit_message_text("❌ Все запросы ИИ были отклонены. Пожалуйста, попробуйте еще раз через минуту.", message.chat.id, status_msg.message_id)
            return

        bot.edit_message_text("📦 Упаковываю все настроенные картинки в ZIP-архив...", message.chat.id, status_msg.message_id)
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for file_name, img in generated_images:
                img_buffer = io.BytesIO()
                img.save(img_buffer, format="PNG")
                zip_file.writestr(file_name, img_buffer.getvalue())
                
        zip_buffer.seek(0)
        bot.send_document(message.chat.id, io.BytesIO(zip_buffer.read()), visible_file_name="premium_hd_pack.zip")
        bot.delete_message(message.chat.id, status_msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(f"💥 Произошла ошибка: {str(e)}", message.chat.id, status_msg.message_id)

bot.infinity_polling()



