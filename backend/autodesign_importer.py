"""Import autodesign demo package fixtures into WonderLens game frontmatter."""

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

try:
    from .game_parser import parse_game_file
except ImportError:
    from game_parser import parse_game_file


class AutodesignImportError(ValueError):
    """Raised when an autodesign package cannot be safely imported."""


@dataclass
class ImportResult:
    """Result of importing one autodesign package."""

    demo_id: str
    status: str
    support_level: str
    asset_readiness: str
    game_path: Path | None
    asset_dir: Path
    unsupported_reasons: list[str] = field(default_factory=list)
    degraded_reasons: list[str] = field(default_factory=list)


_REQUIRED_PACKAGE_FILES = (
    "spec.md",
    "prod.md",
    "tag_block.yaml",
    "recap.template.yaml",
    "dashboard.template.yaml",
)

_CATEGORY_BY_TEMPLATE = {
    "cat1_dialogue": "category_1",
    "cat5_collection": "category_5",
    "cat5_judgment": "category_5",
}
_SOURCE_STRATEGIES = {
    "generated_illustrative",
    "curated_original",
    "redraw_from_verified_data",
    "licensed_reference",
    "approved_internal_reference",
}
_REFERENCE_SOURCE_STRATEGIES = {
    "curated_original",
    "redraw_from_verified_data",
    "licensed_reference",
    "approved_internal_reference",
}
_TRANSFORMATION_POLICIES = {
    "generate_new",
    "crop_resize_only",
    "simplified_redraw",
    "style_preserving_redraw",
    "no_derivative_generation",
}
_REFERENCE_TRANSFORMATION_POLICIES = {
    "crop_resize_only",
    "simplified_redraw",
    "style_preserving_redraw",
    "no_derivative_generation",
}
_REFERENCE_SOURCE_TYPES = {
    "licensed_asset",
    "public_domain_reference",
    "approved_internal_reference",
    "verified_source_url",
}
_RANDOM_REFERENCE_WORDS = ("random", "arbitrary", "made-up", "made up", "hallucinated")


def import_autodesign_package(
    package_dir: Path,
    games_dir: Path,
    activity_assets_dir: Path,
    source_commit: str,
) -> ImportResult:
    """Import a package directory into generated game frontmatter.

    Args:
        package_dir: Directory containing canonical package files plus demo extensions.
        games_dir: Destination directory for generated `backend/games/*.md` files.
        activity_assets_dir: Destination root for browser-visible activity assets.
        source_commit: Pinned upstream autodesign fixture commit.

    Returns:
        Import result including generated paths and support status.

    Raises:
        AutodesignImportError: If required package files are missing or the package
            claims support with unsafe/missing required information.
    """
    package_dir = Path(package_dir)
    _validate_package_files(package_dir)

    tag_block = _load_yaml(package_dir / "tag_block.yaml")
    missing_extensions = [
        name for name in ("demo_support.yaml", "asset_manifest.yaml") if not (package_dir / name).exists()
    ]
    if missing_extensions:
        activity_id = str(tag_block.get("activity_id") or package_dir.name)
        entity_id = str(tag_block.get("source_entity_exemplar") or tag_block.get("entity") or "unbound_entity")
        demo_id = f"{_slug(activity_id)}__{_slug(entity_id)}"
        return ImportResult(
            demo_id=demo_id,
            status="unsupported",
            support_level="not_demo_ready",
            asset_readiness="blocked",
            game_path=None,
            asset_dir=activity_assets_dir / demo_id,
            unsupported_reasons=["Package does not include demo_support.yaml or asset_manifest.yaml."],
        )

    demo_support = _load_yaml(package_dir / "demo_support.yaml")
    asset_manifest = _load_yaml(package_dir / "asset_manifest.yaml")

    support = demo_support.get("demo_support") or {}
    status = str(support.get("status") or "unsupported")
    ui_template = str(support.get("ui_template") or "none")
    binding = _default_entity_binding(support)
    activity_id = str(demo_support.get("activity_id") or asset_manifest.get("activity_id") or tag_block.get("activity_id"))
    entity_id = str(binding.get("entity_id") or asset_manifest.get("entity_id") or tag_block.get("source_entity_exemplar"))
    demo_id = f"{_slug(activity_id)}__{_slug(entity_id)}"
    asset_dir = activity_assets_dir / demo_id

    unsupported_reasons = list(support.get("unsupported_reasons") or [])
    degraded_reasons = list(support.get("degraded_reasons") or [])

    if status == "unsupported" or ui_template == "none":
        return ImportResult(
            demo_id=demo_id,
            status="unsupported",
            support_level=str(support.get("support_level") or "unsupported"),
            asset_readiness="blocked",
            game_path=None,
            asset_dir=asset_dir,
            unsupported_reasons=unsupported_reasons or ["Package is not marked playable in demo_support.yaml."],
            degraded_reasons=degraded_reasons,
        )

    if status not in {"supported", "degraded"}:
        raise AutodesignImportError(f"Unsupported demo status: {status}")
    if ui_template not in _CATEGORY_BY_TEMPLATE:
        raise AutodesignImportError(f"Unsupported demo UI template: {ui_template}")
    if status == "supported" and ui_template == "cat5_judgment":
        raise AutodesignImportError("cat5_judgment packages must be degraded, not supported")

    resolved_manifest, asset_readiness = _resolve_assets(
        package_dir=package_dir,
        activity_assets_dir=activity_assets_dir,
        demo_id=demo_id,
        asset_manifest=asset_manifest,
        status=status,
    )

    game_data = _build_game_frontmatter(
        package_dir=package_dir,
        activity_id=activity_id,
        demo_id=demo_id,
        entity_id=entity_id,
        binding=binding,
        status=status,
        ui_template=ui_template,
        support=support,
        tag_block=tag_block,
        resolved_manifest=resolved_manifest,
        asset_readiness=asset_readiness,
        source_commit=source_commit,
    )

    games_dir.mkdir(parents=True, exist_ok=True)
    game_path = games_dir / f"{demo_id}.md"
    body = _package_body(package_dir)
    game_path.write_text(_dump_frontmatter(game_data) + "\n" + body, encoding="utf-8")
    parse_game_file(game_path)

    return ImportResult(
        demo_id=demo_id,
        status=status,
        support_level=str(support.get("support_level") or status),
        asset_readiness=asset_readiness["status"],
        game_path=game_path,
        asset_dir=asset_dir,
        unsupported_reasons=unsupported_reasons,
        degraded_reasons=degraded_reasons,
    )


