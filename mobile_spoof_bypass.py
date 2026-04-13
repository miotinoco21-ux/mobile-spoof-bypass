"""
Mobile Spoof Bypass v2
Inyecta .so en Free Fire via ADB para hacer device spoofing (Samsung A54) en emuladores Android.
"""

import os
import sys
import subprocess
import shutil
import glob
import time
from datetime import datetime
from pathlib import Path

# ─── CONFIGURACION ─────────────────────────────────────────────────────────────
CONFIG = {
    "adb_port": "21503",
    "package": "com.dts.freefireth",
    "spoof_model": "SM-A546E",
    "spoof_brand": "samsung",
    "spoof_manufacturer": "samsung",
    "resolution": "2340x1080",
    "dpi": 420,
    "ndk_path": "",
    "src_dir": "./native_src",
    "out_dir": "./native_out",
    "programdata": "C:/ProgramData",
}

# ─── COLORES ANSI ───────────────────────────────────────────────────────────────
USE_COLOR = sys.stdout.isatty()
GREEN  = "\033[92m" if USE_COLOR else ""
RED    = "\033[91m" if USE_COLOR else ""
YELLOW = "\033[93m" if USE_COLOR else ""
CYAN   = "\033[96m" if USE_COLOR else ""
BOLD   = "\033[1m"  if USE_COLOR else ""
RESET  = "\033[0m"  if USE_COLOR else ""


def ts() -> str:
    """Retorna timestamp [HH:MM:SS]."""
    return datetime.now().strftime("[%H:%M:%S]")


def log(msg: str, color: str = "") -> None:
    """Imprime mensaje con timestamp y color opcional."""
    print(f"{ts()} {color}{msg}{RESET}")


def find_adb() -> str:
    """Busca ADB en rutas conocidas de MEmu y BlueStacks."""
    candidates = [
        "C:/Program Files/Microvirt/MEmu/adb.exe",
        "C:/Program Files (x86)/Microvirt/MEmu/adb.exe",
        "C:/Program Files/MEmuManage/adb.exe",
        "C:/Program Files/Bluestacks_msi5/HD-Adb.exe",
        "C:/Program Files/BlueStacks_nxt/HD-Adb.exe",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    fallback = shutil.which("adb")
    return fallback if fallback else ""


def find_ndk() -> str:
    """Busca ndk-build en rutas conocidas."""
    ndk_bin = "ndk-build.cmd" if sys.platform == "win32" else "ndk-build"

    env_ndk = os.environ.get("ANDROID_NDK_HOME", "")
    if env_ndk:
        candidate = os.path.join(env_ndk, ndk_bin)
        if os.path.isfile(candidate):
            return candidate

    win_patterns = [
        "C:/Android/ndk/*/ndk-build.cmd",
        "C:/Users/*/AppData/Local/Android/Sdk/ndk/*/ndk-build.cmd",
    ]
    for pattern in win_patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]

    fallback = shutil.which(ndk_bin)
    return fallback if fallback else ""


def run_adb(adb_path: str, args: str, port: str, capture: bool = False) -> str:
    """Ejecuta un comando ADB. Retorna stdout si capture=True, si no ''."""
    cmd = [adb_path, "-s", f"127.0.0.1:{port}"] + args.split()
    kwargs = {"timeout": 30}
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    try:
        if capture:
            kwargs["capture_output"] = True
            result = subprocess.run(cmd, **kwargs)
            return result.stdout.decode(errors="replace")
        else:
            subprocess.run(cmd, **kwargs)
            return ""
    except Exception as exc:
        log(f"[ERROR] ADB: {exc}", RED)
        return ""


