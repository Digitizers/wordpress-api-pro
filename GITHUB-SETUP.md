# GitHub Setup Guide

## 📦 Repository Ready

התיקייה `wordpress-api/` מוכנה להעלאה לגיטהאב.

**מה נכלל:**
- ✅ SKILL.md - Skill definition
- ✅ 4 Python scripts (update, create, get, list)
- ✅ 2 reference docs (API + Gutenberg)
- ✅ README.md - GitHub-facing documentation
- ✅ LICENSE - MIT
- ✅ package.json - ClawHub metadata
- ✅ .gitignore - Security rules
- ✅ Git initialized + initial commit

---

## 🚀 העלאה לגיטהאב

### שלב 1: צור repository בגיטהאב

1. עבור ל-https://github.com/new
2. שם: `wordpress-api-skill`
3. תיאור: "WordPress REST API integration skill for OpenClaw"
4. Public (להפצה ב-ClawHub) או Private (לשימוש אישי)
5. ⚠️ **אל תאתחל עם README** (יש לנו כבר)
6. לחץ "Create repository"

### שלב 2: חבר את ה-repo המקומי

```bash
cd ~/.openclaw/workspace/skills/wordpress-api

# הוסף remote (החלף YOUR_USERNAME בשם המשתמש שלך)
git remote add origin https://github.com/YOUR_USERNAME/wordpress-api-skill.git

# שנה את שם ה-branch ל-main
git branch -M main

# העלה
git push -u origin main
```

### שלב 3: Topics / Tags

בעמוד הrepository בגיטהאב, הוסף topics:
- `openclaw`
- `openclaw-skill`
- `wordpress`
- `rest-api`
- `gutenberg`
- `cms`
- `publishing`

---

## 📋 שימוש ב-Skill

### התקנה ידנית:

```bash
cd ~/.openclaw/workspace/skills/
git clone https://github.com/YOUR_USERNAME/wordpress-api-skill wordpress-api
```

### התקנה דרך ClawHub (אחרי פרסום):

```bash
clawhub install wordpress-api
```

---

## 🔗 ClawHub Publication (אופציונלי)

אם תרצה לפרסם ב-ClawHub (https://clawhub.com):

1. וודא ש-`package.json` תקין ✅
2. הרץ: `clawhub publish`
3. הסקיל יופיע ב-ClawHub search
4. משתמשים יוכלו להתקין עם: `clawhub install wordpress-api`

---

## 🛠️ עדכונים עתידיים

כשתעדכן תוכן:

```bash
cd ~/.openclaw/workspace/skills/wordpress-api
git add .
git commit -m "תיאור השינוי"
git push
```

**זכור לעדכן:**
- `package.json` version - אם יש שינוי משמעותי

---

## 🧪 בדיקה

לפני פרסום, בדוק שהskill עובד:

```bash
# הגדר credentials:
export WP_URL="https://your-test-site.com"
export WP_USERNAME="your-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"

# בדוק script:
python3 scripts/get_post.py --post-id 1
```

---

## 🔐 אבטחה

**כלול:**
- ✅ קוד סקריפטים
- ✅ תיעוד
- ✅ דוגמאות

**לא כלול (.gitignore):**
- ❌ credentials/
- ❌ .env files
- ❌ passwords או API keys

---

---

## 🚀 פרסום ב-ClawHub

לאחר העלאה לגיטהאב, פרסם ב-ClawHub:

### שלב 1: התחבר

```bash
clawhub login
# → פותח דפדפן, תתחבר עם GitHub/Google
```

### שלב 2: פרסם

**אוטומטי (מומלץ):**
```bash
./QUICK-PUBLISH.sh
```

**ידני:**
```bash
clawhub publish ./skills/wordpress-api \
  --slug wordpress-api \
  --name "WordPress API" \
  --version 2.0.0 \
  --changelog "Multi-site management + batch operations"
```

### שלב 3: אישור

✓ Skill מפורסם ב-https://clawhub.com/skills/wordpress-api

אנשים יכולים להתקין:
```bash
clawhub install wordpress-api
```

---

**הכל מוכן! 🎉**

1. העלה לגיטהאב
2. פרסם ב-ClawHub
3. השתמש בעצמך או שתף עם הקהילה!
