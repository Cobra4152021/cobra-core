"""Investigation skill registry — registration without engine code changes."""

from __future__ import annotations

from cobra_core.isf.errors import IsfError, IsfErrorCode
from cobra_core.isf.manifest import SkillManifest


class SkillRegistry:
    """In-memory registry of skill manifests."""

    def __init__(self) -> None:
        self._skills: dict[str, SkillManifest] = {}

    def register(self, manifest: SkillManifest) -> None:
        if not isinstance(manifest, SkillManifest):
            raise IsfError(IsfErrorCode.MANIFEST_INVALID, "expected SkillManifest")
        # Validate via dataclass post_init already; store by id.
        self._skills[manifest.id] = manifest

    def get(self, skill_id: str) -> SkillManifest:
        key = (skill_id or "").strip()
        try:
            return self._skills[key]
        except KeyError as exc:
            raise IsfError(
                IsfErrorCode.SKILL_NOT_FOUND,
                f"skill not registered: {skill_id!r}",
            ) from exc

    def list_skills(self) -> list[SkillManifest]:
        return [self._skills[k] for k in sorted(self._skills)]

    def ids(self) -> list[str]:
        return sorted(self._skills)

    def __contains__(self, skill_id: object) -> bool:
        return isinstance(skill_id, str) and skill_id in self._skills

    def __len__(self) -> int:
        return len(self._skills)


# Process-wide default registry populated by builtin registration.
SKILL_REGISTRY = SkillRegistry()
