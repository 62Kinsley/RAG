## Smart Cloth Service — RAG System Architecture

A Retrieval-Augmented Generation (RAG) system that acts as a smart customer
service assistant for clothing (size recommendation, washing care, color
selection). It answers user questions by retrieving relevant content from a
knowledge base and generating answers with an LLM.

The system has two main flows:

- **Offline flow** — building the knowledge base (ingesting documents into the
  Chroma vector database).
- **Online flow** — answering user questions at query time.

The two flows hand off through the **Chroma vector database**: the offline flow
writes to it, the online flow reads from it. Both sides must use the **same
embedding model** so vector dimensions match.

---

## Tech Stack

- **Language / Framework**: Python, LangChain, Streamlit
- **Vector DB**: ChromaDB
- **Embeddings**: DashScope (`text-embedding-v*`)
- **Text splitting**: `RecursiveCharacterTextSplitter`

---

## Project Files

| File | Role | Flow |
|------|------|------|
| `config_data.py` | Shared configuration (paths, model names, params) | both |
| `data/*.txt` | Raw knowledge documents | offline input |
| `knowledge_base.py` | Knowledge base ingestion service | offline |
| `app_file_upload.py` | Streamlit upload UI | offline entry |
| `vector_stores.py` | Vector store / retriever service | online |
| `rag.py` | Core RAG service (the chain) | online |
| `file_history_store.py` | Conversation history storage | online |
| `app_qa.py` | Streamlit chat UI | online entry |
| `chroma_db/` | Chroma vector database (generated) | shared |
| `md5.txt` | Stored MD5 hashes for de-duplication (generated) | offline |

---

# Offline Flow (Knowledge Base Ingestion)

A user uploads documents through a web page; the documents are de-duplicated,
split into chunks, embedded, and stored in the Chroma vector database.

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
    |                              |   str_to_vector(data, filename) --+--> Chroma
    v   app_file_upload.py         |                                   |    vector DB
+----------------------------+     +-----------------------------------+
| Streamlit Web Service      |                  ^
|                            |                  |
|  st.file_uploader()        |                  |
|        |                   |                  |
|        v                   |                  |
|  getvalue() / decode       |                  |
|        |                   |                  |
|        v                   |                  |
|  st.session_state:         |                  |
|  KnowledgeBaseService -----+------------------+
|  instance                  |
+----------------------------+
```

## Offline Components

### `app_file_upload.py` — Web Layer (Streamlit)

Entry point for knowledge base updates.

- **`st.file_uploader()`** — render the upload widget and receive the file.
- **`getvalue().decode("utf-8")`** — read the raw content of the uploaded file.
- **`st.session_state`** — hold a single `KnowledgeBaseService` instance across
  reruns, so the service (and its Chroma connection) is not rebuilt on every
  page interaction.
- Calls `str_to_vector(data, filename)` to ingest the content.

### `knowledge_base.py` — Core Ingestion Service

Defines `class KnowledgeBaseService`, which ingests content and de-duplicates.

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
       |- not exists -> str_to_vector() -> save_md5()
```

**Ingestion attributes / method:**

- **`self.chroma`** — connection to the Chroma vector database.
- **`self.splitter`** — text splitter that breaks long documents into chunks.
- **`str_to_vector(self, data, filename)`** — main method: de-dup check, split
  the text into chunks, attach metadata, embed, and store into Chroma.

## Offline Data Flow

1. User uploads a file on the Streamlit page.
2. `st.file_uploader()` receives it; `getvalue().decode()` reads the content.
3. A `KnowledgeBaseService` instance (cached in `st.session_state`) handles it.
4. The content's MD5 is computed and checked against `md5.txt`.
5. If new: the text is split into chunks, each chunk gets metadata
   (source, create_time, operator), the chunks are embedded and written to
   Chroma, then the MD5 is saved.
6. If already present: ingestion is skipped.

---

# Online Flow (Question Answering)

