import time

import streamlit as st
from knowledge_base import *
from streamlit import file_uploader

#add web title

st.title("Smart Cloth Service")

uploader_file = st.file_uploader(
    "please upload a txt file",
    type="txt",
    accept_multiple_files=False,
)

if "service" not in st.session_state:
    st.session_state["service"] = KnowledgeBaseService()

if uploader_file is not None:
    file_name = uploader_file.name
    file_type = uploader_file.type
    file_size = uploader_file.size / 1024

    st.subheader({f"file name: {file_name}"})
    st.write(f"file type: {file_type} | file size: {file_size:.2f} KB" )

    #getvalue
    content = uploader_file.getvalue().decode("utf-8")

    with st.spinner("Uploading file..."):
        time.sleep(3)
        res = st.session_state["service"].str_to_vector(content, file_name)
        st.write(res)
