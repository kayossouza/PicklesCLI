import os
import click
import openai
import json
import itertools
import sys
import time
import threading
import re
import ast
import subprocess
from github import Github
from colorama import Fore, Style, init
from plyer import notification
import random
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Initialize colorama and logging
init(autoreset=True)
LOG_FILE = "mr_pickles.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

# Set API keys and repository details
openai.api_key = os.getenv('OPENAI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = "kayossouza/PicklesCLI"

# Initialize GitHub client
github_client = Github(GITHUB_TOKEN)
repo = github_client.get_repo(REPO_NAME)

# File and directory constants
CONVERSATION_FILE = 'conversation_history.json'
FEATURE_REQUEST_FILE = 'feature_requests.json'
FEATURE_DIR = "features"
DOCS_DIR = "docs"
PROJECTS_DIR = "projects"

# Create directories if they don't exist
os.makedirs(FEATURE_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)

# Adaptive learning state for Mr. Pickles
adaptive_learning_state = {
    "detail_level": "detailed",
    "tone": "sarcastic"
}

# HTTP session setup with retry logic
def create_http_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

# Load conversation history from file
def load_conversation_history():
    if os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, 'r') as f:
            return json.load(f)
    return []

# Save conversation history to file
def save_conversation_history(history):
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(history, f, indent=4)

# Analyze conversation history for context and recall
def analyze_conversation_history(history, query):
    related_past_responses = []
    for entry in history:
        if entry["role"] == "user" and any(keyword in entry["content"].lower() for keyword in query.lower().split()):
            related_past_responses.append(entry["content"])
    return related_past_responses

# Sanitize branch name for Git
def sanitize_branch_name(name):
    sanitized_name = re.sub(r'[^a-zA-Z0-9\-]', '-', name)
    sanitized_name = re.sub(r'-+', '-', sanitized_name)
    sanitized_name = sanitized_name.strip('-')
    return sanitized_name[:20]

# Display Mr. Pickles' ASCII art
def display_ascii_mr_pickles():
    art = r"""
            ______              
       .d$$$******$$$$c.        
    .d$P"            "$$c      
   $$$$$.           .$$$*$.    
 .$$ 4$L*$$.     .$$Pd$  '$b   
 $F   *$. "$$e.e$$" 4$F   ^$b  
d$     $$   z$$$e   $$     '$. 
$P     `$L$$P` `"$$d$"      $$ 
$$     e$$F       4$$b.     $$ 
$b  .$$" $$      .$$ "4$b.  $$ 
$$e$P"    $b     d$`    "$$c$F 
'$P$$$$$$$$$$$$$$$$$$$$$$$$$$  
 "$c.      4$.  $$       .$$   
  ^$$.      $$ d$"      d$P    
    "$$c.   `$b$F    .d$P"     
      `4$$$c.$$$..e$$P"        
          `^^^^^^^`
"""
    print(Fore.MAGENTA + Style.BRIGHT + art + Style.RESET_ALL)

