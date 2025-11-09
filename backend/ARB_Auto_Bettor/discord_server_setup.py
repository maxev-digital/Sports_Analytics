"""
Discord Server Setup Script for MAX-EV Sports
Automatically creates all channels, categories, and roles for the community server.
"""

import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))

# Bot setup
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Server structure configuration
SERVER_STRUCTURE = {
    "📋 WELCOME & INFO": {
        "description": "Start here! Welcome to MAX-EV Sports",
        "channels": [
            {"name": "👋welcome", "description": "Welcome to MAX-EV Sports! Read the rules and get started."},
            {"name": "📜rules", "description": "Server rules and community guidelines."},
            {"name": "📢announcements", "description": "Official announcements from MAX-EV Sports team."},
            {"name": "🎯start-here", "description": "New? Start here! Setup guide and quick start."},
            {"name": "🔗links", "description": "Important links: Website, Chrome Extension, Guides."}
        ]
    },
    "🚨 LIVE ALERTS": {
        "description": "Real-time betting opportunities",
        "channels": [
            {"name": "🟢arb-alerts", "description": "Real-time arbitrage opportunities (2-5% risk-free)."},
            {"name": "🔵middle-alerts", "description": "Middle opportunities - bet both sides with a gap."},
            {"name": "🟠steam-alerts", "description": "Sharp money detection - follow the pros."},
            {"name": "🔴goalie-pull-alerts", "description": "NHL empty net betting alerts (8-12% edge)."},
            {"name": "⚡live-steam", "description": "Live line movements and steam detection."},
            {"name": "🎰ev-plays", "description": "Positive expected value betting opportunities."}
        ]
    },
    "🏀 NBA": {
        "description": "NBA discussion and analysis",
        "channels": [
            {"name": "💬nba-general", "description": "General NBA discussion and questions."},
            {"name": "📊nba-predictions", "description": "Daily NBA totals predictions and analysis."},
            {"name": "📈nba-lines", "description": "NBA line discussions and movements."},
            {"name": "🔥nba-picks", "description": "Share your NBA picks and analysis."}
        ]
    },
    "🏈 NFL": {
        "description": "NFL discussion and analysis",
        "channels": [
            {"name": "💬nfl-general", "description": "General NFL discussion and questions."},
            {"name": "📊nfl-predictions", "description": "NFL game predictions and analysis."},
            {"name": "📈nfl-lines", "description": "NFL line discussions and movements."},
            {"name": "🔥nfl-picks", "description": "Share your NFL picks and analysis."}
        ]
    },
    "🏒 NHL": {
        "description": "NHL discussion and analysis",
        "channels": [
            {"name": "💬nhl-general", "description": "General NHL discussion and questions."},
            {"name": "📊nhl-predictions", "description": "NHL game predictions and analysis."},
            {"name": "🥅goalie-pulls", "description": "NHL goalie pull strategy and discussion."},
            {"name": "🔥nhl-picks", "description": "Share your NHL picks and analysis."}
        ]
    },
    "⚾ MLB": {
        "description": "MLB discussion and analysis",
        "channels": [
            {"name": "💬mlb-general", "description": "General MLB discussion and questions."},
            {"name": "📊mlb-predictions", "description": "MLB game predictions and analysis."},
            {"name": "🔥mlb-picks", "description": "Share your MLB picks and analysis."}
        ]
    },
    "🏀 COLLEGE BASKETBALL": {
        "description": "NCAA Basketball discussion",
        "channels": [
            {"name": "💬ncaab-general", "description": "General college basketball discussion."},
            {"name": "📊ncaab-predictions", "description": "NCAA Basketball totals predictions."},
            {"name": "🔥ncaab-picks", "description": "Share your college basketball picks."}
        ]
    },
    "⚽ OTHER SPORTS": {
        "description": "Soccer, Tennis, MMA, and more",
        "channels": [
            {"name": "⚽soccer", "description": "Soccer betting discussion."},
            {"name": "🥊mma-boxing", "description": "MMA and Boxing betting."},
            {"name": "🎾tennis", "description": "Tennis betting discussion."},
            {"name": "🏌️other-sports", "description": "Golf, NASCAR, eSports, and more."}
        ]
    },
    "📊 ANALYTICS & TOOLS": {
        "description": "Data, models, and tools",
        "channels": [
            {"name": "📈analytics", "description": "Advanced analytics and statistical discussion."},
            {"name": "🤖bot-commands", "description": "Bot commands and automated tools."},
            {"name": "💻chrome-extension", "description": "Chrome Extension support and discussion."},
            {"name": "📱platform-help", "description": "MAX-EV Sports platform help and tips."},
            {"name": "🔬backtesting", "description": "Model backtesting and performance analysis."}
        ]
    },
    "🎓 EDUCATION": {
        "description": "Learn betting strategies",
        "channels": [
            {"name": "📚strategies", "description": "Betting strategies and education."},
            {"name": "📖glossary", "description": "Betting terms and definitions."},
            {"name": "❓faqs", "description": "Frequently asked questions."},
            {"name": "🎥tutorials", "description": "Video tutorials and guides."},
            {"name": "📝bankroll-mgmt", "description": "Bankroll management and staking strategies."}
        ]
    },
    "💬 COMMUNITY": {
        "description": "General community chat",
        "channels": [
            {"name": "💬general-chat", "description": "General discussion - anything goes!"},
            {"name": "🎉wins", "description": "Share your winning bets! 🤑"},
            {"name": "😭bad-beats", "description": "Share your losses and bad beats."},
            {"name": "😂memes", "description": "Sports betting memes and humor."},
            {"name": "📸screenshots", "description": "Share bet screenshots and slips."},
            {"name": "🎮off-topic", "description": "Non-sports betting chat."}
        ]
    },
    "🛠️ SUPPORT": {
        "description": "Get help and give feedback",
        "channels": [
            {"name": "🆘support", "description": "Need help? Ask here! Response within 24 hours."},
            {"name": "💡feedback", "description": "Feature requests and feedback."},
            {"name": "🐛bug-reports", "description": "Report bugs and issues."},
            {"name": "📋changelog", "description": "Platform updates and new features."}
        ]
    }
}

