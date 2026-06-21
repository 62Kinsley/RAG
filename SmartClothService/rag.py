from langchain_core.output_parsers import StrOutputParser

from retriever import RetrieverService
from langchain_community.embeddings import DashScopeEmbeddings
import config_data as config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents  import Document
from langchain_qwq import ChatQwen


def print_prompt(prompt):
    print("=" * 20)
    print(prompt.to_string())
    print("=" * 20)

    return prompt
class RagService(object):

    def __init__(self):
       
        self.vector_service = RetrieverService()
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful AI bot. and has the knowledge of fashion :{context}, you can answer the question based on the retrieved information. If the retrieved information is not relevant to the question, please answer based on your own knowledge."),
                ("human", "{input}")
            ]
        )
        
        self.chat_model = ChatQwen(
            model=config.chat_model,
            api_key=config.dashscope_api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        self.chain = self._get_chain()



    def _get_chain(self):

        retriever = self.vector_service.get_retriever()
        
        def format_document(docs: list[Document]) -> str:
            if not docs:
                return "No relevant information found."
            formatted_docs = []
            for doc in docs:
                formatted_docs.append(f"Content: {doc.page_content}\nMetadata: {doc.metadata}\n\n")
            return "\n".join(formatted_docs)
        
        chain = (  #(retriever, prompt, llm)
            {
                "input": RunnablePassthrough(),  # Pass the input through to the retriever
                "context": retriever | format_document,  # Use the retriever to get relevant context
            } | self.prompt_template | print_prompt | self.chat_model | StrOutputParser()
        )

        return chain 
    

if __name__ == '__main__':
    res = RagService().chain.invoke("My height is 168cm, and weight 55kg, please recommend size for me ")
    print(res)