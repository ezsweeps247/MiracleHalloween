import os
import sqlite3
import random
import pandas as pd
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

BOT_NAME = "Bot B"
DB_NAME = "winners_b.db"
CSV_FILE = "codes_part2.csv"

admin_id_str = os.environ.get('ADMIN_USER_ID', '0')
try:
    ADMIN_USER_ID = int(admin_id_str)
except ValueError:
    print(f"⚠️ Warning: ADMIN_USER_ID '{admin_id_str}' is not a valid numeric ID. Admin commands will be disabled.")
    ADMIN_USER_ID = 0

REQUIRED_CHANNELS = os.environ.get('REQUIRED_CHANNELS_B', '')

PORT = int(os.environ.get('PORT', 8443))
DOMAIN = os.environ.get('DOMAIN', '')

PRIZES = [
    {"tier": "Large", "message_template": "🎃 Whoa! You just unlocked Large Candy! CODE: {code}", "probability": 0.20},
    {"tier": "Medium", "message_template": "🍭 Half Spooky, Half Sweet – perfect for the Medium Candy! CODE: {code}", "probability": 0.30},
    {"tier": "Small", "message_template": "🍬 Only the Small Candy left... lucky you! CODE: {code}", "probability": 0.50}
]

def init_database():
    """Initialize SQLite database with codes and winners tables"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            tier TEXT NOT NULL,
            is_used INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS winners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            username TEXT,
            prize_tier TEXT NOT NULL,
            code TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ {BOT_NAME} database initialized successfully")

def load_codes_from_csv():
    """Load codes from CSV file into database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM codes')
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"ℹ️ {BOT_NAME} codes already exist in database ({count} codes)")
        conn.close()
        return
    
    print(f"🔄 {BOT_NAME} loading codes from {CSV_FILE}...")
    
    df = pd.read_csv(CSV_FILE)
    
    codes_to_insert = []
    for _, row in df.iterrows():
        codes_to_insert.append((row['Code'], row['Prize'], 0))
    
    cursor.executemany('INSERT INTO codes (code, tier, is_used) VALUES (?, ?, ?)', codes_to_insert)
    conn.commit()
    
    large_count = len(df[df['Prize'] == 'Large'])
    medium_count = len(df[df['Prize'] == 'Medium'])
    small_count = len(df[df['Prize'] == 'Small'])
    
    conn.close()
    print(f"✅ {BOT_NAME} loaded {len(df)} codes ({large_count} Large, {medium_count} Medium, {small_count} Small)")

