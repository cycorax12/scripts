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
    
    # Print the content for debugging
    print("Original Jenkinsfile content:")
    print("-" * 40)
    print(content)
    print("-" * 40)
    
    # Find the stages block
    stages_pattern = r"(stages\s*\{)\s*([\s\S]*?)(\s*\})"
    stages_match = re.search(stages_pattern, content, re.DOTALL)
    
    if not stages_match:
        print("Error: Could not find stages block in the Jenkinsfile")
        sys.exit(1)
    
    stages_start = stages_match.group(1)  # "stages {"
    stages_content = stages_match.group(2)  # content between brackets
    stages_end = stages_match.group(3)  # "}"
    
    # More flexible regex pattern for finding stages
    container_stage_pattern = r"(stage\s*\(\s*['\"]Build\s*container\s*image['\"][\s\S]*?(?:^[ \t]*\}))"
    ecs_stage_pattern = r"(stage\s*\(\s*['\"]Build\s*ECS\s*deployment\s*image['\"][\s\S]*?(?:^[ \t]*\}))"
    
    # Search for stages with multiline and DOTALL flags
    container_matches = list(re.finditer(container_stage_pattern, stages_content, re.DOTALL | re.MULTILINE))
    ecs_matches = list(re.finditer(ecs_stage_pattern, stages_content, re.DOTALL | re.MULTILINE))
    
    # Debug output
    print(f"Found {len(container_matches)} container stage matches")
    print(f"Found {len(ecs_matches)} ECS stage matches")
    
    if not container_matches or not ecs_matches:
        # Try alternate pattern as a fallback
        print("Using alternate pattern for stage detection...")
        
        # Try to find any stage that contains the keywords
        container_stage_pattern = r"(stage\s*\([^\)]*container[^\)]*\)[\s\S]*?(?:^[ \t]*\}))"
        ecs_stage_pattern = r"(stage\s*\([^\)]*ECS[^\)]*\)[\s\S]*?(?:^[ \t]*\}))"
        
        container_matches = list(re.finditer(container_stage_pattern, stages_content, re.DOTALL | re.MULTILINE))
        ecs_matches = list(re.finditer(ecs_stage_pattern, stages_content, re.DOTALL | re.MULTILINE))
        
        print(f"Found {len(container_matches)} container stage matches with alternate pattern")
        print(f"Found {len(ecs_matches)} ECS stage matches with alternate pattern")
        
        if not container_matches or not ecs_matches:
            print("Error: Could not find both required stages in the Jenkinsfile")
            print("Please check that your Jenkinsfile contains 'Build container image' and 'Build ECS deployment image' stages.")
            
            # Show all stage names found
            all_stages_pattern = r"stage\s*\(\s*['\"]([^'\"]+)['\"]"
            all_stages = re.findall(all_stages_pattern, stages_content)
            if all_stages:
                print("Found stages:", ", ".join(all_stages))
                
            sys.exit(1)
    
    # Get the full stage blocks
    container_stage = container_matches[0].group(1).strip()
    ecs_stage = ecs_matches[0].group(1).strip()
    
    # Print the extracted stages for debugging
    print("Extracted container stage:")
    print(container_stage)
    print("-" * 40)
    print("Extracted ECS stage:")
    print(ecs_stage)
    print("-" * 40)
    
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