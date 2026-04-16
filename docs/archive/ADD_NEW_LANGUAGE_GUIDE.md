# Adding a New Language to the Bot

This guide walks you through extending the internationalization (i18n) system with a fresh locale. Follow the steps in order so the new language is fully wired into the bot, tests, and documentation.

---

## 1. Choose the Language Code and Name
- Pick a two-letter ISO 639-1 code (for example, `de` for German, `it` for Italian).
- Decide on the human-readable language name that will appear in menus.

Update `translations.py`:
1. Add the new entry to `TranslationManager.SUPPORTED_LANGUAGES`.
2. Keep keys sorted for readability.

```python
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'ar': 'العربية',
    # ... existing languages ...
    'de': 'Deutsch',   # ← example new entry
}
```

> 💡 The bot automatically loads a JSON file named after the code (for example, `languages/de.json`) when it exists.

---

## 2. Create the Translation File
1. Copy `languages/en.json` to `languages/<code>.json`.
2. Translate every value while keeping the keys and JSON structure identical.
3. Use UTF-8 encoding and escape sequences only when necessary.

Tips:
- Keep placeholders such as `{first_name}`, `{count}`, `{price}` unchanged.
- Preserve Markdown formatting and emoji—it affects message rendering.
- For right-to-left languages, ensure punctuation and emoji placement are correct.

---

## 3. Verify Completeness
Run a quick diff between the English file and the new file to ensure no keys are missing or extra:

```powershell
# Example for German
py -3 -m json.tool languages/en.json > en_pretty.json
py -3 -m json.tool languages/de.json > de_pretty.json
diff en_pretty.json de_pretty.json
```

Alternatively, use any JSON diff/validation tool you prefer.

---

## 4. Update Tests and Utilities
Several lightweight test scripts enumerate all supported languages. Search for language lists such as:
- `['en', 'ar', 'fa', 'tr', 'ru', 'es', 'zh']`

Update the lists in:
- `test_glass_menu_languages.py`
- `test_language_fixes.py`
- Any other scripts under `test_*.py` or docs that mention the language set

This keeps smoke tests and diagnostic scripts aware of the new locale.

---

## 5. Run the Test Suite
Before shipping, confirm nothing regressed:

```powershell
python -m pytest test_i18n_system.py
python -m pytest test_glass_menu_languages.py
python -m pytest test_language_fixes.py
```

If you added or updated referral/payment strings, run the focused suites as well:

```powershell
python -m pytest test_referral_system.py
python -m pytest test_payment_handler.py
```

---

## 6. Update Documentation
- Mention the new language in `I18N_DOCUMENTATION.md` and `README.md` if they list supported locales.
- If you created any helper tools/scripts for translators, document them in the relevant `*.MD` files.

---

## 7. Deploy Checklist
- [ ] `translations.py` includes the new language in `SUPPORTED_LANGUAGES`.
- [ ] `languages/<code>.json` exists and mirrors the English key structure.
- [ ] Tests referencing language lists are updated.
- [ ] `pytest` suites pass.
- [ ] Documentation reflects the new language.

Once the checklist is complete, commit the changes and push your branch:

```powershell
git add translations.py languages/<code>.json *.md tests/
git commit -m "Add <Language> localization"
git push
```

Your bot will now greet users in the new language as soon as the deployment picks up the updated branch. Enjoy the expanded reach! ✨