def get_unused_code(tier: str):
    """Get an unused code for the specified tier"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT code FROM codes WHERE tier = ? AND is_used = 0 LIMIT 1',
        (tier,)
    )
    result = cursor.fetchone()
    
    if result:
        code = result[0]
        cursor.execute('UPDATE codes SET is_used = 1 WHERE code = ?', (code,))
        conn.commit()
        conn.close()
        return code
    
    conn.close()
    return None

def has_user_won(user_id: int) -> bool:
    """Check if user has already won a prize"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM winners WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_winner(user_id: int, username: str, prize_tier: str, code: str):
    """Add winner to database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        'INSERT INTO winners (user_id, username, prize_tier, code, date) VALUES (?, ?, ?, ?, ?)',
        (user_id, username, prize_tier, code, date)
    )
    conn.commit()
    conn.close()

def get_random_prize():
    """Select a random prize based on probability distribution"""
    rand = random.random()
    cumulative = 0
    for prize in PRIZES:
        cumulative += prize["probability"]
        if rand <= cumulative:
            return prize
    return PRIZES[-1]

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, str]:
    """Check if user is a member of at least one required channel"""
    if not REQUIRED_CHANNELS:
        return True, ""
    
    channels = [ch.strip() for ch in REQUIRED_CHANNELS.split(',') if ch.strip()]
    
    if not channels:
        return True, ""
    
    for channel in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['member', 'administrator', 'creator']:
                print(f"✅ {BOT_NAME} - User {user_id} is a member of {channel}")
                return True, channel
        except Exception as e:
            print(f"⚠️ {BOT_NAME} - Error checking {channel} membership: {str(e)}")
            continue
    
    channel_list = " or ".join(channels)
    return False, channel_list

async def trick_or_treat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'trick or treat' messages"""
    user = update.effective_user
    message_text = update.message.text.lower() if update.message.text else ""
    chat_type = update.message.chat.type
    
    print(f"📨 {BOT_NAME} - Received message: '{message_text}' from user {user.id} in {chat_type} chat")
    
    if "trick or treat" not in message_text:
        return
    
    if chat_type in ['group', 'supergroup', 'channel']:
        print(f"📢 {BOT_NAME} - Message from group/channel - sending instruction to go to private chat")
        if has_user_won(user.id):
            await update.message.reply_text("🧛‍♂️ You've already claimed your candy!")
        else:
            await update.message.reply_text("🎃 Please start a private chat with me to receive CANDY CODE!")
        return
    
    print(f"💬 {BOT_NAME} - Message from private chat - processing prize")
    
    if has_user_won(user.id):
        print(f"✋ {BOT_NAME} - User {user.id} has already won")
        await update.message.reply_text("🧛‍♂️ You've already claimed your candy!")
        return
    
    if REQUIRED_CHANNELS:
        is_member, channel_info = await is_user_member(user.id, context)
        if not is_member:
            print(f"❌ {BOT_NAME} - User {user.id} is not a member of any required channel")
            channels = [ch.strip() for ch in REQUIRED_CHANNELS.split(',') if ch.strip()]
            channel_links = "\n".join([f"👉 {ch}" for ch in channels])
            await update.message.reply_text(
                f"🔒 Sorry! You must join one of our channels first to receive candy codes.\n\n"
                f"{channel_links}\n\n"
                f"After joining, come back and type 'trick or treat' again! 🎃"
            )
            return
    
    prize = get_random_prize()
    unique_code = get_unused_code(prize["tier"])
    
    if not unique_code:
        await update.message.reply_text(f"😔 Sorry, all {prize['tier']} Candy prizes have been claimed! Try again later.")
        print(f"❌ {BOT_NAME} - No more {prize['tier']} codes available")
        return
    
    add_winner(user.id, user.username or user.first_name, prize["tier"], unique_code)
    prize_message = prize["message_template"].format(code=unique_code)
    await update.message.reply_text(prize_message)
    print(f"✅ {BOT_NAME} - Prize sent to user {user.id}: {prize['tier']} with code {unique_code}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to show code pool status"""
    user = update.effective_user
    
    if ADMIN_USER_ID and user.id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ This command is for admins only.")
        return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT tier, COUNT(*) as total, SUM(CASE WHEN is_used = 0 THEN 1 ELSE 0 END) as available FROM codes GROUP BY tier ORDER BY tier')
    stats = cursor.fetchall()
    conn.close()
    
    message = f"📊 **{BOT_NAME} Code Pool Status**\n\n"
    total_codes = 0
    total_available = 0
    
    for tier, total, available in stats:
        used = total - available
        total_codes += total
        total_available += available
        emoji = "🎃" if tier == "Large" else "🍭" if tier == "Medium" else "🍬"
        message += f"{emoji} **{tier}:** {available}/{total} available ({used} used)\n"
    
    total_used = total_codes - total_available
    message += f"\n**Total:** {total_available}/{total_codes} available ({total_used} used)"
    
    await update.message.reply_text(message)

async def winners_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to view all winners"""
    user = update.effective_user
    
    if ADMIN_USER_ID and user.id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ This command is for admins only.")
        return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, prize_tier, code, date FROM winners ORDER BY date DESC')
    winners = cursor.fetchall()
    conn.close()
    
    if not winners:
        await update.message.reply_text("📭 No winners yet!")
        return
    
    message = f"🎃 **{BOT_NAME} Winners** 🎃\n\n"
    
    large_count = sum(1 for _, _, tier, _, _ in winners if tier == "Large")
    medium_count = sum(1 for _, _, tier, _, _ in winners if tier == "Medium")
    small_count = sum(1 for _, _, tier, _, _ in winners if tier == "Small")
    
    message += f"📊 **Statistics:**\n"
    message += f"🎃 Large Candy: {large_count}\n"
    message += f"🍭 Medium Candy: {medium_count}\n"
    message += f"🍬 Small Candy: {small_count}\n"
    message += f"👥 Total Winners: {len(winners)}\n\n"
    message += f"📜 **All Winners (showing all {len(winners)}):**\n"
    
    await update.message.reply_text(message)
    
    chunk_message = ""
    chunk_size = 0
    max_chars = 3800
    
    for user_id, username, prize_tier, code, date in winners:
        emoji = "🎃" if prize_tier == "Large" else "🍭" if prize_tier == "Medium" else "🍬"
        line = f"{emoji} @{username or user_id} - {prize_tier} - CODE: {code} ({date})\n"
        
        if chunk_size + len(line) > max_chars:
            await update.message.reply_text(chunk_message)
            chunk_message = ""
            chunk_size = 0
        
        chunk_message += line
        chunk_size += len(line)
    
    if chunk_message:
        await update.message.reply_text(chunk_message)

def main():
    """Start Bot B with webhook"""
    bot_token = os.environ.get('BOT_TOKEN_B')
    
    if not bot_token:
        print(f"❌ Error: BOT_TOKEN_B environment variable not set!")
        print("Please set your Telegram Bot Token in Railway environment variables.")
        return
    
    if not DOMAIN:
        print(f"❌ Error: DOMAIN environment variable not set!")
        print("Please set DOMAIN to your Railway app URL (e.g., https://your-app.up.railway.app)")
        return
    
    init_database()
    load_codes_from_csv()
    
    application = Application.builder().token(bot_token).build()
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, trick_or_treat_handler))
    application.add_handler(CommandHandler("winners", winners_command))
    application.add_handler(CommandHandler("status", status_command))
    
    print(f"🍬 {BOT_NAME} (Trick or Treat Bot) starting with WEBHOOK mode...")
    print(f"📡 Domain: {DOMAIN}")
    print(f"🔌 Port: {PORT}")
    
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=bot_token,
        webhook_url=f"{DOMAIN}/{bot_token}"
    )

if __name__ == '__main__':
    main()
