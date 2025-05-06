# setup.py
import sys
from cx_Freeze import setup, Executable
from version import __version__  # Importiere die Versionsinformationen

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="EasyVideoCompare",  # Ersetze dies durch den Namen deines Programms
    version=__version__,
    description="Ein einfaches Programm um Videos zu vergleichen",  # Füge hier eine Beschreibung hinzu
    executables=[Executable("main.py", base=base)],
    packages=["tkinter", "PIL", "cv2", "os", "tkinter.ttk"],  # Explizit benötigte Packages
    include_files=["version.py"],  # Füge version.py zu den Included Files hinzu
    # Wenn du zusätzliche Daten oder Ordner hast (z.B. Bilder), füge sie hier hinzu:
    # include_files=[("assets", "assets"), "version.py"],
    # Wenn du bestimmte DLLs oder andere Dateien benötigst, kannst du 'include_files' erweitern.
)