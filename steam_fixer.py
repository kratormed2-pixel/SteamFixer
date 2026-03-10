import os
import sys
import shutil
import time
import webbrowser
import subprocess
import winreg
import tkinter as tk
from tkinter import messagebox, scrolledtext

class SteamFixerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ST Fixer GUI - by @piqseu (Ported by AI)")
        self.root.geometry("600x450")
        self.root.configure(bg="#1e1e1e")

        # Título
        tk.Label(root, text="SteamTools Fixer", font=("Arial", 16, "bold"), bg="#1e1e1e", fg="#00ffff").pack(pady=10)

        # Consola de texto
        self.log_area = scrolledtext.ScrolledText(root, width=70, height=18, bg="#2d2d2d", fg="#ffffff", font=("Consolas", 10))
        self.log_area.pack(pady=5)
        self.log_area.config(state=tk.DISABLED)

        # Botón de inicio
        self.start_btn = tk.Button(root, text="Iniciar Corrección", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=self.run_fixer)
        self.start_btn.pack(pady=10)

    def log(self, message, color="#ffffff"):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.root.update()

    def find_steam(self):
        self.log("[Paso 1] Buscando instalación de Steam...", "#ffff00")
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
                    self.log(f"Steam encontrado en: {install_path}", "#00ff00")
                    return install_path
            except FileNotFoundError:
                continue
        return None

    def kill_steam(self):
        self.log("Cerrando procesos de Steam...", "#aaaaaa")
        subprocess.run(["taskkill", "/F", "/IM", "steam.exe"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "steamwebhelper.exe"], capture_output=True)
        time.sleep(3)

    def run_fixer(self):
        self.start_btn.config(state=tk.DISABLED)
        steam_path = self.find_steam()
        
        if not steam_path:
            self.log("ERROR: No se pudo encontrar Steam en el registro.", "#ff0000")
            messagebox.showerror("Error", "No se encontró Steam.")
            self.start_btn.config(state=tk.NORMAL)
            return

        # Paso 2: Verificar xinput1_4.dll
        self.log("\n[Paso 2] Comprobando si SteamTools está instalado...", "#ffff00")
        dll_path = os.path.join(steam_path, "xinput1_4.dll")
        if os.path.exists(dll_path):
            self.log("xinput1_4.dll encontrado.", "#00ff00")
        else:
            self.log("xinput1_4.dll NO encontrado. Abriendo página de descarga...", "#ff0000")
            webbrowser.open("https://steamtools.net/download.html")
            messagebox.showwarning("Falta SteamTools", "No tienes SteamTools instalado. Se abrió la web para descargarlo.")
            self.start_btn.config(state=tk.NORMAL)
            return

        # Paso 3: Contar .lua
        self.log("\n[Paso 3] Contando archivos .lua...", "#ffff00")
        stplug_path = os.path.join(steam_path, r"config\stplug-in")
        if os.path.exists(stplug_path):
            lua_files = [f for f in os.listdir(stplug_path) if f.endswith('.lua')]
            if len(lua_files) == 0:
                self.log("ERROR: 0 archivos .lua encontrados.", "#ff0000")
            else:
                self.log(f"Encontrados {len(lua_files)} archivo(s) .lua.", "#00ff00")
        else:
            self.log("ERROR: Directorio stplug-in no encontrado.", "#ff0000")

        # Pre-Paso 4: Backup
        backup_path = os.path.join(steam_path, "cache-backup")
        if os.path.exists(backup_path):
            self.log("\n[Pre-Paso 4] Carpeta de backup encontrada.", "#ffff00")
            # Aquí es donde pregunta SI o NO
            if messagebox.askyesno("Restaurar Backup", "La carpeta de backup ya existe. ¿Deseas restaurar el backup en su lugar?"):
                self.kill_steam()
                self.log("Restaurando backup...", "#ffff00")
                for item in os.listdir(backup_path):
                    src = os.path.join(backup_path, item)
                    dst = os.path.join(steam_path, item)
                    if os.path.exists(dst):
                        if os.path.isdir(dst): shutil.rmtree(dst, ignore_errors=True)
                        else: os.remove(dst)
                    shutil.move(src, dst)
                self.log("Backup restaurado. Limpiando carpeta de backup...", "#00ff00")
                shutil.rmtree(backup_path, ignore_errors=True)
                
                self.log("Iniciando Steam...", "#aaaaaa")
                subprocess.Popen([os.path.join(steam_path, "steam.exe"), "-clearbeta"])
                messagebox.showinfo("Éxito", "Backup restaurado y Steam iniciado.")
                self.start_btn.config(state=tk.NORMAL)
                return
            else:
                self.log("Continuando con la limpieza de caché...", "#aaaaaa")
        
        # Paso 4: Limpiar cachés
        self.log("\n[Paso 4] Limpiando cachés de Steam...", "#ffff00")
        os.makedirs(backup_path, exist_ok=True)
        self.kill_steam()

        # Appcache
        appcache = os.path.join(steam_path, "appcache")
        appcache_bkp = os.path.join(backup_path, "appcache")
        if os.path.exists(appcache):
            os.makedirs(appcache_bkp, exist_ok=True)
            for item in os.listdir(appcache):
                src = os.path.join(appcache, item)
                dst = os.path.join(appcache_bkp, item)
                if item.lower() != "stats":
                    shutil.move(src, dst)
                else:
                    shutil.copytree(src, dst, dirs_exist_ok=True)

        # Depotcache
        depotcache = os.path.join(steam_path, "depotcache")
        depotcache_bkp = os.path.join(backup_path, "depotcache")
        if os.path.exists(depotcache):
            shutil.move(depotcache, depotcache_bkp)

        # Userdata
        self.log("Limpiando cachés de usuario y preservando localconfig...", "#aaaaaa")
        userdata = os.path.join(steam_path, "userdata")
        if os.path.exists(userdata):
            for user in os.listdir(userdata):
                user_folder = os.path.join(userdata, user)
                if os.path.isdir(user_folder):
                    user_config = os.path.join(user_folder, "config")
                    if os.path.exists(user_config):
                        user_bkp = os.path.join(backup_path, "userdata", user)
                        os.makedirs(user_bkp, exist_ok=True)
                        shutil.move(user_config, os.path.join(user_bkp, "config"))
                        
                        # Restaurar playtime (localconfig.vdf)
                        localconfig_bkp = os.path.join(user_bkp, "config", "localconfig.vdf")
                        if os.path.exists(localconfig_bkp):
                            os.makedirs(user_config, exist_ok=True)
                            shutil.copy2(localconfig_bkp, os.path.join(user_config, "localconfig.vdf"))

        self.log("¡Caché de usuario limpiado!", "#00ff00")
        self.log("Iniciando Steam (beta desactivada)...", "#aaaaaa")
        subprocess.Popen([os.path.join(steam_path, "steam.exe"), "-clearbeta"])
        
        self.log("\n¡Tus juegos DEBERÍAN funcionar ahora!", "#00ffff")
        messagebox.showinfo("Proceso Terminado", "Caché limpiado con éxito. Se ha iniciado Steam.")
        self.start_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = SteamFixerApp(root)
    root.mainloop()
