import os
import sys
import shutil
import time
import webbrowser
import subprocess
import winreg
import threading
import ctypes
import customtkinter as ctk
from tkinter import messagebox

# Configuración visual moderna
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class SteamFixerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SteamTools Fixer GUI - por @piqseu")
        self.geometry("650x550")
        self.resizable(False, False)

        # Diseño de la interfaz
        self.grid_columnconfigure(0, weight=1)
        
        self.label = ctk.CTkLabel(self, text="SteamTools Fixer", font=ctk.CTkFont(size=26, weight="bold"), text_color="#00ffff")
        self.label.pack(pady=(25, 5))

        self.sublabel = ctk.CTkLabel(self, text="Corrección de caché y preservación de tiempo de juego", font=ctk.CTkFont(size=13))
        self.sublabel.pack(pady=(0, 15))

        # Consola de logs
        self.log_area = ctk.CTkTextbox(self, width=580, height=320, fg_color="#1a1a1a", border_color="#333333", border_width=1, font=("Consolas", 12))
        self.log_area.pack(pady=10, padx=20)
        self.log_area.configure(state="disabled")

        # Botón de inicio
        self.start_btn = ctk.CTkButton(self, text="Iniciar Corrección", command=self.start_process_thread, 
                                       fg_color="#28a745", hover_color="#218838", height=45, font=ctk.CTkFont(size=15, weight="bold"))
        self.start_btn.pack(pady=20)

    def log(self, message):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", message + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")
        self.update_idletasks()

    def start_process_thread(self):
        self.start_btn.configure(state="disabled", text="Procesando...")
        thread = threading.Thread(target=self.run_fixer, daemon=True)
        thread.start()

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
                    return install_path
            except: continue
        return None

    def kill_steam(self):
        self.log("[!] Cerrando procesos de Steam...")
        subprocess.run(["taskkill", "/F", "/IM", "steam.exe"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "steamwebhelper.exe"], capture_output=True)
        time.sleep(3)

    def run_fixer(self):
        steam_path = self.find_steam()
        if not steam_path:
            messagebox.showerror("Error", "No se encontró Steam en el registro.")
            self.reset_button()
            return

        self.log(f"Steam encontrado en: {steam_path}")

        # Paso 2: xinput1_4.dll (Igual que el PS1)
        self.log("\n[Paso 2] Comprobando SteamTools...")
        dll_path = os.path.join(steam_path, "xinput1_4.dll")
        if not os.path.exists(dll_path):
            self.log("ERROR: Falta xinput1_4.dll")
            webbrowser.open("https://steamtools.net/download.html")
            messagebox.showwarning("Falta SteamTools", "No tienes SteamTools instalado. Redirigiendo...")
            self.reset_button()
            return

        # Paso 3: Contar .lua (Igual que el PS1)
        self.log("\n[Paso 3] Verificando archivos .lua...")
        stplug_path = os.path.join(steam_path, "config", "stplug-in")
        if os.path.exists(stplug_path):
            lua_files = [f for f in os.listdir(stplug_path) if f.endswith('.lua')]
            self.log(f"Encontrados {len(lua_files)} archivo(s) .lua.")
        else:
            self.log("ERROR: Directorio stplug-in no encontrado.")

        # Pre-Paso 4: Backup Check (Igual que el PS1)
        backup_path = os.path.join(steam_path, "cache-backup")
        if os.path.exists(backup_path):
            if messagebox.askyesno("Restaurar Backup", "La carpeta de backup ya existe. ¿Deseas restaurar el backup en su lugar?"):
                self.restore_backup(steam_path, backup_path)
                return

        # Paso 4: Limpieza (Mejorada para evitar el error de carpetas existentes)
        self.log("\n[Paso 4] Limpiando cachés...")
        self.kill_steam()
        
        try:
            if not os.path.exists(backup_path): os.makedirs(backup_path)
            
            # Appcache (Preservando stats como en el PS1)
            appcache = os.path.join(steam_path, "appcache")
            app_bkp = os.path.join(backup_path, "appcache")
            if os.path.exists(appcache):
                if os.path.exists(app_bkp): shutil.rmtree(app_bkp, ignore_errors=True)
                os.makedirs(app_bkp)
                for item in os.listdir(appcache):
                    s, d = os.path.join(appcache, item), os.path.join(app_bkp, item)
                    if item.lower() != "stats":
                        shutil.move(s, d)
                    else:
                        shutil.copytree(s, d, dirs_exist_ok=True)
            
            # Depotcache
            depot = os.path.join(steam_path, "depotcache")
            depot_bkp = os.path.join(backup_path, "depotcache")
            if os.path.exists(depot):
                if os.path.exists(depot_bkp): shutil.rmtree(depot_bkp, ignore_errors=True)
                shutil.move(depot, depot_bkp)

            # Userdata y localconfig.vdf (Preservando Playtime como el PS1)
            userdata = os.path.join(steam_path, "userdata")
            if os.path.exists(userdata):
                for user in os.listdir(userdata):
                    u_path = os.path.join(userdata, user)
                    if os.path.isdir(u_path):
                        cfg = os.path.join(u_path, "config")
                        if os.path.exists(cfg):
                            u_bkp = os.path.join(backup_path, "userdata", user, "config")
                            if os.path.exists(u_bkp): shutil.rmtree(os.path.dirname(u_bkp), ignore_errors=True)
                            os.makedirs(os.path.dirname(u_bkp), exist_ok=True)
                            shutil.move(cfg, u_bkp)
                            
                            # Restaurar localconfig.vdf inmediatamente
                            os.makedirs(cfg, exist_ok=True)
                            shutil.copy2(os.path.join(u_bkp, "localconfig.vdf"), os.path.join(cfg, "localconfig.vdf"))
            
            self.log("¡Caché limpiado y Playtime preservado!")
            subprocess.Popen([os.path.join(steam_path, "steam.exe"), "-clearbeta"])
            messagebox.showinfo("Éxito", "Caché limpiado. Steam se está iniciando.")
        except Exception as e:
            self.log(f"Error: {e}")
        
        self.reset_button()

    def restore_backup(self, steam_path, backup_path):
        self.kill_steam()
        self.log("Restaurando archivos...")
        for item in os.listdir(backup_path):
            src, dst = os.path.join(backup_path, item), os.path.join(steam_path, item)
            if os.path.exists(dst):
                shutil.rmtree(dst) if os.path.isdir(dst) else os.remove(dst)
            shutil.move(src, dst)
        shutil.rmtree(backup_path)
        subprocess.Popen([os.path.join(steam_path, "steam.exe"), "-clearbeta"])
        self.log("Backup restaurado.")
        self.reset_button()

    def reset_button(self):
        self.start_btn.configure(state="normal", text="Iniciar Corrección")

if __name__ == "__main__":
    if is_admin():
        app = SteamFixerApp()
        app.mainloop()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
