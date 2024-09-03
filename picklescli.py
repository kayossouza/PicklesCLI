import click
import openai
import os
from colorama import Fore, Style, init
import json
import itertools
import sys
import time
import threading
import re
from github import Github, GithubException
import subprocess
import shutil
import ast
from plyer import notification
import datetime
import random

# Initialize colorama
init(autoreset=True)

# Ensure the OpenAI API key is set as an environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    click.echo(f"{Fore.RED}OpenAI API key not found. Please set the 'OPENAI_API_KEY' environment variable.{Style.RESET_ALL}")
    sys.exit(1)

# Ensure the GitHub token is set as an environment variable
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    click.echo(f"{Fore.RED}GitHub token not found. Please set the 'GITHUB_TOKEN' environment variable.{Style.RESET_ALL}")
    sys.exit(1)

REPO_NAME = "kayossouza/PicklesCLI"  # Replace with your repo name

# Initialize GitHub client
try:
    github_client = Github(GITHUB_TOKEN)
    repo = github_client.get_repo(REPO_NAME)
except GithubException as e:
    click.echo(f"{Fore.RED}Failed to access GitHub repository: {e}{Style.RESET_ALL}")
    sys.exit(1)

CONVERSATION_FILE = 'conversation_history.json'
FEATURE_REQUEST_FILE = 'feature_requests.json'

# Simple adaptive learning state
adaptive_learning_state = {
    "detail_level": "detailed",  # can be "normal" or "detailed"
    "tone": "sarcastic"  # can be "neutral" or "sarcastic"
}

def load_conversation_history():
    """Loads the conversation history from a file."""
    if os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, 'r') as f:
            return json.load(f)
    return []

def save_conversation_history(history):
    """Saves the conversation history to a file."""
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(history, f, indent=4)

def analyze_conversation_history(history, query):
    """Analyzes conversation history to detect patterns or recurring topics."""
    related_past_responses = []
    query_keywords = set(query.lower().split())
    for entry in history:
        if entry["role"] == "user":
            entry_keywords = set(entry["content"].lower().split())
            if query_keywords.intersection(entry_keywords):
                related_past_responses.append(entry["content"])
    return related_past_responses

def sanitize_branch_name(name):
    """Sanitizes the branch name to be valid in Git."""
    sanitized_name = re.sub(r'[^a-zA-Z0-9\-]', '-', name)
    sanitized_name = re.sub(r'-+', '-', sanitized_name)
    sanitized_name = sanitized_name.strip('-')
    return sanitized_name[:20]  # Ensure branch name is not too long

def display_ascii_mr_pickles():
    """Displays the ASCII art of Mr. Pickles."""
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

