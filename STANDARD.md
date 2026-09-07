# The Semantic Skill Standard

Version `skills.automacene.org/v1alpha1`

A semantic skill is a prompt written as data. One file holds the sections the
prompt is made of, the inputs it takes, what it returns, and the capabilities it
implements. Something else decides whether that becomes a completion string, a
message array, or whatever comes after those.

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
| `namespace` | required | DNS-1123 label, same rule as `name`. Flat, and replaces the folder a skill used to live in. |
| `labels` | optional | Queryable. Keys take an `automacene.org/` prefix; values are 63 characters at most and hold no slashes or spaces. |
| `annotations` | required | Not queryable, no practical size limit. |

Names are DNS-1123 rather than Nuclio's looser rule. Nuclio accepts uppercase and
underscores, but every name that satisfies DNS-1123 also satisfies Nuclio, so the
strict rule is the intersection and costs nothing but a rename.

Namespaces do not nest. A second dimension of classification belongs in a label.

Two annotations carry weight:

- `automacene.org/description` is prose, used as the record description on export.
- `automacene.org/oasf-name` is the human title for a directory listing, since
  `metadata.name` is an identifier and reads badly as one.

`automacene.org/version` is a label rather than a field, matching how Kubernetes
handles versions, and it is semantic versioning.

### spec.authors

Required, and at least one entry. Each is npm's author string: a name, then an
optional email in angle brackets, then an optional URL in parentheses.

```
Codie Petersen <codie@asteres-technologies.com>
Microsoft Semantic Kernel (https://github.com/microsoft/semantic-kernel)
Jane Doe <jane@example.com> (https://example.com)
Some Working Group
```

Only the name is required. Attribution to a project rather than a person is
ordinary, and such a project has a repository and no address. A format that
demanded an address would be asking authors to invent one.

OASF's `authors` is a string array and nothing validates its contents, so an
entry carrying a URL rather than an address exports unchanged.

### spec.capabilities

What this skill implements, in taxonomy terms. This is not decoration: it is how
a workflow finds the skill when binding late, so it is load-bearing.

`skills` and `domains` hold entries carrying a `name` and, optionally, an `id`.
The base skill definition constrains a reference to `at_least_one: [id, name]`,
so a name alone is a complete citation. Cite an id when the taxonomy has assigned
one; a private node has none and needs none.

Private nodes carry no id on purpose. Numeric ids are AGNTCY's to assign, and
minting your own guarantees a collision the first time they assign the same
number. Prefix a private name with your domain and it cannot be mistaken for
anyone else's.

Nothing here asks a reader to work out whether a citation is public or private.
The id is optional either way, and deciding whether a name resolves needs the
taxonomy, which is a fetch rather than something a single file can settle.

### spec.inputs

Input names, section names and output field names are each unique within a
skill. Two of anything sharing a name is a validation failure, not a rule about
which one wins.

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
| `absent` | optional | Used instead of `text` when the section has nothing to say. |

A section falls back to `absent` when any input its `text` uses came back empty.
Nothing declares that. A section written around `{{$context}}` needs `context`
because it says so, and writing it down a second time gives two places to hold
one fact, which is two places to disagree.

A section wanting some other gate is a section doing two jobs. One that prints an
API name, its results, and a note about them, but should only vanish when the
results are missing, is three things wearing one name. Split it and each part
gates on what it actually says.

`absent` is why any of this matters. A section that simply disappears when its
slot is empty leaves a model unable to tell "nothing was found" from "nothing was
looked for", and that silence is the most common way a skill answers confidently
from nothing.

### Placement is not the skill's business

`kind` says what a section is. It never says where the section goes, and this
standard does not either.

Pinning placement means pinning it for every arrangement a skill can take, which
is a rule per skill, which is no rule at all. A document that named two of them
would be generalizing from whichever skill it happened to be looking at.

So an adapter decides, completely. One targeting a chat API chooses which kinds
become system material and which become the current message; one targeting a
completion concatenates in order; one targeting MCP folds everything into the
roles MCP has. Two conforming adapters may send different prompts from the same
file, and that is the intended arrangement rather than a gap in this document.

### spec.settings

Optional.

| Field | | |
|---|---|---|
| `temperature` | optional | |
| `maxTokens` | optional | Caps what the model writes. |
| `promptTokens` | optional | Caps what the rendered skill costs to send. |

Every value here is the author's suggestion, measured in whatever environment
they wrote the skill in. A caller overrides any of them at call time and needs no
permission from the file. A skill that could pin a temperature would be a skill
that decides how somebody else's model behaves.

`promptTokens` and `maxTokens` are easy to confuse and cap opposite ends. The
first is the size of what you send; the second is the size of what comes back.

There is nothing else. Sampling parameters beyond temperature rarely carry
intent, and a file full of them is a file full of values nobody chose.

A model name and its deployment coordinates are not settings. A skill naming
them is a skill that runs in one place, and model configuration has a
standardized home in an OASF module.

There are no stop sequences. A stop sequence is tied to the template's own
markup, which makes it a property of a completion rather than of a skill, and
`output` covers what it was doing.

Field names are camelCase, matching Kubernetes API convention throughout `spec`.

### There is no status

Kubernetes gives a resource a `status` because a controller reports what is
actually true of a running thing against what `spec` asked for. A prompt template
runs nothing and reconciles nothing, so there is no gap for a status to report.
Taking the envelope without asking what its fourth key is for would leave one
here.

The four values that would go in it have better homes. `createdAt` and
`locators` are read from git when a record is published. `tokens` is computed
from `spec` whenever something asks. `validated` is a CI result and belongs in
CI output.

Storing any of them in the file makes a second copy that goes stale the moment
somebody edits a section, and writing `validated` back would produce a commit on
every CI run.

## Placeholders

`{{$name}}` takes the value of an input. Anything else inside `{{ }}` is left
exactly as written, so an unrecognised placeholder appears in the output rather
than vanishing.

There is no escape, and there will not be one. A skill cannot write `{{$name}}`
literally, which means a skill cannot quote another skill's template. That costs
one real use, and it buys a format where a placeholder always means a
substitution and never means a quoted string a reader has to decide about.

An undeclared placeholder is a validation failure. It still renders unsubstituted
rather than becoming empty, so text arriving from somewhere it should not have
shows up where a person can see it instead of quietly disappearing.

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

- Each declared input is used by at least one section.
- No two inputs, sections or output fields share a name.
- Each `kind` is drawn from the vocabulary, and exactly one section is `input`.
- `metadata.name` and `metadata.namespace` satisfy DNS-1123, and
  `automacene.org/version` is semver.
- Each author reads as npm's author string.
- Every placeholder used names a declared input.
- Each capability citation resolves, against the OASF taxonomy or against a
  `Capability` document in the repository.
- The rendered token count with defaults applied is within `promptTokens`.

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
| `created_at` | Read from git at publish time |
| `skills` | `spec.capabilities.skills` |
| `domains` | `spec.capabilities.domains` |
| `locators` | Read from git at publish time |
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
