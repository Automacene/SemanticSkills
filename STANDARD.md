# The Semantic Skill Standard

Version `skills.automacene.org/v1alpha1`

A semantic skill is a prompt written as data. One file holds the sections the
prompt is made of, the inputs it takes, what it returns, and the capabilities it
implements. Something else decides whether that becomes a completion string, a
message array, or whatever comes after those.

## Why the old format is being replaced

The previous format was built for `text-davinci-003`, which took one string and
continued it. That single assumption is the source of everything awkward about
it.

A skill was one opaque blob, so the structure that mattered was visible only to a
person reading the template. Nothing could ask a skill where its context went or
what order its parts came in. `inputs` restated what the template already said,
in a second place that drifted, which is why `Scripts/fix_skill_inputs.py` exists
at all. `default` did two unrelated jobs, holding both a literal value like `USER`
and a paragraph of instructions for when a slot came back empty. Trailing markers
like `<{{$bot}}>` and `stop` sequences existed to make a completion model start
and stop talking. `skill_class` decided whether the `skill` field held a prompt or
Python source, which made one key mean two unrelated things.

Sections fix the first of those and most of the rest follow.

## The document

```yaml
apiVersion: skills.automacene.org/v1alpha1
kind: SemanticSkill

metadata:
  name: deal-summary
  namespace: summarize
  labels:
    automacene.org/version: "1.0.0"
  annotations:
    automacene.org/oasf-name: Commercial Deal Summarization
    automacene.org/description: >
      Condense a commercial agreement into its material terms.

spec:
  authors:
    - Codie Petersen <codie@asteres-technologies.com>

  capabilities:
    skills:
      - name: language_processing/language_generation/summarization
        id: 10302
      - name: automacene.org/deal_summarization
    domains:
      - name: legal_and_compliance/contract_management
        id: 1203

  inputs:
    - name: document
      description: The agreement text to summarize.
      required: true
    - name: company
      description: The counterparty, when already known.
    - name: focus
      description: What the reader cares about most.
      default: payment terms, termination, and liability

  output:
    fields:
      - name: summary
        type: string
        required: true
      - name: counterparty
        type: string
      - name: risks
        type: string
        repeated: true

  sections:
    - name: instructions
      kind: instructions
      text: |
        Summarize the agreement below. Concentrate on {{$focus}}.

    - name: counterparty
      kind: context
      needs: [company]
      text: |
        The counterparty is {{$company}}.
      absent: |
        The counterparty is not given. Identify it from the document, and say so
        if the document does not name one.

    - name: document
      kind: input
      text: "{{$document}}"

  settings:
    temperature: 0.1
    maxTokens: 1500

status:
  createdAt: "2026-09-06T18:04:00Z"
  locators:
    - type: source_code
      urls:
        - https://github.com/Automacene/SemanticSkills/blob/main/summarize/deal-summary.skill
  tokens: 212
  validated: "2026-09-06T18:04:00Z"
```

## The contract, and the implementation

`capabilities`, `inputs` and `output` are the public contract. They are the whole
of what a caller reads, and they are identical across every callable kind, so a
workflow binds to a capability and never learns whether a prompt or a lambda
answered.

`sections` and `settings` are the implementation. Nothing outside the renderer
reads them. Replacing this prompt with a function that implements the same
capability changes nothing upstream.

## Fields

### Envelope

| Field | | |
|---|---|---|
| `apiVersion` | required | `skills.automacene.org/v1alpha1`. Versions the format, not the skill. |
| `kind` | required | `SemanticSkill`. The dispatch key, alongside `NuclioFunction` and `Capability`. |

The envelope is Kubernetes CRD convention, which Nuclio also uses. Conforming to
it means a skill can become a real cluster resource later, validated by
`kubeconform` and distributed by whatever GitOps tooling an organization already
runs, and it means every callable kind reads the same on the outside.

A functional skill is not a kind of ours at all. It is a literal
`apiVersion: nuclio.io/v1beta1, kind: NuclioFunction`, carrying the same
`capabilities`, `inputs` and `output` blocks inside its `spec`. Nuclio's CRD
declares `x-kubernetes-preserve-unknown-fields: true` on both `spec` and
`status`, so those fields are stored intact and ignored by Nuclio's own
controller. `nuctl deploy` and `kubectl apply` take the document as it stands,
with nothing converted.

That is the rule this standard follows wherever it can: adopt the industry
format, add a thin layer to carry what the format has no place for. A semantic
skill needs its own kind only because no industry format describes a
parameterized prompt with declared sections.

### metadata

Kubernetes `ObjectMeta`, verbatim. Only these four keys exist; there is nowhere
to hang a fifth.

| Field | | |
|---|---|---|
| `name` | required | DNS-1123 label: `[a-z0-9-]`, begins with a letter, ends alphanumeric, 63 characters at most. |
| `namespace` | required | Flat. Replaces the folder a skill used to live in. |
| `labels` | optional | Queryable. Keys take an `automacene.org/` prefix; values are 63 characters at most and hold no slashes or spaces. |
| `annotations` | required | Not queryable, no practical size limit. |

