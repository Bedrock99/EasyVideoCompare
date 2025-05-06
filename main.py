# video_vergleich_app.py
from version import __version__

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Scrollbar, LabelFrame
from PIL import Image, ImageTk
import cv2
import numpy as np
from itertools import combinations
import threading
from auswahl_dialog import AuswahlDialog


def extrahiere_keyframe_histogramme(video_pfad, schwellwert=20, bins=None, ranges=None, progress_callback=None, status_callback=None):
    """
    Extrahiert Keyframes aus einem Video und gibt deren Farbhistogramme als NumPy-Arrays zurück.
    """
    if ranges is None:
        ranges = [0, 256, 0, 256, 0, 256]
    if bins is None:
        bins = [8, 8, 8]

    cap = cv2.VideoCapture(video_pfad)
    if not cap.isOpened():
        print(f"Fehler: Konnte Video nicht öffnen: {video_pfad}")
        return []

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    histogramme = []
    letzter_grauer_frame = None

    for i in range(frame_count):
        ret, aktueller_frame = cap.read()
        if not ret:
            break

        grauer_aktueller_frame = cv2.cvtColor(aktueller_frame, cv2.COLOR_BGR2GRAY)

        if letzter_grauer_frame is None or np.mean(cv2.absdiff(grauer_aktueller_frame, letzter_grauer_frame)) > schwellwert:
            histogramm = cv2.calcHist([aktueller_frame], [0, 1, 2], None, bins, ranges).flatten()
            histogramme.append(histogramm)
            letzter_grauer_frame = grauer_aktueller_frame

        if progress_callback and frame_count > 0:
            progress_callback(i / frame_count * 0.5)

    if status_callback:
        status_callback(f"Keyframes extrahiert: {len(histogramme)}")

    cap.release()
    return histogramme

def vergleiche_videos(video_pfade, vergleichs_schwelle=0.3, progress_callback=None, status_callback=None):
    """
    Vergleicht die ausgewählten Videos anhand ihrer Keyframe-Histogramme.
    """
    alle_histogramme = {}
    total_videos = len(video_pfade)
    for i, pfad in enumerate(video_pfade):
        if os.path.exists(pfad):
            if status_callback:
                status_callback(f"Analysiere Video {i+1}/{total_videos}: {os.path.basename(pfad)}")
            alle_histogramme[pfad] = extrahiere_keyframe_histogramme(
                pfad,
                progress_callback=lambda p: progress_callback(p / total_videos * 0.5 + i / total_videos * 0.5) if progress_callback else None,
                status_callback=status_callback
            )
        else:
            print(f"Warnung: Video nicht gefunden: {pfad}")

    vergleichs_ergebnisse = {}
    video_paare = list(combinations(video_pfade, 2))
    total_vergleiche = len(video_paare)

    for i, (video_pfad1, video_pfad2) in enumerate(video_paare):
        if video_pfad1 in alle_histogramme and video_pfad2 in alle_histogramme:
            if status_callback:
                status_callback(f"Vergleiche '{os.path.basename(video_pfad1)}' mit '{os.path.basename(video_pfad2)}' ({i+1}/{total_vergleiche})")
            histogramme1 = alle_histogramme[video_pfad1]
            histogramme2 = alle_histogramme[video_pfad2]

            min_distanzen1_zu_2 = []
            for hist1 in histogramme1:
                min_dist = float('inf')
                for hist2 in histogramme2:
                    distanz = cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
                    min_dist = min(min_dist, distanz)
                if min_dist != float('inf'):
                    min_distanzen1_zu_2.append(min_dist)

            min_distanzen2_zu_1 = []
            for hist2 in histogramme2:
                min_dist = float('inf')
                for hist1 in histogramme1:
                    distanz = cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
                    min_dist = min(min_dist, distanz)
                if min_dist != float('inf'):
                    min_distanzen2_zu_1.append(min_dist)

            gesamt_aehnlichkeit = []
            if min_distanzen1_zu_2:
                gesamt_aehnlichkeit.extend(min_distanzen1_zu_2)
            if min_distanzen2_zu_1:
                gesamt_aehnlichkeit.extend(min_distanzen2_zu_1)

            if gesamt_aehnlichkeit:
                mittelwert_distanz = np.mean(gesamt_aehnlichkeit)
                vergleichs_ergebnisse[(video_pfad1, video_pfad2)] = [mittelwert_distanz]
            else:
                vergleichs_ergebnisse[(video_pfad1, video_pfad2)] = []

        if progress_callback and total_vergleiche > 0:
            progress_callback(0.5 + (i + 1) / total_vergleiche * 0.5)

    return vergleichs_ergebnisse

