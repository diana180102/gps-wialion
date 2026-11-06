"""Verificación manual del cliente Wialon. Ejecutar desde backend/:

    python -m scripts.probe
"""
import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.wialon.client import WialonClient  # noqa: E402
from config import get_settings  # noqa: E402

SEARCH_PARAMS: dict[str, Any] = {
    "spec": {
        "itemsType": "avl_unit",
        "propName": "sys_name",
        "propValueMask": "*",
        "sortType": "sys_name",
    },
    "force": 1,
    "flags": 1025,
    "from": 0,
    "to": 0,
}


async def count_units(client: WialonClient) -> tuple[int, int]:
    data = await client.call("core/search_items", SEARCH_PARAMS)
    return len(data["items"]), data["totalItemsCount"]


async def main() -> None:
    settings = get_settings()
    client = WialonClient(settings.wialon_host, settings.wialon_token)
    print(repr(settings.wialon_host))
    try:
        await client.login()
        received, total = await count_units(client)
        print(f"Tras login: {received} unidades recibidas (total reportado: {total})")

        client._sid = None  # a propósito: simula sesión perdida
        received, total = await count_units(client)
        print(f"Tras sid=None: {received} unidades recibidas (total reportado: {total})")
        print("OK: el cliente se recuperó solo.")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
