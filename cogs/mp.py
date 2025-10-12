import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
import os

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]

PRESET_MESSAGES = {
    "maj": {
        "title": "📢 Mise à jour importante du bot",
        "description": (
            "Une mise à jour importante du bot vient d'être effectuée.\n\n"
            "⚠️ **Information importante** : Si vous aviez un ticket ouvert, "
            "celui-ci a été fermé. Merci de réouvrir un nouveau ticket si besoin."
        ),
        "color": discord.Color.blue()
    },
    "maintenance": {
        "title": "🔧 Maintenance prévue",
        "description": (
            "Une maintenance du bot est prévue prochainement.\n"
            "Le système de ticket sera temporairement indisponible pendant cette période."
        ),
        "color": discord.Color.orange()
    },
    "nouveaute": {
        "title": "✨ Nouvelles fonctionnalités",
        "description": (
            "De nouvelles fonctionnalités ont été ajoutées au bot !\n"
            "N'hésitez pas à ouvrir un ticket pour les découvrir et poser vos questions.\n"
            "Vous pouvez aller voir les nouveautés avec la commande `/changelog`."
        ),
        "color": discord.Color.green()
    }
}

class MaJ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="mp",
        description="Envoie un message prédéfini aux propriétaires des serveurs"
    )
    @app_commands.choices(
        type_message=[
            app_commands.Choice(name="Mise à jour", value="maj"),
            app_commands.Choice(name="Maintenance", value="maintenance"),
            app_commands.Choice(name="Nouveautés", value="nouveaute")
        ]
    )
    @app_commands.check(lambda interaction: interaction.user.id in OWNER_IDS)
    async def mp(
        self, 
        interaction: discord.Interaction, 
        type_message: str
    ):
        await interaction.response.defer(ephemeral=True)
        
        sent_count = 0
        failed_count = 0
        processed_owners = set()

        message_template = PRESET_MESSAGES[type_message]
        embed = discord.Embed(
            title=message_template["title"],
            description=message_template["description"],
            color=message_template["color"],
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")

        progress_msg = await interaction.followup.send(
            "⏳ Envoi des messages aux propriétaires en cours...\n⚠️ Délai de 25 secondes entre chaque envoi", 
            ephemeral=True
        )

        for guild in self.bot.guilds:
            owner = guild.owner
            if owner and owner.id not in processed_owners and not owner.bot:
                processed_owners.add(owner.id)
                try:
                    dm_channel = await owner.create_dm()
                    await dm_channel.send(embed=embed)
                    sent_count += 1
                    
                    await progress_msg.edit(
                        content=(
                            f"⏳ Envoi en cours... ({sent_count} messages envoyés)\n"
                            f"⏰ Attente de 25 secondes avant le prochain envoi...\n"
                            f"📊 Progression : {sent_count}/{len(self.bot.guilds)} serveurs"
                        )
                    )
                    
                    await asyncio.sleep(25)
                except (discord.Forbidden, discord.HTTPException):
                    failed_count += 1
                    continue

        summary = (
            f"✅ Messages envoyés avec succès !\n"
            f"📨 Messages envoyés : {sent_count}\n"
            f"❌ Échecs : {failed_count}\n"
            f"👥 Propriétaires contactés : {len(processed_owners)}\n"
            f"📝 Type de message : {type_message}\n"
            f"⏱️ Temps total : ~{sent_count * 25} secondes"
        )
        
        await progress_msg.edit(content=summary)

    @app_commands.command(
        name="majmp",
        description="[Déprécié] Utilisez /mp à la place"
    )
    @app_commands.check(lambda interaction: interaction.user.id in OWNER_IDS)
    async def majmp(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "⚠️ Cette commande est dépréciée. Utilisez `/mp` à la place !",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(MaJ(bot))