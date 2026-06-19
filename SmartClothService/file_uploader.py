import streamlit as st
from streamlit import file_uploader

#add web title

st.title("Smart Cloth Service")

uploader_file = st.file_uploader(
    "please upload a txt file",
    type="txt",
    accept_multiple_files=False,
)

if uploader_file is not None:
    file_name = uploader_file.name
    file_type = uploader_file.type
    file_size = uploader_file.size / 1024

    st.subheader({f"file name: {file_name}"})
    st.write(f"file type: {file_type} | file size: {file_size:.2f} KB" )

    #getvalue
    content = uploader_file.getvalue().decode("utf-8")
    st.write(content)

