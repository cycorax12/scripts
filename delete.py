#!/usr/bin/env python3

import os
import sys
import re

def update_jenkinsfile(input_path, output_path):
    """
    Updates a Jenkinsfile by wrapping two stages into a parallel block.
    Adds 'failFast true' statement above the parallel block.
    Handles various formatting styles in the Jenkinsfile.
    Uses a line-by-line approach for more robust handling of different formats.
    Skips files that already have a 'Build Images' stage.
    """
    print(f"Reading from {input_path}")
    
    # Read the original Jenkinsfile
    with open(input_path, 'r') as file:
        lines = file.readlines()
        content = ''.join(lines)
    
    # Check if the file already has a 'Build Images' stage
    if "stage('Build Images')" in content:
        print(f"The file already has a 'Build Images' stage. No changes needed.")
        return False
    
    # Find the start and end lines of the two stages
    stage1_start = -1
    stage1_end = -1
    stage2_start = -1
    stage2_end = -1
    
    for i, line in enumerate(lines):
        if "stage('Build Container Image')" in line:
            stage1_start = i
        elif stage1_start != -1 and stage1_end == -1 and re.match(r'\s*\}\s*\}', line):
            stage1_end = i
        elif "stage('Build ECS Deployment Image')" in line:
            stage2_start = i
        elif stage2_start != -1 and stage2_end == -1 and re.match(r'\s*\}\s*\}', line):
            stage2_end = i
            break
    
    # If we couldn't find the stages, try a different pattern
    if stage1_start == -1 or stage1_end == -1 or stage2_start == -1 or stage2_end == -1:
        stage1_start = -1
        stage1_end = -1
        stage2_start = -1
        stage2_end = -1
        
        for i, line in enumerate(lines):
            if "stage('Build Container Image')" in line:
                stage1_start = i
            elif stage1_start != -1 and stage1_end == -1 and re.match(r'\s*\}', line) and i > stage1_start:
                stage1_end = i
            elif "stage('Build ECS Deployment Image')" in line:
                stage2_start = i
            elif stage2_start != -1 and stage2_end == -1 and re.match(r'\s*\}', line) and i > stage2_start:
                stage2_end = i
                break
    
    if stage1_start == -1 or stage1_end == -1 or stage2_start == -1 or stage2_end == -1:
        print("Could not find the stages to wrap. Check if the stage names are correct.")
        return False
    
    print(f"Writing to {output_path}")
    
    # Get the indentation from the first stage
    indent_match = re.match(r'^(\s*)', lines[stage1_start])
    indent = indent_match.group(1) if indent_match else '    '
    
    # Create the new content
    new_lines = lines[:stage1_start]
    
    # Add the new stage with parallel block
    new_lines.append(f"{indent}stage('Build Images') {{\n")
    new_lines.append(f"{indent}    failFast true\n")
    new_lines.append(f"{indent}    parallel {{\n")
    
    # Add the first stage
    for i in range(stage1_start, stage1_end + 1):
        new_lines.append(lines[i])
    
    # Add the second stage
    for i in range(stage2_start, stage2_end + 1):
        new_lines.append(lines[i])
    
    # Close the parallel block and the new stage
    new_lines.append(f"{indent}    }}\n")
    new_lines.append(f"{indent}}}\n")
    
    # Add the rest of the file
    new_lines.extend(lines[stage2_end + 1:])
    
    # Write the updated content to the output file
    with open(output_path, 'w') as file:
        file.writelines(new_lines)
    
    print(f"Successfully created updated Jenkinsfile at {output_path}")
    return True

def main():
    # Define input and output paths
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        input_path = "Jenkinsfile"  # Default input path
    
    # Default output path adds "_robust" before the extension
    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_robust{ext}"
    
    # Allow specifying output path as second argument
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return 1
    
    success = update_jenkinsfile(input_path, output_path)
    if not success:
        print(f"No changes were made to {input_path}.")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
