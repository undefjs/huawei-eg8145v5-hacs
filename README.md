# Huawei EG8145V5 Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Integración personalizada de Home Assistant para el router **Huawei EG8145V5 GPON**.

## Características

✅ **Sensores del router**
- Contador de dispositivos conectados
- Uso de CPU
- Uso de memoria
- Información del dispositivo (modelo, versión, serial)

✅ **Seguimiento de dispositivos**
- Detección automática de dispositivos conectados
- Rastreo de presencia (home/away)
- Información detallada: IP, MAC, tiempo conectado, tipo de dispositivo

## Instalación

### Vía HACS (Recomendado)

1. Asegúrate de tener [HACS](https://hacs.xyz/) instalado
2. Ve a HACS → Integraciones → ⋮ (menú superior derecho) → Repositorios personalizados
3. Añade este repositorio:
   - **URL**: `https://github.com/undefjs/huawei-eg8145v5-hacs`
   - **Categoría**: Integration
4. Haz clic en "Explorar y descargar repositorios"
5. Busca "Huawei EG8145V5" y haz clic en "Descargar"
6. Reinicia Home Assistant

### Manual

1. Copia la carpeta `custom_components/huawei_eg8145v5` a tu carpeta `config/custom_components/`
2. Reinicia Home Assistant

## Configuración

1. Ve a **Configuración** → **Dispositivos y servicios** → **Añadir integración**
2. Busca "Huawei EG8145V5"
3. Introduce las credenciales de tu router:
   - **Host**: `192.168.18.1` (o la IP de tu router)
   - **Usuario**: Tu nombre de usuario del router
   - **Contraseña**: Tu contraseña del router

## Detalles Técnicos

### Autenticación
La integración utiliza el mecanismo de autenticación nativo del router:
- Obtiene token de `/asp/GetRandCount.asp`
- Contraseña codificada en Base64
- Cookie de sesión: `Cookie=body:Language:english:id=-1`

### Endpoints utilizados
- **Dispositivos conectados**: `/html/bbsp/userdevinfo/getuserdevinfo.asp`
- **Información del router**: `/html/ssmp/deviceinfo/deviceinfo.asp`

### Actualización de datos
- Los datos se actualizan cada 30 segundos
- El re-login automático en caso de expiración de sesión

## Compatibilidad

✅ **Probado con**:
- Huawei EG8145V5 (Firmware: V5R020C10S195)
- Home Assistant 2023.1+

⚠️ **Puede funcionar con**:
- Otros modelos de la serie EG8145
- Firmware similar (verificar endpoints)

## Sensores disponibles

| Sensor | Descripción | Ejemplo |
|--------|-------------|---------|
| `sensor.eg8145v5_device_count` | Número de dispositivos conectados | `12` |
| `sensor.eg8145v5_cpu_usage` | Uso de CPU | `9%` |
| `sensor.eg8145v5_memory_usage` | Uso de memoria | `50%` |
| `device_tracker.*` | Rastreador por cada dispositivo | `home`/`away` |

## Solución de problemas

### La integración no aparece
- Asegúrate de haber reiniciado Home Assistant después de la instalación
- Verifica que la carpeta `custom_components/huawei_eg8145v5` existe

### Error de autenticación
- Verifica que las credenciales son correctas
- Comprueba que puedes acceder al router en `http://192.168.18.1`
- Espera si hay un bloqueo por múltiples intentos fallidos

### No se detectan dispositivos
- Verifica que hay dispositivos conectados al router
- Revisa los logs de Home Assistant para más detalles

## Contribuir

¿Encontraste un error o tienes una sugerencia? Abre un issue en GitHub.

## Licencia

MIT License - Ver archivo [LICENSE](LICENSE) para más detalles.

## Créditos

Basado en la integración base de [Huawei HG659](https://github.com/Sheep26/huawei_hg659) de @Sheep26.