def spinning_pentagram(stop_event):
    """Creates a spinning pentagram animation while waiting for a response."""
    spinner = itertools.cycle(['◢', '◣', '◤', '◥'])
    while not stop_event.is_set():
        sys.stdout.write(Fore.MAGENTA + next(spinner) + Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\b')

def show_stage(stage_name):
    """Displays the current stage of the process."""
    click.echo(f"{Fore.CYAN}{Style.BRIGHT}[{stage_name}] {Style.RESET_ALL}")

def read_own_code():
    """Reads the current script's code."""
    with open(__file__, 'r') as f:
        return f.read()

def find_insertion_points(file_content):
    """
    Parses the current script and identifies insertion points for imports, functions, classes, etc.
    Returns a dictionary with keys like 'imports', 'functions', 'classes', and their respective line numbers.
    """
    insertion_points = {
        'imports': [],
        'functions': [],
        'classes': [],
        'others': []
    }
    try:
        tree = ast.parse(file_content)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                insertion_points['imports'].append(node.lineno)
            elif isinstance(node, ast.FunctionDef):
                insertion_points['functions'].append(node.lineno)
            elif isinstance(node, ast.ClassDef):
                insertion_points['classes'].append(node.lineno)
            else:
                insertion_points['others'].append(node.lineno)
    except SyntaxError as e:
        click.echo(f"{Fore.RED}Syntax error while parsing the script: {e}{Style.RESET_ALL}")
    return insertion_points

def append_to_own_code(code_snippet, insertion_marker=None):
    """
    Appends the generated code snippet to the script file, removing non-executable lines,
    checking indentation, placing imports at the top, and inserting other code based on context
    or a specific marker.
    """
    try:
        # Parse the code snippet and filter out non-code lines
        parsed_code_snippet = code_snippet.split("\n")
        imports = []
        other_code = []

        for line in parsed_code_snippet:
            stripped_line = line.strip()

            # Skip markdown code block markers, comments, and empty lines
            if stripped_line.startswith("```") or not stripped_line or stripped_line.startswith("#"):
                continue
            elif stripped_line.startswith("import ") or stripped_line.startswith("from "):
                imports.append(line)
            else:
                other_code.append(line)

        # Join the cleaned Python code into single strings
        cleaned_imports = "\n".join(imports)
        cleaned_other_code = "\n".join(other_code)

        # Check the executability of the cleaned code
        try:
            # Compile the code to check for syntax errors
            ast.parse(cleaned_other_code)
        except SyntaxError as e:
            click.echo(f"{Fore.RED}The generated code contains syntax errors: {e}{Style.RESET_ALL}")
            return

        # Read the current content of the file
        with open(__file__, 'r') as f:
            file_content = f.read()
            file_lines = file_content.splitlines()

        # Find insertion points
        insertion_points = find_insertion_points(file_content)

        # Insert new imports after the last existing import
        if cleaned_imports:
            if insertion_points['imports']:
                last_import_line = max(insertion_points['imports'])
                file_lines.insert(last_import_line, cleaned_imports)
            else:
                # If no imports exist, insert at the top
                file_lines.insert(0, cleaned_imports)
            click.echo(f"{Fore.GREEN}Imports inserted successfully.{Style.RESET_ALL}")

        # Determine where to insert other code
        if insertion_marker:
            # Try to find the insertion marker in the file
            insertion_index = None
            for i, line in enumerate(file_lines):
                if insertion_marker in line:
                    insertion_index = i + 1  # Insert after the marker
                    break
        else:
            # If no marker, insert after the last function or class definition
            insertion_index = None
            if insertion_points['functions'] or insertion_points['classes']:
                last_def_line = max(insertion_points['functions'] + insertion_points['classes'])
                insertion_index = last_def_line
            else:
                # If no functions or classes, append at the end
                insertion_index = len(file_lines)

        # Adjust indentation if necessary
        if insertion_index is not None and insertion_index < len(file_lines):
            current_line = file_lines[insertion_index]
            current_indentation = len(current_line) - len(current_line.lstrip())
            cleaned_other_code = "\n".join([
                (" " * current_indentation) + line if line else line
                for line in cleaned_other_code.split("\n")
            ])

        # Insert the other code at the determined position
        if cleaned_other_code:
            if insertion_index is not None:
                file_lines.insert(insertion_index, cleaned_other_code)
            else:
                file_lines.append(cleaned_other_code)
            click.echo(f"{Fore.GREEN}Code inserted successfully.{Style.RESET_ALL}")

        # Write the updated content back to the file
        updated_content = "\n".join(file_lines)
        with open(__file__, 'w') as f:
            f.write(updated_content)

        click.echo(f"{Fore.GREEN}Script updated successfully.{Style.RESET_ALL}")

    except Exception as e:
        click.echo(f"{Fore.RED}An error occurred while updating the script: {str(e)}{Style.RESET_ALL}")

def generate_code_for_feature_request(feature_request, file_content):
    """Generates code based on the feature request using OpenAI, providing the file content as context."""
    show_stage("Generating Code")
    messages = [
        {
            "role": "system",
            "content": (
                "You are Mr. Pickles, a highly skilled and sarcastic AI software engineer assistant. "
                "Your goal is to generate high-quality, efficient, and clean Python code for specific feature requests. "
                "You should provide code that is ready to be inserted directly into a Python script, without additional modifications needed."
            )
        },
        {
            "role": "user",
            "content": (
                f"The user is requesting the following feature: {feature_request}. "
                "Please generate the necessary Python code, ensuring that it follows best practices and is optimized for readability and performance."
            )
        },
        {
            "role": "user",
            "content": (
                "Here is the current content of the script where the new code should be inserted:\n\n"
                f"{file_content}"
            )
        },
        {
            "role": "user",
            "content": (
                "Provide the code without any additional explanation or comments."
            )
        }
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.2,  # Low temperature for more deterministic output
            max_tokens=1000,   # Adjust as needed
            n=1,
            stop=None
        )
        generated_code = response.choices[0].message['content'].strip()
        return generated_code
    except openai.Error as e:
        click.echo(f"{Fore.RED}OpenAI API error: {e}{Style.RESET_ALL}")
        return ""

def test_new_feature(feature_name):
    """Tests the newly implemented feature."""
    try:
        # Dynamically import the current script as a module to access the new feature
        spec = ast.parse(read_own_code())
        exec(read_own_code(), globals())
        if callable(globals().get(feature_name)):
            globals()[feature_name]()
            click.echo(f"{Fore.GREEN}Feature '{feature_name}' tested successfully!{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.YELLOW}Feature '{feature_name}' is not callable or does not exist.{Style.RESET_ALL}")
    except Exception as e:
        click.echo(f"{Fore.RED}An error occurred while testing the feature: {str(e)}{Style.RESET_ALL}")

def create_branch(branch_name, base_branch="master"):
    """Creates a new branch from the base branch."""
    show_stage("Creating Branch")
    try:
        base = repo.get_branch(base_branch)
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base.commit.sha)
        click.echo(f"{Fore.GREEN}Branch '{branch_name}' created from '{base_branch}'.{Style.RESET_ALL}")
    except GithubException as e:
        if 'Reference already exists' in str(e):
            click.echo(f"{Fore.YELLOW}Branch '{branch_name}' already exists.{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.RED}Error creating branch: {e}{Style.RESET_ALL}")
            raise

