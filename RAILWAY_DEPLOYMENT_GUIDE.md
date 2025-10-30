# 🚂 Railway Deployment Guide - Dual Bot System

This guide will help you deploy **Bot A** and **Bot B** as **two separate Railway services**.

---

## 📋 Prerequisites

Before deploying, make sure you have:
1. ✅ A Railway account (sign up at https://railway.app)
2. ✅ Your GitHub repository with the bot code
3. ✅ Two Telegram bot tokens from @BotFather
4. ✅ Your Telegram user ID (from @userinfobot)
5. ✅ Both bots added as administrators in their respective channels

---

## 🎯 Deployment Strategy

You'll create **2 separate Railway projects**:
- **Project 1**: Bot A (Channel A)
- **Project 2**: Bot B (Channel B)

Each bot gets its own:
- Railway project
- Domain (e.g., `bot-a-production.up.railway.app`)
- Database files
- Environment variables

---

## 🚀 Deploying Bot A

### Step 1: Create New Railway Project for Bot A

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway will detect it's a Python app

### Step 2: Configure Bot A Settings

#### A) Set Environment Variables

In Railway dashboard, go to **Variables** tab and add:

| Variable Name | Value | Example |
|--------------|-------|---------|
| `BOT_TOKEN_A` | Your Bot A token from @BotFather | `123456:ABCdef...` |
| `REQUIRED_CHANNELS_A` | Your Channel A username | `@your_channel_a` |
| `ADMIN_USER_ID` | Your Telegram user ID | `7371759174` |
| `DOMAIN` | Your Railway domain (see below) | `https://bot-a-production.up.railway.app` |
| `PORT` | Railway provides this automatically | Leave empty or use `8443` |

#### B) Get Your Railway Domain

1. In Railway dashboard, go to **"Settings"** tab
2. Scroll to **"Domains"** section
3. Click **"Generate Domain"**
4. Copy the domain (e.g., `https://bot-a-production.up.railway.app`)
5. Go back to **"Variables"** and paste it as `DOMAIN`

#### C) Configure Start Command

1. In Railway dashboard, go to **"Settings"** tab
2. Find **"Start Command"** or **"Custom Start Command"**
3. Enter: `python bot_a_webhook.py`

Alternatively, create a file named `Procfile` (no extension) in your repo:
```
web: python bot_a_webhook.py
```

### Step 3: Add Required Files to Repository

Make sure these files are in your **Bot A** repository:

```
your-repo/
├── bot_a_webhook.py       ← Webhook version for Railway
├── codes_part1.csv         ← Bot A's 900 codes
├── requirements.txt        ← Python dependencies
├── runtime.txt             ← Python version
└── Procfile (optional)     ← Start command
```

**Important**: You DON'T need to include:
- `bot_b_webhook.py` (only Bot A files)
- `codes_part2.csv` (only for Bot B)
- `winners_b.db` (only for Bot B)

### Step 4: Deploy Bot A

1. Railway will automatically deploy when you push to GitHub
2. Or click **"Deploy"** button in Railway dashboard
3. Wait for deployment to complete (check **"Deployments"** tab)
4. Check logs for: `🍬 Bot A (Trick or Treat Bot) starting with WEBHOOK mode...`

### Step 5: Set Telegram Webhook for Bot A

After deployment, you need to tell Telegram about your webhook:

1. Open this URL in your browser (replace values):
```
https://api.telegram.org/bot<BOT_TOKEN_A>/setWebhook?url=<RAILWAY_DOMAIN>/<BOT_TOKEN_A>
```

**Example**:
```
https://api.telegram.org/bot123456:ABCdef/setWebhook?url=https://bot-a-production.up.railway.app/123456:ABCdef
```

2. You should see:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

3. Verify it worked:
```
https://api.telegram.org/bot<BOT_TOKEN_A>/getWebhookInfo
```

### Step 6: Test Bot A

1. Go to your Bot A on Telegram
2. Start a private chat
3. Type: `trick or treat`
4. You should receive a candy code! 🎃

---

## 🚀 Deploying Bot B

Repeat the **exact same process** for Bot B, but with these changes:

### Differences for Bot B:

| Setting | Bot B Value |
|---------|-------------|
| **Railway Project Name** | "Halloween Bot B" or similar |
| **Environment Variables** | Use `BOT_TOKEN_B` and `REQUIRED_CHANNELS_B` |
| **Start Command** | `python bot_b_webhook.py` |
| **Files Needed** | `bot_b_webhook.py` + `codes_part2.csv` |
| **Webhook URL** | Use Bot B's Railway domain + Bot B token |

### Quick Checklist for Bot B:

1. ✅ Create new Railway project (separate from Bot A)
2. ✅ Set environment variables (`BOT_TOKEN_B`, `REQUIRED_CHANNELS_B`, `ADMIN_USER_ID`, `DOMAIN`)
3. ✅ Generate Railway domain for Bot B
4. ✅ Update `DOMAIN` variable with Bot B's Railway domain
5. ✅ Set start command: `python bot_b_webhook.py`
6. ✅ Deploy
7. ✅ Set Telegram webhook for Bot B
8. ✅ Test with "trick or treat"

---

## 🔧 Alternative: Deploy from Same Repo

If you want both bots deployed from the **same GitHub repository**:

### Option 1: Use Different Procfiles (Recommended)

**For Bot A Railway Project:**
1. Create `Procfile` with: `web: python bot_a_webhook.py`
2. Commit and deploy

**For Bot B Railway Project:**
1. Create a different branch (e.g., `bot-b-deploy`)
2. Edit `Procfile` to: `web: python bot_b_webhook.py`
3. In Railway, deploy from the `bot-b-deploy` branch

### Option 2: Set Custom Start Command

In each Railway project's settings, manually set the start command:
- Bot A: `python bot_a_webhook.py`
- Bot B: `python bot_b_webhook.py`

---

## 📊 File Structure for Railway

### Bot A Repository/Branch:
```
├── bot_a_webhook.py
├── codes_part1.csv
├── requirements.txt
├── runtime.txt
└── Procfile (web: python bot_a_webhook.py)
```

### Bot B Repository/Branch:
```
├── bot_b_webhook.py
├── codes_part2.csv
├── requirements.txt
├── runtime.txt
└── Procfile (web: python bot_b_webhook.py)
```

---

## 🐛 Troubleshooting

### Bot Not Responding

**Problem**: Bot deployed but doesn't respond to messages

**Solutions**:
1. Check Railway logs for errors
2. Verify `DOMAIN` environment variable matches your actual Railway domain
3. Make sure you set the Telegram webhook (Step 5)
4. Check webhook status: `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

### "Conflict: terminated by other getUpdates"

**Problem**: Webhook and polling both active

**Solution**: Delete the webhook first:
```
https://api.telegram.org/bot<TOKEN>/deleteWebhook
```
Then set it again.

### Railway App Crashes Immediately

**Problem**: Application error on startup

**Check**:
1. Railway logs for error messages
2. `BOT_TOKEN_A` or `BOT_TOKEN_B` is set correctly
3. `DOMAIN` variable is set
4. `codes_part1.csv` or `codes_part2.csv` exists in the repository

### Channel Verification Fails

**Problem**: Bot says user must join channel, but they already did

**Solutions**:
1. Make sure bot is an **administrator** in the channel
2. Check `REQUIRED_CHANNELS_A` or `REQUIRED_CHANNELS_B` has correct channel username (with @)
3. Try removing the @ symbol in the environment variable

### Database Not Saving Winners

**Problem**: Users can win multiple times

**Check**:
1. Railway has persistent storage (databases are created automatically)
2. Check Railway logs for database errors
3. Make sure `winners_a.db` and `winners_b.db` are not in `.gitignore`

---

## 🎯 Environment Variables Summary

### Bot A Variables:
```bash
BOT_TOKEN_A=123456:ABCdef...
REQUIRED_CHANNELS_A=@your_channel_a
ADMIN_USER_ID=7371759174
DOMAIN=https://bot-a-production.up.railway.app
```

### Bot B Variables:
```bash
BOT_TOKEN_B=789012:GHIjkl...
REQUIRED_CHANNELS_B=@your_channel_b
ADMIN_USER_ID=7371759174
DOMAIN=https://bot-b-production.up.railway.app
```

---

## 📱 Testing Checklist

After deployment, test each bot:

**Bot A**:
- ✅ Responds to "trick or treat" in private chat
- ✅ Verifies channel membership
- ✅ Gives unique candy codes
- ✅ `/status` command works (admin only)
- ✅ `/winners` command works (admin only)
- ✅ Same user cannot win twice

**Bot B**:
- ✅ Same tests as Bot A
- ✅ Uses separate code pool (codes_part2.csv)
- ✅ Independent winner database

---

## 🎉 Success!

Once both bots are deployed and responding, you're all set!

Each bot will:
- Run 24/7 on Railway
- Use its own 900 candy codes
- Track winners independently
- Verify channel membership
- Respond instantly via webhooks

**Cost**: Railway offers a free tier that should be sufficient for most Telegram bots.

---

## 📞 Need Help?

If you encounter issues:
1. Check Railway deployment logs
2. Verify all environment variables are set correctly
3. Make sure Telegram webhooks are configured
4. Test with `getWebhookInfo` API endpoint

Good luck with your Halloween candy distribution! 🎃🍬
