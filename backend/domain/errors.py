class UpstreamError(Exception):
    """El upstream (Wialon) respondió con un código de error distinto de 0."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code: int = code
        self.message: str = message


class UpstreamUnavailable(Exception):
    """No se pudo hablar con el upstream (red, timeout o respuesta ilegible)."""
