import os
import zipfile
import telebot
import requests
import io
import urllib.parse
from PIL import Image
from threading import Thread
from flask import Flask

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

# Забираем токен Телеграм из скрытых настроек сервера
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

print("🤖 Бот 'Массовый Генератор Картинок' успешно запущен в облаке через Pollinations...")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! 🎬 Я твой массовый генератор картинок.\n\nПросто пришли мне текстовый файл (.txt), где каждая строчка — это новый промпт на английском, и я сгенерирую тебе пачку крутых изображений!")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if not message.document.file_name.endswith('.txt'):
        bot.reply_to(message, "❌ Пожалуйста, пришли файл именно в формате .txt")
        return

    status_msg = bot.reply_to(message, "📥 Файл принят! Начинаю читать промпты и генерировать картинки. Подожди немного...")
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        prompts = downloaded_file.decode('utf-8').splitlines()
        prompts = [p.strip() for p in prompts if p.strip()]
        
        if not prompts:
            bot.edit_message_text("❌ Файл пустой! Напиши промпты внутри файла.", message.chat.id, status_msg.message_id)
            return

        generated_images = []
        
        for idx, prompt in enumerate(prompts):
            bot.edit_message_text(f"🎨 Генерирую картинку {idx + 1} из {len(prompts)}...", message.chat.id, status_msg.message_id)
            
            # Кодируем текст промпта для безопасной передачи в ссылке
            encoded_prompt = urllib.parse.quote(prompt)
            
            # Генерируем картинку через бесплатный и быстрый Flux от Pollinations.ai
            # Добавляем параметры для лучшего качества и стиля обложки YouTube
            image_url = f"https://pollinations.ai{encoded_prompt}?width=1280&height=720&model=flux&enhance=true"
            
            response = requests.get(image_url, timeout=40)
            
            if response.status_code == 200:
                image_bytes = response.content
                img = Image.open(io.BytesIO(image_bytes))
                generated_images.append((f"image_{idx + 1}.png", img))
            else:
                print(f"Ошибка на промпте '{prompt}': {response.status_code}")
                continue

        if not generated_images:
            bot.edit_message_text("❌ Не удалось сгенерировать картинки. Попробуй позже.", message.chat.id, status_msg.message_id)
            return

        bot.edit_message_text("📦 Упаковываю все картинки in ZIP-архив...", message.chat.id, status_msg.message_id)
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for file_name, img in generated_images:
                img_buffer = io.BytesIO()
                img.save(img_buffer, format="PNG")
                zip_file.writestr(file_name, img_buffer.getvalue())
                
        zip_buffer.seek(0)
        
        bot.send_document(message.chat.id, io.BytesIO(zip_buffer.read()), visible_file_name="your_images_pack.zip")
        bot.delete_message(message.chat.id, status_msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(f"💥 Произошла ошибка: {str(e)}", message.chat.id, status_msg.message_id)

bot.infinity_polling()