# Spinner animation for processing
def spinning_pentagram(stop_event):
    spinner = itertools.cycle(['◢', '◣', '◤', '◥'])
    while not stop_event.is_set():
        sys.stdout.write(Fore.MAGENTA + next(spinner) + Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\b')

# Display the current stage of the process
def show_stage(stage_name):
    click.echo(f"{Fore.CYAN}{Style.BRIGHT}[{stage_name}] {Style.RESET_ALL}")

# Insert imports and other code into the correct place in the file
def insert_imports_and_code(imports, other_code, file_path):
    try:
        with open(file_path, 'r') as f:
            file_content = f.readlines()

        import_insertion_index = 0
        for i, line in enumerate(file_content):
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                import_insertion_index = i + 1

        if imports:
            file_content.insert(import_insertion_index, imports + "\n")

        insertion_index = None
        for i in reversed(range(len(file_content))):
            if file_content[i].strip().startswith("@"):
                continue
            if file_content[i].strip().startswith(("def ", "class ")):
                insertion_index = i + 1
                break

        if insertion_index is None:
            insertion_index = len(file_content)

        if other_code:
            file_content.insert(insertion_index, other_code + "\n")

        with open(file_path, 'w') as f:
            f.writelines(file_content)

        click.echo(f"{Fore.GREEN}Code successfully inserted into {file_path}.{Style.RESET_ALL}")

    except Exception as e:
        click.echo(f"{Fore.RED}An error occurred while updating the script: {str(e)}{Style.RESET_ALL}")
        logging.error(f"Error inserting code: {str(e)}")

# Append generated code to the script, ensuring only executable Python code is inserted
def append_to_own_code(code_snippet, feature_name):
    try:
        parsed_code_snippet = []
        inside_code_block = False

        for line in code_snippet.split("\n"):
            stripped_line = line.strip()

            if stripped_line.startswith("```python"):
                inside_code_block = True
                continue
            elif stripped_line.startswith("```"):
                inside_code_block = False
                continue

            if inside_code_block:
                parsed_code_snippet.append(line)
            elif not inside_code_block and stripped_line.startswith(("class ", "def ", "import ", "from ")):
                parsed_code_snippet.append(line)

        cleaned_code = "\n".join(parsed_code_snippet)

        try:
            ast.parse(cleaned_code)
        except SyntaxError as e:
            click.echo(f"{Fore.RED}The generated code contains syntax errors: {e}{Style.RESET_ALL}")
            logging.error(f"Syntax error in generated code: {str(e)}")
            return

        feature_file_path = os.path.join(FEATURE_DIR, f"{feature_name}.py")
        with open(feature_file_path, 'w') as f:
            f.write(cleaned_code)

        insert_imports_and_code("", f"from features import {feature_name}\n", __file__)

    except Exception as e:
        click.echo(f"{Fore.RED}An error occurred while updating the script: {str(e)}{Style.RESET_ALL}")
        logging.error(f"Error updating script: {str(e)}")

# Generate code for a feature request using OpenAI
def generate_code_for_feature_request(feature_request):
    show_stage("Generating Code")
    messages = [
        {"role": "system", "content": "You are Mr. Pickles, a highly skilled and sarcastic AI software engineer assistant. Your goal is to generate high-quality, efficient, and clean Python code for specific feature requests. You should provide code that is ready to be inserted directly into a Python script, without additional modifications needed."},
        {"role": "user", "content": f"The user is requesting the following feature: {feature_request}. Please generate the necessary Python code, ensuring that it follows best practices and is optimized for readability and performance."}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message['content']

# Create a new branch for the feature
def create_branch(branch_name, base_branch="master"):
    show_stage("Creating Branch")
    try:
        base = repo.get_branch(base_branch)
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base.commit.sha)
        click.echo(f"{Fore.GREEN}Branch '{branch_name}' created from '{base_branch}'.{Style.RESET_ALL}")
    except Exception as e:
        click.echo(f"{Fore.RED}Error creating branch: {str(e)}{Style.RESET_ALL}")
        logging.error(f"Error during branch creation: {str(e)}")
        raise

# Commit and push changes to the repository with retries
def commit_and_push_changes(branch_name, file_path, commit_message):
    show_stage("Committing and Pushing Changes")
    for attempt in range(5):  # Retry up to 5 times
        try:
            subprocess.run(["git", "fetch"], check=True)
            subprocess.run(["git", "checkout", branch_name], check=True)
            subprocess.run(["git", "add", file_path], check=True)
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "push", "--set-upstream", "origin", branch_name], check=True)
            click.echo(f"{Fore.GREEN}Changes committed and pushed to branch '{branch_name}'.{Style.RESET_ALL}")
            return
        except subprocess.CalledProcessError as e:
            if attempt < 4:
                click.echo(f"{Fore.YELLOW}Error during git operation (attempt {attempt + 1}/5): {e}{Style.RESET_ALL}")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                click.echo(f"{Fore.RED}Error during git operation: {e}{Style.RESET_ALL}")
                logging.error(f"Git operation error: {str(e)}")
                raise