def create_native_sources(src_dir: str, config: dict) -> None:
    """Crea el directorio de fuentes nativas y escribe los archivos C/mk."""
    os.makedirs(src_dir, exist_ok=True)

    model = config["spoof_model"]
    brand = config["spoof_brand"]
    manufacturer = config["spoof_manufacturer"]

    wag_own_c = f"""\
#include <jni.h>
#include <android/log.h>
#include <stdlib.h>
#include <string.h>

#define TAG "libwag_own"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)

__attribute__((constructor))
static void on_load(void) {{
    LOGI("libwag_own loaded - Mobile Spoof Bypass v2");
    setenv("ro.product.model",        "{model}",  1);
    setenv("ro.product.brand",        "{brand}",   1);
    setenv("ro.product.manufacturer", "{manufacturer}",   1);
    setenv("ro.product.name",         "a54xnsxx",  1);
    setenv("ro.product.device",       "a54x",      1);
    setenv("ro.build.fingerprint",
        "samsung/a54xnsxx/a54x:13/TP1A.220624.014/A546EXXS5EXL1:user/release-keys", 1);
    LOGI("Device spoofed as {model}");
}}
"""

    libmain_loader_c = """\
#include <dlfcn.h>
#include <android/log.h>
#include <stdlib.h>

#define TAG "libmain_loader"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)

__attribute__((constructor))
static void loader_init(void) {
    LOGI("libmain_loader initializing...");
    void* wag = dlopen("/data/local/tmp/libwag_own.so", RTLD_NOW | RTLD_GLOBAL);
    if (!wag) {
        LOGI("ERROR loading libwag_own: %s", dlerror());
    } else {
        LOGI("libwag_own loaded OK");
    }
    void* orig = dlopen("/data/local/tmp/libmain_backup.so", RTLD_NOW | RTLD_GLOBAL);
    if (!orig) {
        LOGI("ERROR loading backup: %s", dlerror());
    } else {
        LOGI("libmain backup loaded OK");
    }
}
"""

    android_mk = """\
LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE    := libwag_own
LOCAL_SRC_FILES := wag_own.c
LOCAL_LDLIBS    := -llog
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE    := libmain_loader
LOCAL_SRC_FILES := libmain_loader.c
LOCAL_LDLIBS    := -llog -ldl
include $(BUILD_SHARED_LIBRARY)
"""

    application_mk = """\
APP_ABI      := x86 x86_64 armeabi-v7a arm64-v8a
APP_PLATFORM := android-21
APP_STL      := none
APP_OPTIM    := release
"""

    Path(os.path.join(src_dir, "wag_own.c")).write_text(wag_own_c, encoding="utf-8")
    Path(os.path.join(src_dir, "libmain_loader.c")).write_text(libmain_loader_c, encoding="utf-8")
    Path(os.path.join(src_dir, "Android.mk")).write_text(android_mk, encoding="utf-8")
    Path(os.path.join(src_dir, "Application.mk")).write_text(application_mk, encoding="utf-8")


def compile_so(config: dict) -> bool:
    """Compila libwag_own.so y libmain_loader.so con Android NDK."""
    src_dir = config["src_dir"]
    out_dir = config["out_dir"]

    create_native_sources(src_dir, config)

    ndk_build = config.get("ndk_path", "") or find_ndk()
    if not ndk_build:
        log("[ERROR] Android NDK no encontrado.", RED)
        log("[INFO] Descarga NDK desde: https://developer.android.com/ndk/downloads", YELLOW)
        log("[INFO] Luego configura la ruta en el menu Configurar → NDK Path.", YELLOW)
        return False

    os.makedirs(out_dir, exist_ok=True)

    cmd = [
        ndk_build,
        f"NDK_PROJECT_PATH={src_dir}",
        f"APP_BUILD_SCRIPT={src_dir}/Android.mk",
        f"NDK_OUT={out_dir}/obj",
        f"NDK_LIBS_OUT={out_dir}/libs",
        'APP_ABI=x86 x86_64 armeabi-v7a arm64-v8a',
    ]

    log("[INFO] Ejecutando ndk-build...", CYAN)
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in proc.stdout:
            print(f"[BUILD] {line}", end="")
        proc.wait()
        if proc.returncode == 0:
            log("[OK] Compilacion exitosa. Copiados: libmain_loader.so, libwag_own.so", GREEN)
            return True
        else:
            log(f"[ERROR] ndk-build termino con codigo {proc.returncode}", RED)
            return False
    except Exception as exc:
        log(f"[ERROR] Al ejecutar ndk-build: {exc}", RED)
        return False


