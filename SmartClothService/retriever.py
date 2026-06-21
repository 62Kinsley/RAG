from langchain_chroma import Chroma
import config_data as config
from langchain_community.embeddings import DashScopeEmbeddings

class RetrieverService():

    def __init__(self):
        embedding = DashScopeEmbeddings(
            model="text-embedding-v4",
            dashscope_api_key="sk-ws-H.REMXLHX.nivW.MEUCIQDTCKuksYgHNbHA6WreGNMNfi0Rk4_aOnWGb0CfJE9PqQIgWGSnESDyfoHqpuChrccXJZWGXcih9RXSHpC8JvSJydA",
        )
        self.embedding = embedding
        self.vector_store  = Chroma(  #chroma object
            collection_name = config.collection_name, #the name of database
            embedding_function = self.embedding,
            persist_directory=config.persist_dir
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": config.top_k})


if __name__ == '__main__':
    service = RetrieverService()
    retriever= service.get_retriever()
    res = retriever.invoke("My height is 162cm, and weight 55kg, please recommend size for me ")
    print(res)