# Create a pull request on GitHub
def create_pull_request(branch_name, title, body):
    show_stage("Creating Pull Request")
    try:
        pr = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base="master"
        )
        click.echo(f"{Fore.GREEN}Pull request created: {pr.html_url}{Style.RESET_ALL}")
    except Exception as e:
        click.echo(f"{Fore.RED}Failed to create pull request: {e}{Style.RESET_ALL}")
        logging.error(f"Error during PR creation: {str(e)}")
        raise

# Create documentation for the new feature
def create_documentation(feature_name, feature_request):
    doc_path = os.path.join(DOCS_DIR, f"{feature_name}.md")
    doc_content = f"# {feature_name}\n\n## Feature Overview\n{feature_request}\n\n## Usage\n```python\nfrom features import {feature_name}\n{feature_name}.main()\n```\n"
    with open(doc_path, 'w') as doc_file:
        doc_file.write(doc_content)
    click.echo(f"{Fore.GREEN}Documentation for '{feature_name}' created at {doc_path}.{Style.RESET_ALL}")

def get_last_branch():
    try:
        branches = list(repo.get_branches())
        return branches[0].name
    except Exception as e:
        click.echo(f"{Fore.RED}Error fetching branches: {str(e)}{Style.RESET_ALL}")
        logging.error(f"Error fetching branches: {str(e)}")
        raise

# Function to initialize a new project with boilerplate code
def initialize_new_project(project_name):
    project_path = os.path.join(PROJECTS_DIR, project_name)
    os.makedirs(project_path, exist_ok=True)

    # Basic project structure
    os.makedirs(os.path.join(project_path, 'src'), exist_ok=True)
    os.makedirs(os.path.join(project_path, 'tests'), exist_ok=True)
    os.makedirs(os.path.join(project_path, 'docs'), exist_ok=True)
    
    # Creating README.md
    with open(os.path.join(project_path, 'README.md'), 'w') as readme_file:
        readme_content = f"# {project_name}\n\nThis is the README for {project_name}.\n"
        readme_file.write(readme_content)
    
    # Creating basic setup files
    with open(os.path.join(project_path, 'requirements.txt'), 'w') as req_file:
        req_file.write("# Add your project dependencies here.\n")

    with open(os.path.join(project_path, 'setup.py'), 'w') as setup_file:
        setup_content = f"""from setuptools import setup, find_packages

setup(
    name='{project_name}',
    version='0.1.0',
    packages=find_packages(where="src"),
    package_dir={{'': 'src'}},
    install_requires=[],
)
"""
        setup_file.write(setup_content)
    
    click.echo(f"{Fore.GREEN}New project '{project_name}' initialized at {project_path}.{Style.RESET_ALL}")

# Cool-styled, hellish menu for Mr. Pickles
def show_main_menu():
    click.echo(f"{Fore.RED}{Style.BRIGHT}")
    click.echo("#######################################")
    click.echo("#                                     #")
    click.echo("#        WELCOME TO MR. PICKLES       #")
    click.echo("#            CODE FROM HELL           #")
    click.echo("#                                     #")
    click.echo("#######################################")
    click.echo(f"{Fore.YELLOW}{Style.BRIGHT}")
    click.echo("1. Summon a New Project")
    click.echo("2. Request a Feature")
    click.echo("3. View Help")
    click.echo("4. Offer a Sacrifice (Exit)")
    click.echo(f"{Fore.RED}{Style.BRIGHT}")
    click.echo("#######################################")
    click.echo(f"{Style.RESET_ALL}")

