from typing import List
from fastapi import HTTPException


MAX_PILLARS = 5
MAX_INITIATIVES_PER_PILLAR = 3
MAX_IMAGES_PER_INITIATIVE = 3


def validate_image_urls(images: List[str]) -> None:
    """Validate image count."""
    if images and len(images) > MAX_IMAGES_PER_INITIATIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_IMAGES_PER_INITIATIVE} images allowed per initiative.",
        )


validate_images = validate_image_urls


def validate_pillar_count(count: int) -> None:
    """Validate pillar count against maximum."""
    if count > MAX_PILLARS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_PILLARS} pillars allowed per pager.",
        )


def validate_initiative_count(count: int, pillar_number: int) -> None:
    """Validate initiative count against maximum per pillar."""
    if count > MAX_INITIATIVES_PER_PILLAR:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Maximum {MAX_INITIATIVES_PER_PILLAR} initiatives allowed "
                f"per pillar (pillar {pillar_number})."
            ),
        )


def validate_weighted_total(pillars: list) -> None:
    """Validate that weighted pillar totals sum to 100."""
    total = sum(p.pillar_weight or 0 for p in pillars)
    if total != 100:
        raise HTTPException(
            status_code=400,
            detail=f"Weighted pillar total must equal 100. Current total: {total}.",
        )
