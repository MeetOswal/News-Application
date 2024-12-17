from recommendation import Recommendation


def get_recommendation(userID, prev_rec):
    recommend = Recommendation()
    # userID = '675b80f0b49e0719e0ac4be5'
    recommend.keyword_based_recommendation(userID, prev_rec)
    recommend.vector_database_recommendation(userID, prev_rec)
    recommend.user_vector_recommendation(userID, prev_rec)
    recommend.popular_keywords_news_recommendation(prev_rec)
    result = recommend.re_rank(userID, prev_rec)
    return result

# get_recommendation('675b80f0b49e0719e0ac4be5')        