# 📊 Telegram Bot Analytics & Stats - Feature Documentation

## Overview
Added comprehensive statistics and analytics commands to provide quick access to database insights without opening the web UI.

---

## 🆕 New Commands

### `/stats` - Comprehensive Database Statistics

**Description:** Get a complete overview of your Snatchbase database with detailed breakdowns.

**Usage:**
```
/stats
```

**Features:**
- 📈 **Overall Database Metrics**
  - Total credentials count
  - Total devices/systems
  - Total uploads
  - Unique domains
  - Country distribution
  - Stealer types count

- ⚡ **Recent Activity Snapshot**
  - New credentials in last 24 hours
  - New credentials in last 7 days
  - New credentials in last 30 days
  - New devices in last 24 hours

- 🔝 **Top 5 Analysis**
  - Most common domains
  - Most affected countries (with flag emojis)
  - Most active stealer families

- 🕐 **Timestamp**
  - Shows when statistics were generated

**Example Output:**
```
📊 SNATCHBASE STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 OVERALL DATABASE
🔑 Total Credentials: 46,346
🖥️ Total Devices: 110
📦 Total Uploads: 15
🌐 Unique Domains: 2,847
🌍 Countries: 45
🦠 Stealer Types: 12

⚡ RECENT ACTIVITY
📅 Last 24h: 1,234 creds | 5 devices
📅 Last 7d: 8,456 credentials
📅 Last 30d: 25,678 credentials

🔝 TOP 5 DOMAINS
1. gmail.com: 5,234
2. facebook.com: 3,456
3. discord.com: 2,890
...

🌍 TOP 5 COUNTRIES
1. 🇺🇸 US: 25
2. 🇬🇧 GB: 18
3. 🇩🇪 DE: 12
...

🦠 TOP 5 STEALERS
1. Lumma: 15,234
2. RedLine: 12,456
3. Raccoon: 8,900
...
```

---

### `/recent` - Recent Activity Tracker

**Description:** View recently added credentials and devices with detailed breakdowns and time-based filtering.

**Usage:**
```
/recent              # Default: last 24 hours
/recent 1h           # Last 1 hour
/recent 6h           # Last 6 hours
/recent 12h          # Last 12 hours
/recent 24h          # Last 24 hours (same as default)
/recent 7d           # Last 7 days
/recent 30d          # Last 30 days
```

**Features:**
- 📊 **Activity Summary**
  - Total new credentials in period
  - Total new devices in period
  - Time range display

- 🌐 **Domain Breakdown**
  - Top 5 domains from recent activity
  - Credential count per domain

- 🦠 **Stealer Analysis**
  - Top 5 stealer types found
  - Distribution of stealer families

- 🖥️ **Recent Devices**
  - Last 5 devices added
  - Country flags
  - Credential counts per device

- 🔑 **Sample Credentials**
  - Latest 5 credentials added
  - Domain, username, and time ago
  - Link to view more

- 💡 **Usage Tips**
  - Shows available time period options

**Example Output:**
```
🕐 RECENT ACTIVITY (24H)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 SUMMARY
🔑 New Credentials: 1,234
🖥️ New Devices: 5
🕐 Period: 2025-11-01 22:47 → Now

🌐 TOP DOMAINS
1. gmail.com: 234
2. facebook.com: 189
3. discord.com: 156
4. steam.com: 145
5. twitter.com: 123

🦠 STEALER TYPES
• Lumma: 456
• RedLine: 389
• Raccoon: 234
• MetaStealer: 155

🖥️ RECENT DEVICES
🇺🇸 PC_USER_[US]_192.168.1.1_Lumma (234 creds)
🇬🇧 DESKTOP-ABC123_[GB]_10.0.0.5_RedLine (189 creds)
🇩🇪 LAPTOP_XYZ_[DE]_172.16.0.10_Raccoon (156 creds)
...

🔑 SAMPLE CREDENTIALS (Latest 5)
1. gmail.com - user@example.com... (5m ago)
2. facebook.com - johndoe@mail.c... (12m ago)
3. discord.com - player123@gmai... (23m ago)
4. steam.com - gamer456@hotmai... (35m ago)
5. twitter.com - tweet_user@out... (47m ago)

... and 1,229 more credentials

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 TIP: Use /recent 1h, /recent 7d, or /recent 30d
```

---

## 🎯 Use Cases

### 1. **Quick Health Check**
```
/stats
```
Get instant overview of database size and recent growth.

### 2. **Monitor New Activity**
```
/recent
```
Check what's been added in the last 24 hours.

