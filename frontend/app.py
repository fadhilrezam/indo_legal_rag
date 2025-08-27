import streamlit as st
import os
import uuid
import requests
import json 
import time

base_dir = os.path.dirname(__file__)
logo_image = os.path.join(base_dir,'logo.png')

col1,col2,col3 = st.columns([0.5,5,0.5])
with col2:
    st.image(logo_image, use_container_width=True)
with col2:
    st.title('Watusi Legal Insight Chatbot')
st.write('')


#-------------------------------FORM USER----------------------------------------#
if 'user_info' not in st.session_state:
    with st.form ('user_info_form'):
        st.subheader("Sebelum memulai, isi informasi berikut:")
        username = st.text_input('Nama Lengkap')
        no_telp = st.text_input('No Telepon (Bisa di hubungi via Whatsapp')
        domisili = st.text_input('Domisili (Kota/Kabupaten)')
        submitted = st.form_submit_button('Submit')
        if submitted:
            if not (username and no_telp and domisili):
                st.warning('Semua form wajib diisi.')
            elif not no_telp.isdigit():
                st.warning('Nomor telepon hanyaboleh berisi angka tanpa spasi atau simbol.')
            else:
                st.session_state.user_info = {
                    "username" : username,
                    "no_telp" : no_telp,
                    "domisili" : domisili
                }
                st.rerun()
    st.stop() 

#-------------------------------CHAT BOT SESSION----------------------------------------#
#Inisialisasi session_state
if 'chat_id' not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4()).replace('-','_')
if 'messages' not in st.session_state:
    st.session_state.messages = [
         {'role': 'ai', 'content': f'Halo {st.session_state.user_info["username"].upper()}! Watusi Legal Insight siap bantu kamu pahami isu hukum dengan cara yang lebih sederhana.'}]

st.write(f"Chat ID: {st.session_state.chat_id}")

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.write(msg['content'])

# User input
user_input = st.chat_input('Tanyakan Apapun')
if user_input: ## := is operator to assign the user's input the the prompt var and checked if it's not None
    #Display user message in chat message container
    with st.chat_message('user'):
        # st.markdown(prompt)
        st.write(user_input)
    st.session_state.messages.append({'role': 'user', 'content': user_input})
        
    #send datas to backend
    payload = {
        "chat_id": st.session_state.chat_id,
        "question": user_input
    }
    #set header to tell server that sended data is formatted in JSON 
    headers = {"Content-Type": "application/json"}

    with st.chat_message('ai'):
        try:
            url = requests.post('http://localhost:5000/chat', data = json.dumps(payload), headers = headers)
            response = url.json()['answer']

            st.write(response)
            st.session_state.messages.append({'role': 'ai', 'content': response})

        except:
            response = "Maaf, terjadi kesalahan saat mengambil jawaban dari server."
            st.error(response)

if any(msg['role'] == 'user' for msg in st.session_state.messages):
    st.markdown ('---')
    trigger = st.button('🔚 Akhiri Chat')
    if trigger:
        conversation = ""
        # st.write(st.session_state.messages)
        for msg in st.session_state.messages[1:]:
            role = msg['role']
            content = msg['content']
            conversation += f"{role}: {content}\n\n"

        #send datas to backend
        end_payload = {
        "chat_id": st.session_state.chat_id,
        "username": st.session_state.user_info["username"],
        "no_telp": st.session_state.user_info["no_telp"],
        "domisili": st.session_state.user_info["domisili"],
        "conversation": conversation
        }
        #set header to tell server that sended data is formatted in JSON 
        headers = {"Content-Type": "application/json"}
        url = requests.post('http://localhost:5000/end_chat', data = json.dumps(end_payload), headers = headers)
        st.session_state.clear()
        st.rerun()


