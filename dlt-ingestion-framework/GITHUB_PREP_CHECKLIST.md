# GitHub Repository Preparation Checklist

**Date:** February 15, 2026  
**Purpose:** Ensure framework is ready for public GitHub repository

---

## ✅ Pre-Commit Checklist

### 1. Security & Secrets 🔒

- [x] **`.gitignore` configured** - Already excludes sensitive files
- [x] **secrets.toml.example created** - Template for users to copy
- [ ] **Remove actual secrets.toml** (if exists in .dlt/)
  ```powershell
  # Check if it exists
  Get-ChildItem -Path .dlt -Filter secrets.toml -Recurse
  
  # If found, DELETE it (it's in .gitignore so won't be committed anyway)
  Remove-Item .dlt\secrets.toml -Force
  ```

- [ ] **Check for hardcoded credentials**
  ```powershell
  # Search for potential secrets in code
  Select-String -Path "src\**\*.py" -Pattern "(password|api_key|secret|token)\s*=\s*['\"](?!.*\{)" -SimpleMatch
  ```

- [ ] **Verify .gitignore coverage**
  ```powershell
  # Test what would be committed
  git status --ignored
  
  # Should NOT see:
  # - .dlt/secrets.toml
  # - logs/
  # - metadata/
  # - __pycache__/
  ```

### 2. Documentation 📚

- [x] **README.md exists** - Good overview already present
- [x] **LICENSE file** - MIT License added
- [x] **Architecture docs** - Complete in docs/ folder
- [ ] **Update README badges** (optional)
  ```markdown
  [![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
  [![DLT](https://img.shields.io/badge/dlt-1.5.0-green.svg)](https://dlthub.com/)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  ```

- [ ] **Add CONTRIBUTING.md** (optional - see template below)

### 3. Code Quality 🧹

- [x] **Modular architecture** - Already refactored
- [ ] **Remove debug prints** (if any)
  ```powershell
  # Check for debug statements
  Select-String -Path "src\**\*.py" -Pattern "print\(|pdb.set_trace|breakpoint\("
  ```

- [ ] **Remove commented code blocks** (optional cleanup)
- [ ] **Check for TODO/FIXME comments**
  ```powershell
  Select-String -Path "src\**\*.py" -Pattern "TODO|FIXME|HACK|XXX"
  ```

### 4. Example Files 📋

- [x] **secrets.toml.example** - Created with all sources
- [ ] **Sample ingestion_config.xlsx** - Check if it contains real data
  ```powershell
  # If it has real credentials/data, create a sanitized copy
  Copy-Item config\ingestion_config.xlsx config\ingestion_config.xlsx.backup
  # Then edit ingestion_config.xlsx to have example/dummy data only
  ```

- [ ] **Create .env.example** (if using environment variables)

### 5. Repository Structure 🗂️

- [x] **Clean folder structure** - Well organized
- [ ] **Remove backup files**
  ```powershell
  # Check for backup files
  Get-ChildItem -Recurse -Filter "*.backup" -File
  Get-ChildItem -Recurse -Filter "*_old*" -File
  Get-ChildItem -Recurse -Filter "*.bak" -File
  
  # Remove if found
  Remove-Item **\*.backup, **\*_old*, **\*.bak
  ```

- [ ] **Remove empty folders**
  ```powershell
  # Find empty directories
  Get-ChildItem -Recurse -Directory | Where-Object { (Get-ChildItem $_.FullName).Count -eq 0 }
  ```

### 6. Git Repository Setup 🔧

- [ ] **Initialize Git** (if not already)
  ```powershell
  cd "C:\Users\Vinithkumar.Perumal\OneDrive - insidemedia.net\Documents\dlt_ingestion_copy\dlt_ingestion - Copy\dlt-ingestion-framework"
  
  # Check if git repo exists
  git status
  
  # If not, initialize
  git init
  ```

- [ ] **First commit**
  ```powershell
  # Stage all files
  git add .
  
  # Check what will be committed (verify no secrets)
  git status
  
  # First commit
  git commit -m "Initial commit: DLT Ingestion Framework - Production-grade multi-source data pipeline"
  ```

