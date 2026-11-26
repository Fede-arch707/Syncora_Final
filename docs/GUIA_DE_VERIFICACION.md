# Verificación general de Syncora (El Poli)

## Objetivo

Antes de entregar el proyecto, verificar en conjunto la configuración de Django, la correspondencia entre modelos y migraciones y el funcionamiento de todas las pruebas automáticas disponibles.

**Importante:** esta guía no afirma que las pruebas ya hayan pasado en la computadora del equipo. El resultado real se obtiene ejecutando el verificador.

## Requisitos

- Abrir una terminal de VS Code en la **carpeta principal**, donde está `manage.py`.
- Tener Python y las dependencias de `requirements.txt` instaladas.
- En Windows PowerShell, activar el entorno virtual si no se ve `(.venv)`:

  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```

## Ejecución recomendada

```powershell
python verificar_syncora.py
```

El verificador ejecuta, en este orden:

1. `python manage.py check`: comprueba la configuración y el registro de las aplicaciones.
2. `python manage.py makemigrations --check --dry-run`: detecta cambios de modelos sin migraciones; **no crea migraciones**.
3. `python manage.py test`: descubre y ejecuta **todas** las pruebas automáticas de las aplicaciones.

### Cómo interpretar el resultado

- Si se muestra **`Resultado general: TODAS LAS COMPROBACIONES APROBADAS`**, las tres verificaciones terminaron con código de salida 0.
- Si aparece `[ERROR]`, revisar el mensaje de esa etapa. No crear el commit de verificación hasta corregirlo y volver a ejecutar.
- El número de pruebas puede aumentar cuando se agreguen nuevas pruebas.

Django crea y elimina una **base de datos de prueba** durante `manage.py test`. No debería modificar los clientes, reservas ni pagos de la base de datos local `db.sqlite3`.

## Cobertura de pruebas existentes

| Archivo | Qué se comprueba |
|---|---|
| `clientes/tests.py` | Acceso a páginas, registro y funciones de clientes, exportación de Excel |
| `clientes/test_reglas_clientes.py` | Validación de clientes e historial de reservas |
| `clientes/test_exportacion_excel.py` | Generación de Excel, hojas, importes e historial |
| `clientes/test_seguridad_accesos.py` | Login, permisos, CSRF y protección de acciones |
| `reservas/tests.py` | Reservas, pagos y validaciones principales |
| `reservas/test_reglas_negocio.py` | Reglas de fechas, pagos y saldos |
| `reservas/test_mensajes_formularios.py` | Errores de validación claros |
| `reservas/test_admin_mejorado.py` | Configuración del administrador Django |
| `reservas/test_crud_reservas.py` | Crear, consultar, editar y borrar reservas |

## Verificación manual complementaria

Las pruebas automáticas no reemplazan una comprobación en el navegador. Antes de entregar, revisar también:

- Inicio, cierre y registro de sesión.
- Calendario de **tres meses por pantalla**, navegación y leyenda de estados.
- Alta de clientes, consulta de ficha y reservas repetidas con historial.
- Creación de reservas, detalle, pagos y cálculo del saldo.
- Descarga y apertura del archivo Excel.
- Panel `/admin/`: búsquedas, listas de clientes, salones, reservas y pagos.
- Diseño en pantalla de escritorio y dispositivo móvil.

Usar **datos ficticios** durante las demostraciones y no subir a GitHub `db.sqlite3`, `.venv/`, claves secretas ni credenciales reales.

## Registro de la ejecución

Completar el archivo `docs/RESULTADO_VERIFICACION.md` **después** de ejecutar el verificador y anotar la salida que aparezca realmente. No declarar pruebas aprobadas antes de ejecutarlas.
