from fastapi import HTTPException

from app.utils.constants import ALLOWED_SCORING_MODES, ALLOWED_STATUSES, WEIGHTED_MODE


def validate_status(status: str) -> None:
    if status.upper() not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Allowed values: {sorted(ALLOWED_STATUSES)}",
        )


def validate_scoring_mode(scoring_mode: str) -> None:
    if scoring_mode.upper() not in ALLOWED_SCORING_MODES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid scoring_mode. Allowed values: {sorted(ALLOWED_SCORING_MODES)}",
        )


def validate_pager_structure(scoring_mode, pillars, require_all_weighted_pillars: bool = True) -> None:
    validate_scoring_mode(scoring_mode)

    if len(pillars) > 5:
        raise HTTPException(status_code=422, detail="A pager can contain a maximum of 5 pillars.")

    pillar_numbers = [pillar.pillar_number for pillar in pillars]
    if len(pillar_numbers) != len(set(pillar_numbers)):
        raise HTTPException(status_code=422, detail="pillar_number must be unique.")

    for pillar in pillars:
        if len(pillar.initiatives) > 3:
            raise HTTPException(
                status_code=422,
                detail=f"Pillar {pillar.pillar_number} can contain a maximum of 3 initiatives.",
            )
        initiative_numbers = [item.initiative_number for item in pillar.initiatives]
        if len(initiative_numbers) != len(set(initiative_numbers)):
            raise HTTPException(
                status_code=422,
                detail=f"initiative_number must be unique in pillar {pillar.pillar_number}.",
            )

    if scoring_mode.upper() == WEIGHTED_MODE:
        if require_all_weighted_pillars and len(pillars) != 5:
            raise HTTPException(
                status_code=422,
                detail="Weighted mode requires all 5 pillars.",
            )
        total_weight = sum((pillar.pillar_weight or 0) for pillar in pillars)
        if abs(total_weight - 100) > 0.001:
            raise HTTPException(
                status_code=422,
                detail=f"Weighted pillar total must equal 100. Current total: {total_weight}.",
            )