def find_lib_dir(adb_path: str, package: str, port: str) -> str:
    """Retorna el directorio de librerías x86 del paquete en el dispositivo."""
    output = run_adb(adb_path, f"shell pm path {package}", port, capture=True)
    for line in output.splitlines():
        if line.startswith("package:"):
            apk_path = line.split("package:")[1].strip()
            app_dir = os.path.dirname(apk_path)
            return f"{app_dir}/lib/x86"
    return ""


def apply_bypass(adb_path: str, config: dict) -> None:
    """Aplica el bypass completo: sube .so, parchea libmain, aplica spoof."""
    port = config["adb_port"]
    out_dir = config["out_dir"]

    # Verificar que los .so existen
    wag_so = f"{out_dir}/libs/x86/libwag_own.so"
    loader_so = f"{out_dir}/libs/x86/libmain_loader.so"
    if not os.path.isfile(wag_so) or not os.path.isfile(loader_so):
        log("[ERROR] Los archivos .so no fueron encontrados.", RED)
        log("[INFO] Ejecuta primero la opcion [1] Compilar .so", YELLOW)
        return

    # Paso 1
    log("1 \u25a1 Detectando ruta del juego...", CYAN)
    lib_dir = find_lib_dir(adb_path, config["package"], port)
    if not lib_dir:
        log("[ERROR] No se pudo detectar la ruta del juego.", RED)
        log("[INFO] Asegurate de que Free Fire este instalado en el emulador.", YELLOW)
        return
    log(f"  Ruta: {lib_dir}")

    # Paso 2
    log("2 \u25a1 Subiendo libwag_own.so a /data/local/tmp/...", CYAN)
    run_adb(adb_path, f'push {wag_so} /data/local/tmp/libwag_own.so', port)
    log("  OK: [100%] /data/local/tmp/libwag_own.so", GREEN)

    # Paso 3
    log("3 \u25a1 Respaldando libmain.so original...", CYAN)
    log("  Creando backup...")
    run_adb(adb_path, f'shell su -c "cp {lib_dir}/libmain.so /data/local/tmp/libmain_backup.so"', port)
    log("  Backup creado \u2713", GREEN)

    # Paso 4
    log("4 \u25a1 Subiendo libmain_loader.so...", CYAN)
    run_adb(adb_path, f'push {loader_so} /sdcard/libmain_loader.so', port)
    log("  Subido: [100%] /sdcard/libmain_loader.so", GREEN)

    # Paso 5
    log("5 \u25a1 Instalando como libmain.so del juego...", CYAN)
    run_adb(adb_path,
            f'shell su -c "cp /sdcard/libmain_loader.so {lib_dir}/libmain.so && chmod 755 {lib_dir}/libmain.so"',
            port)
    log("  libmain_loader instalado \u2713", GREEN)

    # Paso 6
    log("6 \u25a1 Aplicando Mobile Spoof (resolucion + DPI)...", CYAN)
    run_adb(adb_path, f"shell wm size {config['resolution']}", port)
    run_adb(adb_path, f"shell wm density {config['dpi']}", port)
    log(f"  Resolucion: {config['resolution']} @ {config['dpi']}dpi \u2713", GREEN)

    # Paso 7
    log("7 \u25a1 Aplicando system props (cobertura doble)...", CYAN)
    run_adb(adb_path, f"shell su -c \"setprop ro.product.model '{config['spoof_model']}'\"", port)
    run_adb(adb_path, f"shell su -c \"setprop ro.product.brand '{config['spoof_brand']}'\"", port)
    run_adb(adb_path, f"shell su -c \"setprop ro.product.manufacturer '{config['spoof_manufacturer']}'\"", port)
    log("  Props aplicadas \u2713", GREEN)

    # Paso 8
    log("8 \u25a1 Reiniciando Free Fire...", CYAN)
    run_adb(adb_path, f"shell am force-stop {config['package']}", port)
    time.sleep(1.5)
    run_adb(adb_path, f"shell monkey -p {config['package']} -c android.intent.category.LAUNCHER 1", port)

    print(f"\n{ts()} {GREEN}\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510{RESET}")
    print(f"{ts()} {GREEN}\u2502 \u2705 MOBILE SPOOF BYPASS APLICADO          \u2502{RESET}")
    print(f"{ts()} {GREEN}\u2502 El servidor te ver\u00e1 como Samsung A54 5G  \u2502{RESET}")
    print(f"{ts()} {GREEN}\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518{RESET}\n")