Names are DNS-1123 rather than Nuclio's looser rule. Nuclio accepts uppercase and
underscores, but every name that satisfies DNS-1123 also satisfies Nuclio, so the
strict rule is the intersection and costs nothing but a rename.

Namespaces do not nest. A second dimension of classification belongs in a label.

Two annotations carry weight:

- `automacene.org/description` — prose, used as the record description on export.
- `automacene.org/oasf-name` — the human title for a directory listing, since
  `metadata.name` is an identifier and reads badly as one.

`automacene.org/version` is a label rather than a field, matching how Kubernetes
handles versions, and it is semantic versioning.

### spec.authors

Required. `Name <email>`, the form OASF expects, so the export needs no
conversion.

### spec.capabilities

What this skill implements, in taxonomy terms. This is not decoration — it is how
a workflow finds the skill when binding late, so it is load-bearing.

`skills` and `domains` both hold entries of `name` and `id`. A public node cites
both. A private node cites `name` only.

Private nodes carry no id on purpose. Numeric ids are AGNTCY's to assign, and
minting your own guarantees a collision the first time they assign the same
number. The base skill definition constrains a reference to `at_least_one: [id,
name]`, so a name-only citation is valid, and prefixing the name with your domain
makes it unambiguous.

### spec.inputs

| Field | | |
|---|---|---|
| `name` | required | |
| `description` | required | |
| `default` | optional | A value, never instructions. Instructions for an empty slot are a section's `absent`. |
| `required` | optional | Defaults to false. |

### spec.output

Optional. When absent, the skill returns a single implicit `text` field, so a
caller binding one field always works.

| Field | | |
|---|---|---|
| `fields[].name` | required | |
| `fields[].type` | required | `string`, `integer`, `number`, `boolean` |
| `fields[].required` | optional | |
| `fields[].repeated` | optional | A list of that type. |

A list of typed fields rather than a map of names to types, because free-form map
keys have no representation in OpenAPI v3, which is what a CRD validation schema
is. The structured-output retry loop rebuilds its example JSON from the list, so
nothing downstream changes.

### spec.sections

Required, ordered. The list order is the order.

| Field | | |
|---|---|---|
| `name` | required | Unique within the skill. |
| `kind` | required | `instructions`, `examples`, `context`, `history`, `input` |
| `text` | required | The template. |
| `needs` | optional | Inputs that must be non-empty for `text` to be used. |
| `absent` | optional | Used instead of `text` when any of `needs` is empty. |

`kind` says what a section is, never where it goes. An adapter targeting a chat
API turns `history` into real turns and `instructions` into a system message; an
adapter targeting a completion concatenates in order. A skill that is a one-shot
transformation declares two sections and never thinks about any of it.

A section with `needs` and no `absent` is a validation failure. Omitting a
section when its slot is empty leaves a model unable to tell "nothing was found"
from "nothing was looked for", and that silence is the most common way a skill
answers confidently from nothing.

### spec.settings

Optional. Two keys.

| Field | | |
|---|---|---|
| `temperature` | optional | |
| `maxTokens` | optional | |

The old format carried `top_p`, `presence_penalty` and `frequency_penalty` in
every file, and across 53 skills 39 of them set `top_p` to `0.0`, 49 set
`presence_penalty` to zero and 51 set `frequency_penalty` to zero. Those were
converter defaults nobody chose, and `top_p: 0.0` does not mean what the files
that carry it intended. Temperature and token count are the two that vary with
intent, and they are the two that remain.

`model`, `project` and `location` are gone. Deployment coordinates in a prompt
template are why a skill written for one provider could not run on another
without editing the skill. Model configuration has a standardized home in an OASF
module.

`stop` is gone with them. Every occurrence was scaffolding tied to the template's
own markup, and structured output covers what it was doing.

Field names are camelCase, matching Kubernetes API convention throughout `spec`.

### status

Generated, never authored. Anything written here by hand is overwritten.

| Field | | |
|---|---|---|
| `createdAt` | RFC 3339. Becomes the record's `created_at`. |
| `locators` | Generated from git. Becomes the record's `locators`. |
| `tokens` | Rendered size with defaults applied. |
| `validated` | When the checks below last passed. |

## Placeholders

`{{$name}}` takes the value of an input. Anything else inside `{{ }}` is left
exactly as written, so an unrecognised placeholder appears in the output rather
than vanishing.

Values are resolved before sections render. An input with no supplied value falls
back to its `default`.

## Private taxonomy nodes

A capability that does not exist in the public taxonomy is defined in its own
document and grafted onto the public tree.

```yaml
apiVersion: skills.automacene.org/v1alpha1
kind: Capability

metadata:
  name: deal-summarization
  namespace: taxonomy

spec:
  name: automacene.org/deal_summarization
  caption: Deal Summarization
  description: Condense a commercial agreement into its material terms.
  extends: language_processing/language_generation/summarization
```