def _validate_package_files(package_dir: Path) -> None:
    missing = [name for name in _REQUIRED_PACKAGE_FILES if not (package_dir / name).exists()]
    if missing:
        raise AutodesignImportError(f"Package missing required files: {', '.join(missing)}")


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise AutodesignImportError(f"Expected mapping YAML in {path}")
    return data


def _default_entity_binding(support: dict) -> dict:
    bindings = support.get("entity_bindings") or []
    if not bindings:
        raise AutodesignImportError("demo_support.yaml must declare at least one entity binding")
    for binding in bindings:
        if binding.get("default"):
            return dict(binding)
    return dict(bindings[0])


def _resolve_assets(
    package_dir: Path,
    activity_assets_dir: Path,
    demo_id: str,
    asset_manifest: dict,
    status: str,
) -> tuple[dict, dict]:
    assets = asset_manifest.get("assets") or []
    if not isinstance(assets, list):
        raise AutodesignImportError("asset_manifest.yaml assets must be a list")

    resolved_assets: dict[str, dict] = {}
    required_missing: list[str] = []
    optional_missing: list[str] = []
    asset_dir = activity_assets_dir / demo_id
    asset_dir.mkdir(parents=True, exist_ok=True)

    for asset in assets:
        asset_id = str(asset.get("id") or "")
        if not asset_id:
            raise AutodesignImportError("Asset entry missing id")
        accuracy_mode = str(asset.get("accuracy_mode") or "illustrative")
        requiredness = str(asset.get("requiredness") or "optional")
        _validate_asset_contract_fields(asset)
        variants = asset.get("variants") or []
        if not isinstance(variants, list) or not variants:
            if requiredness == "required":
                required_missing.append(asset_id)
            else:
                optional_missing.append(asset_id)
            continue

        if accuracy_mode == "reference_bound":
            _validate_reference_bound_asset(asset, package_dir)

        resolved_variants = []
        browser_url = ""
        for variant in variants:
            resolved_variant = dict(variant)
            path_value = variant.get("path")
            if not path_value:
                if requiredness == "required":
                    _append_unique(required_missing, asset_id)
                else:
                    _append_unique(optional_missing, asset_id)
                resolved_variant["browser_url"] = ""
                resolved_variants.append(resolved_variant)
                continue

            filename = f"{_slug(asset_id)}__{_slug(str(variant.get('id') or 'asset'))}.png"
            destination = asset_dir / filename
            if path_value:
                source = _safe_package_path(package_dir, str(path_value))
                if not source.exists():
                    if requiredness == "required":
                        _append_unique(required_missing, asset_id)
                    else:
                        _append_unique(optional_missing, asset_id)
                    resolved_variant["browser_url"] = ""
                    resolved_variants.append(resolved_variant)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            resolved_variant["path"] = str(Path("activity-assets") / demo_id / filename)
            resolved_variant["browser_url"] = f"/activity-assets/{demo_id}/{filename}"
            if not browser_url:
                browser_url = resolved_variant["browser_url"]
            resolved_variants.append(resolved_variant)

        resolved_asset = dict(asset)
        resolved_asset["variants"] = resolved_variants
        resolved_asset["browser_url"] = browser_url
        resolved_assets[asset_id] = resolved_asset

    if required_missing and status == "supported":
        raise AutodesignImportError(f"Missing required assets for supported package: {', '.join(required_missing)}")

    readiness = {
        "status": "blocked" if required_missing else "partial" if optional_missing else "ready",
        "required_missing": required_missing,
        "optional_missing": optional_missing,
    }
    resolved_manifest = dict(asset_manifest)
    resolved_manifest["assets"] = resolved_assets
    return resolved_manifest, readiness


