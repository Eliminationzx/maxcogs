"""
AutoResponder cog for Red-DiscordBot.
Automatically responds to messages containing configured keywords.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

import discord
from discord.utils import escape_mentions
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, pagify

log = logging.getLogger("red.autoresponder")


class AutoResponder(commands.Cog):
    """Auto responder for keyword-based automatic responses."""

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9876543210, force_registration=True)
        
        # Define default schema
        default_global = {
            "triggers": {}
        }
        
        self.config.register_global(**default_global)
        
        # In-memory cache for cooldowns: {channel_id: {trigger_name: last_trigger_time}}
        self.cooldowns: Dict[int, Dict[str, datetime]] = {}
        # Cache for triggers to reduce database reads
        self._triggers_cache: Optional[Dict[str, Dict[str, Any]]] = None
        
        log.debug("AutoResponder cog initialized")

    # Cache management
    def _invalidate_triggers_cache(self) -> None:
        """Invalidate the triggers cache."""
        self._triggers_cache = None
        log.debug("Triggers cache invalidated")

    async def _get_triggers_cached(self) -> Dict[str, Dict[str, Any]]:
        """Get all triggers, using cache if possible."""
        if self._triggers_cache is None:
            self._triggers_cache = await self.config.triggers()
            log.debug("Triggers cache populated")
        return self._triggers_cache

    # Helper methods for trigger management
    async def _get_trigger(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a trigger by name."""
        triggers = await self._get_triggers_cached()
        return triggers.get(name.lower())

    async def _save_trigger(self, name: str, trigger_data: Dict[str, Any]) -> None:
        """Save a trigger."""
        name = name.lower()
        async with self.config.triggers() as triggers:
            triggers[name] = trigger_data
        self._invalidate_triggers_cache()

    async def _delete_trigger(self, name: str) -> bool:
        """Delete a trigger."""
        name = name.lower()
        async with self.config.triggers() as triggers:
            if name in triggers:
                del triggers[name]
                self._invalidate_triggers_cache()
                return True
        return False

    async def _get_all_triggers(self) -> Dict[str, Dict[str, Any]]:
        """Get all triggers."""
        return await self._get_triggers_cached()

    # Command group
    @commands.group(name="autoresponder", aliases=["ar"])
    @checks.admin_or_permissions(manage_guild=True)
    async def autoresponder(self, ctx: commands.Context) -> None:
        """Manage auto responder triggers."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @autoresponder.command(name="add")
    async def autoresponder_add(self, ctx: commands.Context, name: str) -> None:
        """Add a new trigger."""
        name = name.lower()
        
        if await self._get_trigger(name):
            await ctx.send(f"Trigger `{name}` already exists.")
            return
        
        trigger_data = {
            "keywords": [],
            "responses": [],
            "cooldown": 60,  # Default cooldown in seconds
            "enabled": True
        }
        
        await self._save_trigger(name, trigger_data)
        await ctx.send(f"Trigger `{name}` created successfully.")

    @autoresponder.command(name="addkeyword")
    async def autoresponder_addkeyword(self, ctx: commands.Context, name: str, *, keyword: str) -> None:
        """Add a keyword to a trigger."""
        trigger = await self._get_trigger(name)
        if not trigger:
            await ctx.send(f"Trigger `{name}` not found.")
            return
        
        keyword = keyword.strip()
        if not keyword:
            await ctx.send("Keyword cannot be empty.")
            return
        
        keyword_lower = keyword.lower()
        # Check for duplicates case-insensitively
        if any(k.lower() == keyword_lower for k in trigger["keywords"]):
            await ctx.send(f"Keyword `{keyword}` already exists for trigger `{name}`.")
            return
        
        trigger["keywords"].append(keyword_lower)
        await self._save_trigger(name, trigger)
        await ctx.send(f"Keyword `{keyword}` added to trigger `{name}` (stored as lowercase).")

    @autoresponder.command(name="addresponse")
    async def autoresponder_addresponse(self, ctx: commands.Context, name: str, *, response: str) -> None:
        """Add a response to a trigger."""
        trigger = await self._get_trigger(name)
        if not trigger:
            await ctx.send(f"Trigger `{name}` not found.")
            return
        
        response = response.strip()
        if not response:
            await ctx.send("Response cannot be empty.")
            return
        
        trigger["responses"].append(response)
        await self._save_trigger(name, trigger)
        await ctx.send(f"Response added to trigger `{name}`.")

    @autoresponder.command(name="remove")
    async def autoresponder_remove(self, ctx: commands.Context, name: str) -> None:
        """Remove a trigger."""
        if not await self._delete_trigger(name):
            await ctx.send(f"Trigger `{name}` not found.")
            return
        
        await ctx.send(f"Trigger `{name}` removed successfully.")

    @autoresponder.command(name="list")
    async def autoresponder_list(self, ctx: commands.Context) -> None:
        """List all triggers."""
        triggers = await self._get_all_triggers()
        
        if not triggers:
            await ctx.send("No triggers configured.")
            return
        
        lines = []
        for name, data in sorted(triggers.items()):
            keywords = len(data["keywords"])
            responses = len(data["responses"])
            cooldown = data["cooldown"]
            enabled = "✓" if data["enabled"] else "✗"
            lines.append(f"{enabled} **{name}**: {keywords} keywords, {responses} responses, {cooldown}s cooldown")
        
        message = "\n".join(lines)
        for page in pagify(message):
            await ctx.send(page)

    @autoresponder.command(name="cooldown")
    async def autoresponder_cooldown(self, ctx: commands.Context, name: str, seconds: int) -> None:
        """Set cooldown for a trigger in seconds."""
        trigger = await self._get_trigger(name)
        if not trigger:
            await ctx.send(f"Trigger `{name}` not found.")
            return
        
        if seconds < 0:
            await ctx.send("Cooldown cannot be negative.")
            return
        
        trigger["cooldown"] = seconds
        await self._save_trigger(name, trigger)
        await ctx.send(f"Cooldown for trigger `{name}` set to {seconds} seconds.")

    @autoresponder.command(name="enable")
    async def autoresponder_enable(self, ctx: commands.Context, name: str) -> None:
        """Enable a trigger."""
        trigger = await self._get_trigger(name)
        if not trigger:
            await ctx.send(f"Trigger `{name}` not found.")
            return
        
        if trigger["enabled"]:
            await ctx.send(f"Trigger `{name}` is already enabled.")
            return
        
        trigger["enabled"] = True
        await self._save_trigger(name, trigger)
        await ctx.send(f"Trigger `{name}` enabled.")

    @autoresponder.command(name="disable")
    async def autoresponder_disable(self, ctx: commands.Context, name: str) -> None:
        """Disable a trigger."""
        trigger = await self._get_trigger(name)
        if not trigger:
            await ctx.send(f"Trigger `{name}` not found.")
            return
        
        if not trigger["enabled"]:
            await ctx.send(f"Trigger `{name}` is already disabled.")
            return
        
        trigger["enabled"] = False
        await self._save_trigger(name, trigger)
        await ctx.send(f"Trigger `{name}` disabled.")

    @autoresponder.command(name="show")
    async def autoresponder_show(self, ctx: commands.Context, name: str) -> None:
        """Show details of a trigger."""
        trigger = await self._get_trigger(name)
        if not trigger:
            await ctx.send(f"Trigger `{name}` not found.")
            return
        
        keywords = trigger["keywords"]
        responses = trigger["responses"]
        cooldown = trigger["cooldown"]
        enabled = "Enabled" if trigger["enabled"] else "Disabled"
        
        message = (
            f"**Trigger: {name}**\n"
            f"Status: {enabled}\n"
            f"Cooldown: {cooldown} seconds\n\n"
            f"**Keywords ({len(keywords)}):**\n"
        )
        
        if keywords:
            message += "\n".join(f"- `{k}`" for k in keywords)
        else:
            message += "No keywords configured."
        
        message += f"\n\n**Responses ({len(responses)}):**\n"
        if responses:
            for i, r in enumerate(responses, 1):
                message += f"{i}. {r}\n"
        else:
            message += "No responses configured."
        
        for page in pagify(message):
            await ctx.send(page)

    @autoresponder.command(name="removekeyword")
    async def autoresponder_removekeyword(self, ctx: commands.Context, name: str, *, keyword: str) -> None:
        """Remove a keyword from a trigger."""
        trigger = await self._get_trigger(name)
        if not trigger:
            await ctx.send(f"Trigger `{name}` not found.")
            return
        
        keyword = keyword.strip().lower()
        if keyword not in trigger["keywords"]:
            # Show the original user input (before lowercasing) in error message
            await ctx.send(f"Keyword `{keyword}` not found in trigger `{name}`.")
            return
        
        trigger["keywords"].remove(keyword)
        await self._save_trigger(name, trigger)
        await ctx.send(f"Keyword `{keyword}` removed from trigger `{name}`.")

    @autoresponder.command(name="removeresponse")
    async def autoresponder_removeresponse(self, ctx: commands.Context, name: str, index: int) -> None:
        """Remove a response from a trigger by index (use [p]autoresponder show to see indices)."""
        trigger = await self._get_trigger(name)
        if not trigger:
            await ctx.send(f"Trigger `{name}` not found.")
            return
        
        if index < 1 or index > len(trigger["responses"]):
            await ctx.send(f"Invalid index. Use a number between 1 and {len(trigger['responses'])}.")
            return
        
        removed = trigger["responses"].pop(index - 1)
        await self._save_trigger(name, trigger)
        await ctx.send(f"Response removed from trigger `{name}`: `{removed}`")

    # Event listener
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Listen for messages and respond to triggers."""
        # Ignore bot messages and DMs
        if message.author.bot:
            return
        if not message.guild:
            return
        
        # Ignore empty messages
        if not message.content:
            return
        
        content_lower = message.content.lower()
        channel_id = message.channel.id
        
        # Get all triggers
        triggers = await self._get_all_triggers()
        
        for trigger_name, trigger_data in triggers.items():
            # Skip disabled triggers
            if not trigger_data["enabled"]:
                log.debug(f"Trigger '{trigger_name}' is disabled, skipping")
                continue
            
            # Check cooldown
            if self._is_on_cooldown(channel_id, trigger_name, trigger_data["cooldown"]):
                log.debug(f"Trigger '{trigger_name}' is on cooldown in channel {channel_id}")
                continue
            
            # Check if any keyword matches
            if not self._matches_keywords(content_lower, trigger_data["keywords"]):
                continue
            
            # Get a random response if available
            responses = trigger_data["responses"]
            if not responses:
                log.debug(f"Trigger '{trigger_name}' has no responses, skipping")
                continue
            
            # Select random response
            response = random.choice(responses)
            log.debug(f"Trigger '{trigger_name}' matched, selected response: {response[:50]}...")
            
            try:
                await message.channel.send(escape_mentions(response))
                log.debug(f"Trigger '{trigger_name}' fired in channel {channel_id}")
                
                # Update cooldown
                self._update_cooldown(channel_id, trigger_name)
                
                # Only respond with one trigger per message
                break
            except discord.Forbidden:
                log.warning(f"No permission to send messages in channel {channel_id}")
            except discord.HTTPException as e:
                log.error(f"Failed to send message: {e}")

    def _matches_keywords(self, content: str, keywords: List[str]) -> bool:
        """Check if content matches any keyword (case-insensitive substring)."""
        for keyword in keywords:
            if keyword.lower() in content:
                return True
        return False

    def _is_on_cooldown(self, channel_id: int, trigger_name: str, cooldown_seconds: int) -> bool:
        """Check if a trigger is on cooldown for a channel."""
        if channel_id not in self.cooldowns:
            return False
        
        channel_cooldowns = self.cooldowns[channel_id]
        if trigger_name not in channel_cooldowns:
            return False
        
        last_trigger = channel_cooldowns[trigger_name]
        cooldown_end = last_trigger + timedelta(seconds=cooldown_seconds)
        
        return datetime.utcnow() < cooldown_end

    def _update_cooldown(self, channel_id: int, trigger_name: str) -> None:
        """Update cooldown timestamp for a trigger in a channel."""
        if channel_id not in self.cooldowns:
            self.cooldowns[channel_id] = {}
        
        self.cooldowns[channel_id][trigger_name] = datetime.utcnow()
        log.debug(f"Cooldown updated for trigger '{trigger_name}' in channel {channel_id}")

    # Cleanup on cog unload
    def cog_unload(self) -> None:
        """Clean up on cog unload."""
        # Clear in-memory caches
        self.cooldowns.clear()
        self._invalidate_triggers_cache()
        log.debug("AutoResponder cog unloaded - caches cleared")