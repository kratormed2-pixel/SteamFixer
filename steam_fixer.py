import os
import sys
import shutil
import time
import webbrowser
import subprocess
import winreg
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

class SteamFixerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ST Fixer GUI - by @piqseu (Ported by AI)")
        self.root.geometry("600x450")
        self.root.configure(bg="#1e1e1e")

        tk.Label(root, text="SteamTools Fixer", font=("Arial", 16, "bold"), bg="#1e1e1e", fg="#00ffff").pack(pady=10)

        self.log_area = scrolledtext.ScrolledText(root, width=70, height=18, bg="#2d2d2d", fg="#ffffff", font=("Consolas", 10))
        self.log_area.pack(pady=5)
        self.log_area.config(state=tk.DISABLED)

        self.start_btn = tk.Button(root, text="Iniciar Corrección", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=self.start_thread)
        self.start_btn.pack(pady=10)

    def log(self, message, color="#ffffff"):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def find_steam(self):
        self.log("[Paso 1] Buscando instalación de Steam...")
        paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam")
        ]
        for root_key, sub_key in paths:
            try:
                key = winreg.OpenKey(root_key, sub_key)
                install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                if os.path.exists(install_path):
                    self.log(f"Steam encontrado en: {install_path}")
                    return install_path
            except: continue
        return None

    def kill_steam(self):
        self.log("Cerrando procesos de Steam...")
        subprocess.run("taskkill /F /T /IM steam.exe", shell=True, capture_output=True)
        subprocess.run("taskkill /F /T /IM steamwebhelper.exe", shell=True, capture_output=True)
        time.sleep(3)

    def start_thread(self):
        self.start_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.run_fixer, daemon=True).start()

    def run_fixer(self):
        steam_path = self.find_steam()
        if not steam_path:
            self.log("ERROR: No se encontró Steam.")
            self.start_btn.config(state=tk.NORMAL)
            return

        # Paso 2: DLL
        dll_path = os.path.join(steam_path, "xinput1_4.dll")
        if not os.path.exists(dll_path):
            self.log("ERROR: xinput1_4.dll no encontrado.")
            webbrowser.open("https://steamtools.net/download.html")
            self.start_btn.config(state=tk.NORMAL)
            return
        self.log("xinput1_4.dll encontrado.")

        # Paso 3: LUA
        stplug_path = os.path.join(steam_path, "config", "stplug-in")
        lua_count = len([f for f in os.listdir(stplug_path) if f.endswith('.lua')]) if os.path.exists(stplug_path) else 0
        self.log(f"Encontrados {lua_count} archivos .lua.")

        # Backup y Limpieza
        backup_path = os.path.join(steam_path, "cache-backup")
        if os.path.exists(backup_path):
            if messagebox.askyesno("Restaurar", "¿Deseas restaurar el backup existente?"):
                self.kill_steam()
                for item in os.listdir(backup_path):
                    shutil.move(os.path.join(backup_path, item), os.path.join(steam_path, item))
                shutil.rmtree(backup_path)
                self.log("Backup restaurado.")
                self.start_btn.config(state=tk.NORMAL)
                return

        self.log("[Paso 4] Iniciando limpieza profunda...")
        self.kill_steam()
        os.makedirs(backup_path, exist_ok=True)

        # Mover appcache y depotcache
        for folder in ["appcache", "depotcache"]:
            src = os.path.join(steam_path, folder)
            if os.path.exists(src):
                shutil.move(src, os.path.join(backup_path, folder))
                self.log(f"Carpeta {folder} movida a backup.")

        # Userdata preservando localconfig
        userdata = os.path.join(steam_path, "userdata")
        if os.path.exists(userdata):
            for user in os.listdir(userdata):
                u_path = os.path.join(userdata, user, "config")
                if os.path.exists(u_path):
                    bk_u = os.path.join(backup_path, "userdata", user, "config")
                    os.makedirs(os.path.dirname(bk_u), exist_ok=True)
                    shutil.move(u_path, bk_u)
                    # Restaurar solo localconfig
                    os.makedirs(u_path, exist_ok=True)
                    shutil.copy2(os.path.join(bk_u, "localconfig.vdf"), os.path.join(u_path, "localconfig.vdf"))
            self.log("Caché de usuario limpiado.")

        self.log("Iniciando Steam...")
        subprocess.Popen([os.path.join(steam_path, "steam.exe"), "-clearbeta"])
        self.log("¡Todo listo! Enjoy.")
        messagebox.showinfo("Éxito", "Limpieza completada.")
        self.start_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = SteamFixerApp(root)
    root.mainloop()
