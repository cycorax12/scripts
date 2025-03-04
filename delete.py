import re
import sys

def modify_jenkinsfile(input_file, output_file):
    """
    Restructure a Jenkinsfile by taking the existing 'Build container image' and 
    'Build ECS deployment image' stages and wrapping them inside a new 'Build Stage' 
    in a parallel block.
    
    Args:
        input_file (str): Path to the original Jenkinsfile
        output_file (str): Path where the modified Jenkinsfile will be saved
    """
    # Read the original Jenkinsfile
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Find the stages block
    stages_pattern = r"(stages\s*\{)\s*([\s\S]*?)(\s*\})"
    stages_match = re.search(stages_pattern, content, re.DOTALL)
    
    if not stages_match:
        print("Error: Could not find stages block in the Jenkinsfile")
        sys.exit(1)
    
    stages_start = stages_match.group(1)  # "stages {"
    stages_content = stages_match.group(2)  # content between brackets
    stages_end = stages_match.group(3)  # "}"
    
    # Find the Build container image stage
    container_stage_pattern = r"(stage\s*\(\s*['\"]Build container image['\"][\s\S]*?\{[\s\S]*?\})"
    container_match = re.search(container_stage_pattern, stages_content, re.DOTALL)
    
    # Find the Build ECS deployment image stage
    ecs_stage_pattern = r"(stage\s*\(\s*['\"]Build ECS deployment image['\"][\s\S]*?\{[\s\S]*?\})"
    ecs_match = re.search(ecs_stage_pattern, stages_content, re.DOTALL)
    
    if not container_match or not ecs_match:
        print("Error: Could not find both required stages in the Jenkinsfile")
        sys.exit(1)
    
    # Get the full stage blocks
    container_stage = container_match.group(1).strip()
    ecs_stage = ecs_match.group(1).strip()
    
    # Remove these stages from the original content
    new_stages_content = stages_content
    new_stages_content = new_stages_content.replace(container_stage, "")
    new_stages_content = new_stages_content.replace(ecs_stage, "")
    
    # Clean up any consecutive empty lines or whitespace
    new_stages_content = re.sub(r'\n\s*\n', '\n\n', new_stages_content)
    
    # Create the new Build Stage with parallel stages
    build_stage = f"""
        stage('Build Stage') {{
            steps {{
                script {{
                    parallel (
                        "Build container image": {{
                            {container_stage}
                        }},
                        "Build ECS deployment image": {{
                            {ecs_stage}
                        }}
                    )
                }}
            }}
        }}
"""
    
    # Add the new Build Stage to the stages content
    new_stages_content = new_stages_content.strip() + "\n" + build_stage
    
    # Replace the stages section in the original content
    modified_content = content.replace(
        stages_match.group(0),
        stages_start + "\n" + new_stages_content + stages_end
    )
    
    # Write the modified content to the output file
    with open(output_file, 'w') as f:
        f.write(modified_content)
    
    print(f"Successfully modified Jenkinsfile. The result is saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python jenkins_modifier.py <input_jenkinsfile> <output_jenkinsfile>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    modify_jenkinsfile(input_file, output_file)