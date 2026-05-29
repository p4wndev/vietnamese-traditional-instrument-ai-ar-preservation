"""
Ontology service.

Wraps OWL ontology queries via owlready2 and returns structured dicts
ready for the API response.
"""

import logging
import random
from typing import Any, Dict, List, Tuple

from app.services.ml import INSTRUMENT_DISPLAY_NAMES

logger = logging.getLogger(__name__)

# Maps OWL property python_name → human-readable Vietnamese label
PROPERTY_LABELS: Dict[str, str] = {
    "có_cách_chơi_là": "Có cách chơi là ",
    "có_cấu_tạo_gồm": "Có cấu tạo gồm ",
    "có_nguồn_gốc": "Có nguồn gốc ",
    "có_số_dây_là": "Có số dây là ",
    "có_tác_giả_là": "Có tác giả là ",
    "có_tên_là": "Có tên là ",
    "có_URL_là": "Có URL là ",
    "xuất_hiện_ở_Việt_Nam_vào": "Xuất hiện ở Việt Nam vào",
    "được_biểu_diễn_bởi": "Được biểu diễn bởi",
    "được_sử_dụng_trong": "Được sử dụng trong",
    "là_nhạc_cụ_đặc_trưng_ở": "Là nhạc cụ đặc trưng ở",
    "được_dùng_rộng_rãi_trong_dân_tộc": "Được sử dụng rộng rãi trong danh tộc",
}

# Set-valued properties – values are joined with ", "
SET_PROPERTIES = {
    "được_sử_dụng_trong",
    "có_cấu_tạo_gồm",
    "được_dùng_rộng_rãi_trong_dân_tộc",
    "là_nhạc_cụ_đặc_trưng_ở",
}


def get_instrument_ontology(class_name: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Query ontology for *class_name* (e.g. ``"dan_bau"``).

    Returns
    -------
    info   : flat dict of property → value
    videos : list of dicts, one per related video (up to 3 random)
    """
    from app.core.lifespan import state

    onto = state.get("ontology")
    if onto is None:
        raise RuntimeError("Ontology is not loaded")

    display_name = INSTRUMENT_DISPLAY_NAMES.get(class_name)
    if display_name is None:
        raise ValueError(f"Unknown instrument class: {class_name!r}")

    instrument_individual = onto[display_name]
    if instrument_individual is None:
        raise ValueError(f"Individual '{display_name}' not found in ontology")

    info: Dict[str, Any] = {}
    video_names: List[str] = []

    for prop in instrument_individual.get_properties():
        prop_name: str = prop.python_name
        label = PROPERTY_LABELS.get(prop_name)
        if label is None:
            continue

        values = list(prop[instrument_individual])

        if prop_name in SET_PROPERTIES:
            if prop_name == "được_sử_dụng_trong":
                arts = set()
                for val in values:
                    video_names.append(val.name)
                    parent = onto.get_parents_of(val)
                    if parent:
                        arts.add(parent[0].name)
                info[label] = ", ".join(arts).replace("_", " ")
            else:
                name_set = {v.name for v in values}
                info[label] = ", ".join(name_set).replace("_", " ")
        else:
            for val in values:
                try:
                    info[label] = val.name
                except AttributeError:
                    info[label] = val

    # Pick up to 3 random related videos
    sample = random.sample(video_names, min(3, len(video_names)))
    videos: List[Dict[str, Any]] = []
    for vid_name in sample:
        vid_individual = onto[vid_name]
        if vid_individual is None:
            continue
        vid_dict: Dict[str, Any] = {}
        for prop in vid_individual.get_properties():
            if prop.python_name == "được_sử_dụng_trong":
                continue
            label = PROPERTY_LABELS.get(prop.python_name)
            if label is None:
                continue
            for val in prop[vid_individual]:
                vid_dict[label] = val
        videos.append(vid_dict)

    return info, videos
