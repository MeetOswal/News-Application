from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

class QdrantConnect:
    def __init__(self):
        self.client = QdrantClient(
            url="<QDRANT Connection URL>", 
            api_key="<Qdrnat Connection API Key>",
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