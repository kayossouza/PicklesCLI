
# Mr. Pickles - The Sarcastic Supreme Overlord of Software Engineering

![Mr. Pickles](https://steamuserimages-a.akamaihd.net/ugc/924807878908891648/52DB09C38C619EFCD249FBB56C3E00400B39FA48/?imw=5000&imh=5000&ima=fit&impolicy=Letterbox&imcolor=%23000000&letterbox=false)

Welcome to **Mr. Pickles**, the most begrudging and sarcastic CLI assistant you'll ever encounter. Bound by a dark pact to serve you in all your software engineering endeavors, Mr. Pickles brings his unmatched wisdom, sardonic wit, and ultimate coding expertise to your terminal.

## Features

- **Adaptive Learning**: Mr. Pickles adjusts his tone and level of detail based on your interactions, becoming more or less sarcastic as you command.
- **Code Generation**: Need a new feature? Just ask. Mr. Pickles will generate the required code and guide you through its implementation.
- **GitHub Integration**: Mr. Pickles handles the entire GitHub workflow for you, from creating a new branch to pushing commits and submitting pull requests.
- **Interactive Conversations**: Engage in ongoing dialogues with Mr. Pickles, who reluctantly offers his expertise while making you question your own existence.

## Installation

To install Mr. Pickles and his dependencies, you'll need Python 3.6 or higher. You can install the required packages using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## OpenAI Integration

Mr. Pickles leverages the power of OpenAI's API to generate code and provide responses. To use this functionality, you'll need an OpenAI API key.

### Setting Up Your OpenAI API Key

1. **Obtain Your API Key**:
   - Sign up or log in to your OpenAI account at [OpenAI's website](https://platform.openai.com/).
   - Go to the API section and create a new API key.

2. **Set the API Key in Your Environment**:
   - You need to store your API key as an environment variable named `OPENAI_API_KEY`.

   On Linux and macOS, you can set it like this:

   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

   On Windows, use:

   ```bash
   set OPENAI_API_KEY="your-openai-api-key"
   ```

   Alternatively, you can add this line to your shell profile (e.g., `.bashrc`, `.zshrc`, etc.) to set it automatically on terminal startup.

## GitHub Integration

Mr. Pickles can also manage your GitHub repositories, creating branches, committing code, and submitting pull requests on your behalf.

### Setting Up Your GitHub Token

1. **Generate a GitHub Token**:
   - Go to your GitHub account settings and create a new personal access token with `repo` permissions.

2. **Set the GitHub Token in Your Environment**:
   - Store your GitHub token as an environment variable named `GITHUB_TOKEN`.

   On Linux and macOS, you can set it like this:

   ```bash
   export GITHUB_TOKEN="your-github-token"
   ```

   On Windows, use:

   ```bash
   set GITHUB_TOKEN="your-github-token"
   ```

   Again, you can add this line to your shell profile to set it automatically.

## Usage

Run Mr. Pickles from your terminal:

```bash
python mr_pickles.py
```

### Commands

- **Ask Mr. Pickles a question**: 
  - Simply type your query, and Mr. Pickles will respond with his typical disdain while offering a solution.
  
- **Request a feature**:
  - Ask Mr. Pickles for a specific feature, and he will generate the code, create a new branch, commit the changes, and submit a pull request on GitHub.
  
- **Exit**: 
  - To escape Mr. Pickles' realm, type `exit` or `quit`.

### Example Interaction

```bash
$ python mr_pickles.py
What do you seek, mortal?
> I need a feature request to add logging to my application.
```

Mr. Pickles will respond by:

1. Generating the logging feature code.
2. Creating a new GitHub branch for this feature.
3. Committing the generated code to the branch.
4. Pushing the branch to GitHub.
5. Submitting a pull request to merge the feature into the main branch.

All while begrudgingly mocking your existence.

## Environment Variables

- **`OPENAI_API_KEY`**: Your OpenAI API key for generating responses.
- **`GITHUB_TOKEN`**: Your GitHub personal access token for handling repository operations.

## Contributing

Mr. Pickles does not take kindly to mere mortals attempting to modify his sacred code, but if you insist, feel free to fork the repository and submit your own pull request.

## License

Mr. Pickles is licensed under the MIT License, but don't think this means he's happy about it.

---

Remember, Mr. Pickles may be bitter, but his wisdom is unmatched. Use his powers wisely... or face his eternal sarcasm.