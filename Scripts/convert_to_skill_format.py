#!/usr/bin/env python
"""
Script to convert skills from the three-file format (config.json, description.toml, skprompt.txt)
to the .skill format, organizing them in a new directory structure.
"""
import os
import json
import toml
import argparse
import shutil
from pathlib import Path

def read_file(file_path):
    """Read file content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def has_skill_files(directory):
    """Check if directory contains the three required files for a skill."""
    return (os.path.isfile(os.path.join(directory, 'config.json')) and
            os.path.isfile(os.path.join(directory, 'description.toml')) and
            os.path.isfile(os.path.join(directory, 'skprompt.txt')))

def get_category_from_path(skill_path, base_path):
    """Extract the category name from the skill path."""
    rel_path = os.path.relpath(skill_path, base_path)
    parts = rel_path.split(os.sep)
    if len(parts) > 0:
        return parts[0]
    return "Uncategorized"

def convert_skill(directory, output_dir, base_dir):
    """Convert a skill directory to .skill format."""
    print(f"Converting: {directory}")
    
    # Read files
    config_path = os.path.join(directory, 'config.json')
    description_path = os.path.join(directory, 'description.toml')
    skprompt_path = os.path.join(directory, 'skprompt.txt')
    
    try:
        config = json.loads(read_file(config_path))
        description = toml.loads(read_file(description_path))
        skprompt = read_file(skprompt_path)
        
        if not all([config, description, skprompt]):
            print(f"Skipping {directory}: Could not read all files.")
            return False
            
        # Extract skill name and category
        skill_dir = os.path.basename(directory)
        skill_name = skill_dir.lower()
        skill_category = get_category_from_path(directory, base_dir)
        
        # Create category directory in output folder
        category_dir = os.path.join(output_dir, skill_category)
        os.makedirs(category_dir, exist_ok=True)
        
        # Get skill description
        if 'description' in config:
            skill_description = config['description']
        elif 'skill_description' in description.get('description', {}):
            skill_description = description['description']['skill_description']
        else:
            skill_description = f"Skill for {skill_name}"
        
        # Create .skill file content
        skill_content = f"name: {skill_name}\n"
        skill_content += f"description: \"{skill_description}\"\n"
        skill_content += "skill_class: semantic\n"
        skill_content += "skill: |\n"
        
        # Add skprompt content with proper indentation
        # Keep original format as required
        skprompt_lines = skprompt.splitlines()
        for line in skprompt_lines:
            skill_content += f"  {line}\n"
        
        # Convert arguments
        skill_content += "inputs:\n"
        if 'description' in description and 'arguments' in description['description']:
            for arg in description['description']['arguments']:
                # Get argument name without {{ $ }} if present
                arg_name = arg['argument_identifier'].replace('{{$', '').replace('}}', '').lower()
                skill_content += f"  - name: {arg_name}\n"
                skill_content += f"    type: text\n"
                skill_content += f"    description: \"{arg['argument_description']}\"\n"
                skill_content += f"    default: \"\"\n"
                skill_content += f"    required: True\n"
        
        # Add settings
        skill_content += "settings:\n"
        if 'default_backends' in config and len(config['default_backends']) > 0:
            model = config['default_backends'][0]
            skill_content += f"    model: \"{model}\"\n"
        
        if 'completion' in config:
            completion = config['completion']
            if 'max_tokens' in completion:
                skill_content += f"    max_tokens: {completion['max_tokens']}\n"
            if 'temperature' in completion:
                skill_content += f"    temperature: {completion['temperature']}\n"
            if 'top_p' in completion:
                skill_content += f"    top_p: {completion['top_p']}\n"
            if 'presence_penalty' in completion:
                skill_content += f"    presence_penalty: {completion['presence_penalty']}\n"
            if 'frequency_penalty' in completion:
                skill_content += f"    frequency_penalty: {completion['frequency_penalty']}\n"
            if 'stop_sequences' in completion and len(completion['stop_sequences']) > 0:
                skill_content += f"    stop: \"{completion['stop_sequences'][0]}\"\n"
        
        # Write skill file to output directory under its category
        skill_filename = os.path.join(category_dir, f"{skill_name}.skill")
        
        with open(skill_filename, 'w', encoding='utf-8') as skill_file:
            skill_file.write(skill_content)
            
        print(f"Created: {skill_filename}")
        return True
        
    except Exception as e:
        print(f"Error converting {directory}: {e}")
        return False

def search_directories(base_dir, output_dir):
    """Recursively search directories for skills to convert."""
    converted_count = 0
    skipped_count = 0
    
    for root, dirs, files in os.walk(base_dir):
        if has_skill_files(root):
            success = convert_skill(root, output_dir, base_dir)
            if success:
                converted_count += 1
            else:
                skipped_count += 1
    
    return converted_count, skipped_count

def main():
    parser = argparse.ArgumentParser(description="Convert skills to .skill format")
    parser.add_argument("directory", nargs="?", default="../Skills",
                        help="Base directory to search for skills (default: ../Skills)")
    parser.add_argument("--output", default="../ConvertedSkills",
                        help="Output directory for .skill files (default: ../ConvertedSkills)")
    args = parser.parse_args()
    
    # Get absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(script_dir, args.directory))
    output_dir = os.path.abspath(os.path.join(script_dir, args.output))
    
    print(f"Searching for skills in: {base_dir}")
    print(f"Output directory: {output_dir}")
    
    if not os.path.isdir(base_dir):
        print(f"Error: {base_dir} is not a valid directory")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    converted, skipped = search_directories(base_dir, output_dir)
    print(f"\nConversion complete!")
    print(f"Skills converted: {converted}")
    print(f"Skills skipped: {skipped}")
    print(f"All skills were saved to: {output_dir}")

if __name__ == "__main__":
    main()
