# 🎮 Mobile Spoof Bypass v2

Herramienta Python para inyectar `.so` en Free Fire vía ADB y hacer pasar el emulador como **Samsung A54 5G** ante los servidores del juego.

## ¿Qué hace?

1. Compila `libwag_own.so` (payload de spoof) y `libmain_loader.so` con Android NDK
2. Los inyecta en el proceso de Free Fire via ADB
3. Aplica spoofing de resolución, DPI y propiedades del sistema
4. El servidor del juego ve un Samsung A54 5G real

## Requisitos

- **Python 3.8+**
- **ADB** (incluido en MEmu / BlueStacks)
- **Android NDK** (solo para compilar `.so`) → [Descargar NDK](https://developer.android.com/ndk/downloads)
- **Emulador corriendo** (MEmu Play recomendado)

## Instalación

```bash
git clone https://github.com/miotinoco21-ux/mobile-spoof-bypass
cd mobile-spoof-bypass
python mobile_spoof_bypass.py
```

## Uso rápido

| Situación | Pasos |
|---|---|
| Primera vez | `[1]` Compilar .so → `[2]` Aplicar Bypass |
| Ya tienes los .so | Directo a `[2]` Aplicar Bypass |
| Restaurar juego original | `[4]` Restaurar |

## Puertos ADB por emulador

| Emulador | Puerto |
|---|---|
| MEmu Play | 21503 |
| BlueStacks MSI | 5555 |
| BlueStacks 5 | 5555 |
| Nox Player | 62001 |

## Estructura del proyecto

```
mobile-spoof-bypass/
├── mobile_spoof_bypass.py   ← Script principal
├── native_src/
│   ├── wag_own.c            ← Payload de spoof
│   ├── libmain_loader.c     ← Loader .so
│   ├── Android.mk           ← Build script NDK
│   └── Application.mk       ← Config ABI
└── native_out/              ← .so compilados (generado al compilar, excluido de git)
    └── libs/
        ├── x86/
        ├── x86_64/
        ├── armeabi-v7a/
        └── arm64-v8a/
```

## ⚠️ Advertencia

Este proyecto es solo para uso educativo e investigación de seguridad.