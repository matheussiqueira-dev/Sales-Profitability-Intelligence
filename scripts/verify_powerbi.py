"""Validate PBIR JSON against official versioned Microsoft schemas; not a DAX engine."""

import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from jsonschema.validators import validator_for
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "artifacts/powerbi-schemas"
COMPATIBILITY = {
    "report/3.3.0/schema.json": "report/3.1.0/schema.json",
    "visualContainer/2.13.0/schema.json": "visualContainer/2.3.0/schema.json",
    "pagesMetadata/1.1.0/schema.json": "pagesMetadata/1.0.0/schema.json",
}


def retrieve(uri):
    prefix = "https://developer.microsoft.com/json-schemas/"
    if not uri.startswith(prefix):
        raise ValueError("Only official Microsoft schema references are allowed")
    CACHE.mkdir(parents=True, exist_ok=True)
    file = CACHE / (hashlib.sha256(uri.encode()).hexdigest() + ".json")
    if not file.exists():
        url = uri.replace(prefix, "https://raw.githubusercontent.com/microsoft/json-schemas/main/")
        with urllib.request.urlopen(url, timeout=30) as response:
            file.write_bytes(response.read())
    return Resource.from_contents(
        json.loads(file.read_text(encoding="utf-8")), default_specification=DRAFT7
    )


def verify():
    registry = Registry(retrieve=retrieve)
    count = 0
    errors = []
    compatibility_checks = []
    for file in (ROOT / "powerbi/project").rglob("*.json"):
        if ".pbi" in file.parts:
            continue
        value = json.loads(file.read_text(encoding="utf-8"))
        uri = value.get("$schema")
        if uri:
            try:
                resource = retrieve(uri)
            except urllib.error.HTTPError as exc:
                replacement = next(
                    (
                        uri.replace(old, new)
                        for old, new in COMPATIBILITY.items()
                        if uri.endswith(old)
                    ),
                    None,
                )
                if exc.code != 404 or replacement is None:
                    raise
                compatibility_checks.append(
                    {
                        "file": str(file.relative_to(ROOT)),
                        "desktop_schema": uri,
                        "public_compatibility_schema": replacement,
                    }
                )
                value["$schema"] = replacement
                resource = retrieve(replacement)
            validator = validator_for(resource.contents)(resource.contents, registry=registry)
            for error in validator.iter_errors(value):
                errors.append(f"{file.relative_to(ROOT)}:{list(error.path)}:{error.message}")
            count += 1
    result = {
        "json_files_validated": count,
        "errors": errors,
        "passed": not errors,
        "desktop_dax_validation": False,
        "compatibility_checks": compatibility_checks,
    }
    (ROOT / "artifacts/powerbi-json-validation.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    return not errors


if __name__ == "__main__":
    sys.exit(0 if verify() else 1)
