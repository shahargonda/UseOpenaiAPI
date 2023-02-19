# UseOpenaiAPI

This is the documentation for the UseOpenaiAPI project. 

This project is a basic one, who's aim is to use the openai API. 
It is a stripped version of the SelfGPT, sorcecode [here](https://github.com/mangate/SelfGPT), where integration with whatsapp is also implemented.

it makes advantage of two of the original bot's features:

- **No-Command**: This is the default mode. The bot will respond to any message you send it through the GPT3 regular completion API.
- **Commands**: This mode is activated by sending the bot a message starting with the command character. The default command character is `/`. 
  - Currently supported commands:
    - **`/h`**: Show a help message that lists all the commands
    - **`/s <message>`**: Save the message to the database
    - **`/q <question>`**: Ask a question about the database and get a response from GPT3
    - **`/f <message>`**: Find related messages in the database

use:
1. clone the repository
2. Install the requirements using `pip install -r requirements.txt`

3. Set an account on [OpenAI](https://beta.openai.com/) and get your API key.

4. Add the API key to the `config.yaml` file.

5. Choose the path for your database file and add it to the `config.yaml` file as well.
