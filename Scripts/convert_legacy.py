"""Convert the legacy .skill corpus to skills.automacene.org/v1alpha1.

Does the mechanical half only. Everything needing judgement is written as the
literal TODO-CONVERT so it is greppable, and every file gets the label
automacene.org/conversion: mechanical until a human has been through it.
"""
import re
import sys
import pathlib
import yaml

ROOT = pathlib.Path("/mnt/data/Git/Automacene/SemanticSkills")
FILLER = "TODO-CONVERT"

NAMESPACES = {
    "CalendarSkill": "calendar",
    "Chat": "chat",
    "ChildrensBookSkill": "childrens-book",
    "ClassificationSkill": "classification",
    "CodingSkill": "coding",
    "FunSkill": "fun",
    "IntentDetectionSkill": "intent-detection",
    "MiscSkill": "misc",
    "QASkill": "qa",
    "Standard": "standard",
    "SummarizeSkill": "summarize",
    "WriterSkill": "writer",
}

# Placeholders that were never inputs: the old script scraped calls as if they were.
NOT_INPUTS = re.compile(r"^\{\{|^(time|year|month|day|date)$", re.I)


class Block(str):
    pass


class Quoted(str):
    pass


class Dumper(yaml.Dumper):
    """Indents sequences under their key, which PyYAML does not do by default."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def block(text):
    """Mark a string so the dumper writes it as a literal block.

    Trailing whitespace on any line forces the emitter back to a quoted scalar, so
    it is stripped per line. Nothing else about the text changes.
    """
    text = text.replace("\r\n", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    return Block("\n".join(lines).rstrip() + "\n")


Dumper.add_representer(
    Block, lambda d, v: d.represent_scalar("tag:yaml.org,2002:str", str(v), style="|")
)
Dumper.add_representer(
    Quoted, lambda d, v: d.represent_scalar("tag:yaml.org,2002:str", str(v), style='"')
)


def represent_str(dumper, value):
    """Long prose reads as a block rather than folding mid-sentence."""
    if len(value) > 100 and "\n" not in value:
        return dumper.represent_scalar("tag:yaml.org,2002:str", value + "\n", style=">")
    return dumper.represent_scalar("tag:yaml.org,2002:str", value)


Dumper.add_representer(str, represent_str)


def kebab(name):
    """A DNS-1123 label: lowercase, camel boundaries become hyphens."""
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", str(name))
    name = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    if not name or not name[0].isalpha():
        name = "skill-" + name
    return name[:63].rstrip("-")


def preclean(text):
    """Make the file parseable without changing what it says.

    Two files declare inputs named `{{date`, `{{year` and the like, which opens a
    YAML flow mapping and takes the parse down. Quoting the value keeps the
    mistake visible rather than guessing at a repair.
    """
    text = text.replace("\r\n", "\n")
    return re.sub(r"^(\s*-?\s*name:\s*)(\{\{[^\n\"']*)$", r'\1"\2"', text, flags=re.M)


def convert_inputs(raw):
    """Old inputs to new, dropping `type` and anything that was never an input."""
    out, dropped = [], []

    for item in raw or []:
        if not isinstance(item, dict) or item.get("name") is None:
            continue

        name = str(item["name"]).strip()
        if NOT_INPUTS.match(name):
            dropped.append(name)
            continue

        entry = {"name": name, "description": str(item.get("description") or FILLER).strip()}

        default = item.get("default")
        if default not in (None, ""):
            entry["default"] = default

        if str(item.get("required")).lower() == "true":
            entry["required"] = True

        out.append(entry)

    return out, dropped


def convert_settings(raw):
    """Only the two that carry intent. Everything else was a converter default."""
    settings = {}
    raw = raw or {}

    if raw.get("temperature") is not None:
        settings["temperature"] = raw["temperature"]
    if raw.get("max_tokens") is not None:
        settings["maxTokens"] = raw["max_tokens"]

    return settings


def convert(path, namespace):
    old = yaml.safe_load(preclean(path.read_text(encoding="utf-8")))
    if not isinstance(old, dict):
        raise ValueError("not a mapping")

    name = kebab(old.get("name") or path.stem)
    inputs, dropped = convert_inputs(old.get("inputs"))

    annotations = {
        "automacene.org/oasf-name": FILLER,
        "automacene.org/description": str(old.get("description") or FILLER).strip(),
    }

    labels = {
        "automacene.org/version": Quoted("1.0.0"),
        # Removed by hand once the sections and capabilities are real.
        "automacene.org/conversion": "mechanical",
    }

    spec = {
        "authors": [FILLER],
        "capabilities": {"skills": [{"name": FILLER}]},
    }

    if inputs:
        spec["inputs"] = inputs

    if isinstance(old.get("output"), dict):
        spec["output"] = {
            "fields": [
                {"name": key, "type": FILLER}
                for key in old["output"]
            ]
        }

    # The whole template as one section. Renders identically until split by hand.
    spec["sections"] = [
        {"name": "prompt", "kind": "input", "text": block(old.get("skill") or "")}
    ]

    settings = convert_settings(old.get("settings"))
    if settings:
        spec["settings"] = settings

    doc = {
        "apiVersion": "skills.automacene.org/v1alpha1",
        "kind": "SemanticSkill",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": labels,
            "annotations": annotations,
        },
        "spec": spec,
    }

    return name, doc, dropped


def main():
    apply = "--apply" in sys.argv
    report = []

    for source in sorted((ROOT / "Skills").rglob("*.skill")):
        folder = source.parent.name
        namespace = NAMESPACES.get(folder)
        if namespace is None:
            report.append((str(source), "unmapped folder", []))
            continue

        try:
            name, doc, dropped = convert(source, namespace)
        except Exception as error:
            report.append((str(source), f"FAILED {error}", []))
            continue

        target = ROOT / "Skills" / namespace / f"{name}.skill"
        text = yaml.dump(doc, Dumper=Dumper, sort_keys=False, allow_unicode=True,
                         width=100, indent=2)

        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")

        report.append((f"{folder}/{source.stem}", f"-> {namespace}/{name}.skill", dropped))

    for old, new, dropped in report:
        note = f"   dropped non-inputs: {', '.join(dropped)}" if dropped else ""
        print(f"{old:<44} {new}{note}")

    print(f"\n{len(report)} files")


if __name__ == "__main__":
    main()
