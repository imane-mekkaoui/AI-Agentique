"""Filtrage des droits d'accès AVANT génération."""

from __future__ import annotations

from maintidoc.models import AccessLevel, UserRole

ROLE_LEVELS: dict[UserRole, frozenset[AccessLevel]] = {
    UserRole.OPERATEUR: frozenset({AccessLevel.PUBLIC}),
    UserRole.TECHNICIEN: frozenset({AccessLevel.PUBLIC, AccessLevel.TECHNICIEN}),
    UserRole.SUPERVISEUR: frozenset(
        {AccessLevel.PUBLIC, AccessLevel.TECHNICIEN, AccessLevel.SUPERVISEUR}
    ),
}


def allowed_levels(role: UserRole) -> frozenset[AccessLevel]:
    """Niveaux de documents visibles pour un rôle."""
    return ROLE_LEVELS[role]


def is_allowed(role: UserRole, level: AccessLevel | str) -> bool:
    """Indique si le rôle peut voir ce niveau d'accès."""
    parsed = level if isinstance(level, AccessLevel) else AccessLevel(level)
    return parsed in allowed_levels(role)
