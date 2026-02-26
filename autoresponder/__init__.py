"""
AutoResponder cog for Red-DiscordBot.
Automatically responds to messages containing configured keywords.
"""

from .autoresponder import AutoResponder


async def setup(bot):
    """Load the AutoResponder cog."""
    cog = AutoResponder(bot)
    await bot.add_cog(cog)