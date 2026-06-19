# Clothing Smart Customer Service — RAG System

A Retrieval-Augmented Generation (RAG) system that answers clothing-related
questions (size recommendation, washing care, color selection) by retrieving
from a knowledge base and generating answers with an LLM.

The system has two main flows: an **offline flow** for building the knowledge
base, and an **online flow** for answering user questions. This document
describes the **offline flow**.

---

## Offline Flow (Knowledge Base Ingestion)

The offline flow lets a user upload documents through a web page; the documents
are de-duplicated, split into chunks, embedded, and stored in a Chroma vector
database.

```
                                    +-----------------------------------+
                                    |   Class KnowledgeBaseService      |
                                    |   (knowledge_base.py)             |
   User                            |                                   |
    |                              |   check_md5()    ----+            |
    v                              |   save_md5()     ----+--> md5.txt |
+----------------+                 |   get_string_md5(str)             |
| Web page:      |                 |                                   |
| upload file    |                 |   self.chroma                     |
+----------------+                 |   self.splitter                   |
    |                              |   upload_by_str(data, filename) --+--> Chroma
    v   app_file_upload.py         |                                   |    vector DB
+----------------------------+     +-----------------------------------+
| Streamlit Web Service      |                  ^
|                            |                  |
|  st.file_uploader()        |                  |
|        |                   |                  |
|        v                   |                  |
|  uploader_file.get_value() |                  |
|        |                   |                  |
|        v                   |                  |
|  st.session_state:         |                  |
|  KnowledgeBaseService -----+------------------+
|  instance                  |
+----------------------------+

                config_data.py  (shared configuration)
```

---

## Components

### 1. `app_file_upload.py` — Web Layer (Streamlit)

The entry point for knowledge base updates. Responsibilities:

- **`st.file_uploader()`** — render the upload widget and receive the file.
- **`uploader_file.get_value()`** — read the raw content of the uploaded file.
- **`st.session_state`** — hold a single `KnowledgeBaseService` instance across
  reruns, so the service (and its Chroma connection) is not rebuilt on every
  page interaction.
- Call `KnowledgeBaseService.upload_by_str(data, filename)` to ingest content.

### 2. `knowledge_base.py` — Core Service Layer

Defines `class KnowledgeBaseService`, which performs ingestion and
de-duplication.

**MD5 de-duplication** (prevents the same content from being stored twice):

- **`get_string_md5(str)`** — compute the MD5 hash of the file content.
- **`check_md5()`** — check whether this MD5 already exists in `md5.txt`.
- **`save_md5()`** — record a new MD5 into `md5.txt` after successful ingestion.

De-dup logic:

```
upload file
  -> compute MD5 of content
  -> check_md5()
       |- exists     -> already ingested, skip
       |- not exists -> upload_by_str() -> save_md5()
```

**Ingestion attributes / method:**

- **`self.chroma`** — connection / client to the Chroma vector database.
- **`self.splitter`** — text splitter that breaks documents into chunks.
- **`upload_by_str(self, data, filename)`** — main method: split the text into
  chunks, embed them, and store them into the Chroma vector DB.

### 3. `config_data.py` — Shared Configuration

Configuration shared by both files: model names, API keys, file paths,
chunk size, vector DB location, and similar parameters.

---

## Data Flow Summary

1. User uploads a file on the Streamlit page.
2. `st.file_uploader()` receives it; `get_value()` reads the content.
3. A `KnowledgeBaseService` instance (cached in `st.session_state`) handles it.
4. The content's MD5 is computed and checked against `md5.txt`.
5. If new: the text is split, embedded, and written to the Chroma vector DB,
   then the MD5 is saved.
6. If already present: ingestion is skipped.