def restore(adb_path: str, config: dict) -> None:
    """Restaura libmain.so original y resetea resolución y DPI."""
    port = config["adb_port"]
    log("Restaurando libmain.so original...", YELLOW)
    lib_dir = find_lib_dir(adb_path, config["package"], port)
    if lib_dir:
        run_adb(adb_path,
                f'shell su -c "cp /data/local/tmp/libmain_backup.so {lib_dir}/libmain.so"',
                port)
    run_adb(adb_path, "shell wm size reset", port)
    run_adb(adb_path, "shell wm density reset", port)
    log("[OK] Restauracion completada \u2713", GREEN)


def frida_mode(adb_path: str, config: dict) -> None:
    """Instala Frida Gadget si está disponible en ProgramData."""
    port = config["adb_port"]
    gadget = os.path.join(config["programdata"], "frida-gadget.so")
    if os.path.exists(gadget):
        run_adb(adb_path, f'push "{gadget}" /data/local/tmp/frida-gadget.so', port)
        run_adb(adb_path, "shell su -c 'chmod 755 /data/local/tmp/frida-gadget.so'", port)
        log("[OK] Frida Gadget instalado", GREEN)
        log(f"[INFO] Conecta con: frida -U -f {config['package']} --no-pause", CYAN)
    else:
        log("[ERROR] frida-gadget.so no encontrado en " + gadget, RED)
        log("[INFO] Descarga desde: https://github.com/frida/frida/releases", YELLOW)
        log(f"[INFO] Guarda como: {gadget}", YELLOW)


def clean_temp(adb_path: str, config: dict) -> None:
    """Elimina archivos temporales del dispositivo."""
    port = config["adb_port"]
    run_adb(adb_path,
            'shell su -c "rm -f /data/local/tmp/libwag_own.so /data/local/tmp/libmain_backup.so /sdcard/libmain_loader.so"',
            port)
    log("[OK] Archivos temporales eliminados \u2713", GREEN)


def configure_menu(config: dict) -> dict:
    """Submenú interactivo para editar la configuración."""
    while True:
        print(f"""
\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557
\u2551  \u2699\ufe0f  CONFIGURACION                       \u2551
\u2560\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2563
\u2551  [1] Puerto ADB          \u2192 {config['adb_port']:<15}\u2551
\u2551  [2] Paquete             \u2192 {config['package'][:15]:<15}\u2551
\u2551  [3] Modelo spoof        \u2192 {config['spoof_model']:<15}\u2551
\u2551  [4] Resolucion          \u2192 {config['resolution']:<15}\u2551
\u2551  [5] DPI                 \u2192 {config['dpi']:<15}\u2551
\u2551  [6] Volver                                \u2551
\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d""")
        choice = input("Selecciona opcion: ").strip()
        if choice == "1":
            val = input(f"Nuevo puerto ADB [{config['adb_port']}]: ").strip()
            if val:
                config["adb_port"] = val
        elif choice == "2":
            val = input(f"Nuevo paquete [{config['package']}]: ").strip()
            if val:
                config["package"] = val
        elif choice == "3":
            val = input(f"Nuevo modelo spoof [{config['spoof_model']}]: ").strip()
            if val:
                config["spoof_model"] = val
        elif choice == "4":
            val = input(f"Nueva resolucion [{config['resolution']}]: ").strip()
            if val:
                config["resolution"] = val
        elif choice == "5":
            val = input(f"Nuevo DPI [{config['dpi']}]: ").strip()
            if val:
                try:
                    config["dpi"] = int(val)
                except ValueError:
                    log("[ERROR] DPI debe ser un numero entero.", RED)
        elif choice == "6":
            break
        else:
            log("[AVISO] Opcion no valida.", YELLOW)
    return config


