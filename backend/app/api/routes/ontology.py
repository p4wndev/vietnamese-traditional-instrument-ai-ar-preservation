import logging

from fastapi import APIRouter, HTTPException, Path, status

from app.schemas.schemas import OntologyInfoOut
from app.services.ml import INSTRUMENT_DISPLAY_NAMES
from app.services.ontology import get_instrument_ontology

logger = logging.getLogger(__name__)
router = APIRouter()

_VALID_CLASSES = list(INSTRUMENT_DISPLAY_NAMES.keys())


@router.get("/{class_name}", response_model=OntologyInfoOut)
async def ontology_info(
    class_name: str = Path(
        ...,
        description=f"Instrument class name. Valid values: {', '.join(_VALID_CLASSES)}",
        example="dan_tranh",
    )
):
    """
    Return ontology-enriched information and related video metadata for a
    specific Vietnamese instrument class.
    """
    try:
        info, videos = get_instrument_ontology(class_name)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Ontology query failed for class=%s", class_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ontology error: {exc}",
        )

    return OntologyInfoOut(ontology_info=info, videos=videos)