def _validate_asset_contract_fields(asset: dict) -> None:
    asset_id = asset.get("id")
    accuracy_mode = str(asset.get("accuracy_mode") or "")
    requiredness = str(asset.get("requiredness") or "")
    source_strategy = str(asset.get("source_strategy") or "")
    transformation_policy = str(asset.get("transformation_policy") or "")

    if source_strategy not in _SOURCE_STRATEGIES:
        raise AutodesignImportError(f"asset '{asset_id}' lacks approved source_strategy")
    if transformation_policy not in _TRANSFORMATION_POLICIES:
        raise AutodesignImportError(f"asset '{asset_id}' lacks approved transformation_policy")
    if accuracy_mode == "illustrative" and requiredness in {"required", "optional"}:
        if source_strategy != "generated_illustrative":
            raise AutodesignImportError(f"illustrative asset '{asset_id}' must use generated_illustrative")
        if transformation_policy != "generate_new":
            raise AutodesignImportError(f"illustrative asset '{asset_id}' must use generate_new")
        if not str(asset.get("prompt_en") or "").strip():
            raise AutodesignImportError(f"illustrative asset '{asset_id}' must declare prompt_en")


def _validate_reference_bound_asset(asset: dict, package_dir: Path) -> None:
    asset_id = asset.get("id")
    source_strategy = str(asset.get("source_strategy") or "")
    transformation_policy = str(asset.get("transformation_policy") or "")
    if source_strategy not in _REFERENCE_SOURCE_STRATEGIES:
        raise AutodesignImportError(f"reference-bound asset '{asset_id}' lacks approved reference source_strategy")
    if transformation_policy not in _REFERENCE_TRANSFORMATION_POLICIES:
        raise AutodesignImportError(f"reference-bound asset '{asset_id}' must not use random generation")

    policy = asset.get("reference_policy") or {}
    sources = asset.get("sources") or []
    if not isinstance(policy, dict) or not policy:
        raise AutodesignImportError(f"reference-bound asset '{asset_id}' lacks reference_policy")

    allowed_sources = {str(source) for source in policy.get("allowed_sources") or []}
    source_required = bool(policy.get("source_required", True))
    verification_required = bool(policy.get("verification_required", True))
    if source_required is not True:
        raise AutodesignImportError(f"reference-bound asset '{asset_id}' must require approved sources")
    if verification_required is not True:
        raise AutodesignImportError(f"reference-bound asset '{asset_id}' must require verification")
    if not allowed_sources or not allowed_sources <= _REFERENCE_SOURCE_TYPES:
        raise AutodesignImportError(f"reference-bound asset '{asset_id}' lacks approved source types")
    if source_required and not sources:
        raise AutodesignImportError(f"reference-bound asset '{asset_id}' lacks approved sources")
    if not isinstance(sources, list):
        raise AutodesignImportError(f"reference-bound asset '{asset_id}' sources must be a list")

    for source in sources:
        if not isinstance(source, dict):
            raise AutodesignImportError(f"reference-bound asset '{asset_id}' has invalid source metadata")

        source_type = str(
            source.get("source_type") or source.get("type") or source.get("kind") or source.get("license") or ""
        )
        if source_type not in allowed_sources:
            raise AutodesignImportError(f"reference-bound asset '{asset_id}' lacks approved source type")

        label = str(source.get("label") or "")
        license_name = str(source.get("license") or "")
        source_location = str(source.get("uri") or source.get("path") or source.get("provenance") or "")
        if not label or not license_name or not source_location:
            raise AutodesignImportError(f"reference-bound asset '{asset_id}' lacks source provenance fields")

        source_path = source.get("path")
        if source_path and not _safe_package_path(package_dir, str(source_path)).exists():
            raise AutodesignImportError(f"reference-bound asset '{asset_id}' source file is missing")

    prompt = str(asset.get("prompt_en") or "").lower()
    if any(word in prompt for word in _RANDOM_REFERENCE_WORDS):
        raise AutodesignImportError(f"reference-bound asset '{asset_id}' must not request random generation")


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _safe_package_path(package_dir: Path, value: str) -> Path:
    path = (package_dir / value).resolve()
    package_root = package_dir.resolve()
    if not path.is_relative_to(package_root):
        raise AutodesignImportError(f"Asset path escapes package directory: {value}")
    return path


