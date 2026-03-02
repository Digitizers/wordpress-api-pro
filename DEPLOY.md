# 🚀 Deployment Instructions

## ✅ Ready to Deploy: v2.0.1

**Changes in this version:**
- Slug: `wordpress-api-skill` → `wordpress-api` (cleaner!)
- GitHub repo will be: `Digitizers/wordpress-api`
- Version: 2.0.1

---

## 📋 Step-by-Step Deployment

### 1️⃣ שנה שם ה-Repository בגיטהאב

**אם ה-repo כבר קיים:**
1. עבור ל: https://github.com/Digitizers/wordpress-api-skill/settings
2. גלול ל-"Repository name"
3. שנה מ-`wordpress-api-skill` ל-`wordpress-api`
4. לחץ "Rename"

**אם ה-repo עדיין לא קיים:**
1. עבור ל: https://github.com/new
2. שם: `wordpress-api`
3. תיאור: "WordPress REST API integration skill for OpenClaw"
4. Public
5. **אל תאתחל עם README** (יש לנו כבר)
6. לחץ "Create repository"

---

### 2️⃣ העלה את הקוד לגיטהאב

```bash
# פתח את הטארבול
tar -xzf wordpress-api.tar.gz
cd wordpress-api

# הוסף remote
git remote add origin https://github.com/Digitizers/wordpress-api.git

# שנה ל-main branch
git branch -M main

# העלה
git push -u origin main
```

---

### 3️⃣ פרסם ב-ClawHub

**התחבר (אם עדיין לא):**
```bash
clawhub login
```

**פרסם גרסה 2.0.1:**
```bash
cd wordpress-api
./QUICK-PUBLISH.sh
```

**או ידני:**
```bash
clawhub publish . \
  --slug wordpress-api \
  --name "WordPress API" \
  --version 2.0.1 \
  --changelog "Renamed from wordpress-api-skill to wordpress-api (cleaner slug following package manager conventions)"
```

---

### 4️⃣ מחק את הגרסה הישנה (אופציונלי)

אם פרסמת קודם `wordpress-api-skill`:

```bash
clawhub delete wordpress-api-skill
```

**או:** פשוט השאר אותו - הוא יישאר במערכת אבל לא מעודכן.

---

## ✅ אישור

**לאחר הפרסום בדוק:**

**1. GitHub:**
- Repo: https://github.com/Digitizers/wordpress-api
- יש 15 commits
- יש README.md

**2. ClawHub:**
- Skill page: https://clawhub.com/skills/wordpress-api
- Version: 2.0.1
- Install works: `clawhub install wordpress-api --dir /tmp/test`

---

## 📦 מה נמצא בטארבול

```
wordpress-api/
├── SKILL.md (name: wordpress-api)
├── package.json (name: wordpress-api, version: 2.0.1)
├── README.md
├── CHANGELOG.md (includes v2.0.1)
├── PUBLISH.md
├── QUICK-PUBLISH.sh
├── GITHUB-SETUP.md
├── LICENSE.txt
├── wp.sh
├── config/sites.example.json
├── scripts/ (6 Python files)
└── references/ (2 docs)
```

**19 files, 15KB compressed**

---

## 🎯 Final State

| Item | Value |
|------|-------|
| **GitHub repo** | `Digitizers/wordpress-api` |
| **ClawHub slug** | `wordpress-api` |
| **package.json name** | `wordpress-api` |
| **SKILL.md name** | `wordpress-api` |
| **Version** | 2.0.1 |
| **Install command** | `clawhub install wordpress-api` |
| **Local folder** | `~/.openclaw/workspace/skills/wordpress-api` |

---

**הכל מוכן! פשוט תריץ את הפקודות למעלה** 🚀