# Roles configuration
ROLES_CONFIG = [
    {"name": "👑 Admin", "color": discord.Color.red(), "permissions": discord.Permissions.all()},
    {"name": "🛡️ Moderator", "color": discord.Color.blue(), "permissions": discord.Permissions(
        kick_members=True, ban_members=True, manage_messages=True, mute_members=True
    )},
    {"name": "💎 Premium", "color": discord.Color.gold(), "hoist": True},
    {"name": "📊 Analytics Pro", "color": discord.Color.purple(), "hoist": True},
    {"name": "🎯 Active Bettor", "color": discord.Color.green(), "hoist": True},
    {"name": "📱 Extension User", "color": discord.Color.teal(), "hoist": False},
    {"name": "🆕 New Member", "color": discord.Color.light_gray(), "hoist": False}
]

@bot.event
async def on_ready():
    print(f'\n✅ Bot logged in as {bot.user.name}')
    print(f'🔗 Connected to Discord API')

    # Get the guild
    guild = bot.get_guild(DISCORD_GUILD_ID)
    if not guild:
        print(f'❌ Error: Could not find guild with ID {DISCORD_GUILD_ID}')
        await bot.close()
        return

    print(f'🏠 Setting up server: {guild.name}')
    print(f'👥 Current member count: {guild.member_count}\n')

    try:
        # Step 1: Create roles
        print('=' * 60)
        print('STEP 1: Creating Roles')
        print('=' * 60)
        await create_roles(guild)

        # Step 2: Create categories and channels
        print('\n' + '=' * 60)
        print('STEP 2: Creating Categories and Channels')
        print('=' * 60)
        await create_server_structure(guild)

        # Step 3: Set up welcome message
        print('\n' + '=' * 60)
        print('STEP 3: Creating Welcome Message')
        print('=' * 60)
        await setup_welcome_message(guild)

        print('\n' + '=' * 60)
        print('✅ SERVER SETUP COMPLETE!')
        print('=' * 60)
        print('\n📋 Summary:')
        print(f'  ✅ {len(ROLES_CONFIG)} roles created')
        print(f'  ✅ {len(SERVER_STRUCTURE)} categories created')
        total_channels = sum(len(cat["channels"]) for cat in SERVER_STRUCTURE.values())
        print(f'  ✅ {total_channels} channels created')
        print('\n🎉 Your Discord server is ready!')
        print('📝 Next steps:')
        print('  1. Customize welcome message in #welcome')
        print('  2. Set up auto-moderator rules')
        print('  3. Configure role permissions as needed')
        print('  4. Add channel icons and banners')
        print('\n🛑 Closing bot...')

    except Exception as e:
        print(f'\n❌ Error during setup: {e}')
        import traceback
        traceback.print_exc()

    await bot.close()

