import discord
from discord.ext import commands
import datetime
import traceback
import asyncio
import os

LOG_CHANNEL_ID = 1426947585473511546

class FullLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, embed: discord.Embed):
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Salon de logs introuvable : {LOG_CHANNEL_ID}")
            return
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        embed = discord.Embed(
            title="✅ Commande exécutée",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Auteur", value=f"{ctx.author} ({ctx.author.id})", inline=False)
        embed.add_field(name="Commande", value=ctx.command.qualified_name, inline=False)
        embed.add_field(name="Arguments", value=str(ctx.args), inline=False)
        embed.add_field(name="Salon", value=f"{ctx.channel} ({ctx.channel.id})", inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        embed = discord.Embed(
            title="❌ Erreur de commande",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Auteur", value=f"{ctx.author} ({ctx.author.id})", inline=False)
        embed.add_field(name="Commande", value=getattr(ctx.command, "qualified_name", "N/A"), inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
        embed.add_field(
            name="Erreur",
            value="```py\n" + "".join(traceback.format_exception(type(error), error, error.__traceback__)) + "```",
            inline=False
        )
        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            cmd_name = interaction.command.name if interaction.command else "N/A"
            args = {opt["name"]: opt.get("value") for opt in interaction.data.get("options", [])} if interaction.data else {}
            embed = discord.Embed(
                title="✅ Commande slash exécutée",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Auteur", value=f"{interaction.user} ({interaction.user.id})", inline=False)
            embed.add_field(name="Commande", value=cmd_name, inline=False)
            embed.add_field(name="Arguments", value=str(args) if args else "Aucun", inline=False)
            embed.add_field(name="Salon", value=f"{interaction.channel} ({interaction.channel.id})", inline=False)
            embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
            await self.send_log(embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = discord.Embed(title="🤖 Bot ajouté à un serveur", color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Nom du serveur", value=guild.name, inline=False)
        embed.add_field(name="ID du serveur", value=guild.id, inline=False)
        embed.add_field(name="Propriétaire", value=f"{guild.owner} ({guild.owner_id})", inline=False)
        embed.add_field(name="Membres", value=guild.member_count, inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        embed = discord.Embed(title="❌ Bot retiré d'un serveur", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Nom du serveur", value=guild.name, inline=False)
        embed.add_field(name="ID du serveur", value=guild.id, inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if before.status != after.status or before.activity != after.activity:
            embed = discord.Embed(title="🔹 Présence mise à jour", color=discord.Color.purple(), timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Membre", value=f"{after} ({after.id})", inline=False)
            embed.add_field(name="Ancien statut", value=str(before.status), inline=False)
            embed.add_field(name="Nouveau statut", value=str(after.status), inline=False)
            embed.add_field(name="Ancienne activité", value=str(before.activity), inline=False)
            embed.add_field(name="Nouvelle activité", value=str(after.activity), inline=False)
            embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
            await self.send_log(embed)

async def setup(bot):
    await bot.add_cog(FullLogs(bot))
