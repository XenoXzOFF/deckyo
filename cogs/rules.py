import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime

RULES_CHANNEL_ID = int(os.getenv('RULES_CHANNEL_ID'))
RULES_ACCEPTED_ROLE_ID = int(os.getenv('RULES_ACCEPTED_ROLE_ID'))

# Envoyer les règles dans le salon spécifié automatiquement au démarrage du bot et supprimer les anciens messages
# Bouton pour accepter les règles

class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_rules_message(self):
        channel = self.bot.get_channel(RULES_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Salon des règles introuvable : {RULES_CHANNEL_ID}")
            return

        # Supprimer les anciens messages
        try:
            async for message in channel.history(limit=100):
                await message.delete()
        except discord.Forbidden:
            print(f"⚠️ Permissions insuffisantes pour supprimer les messages dans le salon {channel.name}.")
        except Exception as e:
            print(f"⚠️ Erreur lors de la suppression des messages dans le salon {channel.name} : {e}")

        # Créer le bouton
        class AcceptButton(discord.ui.View):
            @discord.ui.button(label="Accepter les règles", style=discord.ButtonStyle.green)
            async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
                role = interaction.guild.get_role(RULES_ACCEPTED_ROLE_ID)
                if role:
                    try:
                        await interaction.user.add_roles(role)
                        await interaction.response.send_message("✅ Vous avez accepté les règles et le rôle vous a été attribué.", ephemeral=True)
                    except discord.Forbidden:
                        await interaction.response.send_message("⚠️ Impossible de vous attribuer le rôle. Permissions insuffisantes.", ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f"⚠️ Erreur lors de l'attribution du rôle : {e}", ephemeral=True)
                else:
                    await interaction.response.send_message("⚠️ Rôle d'acceptation des règles introuvable.", ephemeral=True)

        # Message des règles
        rules_text = (
            "Bienvenue sur le serveur !\n\n"
            "1. Respectez les autres membres.\n"
            "2. Pas de spam ou de publicité.\n"
            "3. Suivez les instructions du staff.\n"
            "4. Utilisez les salons appropriés pour vos discussions.\n"
            "5. Pas de contenu NSFW.\n\n"
            "En cliquant sur le bouton ci-dessous, vous acceptez ces règles."
        )

        embed = discord.Embed(title="Règles du Serveur", description=rules_text, color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
        await channel.send(embed=embed, view=AcceptButton())
        print(f"✅ Message des règles envoyé dans le salon {channel.name}.")

async def setup(bot):
    cog = Rules(bot)
    await bot.add_cog(cog)
    await cog.send_rules_message()