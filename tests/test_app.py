"""Модульные тесты валидации CLI, DFS, обратных зависимостей и Mermaid."""

import unittest
from pathlib import Path

from src.cli import format_config, parse_args
from src.graph import DependencyGraphBuilder
from src.test_repo import TestRepository
from src.visualizer import sanitize_node_id, to_mermaid

TESTS_DIR = Path(__file__).parent
BASIC_REPO = str(TESTS_DIR / "sample_basic.txt")
CYCLE_REPO = str(TESTS_DIR / "sample_cycle.txt")


class TestCli(unittest.TestCase):
    """Тесты разбора и валидации параметров CLI."""

    def test_valid_real_mode_args(self) -> None:
        """Корректные аргументы реального режима успешно разбираются."""
        cfg = parse_args([
            "-p", "axios", "-r", "https://registry.npmjs.org",
            "-v", "1.7.7", "-d", "2", "-f", "test"
        ])
        self.assertEqual(cfg.package, "axios")
        self.assertIn("package: axios", format_config(cfg))

    def test_invalid_url_raises(self) -> None:
        """Некорректный URL репозитория вызывает ValueError."""
        with self.assertRaises(ValueError):
            parse_args(["-p", "axios", "-r", "ftp://bad", "-v", "1.0.0"])

    def test_missing_version_in_real_mode_raises(self) -> None:
        """Отсутствие версии в реальном режиме вызывает ValueError."""
        with self.assertRaises(ValueError):
            parse_args(["-p", "axios", "-r", "https://registry.npmjs.org"])

    def test_negative_depth_raises(self) -> None:
        """Отрицательная глубина анализа вызывает ValueError."""
        with self.assertRaises(ValueError):
            parse_args(["-p", "A", "-r", BASIC_REPO, "-t", "-d", "-1"])

    def test_missing_test_file_raises(self) -> None:
        """Отсутствующий файл тестового репозитория вызывает ValueError."""
        with self.assertRaises(ValueError):
            parse_args(["-p", "A", "-r", "no_such_file.txt", "-t"])


class TestGraphAndVisualizer(unittest.TestCase):
    """Тесты рекурсивного DFS, фильтрации, циклов, реверса и Mermaid."""

    def test_basic_dfs_with_depth_limit(self) -> None:
        """Обход DFS соблюдает ограничение максимальной глубины."""
        repo = TestRepository(BASIC_REPO)
        builder = DependencyGraphBuilder(repo, max_depth=1)
        graph = builder.build("A")
        self.assertEqual(graph["A"], ["B", "C"])
        self.assertEqual(graph["B"], [])

    def test_filter_substring(self) -> None:
        """Пакеты, содержащие подстроку фильтра, исключаются из графа."""
        repo = TestRepository(BASIC_REPO)
        builder = DependencyGraphBuilder(repo, max_depth=5, filter_substr="E")
        graph = builder.build("A")
        self.assertNotIn("E", graph)
        self.assertNotIn("E", graph["B"])

    def test_cyclic_dependencies(self) -> None:
        """Циклические зависимости обрабатываются без зацикливания."""
        repo = TestRepository(CYCLE_REPO)
        builder = DependencyGraphBuilder(repo, max_depth=10)
        graph = builder.build("A")
        self.assertEqual(graph["C"], ["A", "D"])

    def test_reverse_dependencies(self) -> None:
        """Обратные зависимости корректно находятся рекурсивным DFS."""
        repo = TestRepository(BASIC_REPO)
        builder = DependencyGraphBuilder(repo, max_depth=5)
        revs = builder.find_reverse_dependencies("F", repo.get_all_packages())
        self.assertEqual(set(revs), {"C", "E", "B", "A"})

    def test_mermaid_output(self) -> None:
        """Генератор Mermaid корректно формирует узлы и направленные рёбра."""
        self.assertEqual(sanitize_node_id("@babel/core"), "pkg__babel_core")
        diagram = to_mermaid({"A": ["B"], "B": []}, "A")
        self.assertIn("graph TD", diagram)
        self.assertIn("pkg_A --> pkg_B", diagram)


if __name__ == "__main__":
    unittest.main()
