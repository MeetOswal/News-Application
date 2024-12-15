from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

class QdrantConnect:
    def __init__(self):
        self.client = QdrantClient(
            url="https://ebc8b276-71dc-4b06-9303-2ced3445a1ec.us-east4-0.gcp.cloud.qdrant.io:6333", 
            api_key="5oIorWxl94DrfMOzfZzrK9xkM5sGQ_1FohJWCqBFZI-NWqXX2-LDJQ",
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