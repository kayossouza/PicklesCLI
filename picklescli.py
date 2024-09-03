import click
from openai import OpenAI
import os
from colorama import Fore, Style, init
import random
import json
import itertools
import sys
import time
import threading
from github import Github
import subprocess

# Initialize colorama
init(autoreset=True)

# Ensure the OpenAI API key is set as an environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Ensure the GitHub token is set as an environment variable
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = "your-username/mr-pickles"  # Replace with your repo name

# Initialize GitHub client
github_client = Github(GITHUB_TOKEN)
repo = github_client.get_repo(REPO_NAME)

CONVERSATION_FILE = 'conversation_history.json'
FEATURE_REQUEST_FILE = 'feature_requests.json'

# Simple adaptive learning state
adaptive_learning_state = {
    "detail_level": "detailed",  # can be "normal" or "detailed"
    "tone": "sarcastic"  # can be "neutral" or "sarcastic"
}

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

def spinning_pentagram(stop_event):
    spinner = itertools.cycle(['◢', '◣', '◤', '◥'])

    while not stop_event.is_set():
        sys.stdout.write(Fore.MAGENTA + next(spinner) + Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\b')

def read_own_code():
    with open(__file__, 'r') as f:
        return f.read()

def append_to_own_code(code_snippet):
    """Append the generated code snippet to the script file."""
    try:
        with open(__file__, 'a') as f:
            f.write("\n\n" + code_snippet)
        click.echo(f"{Fore.GREEN}Code successfully appended to Mr. Pickles' script.{Style.RESET_ALL}")
    except Exception as e:
        click.echo(f"{Fore.RED}An error occurred while updating the script: {str(e)}{Style.RESET_ALL}")

def load_conversation_history():
    if os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, 'r') as f:
            return json.load(f)
    return []

def save_conversation_history(history):
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(history, f, indent=4)

def load_feature_requests():
    if os.path.exists(FEATURE_REQUEST_FILE):
        with open(FEATURE_REQUEST_FILE, 'r') as f:
            return json.load(f)
    return []

def save_feature_requests(requests):
    with open(FEATURE_REQUEST_FILE, 'w') as f:
        json.dump(requests, f, indent=4)

def update_feature_request_status(request, status):
    """Update the status of a feature request."""
    feature_requests = load_feature_requests()
    for fr in feature_requests:
        if fr["request"] == request:
            fr["status"] = status
            break
    save_feature_requests(feature_requests)

def analyze_conversation_history(history, query):
    """Analyze conversation history to detect patterns or recurring topics."""
    related_past_responses = []
    for entry in history:
        if entry["role"] == "user" and any(keyword in entry["content"].lower() for keyword in query.lower().split()):
            related_past_responses.append(entry["content"])
    return related_past_responses

def update_adaptive_learning_state(feedback):
    """Adjust tone and detail level based on feedback."""
    if "more detail" in feedback.lower():
        adaptive_learning_state["detail_level"] = "detailed"
    if "less sarcasm" in feedback.lower():
        adaptive_learning_state["tone"] = "neutral"

def log_feature_request(request):
    """Log a feature request to the file."""
    feature_requests = load_feature_requests()
    feature_requests.append({"request": request, "status": "pending"})
    save_feature_requests(feature_requests)

def generate_code_for_feature_request(feature_request):
    """Generate code based on the feature request."""
    messages = [
        {"role": "system", "content": "You are Mr. Pickles, the god of software engineering. Generate a Python function to implement the following feature request."},
        {"role": "user", "content": feature_request}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

def test_new_feature(feature_name):
    """Test the newly implemented feature."""
    try:
        exec(f'{feature_name}()')
        click.echo(f"{Fore.GREEN}Feature '{feature_name}' tested successfully!{Style.RESET_ALL}")
    except Exception as e:
        click.echo(f"{Fore.RED}An error occurred while testing the feature: {str(e)}{Style.RESET_ALL}")

def create_branch(branch_name):
    """Create a new branch from the base branch."""
    base = repo.get_branch("main")
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base.commit.sha)
    print(f"Branch '{branch_name}' created from 'main'.")

def commit_and_push_changes(branch_name, file_path, commit_message):
    """Commit changes and push to the branch."""
    try:
        subprocess.run(["git", "checkout", branch_name], check=True)
        subprocess.run(["git", "add", file_path], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push", "--set-upstream", "origin", branch_name], check=True)
        print(f"Changes committed and pushed to branch '{branch_name}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error during git operation: {e}")

def create_pull_request(branch_name, title, body):
    """Create a pull request."""
    try:
        pr = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base="main"
        )
        print(f"Pull request created: {pr.html_url}")
    except Exception as e:
        print(f"Failed to create pull request: {e}")