def _build_game_frontmatter(
    package_dir: Path,
    activity_id: str,
    demo_id: str,
    entity_id: str,
    binding: dict,
    status: str,
    ui_template: str,
    support: dict,
    tag_block: dict,
    resolved_manifest: dict,
    asset_readiness: dict,
    source_commit: str,
) -> dict:
    base_data = _load_base_game_data(activity_id)
    category = _CATEGORY_BY_TEMPLATE[ui_template]

    if not base_data:
        base_data = _default_game_data(
            activity_id=activity_id,
            entity_id=entity_id,
            binding=binding,
            category=category,
            tag_block=tag_block,
            resolved_manifest=resolved_manifest,
        )

    data = dict(base_data)
    data["activity_type"] = demo_id
    data["entity_name"] = entity_id
    data["category"] = category
    data["template_type"] = "cat5" if category == "category_5" else "cat1"
    data["demo_filename"] = f"{demo_id}.png"
    data["icon_src"] = _asset_url_by_role(resolved_manifest, "entity") or _first_asset_url(resolved_manifest)
    if not data["icon_src"]:
        data["icon_src"] = f"/icons/{entity_id}.png"
    data["display_label"] = str(binding.get("display_label") or data.get("display_label") or entity_id.title())
    data["keywords"] = _dedupe([entity_id, activity_id, demo_id, *(data.get("keywords") or [])])
    data["feature_keywords"] = _dedupe(data.get("feature_keywords") or tag_block.get("attributes") or [])
    data["photo_features"] = _dedupe(data.get("photo_features") or tag_block.get("attributes") or [entity_id])
    data["plain_description"] = data.get("plain_description") or _tag_block_text(tag_block, "activity_signature", "intro")
    data["steps_summary"] = data.get("steps_summary") or _default_steps_summary(category, tag_block)
    data["autodesign"] = {
        "source_activity_id": activity_id,
        "source_commit": source_commit,
        "package_dir": str(package_dir),
    }
    data["entity_binding"] = {
        "entity_id": entity_id,
        "display_label": data["display_label"],
        "source_entity_exemplar": binding.get("source_entity_exemplar", ""),
    }
    data["demo_support"] = {
        "status": status,
        "ui_template": ui_template,
        "support_level": support.get("support_level", status),
        "unsupported_reasons": list(support.get("unsupported_reasons") or []),
        "degraded_reasons": list(support.get("degraded_reasons") or []),
        "requires": dict(support.get("requires") or {}),
        "consumer_notes": dict(support.get("consumer_notes") or {}),
    }
    data["asset_readiness"] = asset_readiness
    data["asset_manifest"] = resolved_manifest

    if category == "category_5":
        _apply_cat5_assets(data, resolved_manifest, tag_block, status)

    return data