A user asks a question in the chat UI; the system retrieves relevant knowledge
from Chroma, combines it with the conversation history, builds a prompt, and
uses an LLM to generate the answer.

```
                                    +-----------------------------+
                                    |   app_qa.py                 |
                                    |   Streamlit Chat UI         |  <--->  User
                                    +-----------------------------+         (Web)
                                                  | invoke
                                                  v
   +-----------------------+        +-------------------------------------+
   | class                 |        |   class RagService (rag.py)         |
   | VectorStoreService    |        |                                     |
   | (vector_stores.py)    |        |   self.vector_service ----+         |
   |                       |        |   self.prompt_template ---+         |
   |   get_retriever()  ---+------> |   self.chat_model --------+--> self.chain
   |   returns a retriever |        |   __get_chain()  ---------+         |
   |   to add to the chain |        |                                     |
   +-----------+-----------+        +------------------+------------------+
               |                                       ^
               v                                       |
        +-------------+                                |
        |   Chroma    | <------------------------------+
        | vector DB   |                                |
        +-------------+                                |
                                    +------------------+------------------+
                                    | class FileChatMessageHistory        |
                                    | (file_history_store.py)             |
                                    |   add_messages()                    |
                                    |   messages                          |
                                    |   clear()                           |
                                    +-------------------------------------+
```

## Online Components

### `vector_stores.py` — `class VectorStoreService`

Manages access to the Chroma vector database for retrieval.

- **`get_retriever()`** — returns a *retriever* object. A retriever takes a user
  query, embeds it, searches Chroma for the most semantically similar chunks,
  and returns them. This retriever is plugged into the chain.

### `rag.py` — `class RagService` (core)

Orchestrates the whole question-answering pipeline.

- **`self.vector_service`** — holds the `VectorStoreService`, used to obtain the
  retriever.
- **`self.prompt_template`** — combines the user's question, the retrieved
  knowledge chunks, and the conversation history into a single prompt.
- **`self.chat_model`** — the LLM that generates the answer.
- **`__get_chain()`** — builds the execution chain.
- **`self.chain`** — the assembled chain. The central piece: it wires together
  retrieval, prompt building, the chat model, and history into one callable
  pipeline. The UI runs the flow by invoking this chain.

### `file_history_store.py` — `class FileChatMessageHistory`

Stores and retrieves the conversation history (persistent chat memory).

- **`add_messages()`** — append new messages (question / answer) to history.
- **`messages`** — read the stored history messages.
- **`clear()`** — clear the stored history.

### `app_qa.py` — Chat UI (Streamlit)

The user-facing entry point.

- Renders the Streamlit chat interface in the browser.
- When the user sends a question, it **invokes** `RagService.chain` and displays
  the generated answer.

## Online Data Flow

1. The user types a question in the Streamlit chat UI (`app_qa.py`).
2. `app_qa.py` invokes `RagService.chain`.
3. The chain runs:
   1. The retriever (from `get_retriever()`) embeds the question and searches
      Chroma for the most relevant chunks.
   2. The conversation history is read from `FileChatMessageHistory`.
   3. `prompt_template` combines the question, retrieved chunks, and history
      into one prompt.
   4. `chat_model` (the LLM) generates the answer.
4. The answer is displayed in the chat UI.
5. The new exchange is saved back into `FileChatMessageHistory` via
   `add_messages()`.

---

# How Offline and Online Connect

```
OFFLINE                          SHARED                       ONLINE
-------                          ------                       ------
upload docs                                                   user question
   |                                                              |
split + embed                                                 embed query
   |                                                              |
   +----------------------> [ Chroma vector DB ] <----------------+
        write chunks                                  retrieve relevant chunks
                                                              |
                                                       build prompt + history
                                                              |
                                                          LLM answer
```

- Offline **writes** embedded knowledge chunks into Chroma.
- Online **reads** from the same Chroma database at query time.
- Chroma is the hand-off point. Both sides must use the **same embedding model**
  so the vector dimensions are consistent.