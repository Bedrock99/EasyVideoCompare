# EasyVideoCompare

## Beschreibung

EasyVideoCompare ist ein einfaches, benutzerfreundliches Programm zum Vergleichen der visuellen Ähnlichkeit zwischen zwei oder mehreren Videodateien. Es analysiert die Videos anhand ihrer Keyframes und deren Farbhistogramme, um eine quantitative Einschätzung der Ähnlichkeit zu ermöglichen. Das Programm bietet eine grafische Benutzeroberfläche (GUI), um Videos auszuwählen, den Vergleich zu starten und die Ergebnisse in einer übersichtlichen Weise anzuzeigen. Ähnliche Videopaare können in einem separaten Dialog detaillierter betrachtet und bei Bedarf gelöscht werden.

## Wie es funktioniert

1.  **Videoauswahl:** Der Benutzer wählt über einen Dateiauswahldialog die zu vergleichenden Videodateien aus (unterstützte Formate sind typischerweise `.mp4`, `.avi`, `.mkv`).
2.  **Keyframe-Extraktion:** Für jedes ausgewählte Video werden automatisch Keyframes extrahiert. Ein Keyframe wird als ein repräsentativer Frame des Videos betrachtet, der eine signifikante visuelle Änderung gegenüber dem vorherigen Frame aufweist. Die Extraktion basiert auf der Erkennung von Unterschieden in aufeinanderfolgenden Frames.
3.  **Histogramm-Berechnung:** Für jeden extrahierten Keyframe wird ein Farbhistogramm berechnet. Ein Farbhistogramm stellt die Verteilung der Farbintensitäten in einem Bild dar und dient als eine Art "visuelle Signatur" des Keyframes.
4.  **Vergleich der Histogramme:** Die Farbhistogramme der Keyframes der verschiedenen Videos werden paarweise verglichen. Als Vergleichsmethode wird die Bhattacharyya-Distanz verwendet, die ein Maß für die Ähnlichkeit zwischen zwei Wahrscheinlichkeitsverteilungen (in diesem Fall den normalisierten Histogrammen) darstellt. Eine niedrigere Bhattacharyya-Distanz deutet auf eine höhere visuelle Ähnlichkeit hin.
5.  **Bewertung der Videoähnlichkeit:** Für jedes Paar von verglichenen Videos wird ein durchschnittlicher Ähnlichkeitswert basierend auf den Vergleichen ihrer Keyframe-Histogramme berechnet. Dieser Wert gibt eine Gesamtbewertung der visuellen Ähnlichkeit der beiden Videos an.
6.  **Anzeige der Ergebnisse:** Die Ergebnisse des Vergleichs werden in der Hauptanwendung angezeigt. Ähnliche Videopaare, die einen bestimmten vom Benutzer einstellbaren Schwellwert unterschreiten, können in einem separaten "Auswahl-Dialog" zur detaillierteren Überprüfung angezeigt werden.
7.  **Überprüfung und Löschen:** Im Auswahl-Dialog kann der Benutzer die Keyframes der als ähnlich erkannten Videopaare nebeneinander betrachten und entscheiden, ob eines oder beide Videos beibehalten oder gelöscht werden sollen.

## Bedienung

1.  **Videos auswählen:** Klicken Sie auf die Schaltfläche "Videos auswählen", um die zu vergleichenden Videodateien über den Dateiauswahldialog hinzuzufügen. Die ausgewählten Videos werden in der Videoliste angezeigt.
2.  **Ähnlichkeitsschwelle (optional):** Passen Sie den Wert im Feld "Ähnlichkeitsschwelle" an. Dieser Wert bestimmt, welche Videopaare als "ähnlich" genug betrachtet werden, um im Auswahl-Dialog angezeigt zu werden (ein niedrigerer Wert bedeutet eine strengere Definition von Ähnlichkeit).
3.  **Videos vergleichen:** Klicken Sie auf die Schaltfläche "Videos vergleichen", um den Analyseprozess zu starten. Der Fortschritt wird in der Fortschrittsleiste und im Log-Bereich angezeigt.
4.  **Ergebnisse überprüfen:** Nach Abschluss des Vergleichs werden die Ergebnisse angezeigt. Wenn ähnliche Videopaare gefunden wurden, wird die Schaltfläche "Ähnliche Paare überprüfen" aktiviert.
5.  **Ähnliche Paare überprüfen (optional):** Klicken Sie auf "Ähnliche Paare überprüfen", um den Auswahl-Dialog zu öffnen. Hier können Sie die Keyframes der ähnlichen Videos betrachten und entscheiden, ob Sie die Videos behalten oder löschen möchten.
6.  **Log:** Der Log-Bereich zeigt detaillierte Informationen über den Ablauf des Programms, einschließlich der extrahierten Keyframes und der Vergleichsergebnisse.

## Hinweis zur Erstellung

Dieses Programm wurde zum Großteil mit Unterstützung von Google Gemini entwickelt.
