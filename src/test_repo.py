"""Загрузчик графа зависимостей из локального тестового файла."""

import re
from pathlib import Path
from typing import Dict, List

PACKAGE_PATTERN = re.compile(r"^[A-Z]+$")
LINE_SEPARATOR = ":"
DEP_SEPARATOR = ","


class TestRepository:
    """Читает описание графа зависимостей из текстового файла."""

    def __init__(self, file_path: str) -> None:
        """Разобрать файл тестового репозитория в список смежности."""
        self._graph: Dict[str, List[str]] = {}
        self._load(Path(file_path))

    def _validate_name(self, name: str) -> None:
        """Проверить, что имя пакета состоит из заглавных латинских букв."""
        if not PACKAGE_PATTERN.match(name):
            raise ValueError(
                f"Некорректное имя пакета '{name}': используйте A-Z."
            )

    def _parse_line(self, line: str) -> None:
        """Разобрать строку формата 'PKG: DEP1, DEP2'."""
        if LINE_SEPARATOR not in line:
            raise ValueError(f"Некорректный формат строки: '{line}'")
        pkg_part, deps_part = line.split(LINE_SEPARATOR, maxsplit=1)
        pkg = pkg_part.strip()
        self._validate_name(pkg)
        deps: List[str] = []
        if deps_part.strip():
            for raw_dep in deps_part.split(DEP_SEPARATOR):
                dep = raw_dep.strip()
                if dep:
                    self._validate_name(dep)
                    deps.append(dep)
        self._graph[pkg] = deps

    def _load(self, path: Path) -> None:
        """Прочитать все непустые строки из файла репозитория."""
        content = path.read_text(encoding="utf-8")
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if line:
                self._parse_line(line)

    def get_dependencies(
        self, package: str, version: str = ""
    ) -> Dict[str, str]:
        """Вернуть прямые зависимости пакета из тестового графа."""
        if package not in self._graph:
            raise RuntimeError(
                f"Пакет '{package}' не найден в тестовом репозитории."
            )
        return {dep: "" for dep in self._graph[package]}

    def get_all_packages(self) -> List[str]:
        """Вернуть список всех пакетов, описанных в тестовом репозитории."""
        return list(self._graph.keys())
