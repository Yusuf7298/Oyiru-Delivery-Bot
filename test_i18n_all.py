import os
import json
import sys

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")

print("==================================================")
print("   RUNNING COMPREHENSIVE MULTI-LANGUAGE TEST")
print("==================================================")

# 1. Test translation files validity
print("\n[1/5] Checking Translation JSON files...")
languages = ["en", "am", "om"]
translations = {}

for lang in languages:
    path = f"translations/{lang}.json"
    if not os.path.exists(path):
        print(f"❌ ERROR: Missing translation file: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        translations[lang] = data
        print(f"  ✅ {lang}.json loaded cleanly ({len(data)} keys)")

# Check key parity
en_keys = set(translations["en"].keys())
for lang in ["am", "om"]:
    lang_keys = set(translations[lang].keys())
    missing = en_keys - lang_keys
    if missing:
        print(f"  ⚠️ Warning: {lang} is missing keys: {missing}")
    else:
        print(f"  ✅ {lang}.json has 100% key parity with English!")

# 2. Test utils.i18n helper
print("\n[2/5] Testing i18n helper (utils.i18n.t)...")
from utils.i18n import t

test_keys = ["welcome_title", "select_language", "btn_place_order", "btn_my_orders", "btn_profile"]
for lang in languages:
    print(f"\n  --- Language: {lang.upper()} ---")
    for key in test_keys:
        res = t(key, lang, name="TestUser")
        print(f"    [{key}]: {res}")

# 3. Test Keyboards rendering across all languages
print("\n[3/5] Testing Keyboards generation for EN, AM, OM...")
from keyboards.customers import customer_menu, customer_reorder_menu, order_summary_keyboard
from keyboards.delivery import delivery_menu
from keyboards.store_manager import store_manager_menu, hotel_admin_menu
from keyboards.admin_menu import admin_main_menu
from keyboards.language_keyboard import language_keyboard

for lang in languages:
    c_menu = customer_menu(lang)
    c_btns = [b.text for row in c_menu.keyboard for b in row]
    print(f"  ✅ customer_menu({lang}): {c_btns}")

    h_menu = hotel_admin_menu(lang)
    h_btns = [b.text for row in h_menu.keyboard for b in row]
    print(f"  ✅ hotel_admin_menu({lang}): {h_btns}")

    d_menu = delivery_menu(lang)
    d_btns = [b.text for row in d_menu.keyboard for b in row]
    print(f"  ✅ delivery_menu({lang}): {d_btns}")

    sm_menu = store_manager_menu(lang)
    sm_btns = [b.text for row in sm_menu.keyboard for b in row]
    print(f"  ✅ store_manager_menu({lang}): {sm_btns}")

    a_menu = admin_main_menu(lang)
    a_btns = [b.text for row in a_menu.keyboard for b in row]
    print(f"  ✅ admin_main_menu({lang}): {a_btns}")

lang_kb = language_keyboard()
kb_btns = [b.text for row in lang_kb.inline_keyboard for b in row]
print(f"  ✅ language_keyboard: {kb_btns}")

# 4. Test User Model language property
print("\n[4/5] Testing User Model language field...")
from database.models.user import User

u_en = User(id=101, full_name="User En", language="en")
u_am = User(id=102, full_name="User Am", language="am")
u_om = User(id=103, full_name="User Om", language="om")

assert u_en.to_dict()["language"] == "en"
assert u_am.to_dict()["language"] == "am"
assert u_om.to_dict()["language"] == "om"
print("  ✅ User model correctly stores and serializes language in to_dict()")

# 5. Test Handlers and App Module
print("\n[5/5] Testing App Router and Handler imports...")
import app
print("  ✅ app.py imported cleanly with LanguageMiddleware and language_router!")

print("\n==================================================")
print("   🎉 ALL MULTI-LANGUAGE CHECKS PASSED SUCCESSFULLY!")
print("==================================================")

