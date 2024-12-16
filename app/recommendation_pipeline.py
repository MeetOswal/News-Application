from recommendation import Recommendation


def get_recommendation(userID):
    recommend = Recommendation()
    # userID = '675b80f0b49e0719e0ac4be5'
    recommend.keyword_based_recommendation(userID)
    recommend.vector_database_recommendation(userID)
    recommend.user_vector_recommendation(userID)
    recommend.popular_keywords_news_recommendation()
    result = recommend.re_rank(userID)
    return result

# get_recommendation('675b80f0b49e0719e0ac4be5')        