`extends` points at a public node or at another private one, so a private tree
can be any depth and every branch terminates at something published upstream.
There is no `uid`; see `spec.capabilities` above for why.

Load every `Capability` and every `SemanticSkill` in a repository and you have
the organization's taxonomy and its implementations, with nothing to look up
beyond the public tree the private nodes hang from. No registry, no central
assignment, no request to anyone. A worker who solves something new commits a
`Capability` and an implementation, and the collection describes itself.

## Validation

Every one of these is checkable without running a model, and all of them are
build failures.

- Each name in `needs` is a declared input.
- Each declared input is used by at least one section.
- Each section carrying `needs` also carries `absent`.
- Each `kind` is drawn from the vocabulary, and exactly one section is `input`.
- `metadata.name` satisfies DNS-1123 and `automacene.org/version` is semver.
- Each public capability citation resolves against the OASF taxonomy.
- Each private capability citation resolves against a `Capability` in the repo.
- The rendered token count with defaults applied is within budget.

Golden renders are worth more than all of them together. Check in a fixture input
set and the expected assembled output for each skill, and a pull request that
touches a prompt shows the rendered result before and after rather than a YAML
diff. Prompt changes stop being unreviewable.

## Serving over MCP

The Model Context Protocol has a prompt primitive, and it is the closest live
industry standard to this format. A skill serves over it with no loss on
discovery and a render on retrieval.

`prompts/list` returns a `Prompt`, which maps directly:

| MCP field | Source |
|---|---|
| `name` | `metadata.name` |
| `title` | `metadata.annotations[automacene.org/oasf-name]` |
| `description` | `metadata.annotations[automacene.org/description]` |
| `arguments[].name` | `spec.inputs[].name` |
| `arguments[].description` | `spec.inputs[].description` |
| `arguments[].required` | `spec.inputs[].required` |

`spec.inputs` is a superset of MCP's `arguments`: it adds `default`, which MCP
has no field for. That costs nothing, because defaults are applied by the
renderer before any message is produced, so a client never needs to know they
existed.

`prompts/get` returns `messages`, and that is `spec.sections` rendered. A
`PromptMessage` carries a `role` of `user` or `assistant` and typed content.
There is no system role, so an adapter targeting MCP folds `kind: instructions`
into the leading user message rather than emitting a system message.

The same `sections` list serves a chat API as roles, a completion API as
concatenated text, and MCP as `messages`. That is what declaring sections buys
over holding one blob.

## Publishing to the Agent Directory

An OASF record is generated from a skill; it is never authored. The mapping is
total.

| Record field | Source |
|---|---|
| `name` | `metadata.annotations[automacene.org/oasf-name]` |
| `version` | `metadata.labels[automacene.org/version]` |
| `schema_version` | Constant, supplied by the tooling |
| `description` | `metadata.annotations[automacene.org/description]` |
| `authors` | `spec.authors` |
| `created_at` | `status.createdAt` |
| `skills` | `spec.capabilities.skills` |
| `domains` | `spec.capabilities.domains` |
| `locators` | `status.locators` |
| `annotations` | `metadata.annotations`, plus `namespace` |
| `modules` | Built from `spec.sections` |

A record has no namespace, so `metadata.namespace` travels as an annotation.
Records are content-addressed and discovered by announced capabilities, so there
is nowhere in the model to say where an author filed something.

The prompt travels as a `core/language_model/prompt` module, whose `prompt`
object holds a `name`, a `description` and a `command`. `command` is the rendered
sections. That is lossy by design: a record advertises that the prompt exists and
what it does, and anyone who wants to run it follows `locators` to this file.

OASF is an export target, not a foundation. It models a catalog entry describing
one agent. It has no edges between records, no representation of composition, and
a centrally governed taxonomy. Publishing to it makes work findable, and that
value does not depend on it modeling how anything is built.

## Migrating from the old format

| Old | New |
|---|---|
| `name` | `metadata.name`, lowercased and hyphenated |
| folder | `metadata.namespace`, lowercased |
| `description` | `metadata.annotations[automacene.org/description]` |
| `skill_class` | Gone. `kind` dispatches; functional skills become `kind: NuclioFunction`. |
| `skill` | Decomposed into `spec.sections` |
| `inputs[].default` holding a value | `spec.inputs[].default` |
| `inputs[].default` holding instructions | The owning section's `absent` |
| `output` | `spec.output.fields`, as a typed list |
| `settings.temperature`, `max_tokens` | `spec.settings.temperature`, `maxTokens` |
| `settings.model`, `project`, `location` | Gone |
| `settings.top_p`, penalties, `stop` | Gone |

A skill converts mechanically to one section of `kind: input` holding the whole
blob. That renders identically to the old format and is a valid document, so the
corpus can move in one pass and gain real sections one skill at a time.
