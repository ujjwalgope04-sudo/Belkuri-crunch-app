# -*- coding: utf-8 -*-
"""
BELKURI CRUNCH - Offline News App
Built with Kivy (Python) for Android.

Features:
- Offline news feed with categories
- Admin Panel (PIN protected) to add/edit/delete news
- Business info page (editable from Admin Panel)
- Promotional banner on home screen + popup offer on app start

Run on desktop for testing:
    python main.py

Package to Android APK:
    buildozer android debug
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.metrics import dp

from news_data import CATEGORIES, get_articles_by_category
import storage

ADMIN_PIN = "1234"  # Change this to your own PIN

# ---------------------------------------------------------------------------
# COLOR PALETTE (Python side) — keep these in sync with the #:set values at
# the top of belkuricrunch.kv. These are only used for widgets built directly
# in Python (category chips, delete buttons, empty-state text) rather than
# defined in the .kv file.
# ---------------------------------------------------------------------------
COLOR_PRIMARY = (0.75, 0.10, 0.12, 1)
COLOR_ACCENT_GREEN = (0.15, 0.55, 0.25, 1)
COLOR_ACCENT_BLUE = (0.15, 0.45, 0.70, 1)
COLOR_CHIP_INACTIVE = (0.90, 0.90, 0.90, 1)
COLOR_WHITE = (1, 1, 1, 1)
COLOR_TEXT_DARK = (0.10, 0.10, 0.10, 1)
COLOR_TEXT_MUTED = (0.40, 0.40, 0.40, 1)


# ---------------- Splash ----------------

class Splash(Screen):
    pass


# ---------------- Article card widget ----------------

class ArticleCard(BoxLayout):
    title_text = StringProperty("")
    summary_text = StringProperty("")
    meta_text = StringProperty("")

    def __init__(self, article, on_press_callback, **kwargs):
        super().__init__(**kwargs)
        self.article = article
        self.title_text = article["title"]
        self.summary_text = article["summary"]
        self.meta_text = f'{article["category"]}  |  {article["date"]}'
        self.on_press_callback = on_press_callback
        self.bind(on_touch_up=self._check_touch)

    def _check_touch(self, instance, touch):
        if self.collide_point(*touch.pos):
            self.on_press_callback(self.article)
            return True
        return False


# ---------------- Home screen ----------------

class HomeScreen(Screen):
    current_category = StringProperty("Top News")

    def on_pre_enter(self, *args):
        if not self.ids.category_bar.children:
            self.build_categories()
        self.refresh_promo_banner()
        self.refresh_articles()

    def build_categories(self):
        self.ids.category_bar.clear_widgets()
        for cat in ["Top News"] + CATEGORIES[1:]:
            btn = Button(
                text=cat,
                size_hint=(None, None),
                height=36,
                width=max(90, len(cat) * 10),
                background_normal="",
                background_color=COLOR_PRIMARY if cat == self.current_category else COLOR_CHIP_INACTIVE,
                color=COLOR_WHITE if cat == self.current_category else COLOR_TEXT_DARK,
            )
            btn.bind(on_release=lambda instance, c=cat: self.select_category(c))
            self.ids.category_bar.add_widget(btn)

    def select_category(self, category):
        self.current_category = category
        self.build_categories()
        self.refresh_articles()

    def refresh_promo_banner(self):
        self.ids.promo_banner.clear_widgets()
        active_promos = [p for p in storage.get_promos() if p.get("active", True)]
        if not active_promos:
            self.ids.promo_banner.height = 0
            return
        promo = active_promos[0]
        self.ids.promo_banner.height = dp(48)
        label = Label(
            text=f'[b]{promo["title"]}:[/b] {promo["message"]}',
            markup=True,
            color=COLOR_WHITE,
            font_size="13sp",
            halign="left",
            valign="middle",
            text_size=(self.width - dp(20), None),
            shorten=True,
            shorten_from="right",
        )
        self.ids.promo_banner.add_widget(label)

    def refresh_articles(self):
        self.ids.article_list.clear_widgets()
        articles = get_articles_by_category(self.current_category)
        for article in articles:
            card = ArticleCard(article=article, on_press_callback=self.open_article)
            self.ids.article_list.add_widget(card)

    def open_article(self, article):
        app = App.get_running_app()
        app.root.get_screen("detail").load_article(article)
        app.root.current = "detail"

    def go_to_admin_gate(self):
        App.get_running_app().root.current = "admin_gate"

    def go_to_business_info(self):
        App.get_running_app().root.current = "business_info"


# ---------------- Article detail ----------------

class ArticleDetailScreen(Screen):
    def load_article(self, article):
        self.ids.detail_title.text = article["title"]
        self.ids.detail_meta.text = f'{article["category"]}  |  {article["date"]}'
        self.ids.detail_content.text = article["content"]

    def go_back(self):
        App.get_running_app().root.current = "home"


# ---------------- Admin PIN gate ----------------

class AdminGateScreen(Screen):
    def check_pin(self):
        entered = self.ids.pin_input.text.strip()
        self.ids.pin_input.text = ""
        if entered == ADMIN_PIN:
            self.ids.pin_error.text = ""
            App.get_running_app().root.current = "admin"
        else:
            self.ids.pin_error.text = "Wrong PIN. Try again."

    def cancel(self):
        App.get_running_app().root.current = "home"


# ---------------- Admin panel (manage news + promos) ----------------

class AdminRow(BoxLayout):
    def __init__(self, label_text, on_edit, on_delete, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(44),
                          spacing=dp(6), padding=(dp(6), 0), **kwargs)
        lbl = Label(text=label_text, halign="left", valign="middle", color=COLOR_TEXT_DARK)
        lbl.bind(size=lambda i, v: setattr(i, "text_size", v))
        self.add_widget(lbl)
        if on_edit:
            edit_btn = Button(text="Edit", size_hint=(None, None), width=dp(60), height=dp(32))
            edit_btn.bind(on_release=lambda i: on_edit())
            self.add_widget(edit_btn)
        del_btn = Button(text="Delete", size_hint=(None, None), width=dp(70), height=dp(32),
                          background_color=COLOR_PRIMARY)
        del_btn.bind(on_release=lambda i: on_delete())
        self.add_widget(del_btn)


class AdminScreen(Screen):
    def on_pre_enter(self, *args):
        self.refresh_articles()
        self.refresh_promos()

    def refresh_articles(self):
        self.ids.admin_article_list.clear_widgets()
        custom = storage.get_custom_articles()
        if not custom:
            self.ids.admin_article_list.add_widget(
                Label(text="No custom articles yet. Tap 'Add News' below.",
                      size_hint_y=None, height=dp(36), color=COLOR_TEXT_MUTED)
            )
        for article in custom:
            row = AdminRow(
                label_text=article["title"],
                on_edit=lambda a=article: self.edit_article(a),
                on_delete=lambda a=article: self.delete_article(a),
            )
            self.ids.admin_article_list.add_widget(row)

    def refresh_promos(self):
        self.ids.admin_promo_list.clear_widgets()
        promos = storage.get_promos()
        if not promos:
            self.ids.admin_promo_list.add_widget(
                Label(text="No promotional offers yet.",
                      size_hint_y=None, height=dp(36), color=COLOR_TEXT_MUTED)
            )
        for promo in promos:
            status = "ON" if promo.get("active", True) else "OFF"
            row = AdminRow(
                label_text=f'{promo["title"]} ({status})',
                on_edit=None,
                on_delete=lambda p=promo: self.delete_promo(p),
            )
            self.ids.admin_promo_list.add_widget(row)

    def add_article(self):
        App.get_running_app().root.get_screen("add_article").load_for_new()
        App.get_running_app().root.current = "add_article"

    def edit_article(self, article):
        App.get_running_app().root.get_screen("add_article").load_for_edit(article)
        App.get_running_app().root.current = "add_article"

    def delete_article(self, article):
        storage.delete_custom_article(article["id"])
        self.refresh_articles()

    def add_promo(self):
        App.get_running_app().root.get_screen("add_promo").load_for_new()
        App.get_running_app().root.current = "add_promo"

    def delete_promo(self, promo):
        storage.delete_promo(promo["id"])
        self.refresh_promos()

    def go_business_info(self):
        App.get_running_app().root.current = "business_info"

    def go_back(self):
        App.get_running_app().root.current = "home"


# ---------------- Add / edit article form ----------------

class AddArticleScreen(Screen):
    editing_id = None

    def load_for_new(self):
        self.editing_id = None
        self.ids.title_input.text = ""
        self.ids.category_input.text = CATEGORIES[1] if len(CATEGORIES) > 1 else "Top News"
        self.ids.summary_input.text = ""
        self.ids.content_input.text = ""
        self.ids.form_error.text = ""

    def load_for_edit(self, article):
        self.editing_id = article["id"]
        self.ids.title_input.text = article["title"]
        self.ids.category_input.text = article["category"]
        self.ids.summary_input.text = article["summary"]
        self.ids.content_input.text = article["content"]
        self.ids.form_error.text = ""

    def save(self):
        from datetime import date as _date
        title = self.ids.title_input.text.strip()
        category = self.ids.category_input.text.strip() or "Top News"
        summary = self.ids.summary_input.text.strip()
        content = self.ids.content_input.text.strip()
        if not title or not content:
            self.ids.form_error.text = "Title and content are required."
            return
        today = _date.today().strftime("%d %b %Y")
        if self.editing_id:
            storage.update_custom_article(self.editing_id, title, category, summary, content, today)
        else:
            storage.add_custom_article(title, category, summary, content, today)
        App.get_running_app().root.current = "admin"

    def cancel(self):
        App.get_running_app().root.current = "admin"


# ---------------- Add promo form ----------------

class AddPromoScreen(Screen):
    def load_for_new(self):
        self.ids.promo_title_input.text = ""
        self.ids.promo_message_input.text = ""
        self.ids.promo_form_error.text = ""

    def save(self):
        title = self.ids.promo_title_input.text.strip()
        message = self.ids.promo_message_input.text.strip()
        if not title or not message:
            self.ids.promo_form_error.text = "Title and message are required."
            return
        storage.add_promo(title, message, active=True)
        App.get_running_app().root.current = "admin"

    def cancel(self):
        App.get_running_app().root.current = "admin"


# ---------------- Business info screen ----------------

class BusinessInfoScreen(Screen):
    def on_pre_enter(self, *args):
        info = storage.get_business_info()
        self.ids.biz_name.text = info["name"]
        self.ids.biz_about.text = info["about"]
        self.ids.biz_phone.text = info["phone"]
        self.ids.biz_email.text = info["email"]
        self.ids.biz_address.text = info["address"]
        self.set_editable(False)

    def set_editable(self, editable):
        for field in (self.ids.biz_name, self.ids.biz_about, self.ids.biz_phone,
                      self.ids.biz_email, self.ids.biz_address):
            field.disabled = not editable
        self.ids.edit_btn.opacity = 0 if editable else 1
        self.ids.edit_btn.disabled = editable
        self.ids.save_btn.opacity = 1 if editable else 0
        self.ids.save_btn.disabled = not editable

    def enable_edit(self):
        self.set_editable(True)

    def save(self):
        storage.save_business_info(
            self.ids.biz_name.text.strip(),
            self.ids.biz_about.text.strip(),
            self.ids.biz_phone.text.strip(),
            self.ids.biz_email.text.strip(),
            self.ids.biz_address.text.strip(),
        )
        self.set_editable(False)

    def go_back(self):
        App.get_running_app().root.current = "home"


# ---------------- App ----------------

class BelkuriCrunchApp(App):
    def build(self):
        self.title = "BELKURI CRUNCH"
        storage.seed_default_promo_if_empty()
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(Splash(name="splash"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(ArticleDetailScreen(name="detail"))
        sm.add_widget(AdminGateScreen(name="admin_gate"))
        sm.add_widget(AdminScreen(name="admin"))
        sm.add_widget(AddArticleScreen(name="add_article"))
        sm.add_widget(AddPromoScreen(name="add_promo"))
        sm.add_widget(BusinessInfoScreen(name="business_info"))
        Clock.schedule_once(lambda dt: self.go_home(sm), 2)
        return sm

    def go_home(self, sm):
        sm.current = "home"
        self.show_promo_popup()

    def show_promo_popup(self):
        active_promos = [p for p in storage.get_promos() if p.get("active", True)]
        if not active_promos:
            return
        promo = active_promos[0]
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(16))
        msg = Label(text=f'[b]{promo["title"]}[/b]\n\n{promo["message"]}', markup=True,
                    halign="center", valign="middle")
        msg.bind(size=lambda i, v: setattr(i, "text_size", v))
        content.add_widget(msg)
        close_btn = Button(text="Close", size_hint=(1, None), height=dp(44),
                            background_color=COLOR_PRIMARY)
        content.add_widget(close_btn)
        popup = Popup(title="Special Offer", content=content, size_hint=(0.85, 0.5))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    BelkuriCrunchApp().run()
