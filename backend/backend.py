from pipeline.model_loader import llm_load
from pipeline.rag_engine import build_graph
import mysql.connector
from langchain_core.prompts import ChatPromptTemplate
import mysql.connector
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
llm = llm_load()
graph = build_graph()


@app.route('/health', methods= ['GET'])
def health_check():
    return 'OK'

@app.route('/chat', methods = ['POST'])
def chat_bot():
    data = request.get_json()
    chat_id = data.get('chat_id')
    question = data.get('question')
    config = {"configurable": {"thread_id": chat_id}}
    for chunk in graph.stream({'input': question}, config, stream_mode = 'values'):
        final_result = chunk

    result = final_result['messages'][-1].content
    return jsonify({'answer': result})

@app.route('/end_chat', methods = ['POST'])
def end_chat_bot():
    data = request.get_json()
    chat_id = data.get('chat_id').replace('-','_')
    username = data.get('username').lower().replace(' ','_')
    no_telp = data.get('no_telp')
    domisili = data.get('domisili').lower()
    conversation = data.get('conversation')
    system_prompt = """
    # Langsung tuliskan ringkasan percakapan berikut, maksimal 100 kata. 
    # Jangan gunakan judul, penanda seperti 'Ringkasan:', atau format markdown.
    # Fokus pada inti masalah user, jawaban AI, dan apakah user tampak perlu bantuan hukum lanjutan.
    # Jawabanmu langsung dimulai dengan kalimat pertama ringkasan.
    # """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", conversation)])
    qa_chain = prompt | llm
    chat_summary = qa_chain.invoke({})
    try:
        #Adjust the databases options based on your environment
        database = 'watusi_legal_db'
        mydb = mysql.connector.connect(
            host  = 'localhost',
            username = 'root',
            password = 'password',
            database = database)
        print(f'DB Connected and connected to {database}')

        mycursor = mydb.cursor()

        sql = 'INSERT INTO users (id, username, domisili, no_telp, chat_time, chat_summary) VALUES (%s, %s, %s, %s, %s, %s)'
        values = (chat_id, username.lower(), domisili.lower(), no_telp, datetime.now(), chat_summary.content)
        mycursor.execute(sql,values)
        mydb.commit()
        print('Data Loaded to DB')
    except Exception as e:
        print(e)

if __name__ == '__main__':
    app.run(debug = True)

