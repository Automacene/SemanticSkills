# SemanticSkills

Prompt templates written as data, so a program can read them, fill them, check them, and
publish them.

A skill file holds the sections a prompt is made of, the inputs it takes, what it returns, and
the capabilities it implements. Nothing in it decides whether the result becomes a completion
string, a chat message array, or an MCP `prompts/get` response. That is the caller's business.

[STANDARD.md](STANDARD.md) is the specification. Read it before adding a skill.

## Layout

Skills live in a directory named for their namespace, one file each.

```
chat/vector.skill
summarize/notegen.skill
writer/twosentencesummary.skill
```

The directory must match `metadata.namespace` and the filename must match `metadata.name`.
Both are DNS-1123 labels, so lowercase letters, digits and hyphens, starting with a letter.

| Namespace | | Namespace | |
|---|---|---|---|
| `calendar` | 1 | `intent-detection` | 1 |
| `chat` | 6 | `misc` | 3 |
| `childrens-book` | 2 | `qa` | 6 |
| `classification` | 2 | `standard` | 2 |
| `coding` | 8 | `summarize` | 3 |
| `fun` | 3 | `writer` | 16 |

`standard/` holds two worked examples, one single-input and one multi-input, kept as
references for anyone writing a new skill.

## A skill

```yaml
apiVersion: skills.automacene.org/v1alpha1
kind: SemanticSkill
metadata:
  name: twosentencesummary
  namespace: writer
  labels:
    automacene.org/version: "1.0.0"
  annotations:
    automacene.org/oasf-name: Two Sentence Summary
    automacene.org/description: Summarize text in two sentences or less.
spec:
  authors:
    - Microsoft Semantic Kernel <https://github.com/microsoft/semantic-kernel>
    - Codie Petersen <codie@asteres-technologies.com>
  capabilities:
    skills:
      - name: language_processing/language_generation/summarization
        id: 10302
  inputs:
    - name: input
      description: The text to summarize.
      required: true
  sections:
    - name: instructions
      kind: instructions
      text: Summarize the following text in two sentences or less.
    - name: input
      kind: input
      text: |-
        [BEGIN TEXT]
        {{$input}}
        [END TEXT]
  settings:
    temperature: 0.0
    maxTokens: 100
```

`capabilities`, `inputs` and `output` are the public contract, identical across every callable
kind, so a caller binds to a capability without knowing a prompt answered rather than a
function. `sections` and `settings` are the implementation and nothing outside the renderer
reads them.

## Checking

```
python3 Scripts/validate.py
```

Exits non-zero if anything fails, so it works as a build step. It checks that every `needs`
names a declared input, every declared input is used, every section with `needs` carries an
`absent`, section kinds come from the vocabulary, names and namespaces are DNS-1123, versions
are semver, and no `TODO-CONVERT` placeholder survives.

## Scripts

`Scripts/validate.py` checks the corpus against the standard.

`Scripts/convert_legacy.py` is the migration that produced this tree from the pre-standard
format. Kept as a record of how the corpus moved, not as something to run again.

## Where these came from

The corpus began as Microsoft's Semantic Kernel samples and grew from there. It has been
converted twice: from the three-file layout of `config.json`, `description.toml` and
`skprompt.txt` into a single `.skill` file, and then from that into the standard described
here. `STANDARD.md` has a migration table covering the second move.