### 3. **Weekly Review**
```
/recent 7d
```
Review weekly trends and top targets.

### 4. **Hourly Monitoring**
```
/recent 1h
```
Monitor real-time ingestion during active collection.

### 5. **Monthly Analysis**
```
/recent 30d
```
Get monthly overview for reports.

---

## 🔧 Technical Details

### Features Implemented:

1. **Time-based Filtering**
   - Supports: 1h, 6h, 12h, 24h, 7d, 30d
   - Default: 24h if no argument provided

2. **Country Flag Emojis**
   - Automatic conversion of 2-letter country codes to flag emojis
   - Uses Unicode regional indicator symbols

3. **Smart Time Formatting**
   - "5m ago" for minutes
   - "2h ago" for hours  
   - "3d ago" for days
   - Full date for older entries

4. **Efficient Queries**
   - Optimized SQL queries with proper indexing
   - Pagination for large result sets
   - Grouped aggregations for performance

5. **Error Handling**
   - Graceful fallbacks on database errors
   - User-friendly error messages
   - Logging for debugging

6. **Back Button Integration**
   - All commands include back-to-main button
   - Consistent navigation experience

---

## 📱 Command List (Updated)

All available Telegram bot commands:

| Command | Description |
|---------|-------------|
| `/start` | Show main menu and database statistics |
| `/status` | Check bot status and uptime |
| `/stats` | ⭐ **NEW** - Comprehensive database analytics |
| `/recent [time]` | ⭐ **NEW** - Recent activity (1h/6h/12h/24h/7d/30d) |
| `/search <query>` | Search credentials by domain/username/URL |
| `/topdomains` | View top 100 domains |
| `/extractdomains` | Extract credentials from target domains |

---

## 🚀 Benefits

### For Users:
- ✅ **Instant Insights** - No need to open web browser
- ✅ **Mobile Friendly** - Check stats from phone
- ✅ **Quick Triage** - Identify important trends fast
- ✅ **Time Filters** - Focus on relevant time periods
- ✅ **Visual Data** - Flag emojis and formatting

### For Operations:
- ✅ **Monitoring** - Track ingestion in real-time
- ✅ **Reporting** - Quick status for stakeholders
- ✅ **Trending** - Identify hot targets
- ✅ **Health Check** - Verify database growth

---

## 📊 Data Shown

### /stats Command:
- Overall metrics (6 key indicators)
- Recent activity (3 time periods)
- Top 5 domains with counts
- Top 5 countries with flags
- Top 5 stealer families
- Timestamp of generation

### /recent Command:
- New credentials count
- New devices count
- Time period range
- Top 5 domains in period
- Stealer type distribution
- Latest 5 devices with details
- Sample of 5 latest credentials
- Usage tips for different time periods

---

## 🎨 Design Principles

1. **Information Density** - Pack maximum value in minimal space
2. **Visual Hierarchy** - Use emojis and formatting for clarity
3. **Progressive Disclosure** - Show summaries with option for details
4. **Consistent Formatting** - Numbers with commas, aligned text
5. **Actionable Insights** - Highlight what matters most

---

## 🔮 Future Enhancements

Potential additions to consider:

1. **Alerts & Notifications**
   - Auto-notify on threshold hits
   - Daily/weekly scheduled reports

2. **Trend Analysis**
   - Compare periods (this week vs last week)
   - Growth rate calculations
   - Predictive insights

3. **Export Options**
   - CSV export of stats
   - PDF reports
   - Scheduled email reports

4. **Custom Filters**
   - Filter by specific stealer
   - Filter by country
   - Filter by domain category

5. **Visualizations**
   - ASCII charts in chat
   - Image generation for charts
   - Timeline graphics

---

## ✨ Example Usage Flow

```
User: /stats
Bot: [Shows comprehensive statistics]

User: Sees 1,234 new credentials in last 24h

User: /recent
Bot: [Shows detailed breakdown of last 24h]

User: Wants to see just last hour

User: /recent 1h
Bot: [Shows activity from last hour only]

User: Wants to search for specific domain seen in stats

User: /search gmail.com
Bot: [Returns Gmail credentials]
```

---

## 🎯 Success Metrics

The analytics commands are successful if they:

1. ✅ Reduce time to get database insights by 90%
2. ✅ Enable mobile-first workflow
3. ✅ Increase user engagement with data
4. ✅ Reduce web UI logins for simple checks
5. ✅ Provide actionable intelligence quickly

---

**Status:** ✅ **IMPLEMENTED & DEPLOYED**

**Bot Version:** 2.1.0  
**Date:** November 2, 2025  
**Module:** `telegram/analytics.py`
