from pymongo import MongoClient

class MongoConnection:
    def __init__(self):
        connection_string = "<Mongo Connection URL>"
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

