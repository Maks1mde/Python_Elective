"""
Пакет алгоритмов подсчёта клеток.
"""

_discovered = False


def autodiscover_algorithms() -> None:
    global _discovered
    if _discovered:
        return

    import models.algorithm_plugin  # noqa

    __import__("models.knn_expert")
    print("✓ knn_expert")

    __import__("models.resnet18_model")
    print("✓ resnet18")

    __import__("models.unet_model")
    print("✓ unet")

    _discovered = True