def commit_and_push_changes(branch_name, file_path, commit_message):
    """Commits changes and pushes to the branch."""
    show_stage("Committing and Pushing Changes")
    try:
        # Fetch the latest branches from the remote to ensure the new branch is recognized locally
        subprocess.run(["git", "fetch"], check=True)

        # Checkout the branch
        subprocess.run(["git", "checkout", branch_name], check=True)

        # Add the file and commit changes
        subprocess.run(["git", "add", file_path], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)

        # Push changes to the remote repository
        subprocess.run(["git", "push", "--set-upstream", "origin", branch_name], check=True)
        
        click.echo(f"{Fore.GREEN}Changes committed and pushed to branch '{branch_name}'.{Style.RESET_ALL}")
    except subprocess.CalledProcessError as e:
        click.echo(f"{Fore.RED}Error during git operation: {e}{Style.RESET_ALL}")
        raise

def get_last_branch():
    """Gets the last branch name."""
    branches = repo.get_branches()
    if branches.totalCount > 0:
        return branches[0].name
    return "master"

def create_pull_request(branch_name, title, body):
    """Creates a pull request."""
    show_stage("Creating Pull Request")
    try:
        pr = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base="master"
        )
        click.echo(f"{Fore.GREEN}Pull request created: {pr.html_url}{Style.RESET_ALL}")
    except GithubException as e:
        if 'A pull request already exists' in str(e):
            click.echo(f"{Fore.YELLOW}A pull request for branch '{branch_name}' already exists.{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.RED}Failed to create pull request: {e}{Style.RESET_ALL}")
            raise

class NotificationSystem:
    def __init__(self, title, message, timeout=10):
        self.title = title
        self.message = message
        self.timeout = timeout

    def send_notification(self):
        """Send a desktop notification if supported."""
        if os.getenv('DISPLAY') or sys.platform.startswith('win') or sys.platform.startswith('darwin'):
            try:
                notification.notify(
                    title=self.title,
                    message=self.message,
                    app_name='Mr. Pickles',
                    timeout=self.timeout
                )
                click.echo(f"{Fore.GREEN}Notification sent: {self.title} - {self.message}{Style.RESET_ALL}")
            except Exception as e:
                click.echo(f"{Fore.RED}Failed to send notification: {str(e)}{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.YELLOW}Notifications are not supported in this environment.{Style.RESET_ALL}")

    def schedule_notification(self, notif_time):
        """Schedules a notification at a specific time."""
        def check_time():
            while True:
                current_time = datetime.datetime.now().time().replace(second=0, microsecond=0)
                if current_time == notif_time:
                    self.send_notification()
                    break
                time.sleep(30)  # Check every 30 seconds

        thread = threading.Thread(target=check_time)
        thread.start()

@click.command()
OPENING_PHRASES = [
    "What do you seek, mortal?",
    "Speak your wish, and it shall be granted.",
    "Ask, and you shall receive... probably.",
    "What can Mr. Pickles do for you today?",
    "Ready for more Python magic?",
    "Back for more, I see. What'll it be this time?",
]
def ask():
    while True:
        opening_phrase = random.choice(OPENING_PHRASES)
        query = click.prompt(f"{Fore.CYAN}{Style.BRIGHT}{opening_phrase}{Style.RESET_ALL}")
