"""Flash Firmware window for the desktop GUI — detect chip, fetch firmware, flash."""

import os
import queue
import threading

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from marauder_core import flasher
from marauder_core.uihelp import Tooltip, GLOSSARY

BG = "#0b0f0a"
PANEL = "#11160f"
FG = "#c8f7c5"
ACCENT = "#39ff14"
DANGER = "#ff4d4d"
MUTED = "#7a8f76"


class FlasherWindow(tk.Toplevel):
    def __init__(self, master, controller, default_port=""):
        super().__init__(master)
        self.ctl = controller
        self.title("Flash Marauder Firmware")
        self.configure(bg=PANEL)
        self.geometry("760x620")

        self.q: "queue.Queue[str]" = queue.Queue()
        self.chip = None
        self.assets = []
        self.tag = ""
        self._label_to_asset = {}
        self._busy = False
        self._need_refill = False   # set by worker threads; applied on the UI thread in _poll
        self._poll_id = None
        self._closed = False

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll()
        if not flasher.esptool_available():
            self._log("[!] esptool not found. Install it:  pip install esptool")

        if default_port:
            self.port_var.set(default_port)

    def _on_close(self):
        self._closed = True
        if self._poll_id is not None:
            try:
                self.after_cancel(self._poll_id)
            except Exception:
                pass
        self.destroy()

    # --- layout ----------------------------------------------------------- #
    def _build(self):
        pad = {"padx": 8, "pady": 4}

        row = tk.Frame(self, bg=PANEL); row.pack(fill="x", **pad)
        tk.Label(row, text="Port:", bg=PANEL, fg=FG).pack(side="left")
        self.port_var = tk.StringVar()
        port_ent = ttk.Entry(row, textvariable=self.port_var, width=24)
        port_ent.pack(side="left", padx=6)
        Tooltip(port_ent, "Serial port of the board to flash (e.g. /dev/ttyUSB0 or COM5). "
                "The live console session is dropped automatically so esptool can use it.")
        detect_btn = ttk.Button(row, text="Detect chip", command=self._detect)
        detect_btn.pack(side="left", padx=4)
        Tooltip(detect_btn, "Ask esptool which ESP32 chip is on this port "
                "(esp32, esp32s3, ...). This picks the right firmware variant and offsets.")
        self.chip_lbl = tk.Label(row, text="chip: ?", bg=PANEL, fg=MUTED)
        self.chip_lbl.pack(side="left", padx=8)
        Tooltip(self.chip_lbl, "The detected chip family. Shows '?' until you detect "
                "(or flash, which auto-detects first).")

        # mode
        mrow = tk.Frame(self, bg=PANEL); mrow.pack(fill="x", **pad)
        tk.Label(mrow, text="Mode:", bg=PANEL, fg=FG).pack(side="left")
        self.mode = tk.StringVar(value="app")
        mode_app = ttk.Radiobutton(mrow, text="Update app only (existing board)", value="app",
                                   variable=self.mode)
        mode_app.pack(side="left", padx=6)
        Tooltip(mode_app, GLOSSARY["app-only flash"])
        mode_full = ttk.Radiobutton(mrow, text="Full flash (blank board)", value="full",
                                    variable=self.mode)
        mode_full.pack(side="left", padx=6)
        Tooltip(mode_full, GLOSSARY["full flash"])

        # source
        srow = tk.Frame(self, bg=PANEL); srow.pack(fill="x", **pad)
        tk.Label(srow, text="Firmware:", bg=PANEL, fg=FG).pack(side="left")
        self.source = tk.StringVar(value="download")
        src_dl = ttk.Radiobutton(srow, text="Download latest release", value="download",
                                 variable=self.source)
        src_dl.pack(side="left", padx=6)
        Tooltip(src_dl, "Pull the latest official Marauder release from GitHub and "
                "choose a board variant below.")
        src_local = ttk.Radiobutton(srow, text="Local .bin", value="local",
                                     variable=self.source)
        src_local.pack(side="left", padx=6)
        Tooltip(src_local, "Flash an application .bin you already have on disk "
                "(use the Browse button below).")

        # download row
        drow = tk.Frame(self, bg=PANEL); drow.pack(fill="x", **pad)
        load_btn = ttk.Button(drow, text="Load release list", command=self._load_release)
        load_btn.pack(side="left")
        Tooltip(load_btn, "Fetch the latest release's firmware list from GitHub and "
                "populate the variant menu.")
        self.showall = tk.BooleanVar(value=False)
        showall_cb = ttk.Checkbutton(drow, text="show all chips", variable=self.showall,
                                     command=self._refill_variants)
        showall_cb.pack(side="left", padx=6)
        Tooltip(showall_cb, "By default only variants matching the detected chip are listed. "
                "Tick this to show every variant in the release.")
        self.variant_var = tk.StringVar()
        self.variant_combo = ttk.Combobox(drow, textvariable=self.variant_var, width=46, state="readonly")
        self.variant_combo.pack(side="left", padx=6)
        Tooltip(self.variant_combo, "The specific board/firmware build to download and flash. "
                "Match it to your exact board (display, chip, revision).")

        # local row
        lrow = tk.Frame(self, bg=PANEL); lrow.pack(fill="x", **pad)
        self.local_var = tk.StringVar()
        local_ent = ttk.Entry(lrow, textvariable=self.local_var, width=52)
        local_ent.pack(side="left", padx=(0, 6))
        Tooltip(local_ent, "Path to a local application .bin to flash when 'Local .bin' "
                "is selected.")
        browse_btn = ttk.Button(lrow, text="Browse .bin", command=self._browse)
        browse_btn.pack(side="left")
        Tooltip(browse_btn, "Pick an application .bin from disk; selecting one also "
                "switches the source to 'Local .bin'.")

        # --- opt-in: Suicide build (flash a pre-provisioned hardened bundle) ---
        # Plain flashing above stays the default; this only engages when ticked.
        surow = tk.Frame(self, bg=PANEL); surow.pack(fill="x", **pad)
        self.suicide = tk.BooleanVar(value=False)
        suicide_cb = ttk.Checkbutton(surow, text="Suicide build (flash provisioned bundle)",
                                     variable=self.suicide, command=self._toggle_suicide)
        suicide_cb.pack(side="left")
        Tooltip(suicide_cb, GLOSSARY["suicide build"] + "\n\nWhen ticked, FLASH writes the "
                "bundle folder's manifest files instead of the firmware selected above. "
                "This app only flashes a bundle — it never burns eFuses.")

        # bundle row — hidden until the suicide checkbox is ticked
        self.bundle_row = tk.Frame(self, bg=PANEL)
        tk.Label(self.bundle_row, text="Bundle:", bg=PANEL, fg=FG).pack(side="left")
        self.bundle_var = tk.StringVar()
        bundle_ent = ttk.Entry(self.bundle_row, textvariable=self.bundle_var, width=48)
        bundle_ent.pack(side="left", padx=6)
        Tooltip(bundle_ent, GLOSSARY["bundle"])
        bundle_browse = ttk.Button(self.bundle_row, text="Browse folder",
                                   command=self._browse_bundle)
        bundle_browse.pack(side="left")
        Tooltip(bundle_browse, "Pick the bundle folder produced by the Suicide-Marauder "
                "provisioner (must contain bundle.json plus its .bin images).")

        self.suicide_lbl = tk.Label(
            self.bundle_row,
            text="owner-only / authorized device — flashes a prepared bundle; no eFuses burned",
            bg=PANEL, fg=DANGER, wraplength=300, justify="left")
        self.suicide_lbl.pack(side="left", padx=8)
        Tooltip(self.suicide_lbl, "Defensive, owner-only feature: provisioning (passwords, "
                "eFuses, T2) happens in the Suicide-Marauder repo. Only flash bundles for "
                "devices you own and are authorized to wipe.")

        # baud + actions
        arow = tk.Frame(self, bg=PANEL); arow.pack(fill="x", **pad)
        tk.Label(arow, text="Baud:", bg=PANEL, fg=FG).pack(side="left")
        self.baud = tk.StringVar(value="921600")
        baud_combo = ttk.Combobox(arow, textvariable=self.baud, width=10, state="readonly",
                                  values=["115200", "460800", "921600"])
        baud_combo.pack(side="left", padx=6)
        Tooltip(baud_combo, GLOSSARY["baud"])
        self.flash_btn = ttk.Button(arow, text="⚡ FLASH", command=self._flash)
        self.flash_btn.pack(side="left", padx=10)
        Tooltip(self.flash_btn, "Flash the selected firmware to the board. Confirms first, "
                "and won't run while another flash/erase is in progress.")
        erase_btn = ttk.Button(arow, text="Erase flash", command=self._erase)
        erase_btn.pack(side="left")
        Tooltip(erase_btn, "Wipe the entire flash chip. The board has no firmware afterwards — "
                "you'll need a full flash to restore it.")

        tk.Label(self, text="Tip: classic ESP32 Gold boards → pick a non-S3 variant "
                 "(e.g. 'Generic ESP32 / original v4'). S3 → MultiBoard S3.",
                 bg=PANEL, fg=MUTED, wraplength=720, justify="left").pack(fill="x", padx=8)

        self.console = tk.Text(self, bg="#05080a", fg=ACCENT, wrap="word",
                               state="disabled", font=("monospace", 9))
        self.console.pack(fill="both", expand=True, padx=8, pady=6)

    # --- helpers ---------------------------------------------------------- #
    def _log(self, s):
        self.q.put(s)

    def _poll(self):
        if self._closed or not self.winfo_exists():
            return
        try:
            while True:
                line = self.q.get_nowait()
                self.console.config(state="normal")
                self.console.insert("end", line + "\n")
                self.console.see("end")
                self.console.config(state="disabled")
        except queue.Empty:
            pass
        # all widget updates happen here on the UI thread (workers only set state/flags)
        self.flash_btn.config(state="disabled" if self._busy else "normal")
        self.chip_lbl.config(text=f"chip: {self.chip or '?'}",
                             fg=ACCENT if self.chip else MUTED)
        if self._need_refill:
            self._need_refill = False
            self._refill_variants()
        self._poll_id = self.after(40, self._poll)

    def _free_port(self):
        """esptool needs exclusive access — drop the live serial connection."""
        if self.ctl and self.ctl.connected:
            self._log("[i] disconnecting live serial session so esptool can use the port")
            self.ctl.disconnect()

    def _worker(self, fn):
        if self._busy:
            messagebox.showinfo("Busy", "A flash/erase is already running.")
            return
        self._busy = True
        self.flash_btn.config(state="disabled")

        def run():
            try:
                fn()
            except Exception as e:
                self._log(f"[error] {e}")
            finally:
                self._busy = False     # _poll re-enables the button on the UI thread

        threading.Thread(target=run, daemon=True).start()

    # --- actions ---------------------------------------------------------- #
    def _detect(self):
        port = self.port_var.get().strip()
        if not port:
            messagebox.showwarning("Port", "Enter the serial port first."); return
        self._free_port()

        def job():
            self._log("[*] detecting chip...")
            self.chip = flasher.detect_chip(port, self._log)
            self._need_refill = True
        self._worker(job)

    def _load_release(self):
        def job():
            self._log("[*] fetching latest release...")
            self.tag, self.assets = flasher.latest_release()
            self._log(f"[i] {self.tag}: {len(self.assets)} firmware variants")
            self._need_refill = True
        self._worker(job)

    def _refill_variants(self):
        if not self.assets:
            return
        items = self.assets if (self.showall.get() or not self.chip) \
            else flasher.variants_for_chip(self.assets, self.chip)
        self._label_to_asset = {f"{a['label']}  [{a['name']}]": a for a in items}
        labels = list(self._label_to_asset)
        self.variant_combo["values"] = labels
        if labels:
            default = flasher.default_variant(items, self.chip) if self.chip else None
            pick = next((l for l, a in self._label_to_asset.items() if default and a["name"] == default["name"]), labels[0])
            self.variant_var.set(pick)

    def _browse(self):
        path = filedialog.askopenfilename(title="Select firmware .bin",
                                          filetypes=[("Firmware", "*.bin"), ("All", "*.*")])
        if path:
            self.local_var.set(path)
            self.source.set("local")

    def _toggle_suicide(self):
        """Reveal/hide the bundle-dir row when the opt-in suicide checkbox flips."""
        if self.suicide.get():
            # show it right under the checkbox (before the baud/actions row)
            self.bundle_row.pack(fill="x", padx=8, pady=4, before=self.flash_btn.master)
        else:
            self.bundle_row.pack_forget()

    def _browse_bundle(self):
        path = filedialog.askdirectory(title="Select provisioned bundle folder")
        if path:
            self.bundle_var.set(path)

    def _resolve_chip(self, port):
        if self.chip:
            return self.chip
        self._log("[*] chip unknown — detecting first...")
        self.chip = flasher.detect_chip(port, self._log)
        self._need_refill = True       # keep the variant list/chip label consistent
        return self.chip

    def _flash(self):
        port = self.port_var.get().strip()
        if not port:
            messagebox.showwarning("Port", "Enter the serial port first."); return
        baud = int(self.baud.get())

        # Opt-in suicide path: flash a pre-provisioned bundle instead of normal firmware.
        if self.suicide.get():
            self._flash_suicide(port, baud); return

        mode = self.mode.get()
        source = self.source.get()

        if source == "download" and not self._label_to_asset:
            messagebox.showinfo("Firmware", "Click 'Load release list' and pick a variant."); return
        if source == "local" and not self.local_var.get().strip():
            messagebox.showinfo("Firmware", "Browse to a local .bin first."); return

        if not messagebox.askyesno("Confirm flash",
                                   f"Flash {mode} via {port} @ {baud}?\nDo not unplug during flashing."):
            return
        # capture all widget values on the UI thread BEFORE starting the worker
        asset = self._label_to_asset.get(self.variant_var.get()) if source == "download" else None
        local = self.local_var.get().strip()
        self._free_port()

        def job():
            chip = self._resolve_chip(port)
            if not chip:
                self._log("[error] could not detect chip; aborting"); return
            cache = flasher.cache_dir()

            if source == "download":
                if not asset:
                    self._log("[error] no variant selected"); return
                if asset["chip"] != chip:
                    self._log(f"[!] WARNING: variant is for {asset['chip']} but chip is {chip}")
                app = flasher.download_to(asset["url"], os.path.join(cache, asset["name"]), self._log)
            else:
                app = local

            support = None
            if mode == "full":
                self._log("[*] fetching bootloader/partitions/boot_app0...")
                support = flasher.support_files(chip, cache, self._log)

            self._log(f"[*] flashing ({mode}) {os.path.basename(app)} to {chip}...")
            rc = flasher.flash(port, chip, app, self._log, mode=mode, baud=baud, support=support)
            self._log("[✓] done — power-cycle the board" if rc == 0 else f"[x] esptool exit {rc}")
        self._worker(job)

    def _flash_suicide(self, port, baud):
        """Opt-in path: flash a pre-provisioned Suicide-Marauder bundle (no eFuses burned)."""
        bundle_dir = self.bundle_var.get().strip()
        if not bundle_dir:
            messagebox.showinfo("Bundle", "Browse to a provisioned bundle folder first."); return
        # Validate the manifest up front (on the UI thread) so a bad path/folder is caught
        # before we drop the live connection or spawn esptool.
        try:
            manifest = flasher.read_bundle_manifest(bundle_dir)
        except (FileNotFoundError, ValueError) as e:
            messagebox.showerror("Bundle", f"Not a valid bundle:\n{e}"); return

        man_chip = manifest.get("chip")
        if not messagebox.askyesno(
                "Confirm SUICIDE-build flash",
                f"Flash provisioned bundle via {port} @ {baud}?\n\n"
                f"Folder: {bundle_dir}\n"
                f"Bundle chip: {man_chip or 'unspecified'}\n\n"
                "Owner-only / authorized devices. This writes the bundle's images; it does "
                "NOT burn eFuses.\nDo not unplug during flashing."):
            return

        # Capture values on the UI thread, then run on a worker (mirrors _flash()).
        chip = man_chip or self.chip
        self._free_port()

        def job():
            use_chip = chip or self._resolve_chip(port)
            if not use_chip:
                self._log("[error] chip unknown and not in bundle; detect first or aborting"); return
            self._log(f"[*] flashing suicide bundle to {use_chip} from {bundle_dir} ...")
            rc = flasher.flash_suicide(port, use_chip, bundle_dir, self._log, baud=baud)
            self._log("[✓] done — power-cycle the board" if rc == 0 else f"[x] esptool exit {rc}")
        self._worker(job)

    def _erase(self):
        port = self.port_var.get().strip()
        if not port:
            messagebox.showwarning("Port", "Enter the serial port first."); return
        if not messagebox.askyesno("Erase", "Erase the entire flash? This wipes the firmware."):
            return
        self._free_port()

        def job():
            chip = self._resolve_chip(port) or "esp32"
            flasher.erase(port, chip, self._log)
        self._worker(job)
