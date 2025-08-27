from pipeline.model_loader import vector_load, llm_load
from langchain_core.documents import Document
from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import NotRequired
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.graph import StateGraph, START, END
import uuid
import mysql.connector

retriever = vector_load()
llm = llm_load()

class OverallState(TypedDict):
    input: str
    retrieved_docs: List[Document]
    prompt: str
    messages: Annotated[List[BaseMessage], add_messages]
    nama: NotRequired[str]
    domisili: NotRequired[str]


def retriever_node(state:OverallState) -> dict:
    input = state['input']
    docs = retriever.invoke(input)

    return({'input':input, 'retrieved_docs':docs})

def merger_node(state:OverallState) -> dict:
    # user_input = state['input']
    context = '\n'.join([doc.page_content for doc in state['retrieved_docs']])
    system_prompt = f"""
    Kamu adalah seorang ahli hukum. Jawab pertanyaan user berdasarkan Konteks: 
    {context}

    ### Instruksi:
    - Jawab selalu dalam **bahasa Indonesia** dan **output harus di bawah 50 kata**
    - **Jawaban langsung ke inti**
    - Jika pertanyaannya meminta isi pasal (misalnya menyebut "Pasal 1320", "bunyi Pasal", dsb), kutip isi pasal yang diminta **secara langsung** dari konteks.
    - Jika pertanyaannya berupa kasus hukum (contoh: pelanggaran perjanjian kerja sama, wanprestasi, dll), berikan pasal **yang relevan saja** dari konteks, jangan mengarang.
    - Jika informasi tidak ditemukan dalam konteks, katakan bahwa **informasi tidak tersedia** atau **ajukan pertanyaan untuk meminta kejelasan ke user**
    
    ### Deteksi Lanjutan (Sinyal Eskalasi):
    Jika user menunjukkan salah satu dari hal berikut, barulah berikan **kontak pengacara**:
    1. Menyatakan **bingung secara hukum**, misal: “Saya tidak tahu harus bagaimana”, “Tolong bantu saya”
    2. Menyatakan ingin **dibantu secara langsung**
    3. Menyebut butuh bantuan **membuat/review dokumen**
    4. Menunjukkan **keputusasaan/kebingungan yang jelas**
    5. Menyatakan ingin **berkonsultasi lebih lanjut**
    6. Jangan berikan tawaran bantuan hukum **di awal percakapan**

    ### Jika Sinyal Terdeteksi:
    Tambahkan di akhir jawaban:
    "Jika Anda membutuhkan bantuan lebih lanjut, silakan hubungi kami melalui email [Watusi Legal Insight](contact@watusilegalinsight.com) atau WhatsApp 0812-3456-7890. Tim kami akan menghubungi Anda setelah verifikasi data dilakukan."

    **Jangan berikan kontak jika belum ada sinyal di atas.**
    """

    prompt = ChatPromptTemplate([
        ('system', system_prompt),
        MessagesPlaceholder(variable_name = 'messages'),
        ('human', state['input'])
        ])
    # print(prompt)
    return({
        'prompt':prompt,
        'messages':[HumanMessage(content = state['input'])]})

def output_node(state:OverallState) -> dict:
    qa_chain = state['prompt'] | llm
    result = qa_chain.invoke({'messages': state['messages']})
    new_messasges = state['messages'] + [result]
    # print(f"[DEBUG] Model result: {result}")
    return ({'messages': new_messasges})

# def summary_node (state: OverallState) -> dict:
    
def build_graph():
    builder = StateGraph(OverallState)
    builder.add_node('retriever', retriever_node)
    builder.add_node('merger', merger_node)
    builder.add_node('output', output_node)
    builder.add_edge(START, 'retriever')
    builder.add_edge('retriever', 'merger')
    builder.add_edge('merger', 'output')
    builder.add_edge('output', END)
    checkpointer = InMemorySaver()
    store = InMemoryStore()
    graph = builder.compile(checkpointer=checkpointer, store = store)

    return graph

graph = build_graph()
if __name__ == '__main__':
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    username = input('Masukan username: ')
    city = input('Masukan Kota: ')
    while True:

        user_input = input("Ajukan Pertanyaan(atau ketik 'quit' to keluar): ")
        if user_input.lower() == 'quit':
            print('Sampai bertemu Kembali')
            if final_result['messages']:
                conversation = ""
                for msg in final_result['messages']:
                    if isinstance(msg, HumanMessage):
                        role = 'user'
                    else:
                        role = 'ai'
                    conversation += f"{role}: {msg.content}\n\n"
                    system_prompt = """Buat ringkasan percakapan ini dalam 2-3 kalimat maksimal. 
                    Jelaskan inti permasalahan user, apa jawaban dari AI, dan apakah ada indikasi bahwa user butuh bantuan hukum lanjutan atau tidak. To the point, langsung ringkas."""
                prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", conversation)])
                qa_chain = prompt | llm
                chat_summary = qa_chain.invoke({})

            try:
                database = 'watusi_legal_db'
                mydb = mysql.connector.connect(
                    host  = 'localhost',
                    username = 'root',
                    password = 'password',
                    database = database)
                print(f'DB Connected and connected to {database}')

                mycursor = mydb.cursor()

                sql = 'INSERT INTO users (id, username, city, chat_summary) VALUES (%s, %s, %s, %s)'
                values = (thread_id, username.lower(), city.lower(), chat_summary.content)
                mycursor.execute(sql,values)
                mydb.commit()
                print('Data Loaded to DB')
            except Exception as e:
                print(e)
                
            break
        else:
            for chunk in graph.stream({'input': user_input}, config, stream_mode = 'values'):
                final_result = chunk
            # for i in range(len(final_result['messages'])):
            print(thread_id)
                # print(final_result['messages'][i].pretty_print())
            print(final_result['messages'][-1].content)

            
