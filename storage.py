# -*- coding: utf-8 -*-
"""
Persistent offline storage for BELKURI CRUNCH.
Uses Kivy's JsonStore so data added via the Admin Panel survives app restarts,
without needing internet or a database server.
"""

import os
import time
from kivy.storage.jsonstore import JsonStore
from kivy.app import App


def _store_path(filename):
    app = App.get_running_app()
    if app is not None:
        base = app.user_data_dir
    else:
        base = "."
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, filename)


def _get_store(filename):
    return JsonStore(_store_path(filename))


# ---------- Custom (admin-added) news articles ----------

def get_custom_articles():
    store = _get_store("custom_articles.json")
    articles = []
    for key in store.keys():
        data = store.get(key)
        data["id"] = key
        articles.append(data)
    articles.sort(key=lambda a: a.get("timestamp", 0), reverse=True)
    return articles


def add_custom_article(title, category, summary, content, date):
    store = _get_store("custom_articles.json")
    article_id = f"custom_{int(time.time() * 1000)}"
    store.put(
        article_id,
        title=title,
        category=category,
        summary=summary,
        content=content,
        date=date,
        timestamp=time.time(),
    )
    return article_id


def update_custom_article(article_id, title, category, summary, content, date):
    store = _get_store("custom_articles.json")
    if store.exists(article_id):
        old = store.get(article_id)
        store.put(
            article_id,
            title=title,
            category=category,
            summary=summary,
            content=content,
            date=date,
            timestamp=old.get("timestamp", time.time()),
        )


def delete_custom_article(article_id):
    store = _get_store("custom_articles.json")
    if store.exists(article_id):
        store.delete(article_id)


# ---------- Promotional offers ----------

def get_promos():
    store = _get_store("promos.json")
    promos = []
    for key in store.keys():
        data = store.get(key)
        data["id"] = key
        promos.append(data)
    promos.sort(key=lambda p: p.get("timestamp", 0))
    return promos


def add_promo(title, message, active=True):
    store = _get_store("promos.json")
    promo_id = f"promo_{int(time.time() * 1000)}"
    store.put(promo_id, title=title, message=message, active=active, timestamp=time.time())
    return promo_id


def delete_promo(promo_id):
    store = _get_store("promos.json")
    if store.exists(promo_id):
        store.delete(promo_id)


def seed_default_promo_if_empty():
    """Add one starter promo the first time the app runs, so the banner/popup
    isn't empty before the owner adds their own."""
    store = _get_store("promos.json")
    if len(store.keys()) == 0:
        add_promo(
            title="Welcome Offer",
            message="Thanks for using Belkuri Crunch! Advertise your business here — contact us to add your offer.",
            active=True,
        )


# ---------- Business info (editable from Admin Panel) ----------

def get_business_info():
    store = _get_store("business_info.json")
    if store.exists("info"):
        return store.get("info")
    default = {
        "name": "BELKURI CRUNCH",
        "about": "Your trusted local news source, straight from Belkuri.",
        "phone": "+91 00000 00000",
        "email": "contact@belkuricrunch.com",
        "address": "Belkuri, India",
    }
    store.put("info", **default)
    return default


def save_business_info(name, about, phone, email, address):
    store = _get_store("business_info.json")
    store.put("info", name=name, about=about, phone=phone, email=email, address=address)
