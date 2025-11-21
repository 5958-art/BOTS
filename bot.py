import discord
from discord.ext import commands
import aiosqlite
import re
import os

# Pega as variáveis do Render
TOKEN = os.environ['DISCORD_TOKEN']
CANAL_ID = int(os.environ['CHANNEL_ID'])

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# IDs dos canais onde o bot vai aceitar números
CANAIS_RECRUTAMENTO = [CANAL_ID]

# ============================================
# INICIAR BANCO DE DADOS
# ============================================
@bot.event
async def on_ready():
    async with aiosqlite.connect("recrutamento.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS recrutamentos (
                recrutador_id INTEGER,
                recrutado_id TEXT UNIQUE
            )
        """)
        await db.commit()
    print(f"Bot online como {bot.user}")

# ============================================
# QUANDO A PESSOA ENVIAR UMA MENSAGEM
# ============================================
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.id not in CANAIS_RECRUTAMENTO:
        return

    texto = message.content.strip()

    if not re.fullmatch(r"\d{5,6}", texto):
        return

    recrutado_id = texto

    async with aiosqlite.connect("recrutamento.db") as db:
        cursor = await db.execute(
            "SELECT 1 FROM recrutamentos WHERE recrutado_id = ?",
            (recrutado_id,)
        )
        existe = await cursor.fetchone()

        if existe:
            await message.reply("❌ Esse ID **já está registrado**!")
            return

        await db.execute(
            "INSERT INTO recrutamentos (recrutador_id, recrutado_id) VALUES (?, ?)",
            (message.author.id, recrutado_id)
        )
        await db.commit()

    await message.reply(f"✅ ID `{recrutado_id}` registrado para **{message.author.name}**!")

    await bot.process_commands(message)

# ============================================
# COMANDO PARA VER RANKING
# ============================================
@bot.command()
async def ranking(ctx):
    async with aiosqlite.connect("recrutamento.db") as db:
        cursor = await db.execute("""
            SELECT recrutador_id, COUNT(*)
            FROM recrutamentos
            GROUP BY recrutador_id
            ORDER BY COUNT(*) DESC
        """)
        dados = await cursor.fetchall()

    if not dados:
        return await ctx.send("📉 Ninguém registrou ainda.")

    embed = discord.Embed(
        title="🏆 Ranking de Recrutamento",
        color=discord.Color.gold()
    )

    pos = 1
    for recrutador_id, total in dados:
        membro = ctx.guild.get_member(recrutador_id)
        nome = membro.name if membro else f"{recrutador_id} (saiu do servidor)"
        embed.add_field(
            name=f"{pos}º — {nome}",
            value=f"IDs registrados: **{total}**",
            inline=False
        )
        pos += 1

    await ctx.send(embed=embed)

# ============================================
# INICIAR BOT
# ============================================
bot.run(TOKEN)
