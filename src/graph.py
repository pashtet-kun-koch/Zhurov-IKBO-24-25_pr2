"""Построение графа зависимостей и обратных зависимостей (DFS)."""

from typing import Dict, List, Protocol, Set

START_DEPTH = 0
DEPTH_STEP = 1


class DependencyProvider(Protocol):
    """Протокол источника зависимостей пакетов."""

    def get_dependencies(
        self, package: str, version: str = ""
    ) -> Dict[str, str]:
        """Вернуть словарь прямых зависимостей пакета."""


class DependencyGraphBuilder:
    """Строит граф прямых и обратных зависимостей рекурсивным DFS."""

    def __init__(
        self,
        provider: DependencyProvider,
        max_depth: int,
        filter_substr: str = "",
    ) -> None:
        """Инициализировать построитель графа с глубиной и фильтром."""
        self._provider = provider
        self._max_depth = max_depth
        self._filter = filter_substr

    def _is_excluded(self, package: str) -> bool:
        """Проверить, нужно ли исключить пакет по подстроке фильтра."""
        return bool(self._filter and self._filter in package)

    def _dfs_forward(
        self,
        package: str,
        version: str,
        depth: int,
        graph: Dict[str, List[str]],
        visited: Set[str],
    ) -> None:
        """Рекурсивно обойти зависимости в глубину (DFS)."""
        visited.add(package)
        graph.setdefault(package, [])
        if depth >= self._max_depth:
            return
        deps = self._provider.get_dependencies(package, version)
        for dep_name, dep_ver in deps.items():
            if self._is_excluded(dep_name):
                continue
            if dep_name not in graph[package]:
                graph[package].append(dep_name)
            if dep_name not in visited:
                self._dfs_forward(
                    dep_name, dep_ver, depth + DEPTH_STEP, graph, visited
                )

    def build(self, root: str, version: str = "") -> Dict[str, List[str]]:
        """Построить транзитивный граф зависимостей от корневого пакета."""
        if self._is_excluded(root):
            return {}
        graph: Dict[str, List[str]] = {}
        visited: Set[str] = set()
        self._dfs_forward(root, version, START_DEPTH, graph, visited)
        return graph

    def _build_inverted_map(
        self, packages: List[str]
    ) -> Dict[str, List[str]]:
        """Построить инвертированный граф (зависимость -> зависящие)."""
        inverted: Dict[str, List[str]] = {}
        for pkg in packages:
            if self._is_excluded(pkg):
                continue
            deps = self._provider.get_dependencies(pkg)
            for dep in deps:
                if not self._is_excluded(dep):
                    inverted.setdefault(dep, []).append(pkg)
        return inverted

    def _dfs_reverse(
        self,
        node: str,
        depth: int,
        inverted: Dict[str, List[str]],
        visited: Set[str],
        result: List[str],
    ) -> None:
        """Рекурсивно собрать обратные зависимости алгоритмом DFS."""
        visited.add(node)
        if depth >= self._max_depth:
            return
        for parent in inverted.get(node, []):
            if parent not in visited:
                result.append(parent)
                self._dfs_reverse(
                    parent, depth + DEPTH_STEP, inverted, visited, result
                )

    def find_reverse_dependencies(
        self, target: str, all_packages: List[str]
    ) -> List[str]:
        """Найти все пакеты, зависящие от target, с помощью DFS."""
        if self._is_excluded(target):
            return []
        inverted = self._build_inverted_map(all_packages)
        visited: Set[str] = set()
        result: List[str] = []
        self._dfs_reverse(target, START_DEPTH, inverted, visited, result)
        return result
