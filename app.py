import streamlit as st
from langchain_openai import ChatOpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
import os

load_dotenv()

# Page config
st.set_page_config(
    page_title="National Plumbing Code Assistant",
    page_icon="🔧",
    layout="centered"
)

st.title("🔧 National Plumbing Code Assistant")
st.caption("Ask any question about the National Plumbing Code of Canada")

@st.cache_resource
def load_resources():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return pc, index, llm

pc, index, llm = load_resources()

def search_plumbing_code(query, k=5):
    embedding = pc.inference.embed(
        model="llama-text-embed-v2",
        inputs=[query],
        parameters={"input_type": "query"}
    )
    results = index.query(
        vector=embedding[0].values,
        top_k=k,
        include_metadata=True
    )
    return results.matches

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask about the plumbing code..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching the plumbing code..."):

            # Retrieve relevant chunks
            matches = search_plumbing_code(prompt)
            context = "\n\n".join([m.metadata["text"] for m in matches])

            # Build messages
            messages = [
                ("system", f"""You are a helpful assistant that answers questions about the
                National Plumbing Code of Canada. Use the following context to answer the question.
                If you don't know the answer, say so clearly. Always cite the section number if visible.

                Context:
                {context}""")
            ]

            # Add chat history
            for msg in st.session_state.messages[:-1]:
                if msg["role"] == "user":
                    messages.append(("human", msg["content"]))
                else:
                    messages.append(("assistant", msg["content"]))

            messages.append(("human", prompt))

            response = llm.invoke(messages)
            answer = response.content

            st.write(answer)

            # Show sources
            if matches:
                with st.expander("📄 Sources"):
                    for i, match in enumerate(matches):
                        st.markdown(f"**Chunk {i+1}** — score: {match.score:.2f}")
                        st.caption(match.metadata["text"][:300] + "...")
                        st.divider()

    st.session_state.messages.append({"role": "assistant", "content": answer})