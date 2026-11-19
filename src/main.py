"""Точка входа CLI-приложения визуализатора зависимостей."""

import sys
from typing import List, Optional

from src.cli import Config, format_config, parse_args
from src.graph import DependencyGraphBuilder
from src.npm_client import NpmRepository
from src.test_repo import TestRepository
from src.visualizer import to_mermaid

EXIT_OK = 0
EXIT_ERROR = 1


def _run_reverse(config: Config, builder: DependencyGraphBuilder) -> None:
    """Выполнить поиск обратных зависимостей и вывести результат."""
    if not config.test_mode:
        raise ValueError("Режим обратных зависимостей требует --test-mode.")
    repo = TestRepository(config.repo)
    revs = builder.find_reverse_dependencies(
        config.package, repo.get_all_packages()
    )
    if not revs:
        print(f"Обратные зависимости для {config.package} не найдены.")
        return
    for dep in revs:
        print(dep)


def _execute(config: Config) -> None:
    """Запустить нужный этап работы согласно настройкам CLI."""
    if config.show_config:
        print(format_config(config))
        return
    provider = (
        TestRepository(config.repo)
        if config.test_mode
        else NpmRepository(config.repo)
    )
    if config.direct_only:
        deps = provider.get_dependencies(config.package, config.version)
        for name, ver in deps.items():
            label = f"{name}: {ver}" if ver else name
            print(label)
        return
    builder = DependencyGraphBuilder(
        provider=provider,
        max_depth=config.max_depth,
        filter_substr=config.filter_substr,
    )
    if config.reverse:
        _run_reverse(config, builder)
        return
    graph = builder.build(config.package, config.version)
    print(to_mermaid(graph, config.package))


def main(argv: Optional[List[str]] = None) -> int:
    """Разобрать аргументы, запустить обработку и перехватить ошибки."""
    try:
        config = parse_args(argv)
        _execute(config)
    except (ValueError, RuntimeError, OSError) as err:
        print(f"Ошибка: {err}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