def _load_base_game_data(activity_id: str) -> dict:
    games_dir = Path(__file__).parent / "games"
    path = games_dir / f"{activity_id}.md"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    yaml_text = text.split("---", maxsplit=2)[1]
    data = yaml.safe_load(yaml_text) or {}
    if not isinstance(data, dict):
        return {}
    return data


def _default_game_data(
    activity_id: str,
    entity_id: str,
    binding: dict,
    category: str,
    tag_block: dict,
    resolved_manifest: dict,
) -> dict:
    tier = _tag_block_text(tag_block, "tier_range", "primary") or "T1"
    concepts = tag_block.get("key_concepts") or ["Connection"]
    if not isinstance(concepts, list):
        concepts = [str(concepts)]
    role_title = _reward_title(tag_block.get("progression", {}).get("reward_hook", "Wonder Explorer"))
    if category == "category_1":
        creative_slots = {
            "game_mechanic": "storytelling_chain",
            "metaphor": _tag_block_text(tag_block, "activity_signature", "preview_prompt") or f"Explore {entity_id}.",
            "role_title": role_title,
            "round_scenarios": ["first idea", "second idea", "third idea"],
            "escalation_axis": "simple to imaginative",
            "observation_detail": entity_id,
        }
        collection_catalog = None
    else:
        count = 2 if tier == "T0" else 3
        creative_slots = {
            "observation_angle": _supported_observation_angle(
                _tag_block_text(tag_block, "activity_signature", "observation_angle")
            ),
            "collection_criterion": _tag_block_text(tag_block, "activity_signature", "preview_prompt")
            or f"Find things connected to {entity_id}",
            "collection_count": count,
            "mission_metaphor": _tag_block_text(tag_block, "activity_signature", "intro") or f"Explore {entity_id}.",
            "role_title": role_title,
            "synthesis_type": "naming_story",
            "stuck_hint": "Look nearby and choose something that matches the mission.",
            "naming_prompt": "What should we call this find?",
            "detail_question_template": "What do you notice about this find?",
            "sorting_criterion": "",
        }
        collection_catalog = _catalog_from_assets(resolved_manifest)

    data = {
        "activity_type": activity_id,
        "entity_name": entity_id,
        "category": category,
        "display_label": binding.get("display_label") or entity_id.title(),
        "tier": tier,
        "ib_theme": str(tag_block.get("transdisciplinary_theme") or "Who We Are").replace("_", " "),
        "ib_key_concept": str(concepts[0]),
        "concepts_earned": concepts,
        "keywords": [entity_id],
        "feature_keywords": tag_block.get("attributes") or [],
        "photo_features": tag_block.get("attributes") or [entity_id],
        "creative_slots": creative_slots,
        "step_instructions": _default_step_instructions(category, creative_slots, concepts, tier),
        "screen_frames": _default_screen_frames(category, entity_id, creative_slots),
        "celebration_frame": _default_celebration_frame(role_title, concepts),
        "plain_description": _tag_block_text(tag_block, "activity_signature", "intro"),
        "steps_summary": _default_steps_summary(category, tag_block),
    }
    if collection_catalog:
        data["collection_catalog"] = collection_catalog
    return data


def _apply_cat5_assets(data: dict, resolved_manifest: dict, tag_block: dict, status: str) -> None:
    manifest_catalog = _catalog_from_assets(resolved_manifest)
    has_manifest_collection_assets = any(
        asset.get("role") in {"collection_correct", "collection_distractor"}
        for asset in resolved_manifest.get("assets", {}).values()
    )
    catalog = manifest_catalog if has_manifest_collection_assets else data.get("collection_catalog") or manifest_catalog
    correct_assets = _assets_by_role(resolved_manifest, "collection_correct")
    distractor_assets = _assets_by_role(resolved_manifest, "collection_distractor")
    if catalog:
        for item in catalog.get("correct", []):
            asset = correct_assets.get(item.get("id")) or correct_assets.get(item.get("label"))
            if asset and asset.get("browser_url"):
                item["image"] = asset["browser_url"]
        for item in catalog.get("distractors", []):
            asset = distractor_assets.get(item.get("id")) or distractor_assets.get(item.get("label"))
            if asset and asset.get("browser_url"):
                item["image"] = asset["browser_url"]
    data["collection_catalog"] = catalog

    if status == "degraded" and len(catalog.get("distractors", [])) < 2:
        catalog["distractors"].extend(
            [
                {"id": "try_another_choice", "label": "Try another choice", "image": "/icons/plain_leaf.png"},
                {"id": "not_this_time", "label": "Not this time", "image": "/icons/plain_dirt.png"},
            ]
        )

    slots = dict(data["creative_slots"])
    if slots.get("collection_count", 3) > len(catalog.get("correct", [])):
        slots["collection_count"] = max(2, min(3, len(catalog.get("correct", [])) or 2))
    slots["observation_angle"] = _supported_observation_angle(slots.get("observation_angle"))
    slots.setdefault("detail_question_template", "What do you notice about this find?")
    slots.setdefault("sorting_criterion", "")
    data["creative_slots"] = slots
    data["play_rounds"] = slots["collection_count"]

    rounds = data["step_instructions"]["rounds"]
    if len(rounds) < slots["collection_count"]:
        for idx in range(len(rounds) + 1, slots["collection_count"] + 1):
            rounds.append(_round_instruction(idx, slots["collection_criterion"], "curious"))
    elif len(rounds) > slots["collection_count"]:
        data["step_instructions"]["rounds"] = rounds[: slots["collection_count"]]


