import json
from sqlmodel import Session, select
from app.models import Model3D, SmartCollection


def _field_value(model: Model3D, field: str):
    if field == "tag":
        return [t.name for t in model.tags]
    if field == "filename":
        return model.filename
    if field == "extension":
        return model.extension
    if field == "designer":
        return model.designer or ""
    if field == "license":
        return model.license or ""
    if field == "description":
        return model.ai_description or ""
    return None


def _condition_matches(model: Model3D, cond: dict) -> bool:
    field = cond.get("field")
    op = cond.get("op", "contains")
    value = str(cond.get("value", "")).lower()
    actual = _field_value(model, field)

    if isinstance(actual, list):
        haystack = [str(a).lower() for a in actual]
        if op == "contains":
            return value in haystack
        if op == "not_contains":
            return value not in haystack
        return False

    actual = str(actual or "").lower()
    if op == "contains":
        return value in actual
    if op == "not_contains":
        return value not in actual
    if op == "equals":
        return actual == value
    if op == "starts_with":
        return actual.startswith(value)
    return False


def matches_rule(model: Model3D, rule: dict) -> bool:
    conditions = rule.get("conditions", [])
    if not conditions:
        return False
    match_mode = rule.get("match", "all")
    results = [_condition_matches(model, c) for c in conditions]
    return all(results) if match_mode == "all" else any(results)


def resolve_smart_collection(session: Session, smart: SmartCollection) -> list[Model3D]:
    rule = json.loads(smart.rule_json)
    all_models = session.exec(select(Model3D)).all()
    return [m for m in all_models if matches_rule(m, rule)]
