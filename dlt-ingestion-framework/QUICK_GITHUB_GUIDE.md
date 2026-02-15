# Quick GitHub Upload Guide

## Option 1: Using GitHub Desktop (Easiest) 🖱️

1. **Download GitHub Desktop**: https://desktop.github.com/
2. **Open in GitHub Desktop**:
   - File → Add Local Repository
   - Choose: `dlt-ingestion-framework` folder
   - If not a repo yet, click "Create a repository"
3. **Commit**:
   - Review changed files (verify no secrets!)
   - Write message: "Initial commit: DLT Ingestion Framework"
   - Click "Commit to main"
4. **Publish**:
   - Click "Publish repository"
   - Choose Public/Private
   - Click "Publish repository"

**Done! ✅**

---

## Option 2: Using Command Line 💻

### Step 1: Navigate to Framework
```powershell
cd "C:\Users\Vinithkumar.Perumal\OneDrive - insidemedia.net\Documents\dlt_ingestion_copy\dlt_ingestion - Copy\dlt-ingestion-framework"
```

### Step 2: Initialize Git (if not done)
```powershell
# Check if already a git repo
git status

# If error, initialize
git init
```

### Step 3: Review What Will Be Committed
```powershell
# See all files
git status

# Check for ignored files (should see .dlt/, logs/, etc.)
git status --ignored

# IMPORTANT: Verify NO secrets are being committed
git add -n .  # Dry run - shows what would be staged
```

### Step 4: First Commit
```powershell
# Stage all files
git add .

# Commit
git commit -m "Initial commit: DLT Ingestion Framework v1.0

- Production-grade multi-source data pipeline
- Excel-driven configuration
- Supports PostgreSQL, Oracle, MSSQL, Azure SQL, REST APIs  
- Config-driven pipeline architecture
- ADLS Gen2 destination with date partitioning
- Comprehensive documentation"
```

### Step 5: Create GitHub Repository
1. Go to: https://github.com/new
2. Repository name: `dlt-ingestion-framework`
3. Description: `Production-grade, Excel-driven data ingestion framework using dlthub for Azure ADLS Gen2`
4. Choose: **Public** (or Private if you prefer)
5. **DO NOT** check any initialization options
6. Click **"Create repository"**

### Step 6: Push to GitHub
```powershell
# Add remote (REPLACE YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/dlt-ingestion-framework.git

# Rename branch to main (if needed)
git branch -M main

# Push
git push -u origin main
```

**Done! ✅**

---

## Option 3: Using VS Code 📝 (Recommended - Easiest!)

VS Code has **built-in GitHub integration** - no need for command line or GitHub Desktop!

### Step-by-Step:

1. **Open Folder in VS Code**
   - File → Open Folder
   - Navigate to: `dlt-ingestion-framework`
   - Click "Select Folder"

2. **Open Source Control**
   - Click Source Control icon (left sidebar) 
   - OR press `Ctrl+Shift+G`

3. **Initialize Repository**
   - Click **"Initialize Repository"** button
   - Git is now enabled for this folder

4. **Review Files to Commit**
   - You'll see all changed files listed
   - ✅ Verify `.dlt/secrets.toml` is **NOT** in the list (should be ignored)
   - ✅ Check that only safe files are shown

5. **Stage All Changes**
   - Click the **"+"** icon next to "Changes"
   - OR hover over each file and click "+"
   - Files move to "Staged Changes"

6. **Write Commit Message**
   - In the message box at top, type:
   ```
   Initial commit: DLT Ingestion Framework v1.0
   
   - Production-grade multi-source data pipeline
   - Excel-driven configuration
   - Modular architecture with config-driven pipeline
   ```

7. **Commit Changes**
   - Click **"Commit"** button (checkmark icon)
   - OR press `Ctrl+Enter`

8. **Sign in to GitHub** (First time only)
   - Click **"Publish to GitHub"** button
   - VS Code will prompt: "The extension 'GitHub' wants to sign in using GitHub"
   - Click **"Allow"**
   - Browser opens → Click **"Authorize Visual-Studio-Code"**
   - VS Code shows: "You are now signed in to GitHub"

9. **Publish Repository**
   - Choose repository name: `dlt-ingestion-framework`
   - Select: **Public** or **Private**
   - Click **"OK"**
   - VS Code uploads your code to GitHub!

10. **Done! ✅**
    - Check notification: "Successfully published to GitHub"
    - Click "Open on GitHub" to view your repository

### 🔑 GitHub Account Linking

**First Time Setup:**
- VS Code will prompt you to sign in to GitHub
- Your browser opens for authorization
- After authorizing, VS Code remembers your GitHub account
- Future repositories publish instantly (no sign-in needed)

