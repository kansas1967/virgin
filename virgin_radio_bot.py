"""
Virgin Radio Discord Bot
-------------------------
Sadece Virgin Radio yayınını çalan basit bir Discord botu.

KURULUM:
1) Python 3.9+ gerekli.
2) FFmpeg kurulu olmalı ve PATH'te olmalı (https://ffmpeg.org/download.html).
   - Windows: ffmpeg.exe'yi indirip klasörünü Sistem PATH'ine ekle.
   - Mac: brew install ffmpeg
   - Linux: sudo apt install ffmpeg
3) Gerekli kütüphaneleri kur:
     pip install -U discord.py PyNaCl
4) Aşağıdaki TOKEN kısmına kendi bot token'ını yaz (veya ortam değişkeni kullan).
5) Botu Discord sunucuna davet ederken şu izinleri ver:
     - View Channels
     - Connect
     - Speak
   ve "applications.commands" scope'unu da seç ki /virgin komutu görünsün.
6) Çalıştır:
     python virgin_radio_bot.py

KOMUTLAR:
  /virgin   -> Bulunduğun ses kanalına katılır ve Virgin Radio'yu çalmaya başlar.
  /stop     -> Yayını durdurur ve ses kanalından ayrılır.
"""

import os
import discord
from discord import app_commands
from discord.ext import commands

# --- AYARLAR ---------------------------------------------------------------

# Token'ı doğrudan buraya yazabilirsin (önerilmez) ya da ortam değişkeninden oku.
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "BURAYA_BOT_TOKENINI_YAZ")

# Virgin Radio canlı yayın adresi
VIRGIN_RADIO_STREAM_URL = "https://29103.live.streamtheworld.com/VIRGIN_RADIO.mp3"

# FFmpeg'in bağlantı kopmalarında yeniden bağlanmayı denemesi için seçenekler
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

# --- BOT KURULUMU ------------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = False  # sadece slash komut kullanıyoruz

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} komut senkronize edildi.")
    except Exception as e:
        print(f"Komut senkronizasyon hatası: {e}")
    print(f"Bot giriş yaptı: {bot.user} (Virgin Radio botu hazır)")


@bot.tree.command(name="virgin", description="Ses kanalına katılıp Virgin Radio'yu çalar")
async def virgin(interaction: discord.Interaction):
    # Kullanıcı bir ses kanalında mı?
    if interaction.user.voice is None or interaction.user.voice.channel is None:
        await interaction.response.send_message(
            "Önce bir ses kanalına katılman lazım.", ephemeral=True
        )
        return

    voice_channel = interaction.user.voice.channel
    guild = interaction.guild

    await interaction.response.defer()

    # Zaten bağlıysa taşı, değilse bağlan
    voice_client = guild.voice_client
    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)

    # Zaten çalıyorsa durdur, yeniden başlat
    if voice_client.is_playing():
        voice_client.stop()

    source = discord.FFmpegPCMAudio(VIRGIN_RADIO_STREAM_URL, **FFMPEG_OPTIONS)
    voice_client.play(source, after=lambda e: print(f"Yayın durdu: {e}" if e else "Yayın bitti."))

    await interaction.followup.send("📻 **Virgin Radio** çalıyor!")


@bot.tree.command(name="stop", description="Yayını durdurur ve ses kanalından ayrılır")
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        await interaction.response.send_message("Zaten bir ses kanalında değilim.", ephemeral=True)
        return

    if voice_client.is_playing():
        voice_client.stop()
    await voice_client.disconnect()
    await interaction.response.send_message("Yayın durduruldu, kanaldan ayrıldım. 👋")


if __name__ == "__main__":
    if TOKEN == "BURAYA_BOT_TOKENINI_YAZ":
        print("UYARI: TOKEN ayarlanmamış. Kod içinden ya da DISCORD_BOT_TOKEN ortam değişkeninden ayarla.")
    bot.run(TOKEN)
