import sys
import math
import os
import json
from urllib.parse import quote_plus, urlsplit
import gi

# Requerir versiones específicas antes de importar
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('WebKit2', '4.1')

from gi.repository import Gdk, GLib, GObject, Gtk, Pango, WebKit2


class BrowserApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Kordex Browser")
        self.set_default_size(1400, 900)
        self.connect("destroy", self.on_destroy)

        self.tab_pages = []
        self.active_tab_index = 0
        self.bookmarks = []
        self.max_single_column_tabs = 6
        self.current_theme = "black"
        self.line_only = False
        self.current_language = "es-es"
        self.search_engine = "brave"
        self.search_engines = {
            "duckduckgo": "https://duckduckgo.com/?q=",
            "brave": "https://search.brave.com/search?q=",
            "google": "https://www.google.com/search?q=",
            "bing": "https://www.bing.com/search?q=",
        }
        self.search_homepages = {
            "duckduckgo": "https://duckduckgo.com/",
            "brave": "https://search.brave.com/",
            "google": "https://www.google.com/",
            "bing": "https://www.bing.com/",
        }
        self.os_name = self.read_os_release()
        self.adblock_enabled = True
        self.volatile_storage = False
        self.theme_provider = None
        self.profile_path = os.path.expanduser("~/.local/share/kordex-browser/profiles/default")
        self.profile_data_path = os.path.join(self.profile_path, "data")
        self.profile_cache_path = os.path.join(self.profile_path, "cache")
        os.makedirs(self.profile_data_path, exist_ok=True)
        os.makedirs(self.profile_cache_path, exist_ok=True)
        self.website_data_manager = GObject.new(
            WebKit2.WebsiteDataManager,
            base_data_directory=self.profile_data_path,
            base_cache_directory=self.profile_cache_path,
        )
        self.web_context = WebKit2.WebContext.new_with_website_data_manager(
            self.website_data_manager
        )
        self.web_context.connect("download-started", self.on_download_started)
        self.cookie_manager = self.web_context.get_cookie_manager()
        self.cookie_manager.set_persistent_storage(
            os.path.join(self.profile_data_path, "cookies.sqlite"),
            WebKit2.CookiePersistentStorage.SQLITE,
        )
        self.adblock_filter = None
        self.adblock_style_sheet = None
        self.adblock_script = None
        self.preferences_path = os.path.expanduser(
            "~/.config/kordex-browser/preferences.json"
        )
        self.legacy_preferences_path = os.path.expanduser(
            "~/.config/navegador-tiling/preferences.json"
        )
        self.language_texts = {
            "es-es": {"settings": "Configuración", "general": "Colores", "colors": "Colores", "lines": "Solo líneas", "language": "Idioma", "history": "Historial", "history_title": "Historial de navegación", "bookmarks": "Marcadores", "add_bookmark": "Añadir marcador", "delete_bookmark": "Eliminar", "paste_url": "Pega la URL", "add": "Añadir", "cancel": "Cancelar", "new_tab": "Nueva pestaña", "window_title": "Kordex Browser", "line_description": "Usa únicamente líneas y bordes del color escogido sobre fondo negro.", "adblock": "Bloqueador de anuncios", "adblock_description": "Bloquea anuncios, rastreadores y solicitudes publicitarias antes de que se carguen, ayudando a mejorar la privacidad y el rendimiento.", "version": "Versión", "beta": "Beta 2", "based_on": "Basado en WebKit mediante WebKitGTK.", "search": "Búsqueda"},
            "es-mx": {"settings": "Configuración", "general": "Colores", "colors": "Colores", "lines": "Solo líneas", "language": "Idioma", "history": "Historial", "history_title": "Historial de navegación", "bookmarks": "Marcadores", "add_bookmark": "Añadir marcador", "delete_bookmark": "Eliminar", "paste_url": "Pega la URL", "add": "Añadir", "cancel": "Cancelar", "new_tab": "Nueva pestaña", "window_title": "Kordex Browser", "line_description": "Usa únicamente líneas y bordes del color escogido sobre fondo negro.", "adblock": "Bloqueador de anuncios", "adblock_description": "Bloquea anuncios, rastreadores y solicitudes publicitarias antes de que se carguen, ayudando a mejorar la privacidad y el rendimiento.", "version": "Versión", "beta": "Beta 2", "based_on": "Basado en WebKit mediante WebKitGTK.", "search": "Búsqueda"},
            "en-uk": {"settings": "Settings", "general": "Colours", "colors": "Colours", "lines": "Lines only", "language": "Language", "history": "History", "history_title": "Browsing history", "bookmarks": "Bookmarks", "add_bookmark": "Add bookmark", "paste_url": "Paste the URL", "add": "Add", "cancel": "Cancel", "new_tab": "New tab", "window_title": "Kordex Browser", "line_description": "Use only lines and borders in the selected colour on a black background.", "adblock": "Ad blocker", "adblock_description": "Blocks adverts, trackers and advertising requests before they load, helping improve privacy and performance.", "version": "Version", "beta": "Beta 2", "based_on": "Built on WebKit through WebKitGTK."},
            "en-us": {"settings": "Settings", "general": "Colors", "colors": "Colors", "lines": "Lines only", "language": "Language", "history": "History", "history_title": "Browsing history", "bookmarks": "Bookmarks", "add_bookmark": "Add bookmark", "paste_url": "Paste the URL", "add": "Add", "cancel": "Cancel", "new_tab": "New tab", "window_title": "Kordex Browser", "line_description": "Use only lines and borders in the selected color on a black background.", "adblock": "Ad blocker", "adblock_description": "Blocks ads, trackers and advertising requests before they load, helping improve privacy and performance.", "version": "Version", "beta": "Beta 2", "based_on": "Built on WebKit through WebKitGTK."},
            "ru": {"settings": "Настройки", "general": "Цвета", "colors": "Цвета", "lines": "Только линии", "language": "Язык", "history": "История", "history_title": "История просмотров", "bookmarks": "Закладки", "add_bookmark": "Добавить закладку", "paste_url": "Вставьте URL", "add": "Добавить", "cancel": "Отмена", "new_tab": "Новая вкладка", "window_title": "Kordex Browser", "line_description": "Использовать только линии и границы выбранного цвета на черном фоне.", "adblock": "Блокировщик рекламы", "adblock_description": "Блокирует рекламу, трекеры и рекламные запросы до их загрузки, повышая конфиденциальность и производительность.", "version": "Версия", "beta": "Бета 2", "based_on": "Работает на WebKit через WebKitGTK."},
            "zh": {"settings": "设置", "general": "颜色", "colors": "颜色", "lines": "仅线条", "language": "语言", "history": "历史记录", "history_title": "浏览历史", "bookmarks": "书签", "add_bookmark": "添加书签", "paste_url": "粘贴网址", "add": "添加", "cancel": "取消", "new_tab": "新标签页", "window_title": "Kordex Browser", "line_description": "仅使用所选颜色绘制黑色背景上的线条和边框。", "adblock": "广告拦截器", "adblock_description": "在广告、跟踪器和广告请求加载之前将其拦截，帮助提升隐私和性能。", "version": "版本", "beta": "测试版 2", "based_on": "基于 WebKitGTK 的 WebKit。"},
        }
        self.theme_colors = {
            "black": ("#000000", "#121212", "#242424", "#f3f3f3", "#8f8f8f"),
            "green": ("#07140d", "#0d2417", "#153522", "#eafff0", "#63d98a"),
            "blue": ("#07111f", "#0d1d33", "#17385f", "#edf5ff", "#70b7ff"),
            "white": ("#e9edf2", "#ffffff", "#f5f6f8", "#15171a", "#3578d4"),
            "pink": ("#1d0b15", "#321326", "#54203e", "#fff0f7", "#ff82bd"),
            "purple": ("#130b20", "#211233", "#38205a", "#f7efff", "#bd8cff"),
            "mex": ("#07140d", "#10261b", "#1d3a29", "#f3fff7", "#ce1126"),
        }
        self.load_preferences()
        self.set_title(self.tr("window_title"))

        self.set_name("browser-window")
        self.apply_glass_style()
        self.apply_theme_style()
        self.install_adblock_filter()
        self.install_adblock_style()
        self.install_adblock_script()

        main_hbox = Gtk.HBox(spacing=0)
        self.add(main_hbox)

        # Area fija de pestañas; el contenido cambia entre lista y mosaico.
        self.tab_bar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.tab_bar.set_name("tab-bar")
        self.tab_bar.set_size_request(155, -1)
        self.tab_bar.set_border_width(3)
        main_hbox.pack_start(self.tab_bar, False, False, 0)

        scrolled_tabs = Gtk.ScrolledWindow()
        scrolled_tabs.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.tab_bar.pack_start(scrolled_tabs, True, True, 0)

        self.tab_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.tab_container.set_name("tab-container")
        self.tab_container.set_border_width(3)
        self.tab_grid = Gtk.Grid()
        self.tab_grid.set_name("tab-grid")
        self.tab_grid.set_row_spacing(3)
        self.tab_grid.set_column_spacing(3)
        self.tab_grid.set_border_width(3)

        self.tab_layout = Gtk.Stack()
        self.tab_layout.add_named(self.tab_container, "list")
        self.tab_layout.add_named(self.tab_grid, "grid")
        scrolled_tabs.add(self.tab_layout)

        self.content_box = Gtk.VBox(spacing=5)
        self.content_box.set_name("content-box")
        main_hbox.pack_start(self.content_box, True, True, 0)

        self.nav_bar = Gtk.HBox(spacing=5)
        self.nav_bar.set_name("nav-bar")
        self.content_box.pack_start(self.nav_bar, False, False, 5)

        self.btn_back = Gtk.Button(label="←")
        self.btn_back.connect("clicked", self.on_back_clicked)
        self.nav_bar.pack_start(self.btn_back, False, False, 2)

        self.btn_forward = Gtk.Button(label="→")
        self.btn_forward.connect("clicked", self.on_forward_clicked)
        self.nav_bar.pack_start(self.btn_forward, False, False, 2)

        self.btn_refresh = Gtk.Button(label="↻")
        self.btn_refresh.connect("clicked", self.on_refresh_clicked)
        self.nav_bar.pack_start(self.btn_refresh, False, False, 2)

        self.btn_new_tab = Gtk.Button(label="＋")
        self.btn_new_tab.connect("clicked", self.on_new_tab_clicked)
        self.nav_bar.pack_start(self.btn_new_tab, False, False, 2)

        self.url_entry = Gtk.Entry()
        self.url_entry.connect("activate", self.on_url_activate)
        self.nav_bar.pack_start(self.url_entry, True, True, 2)

        self.search_button = Gtk.Button(label="⌕")
        self.search_button.set_tooltip_text("Buscar")
        self.search_button.connect("clicked", self.on_search_button_clicked)
        self.nav_bar.pack_start(self.search_button, False, False, 2)

        self.download_button = Gtk.Button(label="Descargas")
        self.download_button.set_tooltip_text("Ver descargas")
        self.download_button.connect("clicked", self.on_downloads_clicked)
        self.nav_bar.pack_start(self.download_button, False, False, 2)

        self.more_button = Gtk.Button(label="⋮")
        self.more_button.set_name("more-button")
        self.more_button.connect("clicked", self.on_more_clicked)
        self.tab_bar.pack_end(self.more_button, False, False, 0)

        self.downloads = []
        self.downloads_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.downloads_panel.set_name("downloads-panel")
        self.downloads_panel.set_border_width(8)
        self.downloads_revealer = Gtk.Revealer()
        self.downloads_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.downloads_revealer.add(self.downloads_panel)
        self.downloads_panel_open = False
        self.content_box.pack_start(self.downloads_revealer, False, False, 0)

        self.stack = Gtk.Stack()
        self.content_box.pack_start(self.stack, True, True, 0)

        self.add_new_tab(self.search_homepages[self.search_engine])
        self.url_entry.set_placeholder_text("Buscar con " + self.get_search_engine_label())
        self.update_navigation_state()

    def tr(self, key):
        return self.language_texts[self.current_language].get(key, key)

    def load_preferences(self):
        try:
            preferences_path = self.preferences_path
            if not os.path.exists(preferences_path):
                preferences_path = self.legacy_preferences_path
            with open(preferences_path, "r", encoding="utf-8") as preferences_file:
                preferences = json.load(preferences_file)
        except (OSError, ValueError):
            return

        self.bookmarks = preferences.get("bookmarks", [])
        self.current_theme = preferences.get("theme", self.current_theme)
        self.current_language = preferences.get("language", self.current_language)
        self.search_engine = preferences.get("search_engine", self.search_engine)
        self.line_only = preferences.get("line_only", self.line_only)
        self.adblock_enabled = preferences.get("adblock_enabled", self.adblock_enabled)
        self.volatile_storage = preferences.get("volatile_storage", self.volatile_storage)

        if self.current_theme not in self.theme_colors:
            self.current_theme = "black"
        if self.current_language not in self.language_texts:
            self.current_language = "es-es"
        if self.search_engine not in self.search_engines:
            self.search_engine = "brave"

    def save_preferences(self):
        preferences_dir = os.path.dirname(self.preferences_path)
        os.makedirs(preferences_dir, exist_ok=True)
        preferences = {
            "bookmarks": self.bookmarks,
            "theme": self.current_theme,
            "language": self.current_language,
            "search_engine": self.search_engine,
            "line_only": self.line_only,
            "adblock_enabled": self.adblock_enabled,
            "volatile_storage": self.volatile_storage,
        }
        with open(self.preferences_path, "w", encoding="utf-8") as preferences_file:
            json.dump(preferences, preferences_file, ensure_ascii=False, indent=2)

    def on_destroy(self, window):
        self.save_preferences()
        if self.volatile_storage:
            self.website_data_manager.clear(
                WebKit2.WebsiteDataTypes.ALL,
                0,
                None,
                self.on_volatile_data_cleared,
            )
            return
        Gtk.main_quit()

    def on_volatile_data_cleared(self, manager, result):
        try:
            manager.clear_finish(result)
        except GLib.Error:
            pass
        Gtk.main_quit()

    def read_os_release(self):
        values = {}
        try:
            with open("/etc/os-release", "r", encoding="utf-8") as os_release:
                for line in os_release:
                    key, separator, value = line.partition("=")
                    if separator:
                        values[key.strip()] = value.strip().strip('"')
        except OSError:
            return "Linux"
        return values.get("PRETTY_NAME") or values.get("NAME") or "Linux"

    def get_operating_system_label(self):
        return {
            "en-uk": "Operating system",
            "en-us": "Operating system",
            "ru": "Операционная система",
            "zh": "操作系统",
        }.get(self.current_language, "Sistema operativo")

    def install_adblock_filter(self):
        filter_path = os.path.expanduser("~/.cache/kordex-browser/filters")
        os.makedirs(filter_path, exist_ok=True)
        store = WebKit2.UserContentFilterStore.new(filter_path)
        third_party_patterns = [
            "adservice", "doubleclick", "googlesyndication", "googleadservices",
            "adnxs", "adsystem", "advertising", "popunder", "prebid", "outstream", "vast",
        ]
        tracker_patterns = [
            "google-analytics.com", "googletagmanager.com", "hotjar.com", "clarity.ms",
            "segment.io", "fullstory.com", "mouseflow.com", "mixpanel.com",
            "amplitude.com", "facebook.com/tr", "connect.facebook.net", "bat.bing.com",
            "mc.yandex.ru", "an.yandex.ru",
        ]
        path_patterns = [
            "/advert", "/banner", "/sponsor", "/prebid", "/vast", "/outstream",
        ]
        youtube_patterns = [
            "youtube.com/pagead", "youtube.com/api/stats/ads",
            "youtube.com/ptracking", "youtube.com/get_midroll_info",
            "googlevideo.com/videoplayback.*adformat",
        ]
        rules = []
        for pattern in third_party_patterns:
            rules.append({
                "trigger": {"url-filter": pattern, "url-filter-is-case-sensitive": False, "load-type": ["third-party"]},
                "action": {"type": "block"},
            })
        for pattern in tracker_patterns:
            rules.append({
                "trigger": {"url-filter": pattern, "url-filter-is-case-sensitive": False},
                "action": {"type": "block"},
            })
        for pattern in path_patterns:
            rules.append({
                "trigger": {"url-filter": pattern, "url-filter-is-case-sensitive": False, "resource-type": ["script", "image", "media", "raw", "style-sheet"]},
                "action": {"type": "block"},
            })
        for pattern in youtube_patterns:
            rules.append({
                "trigger": {"url-filter": pattern, "url-filter-is-case-sensitive": False},
                "action": {"type": "block"},
            })
        for pattern in [
            "adblock-tester.com/banners/",
            "pr_advertising_ads_banner.gif",
            "pr_advertising_ads_banner.png",
        ]:
            rules.append({
                "trigger": {"url-filter": pattern, "url-filter-is-case-sensitive": False},
                "action": {"type": "block"},
            })
        source = GLib.Bytes.new(json.dumps(rules).encode())
        store.save("default-adblock-v3", source, None, self.on_adblock_saved, None)

    def on_adblock_saved(self, store, result, user_data):
        try:
            self.adblock_filter = store.save_finish(result)
            if self.adblock_enabled:
                for item in self.tab_pages:
                    if item.get("web_view") is not None:
                        item["web_view"].get_user_content_manager().add_filter(
                            self.adblock_filter
                        )
                        item["web_view"].reload()
        except GLib.Error:
            self.adblock_filter = None

    def configure_web_view(self, web_view):
        user_content_manager = web_view.get_user_content_manager()
        if self.adblock_filter is not None:
            user_content_manager.add_filter(self.adblock_filter)
        if self.adblock_style_sheet is not None:
            user_content_manager.add_style_sheet(self.adblock_style_sheet)
        if self.adblock_script is not None:
            user_content_manager.add_script(self.adblock_script)

    def on_downloads_clicked(self, button):
        self.downloads_panel_open = not self.downloads_panel_open
        self.downloads_revealer.set_reveal_child(self.downloads_panel_open)
        self.refresh_downloads_panel()

    def on_download_started(self, web_context, download):
        self.downloads.append({
            "download": download,
            "row": None,
            "status": "Descargando",
        })
        download.connect("decide-destination", self.on_download_decide_destination)
        download.connect("notify::received-data-length", self.on_download_status_changed)
        download.connect("finished", self.on_download_finished)
        download.connect("failed", self.on_download_failed)
        self.set_download_destination(download)
        self.downloads_panel_open = True
        self.downloads_revealer.set_reveal_child(True)
        self.refresh_downloads_panel()

    def on_download_decide_destination(self, download, suggested_filename):
        self.set_download_destination(download, suggested_filename)
        return True

    def set_download_destination(self, download, suggested_filename=None):
        download_directory = os.path.expanduser("~/Downloads")
        if not os.path.isdir(download_directory):
            download_directory = os.path.expanduser("~/Descargas")
        os.makedirs(download_directory, exist_ok=True)

        if not suggested_filename:
            request = download.get_request()
            uri = request.get_uri() if request is not None else ""
            suggested_filename = os.path.basename(uri.split("?", 1)[0].rstrip("/"))
        filename = os.path.basename(suggested_filename or "descarga")
        destination = os.path.join(download_directory, filename)
        base, extension = os.path.splitext(filename)
        counter = 1
        while os.path.exists(destination):
            destination = os.path.join(
                download_directory, f"{base} ({counter}){extension}"
            )
            counter += 1
        download.set_allow_overwrite(True)
        download.set_destination(GLib.filename_to_uri(destination, None))

    def on_download_status_changed(self, download, *args):
        self.refresh_downloads_panel()

    def on_download_finished(self, download, *args):
        self.set_download_status(download, "Completada")

    def on_download_failed(self, download, *args):
        self.set_download_status(download, "Error")

    def set_download_status(self, download, status):
        for item in self.downloads:
            if item["download"] is download:
                item["status"] = status
                break
        self.refresh_downloads_panel()

    def refresh_downloads_panel(self):
        for child in list(self.downloads_panel.get_children()):
            self.downloads_panel.remove(child)

        title = Gtk.Label(label="Descargas")
        title.set_xalign(0.0)
        self.downloads_panel.pack_start(title, False, False, 0)

        if not self.downloads:
            empty_label = Gtk.Label(label="No hay descargas")
            empty_label.set_xalign(0.0)
            self.downloads_panel.pack_start(empty_label, False, False, 0)
        else:
            for item in self.downloads:
                self.add_download_row(item)
        self.downloads_panel.show_all()

    def add_download_row(self, item):
        download = item["download"]
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        row.set_name("download-row")

        request = download.get_request()
        uri = request.get_uri() if request is not None else ""
        filename = os.path.basename(uri.split("?", 1)[0].rstrip("/")) or "Descarga"
        name_label = Gtk.Label(label=filename)
        name_label.set_xalign(0.0)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.set_single_line_mode(True)
        row.pack_start(name_label, False, False, 0)

        status_label = Gtk.Label(label=self.get_download_status_label(item))
        status_label.set_xalign(0.0)
        row.pack_start(status_label, False, False, 0)

        progress = Gtk.ProgressBar()
        progress.set_fraction(max(0.0, min(1.0, download.get_estimated_progress())))
        row.pack_start(progress, False, False, 0)

        item["row"] = row
        self.downloads_panel.pack_start(row, False, False, 0)

    def get_download_status_label(self, item):
        download = item["download"]
        label = item["status"]
        if label == "Descargando":
            received = download.get_received_data_length()
            label = f"{label} ({self.format_download_size(received)})"
        return label

    def format_download_size(self, size):
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"

    def install_adblock_style(self):
        css = """
        ytd-display-ad-renderer,
        ytd-promoted-sparkles-web-renderer,
        ytd-ad-slot-renderer,
        ytd-in-feed-ad-layout-renderer,
        ytd-banner-promo-renderer,
        ytd-statement-banner-renderer,
        ytd-action-companion-ad-renderer,
        #player-ads,
        #masthead-ad,
        .video-ads,
        .ytp-ad-module,
        .ytp-ad-overlay-container,
        .ytp-ad-text-overlay,
        .ytp-ad-player-overlay,
        .ytp-ad-overlay-close-button {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }
        """
        self.adblock_style_sheet = WebKit2.UserStyleSheet.new(
            css,
            WebKit2.UserContentInjectedFrames.ALL_FRAMES,
            WebKit2.UserStyleLevel.USER,
            None,
            None,
        )

    def install_adblock_script(self):
        script = r"""
        (() => {
            const blocked = /adservice|doubleclick|googlesyndication|googleadservices|adnxs|adsystem|google-analytics|googletagmanager|hotjar|clarity\.ms|mc\.yandex|adblock-tester\.com\/banners|pr_advertising_ads_banner/i;
            const isBlocked = value => blocked.test(String(value || ''));
            const cleanAds = () => {
                if (!document.documentElement) return;
                document.querySelectorAll(
                    'ytd-display-ad-renderer,ytd-promoted-sparkles-web-renderer,' +
                    'ytd-ad-slot-renderer,ytd-in-feed-ad-layout-renderer,' +
                    'ytd-banner-promo-renderer,#player-ads,#masthead-ad,' +
                    '.video-ads,.ytp-ad-module,.ytp-ad-overlay-container,' +
                    'img[src*="pr_advertising_ads_banner"]'
                ).forEach(node => node.remove());
            };
            const nativeFetch = window.fetch;
            window.fetch = (...args) => {
                if (isBlocked(args[0])) {
                    return Promise.reject(new TypeError('Blocked by Kordex adblock'));
                }
                return nativeFetch(...args);
            };
            const nativeOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(method, url, ...rest) {
                if (isBlocked(url)) {
                    this.__kordexBlocked = true;
                }
                return nativeOpen.call(this, method, url, ...rest);
            };
            const nativeSend = XMLHttpRequest.prototype.send;
            XMLHttpRequest.prototype.send = function(...args) {
                if (this.__kordexBlocked) {
                    this.abort();
                    return;
                }
                return nativeSend.apply(this, args);
            };
            cleanAds();
            if (document.documentElement) {
                new MutationObserver(cleanAds).observe(document.documentElement, {childList: true, subtree: true});
            } else {
                document.addEventListener('DOMContentLoaded', () => {
                    cleanAds();
                    new MutationObserver(cleanAds).observe(document.documentElement, {childList: true, subtree: true});
                });
            }
        })();
        """
        self.adblock_script = WebKit2.UserScript.new(
            script,
            WebKit2.UserContentInjectedFrames.ALL_FRAMES,
            WebKit2.UserScriptInjectionTime.START,
            None,
            None,
        )

    def apply_glass_style(self):
        css = b"""
        #browser-window {
            background: #101210;
            color: #e8eee9;
        }
        #tab-container,
        #tab-grid {
            background: #151815;
            border-right: 1px solid #272d28;
            padding: 5px 4px;
        }
        #nav-bar {
            background: #191d19;
            border: 1px solid #2a312b;
            border-radius: 8px;
            padding: 5px 7px;
        }
        button {
            background: #242a25;
            border: 1px solid #343d35;
            border-radius: 6px;
            color: #e8eee9;
            padding: 5px 9px;
        }
        button:hover {
            background: #303a31;
            border-color: #4b5b4d;
        }
        button:active {
            background: #202820;
        }
        button:disabled {
            color: #737d74;
            background: #1c201c;
        }
        entry {
            background: #111511;
            border: 1px solid #303830;
            border-radius: 6px;
            color: #f0f4f0;
            padding: 6px 9px;
        }
        entry:focus {
            border-color: #8fcea0;
        }
        #tab-item {
            background: #1b201c;
            border: 1px solid #29312a;
            border-radius: 6px;
            padding: 3px 6px;
        }
        #tab-item:hover,
        #tab-item-grid:hover {
            background: #252d26;
        }
        #tab-item-active,
        #tab-item-grid {
            background: #1b201c;
            border: 1px solid #29312a;
            border-radius: 6px;
            padding: 4px;
        }
        #tab-item-active {
            background: #202a22;
            border: 1px solid #8fcea0;
        }
        #tab-item-grid-active {
            background: #202a22;
            border: 1px solid #8fcea0;
            border-radius: 6px;
            padding: 4px;
        }
        #more-button {
            background: #1d231e;
            border: 1px solid #303a31;
            border-radius: 6px;
            color: #dce6dd;
        }
        #downloads-panel {
            background: #191d19;
            border: 1px solid #2a312b;
            color: #e8eee9;
        }
        #download-row {
            background: #222822;
            border: 1px solid #333d34;
            border-radius: 5px;
            padding: 6px 8px;
        }
        progressbar trough {
            background: #111511;
            border: 1px solid #303830;
            border-radius: 4px;
        }
        progressbar progress {
            background: #8fcea0;
            border-radius: 4px;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _find_tab_info(self, web_view):
        for item in self.tab_pages:
            if item["web_view"] is web_view:
                return item
        return None

    def _get_current_page(self):
        return self.stack.get_visible_child()

    def _get_current_web_view(self):
        page = self._get_current_page()
        if page is None:
            return None
        for item in self.tab_pages:
            if item["page"] is page:
                return item["web_view"]
        return None

    def show_tab(self, index):
        if not 0 <= index < len(self.tab_pages):
            return
        self.active_tab_index = index
        self.stack.set_visible_child(self.tab_pages[index]["page"])
        self.update_navigation_state()
        self.render_tab_bar()

    def render_tab_bar(self):
        # Limpiar contenedores anteriores
        for child in list(self.tab_container.get_children()):
            self.tab_container.remove(child)
        
        for child in self.tab_grid.get_children():
            self.tab_grid.remove(child)

        num_tabs = len(self.tab_pages)
        use_grid = num_tabs > self.max_single_column_tabs

        if use_grid:
            self.tab_layout.set_visible_child_name("grid")
            self.render_grid_layout()
        else:
            self.tab_layout.set_visible_child_name("list")
            self.render_list_layout()

    def render_list_layout(self):
        """Layout vertical de pestañas (original)"""
        for index, item in enumerate(self.tab_pages):
            row = Gtk.EventBox()
            row.set_size_request(130, 28)
            row.connect("button-press-event", self.on_tab_clicked, index)
            row.set_name("tab-item" if index != self.active_tab_index else "tab-item-active")

            content = Gtk.HBox(spacing=4)
            content.set_border_width(3)

            title_label = Gtk.Label(label=item["title"])
            title_label.set_xalign(0.0)
            title_label.set_ellipsize(Pango.EllipsizeMode.END)
            title_label.set_single_line_mode(True)
            title_label.set_width_chars(12)
            content.pack_start(title_label, True, True, 0)

            close_button = Gtk.Button(label="×")
            close_button.set_relief(Gtk.ReliefStyle.NONE)
            close_button.set_focus_on_click(False)
            close_button.set_size_request(18, 18)
            close_button.connect("clicked", self.on_close_tab_clicked, index)
            content.pack_end(close_button, False, False, 0)

            row.add(content)
            item["title_label"] = title_label
            self.tab_container.pack_start(row, False, False, 0)

        self.tab_container.show_all()

    def render_grid_layout(self):
        """Layout en grid/tiling como Hyprland"""
        num_tabs = len(self.tab_pages)
        cols = 2

        for index, item in enumerate(self.tab_pages):
            row = index // cols
            col = index % cols

            button = Gtk.EventBox()
            button.set_size_request(70, 60)
            button.set_name("tab-item-grid" if index != self.active_tab_index else "tab-item-grid-active")
            button.connect("button-press-event", self.on_tab_clicked, index)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            vbox.set_border_width(2)

            title_label = Gtk.Label(label=item["title"])
            title_label.set_xalign(0.5)
            title_label.set_ellipsize(Pango.EllipsizeMode.END)
            title_label.set_single_line_mode(True)
            title_label.set_width_chars(5)
            vbox.pack_start(title_label, False, False, 0)

            index_label = Gtk.Label(label=f"[{index + 1}]")
            index_label.set_xalign(0.5)
            index_label.set_markup(f"<small>[{index + 1}]</small>")
            vbox.pack_start(index_label, False, False, 0)

            close_button = Gtk.Button(label="×")
            close_button.set_relief(Gtk.ReliefStyle.NONE)
            close_button.set_focus_on_click(False)
            close_button.set_size_request(20, 20)
            close_button.connect("clicked", self.on_close_tab_clicked, index)
            vbox.pack_end(close_button, False, False, 0)

            button.add(vbox)
            self.tab_grid.attach(button, col, row, 1, 1)
            item["title_label"] = title_label

        self.tab_grid.show_all()

    def on_tab_clicked(self, widget, event_or_index=None, index=None):
        if index is None:
            index = event_or_index
        self.show_tab(index)

    def add_new_tab(self, url=None):
        if url is None:
            url = self.search_homepages[self.search_engine]
        page = Gtk.ScrolledWindow()
        page.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        page.set_shadow_type(Gtk.ShadowType.NONE)

        web_view = WebKit2.WebView.new_with_context(self.web_context)
        self.configure_web_view(web_view)
        web_view.connect("notify::title", self.on_title_changed)
        web_view.connect("notify::uri", self.on_uri_changed)
        page.add(web_view)

        item = {
            "page": page,
            "web_view": web_view,
            "title": self.tr("new_tab"),
            "title_label": None,
            "kind": "new_tab",
        }
        self.tab_pages.append(item)
        self.stack.add_titled(page, str(len(self.tab_pages) - 1), "")
        page.show_all()
        self.show_tab(len(self.tab_pages) - 1)

        web_view.load_uri(url)
        self.update_navigation_state()
        return page

    def on_new_tab_clicked(self, button):
        self.add_new_tab(self.search_homepages[self.search_engine])
        self.url_entry.set_placeholder_text(
            "Buscar con " + self.get_search_engine_label()
        )

    def get_search_engine_label(self):
        return {
            "duckduckgo": "DuckDuckGo",
            "brave": "Brave",
            "google": "Google",
            "bing": "Bing",
        }[self.search_engine]

    def on_close_tab_clicked(self, button, index):
        if len(self.tab_pages) <= 1:
            item = self.tab_pages[0]
            if item["web_view"] is None:
                self.stack.remove(item["page"])
                self.tab_pages.pop(0)
                self.add_new_tab()
            else:
                homepage = self.search_homepages[self.search_engine]
                self.url_entry.set_text(homepage)
                item["web_view"].load_uri(homepage)
                self.show_tab(0)
            return

        old_active_index = self.active_tab_index
        page = self.tab_pages[index]["page"]
        self.stack.remove(page)
        self.tab_pages.pop(index)

        if index < old_active_index:
            old_active_index -= 1
        elif index == old_active_index and index >= len(self.tab_pages):
            old_active_index = len(self.tab_pages) - 1
        self.show_tab(old_active_index)

    def on_more_clicked(self, button):
        menu = Gtk.Menu()

        item_bookmarks = Gtk.MenuItem(label=self.tr("bookmarks"))
        item_settings = Gtk.MenuItem(label=self.tr("settings"))

        item_bookmarks.connect("activate", self.open_bookmarks_tab)
        item_settings.connect("activate", self.open_settings_tab)
        for item in (item_bookmarks, item_settings):
            menu.append(item)

        menu.show_all()
        menu.popup_at_widget(button, Gdk.Gravity.SOUTH, Gdk.Gravity.NORTH, None)

    def open_settings_tab(self, widget):
        for index, item in enumerate(self.tab_pages):
            if item.get("kind") == "settings":
                self.show_tab(index)
                return

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        page.set_name("settings-page")
        page.set_border_width(28)

        title = Gtk.Label(label=self.language_texts[self.current_language]["settings"])
        title.set_name("settings-title")
        title.set_halign(Gtk.Align.START)
        page.pack_start(title, False, False, 0)
        self.settings_title = title

        notebook = Gtk.Notebook()
        notebook.set_name("settings-notebook")
        page.pack_start(notebook, True, True, 0)

        general_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        general_page.set_border_width(8)
        general_tab = Gtk.Label(label=self.language_texts[self.current_language]["general"])
        notebook.append_page(general_page, general_tab)
        self.settings_general_tab = general_tab

        section = Gtk.Label(label=self.language_texts[self.current_language]["colors"])
        section.set_name("settings-section")
        section.set_halign(Gtk.Align.START)
        general_page.pack_start(section, False, False, 0)
        self.settings_colors = section

        themes_grid = Gtk.Grid()
        themes_grid.set_row_spacing(16)
        themes_grid.set_column_spacing(16)
        themes = [
            ("black", "Negro"),
            ("green", "Verde"),
            ("blue", "Azul"),
            ("white", "Blanco"),
            ("pink", "Rosa"),
            ("purple", "Morado"),
            ("mex", "MEX"),
        ]
        for index, (theme_name, label_text) in enumerate(themes):
            choice = Gtk.Button()
            choice.set_name("theme-choice")
            choice.set_relief(Gtk.ReliefStyle.NONE)
            choice.connect("clicked", self.on_theme_selected, theme_name)

            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
            ball = Gtk.EventBox()
            ball.set_name("theme-ball-mex" if theme_name == "mex" else "theme-ball-" + theme_name)
            ball.set_size_request(42, 42)
            ball.set_halign(Gtk.Align.CENTER)
            content.pack_start(ball, False, False, 0)

            label = Gtk.Label(label=label_text)
            if not hasattr(self, "theme_labels"):
                self.theme_labels = {}
            self.theme_labels[theme_name] = label
            content.pack_start(label, False, False, 0)
            choice.add(content)
            themes_grid.attach(choice, index % 4, index // 4, 1, 1)

        general_page.pack_start(themes_grid, False, False, 0)

        line_only = Gtk.CheckButton(label=self.language_texts[self.current_language]["lines"])
        line_only.set_active(self.line_only)
        line_only.set_sensitive(self.current_theme != "black")
        self.line_only_button = line_only
        line_only.connect("toggled", self.on_line_only_toggled)
        general_page.pack_start(line_only, False, False, 0)
        self.settings_line_only = line_only

        description = Gtk.Label(label=self.tr("line_description"))
        description.set_xalign(0.0)
        description.set_line_wrap(True)
        general_page.pack_start(description, False, False, 0)
        self.settings_lines_description = description

        adblock_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        adblock_page.set_border_width(8)
        adblock_page.set_valign(Gtk.Align.CENTER)
        adblock_tab = Gtk.Label(label=self.tr("adblock"))
        notebook.append_page(adblock_page, adblock_tab)
        self.settings_adblock_tab = adblock_tab

        adblock_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        adblock_content.set_halign(Gtk.Align.CENTER)
        adblock_content.set_valign(Gtk.Align.CENTER)
        icon = Gtk.Image.new_from_icon_name("security-high-symbolic", Gtk.IconSize.DIALOG)
        icon.set_pixel_size(64)
        adblock_content.pack_start(icon, False, False, 0)

        adblock_toggle = Gtk.CheckButton(label=self.tr("adblock"))
        adblock_toggle.set_active(self.adblock_enabled)
        adblock_toggle.set_halign(Gtk.Align.CENTER)
        adblock_toggle.connect("toggled", self.on_adblock_toggled)
        adblock_content.pack_start(adblock_toggle, False, False, 0)
        self.settings_adblock = adblock_toggle

        adblock_description = Gtk.Label(label=self.tr("adblock_description"))
        adblock_description.set_max_width_chars(62)
        adblock_description.set_line_wrap(True)
        adblock_description.set_justify(Gtk.Justification.CENTER)
        adblock_content.pack_start(adblock_description, False, False, 0)
        self.settings_adblock_description = adblock_description
        adblock_page.pack_start(adblock_content, False, False, 0)

        volatility_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        volatility_page.set_border_width(8)
        volatility_page.set_valign(Gtk.Align.CENTER)
        volatility_tab = Gtk.Label(label="Volatibilidad")
        notebook.append_page(volatility_page, volatility_tab)
        self.settings_volatility_tab = volatility_tab

        volatility_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        volatility_content.set_halign(Gtk.Align.CENTER)
        volatility_content.set_valign(Gtk.Align.CENTER)
        volatility_toggle = Gtk.CheckButton(label="Volatibilidad")
        volatility_toggle.set_active(self.volatile_storage)
        volatility_toggle.set_halign(Gtk.Align.CENTER)
        volatility_toggle.connect("toggled", self.on_volatility_toggled)
        volatility_content.pack_start(volatility_toggle, False, False, 0)
        self.settings_volatility = volatility_toggle
        volatility_description = Gtk.Label(
            label="si esta desactivado se guardan tus cosas"
        )
        volatility_description.set_max_width_chars(62)
        volatility_description.set_line_wrap(True)
        volatility_description.set_justify(Gtk.Justification.CENTER)
        volatility_content.pack_start(volatility_description, False, False, 0)
        volatility_page.pack_start(volatility_content, False, False, 0)

        language_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        language_page.set_border_width(8)
        language_tab = Gtk.Label(label=self.language_texts[self.current_language]["language"])
        notebook.append_page(language_page, language_tab)
        self.settings_language_tab = language_tab

        language_title = Gtk.Label(label=self.language_texts[self.current_language]["language"])
        language_title.set_name("settings-section")
        language_title.set_halign(Gtk.Align.START)
        language_page.pack_start(language_title, False, False, 0)
        self.settings_language_title = language_title

        languages_grid = Gtk.Grid()
        languages_grid.set_row_spacing(10)
        languages_grid.set_column_spacing(10)
        languages = [
            ("es-es", "🇪🇸", "Español (España)"),
            ("es-mx", "🇲🇽", "Español (México)"),
            ("en-uk", "🇬🇧", "English (UK)"),
            ("en-us", "🇺🇸", "English (USA)"),
            ("ru", "🇷🇺", "Русский"),
            ("zh", "🇨🇳", "中文"),
        ]
        self.language_buttons = {}
        for index, (language_code, flag, language_name) in enumerate(languages):
            language_button = Gtk.Button()
            language_button.set_name(
                "language-choice-selected-" + language_code
                if language_code == self.current_language else "language-choice-" + language_code
            )
            language_button.set_relief(Gtk.ReliefStyle.NONE)
            language_button.connect("clicked", self.on_language_selected, language_code)

            language_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            flag_ball = Gtk.EventBox()
            flag_ball.set_name("language-ball-" + language_code)
            flag_ball.set_size_request(62, 62)
            flag_label = Gtk.Label(label=flag)
            flag_label.set_name("language-flag")
            flag_ball.add(flag_label)
            language_content.pack_start(flag_ball, False, False, 0)
            name_label = Gtk.Label(label=language_name)
            name_label.set_xalign(0.0)
            language_content.pack_start(name_label, True, True, 0)
            language_button.add(language_content)
            languages_grid.attach(language_button, index % 2, index // 2, 1, 1)
            self.language_buttons[language_code] = language_button

        language_page.pack_start(languages_grid, False, False, 0)

        search_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        search_page.set_border_width(8)
        search_tab = Gtk.Label(label=self.tr("search"))
        notebook.append_page(search_page, search_tab)
        self.settings_search_tab = search_tab

        search_title = Gtk.Label(label=self.tr("search"))
        search_title.set_name("settings-section")
        search_title.set_halign(Gtk.Align.START)
        search_page.pack_start(search_title, False, False, 0)

        search_buttons = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        search_page.pack_start(search_buttons, False, False, 0)
        self.search_engine_buttons = {}
        for engine_name, engine_label in (
            ("duckduckgo", "DuckDuckGo"),
            ("brave", "Brave"),
            ("google", "Google"),
            ("bing", "Bing"),
        ):
            engine_button = Gtk.Button(label=engine_label)
            engine_button.set_relief(Gtk.ReliefStyle.NONE)
            engine_button.set_name(
                "search-engine-selected" if engine_name == self.search_engine
                else "search-engine"
            )
            engine_button.connect("clicked", self.on_search_engine_selected, engine_name)
            search_buttons.pack_start(engine_button, False, False, 0)
            self.search_engine_buttons[engine_name] = engine_button

        self.settings_search_title = search_title

        history_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        history_page.set_border_width(8)
        history_tab = Gtk.Label(label=self.language_texts[self.current_language]["history"])
        notebook.append_page(history_page, history_tab)
        self.settings_history_tab = history_tab

        history_title = Gtk.Label(label=self.language_texts[self.current_language]["history_title"])
        history_title.set_name("settings-section")
        history_title.set_halign(Gtk.Align.START)
        history_page.pack_start(history_title, False, False, 0)
        self.settings_history_title = history_title

        history_message = Gtk.Label(
            label="Este navegador no guarda un historial local de tus páginas. "
            "Su funcionamiento es similar al modo incógnito, de forma permanente."
        )
        history_message.set_xalign(0.0)
        history_message.set_line_wrap(True)
        history_page.pack_start(history_message, False, False, 0)
        self.settings_history_message = history_message

        network_message = Gtk.Label(
            label="Ten en cuenta que las páginas web, la red y tu proveedor de internet "
            "pueden conservar información sobre la actividad de conexión."
        )
        network_message.set_xalign(0.0)
        network_message.set_line_wrap(True)
        history_page.pack_start(network_message, False, False, 0)
        self.settings_network_message = network_message

        version_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        version_page.set_border_width(8)
        version_page.set_valign(Gtk.Align.CENTER)
        version_tab = Gtk.Label(label=self.tr("version"))
        notebook.append_page(version_page, version_tab)
        self.settings_version_tab = version_tab

        version_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        version_content.set_halign(Gtk.Align.CENTER)
        version_content.set_valign(Gtk.Align.CENTER)
        logo = Gtk.Image.new_from_file(
            "/home/jose/Descargas/hijosdeputa-removebg-preview.png"
        )
        logo.set_halign(Gtk.Align.CENTER)
        version_content.pack_start(logo, False, False, 0)
        product_name = Gtk.Label(label="Kordex Browser")
        product_name.set_name("settings-title")
        version_content.pack_start(product_name, False, False, 0)
        version_number = Gtk.Label(label=self.tr("beta"))
        version_content.pack_start(version_number, False, False, 0)
        based_on = Gtk.Label(label=self.tr("based_on"))
        based_on.set_line_wrap(True)
        based_on.set_justify(Gtk.Justification.CENTER)
        version_content.pack_start(based_on, False, False, 0)
        operating_system = Gtk.Label(
            label=self.get_operating_system_label() + ": " + self.os_name
        )
        operating_system.set_line_wrap(True)
        operating_system.set_justify(Gtk.Justification.CENTER)
        version_content.pack_start(operating_system, False, False, 0)
        version_page.pack_start(version_content, False, False, 0)
        self.settings_product_name = product_name
        self.settings_version_number = version_number
        self.settings_based_on = based_on
        self.settings_operating_system = operating_system

        item = {
            "page": page,
            "web_view": None,
            "title": self.tr("settings"),
            "title_label": None,
            "kind": "settings",
        }
        self.tab_pages.append(item)
        self.stack.add_titled(page, str(len(self.tab_pages) - 1), "")
        page.show_all()
        self.show_tab(len(self.tab_pages) - 1)

    def on_theme_selected(self, button, theme_name):
        self.current_theme = theme_name
        if theme_name == "black":
            self.line_only = False
            if hasattr(self, "line_only_button"):
                self.line_only_button.set_active(False)
                self.line_only_button.set_sensitive(False)
        elif hasattr(self, "line_only_button"):
            self.line_only_button.set_sensitive(True)
        self.apply_theme_style()
        self.save_preferences()

    def on_language_selected(self, button, language_code):
        self.current_language = language_code
        for code, language_button in self.language_buttons.items():
            language_button.set_name(
                "language-choice-selected-" + code
                if code == language_code else "language-choice-" + code
            )
        self.apply_language()
        self.save_preferences()

    def on_search_engine_selected(self, button, engine_name):
        self.search_engine = engine_name
        for code, engine_button in self.search_engine_buttons.items():
            engine_button.set_name(
                "search-engine-selected" if code == engine_name else "search-engine"
            )
        self.url_entry.set_placeholder_text("Buscar con " + self.get_search_engine_label())
        web_view = self._get_current_web_view()
        if web_view is not None:
            homepage = self.search_homepages[engine_name]
            self.url_entry.set_text(homepage)
            web_view.load_uri(homepage)
        self.save_preferences()

    def get_search_url(self, query):
        return self.search_engines[self.search_engine] + quote_plus(query.strip())

    def apply_language(self):
        text = self.language_texts[self.current_language]
        self.settings_title.set_text(text["settings"])
        self.settings_general_tab.set_text(text["general"])
        self.settings_colors.set_text(text["colors"])
        self.settings_line_only.set_label(text["lines"])
        self.settings_adblock.set_label(text["adblock"])
        self.settings_adblock_tab.set_text(text["adblock"])
        self.settings_adblock_description.set_text(text["adblock_description"])
        theme_names = {
            "zh": {"black": "黑色", "green": "绿色", "blue": "蓝色", "white": "白色", "pink": "粉色", "purple": "紫色", "mex": "墨西哥"},
            "ru": {"black": "Черный", "green": "Зеленый", "blue": "Синий", "white": "Белый", "pink": "Розовый", "purple": "Фиолетовый", "mex": "Мексика"},
            "en-uk": {"black": "Black", "green": "Green", "blue": "Blue", "white": "White", "pink": "Pink", "purple": "Purple", "mex": "MEX"},
            "en-us": {"black": "Black", "green": "Green", "blue": "Blue", "white": "White", "pink": "Pink", "purple": "Purple", "mex": "MEX"},
        }.get(self.current_language)
        if theme_names and hasattr(self, "theme_labels"):
            for theme_name, label in self.theme_labels.items():
                label.set_text(theme_names[theme_name])
        self.settings_language_tab.set_text(text["language"])
        self.settings_language_title.set_text(text["language"])
        self.settings_history_tab.set_text(text["history"])
        self.settings_history_title.set_text(text["history_title"])
        self.settings_version_tab.set_text(text["version"])
        self.settings_version_number.set_text(text["beta"])
        self.settings_based_on.set_text(text["based_on"])
        self.settings_search_tab.set_text(text.get("search", "Búsqueda"))
        self.settings_search_title.set_text(text.get("search", "Búsqueda"))
        self.settings_operating_system.set_text(
            self.get_operating_system_label() + ": " + self.os_name
        )
        self.settings_lines_description.set_text({
            "en-uk": "Use only lines and borders in the selected colour on a black background.",
            "en-us": "Use only lines and borders in the selected color on a black background.",
            "zh": "仅使用所选颜色绘制黑色背景上的线条和边框。",
            "ru": "Использовать только линии и границы выбранного цвета на черном фоне.",
        }.get(self.current_language, self.tr("line_description")))
        self.settings_history_message.set_text({
            "en-uk": "This browser does not save local browsing history. It works like a permanent private browsing mode.",
            "en-us": "This browser does not save local browsing history. It works like a permanent private browsing mode.",
            "zh": "此浏览器不会在本地保存网页浏览历史，始终以类似永久无痕模式的方式运行。",
            "ru": "Браузер не сохраняет историю страниц локально и всегда работает подобно постоянному режиму инкогнито.",
        }.get(self.current_language, "Este navegador no guarda un historial local de tus páginas. Su funcionamiento es similar al modo incógnito, de forma permanente."))
        self.settings_network_message.set_text({
            "en-uk": "Websites, networks and your internet provider may still retain information about connection activity.",
            "en-us": "Websites, networks and your internet provider may still retain information about connection activity.",
            "zh": "请注意，网站、网络或互联网服务提供商仍可能保存连接活动信息。",
            "ru": "Обратите внимание: сайты, сеть или интернет-провайдер могут сохранять сведения о подключении.",
        }.get(self.current_language, "Ten en cuenta que las páginas web, la red y tu proveedor de internet pueden conservar información sobre la actividad de conexión."))
        self.set_title(self.tr("window_title"))
        for item in self.tab_pages:
            if item.get("kind") == "settings":
                item["title"] = self.tr("settings")
            elif item.get("kind") == "bookmarks":
                item["title"] = self.tr("bookmarks")
            elif item.get("kind") == "new_tab":
                item["title"] = self.tr("new_tab")
        self.render_tab_bar()
        if self.current_language == "zh":
            self.btn_back.set_tooltip_text("后退")
            self.btn_forward.set_tooltip_text("前进")
            self.btn_refresh.set_tooltip_text("刷新")
        elif self.current_language == "ru":
            self.btn_back.set_tooltip_text("Назад")
            self.btn_forward.set_tooltip_text("Вперед")
            self.btn_refresh.set_tooltip_text("Обновить")
        else:
            self.btn_back.set_tooltip_text("Atrás")
            self.btn_forward.set_tooltip_text("Adelante")
            self.btn_refresh.set_tooltip_text("Recargar")

    def on_line_only_toggled(self, button):
        if self.current_theme == "black":
            button.set_active(False)
            return
        self.line_only = button.get_active()
        self.apply_theme_style()
        self.save_preferences()

    def on_adblock_toggled(self, button):
        self.adblock_enabled = button.get_active()
        for item in self.tab_pages:
            web_view = item.get("web_view")
            if web_view is None:
                continue
            user_content_manager = web_view.get_user_content_manager()
            if self.adblock_filter is not None:
                if self.adblock_enabled:
                    user_content_manager.add_filter(self.adblock_filter)
                else:
                    user_content_manager.remove_filter(self.adblock_filter)
            if self.adblock_style_sheet is not None:
                if self.adblock_enabled:
                    user_content_manager.add_style_sheet(self.adblock_style_sheet)
                else:
                    user_content_manager.remove_style_sheet(self.adblock_style_sheet)
            if self.adblock_script is not None:
                if self.adblock_enabled:
                    user_content_manager.add_script(self.adblock_script)
                else:
                    user_content_manager.remove_script(self.adblock_script)
        self.save_preferences()

    def on_volatility_toggled(self, button):
        self.volatile_storage = button.get_active()
        self.save_preferences()

    def apply_theme_style(self):
        if self.current_theme == "black":
            self.line_only = False
        background, surface, button, text, accent = self.theme_colors[self.current_theme]
        line_css = ""
        if self.line_only:
            background = "#000000"
            surface = "#000000"
            button = "#000000"
            text = "#f3f3f3"
            if self.current_theme == "white":
                accent = "#ffffff"
            line_css = f"""
            #tab-container, #tab-grid, #nav-bar, button, entry, #theme-choice {{
                border-color: {accent};
            }}
            #tab-container, #tab-grid, #nav-bar, button, entry, #theme-choice,
            #tab-item, #tab-item-grid, #tab-item-active, #tab-item-grid-active,
            #more-button {{ background: #000000; }}
            """
            if self.current_theme == "mex":
                line_css += """
                #tab-container, #tab-grid, #tab-item, #tab-item-grid,
                #tab-item-active, #tab-item-grid-active, #more-button {
                    border-color: #ce1126;
                }
                #nav-bar, #nav-bar button, #nav-bar entry {
                    border-color: #006847;
                }
                #settings-page, #settings-page button, #settings-page entry,
                #theme-choice {
                    border-color: #ffffff;
                }
                """
        css = f"""
        #browser-window, #settings-page {{ background: {background}; color: {text}; }}
        #tab-container, #tab-grid {{ background: {surface}; }}
        #nav-bar {{ background: {surface}; }}
        button, #theme-choice {{ background: {button}; color: {text}; }}
        entry {{ background: {surface}; color: {text}; }}
        #tab-item, #tab-item-grid {{ background: {button}; color: {text}; }}
        #tab-item-active, #tab-item-grid-active {{ background: {surface}; border-color: {accent}; }}
        #more-button {{ background: {button}; color: {text}; }}
        #settings-title, #settings-section {{ color: {text}; }}
        #language-choice {{ background: {button}; color: {text}; padding: 10px; }}
        #search-engine {{ background: {button}; color: {text}; padding: 8px; }}
        #search-engine-selected {{ background: {surface}; color: {text}; border-color: {accent}; padding: 8px; }}
        #language-choice-selected-es-es, #language-choice-selected-es-mx,
        #language-choice-selected-en-uk, #language-choice-selected-en-us,
        #language-choice-selected-ru, #language-choice-selected-zh {{
            color: {text}; border-color: {accent}; padding: 10px;
        }}
        #language-choice-es-es, #language-choice-selected-es-es {{ background: linear-gradient(to right, #aa151b 0%, #aa151b 34%, #f1bf00 34%, #f1bf00 66%, #aa151b 66%, #aa151b 100%); }}
        #language-choice-es-mx, #language-choice-selected-es-mx {{ background: linear-gradient(to right, #006847 0%, #006847 34%, #ffffff 34%, #ffffff 66%, #ce1126 66%, #ce1126 100%); }}
        #language-choice-en-uk, #language-choice-selected-en-uk {{ background: #1b3f91; border-color: #ffffff; }}
        #language-choice-en-us, #language-choice-selected-en-us {{ background: linear-gradient(to bottom, #b22234 0%, #b22234 14%, #ffffff 14%, #ffffff 28%, #b22234 28%, #b22234 42%, #ffffff 42%, #ffffff 56%, #b22234 56%, #b22234 70%, #ffffff 70%, #ffffff 84%, #b22234 84%, #b22234 100%); }}
        #language-choice-ru, #language-choice-selected-ru {{ background: linear-gradient(to bottom, #ffffff 0%, #ffffff 33%, #2456a6 33%, #2456a6 66%, #d52b1e 66%, #d52b1e 100%); }}
        #language-choice-zh, #language-choice-selected-zh {{ background: #de2910; }}
        #language-ball-es-es, #language-ball-es-mx, #language-ball-en-uk,
        #language-ball-en-us, #language-ball-ru, #language-ball-zh {{
            font-size: 28px; border-radius: 31px; border: 2px solid rgba(255,255,255,0.55);
        }}
        #language-ball-es-es {{ background: linear-gradient(to bottom, #aa151b 0%, #aa151b 25%, #f1bf00 25%, #f1bf00 75%, #aa151b 75%, #aa151b 100%); }}
        #language-ball-es-mx {{ background: linear-gradient(to right, #006847 0%, #006847 33%, #ffffff 33%, #ffffff 66%, #ce1126 66%, #ce1126 100%); }}
        #language-ball-en-uk {{ background: #1b3f91; }}
        #language-ball-en-us {{ background: linear-gradient(to bottom, #b22234 0%, #b22234 14%, #ffffff 14%, #ffffff 28%, #b22234 28%, #b22234 42%, #ffffff 42%, #ffffff 56%, #b22234 56%, #b22234 70%, #ffffff 70%, #ffffff 84%, #b22234 84%, #b22234 100%); }}
        #language-ball-ru {{ background: linear-gradient(to bottom, #ffffff 0%, #ffffff 33%, #2456a6 33%, #2456a6 66%, #d52b1e 66%, #d52b1e 100%); }}
        #language-ball-zh {{ background: #de2910; }}
        #theme-ball-black {{ background: #202020; border: 2px solid #555555; border-radius: 21px; }}
        #theme-ball-green {{ background: #24a05a; border-radius: 21px; }}
        #theme-ball-blue {{ background: #287bd8; border-radius: 21px; }}
        #theme-ball-white {{ background: #f5f5f5; border: 1px solid #777777; border-radius: 21px; }}
        #theme-ball-pink {{ background: #ed5d9d; border-radius: 21px; }}
        #theme-ball-purple {{ background: #9554d4; border-radius: 21px; }}
        #theme-ball-mex {{ background: linear-gradient(to right, #006847 0%, #006847 33%, #ffffff 33%, #ffffff 66%, #ce1126 66%, #ce1126 100%); border-radius: 21px; }}
        {line_css}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        screen = Gdk.Screen.get_default()
        if self.theme_provider is not None:
            Gtk.StyleContext.remove_provider_for_screen(screen, self.theme_provider)
        self.theme_provider = provider
        Gtk.StyleContext.add_provider_for_screen(
            screen, self.theme_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1
        )

    def open_bookmarks_tab(self, widget):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_name("bookmarks-page")

        title = Gtk.Label(label=self.tr("bookmarks"))
        title.set_halign(Gtk.Align.START)
        page.pack_start(title, False, False, 0)

        add_button = Gtk.Button(label=self.tr("add_bookmark"))
        add_button.set_halign(Gtk.Align.START)
        add_button.connect("clicked", self.show_add_bookmark_dialog)
        page.pack_start(add_button, False, False, 0)

        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.populate_bookmarks_list(list_box)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(list_box)
        page.pack_start(scrolled, True, True, 0)

        item = {
            "page": page,
            "web_view": None,
            "title": self.tr("bookmarks"),
            "title_label": None,
            "kind": "bookmarks",
            "list_box": list_box,
        }
        self.tab_pages.append(item)
        self.stack.add_titled(page, str(len(self.tab_pages) - 1), "")
        page.show_all()
        self.show_tab(len(self.tab_pages) - 1)

    def populate_bookmarks_list(self, list_box):
        for child in list_box.get_children():
            list_box.remove(child)
        for bookmark in self.bookmarks:
            row = Gtk.ListBoxRow()
            row_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            bookmark_button = Gtk.Button(label=bookmark)
            bookmark_button.set_relief(Gtk.ReliefStyle.NONE)
            bookmark_button.set_halign(Gtk.Align.FILL)
            bookmark_button.connect("clicked", self.open_bookmark_from_tab, bookmark)
            row_content.pack_start(bookmark_button, True, True, 0)
            delete_button = Gtk.Button(label="×")
            delete_button.set_tooltip_text(self.tr("delete_bookmark"))
            delete_button.set_relief(Gtk.ReliefStyle.NONE)
            delete_button.connect("clicked", self.on_delete_bookmark, bookmark, row)
            row_content.pack_end(delete_button, False, False, 0)
            row.add(row_content)
            list_box.add(row)
        list_box.show_all()

    def refresh_bookmarks_lists(self):
        for item in self.tab_pages:
            if item.get("kind") == "bookmarks":
                self.populate_bookmarks_list(item["list_box"])

    def on_delete_bookmark(self, button, bookmark, row):
        if bookmark in self.bookmarks:
            self.bookmarks.remove(bookmark)
            self.save_preferences()
            self.refresh_bookmarks_lists()

    def show_add_bookmark_dialog(self, button):
        dialog = Gtk.Dialog(title=self.tr("add_bookmark"), parent=self)
        dialog.set_modal(True)
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_border_width(12)

        entry = Gtk.Entry()
        entry.set_placeholder_text(self.tr("paste_url"))
        box.pack_start(entry, False, False, 0)
        dialog.add_button(self.tr("add"), Gtk.ResponseType.OK)
        dialog.add_button(self.tr("cancel"), Gtk.ResponseType.CANCEL)
        dialog.show_all()
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.save_bookmark(entry.get_text())
        dialog.destroy()
        self.refresh_bookmarks_lists()

    def save_bookmark(self, value):
        if not value.strip():
            return
        url = self.normalize_url(value)
        if url not in self.bookmarks:
            self.bookmarks.append(url)
            self.save_preferences()

    def open_bookmark_from_tab(self, button, bookmark):
        self.open_url_in_current_tab(bookmark)

    def open_url_in_current_tab(self, value):
        url = self.normalize_url(value)
        index = self.active_tab_index
        web_view = self._get_current_web_view()
        if web_view is not None:
            self.url_entry.set_text(url)
            web_view.load_uri(url)
            return

        if not self.tab_pages:
            self.add_new_tab(url)
            return

        old_page = self.tab_pages[index]["page"]
        page = Gtk.ScrolledWindow()
        page.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        page.set_shadow_type(Gtk.ShadowType.NONE)

        web_view = WebKit2.WebView.new_with_context(self.web_context)
        self.configure_web_view(web_view)
        web_view.connect("notify::title", self.on_title_changed)
        web_view.connect("notify::uri", self.on_uri_changed)
        page.add(web_view)

        self.stack.remove(old_page)
        self.tab_pages[index].update({
            "page": page,
            "web_view": web_view,
            "title": self.tr("new_tab"),
            "kind": "web",
        })
        self.stack.add_titled(page, str(index), "")
        page.show_all()
        self.show_tab(index)
        self.url_entry.set_text(url)
        web_view.load_uri(url)

    def normalize_url(self, value):
        text = value.strip()
        if not text:
            return ""
        if text.startswith(("http://", "https://")):
            return text
        if not any(character.isspace() for character in text):
            try:
                hostname = urlsplit("//" + text).hostname or ""
            except ValueError:
                hostname = ""
            if hostname.lower() == "localhost" or "." in hostname or ":" in hostname:
                return "https://" + text
        return self.get_search_url(text)

    def on_url_activate(self, entry):
        self.perform_url_action(entry.get_text())

    def on_search_button_clicked(self, button):
        self.perform_url_action(self.url_entry.get_text())

    def perform_url_action(self, value):
        value = value.strip()
        if not value:
            return
        self.open_url_in_current_tab(value)

    def on_back_clicked(self, button):
        web_view = self._get_current_web_view()
        if web_view is not None and web_view.can_go_back():
            web_view.go_back()

    def on_forward_clicked(self, button):
        web_view = self._get_current_web_view()
        if web_view is not None and web_view.can_go_forward():
            web_view.go_forward()

    def on_refresh_clicked(self, button):
        web_view = self._get_current_web_view()
        if web_view is not None:
            web_view.reload()

    def on_title_changed(self, web_view, pspec):
        item = self._find_tab_info(web_view)
        if item is None:
            return

        title = web_view.get_title() or self.tr("new_tab")
        if title == "about:blank":
            title = self.tr("new_tab")
        else:
            item["kind"] = "web"
        if len(title) > 20:
            title = title[:17] + "..."
        item["title"] = title
        if item["title_label"] is not None:
            item["title_label"].set_text(title)

    def on_uri_changed(self, web_view, pspec):
        if self._get_current_web_view() is web_view:
            uri = web_view.get_uri() or ""
            self.url_entry.set_text(uri)
            self.update_navigation_state()

    def update_navigation_state(self):
        web_view = self._get_current_web_view()
        if web_view is None:
            self.btn_back.set_sensitive(False)
            self.btn_forward.set_sensitive(False)
            self.btn_refresh.set_sensitive(False)
            if self.tab_pages:
                self.url_entry.set_text(self.tab_pages[self.active_tab_index]["title"].upper())
            else:
                self.url_entry.set_text("")
            return

        self.btn_back.set_sensitive(web_view.can_go_back())
        self.btn_forward.set_sensitive(web_view.can_go_forward())
        self.btn_refresh.set_sensitive(True)
        uri = web_view.get_uri() or ""
        if self.url_entry.get_text() != uri:
            self.url_entry.set_text(uri)


if __name__ == "__main__":
    app = BrowserApp()
    app.show_all()
    Gtk.main()