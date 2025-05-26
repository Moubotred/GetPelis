import sys
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
from view.main_window import MainWindow
from controller.main_controller import MainController

import os
import sys
import shutil
import tempfile
import zipfile
import tarfile
import subprocess
from pathlib import Path
from urllib.request import urlretrieve

if sys.platform == "win32":
    import winreg

def is_tool_installed(tool_name):
    return shutil.which(tool_name) is not None

def get_firefox_install_path_windows():
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Mozilla\Mozilla Firefox"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Mozilla\Mozilla Firefox")
    ]
    for hive, key_path in reg_paths:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                current_version, _ = winreg.QueryValueEx(key, "CurrentVersion")
                with winreg.OpenKey(hive, f"{key_path}\\{current_version}\\Main") as subkey:
                    path_to_exe, _ = winreg.QueryValueEx(subkey, "PathToExe")
                    return path_to_exe
        except FileNotFoundError:
            continue
    return None

def get_vlc_install_path_windows():
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\VideoLAN\VLC") as key:
            install_path, _ = winreg.QueryValueEx(key, "InstallDir")
            exe_path = os.path.join(install_path, "vlc.exe")
            return exe_path if os.path.exists(exe_path) else None
    except FileNotFoundError:
        return None

def add_path_windows(folder_path):
    current_path = os.environ.get("PATH", "")
    if folder_path.lower() not in current_path.lower():
        print(f"📝 Añadiendo '{folder_path}' al PATH del sistema...")
        subprocess.run(["setx", "/M", "PATH", f"{current_path};{folder_path}"], shell=True)

def install_firefox_and_geckodriver_and_vlc():
    temp_dir = tempfile.mkdtemp()
    platform = sys.platform

    # Verificación inicial
    firefox_ok = is_tool_installed("firefox")
    gecko_ok   = is_tool_installed("geckodriver")
    vlc_ok     = is_tool_installed("vlc")

    if not firefox_ok and platform == "win32":
        firefox_path = get_firefox_install_path_windows()
        if firefox_path and Path(firefox_path).exists():
            firefox_ok = True
            firefox_dir = str(Path(firefox_path).parent)
            os.environ["PATH"] += os.pathsep + firefox_dir
            add_path_windows(firefox_dir)
            print(f"🔧 FIREFOX_PATH = {firefox_path}")
        else:
            print("⚠️ Firefox no encontrado.")

    if not gecko_ok and platform == "win32":
        possible_path = Path("C:/Program Files/geckodriver/geckodriver.exe")
        if possible_path.exists():
            gecko_ok = True
            os.environ["PATH"] += os.pathsep + str(possible_path.parent)
            add_path_windows(str(possible_path.parent))
            print(f"🔧 GECKODRIVER_PATH = {possible_path}")

    if not vlc_ok and platform == "win32":
        vlc_path = get_vlc_install_path_windows()
        if vlc_path:
            vlc_ok = True
            vlc_dir = str(Path(vlc_path).parent)
            os.environ["PATH"] += os.pathsep + vlc_dir
            add_path_windows(vlc_dir)
            print(f"🔧 VLC_PATH = {vlc_path}")
        else:
            print("⚠️ VLC no encontrado.")

    print(f"🔍 Firefox instalado: {firefox_ok}")
    print(f"🔍 geckodriver instalado: {gecko_ok}")
    print(f"🔍 VLC instalado: {vlc_ok}")
    print(f"🖥️ Plataforma detectada: {platform}")

    # === WINDOWS ===
    if platform == "win32":
        if not firefox_ok:
            print("🔽 Descargando Firefox...")
            firefox_url = "https://download.mozilla.org/?product=firefox-latest&os=win64&lang=es-ES"
            installer = os.path.join(temp_dir, "firefox_installer.exe")
            urlretrieve(firefox_url, installer)
            print("⚙️ Instalando Firefox en modo silencioso...")
            subprocess.run([installer, "/silent", "/install"], check=True)

        if not gecko_ok:
            print("🔽 Descargando geckodriver para Windows...")
            gecko_url = "https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-v0.34.0-win64.zip"
            zip_path = os.path.join(temp_dir, "geckodriver.zip")
            urlretrieve(gecko_url, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zz:
                zz.extractall(temp_dir)
            dest = os.path.join(os.environ["USERPROFILE"], "geckodriver_bin")
            os.makedirs(dest, exist_ok=True)
            shutil.move(os.path.join(temp_dir, "geckodriver.exe"), os.path.join(dest, "geckodriver.exe"))
            os.environ["PATH"] += os.pathsep + dest
            add_path_windows(dest)
            print(f"✅ geckodriver instalado en: {dest}")

        if not vlc_ok:
            print("🔽 Descargando VLC...")
            vlc_url = "https://get.videolan.org/vlc/3.0.20/win64/vlc-3.0.20-win64.exe"
            vlc_installer = os.path.join(temp_dir, "vlc_installer.exe")
            urlretrieve(vlc_url, vlc_installer)
            print("⚙️ Instalando VLC en modo silencioso...")
            subprocess.run([vlc_installer, "/S"], check=True)

    # === LINUX ===
    elif platform.startswith("linux"):
        if not firefox_ok:
            print("⚙️ Instalando Firefox con APT...")
            try:
                subprocess.run(["sudo", "apt", "install", "-y", "firefox"], check=True)
            except subprocess.CalledProcessError:
                print("❌ Error instalando Firefox.")

        if not gecko_ok:
            print("🔽 Descargando geckodriver para Linux...")
            gecko_url = "https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-v0.34.0-linux64.tar.gz"
            tar_path = os.path.join(temp_dir, "geckodriver.tar.gz")
            urlretrieve(gecko_url, tar_path)
            with tarfile.open(tar_path, 'r:gz') as tf:
                tf.extractall(temp_dir)
            dest = str(Path.home() / ".local" / "bin")
            os.makedirs(dest, exist_ok=True)
            shutil.move(os.path.join(temp_dir, "geckodriver"), os.path.join(dest, "geckodriver"))
            os.chmod(os.path.join(dest, "geckodriver"), 0o755)
            os.environ["PATH"] += os.pathsep + dest
            with open(Path.home() / ".bashrc", "a") as f:
                f.write(f'\nexport PATH="{dest}:$PATH"\n')
            print(f"✅ geckodriver instalado en: {dest}")

        if not vlc_ok:
            print("⚙️ Instalando VLC con APT...")
            try:
                subprocess.run(["sudo", "apt", "install", "-y", "vlc"], check=True)
            except subprocess.CalledProcessError:
                print("❌ Error instalando VLC.")

    else:
        print("❌ Plataforma no soportada.")
        return

    print("🎉 Proceso de instalación completado.")


# install_firefox_and_geckodriver_and_vlc()

app = QApplication(sys.argv)
loop = QEventLoop(app)
main_win = MainWindow()
controller = MainController(main_win)
main_win.show()

with loop:
    loop.run_forever()