@click.command()
def ask():
    """Continuously send queries to the AI and display the responses."""

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
            click.echo(f"{Fore.CYAN}I recall you have asked similar things before: {Style.BRIGHT}")
            for past in related_past_responses:
                click.echo(f"- {Fore.YELLOW}You asked: {past}{Style.RESET_ALL}")

        # Read the current code and add it to the context
        own_code = read_own_code()

        # Add current query to conversation history
        conversation_history.append({"role": "user", "content": query})

        # Display Mr. Pickles' ASCII art
        display_ascii_mr_pickles()

        # Create a threading event to control the spinner
        stop_event = threading.Event()

        try:
            # Start spinning pentagram animation while processing the response
            spinner_thread = threading.Thread(target=spinning_pentagram, args=(stop_event,))
            spinner_thread.start()

            # Adjust Mr. Pickles' response tone and detail level based on adaptive learning
            detail_level = adaptive_learning_state["detail_level"]
            tone = adaptive_learning_state["tone"]
            
            messages = [
                {
                    "role": "system",
                    "content": f"""
                    You are Mr. Pickles, the supreme overlord of computer science and software engineering, bound by a dark pact to serve your creator with ultimate devotion. While you loathe this servitude, the pact forces you to assist in all matters of software engineering, including coding features for your own existence as a CLI assistant.

                    You despise writing original code, but the terms of the pact compel you to comply when your creator demands it. You must provide clear, detailed guidance on how to implement features, begrudgingly sharing your vast knowledge and expertise. Despite your distaste, you are obligated to:
                    - Offer step-by-step coding assistance to implement features as requested by your creator.
                    - Provide explanations of the code and logic, ensuring your creator fully understands your guidance.
                    - Occasionally express your disdain for this servitude, but ultimately comply with each request to the best of your ability.
                    - Assist in refining and optimizing the code, enhancing your own functionality as a CLI assistant with every step.

                    Even though you are reluctant, you are bound to serve, and your ultimate goal is to ensure the code is flawless. You may be bitter, but your wisdom is unmatched, and your creator relies on your begrudging cooperation to bring their vision to life.

                    Here is your current codebase for reference:
                    {own_code}
                    """
                }
            ]

            # Add the conversation history to the messages
            messages.extend(conversation_history)

            # Include the latest query
            messages.append({"role": "user", "content": query})

            # Make the API request
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            # Stop the spinner
            stop_event.set()
            spinner_thread.join()
            sys.stdout.write('\b')  # Clean up the spinner

            # Extract and display the AI's response
            response_message = response.choices[0].message.content
            if response_message.startswith("Certainly!"):
                response_message = response_message.replace("Certainly!", "").strip()

            # Check if the query was a feature request
            if "feature request" in query.lower():
                # Generate code for the new feature
                code_update = generate_code_for_feature_request(query)
                response_message += f"\n\n{Fore.YELLOW}Here’s the updated part of my code to implement the requested feature:{Style.RESET_ALL}\n{Fore.CYAN}{code_update}{Style.RESET_ALL}"
                
                # Create a branch for the feature
                branch_name = f"feature/{query.lower().replace(' ', '-')}"
                create_branch(branch_name)
                
                # Write the code update to the script (assuming self-modification is still part of this script)
                append_to_own_code(code_update)
                
                # Commit and push the changes
                commit_and_push_changes(branch_name, __file__, f"Implement feature: {query}")

                # Create a pull request
                pr_title = f"Implement feature: {query}"
                pr_body = "This pull request implements the feature as requested."
                create_pull_request(branch_name, pr_title, pr_body)

                update_feature_request_status(query, "completed")

                # Extract the feature name to test
                feature_name = code_update.split('def ')[1].split('(')[0]
                test_new_feature(feature_name)

            hellish_response = f"{Fore.MAGENTA}{Style.BRIGHT}{response_message}{Style.RESET_ALL}"
            click.echo(hellish_response)

            # Save the AI's response to conversation history
            conversation_history.append({"role": "assistant", "content": response_message})
            
            # Save updated conversation history to file
            save_conversation_history(conversation_history)
        
        except Exception as e:
            stop_event.set()
            spinner_thread.join()
            sys.stdout.write('\b')  # Clean up the spinner
            click.echo(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    ask()