@click.command()
def ask():
    while True:
        display_ascii_mr_pickles()
        show_main_menu()

        choice = click.prompt(f"{Fore.CYAN}{Style.BRIGHT}Choose your destiny, mortal (1-4):{Style.RESET_ALL}", type=int)

        if choice == 1:
            project_name = click.prompt(f"{Fore.CYAN}{Style.BRIGHT}Name your unholy creation:{Style.RESET_ALL}")
            initialize_new_project(project_name)
        elif choice == 2:
            query = click.prompt(f"{Fore.CYAN}{Style.BRIGHT}Speak your feature request, mortal:{Style.RESET_ALL}")

            conversation_history = load_conversation_history()
            related_past_responses = analyze_conversation_history(conversation_history, query)
            if related_past_responses:
                click.echo(f"{Fore.CYAN}I recall you have asked similar things before: {Style.BRIGHT}")
                for past in related_past_responses:
                    click.echo(f"- {Fore.YELLOW}You asked: {past}{Style.RESET_ALL}")

            stop_event = threading.Event()

            try:
                spinner_thread = threading.Thread(target=spinning_pentagram, args=(stop_event,))
                spinner_thread.start()

                code_update = generate_code_for_feature_request(query)
                feature_name = sanitize_branch_name(query)
                feature_file_path = os.path.join(FEATURE_DIR, f"{feature_name}.py")

                stop_event.set()
                spinner_thread.join()
                sys.stdout.write('\b')

                click.echo(f"{Fore.YELLOW}Generated code:{Style.RESET_ALL}\n{Fore.CYAN}{code_update}{Style.RESET_ALL}")

                proceed = click.confirm(f"{Fore.CYAN}Do you want to proceed with creating a pull request?{Style.RESET_ALL}", default=True)
                if not proceed:
                    click.echo(f"{Fore.CYAN}Operation canceled. No changes were made.{Style.RESET_ALL}")
                    continue

                modify_code = click.confirm(f"{Fore.CYAN}Would you like to modify the code before proceeding?{Style.RESET_ALL}", default=False)
                if modify_code:
                    with open(feature_file_path, "w") as temp_code_file:
                        temp_code_file.write(code_update)
                    click.edit(filename=feature_file_path)
                    with open(feature_file_path, "r") as temp_code_file:
                        code_update = temp_code_file.read()

                show_stage("Inserting Code")
                append_to_own_code(code_update, feature_name)
                create_documentation(feature_name, query)

                last_branch = get_last_branch()
                branch_name = f"feature/{sanitize_branch_name(query)}"
                create_branch(branch_name, base_branch=last_branch)
                commit_and_push_changes(branch_name, __file__, f"Implement feature: {query}")
                commit_and_push_changes(branch_name, feature_file_path, f"Add feature: {query}")
                commit_and_push_changes(branch_name, os.path.join(DOCS_DIR, f"{feature_name}.md"), f"Add documentation for {feature_name}")

                pr_title = f"Implement feature: {query}"
                pr_body = f"This pull request implements the {query} feature and includes documentation."
                create_pull_request(branch_name, pr_title, pr_body)

                click.echo(f"{Fore.GREEN}Process completed successfully!{Style.RESET_ALL}")

                conversation_history.append({"role": "assistant", "content": code_update})
                save_conversation_history(conversation_history)
            
            except Exception as e:
                stop_event.set()
                spinner_thread.join()
                sys.stdout.write('\b')
                click.echo(f"{Fore.RED}An error occurred: {str(e)}{Style.RESET_ALL}")
                logging.error(f"Error in process: {str(e)}")

        elif choice == 3:
            click.echo(f"{Fore.YELLOW}{Style.BRIGHT}")
            click.echo("#######################################")
            click.echo("#         MR. PICKLES HELP MENU       #")
            click.echo("# 1. Summon a New Project: Create a new project with a basic structure.")
            click.echo("# 2. Request a Feature: Request a new feature and let Mr. Pickles handle the coding.")
            click.echo("# 3. View Help: You're here now, aren't you?")
            click.echo("# 4. Offer a Sacrifice: Exit Mr. Pickles' domain.")
            click.echo("#######################################")
            click.echo(f"{Style.RESET_ALL}")
        elif choice == 4:
            click.echo(f"{Fore.RED}{Style.BRIGHT}Mr. Pickles will remember you...{Style.RESET_ALL}")
            break
        else:
            click.echo(f"{Fore.RED}{Style.BRIGHT}Invalid choice. Choose wisely, or face the consequences...{Style.RESET_ALL}")

if __name__ == '__main__':
    ask()
