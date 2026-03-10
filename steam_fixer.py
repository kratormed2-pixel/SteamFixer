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

# Configuración visual: Interfaz moderna en modo oscuro
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def es_administrador():
    """Verifica si el script tiene privilegios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class AplicacionCorrectora(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SteamTools Fixer")
        self.geometry("650x550")
        self.resizable(False, False)

        # Diseño de la interfaz
        self.grid_columnconfigure(0, weight=1)
        
        self.label = ctk.CTkLabel(self, text="SteamTools Fixer", font=ctk.CTkFont(size=26, weight="bold"), text_color="#00ffff")
        self.label.pack(pady=(25, 5))

        self.sublabel = ctk.CTkLabel(self, text="Limpieza de caché y optimización de configuración", font=ctk.CTkFont(size=13))
        self.sublabel.pack(pady=(0, 15))

        # Consola de registro (Logs)
        self.log_area = ctk.CTkTextbox(self, width=580, height=320, fg_color="#1a1a1a", border_color="#333333", border_width=1, font=("Consolas", 12))
        self.log_area.pack(pady=10, padx=20)
        self.log_area.configure(state="disabled")

        # Botón principal
        self.start_btn = ctk.CTkButton(self, text="Iniciar Corrección", command=self.iniciar_hilo_proceso, 
                                       fg_color="#28a745", hover_color="#218838", height=45, font=ctk.CTkFont(size=15, weight="bold"))
        self.start_btn.pack(pady=20)

    def registrar(self, mensaje):
        """Añade mensajes a la consola de la interfaz."""
        self.log_area.configure(state="normal")
        self.log_area.insert("end", mensaje + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")
        self.update_idletasks()

    def iniciar_hilo_proceso(self):
        """Ejecuta el proceso en un segundo plano para evitar que la ventana se congele."""
        self.start_btn.configure(state="disabled", text="Procesando...")
        hilo = threading.Thread(target=self.ejecutar_correccion, daemon=True)
        hilo.start()

    def buscar_steam(self):
        self.registrar("[Paso 1] Localizando instalación de Steam en el sistema...")
        rutas_registro = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam")
        ]
        for clave_raiz, sub_clave in rutas_registro:
            try:
                clave = winreg.OpenKey(clave_raiz, sub_clave)
                ruta_instalacion, _ = winreg.QueryValueEx(clave, "InstallPath")
                if os.path.exists(ruta_instalacion):
                    return ruta_instalacion
            except: continue
        return None

    def cerrar_steam(self):
        self.registrar("[!] Finalizando procesos de Steam activos...")
        subprocess.run(["taskkill", "/F", "/IM", "steam.exe"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "steamwebhelper.exe"], capture_output=True)
        time.sleep(3)

    def ejecutar_correccion(self):
        ruta_steam = self.buscar_steam()
        if not ruta_steam:
            messagebox.showerror("Error", "No se encontró la carpeta de Steam.")
            self.restablecer_boton()
            return

        self.registrar(f"Steam detectado en: {ruta_steam}")

        # Paso 2: Verificación de librerías
        self.registrar("\n[Paso 2] Verificando componentes necesarios...")
        ruta_dll = os.path.join(ruta_steam, "xinput1_4.dll")
        if not os.path.exists(ruta_dll):
            self.registrar("ERROR: No se encontró xinput1_4.dll")
            webbrowser.open("https://steamtools.net/download.html")
            messagebox.showwarning("Componente Faltante", "Faltan archivos necesarios. Se ha abierto la página de descarga.")
            self.restablecer_boton()
            return

        # Paso 3: Verificación de complementos
        self.registrar("\n[Paso 3] Comprobando archivos de configuración...")
        ruta_plugins = os.path.join(ruta_steam, "config", "stplug-in")
        if os.path.exists(ruta_plugins):
            archivos_lua = [f for f in os.listdir(ruta_plugins) if f.endswith('.lua')]
            self.registrar(f"Se encontraron {len(archivos_lua)} archivos de configuración.")
        else:
            self.registrar("AVISO: Carpeta de configuraciones no encontrada.")

        # Manejo de Copias de Seguridad
        ruta_respaldo = os.path.join(ruta_steam, "cache-backup")
        if os.path.exists(ruta_respaldo):
            if messagebox.askyesno("Restaurar Copia", "Ya existe un respaldo anterior.\n\n¿Deseas RESTAURAR los archivos ahora?"):
                self.restaurar_respaldo(ruta_steam, ruta_respaldo)
                return

        # Paso 4: Limpieza de Caché
        self.registrar("\n[Paso 4] Iniciando limpieza de archivos temporales...")
        self.cerrar_steam()
        
        try:
            if not os.path.exists(ruta_respaldo): os.makedirs(ruta_respaldo)
            
            # Limpieza de Appcache (Preservando estadísticas locales)
            appcache = os.path.join(ruta_steam, "appcache")
            respaldo_app = os.path.join(ruta_respaldo, "appcache")
            if os.path.exists(appcache):
                if os.path.exists(respaldo_app): shutil.rmtree(respaldo_app, ignore_errors=True)
                os.makedirs(respaldo_app)
                for item in os.listdir(appcache):
                    origen, destino = os.path.join(appcache, item), os.path.join(respaldo_app, item)
                    if item.lower() != "stats":
                        shutil.move(origen, destino)
                    else:
                        shutil.copytree(origen, destino, dirs_exist_ok=True)
            
            # Limpieza de Depotcache
            depot = os.path.join(ruta_steam, "depotcache")
            respaldo_depot = os.path.join(ruta_respaldo, "depotcache")
            if os.path.exists(depot):
                if os.path.exists(respaldo_depot): shutil.rmtree(respaldo_depot, ignore_errors=True)
                shutil.move(depot, respaldo_depot)

            # Limpieza de datos de usuario (Preservando tiempo de juego)
            userdata = os.path.join(ruta_steam, "userdata")
            if os.path.exists(userdata):
                for usuario in os.listdir(userdata):
                    ruta_usuario = os.path.join(userdata, usuario)
                    if os.path.isdir(ruta_usuario):
                        config = os.path.join(ruta_usuario, "config")
                        if os.path.exists(config):
                            respaldo_usuario = os.path.join(ruta_respaldo, "userdata", usuario, "config")
                            if os.path.exists(respaldo_usuario): 
                                shutil.rmtree(os.path.dirname(respaldo_usuario), ignore_errors=True)
                            os.makedirs(os.path.dirname(respaldo_usuario), exist_ok=True)
                            shutil.move(config, respaldo_usuario)
                            
                            # Restaurar localconfig.vdf inmediatamente
                            os.makedirs(config, exist_ok=True)
                            shutil.copy2(os.path.join(respaldo_usuario, "localconfig.vdf"), os.path.join(config, "localconfig.vdf"))
            
            self.registrar("¡Limpieza finalizada con éxito!")
            subprocess.Popen([os.path.join(ruta_steam, "steam.exe"), "-clearbeta"])
            messagebox.showinfo("Éxito", "Proceso completado. Steam se está reiniciando.")
        except Exception as e:
            self.registrar(f"Ocurrió un error inesperado: {e}")
        
        self.restablecer_boton()

    def restaurar_respaldo(self, ruta_steam, ruta_respaldo):
        """Mueve los archivos desde el respaldo de vuelta a la carpeta principal."""
        self.cerrar_steam()
        self.registrar("Restaurando archivos originales...")
        for item in os.listdir(ruta_respaldo):
            origen, destino = os.path.join(ruta_respaldo, item), os.path.join(ruta_steam, item)
            if os.path.exists(destino):
                if os.path.isdir(destino): shutil.rmtree(destino, ignore_errors=True)
                else: os.remove(destino)
            shutil.move(origen, destino)
        shutil.rmtree(ruta_respaldo)
        subprocess.Popen([os.path.join(ruta_steam, "steam.exe"), "-clearbeta"])
        self.registrar("Respaldo restaurado correctamente.")
        self.restablecer_boton()

    def restablecer_boton(self):
        self.start_btn.configure(state="normal", text="Iniciar Corrección")

if __name__ == "__main__":
    if es_administrador():
        app = AplicacionCorrectora()
        app.mainloop()
    else:
        # Re-lanza la aplicación pidiendo permisos de administrador
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
