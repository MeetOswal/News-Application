from transformers import pipeline, BartTokenizer, BartModel, logging
from transformers import BartForConditionalGeneration
import numpy as np
from bson import ObjectId

class Model:
    def search(self, client, collection, query):
        # Load the tokenizer and model
        tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
        model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn").to("cuda")

        # Helper function to generate embeddings for the query
        def embed_query(query):
            tokens = tokenizer(query, return_tensors='pt', truncation=True, padding=True, max_length=1024)
            tokens = {key: value.to('cuda') for key, value in tokens.items()}
            with torch.no_grad():
                outputs = model.model.encoder(**tokens)
            embeddings = outputs.last_hidden_state
            query_vector = embeddings.mean(dim=1).detach().cpu().numpy()
            return query_vector

        # Generate query embeddings
        query_embedding = embed_query(query).flatten()

        # Search in Qdrant vector database
        search_results = client.search(
            collection_name="bigData_collection",
            query_vector=query_embedding.tolist(),
            limit=5  # Fetch top 5 documents
        )

        # Extract document IDs from the search results
        document_ids = [result.payload["_id"] for result in search_results]

        # Query MongoDB for documents corresponding to the IDs
        documents = list(collection.find(
            {"_id": {"$in": [ObjectId(doc_id) for doc_id in document_ids]}},
            {"_id": 1, "summary": 1, "url": 1}
        ))

        # Check if documents are found
        if not documents:
            return "No relevant documents found for your query."

        # Extract summaries and URLs from the documents
        summaries = [doc["summary"] for doc in documents if "summary" in doc]
        urls = [doc["url"] for doc in documents if "url" in doc]

        # Combine the summaries into a single context
        combined_summaries = " ".join(summaries)

        # Generate a response using the BART model
        input_text = f"Query: {query}\nContext: {combined_summaries}"
        input_tokens = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=1024).to("cuda")
        
        with torch.no_grad():
            generated_ids = model.generate(input_tokens["input_ids"], max_length=200, num_beams=4, early_stopping=True)
        
        response_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

        # Append URLs to the response
        url_texts = [f"[For More Information, Click here]({url})" for url in urls]
        final_response = response_text + "\n\n" + "\n".join(url_texts)

        return final_response

from qdrant_client.http.models import PointStruct
from pymongo.errors import BulkWriteError
from datasets import Dataset
from datetime import datetime
from bson import ObjectId
import torch
import uuid

logging.set_verbosity_error()

