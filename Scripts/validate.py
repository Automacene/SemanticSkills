"""Check every skill against the standard.

Reports rather than throwing, because a corpus is more useful checked in one pass
than one exception at a time. Exits non-zero when anything failed, so it works as
a build step.

    python3 Scripts/validate.py [--quiet]
"""
import re
import sys
import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent

API_VERSION = "skills.automacene.org/v1alpha1"
SECTION_KINDS = {"instructions", "examples", "context", "history", "input"}
OUTPUT_TYPES = {"string", "integer", "number", "boolean"}

DNS_LABEL = re.compile(r"^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
VARIABLE = re.compile(r"\{\{\s*\$([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")

FILLER = "TODO-CONVERT"


def variables_in(text):
    return set(VARIABLE.findall(str(text or "")))


def check(path):
    """Everything wrong with one skill, as a list of sentences."""
    problems = []

    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as error:
        return [f"will not parse: {error}"]

    if not isinstance(doc, dict):
        return ["is not a mapping"]

    if doc.get("apiVersion") != API_VERSION:
        problems.append(f"apiVersion is {doc.get('apiVersion')!r}, expected {API_VERSION!r}")
    if doc.get("kind") != "SemanticSkill":
        problems.append(f"kind is {doc.get('kind')!r}, expected 'SemanticSkill'")

    meta = doc.get("metadata") or {}
    spec = doc.get("spec") or {}

    name = meta.get("name")
    if not name or not DNS_LABEL.match(str(name)):
        problems.append(f"metadata.name {name!r} is not a DNS-1123 label")
    if name and path.stem != name:
        problems.append(f"filename {path.stem!r} does not match metadata.name {name!r}")

    namespace = meta.get("namespace")
    if not namespace or not DNS_LABEL.match(str(namespace)):
        problems.append(f"metadata.namespace {namespace!r} is not a DNS-1123 label")
    if namespace and path.parent.name != namespace:
        problems.append(f"directory {path.parent.name!r} does not match namespace {namespace!r}")

    labels = meta.get("labels") or {}
    version = labels.get("automacene.org/version")
    if not version or not SEMVER.match(str(version)):
        problems.append(f"automacene.org/version {version!r} is not semver")

    annotations = meta.get("annotations") or {}
    for key in ("automacene.org/oasf-name", "automacene.org/description"):
        if not annotations.get(key):
            problems.append(f"missing annotation {key}")

    if not spec.get("authors"):
        problems.append("spec.authors is empty")

    capabilities = (spec.get("capabilities") or {}).get("skills") or []
    if not capabilities:
        problems.append("spec.capabilities.skills is empty")
    for entry in capabilities:
        if not isinstance(entry, dict) or not entry.get("name"):
            problems.append(f"capability {entry!r} has no name")

    declared = {}
    for item in spec.get("inputs") or []:
        if not isinstance(item, dict) or not item.get("name"):
            problems.append(f"input {item!r} has no name")
            continue
        declared[item["name"]] = item
        if not item.get("description"):
            problems.append(f"input {item['name']!r} has no description")

    sections = spec.get("sections") or []
    if not sections:
        problems.append("spec.sections is empty")

    used = set()
    inputs_seen = 0

    for section in sections:
        if not isinstance(section, dict):
            problems.append(f"section {section!r} is not a mapping")
            continue

        label = section.get("name") or "<unnamed>"

        if not section.get("name"):
            problems.append("a section has no name")

        kind = section.get("kind")
        if kind not in SECTION_KINDS:
            problems.append(f"section {label!r} has kind {kind!r}, not one of {sorted(SECTION_KINDS)}")
        if kind == "input":
            inputs_seen += 1

        if not section.get("text"):
            problems.append(f"section {label!r} has no text")

        used |= variables_in(section.get("text"))
        used |= variables_in(section.get("absent"))

        needs = section.get("needs") or []
        for need in needs:
            if need not in declared:
                problems.append(f"section {label!r} needs {need!r}, which is not a declared input")
        if needs and not section.get("absent"):
            problems.append(f"section {label!r} has needs but no absent")

    if inputs_seen != 1:
        problems.append(f"{inputs_seen} sections of kind 'input', expected exactly 1")

    for variable in sorted(used - set(declared)):
        problems.append(f"uses {{{{${variable}}}}} but does not declare it")
    for unused in sorted(set(declared) - used):
        problems.append(f"declares {unused!r} but no section uses it")

    output = spec.get("output") or {}
    for field in output.get("fields") or []:
        if not isinstance(field, dict) or not field.get("name"):
            problems.append(f"output field {field!r} has no name")
            continue
        if field.get("type") not in OUTPUT_TYPES:
            problems.append(
                f"output field {field['name']!r} has type {field.get('type')!r}, "
                f"not one of {sorted(OUTPUT_TYPES)}"
            )

    fillers = str(doc).count(FILLER)
    if fillers:
        problems.append(f"{fillers} unfilled {FILLER} placeholder{'s' if fillers > 1 else ''}")

    if labels.get("automacene.org/conversion") == "mechanical":
        problems.append("still marked conversion: mechanical")

    return problems


def main():
    quiet = "--quiet" in sys.argv
    skills = sorted(p for p in ROOT.glob("*/*.skill") if p.parts[-2] != "Scripts")

    failed = 0
    total = 0

    for path in skills:
        problems = check(path)
        total += len(problems)
        if not problems:
            continue
        failed += 1
        if not quiet:
            print(f"\n{path.relative_to(ROOT)}")
            for problem in problems:
                print(f"  {problem}")

    clean = len(skills) - failed
    print(f"\n{clean}/{len(skills)} skills clean, {total} problems")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
