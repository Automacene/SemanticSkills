#!/usr/bin/env python
"""
Script to correct input variable names in .skill files by extracting {{$var}} from the skill prompt and updating the inputs section to match their exact spelling/capitalization.
"""
import os
import re
import argparse

def extract_vars_from_prompt(skill_content):
    """Extract all {{$var}} from the skill: | section."""
    skill_section = re.search(r'skill:\s*\|\n((?:\s{2,}.*\n)+)', skill_content)
    if not skill_section:
        return []
    prompt = skill_section.group(1)
    # Find all {{$var}}
    vars_found = re.findall(r'\{\{\$(.*?)\}\}', prompt)
    # Remove duplicates, preserve order
    seen = set()
    result = []
    for v in vars_found:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result

def fix_skill_file(skill_path):
    """Update input names in .skill file to match vars in prompt."""
    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()
    vars_in_prompt = extract_vars_from_prompt(content)
    if not vars_in_prompt:
        print(f"No vars found in prompt for {skill_path}")
        return
    # Replace input names in order
    def repl(match):
        idx = repl.counter
        if idx < len(vars_in_prompt):
            name = vars_in_prompt[idx]
        else:
            name = match.group(1)  # fallback
        repl.counter += 1
        return f"  - name: {name}\n"
    repl.counter = 0
    new_content = re.sub(r"  - name: (\w+)\n", repl, content)
    with open(skill_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Fixed: {skill_path}")

def main():
    parser = argparse.ArgumentParser(description="Fix input variable names in .skill files using vars from skill prompt.")
    parser.add_argument("--skills", required=True, help="Path to directory containing .skill files.")
    args = parser.parse_args()
    skills_dir = os.path.abspath(args.skills)
    for root, dirs, files in os.walk(skills_dir):
        for file in files:
            if file.endswith('.skill'):
                skill_path = os.path.join(root, file)
                fix_skill_file(skill_path)

if __name__ == "__main__":
    main()
