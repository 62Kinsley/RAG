from langchain_core.output_parsers import StrOutputParser
from histoty_store import get_history
from retriever import RetrieverService
import config_data as config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda
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
                ("system", "and the history of conversation is:  "),
                MessagesPlaceholder("history"),
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
        
        def format_for_retriever(value: dict) -> str:
            return value["input"]

        def format_for_prompt_template(value):
            # {input, context, history}
            new_value = {}
            new_value["input"] = value["input"]["input"]
            new_value["context"] = value["context"]
            new_value["history"] = value["input"]["history"]
            return new_value
        
        chain = (  #(retriever, prompt, llm)
            {
                "input": RunnablePassthrough(),  # Pass the input through to the retriever
                "context": RunnableLambda(format_for_retriever) | retriever | format_document,  # Use the retriever to get relevant context
            } | RunnableLambda(format_for_prompt_template) |self.prompt_template | print_prompt | self.chat_model | StrOutputParser()
        )

        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history",
        )
        return conversation_chain

if __name__ == '__main__':
    #session id
    session_config = {
        "configurable":{
            "session_id": "user_001"
        }
    }
    res = RagService().chain.invoke({"input": "My height is 168cm, and weight 55kg, please recommend size for me "}, config=session_config)
    print(res)