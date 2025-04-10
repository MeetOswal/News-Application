from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
import os
from dotenv import load_dotenv
class QdrantConnect:
    def __init__(self):
        load_dotenv()
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URI"), 
            api_key=os.getenv("QDRANT_KEY"),
        )
    
    def create_collection(self, name, embedding_size = 1024):
        if not self.client.collection_exists(name):
            self.client.create_collection(
                    collection_name= name,
                    vectors_config=VectorParams(size=embedding_size, distance=Distance.COSINE),
            )

    def getClient(self):
        return self.client

# connect = QdrantConnect()
# client = connect.getClient()