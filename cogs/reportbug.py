import discord
from discord import app_commands
from discord.ext import commands
import os
import datetime
import asyncio

# Envoies un rapport de bug dans un salon spécifique
# Envoies un MP à l'utilisateur pour dire que le rapport a bien été envoyé et son état d'avancement (en cours de traitement, traité, non pris en compte, etc.)
# OWNER_IDS uniquement pourra donner son état d'avancement
# Boutons (non des réactions emoji) en dessous du rapport pour que les OWNER_IDS puissent changer l'état d'avancement (en cours de traitement, traité, non pris en compte, etc.)
# Utiliser uniquement des EMBED avancés et pas de message textes
# Le rapport doit contenir le pseudo de l'utilisateur, son ID, la date et l'heure, le serveur d'où provient le rapport, le salon d'où provient le rapport, et le message du rapport
# Afficher l'état d'avancement dans l'embed du rapport

REPORTS_CHANNEL_ID = int(os.getenv('REPORTS_CHANNEL_ID'))
OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
STATUS_OPTIONS = {
    "waiting": ("En attente", discord.Color.greyple()),
    "pending": ("En cours de traitement", discord.Color.orange()),
    "resolved": ("Traité", discord.Color.green()),
    "dismissed": ("Non pris en compte", discord.Color.red())
}
class ReportBug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reportbug", description="Signale un bug ou un problème")
    @app_commands.describe(message="Description du bug ou problème")
    async def reportbug(self, interaction: discord.Interaction, message: str = None):
        if not message:
            await interaction.response.send_message("🚫 Veuillez fournir une description du bug ou problème.", ephemeral=True)
            return

        reports_channel = self.bot.get_channel(REPORTS_CHANNEL_ID)
        if not reports_channel:
            await interaction.response.send_message("⚠️ Le salon de rapport de bugs est introuvable. Veuillez contacter un administrateur.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🐞 Nouveau rapport de bug",
            description=message,
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Utilisateur", value=f"{interaction.user} (ID: {interaction.user.id})", inline=False)
        embed.add_field(name="Serveur", value=f"{interaction.guild.name} (ID: {interaction.guild.id})", inline=False)
        embed.add_field(name="Salon", value=f"{interaction.channel.name} (ID: {interaction.channel.id})", inline=False)
        embed.add_field(name="État", value=STATUS_OPTIONS["waiting"][0], inline=False)
        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)

        class StatusView(discord.ui.View):
            @discord.ui.button(label="En cours de traitement", style=discord.ButtonStyle.secondary, custom_id="status_pending")
            async def pending(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.update_status(interaction_btn, "pending")

            @discord.ui.button(label="Traité", style=discord.ButtonStyle.success, custom_id="status_resolved")
            async def resolved(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.update_status(interaction_btn, "resolved")

            @discord.ui.button(label="Non pris en compte", style=discord.ButtonStyle.danger, custom_id="status_dismissed")
            async def dismissed(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.update_status(interaction_btn, "dismissed")

            async def update_status(self, interaction_btn: discord.Interaction, status_key: str):
                if interaction_btn.user.id not in OWNER_IDS:
                    await interaction_btn.response.send_message("🚫 Tu n’as pas la permission de changer l’état.", ephemeral=True)
                    return

                status_text, status_color = STATUS_OPTIONS[status_key]
                embed.color = status_color
                embed.set_field_at(3, name="État", value=status_text, inline=False)
                await message_report.edit(embed=embed)
                await interaction_btn.response.send_message(f"✅ État mis à jour : {status_text}", ephemeral=True)
                try:
                    await interaction.user.send(f"✅ L'état de votre rapport de bug a été mis à jour : {status_text}")
                except discord.Forbidden:
                    pass  # L'utilisateur a désactivé les MP
        view = StatusView()
        message_report = await reports_channel.send(embed=embed, view=view)
        try:
            await interaction.user.send("✅ Votre rapport de bug a été envoyé avec succès. Merci pour votre contribution !")
            await interaction.response.send_message("✅ Votre rapport de bug a été envoyé avec succès. Un message privé vous a été envoyé.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("✅ Votre rapport de bug a été envoyé avec succès. Cependant, je n'ai pas pu vous envoyer de message privé.", ephemeral=True)
        # Suppression du message de confirmation après 30 secondes
        await asyncio.sleep(30)
        try:
            await interaction.delete_original_response()
        except discord.NotFound:
            pass  # Le message a déjà été supprimé
async def setup(bot):
    await bot.add_cog(ReportBug(bot))