def _catalog_from_assets(resolved_manifest: dict) -> dict:
    correct = []
    distractors = []
    for asset in resolved_manifest.get("assets", {}).values():
        role = asset.get("role")
        catalog_id = asset.get("collection_catalog_id") or asset.get("id")
        item = {
            "id": catalog_id,
            "label": asset.get("label") or str(catalog_id).replace("_", " ").title(),
            "image": asset.get("browser_url") or "/icons/plain_leaf.png",
        }
        if role == "collection_correct":
            correct.append(item)
        elif role == "collection_distractor":
            distractors.append(item)
    if not correct:
        correct.append({"id": "demo_correct_1", "label": "Match", "image": "/icons/green_leaf.png"})
    while len(distractors) < 2:
        idx = len(distractors) + 1
        distractors.append({"id": f"demo_distractor_{idx}", "label": f"Other {idx}", "image": "/icons/plain_leaf.png"})
    return {"correct": correct, "distractors": distractors}


def _assets_by_role(resolved_manifest: dict, role: str) -> dict[str, dict]:
    result = {}
    for asset in resolved_manifest.get("assets", {}).values():
        if asset.get("role") == role:
            result[str(asset.get("collection_catalog_id") or asset.get("id"))] = asset
            result[str(asset.get("label") or "")] = asset
    return result


def _asset_url_by_role(resolved_manifest: dict, role: str) -> str:
    for asset in resolved_manifest.get("assets", {}).values():
        if asset.get("role") == role and asset.get("browser_url"):
            return str(asset["browser_url"])
    return ""


def _first_asset_url(resolved_manifest: dict) -> str:
    for asset in resolved_manifest.get("assets", {}).values():
        if asset.get("browser_url"):
            return str(asset["browser_url"])
    return ""


def _default_step_instructions(category: str, slots: dict, concepts: list[str], tier: str) -> dict:
    if category == "category_1":
        rounds = [
            _cat1_round_instruction(1, "first idea"),
            _cat1_round_instruction(2, "second idea"),
            _cat1_round_instruction(3, "third idea"),
        ]
        synthesis = None
    else:
        rounds = [
            _round_instruction(1, slots["collection_criterion"], "encouraging"),
            _round_instruction(2, slots["collection_criterion"], "curious"),
            _round_instruction(3, slots["collection_criterion"], "excited"),
        ][: slots["collection_count"]]
        synthesis = {
            "goal": "Invite the child to compare or name the collected finds and make one tiny shared story.",
            "constraint": f"{tier} max 3 sentences, frame as invitation",
            "emotion_tag": "amazed",
        }
    result = {
        "hook": {
            "goal": "Notice the bound entity and ask one imaginative question.",
            "constraint": f"{tier} max 2 sentences, must end with a question",
            "emotion_tag": "excited",
        },
        "transition": {
            "goal": "Introduce the activity mission as a gentle invitation.",
            "constraint": f"{tier} max 3 sentences, end with Would you like to try?",
            "emotion_tag": "playful",
        },
        "rounds": rounds,
        "celebrate": {
            "goal": f"Award the child the title '{slots['role_title']}' and recap the activity.",
            "constraint": f"{tier} max 2 sentences, warm and specific",
            "emotion_tag": "proud",
        },
        "closing": {
            "goal": f"Connect the activity naturally to {', '.join(concepts)}.",
            "constraint": f"{tier} max 2 sentences, warm goodbye",
            "emotion_tag": "warm",
        },
        "early_exit": {
            "goal": "Gentle goodbye that validates the child's participation.",
            "constraint": f"{tier} max 2 sentences, no pressure",
            "emotion_tag": "gentle",
        },
    }
    if synthesis:
        result["synthesis"] = synthesis
    return result


