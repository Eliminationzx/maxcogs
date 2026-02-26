# AutoResponder Cog

Keyword-based automatic message responses with cooldown management.

## Overview

The AutoResponder cog allows server administrators to set up triggers that automatically respond to messages containing specific keywords. Each trigger can have multiple keywords and multiple possible responses (selected randomly). Triggers can be enabled/disabled individually and have configurable cooldowns per channel.

## Installation

1. Add the maxcogs repository if you haven't already:
   ```
   [p]repo add maxcogs https://github.com/ltzmax/maxcogs
   ```

2. Install the autoresponder cog:
   ```
   [p]cog install maxcogs autoresponder
   ```

3. Load the cog:
   ```
   [p]load autoresponder
   ```

## Commands

All commands require **Manage Server** permission or higher.

### `[p]autoresponder` / `[p]ar`
Base command group. Use `[p]autoresponder` to see all subcommands.

### `[p]autoresponder add <name>`
Create a new trigger with the given name.
- Example: `[p]autoresponder add welcome`

### `[p]autoresponder addkeyword <name> <keyword>`
Add a keyword to a trigger. The trigger will fire when any of its keywords appear in a message (case-insensitive).
- Example: `[p]autoresponder addkeyword welcome hello`

### `[p]autoresponder addresponse <name> <response>`
Add a response to a trigger. When the trigger fires, one of its responses is chosen randomly.
- Example: `[p]autoresponder addresponse welcome "Hello there!"`

### `[p]autoresponder remove <name>`
Delete a trigger entirely.
- Example: `[p]autoresponder remove welcome`

### `[p]autoresponder list`
List all triggers with their keywords, response count, cooldown, and status.

### `[p]autoresponder show <name>`
Show detailed information about a specific trigger.

### `[p]autoresponder cooldown <name> <seconds>`
Set the cooldown for a trigger (in seconds). After a trigger fires in a channel, it won't fire again in the same channel until the cooldown expires.
- Example: `[p]autoresponder cooldown welcome 300` (5 minutes)

### `[p]autoresponder enable <name>`
Enable a trigger (triggers are enabled by default when created).

### `[p]autoresponder disable <name>`
Disable a trigger (stops it from firing).

### `[p]autoresponder removekeyword <name> <keyword>`
Remove a keyword from a trigger.
- Example: `[p]autoresponder removekeyword welcome hi`

### `[p]autoresponder removeresponse <name> <index>`
Remove a response by its index (use `[p]autoresponder show` to see indices).
- Example: `[p]autoresponder removeresponse welcome 2`

## Configuration Examples

### Basic Welcome Trigger
```
[p]autoresponder add welcome
[p]autoresponder addkeyword welcome hello
[p]autoresponder addkeyword welcome hi
[p]autoresponder addresponse welcome "Hey there! Welcome to the server!"
[p]autoresponder addresponse welcome "Hello! How can I help you?"
[p]autoresponder cooldown welcome 60
```

### FAQ Trigger
```
[p]autoresponder add faq
[p]autoresponder addkeyword faq "how do I"
[p]autoresponder addkeyword faq "where can I"
[p]autoresponder addresponse faq "Please check the #faq channel for answers."
[p]autoresponder addresponse faq "Our FAQ is available at https://example.com/faq"
[p]autoresponder cooldown faq 30
```

### Rule Reminder
```
[p]autoresponder add rules
[p]autoresponder addkeyword rules "what are the rules"
[p]autoresponder addresponse rules "Please read the rules in #rules before participating."
```

## Features

- **Multiple keywords per trigger**: A trigger can have any number of keywords; if any keyword matches, the trigger fires.
- **Multiple responses**: Each trigger can have multiple responses; one is chosen randomly each time.
- **Per‑channel cooldowns**: Each trigger has a configurable cooldown that applies separately per channel.
- **Enable/disable toggle**: Triggers can be temporarily disabled without deleting them.
- **Safe mentions**: All responses are automatically sanitized to prevent accidental mention spam.
- **Efficient caching**: Triggers are cached to reduce database reads.
- **Clean unload**: Cooldown cache is cleared when the cog is unloaded.

## Notes

- Triggers are global (not per‑server) because the cog uses a global Config identifier. However, you can create server‑specific triggers by including the server ID in the trigger name.
- The cooldown is tracked per channel, not per user.
- Keywords are matched case‑insensitively and as substrings (e.g., `hello` matches `Hello, world!`).
- Responses are automatically escaped to prevent unintended mentions (`@everyone`, `@here`, user/role mentions).

## Support

If you encounter any issues or have questions, visit the [Cog Support server](https://discord.gg/GET4DVk) and go to the #maxcogs channel.