- [ ] **Create GitHub repository**
  1. Go to https://github.com/new
  2. Repository name: `dlt-ingestion-framework` (or your preference)
  3. Description: "Production-grade, Excel-driven data ingestion framework using dlthub for ADLS Gen2"
  4. Choose: Public or Private
  5. **DO NOT** initialize with README (you already have one)
  6. Click "Create repository"

- [ ] **Connect and push**
  ```powershell
  # Add remote (replace YOUR_USERNAME)
  git remote add origin https://github.com/YOUR_USERNAME/dlt-ingestion-framework.git
  
  # Push to GitHub
  git branch -M main
  git push -u origin main
  ```

---

## 📝 Optional Enhancements

### Create CONTRIBUTING.md

```markdown
# Contributing to DLT Ingestion Framework

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Adding New Source Types

1. Create handler in `src/core/connection_builder.py`
2. Add to `builders` dictionary
3. Update `secrets.toml.example`
4. Test with sample data
5. Document in README.md

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all public methods
- Keep functions focused (single responsibility)

## Testing

```bash
# Run tests (when implemented)
pytest tests/

# Type checking
mypy src/
```

## Questions?

Open an issue or discussion on GitHub.
```

### Add README Badges

```markdown
# At top of README.md
![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![DLT Version](https://img.shields.io/badge/dlt-1.5.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)
[![GitHub Stars](https://img.shields.io/github/stars/YOUR_USERNAME/dlt-ingestion-framework.svg)](https://github.com/YOUR_USERNAME/dlt-ingestion-framework/stargazers)
```

### Create GitHub Actions CI/CD (Advanced)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest tests/
```

---

## 🚨 Critical Warnings

### ❌ NEVER COMMIT:
- `secrets.toml` (actual credentials)
- `.dlt/` folder (contains pipeline state and local secrets)
- `logs/` with real data
- `metadata/` with sensitive audit info
- Excel files with real connection strings/passwords

### ✅ ALWAYS COMMIT:
- `secrets.toml.example` (template only)
- `.gitignore` (comprehensive exclusions)
- Documentation
- Source code
- Sample configurations (sanitized)

---

## Final Pre-Push Checks

```powershell
# 1. Verify .gitignore working
git status --ignored
# Should show .dlt/, logs/, metadata/ as ignored

# 2. Check what's being committed
git diff --cached --name-only

# 3. Search for any leaked secrets in staged files
git diff --cached | Select-String -Pattern "(password|api_key|secret_key|private_key)\s*[:=]\s*['\"](?!.*example)"

# 4. Dry run to see what would be pushed
git push --dry-run origin main

# 5. If all looks good, push!
git push origin main
```

---

## Post-Push Tasks

### 1. Update Repository Settings on GitHub
- [ ] Add description
- [ ] Add topics/tags: `data-engineering`, `dlt`, `azure`, `etl`, `python`
- [ ] Enable Issues
- [ ] Enable Discussions (optional)
- [ ] Set up branch protection (optional)

### 2. Create Initial Release
- [ ] Tag version v1.0.0
- [ ] Write release notes
- [ ] Upload any binaries (if applicable)

### 3. Add Repository Badges to README
- [ ] Build status (if CI/CD configured)
- [ ] Coverage (if tests configured)
- [ ] Version badge

### 4. Share Your Work! 🎉
- [ ] Share on LinkedIn
- [ ] Share in DLT community
- [ ] Add to your portfolio

---

## Need Help?

**Common Issues:**

1. **"git push" rejected**: Check if repository already has files
   ```powershell
   git pull origin main --allow-unrelated-histories
   git push origin main
   ```

2. **Secrets accidentally committed**: 
   ```powershell
   # Remove from history (use with caution!)
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch .dlt/secrets.toml' \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push (overwrites remote)
   git push origin --force --all
   ```

3. **Large files**: Use Git LFS
   ```powershell
   git lfs install
   git lfs track "*.xlsx"
   git add .gitattributes
   ```

---

## Summary

✅ **Safe to push when:**
- No secrets in code
- .gitignore properly configured
- Documentation complete
- Code is clean and commented
- Examples are sanitized

🚀 **Ready to go public!**
