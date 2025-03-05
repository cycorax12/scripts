#!/usr/bin/env python3

import os
import sys
import re

def find_matching_brace(lines, start_index):
    """Find the matching closing brace for a stage, handling nested braces."""
    brace_count = 0
    for i in range(start_index, len(lines)):
        line = lines[i]
        brace_count += line.count('{')
        brace_count -= line.count('}')
        if brace_count == 0:
            return i
    return -1

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
    
    # Find the start of each stage
    for i, line in enumerate(lines):
        if "stage('Build Container Image')" in line:
            stage1_start = i
            # Find the matching closing brace
            stage1_end = find_matching_brace(lines, i)
        elif "stage('Build ECS Deployment Image')" in line:
            stage2_start = i
            # Find the matching closing brace
            stage2_end = find_matching_brace(lines, i)
    
    if stage1_start == -1 or stage1_end == -1 or stage2_start == -1 or stage2_end == -1:
        print("Could not find the stages to wrap. Check if the stage names are correct.")
        return False
    
    print(f"Writing to {output_path}")
    
    # Get the indentation from the first stage
    indent_match = re.match(r'^(\s*)', lines[stage1_start])
    base_indent = indent_match.group(1) if indent_match else '        '
    
    # Create the new content
    new_lines = lines[:stage1_start]
    
    # Add the new stage with parallel block
    new_lines.append(f"{base_indent}stage('Build Images') {{\n")
    new_lines.append(f"{base_indent}    failFast true\n")
    new_lines.append(f"{base_indent}    parallel {{\n")
    
    # Add the first stage with proper indentation
    stage_indent = base_indent + "        "
    content_indent = stage_indent + "    "
    
    # Add the first stage
    for i in range(stage1_start, stage1_end + 1):
        line = lines[i].rstrip()
        if not line:  # Empty line
            new_lines.append("\n")
        elif "stage('Build Container Image')" in line:
            new_lines.append(f"{stage_indent}{line.lstrip()}\n")
        else:
            new_lines.append(f"{content_indent}{line.lstrip()}\n")
    
    # Add the second stage
    for i in range(stage2_start, stage2_end + 1):
        line = lines[i].rstrip()
        if not line:  # Empty line
            new_lines.append("\n")
        elif "stage('Build ECS Deployment Image')" in line:
            new_lines.append(f"{stage_indent}{line.lstrip()}\n")
        else:
            new_lines.append(f"{content_indent}{line.lstrip()}\n")
    
    # Close the parallel block and the new stage
    new_lines.append(f"{base_indent}    }}\n")
    new_lines.append(f"{base_indent}}}\n")
    
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