def erzeuge_thumbnail(video_pfad, groesse=(100, 75)):
    """
    Erzeugt ein kleines Vorschaubild (Thumbnail) für das angegebene Video.
    """
    try:
        cap = cv2.VideoCapture(video_pfad)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img.thumbnail(groesse)
            return ImageTk.PhotoImage(img)
        return None
    except Exception as e:
        print(f"Fehler beim Erzeugen des Thumbnails für {video_pfad}: {e}")
        return None

class VideoVergleichsApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Video Vergleich - v{__version__}")
        self.video_pfade = []
        self.vergleichs_ergebnisse = {}
        self.vergleichs_schwelle = tk.DoubleVar(value=0.3)

        self.status_text = tk.StringVar(value="")
        self.status_display = tk.Text(root, height=5, state=tk.DISABLED)
        self.status_scrollbar = Scrollbar(root, command=self.status_display.yview)
        self.status_display.config(yscrollcommand=self.status_scrollbar.set)

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progressbar = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate', variable=self.progress_var)
        self.progressbar_label = ttk.Label(root, text="0.00 %")

        self.vergleichs_thread = None
        self.stop_flag = False

        self.video_liste_text = tk.Text(root, height=5, state=tk.DISABLED)
        self.video_liste_scrollbar = Scrollbar(root, command=self.video_liste_text.yview)
        self.video_liste_text.config(yscrollcommand=self.video_liste_scrollbar.set)

        self.schwellwert_eingabe = None
        self.browse_button = None
        self.vergleichen_button = None

        self.create_widgets()
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=1)

    def create_widgets(self):
        # GroupBox für Videoliste
        videoliste_group = LabelFrame(self.root, text="Videoliste")
        videoliste_group.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")
        self.video_liste_text = tk.Text(videoliste_group, height=5, state=tk.DISABLED)
        self.video_liste_text.grid(row=0, column=0, sticky="nsew")
        self.video_liste_scrollbar = Scrollbar(videoliste_group, command=self.video_liste_text.yview)
        self.video_liste_scrollbar.grid(row=0, column=1, sticky="ns")
        self.video_liste_text.config(yscrollcommand=self.video_liste_scrollbar.set)
        videoliste_group.grid_rowconfigure(0, weight=1)
        videoliste_group.grid_columnconfigure(0, weight=1)

        # GroupBox für Eingabe
        eingabe_group = LabelFrame(self.root, text="Eingabe")
        eingabe_group.grid(row=0, column=1, padx=2, pady=2, sticky="nw")
        self.browse_button = ttk.Button(eingabe_group, text="Videos auswählen", command=self.waehle_videos)
        self.browse_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.vergleichen_button = ttk.Button(eingabe_group, text="Videos vergleichen", command=self.starte_vergleich_threaded)
        self.vergleichen_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        schwelle_frame = ttk.Frame(eingabe_group)
        schwelle_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        ttk.Label(schwelle_frame, text="Ähnlichkeitsschwelle: ").pack(side=tk.LEFT)
        self.schwellwert_eingabe = ttk.Entry(schwelle_frame, textvariable=self.vergleichs_schwelle, width=5)
        self.schwellwert_eingabe.pack(side=tk.LEFT)
        eingabe_group.grid_columnconfigure(0, weight=1)

        # GroupBox für Fortschritt
        fortschritt_group = LabelFrame(self.root, text="Fortschritt")
        fortschritt_group.grid(row=1, column=0, columnspan=2, padx=2, pady=2, sticky="ew")
        self.progressbar = ttk.Progressbar(fortschritt_group, orient=tk.HORIZONTAL, length=300, mode='determinate', variable=self.progress_var)
        self.progressbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5 )
        self.progressbar_label = ttk.Label(fortschritt_group, text="0.00 %")
        self.progressbar_label.grid(row=0, column=1, sticky="w", padx=5, pady=5 )
        fortschritt_group.grid_columnconfigure(0, weight=1)

        # GroupBox für Log
        log_group = LabelFrame(self.root, text="Log")
        log_group.grid(row=2, column=0, columnspan=2, padx=2, pady=2, sticky="nsew")
        self.status_display = tk.Text(log_group, height=5, state=tk.DISABLED)
        self.status_display.grid(row=0, column=0, sticky="nsew")
        self.status_scrollbar = Scrollbar(log_group, command=self.status_display.yview)
        self.status_scrollbar.grid(row=0, column=1, sticky="ns")
        self.status_display.config(yscrollcommand=self.status_scrollbar.set)
        log_group.grid_rowconfigure(0, weight=1)
        log_group.grid_columnconfigure(0, weight=1)

    def waehle_videos(self):
        dateien = filedialog.askopenfilenames(title="Videos auswählen",
                                               filetypes=(("Video-Dateien", "*.mp4;*.avi;*.mkv"), ("Alle Dateien", "*.*")))
        if dateien:
            self.video_pfade = list(dateien)
            self.update_video_liste_anzeige()
            self.update_status("Videos ausgewählt.")
            self.vergleichs_ergebnisse = {}

    def update_video_liste_anzeige(self):
        self.video_liste_text.config(state=tk.NORMAL)
        self.video_liste_text.delete("1.0", tk.END)
        for pfad in self.video_pfade:
            self.video_liste_text.insert(tk.END, os.path.basename(pfad) + "\n")
        self.video_liste_text.config(state=tk.DISABLED)

    def starte_vergleich_threaded(self):
        if not self.video_pfade:
            messagebox.showinfo("Hinweis", "Bitte wähle zuerst Videos aus.")
            return

        # Deaktiviere die Eingabefelder und Buttons
        if self.schwellwert_eingabe:
            self.schwellwert_eingabe.config(state=tk.DISABLED)
        if self.browse_button:
            self.browse_button.config(state=tk.DISABLED)
        if self.vergleichen_button:
            self.vergleichen_button.config(state=tk.DISABLED)

        self.progress_var.set(0.0)
        self.progressbar['value'] = 0.0
        self.progressbar_label.config(text="0.00 %")
        self.update_progressbar(0.0)
        self.update_status("Starte Videovergleich...")

        self.stop_flag = False
        self.vergleichs_thread = threading.Thread(target=self.fuehre_vergleich_aus)
        self.vergleichs_thread.start()

    def fuehre_vergleich_aus(self):
        schwelle = self.vergleichs_schwelle.get()
        ergebnisse = vergleiche_videos(
            self.video_pfade,
            schwelle,
            progress_callback=self.update_progressbar,
            status_callback=self.update_status
        )
        self.root.after(0, self.zeige_auswahl_dialog, ergebnisse)

    def update_progressbar(self, progress):
        if not self.stop_flag:
            self.progress_var.set(progress * 100)
            self.progressbar['value'] = progress * 100
            self.update_progressbar_label(progress)
            self.root.update_idletasks()

    def update_progressbar_label(self, progress):
        self.progressbar_label.config(text=f"{progress * 100:.2f} %")

    def update_status(self, status_meldung):
        if not self.stop_flag:
            self.status_display.config(state=tk.NORMAL)
            self.status_display.insert(tk.END, status_meldung + "\n")
            self.status_display.see(tk.END) # Auto-Scroll
            self.status_display.config(state=tk.DISABLED)
            self.root.update_idletasks()

    def zeige_auswahl_dialog(self, ergebnisse):
        thumbnails = {pfad: erzeuge_thumbnail(pfad) for pfad in self.video_pfade}

        # Re-aktiviere die Eingabefelder und Buttons
        if self.schwellwert_eingabe:
            self.schwellwert_eingabe.config(state=tk.NORMAL)
        if self.browse_button:
            self.browse_button.config(state=tk.NORMAL)
        if self.vergleichen_button:
            self.vergleichen_button.config(state=tk.NORMAL)

        dialog = AuswahlDialog(
            self.root,
            ergebnisse,
            self.vergleichs_schwelle.get(),
            thumbnails,
            self.video_pfade
        )
        dialog.grab_set()
        self.root.wait_window(dialog)

    def aktualisiere_video_liste(self, neue_liste):
        self.video_pfade = neue_liste
        self.update_video_liste_anzeige()


if __name__ == '__main__':
    root = tk.Tk()
    app = VideoVergleichsApp(root)
    root.mainloop()