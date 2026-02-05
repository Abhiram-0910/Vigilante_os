import chromadb
from chromadb.utils import embedding_functions

# Setup Local Vector DB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="scam_knowledge_base")

def learn_interaction(scam_text: str, successful_reply: str, scam_type: str):
    """
    Stores a winning interaction into the Vector Brain.
    """
    collection.add(
        documents=[scam_text],
        metadatas=[{"reply": successful_reply, "type": scam_type}],
        ids=[str(hash(scam_text + successful_reply))]
    )

def recall_past_experience(current_message: str):
    """
    Queries the brain: 'Have we seen this before?'
    """
    results = collection.query(
        query_texts=[current_message],
        n_results=1
    )
    
    if results['documents'][0]:
        past_reply = results['metadatas'][0][0]['reply']
        return f"MEMORY RECALL: I faced this before. Successful reply was: '{past_reply}'"
    return None