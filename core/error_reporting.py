"""
Muestra errores por pantalla con tipo, mensaje y traceback completo.
"""
import sys
import traceback


def report_exception(exc: BaseException, title: str = "Error") -> None:
    """
    Imprime el error de forma visible en consola (stderr).
    """
    lines = [
        "",
        "=" * 72,
        f" {title}: {type(exc).__name__}",
        "=" * 72,
        str(exc),
        "-" * 72,
    ]
    msg = "\n".join(lines)
    print(msg, file=sys.stderr)
    traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
    print("=" * 72, file=sys.stderr)


def run_with_error_report(main_callable, *, exit_on_error: bool = True):
    """
    Ejecuta main_callable() y captura excepciones mostrándolas por pantalla.
    """
    try:
        return main_callable()
    except KeyboardInterrupt:
        print("\nParado por el usuario.", file=sys.stderr)
        if exit_on_error:
            sys.exit(130)
        raise
    except Exception as e:
        report_exception(e)
        if exit_on_error:
            sys.exit(1)
        raise