async def create_roles(guild):
    """Create all member roles"""
    existing_roles = {role.name: role for role in guild.roles}

    for role_config in ROLES_CONFIG:
        role_name = role_config['name']

        if role_name in existing_roles:
            print(f'  ⏭️  Role already exists: {role_name}')
            continue

        try:
            permissions = role_config.get('permissions', discord.Permissions.none())
            color = role_config.get('color', discord.Color.default())
            hoist = role_config.get('hoist', False)

            await guild.create_role(
                name=role_name,
                color=color,
                permissions=permissions,
                hoist=hoist,
                mentionable=True
            )
            print(f'  ✅ Created role: {role_name}')
            await asyncio.sleep(0.5)  # Rate limit protection

        except Exception as e:
            print(f'  ❌ Failed to create role {role_name}: {e}')

async def create_server_structure(guild):
    """Create all categories and channels"""
    existing_categories = {cat.name: cat for cat in guild.categories}

    for category_name, category_data in SERVER_STRUCTURE.items():
        # Create or get category
        if category_name in existing_categories:
            print(f'\n📁 Category already exists: {category_name}')
            category = existing_categories[category_name]
        else:
            try:
                category = await guild.create_category(category_name)
                print(f'\n✅ Created category: {category_name}')
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f'❌ Failed to create category {category_name}: {e}')
                continue

        # Create channels in this category
        existing_channels = {ch.name: ch for ch in category.channels}

        for channel_config in category_data['channels']:
            channel_name = channel_config['name']
            channel_topic = channel_config.get('description', '')

            if channel_name in existing_channels:
                print(f'  ⏭️  Channel already exists: {channel_name}')
                continue

            try:
                await guild.create_text_channel(
                    name=channel_name,
                    category=category,
                    topic=channel_topic
                )
                print(f'  ✅ Created channel: {channel_name}')
                await asyncio.sleep(0.5)  # Rate limit protection

            except Exception as e:
                print(f'  ❌ Failed to create channel {channel_name}: {e}')

async def setup_welcome_message(guild):
    """Create a welcome message in the welcome channel"""
    # Find the welcome channel
    welcome_channel = discord.utils.get(guild.text_channels, name='👋welcome')

    if not welcome_channel:
        print('  ⚠️  Welcome channel not found, skipping welcome message')
        return

    # Check if messages already exist
    messages = [msg async for msg in welcome_channel.history(limit=5)]
    if messages:
        print('  ⏭️  Welcome channel already has messages, skipping')
        return

    welcome_embed = discord.Embed(
        title="👋 Welcome to MAX-EV Sports!",
        description=(
            "**The #1 Community for Professional Sports Betting Analytics**\n\n"
            "We help you find profitable betting opportunities using:\n"
            "🟢 Arbitrage (risk-free profits)\n"
            "🔵 Middles (bet both sides)\n"
            "🟠 Steam Moves (sharp money)\n"
            "🔴 Goalie Pulls (8-12% edge)\n\n"
            "**Get Started:**\n"
            "1️⃣ Read the rules in <#rules>\n"
            "2️⃣ Check out <#start-here> for setup guide\n"
            "3️⃣ Install our Chrome Extension from <#links>\n"
            "4️⃣ Join the discussion and start winning!\n\n"
            "**Important Links:**\n"
            "🌐 Website: https://www.max-ev-sports.com/\n"
            "📧 Support: support@max-ev-sports.com\n"
            "📖 Installation Guide: Check <#links>\n\n"
            "**Let's find profitable opportunities together! 🚀**"
        ),
        color=discord.Color.green()
    )

    welcome_embed.set_footer(text="MAX-EV Sports | Professional Sports Betting Analytics")

    try:
        await welcome_channel.send(embed=welcome_embed)
        print('  ✅ Created welcome message')
    except Exception as e:
        print(f'  ❌ Failed to create welcome message: {e}')

def main():
    """Main entry point"""
    print('\n' + '=' * 60)
    print('MAX-EV SPORTS - DISCORD SERVER SETUP')
    print('=' * 60)

    # Validate environment variables
    if not DISCORD_BOT_TOKEN:
        print('❌ Error: DISCORD_BOT_TOKEN not found in .env file')
        print('📝 Please create a .env file with your bot token')
        print('   Example: DISCORD_BOT_TOKEN=your_token_here')
        return

    if not DISCORD_GUILD_ID:
        print('❌ Error: DISCORD_GUILD_ID not found in .env file')
        print('📝 Please add your server ID to .env file')
        print('   Example: DISCORD_GUILD_ID=123456789012345678')
        return

    print('\n🤖 Starting bot...')
    print('⏳ This may take 1-2 minutes depending on server size...\n')

    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.errors.LoginFailure:
        print('\n❌ Error: Invalid bot token')
        print('📝 Please check your DISCORD_BOT_TOKEN in .env file')
    except Exception as e:
        print(f'\n❌ Unexpected error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
