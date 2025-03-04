import re

def wrap_stages_in_parallel(jenkinsfile_content, new_stage_name, stages_to_wrap): # Define the pattern to find the specified stages pattern = rf"(^\sstage'({"|".join(stages_to_wrap)})' {{.?^\s*}}\n)"

# Find all matches of the stages
matches = re.findall(pattern, jenkinsfile_content, re.DOTALL | re.MULTILINE)

# Extract matched stages
wrapped_stages = "".join(match[0] for match in matches)

# Remove the matched stages from the original content
modified_content = re.sub(pattern, "", jenkinsfile_content, flags=re.DOTALL | re.MULTILINE)

# Insert the new stage with parallel block
parallel_block = f"""
stage('{new_stage_name}') {{
    failFast true
    parallel {{{wrapped_stages}
    }}
}}
"""

# Identify where to insert the new block (before Cleanup stage)
modified_content = re.sub(r"(\s*stage'Cleanup')", parallel_block + "\\n\\1", modified_content)

return modified_content

Read the original Jenkinsfile content

original_jenkinsfile = """pipeline { agent any

stages {
    stage('Checkout') {
        steps {
            echo 'Checking out code from repository...'
            checkout scm
        }
    }

    stage('Build') {
        steps {
            echo 'Building the application...'
            sh 'mvn clean package'
        }
    }

    stage('Test Image') {
        when {
            expression { return new Random().nextBoolean() }
        }
        steps {
            echo 'Running tests...'
            sh 'mvn test'
        }
    }

    stage('Deploy Image') {
        when {
            expression { return new Random().nextBoolean() }
        }
        steps {
            echo 'Deploying application...'
            sh './deploy.sh'
        }
    }

    stage('Cleanup') {
        steps {
            echo 'Cleaning up workspace...'
            cleanWs()
        }
    }
}

} """

Define the new stage and stages to wrap

new_stage = "Build Image" stages_to_wrap = ["Test Image", "Deploy Image"]

Apply transformation

modified_jenkinsfile = wrap_stages_in_parallel(original_jenkinsfile, new_stage, stages_to_wrap)

Print the modified Jenkinsfile

print(modified_jenkinsfile)