**Already Signed In?**
- Check bottom-left corner of VS Code
- You'll see your GitHub username if signed in
- Click it to manage accounts or sign out

### 🎨 Visual Benefits of VS Code

- ✅ **See exactly what's being committed** (file-by-file review)
- ✅ **Color-coded changes** (green = added, red = deleted)
- ✅ **Built-in diff viewer** (click any file to see changes)
- ✅ **Git history** (Timeline view shows all commits)
- ✅ **No command line needed** (everything is point-and-click)

### 💡 Pro Tips

**Review Changes Before Committing:**
- Click any file in Source Control to see exactly what changed
- Look for any accidentally included secrets
- Green = new content, Red = deleted content

**Ignore Additional Files:**
- Right-click any file → "Add to .gitignore"
- VS Code automatically updates `.gitignore` file

**Future Commits:**
- After making changes: Source Control → Stage → Commit → Push
- VS Code syncs changes to GitHub automatically

---

## 🔍 Pre-Push Safety Check

Run this before pushing:

```powershell
# 1. Check what will be committed
git diff --cached --name-only

# 2. Search for secrets in staged files
git diff --cached | Select-String -Pattern "password|api_key|secret_key|private_key"

# 3. If ANY matches found, DO NOT PUSH!
# Review those files and ensure they're example/template only
```

---

## ⚠️ Before You Push - Critical Checks

### ✅ Must Be True:
- [ ] No actual `secrets.toml` in `.dlt/` folder (only `secrets.toml.example`)
- [ ] `ingestion_config.xlsx` has dummy/example data only
- [ ] No real credentials in any file
- [ ] `.gitignore` excludes `.dlt/`, `logs/`, `metadata/`

### ❌ Must NOT Be Committed:
- `.dlt/secrets.toml` (actual credentials)
- `.dlt/*.duckdb` (local database files)
- `logs/*.log` (log files)
- `metadata/audit_*.csv` (audit data)
- Any file with real passwords/API keys

---

## 📦 What Will Be Uploaded

```
dlt-ingestion-framework/
├── .gitignore                ✅ Yes - protects secrets
├── LICENSE                   ✅ Yes - MIT License
├── README.md                 ✅ Yes - documentation
├── requirements.txt          ✅ Yes - dependencies
├── run.py                    ✅ Yes - entry point
├── GITHUB_PREP_CHECKLIST.md  ✅ Yes - this guide
├── .dlt/
│   └── secrets.toml.example  ✅ Yes - template only
├── config/
│   └── ingestion_config.xlsx ⚠️  Check for real data!
├── docs/                     ✅ Yes - all documentation
├── src/                      ✅ Yes - all source code
└── tests/                    ✅ Yes - test files

NOT uploaded (ignored):
├── .dlt/secrets.toml         ❌ Ignored
├── .dlt/*.duckdb             ❌ Ignored
├── logs/                     ❌ Ignored
├── metadata/                 ❌ Ignored
└── __pycache__/              ❌ Ignored
```

---

## 🚀 After Successful Push

### 1. Verify on GitHub
Visit: `https://github.com/YOUR_USERNAME/dlt-ingestion-framework`
- [ ] README displays correctly
- [ ] No secrets visible
- [ ] All docs accessible

### 2. Add Topics (on GitHub)
Click "⚙️ Settings" → "Topics"
Add: `data-engineering`, `etl`, `azure`, `dlt`, `python`, `data-pipeline`

### 3. Optional: Add README Badge
```markdown
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![DLT](https://img.shields.io/badge/powered%20by-dlthub-green.svg)
```

### 4. Share Your Work! 🎉
- LinkedIn: "Just open-sourced my production DLT framework! 🚀"
- Twitter/X: Tag @dlthub
- Add to your resume/portfolio

---

## 🆘 Common Issues

### Issue: "fatal: not a git repository"
**Solution:**
```powershell
git init
git add .
git commit -m "Initial commit"
```

### Issue: "remote origin already exists"
**Solution:**
```powershell
# Remove old remote
git remote remove origin

# Add new one
git remote add origin https://github.com/YOUR_USERNAME/dlt-ingestion-framework.git
```

### Issue: "rejected - non-fast-forward"
**Solution:**
```powershell
# Pull first (if repo already has files)
git pull origin main --allow-unrelated-histories
git push origin main
```

### Issue: "Accidentally committed secrets!"
**Solution:** See GITHUB_PREP_CHECKLIST.md section on removing secrets from history

---

## 📞 Need Help?

1. Check [GITHUB_PREP_CHECKLIST.md](GITHUB_PREP_CHECKLIST.md) for detailed steps
2. GitHub Docs: https://docs.github.com/en/get-started
3. Open an issue after pushing

---

## ✨ You're Ready!

Pick your option above and push in under 5 minutes! 🚀
