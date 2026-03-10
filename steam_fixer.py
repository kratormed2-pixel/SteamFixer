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

# Configuración visual: Modo oscuro y color cyan para el estilo "SteamTools"
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

        self.title("SteamTools Fixer - GUI Minimalista")
        self.geometry("650x550")
        self.resizable(False, False)

        # Contenedor principal
        self.grid_columnconfigure(0, weight=1)
        
        # Título estilo Moderno
        self.label = ctk.CTkLabel(self, text="SteamTools Fixer", font=ctk.CTkFont(size=26, weight="bold"), text_color="#00ffff")
        self.label.pack(pady=(25, 10))

        self.sublabel = ctk.CTkLabel(self, text="Reparación automática de caché y configuración", font=ctk.CTkFont(size=12))
        self.sublabel.pack(pady=(0, 10))

        # Consola de logs (Modo Oscuro)
        self.log_area = ctk.CTkTextbox(self, width=580, height=320, fg_color="#1a1a1a", border_color="#333333", border_width=1, font=("Consolas", 12))
        self.log_area.pack(pady=10, padx=20)
        self.log_area.configure(state="disabled")

        # Botón de acción
        self.start_btn = ctk.CTkButton(self, text="Iniciar Corrección", command=self.start_process_thread, 
                                       fg_color="#28a745", hover_color="#218838", height=45, font=ctk.CTkFont(size=15, weight="bold"))
        self.start_btn.pack(pady=20)

        self.log("[ℹ️] Programa listo. Haz clic en Iniciar para comenzar.")

    def log(self, message):
        """Escribe mensajes en la consola de la interfaz."""
        self.log_area.configure(state="normal")
        self.log_area.insert("end", message + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")
        self.update_idletasks()

    def start_process_thread(self):
        """Lanza el proceso en un hilo separado para no congelar la ventana."""
        self.start_btn.configure(state="disabled", text="Procesando...")
        thread = threading.Thread(target=self.run_fixer, daemon=True)
        thread.start()

    def find_steam(self):
        self.log("[1/4] Buscando ruta de Steam en el registro...")
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
        self.log("[!] Cerrando Steam y procesos relacionados...")
        subprocess.run(["taskkill", "/F", "/IM", "steam.exe"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "steamwebhelper.exe"], capture_output=True)
        time.sleep(3) # Esperar a que se liberen los archivos

    def run_fixer(self):
        steam_path = self.find_steam()
        
        if not steam_path:
            self.log("[ERROR] No se pudo encontrar Steam automáticamente.")
            messagebox.showerror("Error", "No se encontró Steam instalado.")
            self.reset_button()
            return

        self.log(f"[OK] Steam detectado: {steam_path}")

        # Paso 2: Verificar DLL
        dll_path = os.path.join(steam_path, "xinput1_4.dll")
        if not os.path.exists(dll_path):
            self.log("[ERROR] xinput1_4.dll no encontrado.")
            webbrowser.open("https://steamtools.net/download.html")
            messagebox.showwarning("Falta SteamTools", "SteamTools no está instalado. Se abrió la web de descarga.")
            self.reset_button()
            return

        # Paso 3: Verificar plugins .lua
        stplug_path = os.path.join(steam_path, "config", "stplug-in")
        if os.path.exists(stplug_path):
            lua_files = [f for f in os.listdir(stplug_path) if f.endswith('.lua')]
            self.log(f"[OK] Plugins encontrados: {len(lua_files)} archivos .lua")
        else:
            self.log("[!] Advertencia: No se encontró la carpeta stplug-in.")

        # Manejo de Backup
        backup_path = os.path.join(steam_path, "cache-backup")
        if os.path.exists(backup_path):
            if messagebox.askyesno("Restaurar Backup", "Se encontró un backup previo.\n\n¿Deseas RESTAURARLO ahora?\n(Si eliges 'No', se borrará el viejo y se creará uno nuevo)"):
                self.restore_backup(steam_path, backup_path)
                return

        # Paso 4: Limpieza y Backup Nuevo
        self.log("[4/4] Iniciando limpieza de caché...")
        self.kill_steam()
        
        try:
            os.makedirs(backup_path, exist_ok=True)
            self.perform_cleanup(steam_path, backup_path)
            
            self.log("[OK] Limpieza completada con éxito.")
            self.log("[!] Iniciando Steam (Modo Seguro -clearbeta)...")
            subprocess.Popen([os.path.join(steam_path, "steam.exe"), "-clearbeta"])
            messagebox.showinfo("Proceso Terminado", "Caché limpiado y Steam iniciado.")
        except Exception as e:
            self.log(f"[ERROR CRÍTICO] {str(e)}")
            messagebox.showerror("Error", f"Ocurrió un error: {e}")
        
        self.reset_button()

    def perform_cleanup(self, steam_path, backup_path):
        """Mueve archivos al backup evitando errores de 'Ya existe'."""
        
        # 1. Appcache y Depotcache
        for folder in ["appcache", "depotcache"]:
            src = os.path.join(steam_path, folder)
            dst = os.path.join(backup_path, folder)
            if os.path.exists(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst, ignore_errors=True)
                
                # Para appcache evitamos mover 'stats' para no perder datos locales
                if folder == "appcache":
                    os.makedirs(dst, exist_ok=True)
                    for item in os.listdir(src):
                        s_item, d_item = os.path.join(src, item), os.path.join(dst, item)
                        if item.lower() != "stats":
                            if os.path.exists(d_item): shutil.rmtree(d_item) if os.path.isdir(d_item) else os.remove(d_item)
                            shutil.move(s_item, d_item)
                        else:
                            shutil.copytree(s_item, d_item, dirs_exist_ok=True)
                else:
                    shutil.move(src, dst)
                self.log(f"[+] {folder} respaldado y limpiado.")

        # 2. Userdata (Preservando localconfig.vdf)
        userdata = os.path.join(steam_path, "userdata")
        if os.path.exists(userdata):
            for user in os.listdir(userdata):
                user_folder = os.path.join(userdata, user)
                if os.path.isdir(user_folder):
                    config_folder = os.path.join(user_folder, "config")
                    if os.path.exists(config_folder):
                        user_bkp_dir = os.path.join(backup_path, "userdata", user, "config")
                        if os.path.exists(user_bkp_dir): shutil.rmtree(user_bkp_dir, ignore_errors=True)
                        os.makedirs(os.path.dirname(user_bkp_dir), exist_ok=True)
                        
                        shutil.move(config_folder, user_bkp_dir)
                        
                        # Restaurar el archivo que guarda las horas de juego
                        l_vdf = os.path.join(user_bkp_dir, "localconfig.vdf")
                        if os.path.exists(l_vdf):
                            os.makedirs(config_folder, exist_ok=True)
                            shutil.copy2(l_vdf, os.path.join(config_folder, "localconfig.vdf"))
            self.log("[+] Userdata procesado (localconfig preservado).")

    def restore_backup(self, steam_path, backup_path):
        self.kill_steam()
        self.log("[!] Restaurando archivos desde el backup...")
        try:
            for item in os.listdir(backup_path):
                src, dst = os.path.join(backup_path, item), os.path.join(steam_path, item)
                if os.path.exists(dst):
                    shutil.rmtree(dst, ignore_errors=True) if os.path.isdir(dst) else os.remove(dst)
                shutil.move(src, dst)
            shutil.rmtree(backup_path, ignore_errors=True)
            self.log("[OK] Backup restaurado correctamente.")
            subprocess.Popen([os.path.join(steam_path, "steam.exe"), "-clearbeta"])
        except Exception as e:
            self.log(f"[ERROR] No se pudo restaurar: {e}")
        self.reset_button()

    def reset_button(self):
        self.start_btn.configure(state="normal", text="Iniciar Corrección")

if __name__ == "__main__":
    if is_admin():
        app = SteamFixerApp()
        app.mainloop()
    else:
        # Si no es admin, pide permisos y reinicia el programa
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
