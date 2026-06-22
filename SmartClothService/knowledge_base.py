import os
import hashlib
from datetime import datetime
import config_data as config
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def check_md5(md5_str : str):
    """"checked if the md5 has been processing"""
    if not os.path.exists(config.md5_path):
        with open(config.md5_path, 'w', encoding= 'utf-8'):
            pass
        return False
    else:
        with open(config.md5_path, 'r', encoding= 'utf-8') as f:
            for line in f:
                line = line.strip() #trim whitespace
                if line == md5_str:
                    return True
            return False

def save_md5(md5_str : str):
    """"save the unsaved md5 hash"""
    with open(config.md5_path, 'a', encoding='utf-8') as f:
        f.write(md5_str + '\n')

def get_string_md5(input : str, encoding = 'utf-8'):
    """"get the md5 hash"""
    #convert str to bytes
    str_to_bytes = input.encode(encoding = encoding)
    #create md5 obj
    md5_obj= hashlib.md5()
    md5_obj.update(str_to_bytes) #add the new bytes
    md5_hex = md5_obj.hexdigest()

    return md5_hex


class KnowledgeBaseService(object):
    embeddings = DashScopeEmbeddings(
            model="text-embedding-v4",
            dashscope_api_key="sk-ws-H.REMXLHX.nivW.MEUCIQDTCKuksYgHNbHA6WreGNMNfi0Rk4_aOnWGb0CfJE9PqQIgWGSnESDyfoHqpuChrccXJZWGXcih9RXSHpC8JvSJydA",
    )
    os.makedirs(config.persist_dir, exist_ok=True) #check if  persist_dir is exist

    def __init__(self):
        self.chroma = Chroma(  #chroma object
            collection_name=config.collection_name, #the name of database
            embedding_function = self.embeddings,
            persist_directory=config.persist_dir
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=0,
            separators=config.separators,
            length_function= len,
            ) #textspliter

    def str_to_vector(self,data, filename):
        """"convert string to vector"""
        md5_hex = get_string_md5(data)

        if check_md5(md5_hex):
            return "sorry, it has been saved"
        if len(data) > config.max_length:
            knowledge_chunks: list[str] = self.splitter.split_text(data)
        else:
            knowledge_chunks = [data]

        metadata = {
            "source" : filename,
            "create_time" : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator" : "kk",
        }

        metadatas = []
        for _ in knowledge_chunks:
            metadatas.append(metadata)

        self.chroma.add_texts(
            knowledge_chunks,
            metadatas = metadatas,
        )

        save_md5(md5_hex)

        return "it has been uploaded to chroma knowledge successfully"

if __name__ == '__main__':
    service = KnowledgeBaseService()
    res = service.str_to_vector("jolin", "testfile")
    print(res)
