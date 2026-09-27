import customtkinter as ctk
import json
import os
import sys
import subprocess
from tkinter import messagebox


COLOR_BG_MAIN = ("#f0f0f5", "#0f0f1a")
COLOR_BG_SIDEBAR = ("#ffffff", "#16162a")
COLOR_BG_CARD = ("#ffffff", "#1e1e35")
COLOR_BG_CARD_HOVER = ("#f0f0f5", "#252542")
COLOR_ACCENT = ("#6a4ce0", "#7c5cff")
COLOR_TEXT_PRIMARY = ("#1a1a2e", "#ffffff")
COLOR_TEXT_SECONDARY = ("#6b7280", "#9ca3af")
COLOR_SUCCESS = ("#16a34a", "#22c55e")
COLOR_DANGER = ("#dc2626", "#ef4444")
COLOR_WARNING = ("#d97706", "#f59e0b")
COLOR_DIVIDER = ("#e5e7eb", "#2a2a45")


DEFAULT_SETTINGS = {
    "dark_mode": True,
    "confirm_changes": True,
    "compact_view": False,
    "start_with_windows": False,
}


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_settings_path():
    """Return a user-writable settings path (works from exe)."""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    folder = os.path.join(appdata, "SmartServiceManager")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "settings.json")


def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_sc(args):
    """Run a sc.exe command and return (success, output)."""
    try:
        result = subprocess.run(
            ["sc"] + args,
            capture_output=True, text=True, shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except Exception as e:
        return False, str(e)


def get_service_state(service_id):
    """Return 'running', 'stopped', or 'unknown'."""
    ok, out = run_sc(["query", service_id])
    if not ok:
        return "unknown"
    if "RUNNING" in out:
        return "running"
    if "STOPPED" in out:
        return "stopped"
    return "unknown"


def disable_service(service_id):
    run_sc(["stop", service_id])
    ok, out = run_sc(["config", service_id, "start=", "disabled"])
    return ok, out


def enable_service(service_id):
    ok, out = run_sc(["config", service_id, "start=", "demand"])
    if ok:
        run_sc(["start", service_id])
    return ok, out


class ServiceManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.settings = self.load_settings()
        ctk.set_appearance_mode("Dark" if self.settings["dark_mode"] else "Light")

        self.services = self.load_services()
        self.service_widgets = {}

        self.title("Smart Service Manager")

        # Set window icon
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icon error: {e}")

        self.geometry("1050x680")
        self.minsize(950, 600)
        self.configure(fg_color=COLOR_BG_MAIN)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_main_area()
        self.build_status_bar()
        self.create_pages()
        self.show_page("dashboard")

        if not is_admin():
            self.after(500, self.warn_admin)

    def warn_admin(self):
        messagebox.showwarning(
            "Administrator Required",
            "The application is NOT running as Administrator.\n\n"
            "You can browse and see services, but enabling or disabling them "
            "will fail.\n\n"
            "Close this app, right-click the exe, and choose "
            "'Run as administrator'."
        )

    def load_settings(self):
        try:
            with open(get_settings_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in DEFAULT_SETTINGS.items():
                    data.setdefault(k, v)
                return data
        except FileNotFoundError:
            return dict(DEFAULT_SETTINGS)

    def save_settings(self):
        with open(get_settings_path(), "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2)

    def load_services(self):
        with open(resource_path("services.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("services", [])

    def build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, fg_color=COLOR_BG_SIDEBAR, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsw")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="  Smart Service\n  Manager",
                     font=("Segoe UI", 18, "bold"),
                     text_color=COLOR_TEXT_PRIMARY, justify="left").pack(anchor="w", padx=20, pady=(30, 5))
        ctk.CTkLabel(sidebar, text="  v1.0.0", font=("Segoe UI", 11),
                     text_color=COLOR_TEXT_SECONDARY, justify="left").pack(anchor="w", padx=20, pady=(0, 25))
        ctk.CTkFrame(sidebar, height=1, fg_color=COLOR_DIVIDER).pack(fill="x", padx=20, pady=10)

        self.nav_buttons = []
        for label, command in [
            ("Dashboard", lambda: self.show_page("dashboard")),
            ("Services", lambda: self.show_page("services")),
            ("Settings", lambda: self.show_page("settings")),
            ("About", lambda: self.show_page("about")),
        ]:
            btn = ctk.CTkButton(sidebar, text=f"   {label}", font=("Segoe UI", 13),
                                fg_color="transparent", hover_color=COLOR_BG_CARD_HOVER,
                                text_color=COLOR_TEXT_SECONDARY, anchor="w",
                                height=40, corner_radius=8, command=command)
            btn.pack(fill="x", padx=12, pady=3)
            self.nav_buttons.append(btn)

        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=20, pady=20)
        admin_text = "Admin: YES" if is_admin() else "Admin: NO"
        admin_color = COLOR_SUCCESS if is_admin() else COLOR_DANGER
        ctk.CTkLabel(bottom, text=admin_text, font=("Segoe UI", 11, "bold"),
                     text_color=admin_color).pack(anchor="w")
        ctk.CTkLabel(bottom, text="Windows 11 Pro", font=("Segoe UI", 10),
                     text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(3, 0))

    def build_main_area(self):
        self.main_container = ctk.CTkFrame(self, fg_color=COLOR_BG_MAIN, corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(self.main_container, fg_color=COLOR_BG_SIDEBAR, height=60, corner_radius=0)
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_propagate(False)

        self.page_title = ctk.CTkLabel(top_bar, text="Dashboard",
                                        font=("Segoe UI", 20, "bold"),
                                        text_color=COLOR_TEXT_PRIMARY)
        self.page_title.pack(side="left", padx=25)

        pill = ctk.CTkFrame(top_bar, fg_color=COLOR_BG_CARD, corner_radius=15, height=30)
        pill.pack(side="right", padx=25)
        ctk.CTkLabel(pill, text="  Active  ", font=("Segoe UI", 11, "bold"),
                     text_color=COLOR_SUCCESS).pack(pady=3)

        self.content_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_container.grid(row=1, column=0, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

    def create_pages(self):
        self.pages = {}
        for key, builder in [
            ("dashboard", self.build_dashboard_content),
            ("services", self.build_services_content),
            ("settings", self.build_settings_content),
            ("about", self.build_about_content),
        ]:
            frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
            frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            builder(frame)
            self.pages[key] = frame

    def show_page(self, name):
        for key, page in self.pages.items():
            page.grid() if key == name else page.grid_remove()
        titles = {"dashboard": "Dashboard", "services": "Services",
                  "settings": "Settings", "about": "About"}
        self.page_title.configure(text=titles[name])
        self.set_active_nav({"dashboard": 0, "services": 1, "settings": 2, "about": 3}[name])
        self.log(f"Viewing: {titles[name]}")

    def set_active_nav(self, index):
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.configure(fg_color=COLOR_ACCENT, text_color=COLOR_TEXT_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=COLOR_TEXT_SECONDARY)

    # ============ DASHBOARD ============
    def build_dashboard_content(self, parent):
        parent.grid_columnconfigure((0, 1, 2), weight=1)
        parent.grid_rowconfigure(1, weight=1)

        welcome = ctk.CTkFrame(parent, fg_color=COLOR_BG_CARD, corner_radius=14, height=100)
        welcome.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        welcome.grid_propagate(False)
        ctk.CTkLabel(welcome, text="Welcome to your Control Center",
                     font=("Segoe UI", 18, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=25, pady=(18, 2))
        ctk.CTkLabel(welcome, text="Monitor and optimize your Windows services for peak performance.",
                     font=("Segoe UI", 12),
                     text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", padx=25)

        self.stat_labels = {}
        self.stat_labels["total"] = self.create_stat_card(parent, "Total Services", str(len(self.services)), COLOR_ACCENT, 0)
        self.stat_labels["recommended"] = self.create_stat_card(parent, "Recommended", str(sum(1 for s in self.services if s.get("recommended"))), COLOR_WARNING, 1)
        self.stat_labels["disabled"] = self.create_stat_card(parent, "Disabled (session)", "0", COLOR_DANGER, 2)

    def create_stat_card(self, parent, title, value, color, col):
        card = ctk.CTkFrame(parent, fg_color=COLOR_BG_CARD, corner_radius=14, height=110)
        card.grid(row=1, column=col, sticky="ew", padx=(0 if col == 0 else 8, 8 if col < 2 else 0))
        card.grid_propagate(False)
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 12),
                     text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(18, 0))
        v = ctk.CTkLabel(card, text=value, font=("Segoe UI", 28, "bold"), text_color=color)
        v.pack(anchor="w", padx=20, pady=(0, 15))
        return v

    def update_stats(self):
        total = len(self.services)
        recommended = sum(1 for s in self.services if s.get("recommended"))
        disabled = sum(1 for w in self.service_widgets.values() if not w["switch"].get())
        self.stat_labels["total"].configure(text=str(total))
        self.stat_labels["recommended"].configure(text=str(recommended))
        self.stat_labels["disabled"].configure(text=str(disabled))

    # ============ SERVICES ============
    def build_services_content(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(header, text="Manage Windows Services",
                     font=("Segoe UI", 15, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(side="left")

        ctk.CTkButton(header, text="Apply Recommended",
                      font=("Segoe UI", 12, "bold"),
                      fg_color=COLOR_WARNING, hover_color="#b45309",
                      corner_radius=8, height=34, width=170,
                      command=self.apply_recommended).pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent",
                                                    scrollbar_button_color=COLOR_BG_CARD,
                                                    scrollbar_button_hover_color=COLOR_ACCENT)
        self.scroll_frame.pack(fill="both", expand=True)
        self.render_service_cards()

    def render_service_cards(self):
        for w in self.service_widgets.values():
            w["card"].destroy()
        self.service_widgets = {}

        for service in self.services:
            sid = service["id"]
            compact = self.settings["compact_view"]
            height = 60 if compact else 90

            card = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_BG_CARD,
                                 corner_radius=14, height=height)
            card.pack(fill="x", pady=(4 if compact else 8), padx=5)
            card.pack_propagate(False)

            badge_color = COLOR_WARNING if service.get("recommended") else COLOR_ACCENT
            ctk.CTkLabel(card, text=service["badge"],
                          font=("Segoe UI", 9, "bold"), text_color=badge_color,
                          fg_color=COLOR_BG_MAIN, corner_radius=6,
                          width=90, height=22).pack(side="left", padx=(20, 15))

            mid = ctk.CTkFrame(card, fg_color="transparent")
            mid.pack(side="left", fill="y", pady=(12 if compact else 18))
            ctk.CTkLabel(mid, text=service["display"], font=("Segoe UI", 14, "bold"),
                         text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(anchor="w")
            if not compact:
                ctk.CTkLabel(mid, text=service["description"],
                             font=("Segoe UI", 11),
                             text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(anchor="w", pady=(2, 0))

            switch = ctk.CTkSwitch(card, text="Enabled", font=("Segoe UI", 11, "bold"),
                                    text_color=COLOR_TEXT_SECONDARY, progress_color=COLOR_SUCCESS,
                                    button_color=COLOR_TEXT_PRIMARY, button_hover_color=COLOR_TEXT_PRIMARY,
                                    fg_color=COLOR_BG_MAIN,
                                    command=lambda s=sid: self.on_toggle(s))
            switch.select()
            switch.pack(side="right", padx=25)

            self.service_widgets[sid] = {"card": card, "switch": switch, "meta": service}

    def on_toggle(self, service_id):
        sw = self.service_widgets[service_id]["switch"]
        new_state = bool(sw.get())

        if self.settings["confirm_changes"]:
            action = "ENABLE" if new_state else "DISABLE"
            if not messagebox.askyesno("Confirm Change",
                                        f"Are you sure you want to {action}\n\n{service_id}?"):
                (sw.select if not new_state else sw.deselect)()
                self.log(f"Cancelled: {service_id}")
                return

        if not is_admin():
            messagebox.showerror("Admin Required",
                                  "You must run the app as Administrator to change services.")
            (sw.select if not new_state else sw.deselect)()
            return

        self.log(f"Working: {service_id}...")
        self.update_idletasks()

        if new_state:
            ok, out = enable_service(service_id)
            action = "enabled"
        else:
            ok, out = disable_service(service_id)
            action = "disabled"

        if ok:
            self.log(f"OK: {service_id} {action}")
        else:
            self.log(f"FAILED: {service_id}")
            messagebox.showerror("Error", f"Failed to change {service_id}:\n\n{out[:300]}")
            (sw.select if not new_state else sw.deselect)()

        self.update_stats()

    def apply_recommended(self):
        if not is_admin():
            messagebox.showerror("Admin Required",
                                  "Run the app as Administrator to apply changes.")
            return

        recommended = [s for s in self.services if s.get("recommended")]
        if not messagebox.askyesno("Apply Recommended",
                                    f"This will DISABLE {len(recommended)} recommended services.\n\nContinue?"):
            return

        success = 0
        fail = 0
        for s in recommended:
            sid = s["id"]
            ok, _ = disable_service(sid)
            if ok:
                success += 1
                sw = self.service_widgets.get(sid, {}).get("switch")
                if sw:
                    sw.deselect()
            else:
                fail += 1

        self.update_stats()
        self.log(f"Recommended applied: {success} OK, {fail} failed")
        messagebox.showinfo("Done",
                             f"Recommended services disabled.\n\nSuccess: {success}\nFailed: {fail}")

    # ============ SETTINGS ============
    def build_settings_content(self, parent):
        ctk.CTkLabel(parent, text="Application Settings",
                     font=("Segoe UI", 15, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 12))

        sec1 = ctk.CTkFrame(parent, fg_color=COLOR_BG_CARD, corner_radius=14)
        sec1.pack(fill="x", pady=5)
        ctk.CTkLabel(sec1, text="Appearance", font=("Segoe UI", 13, "bold"),
                     text_color=COLOR_ACCENT).pack(anchor="w", padx=20, pady=(18, 8))

        self.dark_mode_switch = self.create_setting_row(
            sec1, "Dark Mode", "Use dark theme across the app",
            self.settings["dark_mode"], self.on_dark_mode_toggle)
        self.compact_view_switch = self.create_setting_row(
            sec1, "Compact View", "Show more services per screen",
            self.settings["compact_view"], self.on_compact_view_toggle)

        sec2 = ctk.CTkFrame(parent, fg_color=COLOR_BG_CARD, corner_radius=14)
        sec2.pack(fill="x", pady=15)
        ctk.CTkLabel(sec2, text="Behavior", font=("Segoe UI", 13, "bold"),
                     text_color=COLOR_ACCENT).pack(anchor="w", padx=20, pady=(18, 8))

        self.startup_switch = self.create_setting_row(
            sec2, "Start with Windows", "Launch automatically on system startup",
            self.settings["start_with_windows"], self.on_startup_toggle)
        self.confirm_switch = self.create_setting_row(
            sec2, "Confirm Changes", "Ask before enabling or disabling services",
            self.settings["confirm_changes"], self.on_confirm_toggle)

    def create_setting_row(self, parent, title, description, default, callback):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=8)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="y")
        ctk.CTkLabel(info, text=title, font=("Segoe UI", 13, "bold"),
                     text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(info, text=description, font=("Segoe UI", 11),
                     text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(anchor="w")

        sw = ctk.CTkSwitch(row, text="", progress_color=COLOR_SUCCESS,
                            button_color=COLOR_TEXT_PRIMARY, button_hover_color=COLOR_TEXT_PRIMARY,
                            fg_color=COLOR_BG_MAIN, command=callback)
        if default:
            sw.select()
        sw.pack(side="right")
        return sw

    def on_dark_mode_toggle(self):
        v = bool(self.dark_mode_switch.get())
        self.settings["dark_mode"] = v
        ctk.set_appearance_mode("Dark" if v else "Light")
        self.save_settings()
        self.log(f"Dark mode: {'ON' if v else 'OFF'}")

    def on_compact_view_toggle(self):
        v = bool(self.compact_view_switch.get())
        self.settings["compact_view"] = v
        self.save_settings()
        self.render_service_cards()
        self.log(f"Compact view: {'ON' if v else 'OFF'}")

    def on_confirm_toggle(self):
        v = bool(self.confirm_switch.get())
        self.settings["confirm_changes"] = v
        self.save_settings()
        self.log(f"Confirm changes: {'ON' if v else 'OFF'}")

    def on_startup_toggle(self):
        v = bool(self.startup_switch.get())
        self.settings["start_with_windows"] = v
        self.save_settings()
        if v:
            if self.enable_startup():
                self.log("Added to Windows startup")
            else:
                self.startup_switch.deselect()
                self.settings["start_with_windows"] = False
                self.save_settings()
                self.log("Failed to add to startup")
        else:
            self.disable_startup()
            self.log("Removed from Windows startup")

    def get_startup_folder(self):
        return os.path.join(os.environ.get("APPDATA", ""),
                             "Microsoft", "Windows", "Start Menu", "Programs", "Startup")

    def get_startup_file(self):
        return os.path.join(self.get_startup_folder(), "SmartServiceManager.bat")

    def enable_startup(self):
        try:
            if getattr(sys, "frozen", False):
                exe_path = sys.executable
                content = f'@echo off\nstart "" "{exe_path}"\n'
            else:
                folder = os.path.dirname(os.path.abspath(sys.argv[0]))
                content = f'@echo off\ncd /d "{folder}"\nstart "" pythonw main.py\n'
            with open(self.get_startup_file(), "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(e)
            return False

    def disable_startup(self):
        try:
            p = self.get_startup_file()
            if os.path.exists(p):
                os.remove(p)
        except Exception as e:
            print(e)

    # ============ ABOUT ============
    def build_about_content(self, parent):
        card = ctk.CTkFrame(parent, fg_color=COLOR_BG_CARD, corner_radius=14)
        card.pack(fill="x", pady=10)
        ctk.CTkLabel(card, text="Smart Service Manager",
                     font=("Segoe UI", 22, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(pady=(30, 5))
        ctk.CTkLabel(card, text="Version 1.0.0", font=("Segoe UI", 12),
                     text_color=COLOR_TEXT_SECONDARY).pack()
        ctk.CTkLabel(card, text="A modern tool to safely manage Windows services\nand improve system performance and privacy.",
                     font=("Segoe UI", 12), text_color=COLOR_TEXT_SECONDARY,
                     justify="center").pack(pady=(15, 25))

        ctk.CTkFrame(card, height=1, fg_color=COLOR_DIVIDER).pack(fill="x", padx=30, pady=5)
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(pady=20)
        for label, val in [("Developer", "heemoali"), ("License", "MIT"),
                           ("Language", "Python 3"), ("Built with", "CustomTkinter")]:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=label, font=("Segoe UI", 12),
                         text_color=COLOR_TEXT_SECONDARY, width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=("Segoe UI", 12, "bold"),
                         text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(side="left")

    def build_status_bar(self):
        bar = ctk.CTkFrame(self, fg_color=COLOR_BG_SIDEBAR, height=35, corner_radius=0)
        bar.grid(row=1, column=1, sticky="ew")
        bar.grid_propagate(False)
        self.status_text = ctk.CTkLabel(bar, text="  Ready.",
                                         font=("Segoe UI", 11),
                                         text_color=COLOR_TEXT_SECONDARY)
        self.status_text.pack(side="left", padx=15)
        ctk.CTkLabel(bar, text=f"{len(self.services)} services loaded  ",
                     font=("Segoe UI", 11),
                     text_color=COLOR_TEXT_SECONDARY).pack(side="right", padx=15)

    def log(self, message):
        self.status_text.configure(text=f"  {message}")


if __name__ == "__main__":
    app = ServiceManagerApp()
    app.mainloop()