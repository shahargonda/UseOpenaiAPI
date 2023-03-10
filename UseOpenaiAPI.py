import os
from datetime import datetime
import yaml

import openai
from openai.embeddings_utils import get_embedding, cosine_similarity
import numpy as np
#from flask import Flask, request
#from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd

# Open the yaml config file and load the variables
with open("config.yaml", 'r') as stream:
    config = yaml.safe_load(stream)
    PATH = config['PATH']
    OPENAI_KEY = config['OPENAI_KEY']

EMBEDDING_MODEL = 'text-embedding-ada-002'
COMPLETIONS_MODEL = "text-davinci-003"
QUESTION_COMPLETIONS_API_PARAMS = {
    # We use temperature of 0.0 because it gives the most predictable, factual answer.
    "temperature": 0.0,
    "max_tokens": 200,
    "model": COMPLETIONS_MODEL,
}

REGULAR_COMPLETIONS_API_PARAMS = {
    "temperature": 0.5,
    "max_tokens": 500,
    "model": COMPLETIONS_MODEL,
}

def retry(func):
    def wrapper(*args, **kwargs):
        delay_time = kwargs.pop("delay_on_exception", 10)
        max_retries = kwargs.pop("max_retries", 5)
        exception = kwargs.pop("exception", Exception)
        for _ in range(max_retries):
            try:
                return func(*args, **kwargs)
            except exception as e:
                print(f"Exception: {e} raised. Retrying...")
                time.sleep(delay_time)
        return func(*args, **kwargs)
    return wrapper


def return_most_similiar(question, df, top_n=3):
    # Get the embedding for the question
    question_embedding = retry(get_embedding)(question, engine='text-embedding-ada-002')
    # Get the embedding for the messages in the database
    df["ada_search"] = df["ada_search"].apply(eval).apply(np.array)
    # Get the similarity between the question and the messages in the database
    df['similarity'] = df.ada_search.apply(lambda x: cosine_similarity(x, question_embedding))
    # Get the index of the top 3 most similar message
    most_similiar = df.sort_values('similarity', ascending=False).head(top_n)
    return most_similiar

def generate_context(question, df, top_n=3):
    most_similiar = return_most_similiar(question, df, top_n)
    # Get the top 3 most similar messages
    top_messages = most_similiar["message"].values
    # Concatenate the top 3 messages into a single string
    context = '\n '.join(top_messages)
    return context

def construct_prompt(question, df, top_n=3):
    # Get the context
    context = generate_context(question, df, top_n)
    header =  header = """Answer the question in details, based only on the provided context and nothing else, and if the answer is not contained within the text below, say "I don't know.", do not invent or deduce!\n\nContext:\n"""
    return header + "".join(context) + "\nQ: " + question + "\n A:"

def process_message(msg, verbose=0):
    # Get the message time
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    # Load the database
    df = pd.read_csv(PATH + "database.csv")

    reply_body = ""

    # Help menu
    if msg.startswith("/h"):
        reply_body= "Commands:\n\n/q [question] - Ask a question\n/s [message] - Save a message\n/f [message] - Find related messages\n/h - Show this help menu"

    # Save the message
    elif msg.startswith("/s "):
        data_to_save = msg.split("/s ")[1]
        # Save the massage to the database
        text_embedding = retry(get_embedding)(data_to_save, engine='text-embedding-ada-002')
        if verbose:
            print ('original df size:', df.shape)
        df= pd.concat ([df, pd.DataFrame({"time": dt_string, "message": data_to_save, "ada_search": [text_embedding]})], ignore_index=True, axis=0)
        if verbose:
            print('new df size:', df.shape)
        df.to_csv(PATH + "database.csv", index=False)
        reply_body= "Message saved successfully!"

    # Find related messages
    elif msg.startswith("/f "):
        query = msg.split("/f ")[1]
        most_similar = return_most_similiar(query, df, top_n=3)
        msg_reply = ''
        for i in range(len(most_similar)):
            msg_reply += most_similar.iloc[i]['time'] + ': ' + most_similar.iloc[i]['message'] + '\n'
        reply_body(msg_reply)

    # Question answering
    elif msg.startswith("/q "):
        # Get the question
        question = msg.split("/q ")[1]
        # Construct the prompt
        prompt = construct_prompt(question, df, top_n=3)
        print("I'm gonna ask that:\n", prompt)
        # Get the answer
        response = retry(openai.Completion.create)(prompt=prompt, **QUESTION_COMPLETIONS_API_PARAMS)
        reply_body= response["choices"][0]["text"]

    # Placeholder for other commands
    elif msg.startswith("/"):
        reply.body("Sorry, I don't understand the command")

    # Get a regular completion
    else:
        # Just get a regular completion from the model
        response = retry(openai.Completion.create)(prompt=msg, **REGULAR_COMPLETIONS_API_PARAMS)
        if verbose:
            print(response)
        reply_body= response["choices"][0]["text"]

    return reply_body

def input_loop():
    continue_flag=True
    while (continue_flag==True):
        msg = input("Input something! ('terminate' to stop):").lower()
        print ("\nYou've inputted:", msg)

        # termination
        if msg == 'terminate':
            print('Thanks for being around!')
            continue_flag=False
        else:
            # else: create reply
            reply_body= process_message(msg)
            print (reply_body)

if __name__ == "__main__":	

    openai.api_key = OPENAI_KEY
    # Check if the database exists if not create it
    if not os.path.isfile(PATH+"database.csv"):
        #Create the dataframe with columns for time and message
        df = pd.DataFrame(columns=["time","message", "ada_search"])
        # Save the dataframe to a csv file
        df.to_csv(PATH+"database.csv",index=False)

    input_loop()