from qdrant_client.models import Filter, FieldCondition, Range
from sklearn.metrics.pairwise  import cosine_similarity
from mongo_initialization import MongoConnection
from qdrant_initialization import QdrantConnect
from datetime import datetime, timedelta
from bson import ObjectId
import numpy as np

class Recommendation:
    def __init__(self):
        self.final_candidate_list = []
        self.mongo = MongoConnection()
        qdrant = QdrantConnect()
        self.user_collection = self.mongo.get_collection('user')
        self.article_collection = self.mongo.get_collection('articles')
        self.qdrant_client = qdrant.getClient()
        self.keywords_collection = self.mongo.get_collection('keywords')
    
    def clean_list(self):
        self.final_candidate_list = []

    def keyword_based_recommendation(self, user_id, prev_rec):
        pipeline = [
            { 
                '$match': { '_id': ObjectId(user_id) }
            },
            { 
                '$project': {
                    'userSelectedPreferences': {
                        '$slice': [{ '$sortArray': { 'input': '$userSelectedPreferences', 'sortBy': { 'score': -1 } } }, 10]
                    },
                    'hiddenPreferences': {
                        '$slice': [{ '$sortArray': { 'input': '$hiddenPreferences', 'sortBy': { 'score': -1 } } }, 10 * min(1+prev_rec, 3)]
                    }
                }
            }
        ]

        result = self.user_collection.aggregate(pipeline)
        top_user_keyword_list = []
        for doc in result:
            top_user_keyword_list.extend([idx['keyword'] for idx in doc['userSelectedPreferences']])
            top_user_keyword_list.extend([idx['keyword'] for idx in doc['hiddenPreferences']])
        
        mongo_query = {
            'keywords': {'$in': top_user_keyword_list}
        }

        mongo_get_articles = self.article_collection.find(mongo_query).sort('date', -1).skip((prev_rec // 2) * 10).limit(30 + (prev_rec) * 10)

        self.final_candidate_list.extend([article['_id'] for article in mongo_get_articles])

    def vector_database_recommendation(self, user_id, prev_rec):

        def find_recency_score_for_user(user_id, decay_rate = -0.15, limit = 10):
            pipeline_exponential_deacy = [{
                    "$match": {
                        "_id": ObjectId(user_id) 
                    }
            },
            {"$addFields" : {
                "newField" : {
                "$map" : {
                    "input" : "$userHistory",
                    "as" : 'hist',
                    "in" : {"$let" : {
                                "vars" : {
                                "recency_score" : {
                                    "$multiply" : ['$$hist.feedback_score',
                                    {
                                        "$exp" : {
                                            "$multiply" : [
                                                decay_rate,
                                                {
                                                    "$dateDiff" : {
                                                        "startDate" : "$$hist.date",
                                                        "endDate" : datetime.now(),
                                                        "unit" : "day"
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                    ]
                                }      
                                },
                                "in" : {
                                'article_id' : "$$hist.article_id",
                                'score' : '$$recency_score'
                                }
                            }
                        }
                    }
                }
            }
        },
        {"$set": {
            "newField": {
                "$slice" : [{
                    "$sortArray": {
                    "input": "$newField",  # The array you want to sort
                    "sortBy": { "score": -1 },  # Sort by 'score' in descending order
                    }
                    },
                    limit + (min(prev_rec, 3) * 10) # limit the output
                ]        
                }
            }
        },{"$project": {
            "newField": 1,
            "_id": 0 
        }
        }]

            result = self.user_collection.aggregate(pipeline_exponential_deacy)

            final_result = next(iter(result))['newField']
            return final_result
        
        articles = [idx['article_id'] for idx in find_recency_score_for_user(user_id)]
        recommendations = []
        date_range = datetime.now() - timedelta(days=4)
        if len(articles) > 0:
            articles_data = self.article_collection.find({"_id" : { "$in" : articles}}, {"embedding" : 1, "_id" : 1})

            for article in articles_data: 
                embedding = article['embedding'][0]
                search_results = self.qdrant_client.search(
                    collection_name="bigData_collection",
                    query_vector=embedding,
                    limit=10 + (prev_rec * 10),
                    offset= (prev_rec // 2) * 10,
                    query_filter = Filter(
                        must = [
                            FieldCondition(
                                key = "date",
                                range = Range(
                                    gte = int(date_range.timestamp())
                                )
                            )
                        ]
                    )
                )
                recommendations.extend([(result.payload['_id'], result.score) for result in search_results if result.score <= 0.82])

            recommendations = sorted(recommendations, key = lambda x: x[1])
            articles = [ObjectId(article) for article, _ in recommendations]
            self.final_candidate_list.extend(articles[:30])

    def user_vector_recommendation(self, user_id, prev_rec):
        user = next(iter(self.user_collection.find({'_id' : ObjectId(user_id)})))
        search_results = self.qdrant_client.search(
            collection_name="bigData_collection",
            query_vector= user['userVector'][0],
            limit= 30 + (prev_rec * 10),
            offset= (prev_rec // 2) * 10
        )
        recommendations = [ObjectId(article.payload['_id']) for article in search_results]
        self.final_candidate_list.extend(recommendations)
    
    def popular_keywords_news_recommendation(self, prev_rec):
        yesterday = datetime.combine(datetime.now().date(), datetime.min.time()) - timedelta(days=1)

        pipeline = [
            {"$unwind": "$last_24_hours"},
            {"$match": {
                "last_24_hours.date": {"$gte": yesterday}
            }},
            {"$group": {
                "_id": "$keyword",
                "total_score": {"$sum": "$last_24_hours.score"}
            }},
            {"$sort": {"total_score": -1}},
            {"$limit": 10 + (min(prev_rec, 5) * 5)}
        ]
        recommendation_keywords = self.keywords_collection.aggregate(pipeline)
        recommendation_keywords = [keyword['_id'] for keyword in recommendation_keywords]

        mongo_query = {
            'keywords': {'$in': recommendation_keywords}
        }
        mongo_get_articles = self.article_collection.find(mongo_query).sort('date', -1).skip((prev_rec // 2) * 10).limit(30 + (prev_rec * 10))
        articles = [article['_id'] for article in mongo_get_articles]

        self.final_candidate_list.extend(articles)
    
    # internal code
    def find_recency_score_for_articles(self, articles, decay_rate = -0.15):
        pipeline_exponential_deacy = [
            {
                "$match" : {
                    "_id" : {"$in" : articles}
                }
            },
            {
                "$addFields" : {
                    "recency_score" : {
                        "$exp" : {
                            "$multiply" : [
                                decay_rate,
                                {
                                    "$dateDiff" : {
                                        "startDate" : "$date",
                                        "endDate" : datetime.now(),
                                        "unit" : "day"
                                    }
                                }
                            ]
                        }
                    }
                }
            },{
                "$project": {
                    "_id": 1,
                    "recency_score": 1
                }
            }
        ]
        return self.article_collection.aggregate(pipeline_exponential_deacy)  

    def re_rank(self, user_id, prev_rec):
        recommendations = list(set(self.final_candidate_list))
        user_data = self.user_collection.find_one({"_id": ObjectId(user_id)}, {"userHistory": {"$slice": -(10 + prev_rec)}, "_id": 0})
        user_history = [article['article_id'] for article in user_data['userHistory']]

        user_embeddings = []
        for embeddings in self.article_collection.find({"_id" : {"$in" : user_history}},{"embedding": 1, "_id" : 0}):
            user_embeddings.append(embeddings['embedding'][0])
        
        user_embeddings = np.array(user_embeddings)

        recommended_embeddings = []
        filtered_recommendations = []
        for embeddings in self.article_collection.find({"_id" : {"$in" : recommendations, "$nin" : user_history}},{"embedding": 1, "_id" : 1}):
            recommended_embeddings.append(embeddings['embedding'][0])
            filtered_recommendations.append(embeddings['_id'])
        
        recommendations = filtered_recommendations
        recommended_embeddings = np.array(recommended_embeddings)

        if user_embeddings.size == 0 or recommended_embeddings.size == 0:
            average_similarity_scores = np.ones(len(recommendations))
        else:
            similarity_scores = cosine_similarity(recommended_embeddings, user_embeddings)  # Shape: (n_recommendations, n_user_history)
            average_similarity_scores = np.mean(similarity_scores, axis=1)  
    
        recency_scores = self.find_recency_score_for_articles(recommendations)
        rec_scores = {}
        for idx in recency_scores:
            rec_scores[idx['_id']] = idx['recency_score']

        final_scores = {}
        for idx, doc_id in enumerate(recommendations):
            cosine_score = average_similarity_scores[idx] # if idx < len(average_similarity_scores) else 0
            r_score= rec_scores[ObjectId(doc_id)]
            if cosine_score > 0: final_scores[doc_id] = r_score / cosine_score
        
        top_recommendations = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        if len(top_recommendations) > 20 and top_recommendations[19][1] <= 0.4:
            prev_rec = -(prev_rec + 1)
        elif len(top_recommendations) < 20 and top_recommendations[-1][1] <= 0.4:
            prev_rec = -(prev_rec + 1)
        elif len(top_recommendations) < 20:
            prev_rec += 1

        top_recommendations = top_recommendations[:10]
        top_recommendations = self.article_collection.find({"_id" : { "$in" : [idx[0] for idx in top_recommendations]}}, {"title" : 1, "summary" : 1, "url" : 1})
        self.clean_list()
        return (top_recommendations, prev_rec)
        
    

