# SemanticSkills

A comprehensive repository of standardized semantic skills for AI, designed for prompt engineering, LLM integration, and automated planning.

## Overview

SemanticSkills provides a large, organized collection of prompt templates and skill descriptions for use with language models (LLMs). Each skill is defined by its purpose, inputs, outputs, and a prompt template, enabling consistent and efficient integration into AI systems and planners.

## Features

- **Standardized Skill Format:** All skills follow a clear, documented format for easy parsing and integration.
- **Automated Conversion:** Scripts are provided to convert legacy three-file skills (`config.json`, `description.toml`, `skprompt.txt`) into a unified `.skill` format, preserving folder structure and metadata.
- **Input Correction:** Additional scripts ensure that input variable names in `.skill` files match the exact spelling and capitalization used in prompt templates, guaranteeing reliability for automated planners and LLMs.
- **Domain Coverage:** Skills span a wide range of domains, including chat, planning, summarization, coding, writing, and more.
- **Ready for Automation:** The repository is designed for use in agentic workflows, automated planners, and any system that needs to chain or orchestrate LLM-powered skills.

## Skill Format

Each skill is described in a `.skill` file using a YAML-like format:

```yaml
name: SkillName
description: "A brief description of the skill."
skill_class: semantic
skill: |
  ...prompt template with {{$InputVars}}...
inputs:
  - name: InputVar
    type: text
    description: "Description of the input."
    default: ""
    required: True
settings:
    model: "text-davinci-003"
    max_tokens: 150
    temperature: 0.9
    stop:
      - "Human:"
      - "AI:"
```

## Conversion & Correction Workflow

1. **Convert legacy skills:**
   - Use `Scripts/convert_to_skill_format.py` to convert folders containing `config.json`, `description.toml`, and `skprompt.txt` into `.skill` files, preserving the original folder structure.
2. **Move existing .skill files:**
   - The converter also moves any `.skill` files found in the input tree to the correct output location.
3. **Correct input variable names:**
   - Use `Scripts/fix_skill_vars_from_prompt.py` to scan `.skill` files and update input names to match the exact spelling/capitalization of variables in the prompt template.

## Example Skill Description

```yaml
name: FunSkill.Excuses
description: "Generates creative and humorous excuses for a given event."
skill_class: semantic
skill: |
  {{$input}} needs an excuse.
inputs:
  - name: input
    type: text
    description: "The event for which an excuse is needed."
    default: ""
    required: True
settings:
    model: "text-davinci-003"
    max_tokens: 50
    temperature: 0.8
```

## Contribution & Community

We welcome contributions of new skills, improvements to conversion scripts, and feedback on standardization. Please submit pull requests or open issues to help expand and refine the repository.

## Acknowledgements

Special thanks to Microsoft for their Semantic Kernel Samples, which inspired much of the skill structure and content. The Automacene Team and contributors continue to advance prompt engineering and agentic AI workflows through open collaboration.

---
**With Love, Various AI and The Automacene Team**
