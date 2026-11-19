"""Генератор текстового представления графа на языке диаграмм Mermaid."""

import re
from typing import Dict, List, Set

INVALID_ID_CHARS = re.compile(r"[^A-Za-z0-9_]")


def sanitize_node_id(name: str) -> str:
    """Преобразовать имя пакета в корректный идентификатор узла Mermaid."""
    cleaned = INVALID_ID_CHARS.sub("_", name)
    return f"pkg_{cleaned}"


def to_mermaid(graph: Dict[str, List[str]], root: str) -> str:
    """Сформировать описание графа зависимостей на языке диаграмм Mermaid."""
    lines: List[str] = ["graph TD"]
    if not graph:
        return "\n".join(lines)
    declared: Set[str] = set()
    has_edges = False
    for src, targets in graph.items():
        src_id = sanitize_node_id(src)
        if src_id not in declared:
            lines.append(f'    {src_id}["{src}"]')
            declared.add(src_id)
        for dst in targets:
            dst_id = sanitize_node_id(dst)
            if dst_id not in declared:
                lines.append(f'    {dst_id}["{dst}"]')
                declared.add(dst_id)
            lines.append(f"    {src_id} --> {dst_id}")
            has_edges = True
    if not has_edges and root in graph:
        root_id = sanitize_node_id(root)
        if root_id not in declared:
            lines.append(f'    {root_id}["{root}"]')
    return "\n".join(lines)
