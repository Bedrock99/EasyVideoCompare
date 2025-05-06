# auswahl_dialog.py
from version import __version__

import tkinter as tk
from tkinter import ttk, messagebox, Scale
from tkinter.ttk import Style

from PIL import Image, ImageTk
import os
import cv2


def get_video_info(video_pfad):
    """Extrahiert Videoinformationen inklusive lesbarer Dateigröße."""
    try:
        cap = cv2.VideoCapture(video_pfad)
        if not cap.isOpened():
            return None
        info = {}
        info['filename'] = os.path.basename(video_pfad)
        info['frame_width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        info['frame_height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        info['fps'] = cap.get(cv2.CAP_PROP_FPS)
        info['frame_count'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Bitrate (ungefähre)
        duration_seconds = info['frame_count'] / info['fps'] if info['fps'] > 0 else 0
        file_size_bytes = os.path.getsize(video_pfad)
        info['bitrate_kbps'] = int((file_size_bytes * 8) / (duration_seconds * 1000)) if duration_seconds > 0 else 0

        # Codec
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        info['codec'] = chr(fourcc & 0xFF) + chr((fourcc >> 8) & 0xFF) + chr((fourcc >> 16) & 0xFF) + chr((fourcc >> 24) & 0xFF)

        # Lesbare Dateigröße
        size_bytes = os.path.getsize(video_pfad)
        if size_bytes < 1024:
            info['filesize_readable'] = f"{size_bytes} Bytes"
        elif size_bytes < (1024 * 1024):
            info['filesize_readable'] = f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < (1024 * 1024 * 1024):
            info['filesize_readable'] = f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            info['filesize_readable'] = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

        cap.release()
        return info
    except Exception as e:
        print(f"Fehler beim Abrufen von Videoinformationen für {video_pfad}: {e}")
        return None


def extrahiere_keyframes(video_pfad):
    """Extrahiert alle Keyframes als PIL Images."""
    try:
        cap = cv2.VideoCapture(video_pfad)
        if not cap.isOpened():
            return []
        keyframes = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # Hier müsstest du deine Logik zur Keyframe-Erkennung einfügen.
            # Für dieses Beispiel nehmen wir einfach jeden N-ten Frame.
            if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) % 30 == 0:  # Beispiel: Jeder 30. Frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                keyframes.append(Image.fromarray(frame_rgb))
        cap.release()
        return keyframes
    except Exception as e:
        print(f"Fehler beim Extrahieren von Keyframes für {video_pfad}: {e}")
        return []


class AuswahlDialog(tk.Toplevel):
    def __init__(self, parent, vergleichs_ergebnisse, schwelle, alle_thumbnails, alle_video_pfade):
        super().__init__(parent)
        self.title(f"Ähnliche Videopaare überprüfen - v{__version__}")
        self.geometry("600x500")  # Etwas mehr Höhe für den Ähnlichkeitswert und Trackbars
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        self.vergleichs_ergebnisse = [(pair, aehnlichkeit) for pair, aehnlichkeit in vergleichs_ergebnisse.items() if aehnlichkeit and aehnlichkeit[0] <= schwelle]
        self.alle_thumbnails = alle_thumbnails
        self.alle_video_pfade = alle_video_pfade
        self.aktueller_index = 0
        self.max_index = len(self.vergleichs_ergebnisse) - 1
        self.aktuelle_keyframes_links = []
        self.aktuelle_keyframes_rechts = []
        self.num_keyframes_links = 0
        self.num_keyframes_rechts = 0

        self.similarity_label = None
        self.video_display_frame = None
        self.left_frame = None
        self.right_frame = None
        self.keyframe_scale_left = None
        self.keyframe_scale_right = None
        self.keyframe_image_label_left = None
        self.keyframe_image_label_right = None
        self.info_label_left = None
        self.info_label_right = None
        self.paar_anzeige_label = None

        self.create_widgets()
        self.zeige_aktuelles_paar()

        self.resize_timer = None
        self.resize_delay = 200  # Millisekunden Verzögerung, bis Resize als beendet gilt

        self.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        if self.resize_timer:
            self.after_cancel(self.resize_timer)  # Alten Timer abbrechen

        self.resize_timer = self.after(self.resize_delay, self.on_resize_end)

    def on_resize_end(self):
        self.resize_timer = None
        if self.aktuelle_keyframes_links_pil and self.keyframe_scale_left:
            self.zeige_keyframe_links(self.keyframe_scale_left.get())
        if self.aktuelle_keyframes_rechts_pil and self.keyframe_scale_right:
            self.zeige_keyframe_rechts(self.keyframe_scale_right.get())

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=0)  # Zeile für Similarity Label
        main_frame.grid_rowconfigure(2, weight=1)  # Zeile für Video Display
        main_frame.grid_rowconfigure(3, weight=0)  # Zeile für Buttons
        main_frame.grid_rowconfigure(4, weight=0)  # Zeile für Navigation
        main_frame.grid_columnconfigure(0, weight=1)

        self.similarity_label = ttk.Label(main_frame, text="Ähnlichkeit: ")
        self.similarity_label.grid(row=1, column=0, pady=5, sticky="ew")

        # Frames für die Videoanzeigen
        self.video_display_frame = ttk.Frame(main_frame)
        self.video_display_frame.grid(row=2, column=0, sticky="nsew")
        self.video_display_frame.grid_columnconfigure(0, weight=1)
        self.video_display_frame.grid_columnconfigure(1, weight=1)
        self.video_display_frame.grid_rowconfigure(0, weight=1)

        self.left_frame = ttk.LabelFrame(self.video_display_frame, text="")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        self.right_frame = ttk.LabelFrame(self.video_display_frame, text="")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.keyframe_image_label_left = ttk.Label(self.left_frame)
        self.keyframe_image_label_left.grid(row=0, column=0, sticky="nsew")
        self.keyframe_scale_left = Scale(self.left_frame, from_=0, to=0, orient=tk.HORIZONTAL, command=self.zeige_keyframe_links)
        self.keyframe_scale_left.grid(row=1, column=0, sticky="ew")

        self.info_label_left = ttk.Label(self.left_frame, text="")
        self.info_label_left.grid(row=2, column=0, sticky="ew", pady=5)

        self.keyframe_image_label_right = ttk.Label(self.right_frame)
        self.keyframe_image_label_right.grid(row=0, column=0, sticky="nsew")
        self.keyframe_scale_right = Scale(self.right_frame, from_=0, to=0, orient=tk.HORIZONTAL, command=self.zeige_keyframe_rechts)
        self.keyframe_scale_right.grid(row=1, column=0, sticky="ew")

        self.info_label_right = ttk.Label(self.right_frame, text="")
        self.info_label_right.grid(row=2, column=0, sticky="ew", pady=5)

        # Buttons zur Auswahl
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        behalten_links_button = ttk.Button(button_frame, text="Linkes Video behalten", command=self.behalte_links)
        behalten_links_button.grid(row=0, column=0, padx=5, sticky="ew")

        behalten_beide_button = ttk.Button(button_frame, text="Beide Videos behalten", command=self.behalte_beide)
        behalten_beide_button.grid(row=0, column=1, padx=5, sticky="ew")

        behalten_rechts_button = ttk.Button(button_frame, text="Rechtes Video behalten", command=self.behalte_rechts)
        behalten_rechts_button.grid(row=0, column=2, padx=5, sticky="ew")

        # Navigation durch Paare
        navigation_frame = ttk.Frame(main_frame)
        navigation_frame.grid(row=4, column=0, pady=5, sticky="ew")
        navigation_frame.grid_columnconfigure(0, weight=0)
        navigation_frame.grid_columnconfigure(1, weight=1)

        prev_button = ttk.Button(navigation_frame, text="Vorheriges Paar", command=self.zeige_vorheriges_paar)
        prev_button.grid(row=0, column=0, padx=5, sticky="w")

        self.paar_anzeige_label = ttk.Label(navigation_frame, text="")
        self.paar_anzeige_label.grid(row=0, column=1, padx=5, sticky="ew")

    def zeige_aktuelles_paar(self):
        if not self.vergleichs_ergebnisse:
            messagebox.showinfo("Info", "Keine ähnlichen Videopaare gefunden.")
            self.destroy()
            return

        if 0 <= self.aktueller_index < len(self.vergleichs_ergebnisse):
            (pfad1, pfad2), aehnlichkeit = self.vergleichs_ergebnisse[self.aktueller_index]
            similarity_value = f"{aehnlichkeit[0]:.4f}"
            self.similarity_label.config(text=f"Ähnlichkeit: {similarity_value}")
            self.paar_anzeige_label.config(text=f"Paar {self.aktueller_index + 1} / {len(self.vergleichs_ergebnisse)}")

            if os.path.exists(pfad1) and os.path.exists(pfad2):
                self.left_frame.config(text=os.path.basename(pfad1))
                self.right_frame.config(text=os.path.basename(pfad2))

                info_links = get_video_info(pfad1)
                info_rechts = get_video_info(pfad2)

                if info_links:
                    self.info_label_left.config(
                        text=f"{info_links['frame_width']}x{info_links['frame_height']} @ {info_links['fps']:.2f} | "
                             f"{info_links['bitrate_kbps']} kbps | {info_links['codec']} | {info_links['filesize_readable']}")
                else:
                    self.info_label_left.config(text="Informationen konnten nicht abgerufen werden.")

                if info_rechts:
                    self.info_label_right.config(
                        text=f"{info_rechts['frame_width']}x{info_rechts['frame_height']} @ {info_rechts['fps']:.2f} | "
                             f"{info_rechts['bitrate_kbps']} kbps | {info_rechts['codec']} | {info_rechts['filesize_readable']}")
                else:
                    self.info_label_right.config(text="Informationen konnten nicht abgerufen werden.")

                self.aktuelle_keyframes_links_pil = extrahiere_keyframes(pfad1)
                self.aktuelle_keyframes_rechts_pil = extrahiere_keyframes(pfad2)
                self.num_keyframes_links = len(self.aktuelle_keyframes_links_pil)
                self.num_keyframes_rechts = len(self.aktuelle_keyframes_rechts_pil)

                self.keyframe_scale_left.config(to=self.num_keyframes_links - 1 if self.num_keyframes_links > 0 else 0)
                self.keyframe_scale_right.config(to=self.num_keyframes_rechts - 1 if self.num_keyframes_rechts > 0 else 0)

                if self.aktuelle_keyframes_links_pil:
                    self.original_image_left = self.aktuelle_keyframes_links_pil[0]
                else:
                    self.original_image_left = None

                if self.aktuelle_keyframes_rechts_pil:
                    self.original_image_right = self.aktuelle_keyframes_rechts_pil[0]
                else:
                    self.original_image_right = None

                self.zeige_keyframe_links(0)
                self.zeige_keyframe_rechts(0)

                # Synchronisiere die Trackbars, wenn sie sich ändern
                self.keyframe_scale_left.config(command=self.synchronisiere_keyframes_links)
                self.keyframe_scale_right.config(command=self.synchronisiere_keyframes_rechts)

            else:
                # Eines oder beide Videos existieren nicht mehr, überspringen
                self.naechstes_paar()
        else:
            self.destroy()

    def zeige_keyframe(self, keyframes, index, label, original_image_attr):
        if keyframes and 0 <= index < len(keyframes):
            original_image = getattr(self, original_image_attr)
            target_width = label.winfo_width()
            target_height = label.winfo_height()

            if target_width > 0 and target_height > 0:
                resized_image = original_image.copy()  # Wichtig: Kopie erstellen
                resized_image.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized_image)
                label.config(image=photo)
                label.image = photo  # Keep a reference!
            else:
                # Größe ist noch nicht bekannt
                pass
        else:
            label.config(image=None)
            label.image = None

    def zeige_keyframe_links(self, value):
        try:
            index_links = int(value)
            if self.aktuelle_keyframes_links_pil:
                self.original_image_left = self.aktuelle_keyframes_links_pil[index_links]
                self.zeige_keyframe(self.aktuelle_keyframes_links_pil, index_links, self.keyframe_image_label_left, "original_image_left")
                # Synchronisiere die rechte Trackbar direkt auf den gleichen Index
                if self.num_keyframes_rechts > 0 and 0 <= index_links < self.num_keyframes_rechts:
                    self.keyframe_scale_right.set(index_links)
                    if self.aktuelle_keyframes_rechts_pil:
                        self.original_image_right = self.aktuelle_keyframes_rechts_pil[index_links]
                        self.zeige_keyframe(self.aktuelle_keyframes_rechts_pil, index_links, self.keyframe_image_label_right, "original_image_right")
                else:
                    # Stelle sicher, dass die rechte Trackbar im gültigen Bereich bleibt
                    self.keyframe_scale_right.set(min(index_links, self.num_keyframes_rechts - 1) if self.num_keyframes_rechts > 0 else 0)
                    if self.aktuelle_keyframes_rechts_pil:
                        self.original_image_right = self.aktuelle_keyframes_rechts_pil[min(index_links, self.num_keyframes_rechts - 1)] if self.num_keyframes_rechts > 0 else None
                        self.zeige_keyframe(self.aktuelle_keyframes_rechts_pil, min(index_links, self.num_keyframes_rechts - 1) if self.num_keyframes_rechts > 0 else 0, self.keyframe_image_label_right, "original_image_right")
        except ValueError:
            pass

    def zeige_keyframe_rechts(self, value):
        try:
            index_rechts = int(value)
            if self.aktuelle_keyframes_rechts_pil:
                self.original_image_right = self.aktuelle_keyframes_rechts_pil[index_rechts]
                self.zeige_keyframe(self.aktuelle_keyframes_rechts_pil, index_rechts, self.keyframe_image_label_right, "original_image_right")
                # Synchronisiere die linke Trackbar direkt auf den gleichen Index
                if self.num_keyframes_links > 0 and 0 <= index_rechts < self.num_keyframes_links:
                    self.keyframe_scale_left.set(index_rechts)
                    if self.aktuelle_keyframes_links_pil:
                        self.original_image_left = self.aktuelle_keyframes_links_pil[index_rechts]
                        self.zeige_keyframe(self.aktuelle_keyframes_links_pil, index_rechts, self.keyframe_image_label_left, "original_image_left")
                else:
                    # Stelle sicher, dass die linke Trackbar im gültigen Bereich bleibt
                    self.keyframe_scale_left.set(min(index_rechts, self.num_keyframes_links - 1) if self.num_keyframes_links > 0 else 0)
                    if self.aktuelle_keyframes_links_pil:
                        self.original_image_left = self.aktuelle_keyframes_links_pil[min(index_rechts, self.num_keyframes_links - 1)] if self.num_keyframes_links > 0 else None
                        self.zeige_keyframe(self.aktuelle_keyframes_links_pil, min(index_rechts, self.num_keyframes_links - 1) if self.num_keyframes_links > 0 else 0, self.keyframe_image_label_left, "original_image_left")
        except ValueError:
            pass
    def synchronisiere_keyframes_links(self, value):
        self.zeige_keyframe_links(value)

    def synchronisiere_keyframes_rechts(self, value):
        self.zeige_keyframe_rechts(value)

    def zeige_vorheriges_paar(self):
        self.aktueller_index -= 1
        if self.aktueller_index < 0:
            self.aktueller_index = 0
        self.zeige_aktuelles_paar()

    def zeige_naechstes_paar(self):
        self.aktueller_index += 1
        if self.aktueller_index > self.max_index:
            self.destroy()
            return
        self.zeige_aktuelles_paar()

    def naechstes_paar(self):
        self.aktueller_index += 1
        if self.aktueller_index > self.max_index:
            self.destroy()
            return
        self.zeige_aktuelles_paar()

    def behalte_links(self):
        if 0 <= self.aktueller_index < len(self.vergleichs_ergebnisse):
            (pfad1, pfad2), _ = self.vergleichs_ergebnisse[self.aktueller_index]
            if os.path.exists(pfad2):
                if messagebox.askyesno("Löschen bestätigen", f"Möchtest du '{os.path.basename(pfad2)}' wirklich löschen?"):
                    try:
                        os.remove(pfad2)
                        self.update_status_im_hauptfenster(f"Gelöscht: {os.path.basename(pfad2)}")
                    except Exception as e:
                        messagebox.showerror("Fehler", f"Fehler beim Löschen von '{os.path.basename(pfad2)}': {e}")
            self.naechstes_paar()

    def behalte_rechts(self):
        if 0 <= self.aktueller_index < len(self.vergleichs_ergebnisse):
            (pfad1, pfad2), _ = self.vergleichs_ergebnisse[self.aktueller_index]
            if os.path.exists(pfad1):
                if messagebox.askyesno("Löschen bestätigen", f"Möchtest du '{os.path.basename(pfad1)}' wirklich löschen?"):
                    try:
                        os.remove(pfad1)
                        self.update_status_im_hauptfenster(f"Gelöscht: {os.path.basename(pfad1)}")
                    except Exception as e:
                        messagebox.showerror("Fehler", f"Fehler beim Löschen von '{os.path.basename(pfad1)}': {e}")
            self.naechstes_paar()

    def behalte_beide(self):
        self.naechstes_paar()

    def update_status_im_hauptfenster(self, meldung):
        """Ruft die update_status-Methode des Hauptfensters auf."""
        if self.master and hasattr(self.master, 'update_status'):
            self.master.update_status(meldung)