def _round_instruction(number: int, criterion: str, emotion_tag: str) -> dict:
    return {
        "round_number": number,
        "goal": f"Invite collection find {number}: {criterion}",
        "scenario": f"collection find {number}",
        "constraint": "invitational phrasing, ask about the next matching item",
        "emotion_tag": emotion_tag,
        "acceptable_themes": ["find", "notice", "match", "look", "choose"],
        "escalation_note": f"collection round {number}",
    }


def _cat1_round_instruction(number: int, scenario: str) -> dict:
    return {
        "round_number": number,
        "goal": f"Invite the child to add to the {scenario}.",
        "scenario": scenario,
        "constraint": "ask one clear imaginative question",
        "emotion_tag": "curious",
        "acceptable_themes": ["story", "feeling", "idea", "imagine"],
        "escalation_note": f"dialogue round {number}",
    }


def _default_screen_frames(category: str, entity_id: str, slots: dict) -> list[dict]:
    frames = [
        {
            "widget": "photo_display",
            "widget_params": {"description": f"{entity_id} activity hero"},
            "animation": "sparkle_highlight",
            "trigger": "on_enter",
            "sfx_cue": "wonder_chime",
            "widget_label": f"{entity_id.title()}",
            "animation_label": "Sparkle highlight",
        }
    ]
    if category == "category_1":
        for idx in range(1, 4):
            frames.append(
                {
                    "widget": "character_display",
                    "widget_params": {"description": f"Dialogue round {idx}"},
                    "animation": "scene_transition",
                    "trigger": f"on_round_{idx}",
                    "sfx_cue": "scene_woosh",
                    "widget_label": f"Round {idx}",
                    "animation_label": "Scene transition",
                }
            )
    else:
        total = slots["collection_count"] + 1
        for idx in range(1, slots["collection_count"] + 1):
            frames.append(
                {
                    "widget": "progress_tracker",
                    "widget_params": {"filled": idx, "total": total},
                    "animation": "card_slide_in" if idx == 1 else "celebration_burst",
                    "trigger": f"on_round_{idx}",
                    "sfx_cue": "photo_shutter_click",
                    "widget_label": f"Find {idx}",
                    "animation_label": "Collection progress",
                }
            )
    return frames


def _default_celebration_frame(role_title: str, concepts: list[str]) -> dict:
    return {
        "widget": "badge_award",
        "widget_params": {"title": role_title, "concepts": concepts},
        "animation": "badge_reveal",
        "trigger": "on_correct",
        "sfx_cue": "badge_awarded",
        "widget_label": "Badge Earned!",
        "animation_label": "Badge reveal",
    }


def _default_steps_summary(category: str, tag_block: dict) -> list[str]:
    intro = _tag_block_text(tag_block, "activity_signature", "intro")
    if category == "category_1":
        return [intro or "Meet the character.", "Imagine three rounds together.", "Earn a badge."]
    return [intro or "Meet the mission.", "Collect matching finds.", "Share a tiny wrap-up.", "Earn a badge."]


def _package_body(package_dir: Path) -> str:
    prod = package_dir / "prod.md"
    return prod.read_text(encoding="utf-8") if prod.exists() else ""


def _dump_frontmatter(data: dict) -> str:
    return "---\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120) + "---\n"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "item"


def _dedupe(values: list[Any]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        result.append(text)
        seen.add(text)
    return result


def _tag_block_text(tag_block: dict, *keys: str) -> str:
    current: Any = tag_block
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return str(current or "")


def _reward_title(value: str) -> str:
    text = str(value or "Wonder Explorer")
    match = re.search(r"Earned the (.+?)(?: badge)?$", text)
    return match.group(1) if match else text


def _supported_observation_angle(value: Any) -> str:
    text = str(value or "form").lower()
    allowed = {"color", "shape", "texture", "size", "pattern", "function", "habitat", "form", "movement", "smell"}
    return text if text in allowed else "form"
