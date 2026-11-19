"""HTTP-клиент для получения зависимостей пакетов из реестра npm."""

import json
import re
from typing import Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

REQUEST_TIMEOUT = 15
SEMVER_PATTERN = re.compile(r"(\d+)\.(\d+)\.(\d+)")
ZERO_VERSION = (0, 0, 0)
LATEST_ALIASES = ("", "latest", "*")


def _version_key(version: str) -> Tuple[int, int, int]:
    """Преобразовать строку версии в числовой кортеж для сравнения."""
    match = SEMVER_PATTERN.search(version)
    if not match:
        return ZERO_VERSION
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _find_min_compatible(versions: Dict[str, dict], spec: str) -> Optional[str]:
    """Найти минимальную стабильную версию, не меньшую указанной в spec."""
    match = SEMVER_PATTERN.search(spec)
    if not match:
        return None
    target = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    candidates = [
        ver for ver in versions
        if "-" not in ver and _version_key(ver) >= target
    ]
    return min(candidates, key=_version_key) if candidates else None


class NpmRepository:
    """Загружает и кэширует метаданные пакетов из реестра npm."""

    def __init__(self, base_url: str) -> None:
        """Инициализировать клиент базовым URL реестра."""
        self._base_url = base_url.rstrip("/")
        self._cache: Dict[str, dict] = {}

    def _fetch_metadata(self, package: str) -> dict:
        """Скачать и закэшировать JSON-метаданные пакета из реестра."""
        if package in self._cache:
            return self._cache[package]
        encoded = quote(package, safe="")
        url = f"{self._base_url}/{encoded}"
        request = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as err:
            raise RuntimeError(
                f"Ошибка HTTP {err.code} для пакета '{package}'."
            ) from err
        except URLError as err:
            raise RuntimeError(
                f"Ошибка сети при загрузке '{package}': {err.reason}"
            ) from err
        self._cache[package] = data
        return data

    def _resolve_version(self, metadata: dict, spec: str) -> str:
        """Сопоставить точную версию или semver-спецификатор с доступной."""
        versions = metadata.get("versions", {})
        if not versions:
            raise RuntimeError("В метаданных пакета отсутствуют версии.")
        if spec in versions:
            return spec
        latest = metadata.get("dist-tags", {}).get("latest", "")
        if spec in LATEST_ALIASES and latest in versions:
            return latest
        compatible = _find_min_compatible(versions, spec)
        if compatible:
            return compatible
        return latest if latest in versions else max(versions, key=_version_key)

    def get_dependencies(
        self, package: str, version: str = ""
    ) -> Dict[str, str]:
        """Вернуть прямые зависимости для заданной версии пакета."""
        metadata = self._fetch_metadata(package)
        resolved = self._resolve_version(metadata, version)
        ver_data = metadata["versions"].get(resolved)
        if ver_data is None:
            raise RuntimeError(
                f"Версия '{version}' не найдена для пакета '{package}'."
            )
        return dict(ver_data.get("dependencies", {}))