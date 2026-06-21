md5_path = "./md.text"

#chroma
collection_name ="rag"
persist_dir = "./chroma_db"

#textspliter
separators = ["\n\n", "\n", ".", "!", "?", " ",""]
max_length = 1000  #max splitter number

#retriever
top_k= 1

#rag
embedding_model = "text-embedding-v4"
dashscope_api_key = "sk-ws-H.REMXLHX.nivW.MEUCIQDTCKuksYgHNbHA6WreGNMNfi0Rk4_aOnWGb0CfJE9PqQIgWGSnESDyfoHqpuChrccXJZWGXcih9RXSHpC8JvSJydA"
chat_model = "qwen-max"