class Model:
    def __init__(self):
        self.data = {
            'article' : [],
            'date' : [],
            'url' : [],
            'title': [],
            'source_location' : [],
            'concepts' : [],
            'uri' : []
        }
        self.dataset = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device= self.device)
        self.tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
        self.model = BartModel.from_pretrained('facebook/bart-large').to(self.device)
        self.retrieved_documents = None

    def transform(self, raw_data, article_collection):
        for row in raw_data:
            if article_collection.find_one({'uri' : row['uri']}) is None:
                self.data['article'].append(row['body'])
                self.data['date'].append(datetime.strptime(row['date'], "%Y-%m-%d").date())
                self.data['url'].append(row['url'])
                self.data['title'].append(row['title'])
                self.data['uri'].append(row['uri'])
                if row['source']['location']['type'] == 'place':
                    self.data['source_location'].append(row['source']['location']['country']['label']['eng'])
                else:
                    self.data['source_location'].append(row['source']['location']['label']['eng'])
                concepts = []
                for concept in row['concepts']:
                    if concept['score'] >= 4:
                        concepts.append(concept['label']['eng'])
                    if len(concepts) < 1:
                        for concept in row['concepts']:
                            if concept['score'] >= 3:
                                concepts.append(concept['label']['eng'])           
                self.data['concepts'].append(concepts)
        self.dataset = Dataset.from_dict(self.data)
    
    def summarize(self):
        def split_text_into_chunks(text, max_tokens):
            tokens = self.tokenizer(text, return_tensors="pt", padding= True)
            num_tokens = len(tokens['input_ids'][0])
            
            chunks = []
            for i in range(0, num_tokens, max_tokens):
                chunk = self.tokenizer.decode(tokens['input_ids'][0][i:i+max_tokens], skip_special_tokens=True)
                chunks.append(chunk)
            return chunks
        
        def summarize_article(article):
            chunks = split_text_into_chunks(article, 728)
            summaries = []
            for chunk in chunks:
                summary = self.summarizer(chunk, max_length= 140, do_sample=False)
                summaries.append(summary[0]['summary_text'])

            final_summary = " ".join(summaries)

            return final_summary
        def summary_tokenizer(summary):
            inputs = self.tokenizer(summary, return_tensors='pt', truncation=True, padding=True, max_length=128)
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state
            vector = embeddings.mean(dim=1).detach().cpu().numpy()
            return vector

        def batch_summarize(batch):
            summaries = [summarize_article(article) for article in batch['article']]
            return {'summary': summaries}

        def batch_embedding(batch):
            embeddings = [summary_tokenizer(summary) for summary in batch['summary']]
            return {'embeddings' : embeddings}

        print("Generating Summary...")
        self.dataset = self.dataset.map(batch_summarize, batched= True, batch_size= 10)
        print('Generated Summary, Generating Embeddings...')
        self.dataset = self.dataset.map(batch_embedding, batched= True, batch_size= 10)

    def insert_to_mongo(self, keywords_col, articles_col):
        documents = []
        keywords = []
        for row in self.dataset:
            document = {
                "date": datetime.combine(row['date'], datetime.min.time()),
                "url": row["url"],
                "title": row["title"],
                "summary": row["summary"],
                "keywords": row["concepts"],
                "uri" : row['uri'],
                "source" : row['source_location'],
                "embedding" : row['embeddings']
            }
            for key in row["concepts"]:
                keywords.append({
                    "keyword" : key,
                    "last_24_hours" : [{"date": datetime.combine(datetime.now().date(), datetime.min.time()), "score": 0}] * 25
                })
            documents.append(document)
        try:
            if len(documents) > 0:
                inserted_documents = articles_col.insert_many(documents, ordered=False)
                inserted_ids = inserted_documents.inserted_ids
                query = {'_id': {'$in': inserted_ids}}
                projection = {'_id': 1, 'embedding': 1, 'date' : 1}   
                self.retrieved_documents = articles_col.find(query, projection)
                keywords_col.insert_many(keywords, ordered=False)

        except BulkWriteError as bwe:
            print(f'Documents Already present')
        
    def insert_to_qdrant(self, client, collection_name):
        try:
            data_points = [PointStruct(id= str(uuid.uuid4()), vector= value['embedding'][0], payload= { "_id" : str(value['_id']), "date" : int(value['date'].timestamp())}) for value in self.retrieved_documents]
            if len(data_points) > 0:
                _ = client.upsert(
                    collection_name = collection_name,
                    wait = True,
                    points = data_points
                )
            else:
                print("No Data to Send")
        except Exception as e:
            print('No Document to Send - exception')

    def search(self, client, collection, query):
        # Load the tokenizer and model
        tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
        model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn").to("cuda")

        # Helper function to generate embeddings for the query
        def embed_query(query):
            tokens = tokenizer(query, return_tensors='pt', truncation=True, padding=True, max_length=1024)
            tokens = {key: value.to('cuda') for key, value in tokens.items()}
            with torch.no_grad():
                outputs = model.model.encoder(**tokens)
            embeddings = outputs.last_hidden_state
            query_vector = embeddings.mean(dim=1).detach().cpu().numpy()
            return query_vector

        # Generate query embeddings
        query_embedding = embed_query(query).flatten()

        # Search in Qdrant vector database
        search_results = client.search(
            collection_name="bigData_collection",
            query_vector=query_embedding.tolist(),
            limit=5  # Fetch top 5 documents
        )

        # Extract document IDs from the search results
        document_ids = [result.payload["_id"] for result in search_results]

        # Query MongoDB for documents corresponding to the IDs
        documents = list(collection.find(
            {"_id": {"$in": [ObjectId(doc_id) for doc_id in document_ids]}},
            {"_id": 1, "summary": 1, "url": 1}
        ))

        # Check if documents are found
        if not documents:
            return "No relevant documents found for your query."

        # Extract summaries and URLs from the documents
        summaries = [doc["summary"] for doc in documents if "summary" in doc]
        urls = [doc["url"] for doc in documents if "url" in doc]

        # Combine the summaries into a single context
        combined_summaries = " ".join(summaries)

        # Generate a response using the BART model
        input_text = f"Query: {query}\nContext: {combined_summaries}"
        input_tokens = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=1024).to("cuda")
        
        with torch.no_grad():
            generated_ids = model.generate(input_tokens["input_ids"], max_length=200, num_beams=4, early_stopping=True)
        
        response_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

        # Append URLs to the response
        url_texts = [f"[For More Information, Click here]({url})" for url in urls]
        final_response = response_text + "\n\n" + "\n".join(url_texts)

        return final_response