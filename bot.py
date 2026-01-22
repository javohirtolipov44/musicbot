import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
from mutagen.id3 import ID3, APIC, TPE1, TALB, TIT2
from mutagen.mp4 import MP4, MP4Cover
from mutagen import File as MutagenFile

# --- SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot Live!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

keep_alive()

# --- SOZLAMALAR ---
API_TOKEN = '8259575713:AAHONkoTzwjh4Up_UxJ-3-QInYi_jwSrLp4'
FIXED_ARTIST = "Subscribe"
FIXED_ALBUM = "@freestyle_beat"
IMAGE_PATH = "cover.jpg"

bot = telebot.TeleBot(API_TOKEN)

def edit_mp3(file_path, title):
    try:
        try: audio = ID3(file_path)
        except: audio = ID3()
        audio['TPE1'] = TPE1(encoding=3, text=FIXED_ARTIST)
        audio['TALB'] = TALB(encoding=3, text=FIXED_ALBUM)
        audio['TIT2'] = TIT2(encoding=3, text=title)
        if os.path.exists(IMAGE_PATH):
            with open(IMAGE_PATH, 'rb') as img:
                audio['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img.read())
        audio.save(v2_version=3)
    except: pass

def edit_m4a(file_path, title):
    try:
        audio = MP4(file_path)
        audio["\xa9ART"] = FIXED_ARTIST
        audio["\xa9alb"] = FIXED_ALBUM
        audio["\xa9nam"] = title
        if os.path.exists(IMAGE_PATH):
            with open(IMAGE_PATH, "rb") as img:
                audio["covr"] = [MP4Cover(img.read(), imageformat=MP4Cover.FORMAT_JPEG)]
        audio.save()
    except: pass

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "<b>Tayyorman! .mp3 yoki .m4a yuboring.</b>", parse_mode="HTML")

@bot.message_handler(content_types=['audio', 'document'])
def handle_audio(message):
    file_id = None
    file_name = ""
    orig_duration = 0
    
    if message.content_type == 'audio':
        file_id = message.audio.file_id
        file_name = message.audio.title or "music"
        orig_duration = message.audio.duration
    elif message.content_type == 'document' and message.document.mime_type in ['audio/mp4', 'audio/mpeg', 'audio/x-m4a']:
        file_id = message.document.file_id
        file_name = message.document.file_name

    if not file_id: return

    chat_id = message.chat.id
    ext = ".m4a" if "m4a" in file_name.lower() else ".mp3"
    temp_file = f"music_{chat_id}{ext}"
    
    msg = bot.send_message(chat_id, "⏳ <b>Fayl tahrirlanmoqda...</b>", parse_mode="HTML")

    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(temp_file, 'wb') as f: f.write(downloaded_file)

        # Tahrirlash
        if ext == ".m4a": edit_m4a(temp_file, file_name)
        else: edit_mp3(temp_file, file_name)

        # Davomiylikni (vaqtni) qayta aniqlash
        try:
            audio_info = MutagenFile(temp_file)
            duration = int(audio_info.info.length) if audio_info and audio_info.info else orig_duration
        except:
            duration = orig_duration

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Kanalimiz", url="https://t.me/freestyle_beat"))

        with open(temp_file, 'rb') as audio_file:
            thumb = open(IMAGE_PATH, 'rb') if os.path.exists(IMAGE_PATH) else None
            bot.send_audio(
                chat_id, audio_file,
                caption=f"⚡ <b>Freestyle:</b> {FIXED_ARTIST}\n💿 <b>Albom:</b> {FIXED_ALBUM}",
                parse_mode="HTML", 
                thumb=thumb, 
                performer=FIXED_ARTIST, 
                title=file_name, 
                reply_markup=markup,
                duration=duration # VAQT MUAMMOSINI TUZATISH
            )
            if thumb: thumb.close()
        bot.delete_message(chat_id, msg.message_id)
    except:
        bot.send_message(chat_id, "❌ Xatolik.")
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling(timeout=20)
    
