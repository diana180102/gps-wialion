## Integración con Wialon (`feat/wialon-client`)

Requisitos relacionados: [INT-01, INT-02: pon los IDs del documento].

### Qué hace
El cliente (`backend/adapters/wialon/client.py`) aísla toda la comunicación con
la API de Wialon. El resto de la aplicación no conoce el formato de la API ni
las credenciales.

- **Autenticación:** `token/login` devuelve un `eid`; el cliente lo guarda en
  memoria como `sid` y lo envía en cada llamada posterior.
- **Renovación de sesión:** si Wialon responde `error: 1` (sesión inválida), el
  cliente vuelve a autenticarse y reintenta **una sola vez**.
- **Concurrencia:** un `asyncio.Lock` evita que dos peticiones simultáneas
  hagan login a la vez.
- **Errores:** timeouts, fallos de red y códigos HTTP no 2xx se convierten en
  `UpstreamUnavailable`; errores propios de Wialon, en `UpstreamError`. Ninguna
  excepción de `httpx` sale de este módulo.
- **Secretos:** el token y el `sid` nunca se imprimen ni se registran.



### Cómo se verificó
- `python -m scripts.probe` (desde `backend/`) hace login, lista unidades,
  invalida la sesión a propósito y comprueba que el cliente se recupera.
- Los fixtures de `tests/fixtures/` son respuestas reales de Wialon con los
  datos sensibles reemplazados por `REDACTED`.

### Uso de IA en esta parte
Herramienta: **Claude Code**.

- **Por qué:** trabaja sobre el repositorio real (estructura, fixtures,
  configuración) y ejecuta el código, así que los fallos de integración se
  detectan en el momento.
- **Qué generó:** borrador de `client.py`, `domain/errors.py` y `scripts/probe.py`,
  a partir de mis requisitos y de las respuestas reales de Wialon.
- **Qué decidí yo:** el diseño de la integración (un único cliente aislado, un
  reintento, un lock), el manejo de secretos y qué respuestas usar como fixtures.
- **Qué revisé y corregí:** [ej.: en `_post`, el `except httpx.HTTPError` leía
  `exc.response`, que solo existe en `HTTPStatusError`; lo separé en dos casos
  para que los fallos de red no produjeran un `AttributeError`].
- **Cómo me aseguré de entenderlo:** leí el archivo completo antes del commit y
  probé contra la API real.