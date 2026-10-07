"""xLocker UI (customtkinter). Talks only to storage + generator."""
import time
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import generator
from storage import VaultStore
from vault_crypto import WrongPassword

AUTOLOCK_MS = 3 * 60 * 1000
CLIP_CLEAR_MS = 30 * 1000
MIN_MASTER = 12
GRAY = ("gray40", "gray65")
MONO = ("Consolas", 17, "bold")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        self.title("xLocker")
        self.geometry("460x720")
        self.minsize(420, 660)
        self.store = VaultStore()
        self.current_pw = ""
        self.shown: set[str] = set()
        self._idle = self._clip = self._clip_value = None
        self._fails, self._blocked_until = 0, 0.0
        for ev in ("<Key>", "<Button>", "<Motion>"):
            self.bind_all(ev, self._touch, add="+")
        self.bind("<Return>", lambda e: self.submit())
        self.show_login()

    # ---------- helpers ----------
    def _wipe(self):
        for w in self.winfo_children():
            w.destroy()

    def _toast(self, text):
        t = ctk.CTkLabel(self, text=text, corner_radius=10, fg_color=("gray15", "gray85"),
                         text_color=("white", "black"), padx=14, pady=6)
        t.place(relx=0.5, rely=0.98, anchor="s")
        self.after(1800, t.destroy)

    def _arm(self):
        if self._idle:
            self.after_cancel(self._idle)
        self._idle = self.after(AUTOLOCK_MS, self.lock)

    def _touch(self, _=None):
        if self.store.unlocked:
            self._arm()

    def copy(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self._clip_value = text
        if self._clip:
            self.after_cancel(self._clip)
        self._clip = self.after(CLIP_CLEAR_MS, self._clear_clip)
        self._toast("Copied · clears in 30s")

    def _clear_clip(self):
        try:
            if self.clipboard_get() == self._clip_value:
                self.clipboard_clear()
                self.clipboard_append(" ")
        except tk.TclError:
            pass
        self._clip_value = None

    # ---------- login ----------
    def show_login(self):
        self._wipe()
        first = not self.store.exists()
        box = ctk.CTkFrame(self, corner_radius=18)
        box.pack(expand=True, fill="x", padx=28)
        ctk.CTkLabel(box, text="🔐 xLocker", font=("Segoe UI", 26, "bold")).pack(pady=(28, 4))
        ctk.CTkLabel(box, text=("Create a master password.\nIt cannot be recovered if forgotten."
                                if first else "Enter your master password."),
                     text_color=GRAY, justify="center").pack(pady=(0, 18))
        self.e1 = ctk.CTkEntry(box, show="•", height=40, placeholder_text="Master password")
        self.e1.pack(fill="x", padx=24, pady=4)
        self.e2 = None
        if first:
            self.e2 = ctk.CTkEntry(box, show="•", height=40, placeholder_text="Confirm master password")
            self.e2.pack(fill="x", padx=24, pady=4)
        self.msg = ctk.CTkLabel(box, text="", text_color="#dc2626")
        self.msg.pack(pady=(8, 0))
        self._btn_text = "Create vault" if first else "Unlock"
        self.btn = ctk.CTkButton(box, text=self._btn_text, height=42, command=self.submit)
        self.btn.pack(fill="x", padx=24, pady=(8, 28))
        self.e1.focus()

    def _err(self, text):
        self.msg.configure(text=text)

    def submit(self):
        if self.store.unlocked:
            return
        wait = self._blocked_until - time.time()
        if wait > 0:
            return self._err(f"Too many attempts. Wait {int(wait) + 1}s.")
        pw, e2 = self.e1.get(), self.e2
        first = e2 is not None
        if e2 is not None:
            if len(pw) < MIN_MASTER:
                return self._err(f"Use at least {MIN_MASTER} characters.")
            if pw != e2.get():
                return self._err("Passwords do not match.")
        self._err("")
        self.btn.configure(state="disabled", text="Working…")
        self.update_idletasks()
        try:
            self.store.create(pw) if first else self.store.unlock(pw)
        except WrongPassword:
            self._fails += 1
            if self._fails >= 5:
                self._blocked_until, self._fails = time.time() + 30, 0
            self._err("Wrong master password.")
            return
        except Exception:
            self._err("Vault file is damaged or unreadable.")
            return
        finally:
            if self.btn.winfo_exists():
                self.btn.configure(state="normal", text=self._btn_text)
        self._fails = 0
        self.show_main()

    def lock(self):
        for job in (self._idle, self._clip):
            if job:
                self.after_cancel(job)
        self._idle = self._clip = None
        self._clear_clip()
        self.store.lock()
        self.current_pw = ""
        self.shown.clear()
        self.show_login()

    # ---------- main ----------
    def show_main(self):
        self._wipe()
        self._arm()
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(14, 0))
        ctk.CTkLabel(head, text="🔐 xLocker", font=("Segoe UI", 20, "bold")).pack(side="left")
        ctk.CTkButton(head, text="Lock", width=70, height=30, command=self.lock,
                      fg_color=("gray80", "gray25"), text_color=("black", "white"),
                      hover_color=("gray70", "gray35")).pack(side="right")
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=12, pady=8)
        self._build_generator(tabs.add("Generator"))
        self._build_vault(tabs.add("Vault"))
        self.regen()

    def _build_generator(self, tab):
        self.out = ctk.CTkLabel(tab, text="", font=MONO, wraplength=370, height=70,
                                fg_color=("gray90", "gray20"), corner_radius=12)
        self.out.pack(fill="x", padx=8, pady=(8, 6))
        self.bar = ctk.CTkProgressBar(tab)
        self.bar.pack(fill="x", padx=8)
        self.info = ctk.CTkLabel(tab, text="", text_color=GRAY)
        self.info.pack(pady=(2, 8))
        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(fill="x", padx=8)
        ctk.CTkButton(row, text="Copy", command=lambda: self.copy(self.current_pw)).pack(
            side="left", expand=True, fill="x", padx=(0, 4))
        ctk.CTkButton(row, text="↻ New", command=self.regen, fg_color=("gray75", "gray30"),
                      text_color=("black", "white")).pack(side="left", expand=True, fill="x", padx=(4, 0))
        self.len_lbl = ctk.CTkLabel(tab, text="")
        self.len_lbl.pack(anchor="w", padx=12, pady=(12, 0))
        self.slider = ctk.CTkSlider(tab, from_=8, to=64, number_of_steps=56, command=lambda v: self.regen())
        self.slider.set(20)
        self.slider.pack(fill="x", padx=12, pady=(2, 6))
        self.opt = {}
        for key, label, default in (("upper", "Uppercase (A–Z)", True), ("lower", "Lowercase (a–z)", True),
                                    ("digits", "Numbers (0–9)", True), ("symbols", "Symbols (!@#$…)", True),
                                    ("ambig", "Avoid look-alikes (O/0, l/1)", False)):
            self.opt[key] = tk.BooleanVar(value=default)
            ctk.CTkSwitch(tab, text=label, variable=self.opt[key], command=self.regen).pack(
                anchor="w", padx=12, pady=3)
        self.site = ctk.CTkEntry(tab, placeholder_text="Site or app (e.g. Gmail)")
        self.site.pack(fill="x", padx=8, pady=(12, 4))
        self.user = ctk.CTkEntry(tab, placeholder_text="Username / email")
        self.user.pack(fill="x", padx=8, pady=4)
        ctk.CTkButton(tab, text="Save to vault", height=38, command=self.save_entry).pack(
            fill="x", padx=8, pady=6)

    def regen(self, *_):
        o = {k: v.get() for k, v in self.opt.items()}
        if not (o["upper"] or o["lower"] or o["digits"] or o["symbols"]):
            self.opt["lower"].set(True)
            o["lower"] = True
        n = int(self.slider.get())
        self.len_lbl.configure(text=f"Length: {n}")
        self.current_pw, bits = generator.generate(n, o["upper"], o["lower"], o["digits"],
                                                   o["symbols"], o["ambig"])
        label, color = generator.rate(bits)
        self.out.configure(text=self.current_pw)
        self.bar.configure(progress_color=color)
        self.bar.set(min(1, bits / 128))
        self.info.configure(text=f"{label} · ~{bits} bits of entropy")

    def save_entry(self):
        site = self.site.get().strip()
        if not site:
            return self._toast("Enter a site name")
        self.store.add(site, self.user.get().strip(), self.current_pw)
        self.site.delete(0, "end")
        self.user.delete(0, "end")
        self.refresh_list()
        self._toast("Saved to vault")

    # ---------- vault list ----------
    def _build_vault(self, tab):
        self.search = ctk.CTkEntry(tab, placeholder_text="Search…")
        self.search.pack(fill="x", padx=8, pady=(8, 4))
        self.search.bind("<KeyRelease>", lambda e: self.refresh_list())
        self.list = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.list.pack(fill="both", expand=True)
        self.refresh_list()

    def refresh_list(self):
        for w in self.list.winfo_children():
            w.destroy()
        q = self.search.get().lower()
        items = [i for i in self.store.items if q in (i["site"] + i["user"]).lower()]
        if not items:
            ctk.CTkLabel(self.list, text="No passwords yet.", text_color=GRAY).pack(pady=20)
        for it in items:
            card = ctk.CTkFrame(self.list, corner_radius=12)
            card.pack(fill="x", padx=4, pady=4)
            ctk.CTkLabel(card, text=it["site"], font=("Segoe UI", 15, "bold"), anchor="w").pack(
                fill="x", padx=12, pady=(8, 0))
            if it["user"]:
                ctk.CTkLabel(card, text=it["user"], text_color=GRAY, anchor="w").pack(fill="x", padx=12)
            shown = it["id"] in self.shown
            ctk.CTkLabel(card, text=it["password"] if shown else "•" * 12, font=("Consolas", 13),
                         anchor="w", wraplength=330, justify="left").pack(fill="x", padx=12, pady=2)
            bar = ctk.CTkFrame(card, fg_color="transparent")
            bar.pack(fill="x", padx=8, pady=(2, 8))
            for text, cmd, red in (("Hide" if shown else "Show", lambda i=it: self.toggle(i), False),
                                   ("Copy", lambda i=it: self.copy(i["password"]), False),
                                   ("User", lambda i=it: self.copy(i["user"]), False),
                                   ("Delete", lambda i=it: self.remove(i), True)):
                button = ctk.CTkButton(bar, text=text, width=64, height=28, command=cmd)
                if red:
                    button.configure(fg_color="#dc2626", hover_color="#b91c1c")
                button.pack(side="left", padx=3)

    def toggle(self, it):
        self.shown ^= {it["id"]}
        self.refresh_list()

    def remove(self, it):
        if messagebox.askyesno("Delete", f'Delete "{it["site"]}"?'):
            self.store.delete(it["id"])
            self.refresh_list()


if __name__ == "__main__":
    App().mainloop()
