"""Разбор и валидация параметров командной строки."""

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

MIN_DEPTH = 0
DEFAULT_DEPTH = 3
VALID_SCHEMES = ("http://", "https://")


@dataclass
class Config:
    """Параметры конфигурации приложения."""

    package: str
    repo: str
    test_mode: bool
    version: str
    max_depth: int
    filter_substr: str
    reverse: bool = False
    show_config: bool = False
    direct_only: bool = False


def build_parser() -> argparse.ArgumentParser:
    """Создать и настроить парсер аргументов CLI."""
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей npm."
    )
    parser.add_argument(
        "-p", "--package", required=True, help="Имя анализируемого пакета."
    )
    parser.add_argument(
        "-r", "--repo", required=True, help="URL реестра или путь к файлу."
    )
    parser.add_argument(
        "-t", "--test-mode", action="store_true", help="Режим теста."
    )
    parser.add_argument(
        "-v", "--version", default="", help="Версия пакета."
    )
    parser.add_argument(
        "-d", "--max-depth", type=int, default=DEFAULT_DEPTH,
        help="Максимальная глубина анализа зависимостей."
    )
    parser.add_argument(
        "-f", "--filter", default="", dest="filter_substr",
        help="Подстрока для фильтрации пакетов."
    )
    parser.add_argument(
        "--reverse", action="store_true", help="Режим обратных зависимостей."
    )
    parser.add_argument(
        "--show-config", action="store_true", help="Вывод параметров."
    )
    parser.add_argument(
        "--direct-only", action="store_true", help="Только прямые зависимости."
    )
    return parser


def _validate_mode_specific(config: Config) -> None:
    """Проверить параметры, зависящие от режима (тестовый или реальный)."""
    if config.test_mode:
        if not Path(config.repo).is_file():
            raise ValueError(
                f"Файл тестового репозитория не найден: {config.repo}"
            )
        return
    if not config.repo.startswith(VALID_SCHEMES):
        raise ValueError(
            "URL репозитория должен начинаться с http:// или https://."
        )
    if not config.version.strip():
        raise ValueError("В реальном режиме необходимо указать версию.")


def validate_config(config: Config) -> None:
    """Проверить корректность параметров и выбросить ValueError при ошибке."""
    if not config.package.strip():
        raise ValueError("Имя пакета не должно быть пустым.")
    if not config.repo.strip():
        raise ValueError("URL репозитория или путь не должны быть пустыми.")
    if config.max_depth < MIN_DEPTH:
        raise ValueError("Максимальная глубина должна быть >= 0.")
    _validate_mode_specific(config)


def parse_args(argv: Optional[List[str]] = None) -> Config:
    """Разобрать и провалидировать аргументы командной строки."""
    parser = build_parser()
    ns = parser.parse_args(argv)
    config = Config(
        package=ns.package.strip(),
        repo=ns.repo.strip(),
        test_mode=ns.test_mode,
        version=ns.version.strip(),
        max_depth=ns.max_depth,
        filter_substr=ns.filter_substr,
        reverse=ns.reverse,
        show_config=ns.show_config,
        direct_only=ns.direct_only,
    )
    validate_config(config)
    return config


def format_config(config: Config) -> str:
    """Сформировать вывод параметров в формате ключ-значение."""
    lines = [
        f"package: {config.package}",
        f"repo: {config.repo}",
        f"test_mode: {config.test_mode}",
        f"version: {config.version}",
        f"max_depth: {config.max_depth}",
        f"filter: {config.filter_substr}",
    ]
    return "\n".join(lines)