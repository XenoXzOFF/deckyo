import discord
from discord.ext import commands
from discord import app_commands
import os

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]


class Reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="reload",
        description="♻️ Recharge un module ou tous les cogs du bot (développeurs uniquement)"
    )
    @app_commands.describe(module="Le module à recharger (laisser vide pour tous)")
    async def reload(
        self,
        interaction: discord.Interaction,
        module: str = None
    ):
        """Recharge un module spécifique ou tous les modules"""
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message(
                "🚫 Tu n’as pas la permission d’utiliser cette commande.", ephemeral=True
            )
            return

        if module:
            try:
                await self.bot.unload_extension(f"cogs.{module}")
                await self.bot.load_extension(f"cogs.{module}")
                embed = discord.Embed(
                    title="♻️ Module rechargé",
                    description=f"Le module `{module}` a été rechargé avec succès ✅",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
                await interaction.response.send_message(embed=embed)
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Erreur de rechargement",
                    description=f"Impossible de recharger `{module}`.\n**Erreur :** {e}",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
                await interaction.response.send_message(embed=embed)
        else:
            count = 0
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py"):
                    try:
                        await self.bot.reload_extension(f"cogs.{filename[:-3]}")
                        count += 1
                    except Exception as e:
                        print(f"⚠️ Erreur sur {filename}: {e}")

            embed = discord.Embed(
                title="♻️ Rechargement global",
                description=f"Tous les modules ont été rechargés ({count} cogs).",
                color=discord.Color.blurple()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)

    @reload.autocomplete("module")
    async def module_autocomplete(self, interaction: discord.Interaction, current: str):
        cogs = [f[:-3] for f in os.listdir("./cogs") if f.endswith(".py")]
        return [
            app_commands.Choice(name=cog, value=cog)
            for cog in cogs if current.lower() in cog.lower()
        ][:25]  

async def setup(bot):
    await bot.add_cog(Reload(bot))