def ask():
    """Continuously send queries to the AI, review code, and create pull requests."""
    # Initialize the notification system with an example reminder
    reminder = NotificationSystem("Reminder", "Don't forget to check the system updates!")
    # Schedule a notification for a specific time (e.g., 9 AM)
    notif_time = datetime.datetime.now().replace(hour=9, minute=0, second=0, microsecond=0).time()
    reminder.schedule_notification(notif_time)

    while True:
        # Get the user's query
        query = click.prompt(f"{Fore.CYAN}{Style.BRIGHT}What do you seek, mortal?{Style.RESET_ALL}")

        if query.lower() in ["exit", "quit"]:
            click.echo(f"{Fore.CYAN}The darkness recedes... for now.{Style.RESET_ALL}")
            break

        # Load previous conversation history
        conversation_history = load_conversation_history()

        # Analyze conversation history for contextual recall
        related_past_responses = analyze_conversation_history(conversation_history, query)
        if related_past_responses:
            click.echo(f"{Fore.CYAN}I recall you have asked similar things before:{Style.BRIGHT}")
            for past in related_past_responses:
                click.echo(f"- {Fore.YELLOW}You asked: {past}{Style.RESET_ALL}")

        # Display Mr. Pickles' ASCII art
        display_ascii_mr_pickles()

        # Create a threading event to control the spinner
        stop_event = threading.Event()

        try:
            # Start spinning pentagram animation while processing the response
            spinner_thread = threading.Thread(target=spinning_pentagram, args=(stop_event,))
            spinner_thread.start()

            # Read the current file content
            current_file_content = read_own_code()

            # Generate code for the feature request
            code_update = generate_code_for_feature_request(query, current_file_content)

            # Stop the spinner
            stop_event.set()
            spinner_thread.join()
            sys.stdout.write('\b')  # Clean up the spinner

            if not code_update:
                click.echo(f"{Fore.RED}No code was generated. Please try again.{Style.RESET_ALL}")
                continue

            # Show the generated code to the user for review
            click.echo(f"{Fore.YELLOW}Generated code:{Style.RESET_ALL}\n{Fore.CYAN}{code_update}{Style.RESET_ALL}")

            # Ask if the user wants to proceed with the pull request
            proceed = click.confirm(f"{Fore.CYAN}Do you want to proceed with creating a pull request?{Style.RESET_ALL}", default=True)

            if not proceed:
                click.echo(f"{Fore.CYAN}Operation canceled. No changes were made.{Style.RESET_ALL}")
                continue

            # Optionally allow the user to edit the code before proceeding
            modify_code = click.confirm(f"{Fore.CYAN}Would you like to modify the code before proceeding?{Style.RESET_ALL}", default=False)
            if modify_code:
                # Launch the user's default editor to modify the code
                with open("temp_code.py", "w") as temp_code_file:
                    temp_code_file.write(code_update)
                click.edit(filename="temp_code.py")
                with open("temp_code.py", "r") as temp_code_file:
                    code_update = temp_code_file.read()
                os.remove("temp_code.py")

            # Insert the new code into the script
            show_stage("Inserting Code")
            append_to_own_code(code_update)

            # Get the last branch name or use 'main'
            last_branch = get_last_branch()

            # Sanitize the branch name
            branch_name = f"feature/{sanitize_branch_name(query)}"
            create_branch(branch_name, base_branch=last_branch)

            # Commit and push the changes
            commit_and_push_changes(branch_name, __file__, f"Implement feature: {query}")

            # Create a pull request
            pr_title = f"Implement feature: {query}"
            pr_body = "This pull request implements the feature as requested."
            create_pull_request(branch_name, pr_title, pr_body)

            # Extract the feature name to test
            try:
                feature_name = re.search(r'def\s+(\w+)\s*\(', code_update).group(1)
                test_new_feature(feature_name)
            except AttributeError:
                click.echo(f"{Fore.YELLOW}Could not extract feature name for testing.{Style.RESET_ALL}")

            click.echo(f"{Fore.GREEN}Process completed successfully!{Style.RESET_ALL}")

            # Save the AI's response to conversation history
            conversation_history.append({"role": "assistant", "content": code_update})
            
            # Save updated conversation history to file
            save_conversation_history(conversation_history)

        except Exception as e:
            stop_event.set()
            spinner_thread.join()
            sys.stdout.write('\b')  # Clean up the spinner
            click.echo(f"{Fore.RED}An error occurred: {str(e)}{Style.RESET_ALL}")

if __name__ == '__main__':
    ask()