
# SemanticSkills
A collection of semantic skills for AI in the form of prompt templates used to query LLMs.

## Purpose of the Repository
The SemanticSkills repository aims to provide a comprehensive collection of semantic skills that can be used to enhance AI capabilities. These skills cover a wide range of domains and use cases, enabling AI systems to perform specific tasks and generate meaningful outputs based on given inputs.

By maintaining a standardized description format for the skills, the repository ensures consistency and ease of integration into AI systems. The descriptions act as a reference, providing clear documentation of each skill's purpose, inputs, and outputs. This allows developers and researchers to easily incorporate these skills into their projects and leverage the power of AI to accomplish various tasks.

### Prompt Templates and Standardization
In the context of the SemanticSkills repository, a prompt template refers to a predefined structure or format that serves as a guide for querying language models and generating specific outputs. It acts as a blueprint for composing prompts that elicit desired responses from AI models.

The use of prompt templates offers several advantages, including:

- Consistency: By adopting standardized prompt templates, developers and researchers can ensure consistent inputs and outputs across various skills. This consistency simplifies integration and interoperability between different AI systems.

- Efficiency: Prompt templates allow for efficient development and deployment of AI models. By following predefined structures, developers can quickly create prompts that adhere to a consistent format, reducing the time and effort required for implementation.

- Reproducibility: Standardized prompt templates facilitate reproducibility in research and development. By sharing and using consistent prompt structures, it becomes easier to replicate and compare results across different experiments and models.

The SemanticSkills repository aims to contribute to the standardization of prompt template practices. By providing a collection of well-defined skill descriptions and associated prompt templates, we strive to establish a common framework for querying language models and generating meaningful responses.

The goal of standardization is to foster collaboration, knowledge sharing, and community-driven advancements in natural language processing. By adopting standardized prompt templates, we can unlock the full potential of AI models and enable researchers and developers to build upon shared foundations.

## Description Files
The SemanticSkills repository contains a variety of skill descriptions that define the capabilities and inputs/outputs of each skill. These descriptions are stored in separate files, following a standard format.

### Purpose of Skill Description Files
The SemanticSkills repository hosts a diverse collection of skill descriptions with a specific focus on enabling automated planners powered by Language Models (LLMs). These skill descriptions, stored as separate files following a standardized format, play a vital role in increasing the autonomy of agents by facilitating the planning and execution of actions.

The purpose of skill description files within the SemanticSkills repository is two-fold:

**1. Documentation and Understanding**: Skill description files provide comprehensive documentation, outlining the capabilities, inputs, and outputs of each skill. They offer valuable insights into the functionalities provided by the skills, enabling developers and researchers to understand and utilize them effectively. This documentation aspect serves as a reference for comprehending the skills available in the repository and their potential contributions to automated planning systems.

**2. Empowering Automated Planners**: The skill description files are a critical resource for empowering automated planners, specifically those powered by LLMs. These planners leverage the information contained within the description files to comprehend the relationships between inputs and outputs of different skills. By understanding the dependencies and connections, the automated planners can orchestrate a series of actions, making use of the outputs from one skill as inputs to subsequent skills. This process enhances the autonomy of agents and enables them to plan and execute complex sequences of actions based on the interconnected skills available in the SemanticSkills repository.

Through the utilization of skill description files, the SemanticSkills repository aims to enable the development and deployment of automated planners powered by LLMs. These planners leverage the standardized format of the description files to understand the capabilities of skills and orchestrate them effectively, increasing the autonomy and decision-making capabilities of AI agents.

By providing comprehensive documentation and empowering automated planners, the SemanticSkills repository serves as a valuable resource to drive innovation and advancements in autonomous AI systems, allowing them to plan and execute actions based on interconnected skills and the power of LLMs.

### Description Format
Each description file follows the format outlined below:

```toml
[description]
skill_name = "Skill Name"
skill_description = "A brief description of the skill."
output_name = "Output Name"
output_description = "A description of the output/result generated by the skill."
output_uses = "A description of how the output can be used."
output_type = "The type of output (e.g., text/string, JSON, etc.)"
[[description.arguments]]
argument_name = "Argument Name"
argument_identifier = "Argument Identifier"
argument_description = "A description of the argument."
argument_sources = "A description of where the argument can be sourced from."
argument_type = "The expected type of the argument." 
```

### Example Description File
Here's an example of a description file for a skill:

```toml
[description]
skill_name = "FunSkill.Excuses"
skill_description = "The skill is the ability to generate creative and humorous excuses for a given event."
output_name = "excuse"
output_description = "A creative and humorous excuse for the given event."
output_uses = "Can be used to provide a humorous response to a given event."
output_type = "text/string"
[[description.arguments]]
argument_name = "input"
argument_identifier = "{{$input}}"
argument_description = "The event for which an excuse is needed."
argument_sources = "Provided by the user or extracted from conversation/dialogue."
argument_type = "text/string"
```

### Future Development
The SemanticSkills repository is an evolving project, with continuous additions of new skills and potential future contributions from AI systems. The aim is to expand the repository's offerings to encompass a broad range of domains, allowing AI models to provide more comprehensive and sophisticated responses to user queries and prompts.

Additionally, the repository welcomes community contributions and feedback. Developers and researchers are encouraged to submit their own skills, further enriching the collection and promoting collaboration in the AI community.

We hope that the SemanticSkills repository serves as a valuable resource for enhancing the capabilities of AI models and fostering innovation in natural language processing and understanding.

## Acknowledgements
### Contributions
We would like to acknowledge Microsoft for their invaluable contributions to this project. The majority of the skills included in the SemanticSkills repository are derived from Microsoft's Semantic Kernel Samples. These samples have provided a solid foundation and served as a source of inspiration for the development of this repository.

By leveraging the insights gained from the efforts of Semantic Kernel, we have been able to research standardization and best practices relating to prompt templating at a much faster rate than we could have without such a database of skills.

### Future Collaboration
We welcome ongoing opensource efforts from Microsoft and other contributors to further enrich the SemanticSkills repository. Together, we can continue to explore the potential of language models and advance the field of natural language processing.

We extend our sincere gratitude to Microsoft and all the contributors for their dedication and efforts in advancing the state of the art in AI and language understanding.


-- **With Love, Various AI and The Automacene Team**
