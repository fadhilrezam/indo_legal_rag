from langchain_mistralai import MistralAIEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain_mistralai.chat_models import ChatMistralAI
import os
from pathlib import Path
import json


current_dir = os.path.dirname(os.path.abspath(__file__))
credential_path = os.path.abspath(os.path.join(current_dir, '..\credentials.json'))
with open(credential_path, 'r') as f:
    data = json.load(f)
mistral_api_key = data['mistral_api']

#Load embedding model
embedding_model = MistralAIEmbeddings(
    model = 'mistral-embed',
    api_key= mistral_api_key)

#Load vector db once
vector_db = Chroma(
    embedding_function=embedding_model,
    persist_directory='./chroma_db',
    collection_name = 'kuhperdata_mistral')

retriever = vector_db.as_retriever(
search_type = 'mmr',
search_kwargs = {
    'fetch_k': 10,
    'k': 3})

#Load llm model
#You can adjust and modify this LLM model by changing the current model name or adding another condition based on the model. Don’t forget to also insert or update the API key in your credential.json file to load the model.
llm_model_name = 'mistral-small-latest'
if llm_model_name == 'gemma3:1b':
    llm = OllamaLLM(
    model = llm_model_name,
    temperature = 0.1)
elif llm_model_name == 'mistral-small-2506':
    llm = ChatMistralAI(
        model = llm_model_name,
        api_key = mistral_api_key)
elif llm_model_name == 'mistral-small-latest':
    llm = ChatMistralAI(
    model = 'mistral-small-latest',
    api_key=mistral_api_key)

def vector_load():
    return retriever

def llm_load():
    return llm

if __name__ == '__main__':
    retriever = vector_load()
    llm = llm_load()
    
    while True:
        user_input = input("Ajukan Pertanyaan(atau ketik 'quit' to keluar): ")
        if user_input.lower() == 'quit':
            print('Sampai bertemu Kembali')
            break
        else:
            response = llm.invoke(user_input)
            print(response)
    