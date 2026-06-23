import streamlit as st
import time
from rag import RagService
import config_data as config



#title
st.title("Smart Customer Service ")
st.divider()


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hello! How can I assist you today?"}]

if "rag" not in st.session_state:
    st.session_state["rag"] = RagService()


for message in st.session_state["messages"]:
    if message["role"] == "assistant":
        st.chat_message("assistant").write(message["content"])
    else:
        st.chat_message("user").write(message["content"])


#user input
prompt = st.chat_input("How can I help you today?")

if prompt:
    # Display user message in chat message container
    st.chat_message("user").write(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})
    
    with st.spinner("Generating response..."):
        time.sleep(1)  # Simulate a delay for generating response
        res = st.session_state["rag"].chain.invoke({"input": prompt}, config=config.session_config)
        st.chat_message("assistant").write(res)
        st.session_state["messages"].append({"role": "assistant", "content": res})

  