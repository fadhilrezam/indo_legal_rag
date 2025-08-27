import os
import re
import traceback
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_mistralai import MistralAIEmbeddings
from langchain_chroma import Chroma
import json

def load_and_parse_docs():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        folder_path = os.path.abspath(os.path.join(current_dir, '..', 'documents'))

        noise_patterns = [
            r'www\.hukumonline\.com',
            r'\nMenemukan kesalahan ketik dalam dokumen\?\nKlik di sini\nuntuk perbaikan.'
        ]
        all_docs = []

        for file in os.listdir(folder_path):
            if file.endswith('.pdf'):
                try:
                    file_path = os.path.join(folder_path, file)
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()  # perbaikan dari .doad()
                    for doc in docs:
                        for noise in noise_patterns:
                            doc.page_content = re.sub(noise, '', doc.page_content)
                    all_docs.extend(docs)
                except Exception as e:
                    print(f"Error saat memproses file: {file_path}")
                    traceback.print_exc()

        full_text = ''.join(page.page_content for page in all_docs)

        document_title_pattern = r'kitab\s+undang-undang\s+hukum\s+perdata'
        document_title = re.search(document_title_pattern, full_text, re.IGNORECASE) 
        if not document_title:
            raise ValueError("Judul dokumen tidak ditemukan.")
        document_title = document_title.group(0)

        list_buku = []
        docs = []

        buku_chunks = re.split(r'(?=BUKU\s+KE\w+)', full_text)
        for buku in buku_chunks:
            try:
                buku_pattern = r'(BUKU\s+KE\w+).*'
                buku_match = re.search(buku_pattern, buku, re.DOTALL)
                if not buku_match:
                    continue
                buku_judul = buku_match.group(1)
                list_buku.append(buku_judul)

                bab_chunks = re.split(r'(?=BAB\s+[IVXLCDM]+[A-Z]?)', buku)
                for bab in bab_chunks:
                    try:
                        bab_pattern = r'(BAB\s+[IVXLCDM]+[A-Z]?)\s*\n(.*?)\s*\n(.*)'
                        bab_match = re.search(bab_pattern, bab, re.DOTALL)
                        if not bab_match:
                            continue
                        bab_number = bab_match.group(1).strip()
                        bab_title = re.sub(r'\s*\n\s*',' ', bab_match.group(2).strip())

                        if 'BAGIAN' in bab:
                            bagian_chunks = re.split(r'(?=BAGIAN\s+[0-9]+)', bab)
                            for bagian in bagian_chunks:
                                try:
                                    bagian_pattern = r'(BAGIAN\s+[0-9]+)\s*\n*(.*?)\s*\n\s*\n(.*)'
                                    bagian_match = re.search(bagian_pattern, bagian, re.DOTALL)
                                    if not bagian_match:
                                        continue
                                    bagian_number = bagian_match.group(1).strip()
                                    bagian_title = bagian_match.group(2).strip()

                                    pasal_chunks = re.split(r'(?=Pasal\s+[0-9]+[a-z]?)', bagian, re.DOTALL)
                                    for pasal in pasal_chunks:
                                        pasal_pattern = r'(Pasal\s+[0-9]+[a-z]?)\s*\n(.*)'
                                        pasal_match = re.search(pasal_pattern, pasal, re.DOTALL)
                                        if not pasal_match:
                                            continue
                                        pasal_number = pasal_match.group(1).strip()
                                        pasal_content = pasal_match.group(2).strip()

                                        doc = Document(
                                            page_content=
                                                f"Dokumen: {document_title}\n"
                                                f"Bab: {bab_number} - {bab_title}\n"
                                                f"Bagian: {bagian_number} - {bagian_title}\n"
                                                f"Pasal: {pasal_number}\n"
                                                f"Isi Pasal: {pasal_content}",
                                            metadata={
                                                'document_type': 'legal_document',
                                                'document_title': f"{document_title} {buku_judul}",
                                                'bab_number': bab_number,
                                                'bab_title': bab_title,
                                                'bagian': bagian_number,
                                                'bagian_title': bagian_title,
                                                'pasal': pasal_number
                                            }
                                        )
                                        docs.append(doc)
                                except Exception as e:
                                    print(f"Error saat memproses bagian di {bab_number}: {e}")
                                    traceback.print_exc()
                        else:
                            pasal_chunks = re.split(r'(?=Pasal\s+[0-9]+[a-z]?)', bab, re.DOTALL)
                            for pasal in pasal_chunks:
                                pasal_pattern = r'(Pasal\s+[0-9]+[a-z]?)\s*\n(.*)'
                                pasal_match = re.search(pasal_pattern, pasal, re.DOTALL)
                                if not pasal_match:
                                    continue
                                pasal_number = pasal_match.group(1).strip()
                                pasal_content = pasal_match.group(2).strip()

                                doc = Document(
                                    page_content=
                                        f"Dokumen: {document_title}\n"
                                        f"Bab: {bab_number} - {bab_title}\n"
                                        f"Bagian: \n"
                                        f"Pasal: {pasal_number}\n"
                                        f"Isi Pasal: {pasal_content}",
                                    metadata={
                                        'document_type': 'legal_document',
                                        'document_title': f"{document_title} {buku_judul}",
                                        'bab_number': bab_number,
                                        'bab_title': bab_title,
                                        'bagian': '',
                                        'bagian_title': '',
                                        'pasal': pasal_number
                                    }
                                )
                                docs.append(doc)
                    except Exception as e:
                        print(f"Error saat memproses bab: {e}")
                        traceback.print_exc()
            except Exception as e:
                print(f"Error saat memproses buku: {e}")
                traceback.print_exc()

        return docs  # <= DI SINI HASILNYA DIKEMBALIKAN

    except Exception as e:
        print("Terjadi error di proses utama:")
        traceback.print_exc()
        return []  # fallback kalau error total

def store_docs_to_vector_db(model_name, mistral_api, collection_name, docs):
    try:
        embedding_model = MistralAIEmbeddings(
        model = model_name,
        api_key=mistral_api)
        if embedding_model:
            vector_store = Chroma(
                embedding_function = embedding_model,
                persist_directory = '.\pipeline\chroma_db',
                collection_name = collection_name)
            vector_store.add_documents(docs)
            print(f"{len(docs)} dokumen berhasil disimpan ke vectorstore.")
        else:
            print('Embedding Model Gagal di Load')
    except Exception as e:
        print('Terjadi error:')
        traceback.print_exc()
        print(e)
        


if __name__ == '__main__':
    print('Proses Parsing Dokumen')
    docs = load_and_parse_docs()
    print(f"Jumlah dokumen hasil ekstraksi: {len(docs)}")
    
    # Run the code below if your vector database is not yet built or stored.
    '''current_dir = os.path.dirname(os.path.abspath(__file__))
    credentials_path = os.path.abspath(os.path.join(current_dir, '..', 'credentials.json'))
    if credentials_path:
        with open(credentials_path, 'r') as f:
            data = json.load(f)
        mistral_api = data['mistral_api']
    model_name = 'mistral-embed'
    collection_name = 'kuhperdata_mistral'
    print('Proses Penyimpanan Dokumen Ke Vector DB')
    store_docs_to_vector_db(model_name, mistral_api, collection_name, docs)'''


