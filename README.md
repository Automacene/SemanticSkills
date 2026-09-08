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
Skills/chat/vector.skill
Skills/summarize/notegen.skill
Skills/writer/twosentencesummary.skill
```

`Skills/` is where the Python loader fetches from, so it stays even though the namespace is
in the document. The directory under it must match `metadata.namespace` and the filename must match `metadata.name`.
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
    - Microsoft Semantic Kernel (https://github.com/microsoft/semantic-kernel)
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
`default`, section kinds come from the vocabulary, names and namespaces are DNS-1123, versions
are semver, and no `TODO-CONVERT` placeholder survives.

## Scripts

`Scripts/validate.py` checks the corpus against the standard.

`Scripts/convert_legacy.py` is the migration that produced this tree from the pre-standard
format. Kept as a record of how the corpus moved, not as something to run again.

`Scripts/skill-designer.html` composes a skill from fields rather than by hand. Open it in a
browser; it needs no server and no build. It shows three views of what you are writing: the
document, the prompt with its placeholders left in, and the prompt with values substituted.
The second and third are the point, since a section's `default` text only proves itself when
you empty a slot and watch the fallback appear.

Each input carries a test value alongside its `default`. The test value never reaches the
document; it is what the filled prompt uses, which keeps "what a caller gets when they supply
nothing" separate from "what I am trying right now".

## Where these came from

The corpus began as Microsoft's Semantic Kernel samples, imported in May 2023, and grew from
there. Forty-five of the 53 skills are theirs; the rest were written here. It has been
converted twice: from the three-file layout of `config.json`, `description.toml` and
`skprompt.txt` into a single `.skill` file, and then from that into the standard described in
`STANDARD.md`.

## The format this replaced

The previous format was built for `text-davinci-003`, which took one string and continued it.
That single assumption is behind everything awkward about it.

A skill was one opaque blob, so the structure that mattered was visible only to a person
reading the template. Nothing could ask a skill where its context went or what order its parts
came in. `inputs` restated what the template already said, in a second place that drifted,
which is why the repository used to carry a `fix_skill_inputs.py` whose whole job was
repairing that. `default` did two unrelated jobs, holding both a literal value like `USER` and
a paragraph of instructions for when a slot came back empty. Trailing markers like
`<{{$bot}}>` and `stop` sequences existed to make a completion model start and stop talking.
`skill_class` decided whether the `skill` field held a prompt or Python source, which made one
key mean two unrelated things.

Two files would not parse at all. `chat/gpt` and `coding/emailsearch` declared inputs named
`{{date` and `{{year`, because the repair script had scraped function placeholders such as
`{{time.Date}}` as if they were variables, and `{{` opens a flow mapping in YAML.

## What the conversion did

| Old | New |
|---|---|
| `name` | `metadata.name`, lowercased and hyphenated |
| folder | `metadata.namespace`, lowercased |
| `description` | `metadata.annotations[automacene.org/description]` |
| `skill_class` | Gone. `kind` dispatches; functional skills become `kind: NuclioFunction`. |
| `skill` | Decomposed into `spec.sections` |
| `inputs[].default` holding a value | `spec.inputs[].default` |
| `inputs[].default` holding instructions | The owning section's `default` |
| `inputs[].type` | Gone. Every one in the corpus was `text`. |
| `output` | `spec.output.fields`, as a typed list |
| `settings.temperature`, `max_tokens` | `spec.settings.temperature`, `maxTokens` |
| `settings.model`, `project`, `location` | Gone |
| `settings.top_p`, penalties, `stop` | Gone |

The sampling parameters went because they carried no intent. Every one of the 53 files set all
five, and 39 set `top_p` to `0.0`, 49 set `presence_penalty` to zero, 51 set
`frequency_penalty` to zero. Those were converter defaults nobody chose, and `top_p: 0.0` does
not mean what the files carrying it intended. Temperature and token count were the two that
varied, so they are the two that remain.

`Scripts/convert_legacy.py` is the script that did the mechanical half, kept as a record. It
converts a skill into a single section of `kind: input` holding the whole blob, which renders
identically to the old format and is a valid document. Real sections were written by hand
afterwards.
