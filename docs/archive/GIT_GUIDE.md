# 📚 Git Usage Guide for NSFWBOT

## 🚀 Quick Git Commands

### Daily Development Workflow

```bash
# Check status of files
git status

# Add specific files
git add filename.py
git add templates/

# Add all changes
git add .

# Commit changes
git commit -m "✨ Add new feature: description"

# View commit history
git log --oneline
git log --graph --oneline --all

# Check differences
git diff                    # Unstaged changes
git diff --staged          # Staged changes
git diff HEAD~1            # Compare with previous commit
```

### Branch Management

```bash
# Create and switch to new branch
git checkout -b feature/new-payment-method
git checkout -b bugfix/dashboard-error
git checkout -b enhancement/ui-improvements

# Switch between branches
git checkout master
git checkout feature/new-payment-method

# List all branches
git branch -a

# Merge branch into master
git checkout master
git merge feature/new-payment-method

# Delete merged branch
git branch -d feature/new-payment-method
```

### Useful Git Commands

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Stash changes temporarily
git stash
git stash pop

# View file history
git log --follow filename.py

# Show changes in specific commit
git show <commit-hash>

# Create tag for releases
git tag -a v1.0.0 -m "Release version 1.0.0"
git tag -l
```

## 📝 Commit Message Conventions

Use emoji prefixes for clear commit categorization:

```bash
# New features
git commit -m "✨ Add OpenRouter model selection"
git commit -m "🚀 Implement TON payment integration"

# Bug fixes
git commit -m "🐛 Fix dashboard template error"
git commit -m "🔧 Resolve database connection issue"

# Documentation
git commit -m "📝 Update README with installation guide"
git commit -m "📚 Add API documentation"

# Performance improvements
git commit -m "⚡ Optimize database queries"
git commit -m "🔥 Improve payment processing speed"

# UI/UX improvements
git commit -m "💄 Enhance admin dashboard design"
git commit -m "🎨 Improve responsive layout"

# Security updates
git commit -m "🔒 Add input validation"
git commit -m "🛡️ Implement rate limiting"

# Configuration changes
git commit -m "⚙️ Update environment variables"
git commit -m "🔧 Configure production settings"
```

## 🌿 Branching Strategy

### Branch Types

- **master**: Production-ready code
- **develop**: Development integration branch
- **feature/**: New features (`feature/payment-analytics`)
- **bugfix/**: Bug fixes (`bugfix/dashboard-error`)
- **hotfix/**: Critical production fixes (`hotfix/security-patch`)
- **enhancement/**: Improvements (`enhancement/ui-polish`)

### Example Workflow

```bash
# Start new feature
git checkout master
git pull origin master
git checkout -b feature/telegram-stars-integration

# Work on feature...
git add .
git commit -m "✨ Add Telegram Stars payment method"

# Merge back to master when ready
git checkout master
git merge feature/telegram-stars-integration
git branch -d feature/telegram-stars-integration
```

## 🔍 Checking Project Status

```bash
# See what files are tracked/ignored
git status
git ls-files

# Check ignored files
git status --ignored

# See file changes
git diff
git diff --name-only

# Check remote status (if using remote repo)
git remote -v
git fetch
git status
```

## 📦 Backup and Remote Repository

### Setting up Remote Repository

```bash
# Add remote repository (GitHub/GitLab)
git remote add origin https://github.com/username/nsfwbot.git

# Push to remote
git push -u origin master

# Pull from remote
git pull origin master

# Clone from remote (for new setup)
git clone https://github.com/username/nsfwbot.git
```

### Backup Strategies

```bash
# Create local backup
git bundle create nsfwbot-backup.bundle master

# Restore from backup
git clone nsfwbot-backup.bundle nsfwbot-restored

# Export specific version
git archive --format=zip --output=nsfwbot-v1.0.zip v1.0.0
```

## 🚨 Emergency Commands

```bash
# Undo all uncommitted changes
git checkout .
git clean -fd

# Restore specific file
git checkout HEAD -- filename.py

# Revert specific commit
git revert <commit-hash>

# Force reset to specific commit (DANGEROUS)
git reset --hard <commit-hash>

# Recover deleted branch
git reflog
git checkout -b recovered-branch <commit-hash>
```

## 📊 Project Statistics

```bash
# Count lines of code
git ls-files | xargs wc -l

# See contributor statistics
git shortlog -sn

# File change frequency
git log --pretty=format: --name-only | sort | uniq -c | sort -rg

# Project activity timeline
git log --pretty=format:"%h %ad %s" --date=short --graph
```

## 🔐 Security Best Practices

### What NOT to commit:
- `.env` files with real credentials
- Database files (`*.db`)
- API keys or passwords
- Personal configuration files
- Large binary files
- Temporary files

### Protected Files (already in .gitignore):
```
.env
*.db
__pycache__/
*.log
.vscode/
node_modules/
```

### Before Each Commit:
```bash
# Always check what you're committing
git diff --staged

# Verify no sensitive data
git show --name-only

# Check file permissions
git ls-files --stage
```

---

**Remember**: Git is your safety net! Commit early, commit often, and use descriptive messages. 🛡️