def main_menu() -> None:
    """Loop principal del menú interactivo."""
    config = CONFIG.copy()
    try:
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            adb_path = find_adb()
            adb_status = f"{GREEN}\u2713 Conectado{RESET}" if adb_path else f"{RED}\u2717 No encontrado{RESET}"

            print(f"""
{BOLD}\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557{RESET}
{BOLD}\u2551     \U0001f3ae MOBILE SPOOF BYPASS v2                \u2551{RESET}
{BOLD}\u2551     Free Fire \u2500 MEmu/BlueStacks \u2192 Samsung A54 \u2551{RESET}
{BOLD}\u2560\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2563{RESET}
{BOLD}\u2551  ADB: {adb_status:<10}  Puerto: {config['adb_port']:<18}{BOLD}\u2551{RESET}
{BOLD}\u2551  Paquete: {config['package']:<37}{BOLD}\u2551{RESET}
{BOLD}\u2560\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2563{RESET}
{BOLD}\u2551  [1] \U0001f527 Compilar .so  (requiere NDK)         \u2551{RESET}
{BOLD}\u2551  [2] \U0001f680 Aplicar Bypass                       \u2551{RESET}
{BOLD}\u2551  [3] \U0001f52c Frida Mode                           \u2551{RESET}
{BOLD}\u2551  [4] \U0001f504 Restaurar                            \u2551{RESET}
{BOLD}\u2551  [5] \u2699\ufe0f  Configurar                          \u2551{RESET}
{BOLD}\u2551  [6] \U0001f9f9 Limpiar archivos temporales          \u2551{RESET}
{BOLD}\u2551  [0] \u274c Salir                                \u2551{RESET}
{BOLD}\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d{RESET}""")

            choice = input("Selecciona opcion: ").strip()

            if choice == "0":
                print("\n[!] Saliendo...")
                sys.exit(0)

            elif choice == "1":
                compile_so(config)
                input("\n[Presiona Enter para continuar...]")

            elif choice == "2":
                if not adb_path:
                    log("[ERROR] ADB no encontrado. Instala MEmu o BlueStacks primero.", RED)
                else:
                    apply_bypass(adb_path, config)
                input("\n[Presiona Enter para continuar...]")

            elif choice == "3":
                if not adb_path:
                    log("[ERROR] ADB no encontrado. Instala MEmu o BlueStacks primero.", RED)
                else:
                    frida_mode(adb_path, config)
                input("\n[Presiona Enter para continuar...]")

            elif choice == "4":
                if not adb_path:
                    log("[ERROR] ADB no encontrado. Instala MEmu o BlueStacks primero.", RED)
                else:
                    restore(adb_path, config)
                input("\n[Presiona Enter para continuar...]")

            elif choice == "5":
                config = configure_menu(config)

            elif choice == "6":
                if not adb_path:
                    log("[ERROR] ADB no encontrado. Instala MEmu o BlueStacks primero.", RED)
                else:
                    clean_temp(adb_path, config)
                input("\n[Presiona Enter para continuar...]")

            else:
                log("[AVISO] Opcion no valida.", YELLOW)
                input("\n[Presiona Enter para continuar...]")

    except KeyboardInterrupt:
        print("\n[!] Saliendo...")
        sys.exit(0)


if __name__ == "__main__":
    main_menu()
