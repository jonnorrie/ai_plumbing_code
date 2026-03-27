import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

PDF_PATH = "NPC_2020.pdf"

def ingest():
    print("Loading PDF...")
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()
    print(f"Loaded {len(documents)} pages")

    print("Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")

    print("Uploading to Pinecone...")
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

    # Upload in batches
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        vectors = []
        for j, chunk in enumerate(batch):
            embedding = pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=[chunk.page_content],
                parameters={"input_type": "passage"}
            )
            vectors.append({
                "id": f"chunk-{i+j}",
                "values": embedding[0].values,
                "metadata": {"text": chunk.page_content}
            })
        index.upsert(vectors=vectors)
        print(f"Uploaded chunks {i} to {i+len(batch)}")