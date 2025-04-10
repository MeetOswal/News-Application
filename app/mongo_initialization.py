from pymongo import MongoClient
import os
from dotenv import load_dotenv
class MongoConnection:
    def __init__(self):
        load_dotenv()
        connection_string = os.getenv("MONGO_URI")
        self.client = MongoClient(connection_string)
        self.db = self.client['bigData']
        self.collection = None

    def get_collection(self, collection = "articles"): # 'user', 'keywords'
        self.collection = self.db[collection]
        return self.collection
    
    def close(self):
        self.client.close()
    
# connect = MongoConnection()
# user = connect.get_collection("articles")

