import os

def get_skill_name_from_directory(directory):
    """
    Get the skill name from the directory.
    Counting from the end, find the folder that says "Skills" and then add all the folders after that.
    This is the skill name.
    """
    directory_parts = os.path.normpath(directory).split(os.sep)
    for i, part in enumerate(directory_parts):
        if part == "Skills":
            directory_parts = directory_parts[i+1:]
            break
    
    name = ""
    for part in directory_parts:
        name += f"{part}."
    name = name[:-1]
    return name

print(get_skill_name_from_directory("D:/Git/AsteresAI/SemanticSkills/Skills/Standard/SingleInput"))