from eventregistry import EventRegistry, QueryArticlesIter, ReturnInfo, ArticleInfoFlags, SourceInfoFlags, QueryEventsIter, QueryItems

class APISource:
    def __init__(self):
        """
        Initializes the EventRegistry object and prepares containers to store events,
        concepts (topics), article results, and a set to track article URIs.
        """
        self.er = EventRegistry(apiKey = '<API Key>')
        self.events_result = []
        self.concepts = [] 
        self.result = []
        self.result_uri = set()

    def get_events(self, country= "United States"):
        """
        Fetches events from a specified country using EventRegistry API.

        Parameters:
        - country (str): Name of the country to fetch events for. Defaults to 'United States'.

        This method performs two separate queries:
        1. Events sorted by date (latest events)
        2. Events sorted by social score (most popular events)
        """
        country = country.replace(" ", "_")
        print(country)
        q = QueryEventsIter(
        sourceLocationUri = "http://en.wikipedia.org/wiki/United_States", # => Get Events in Unisted States
        lang = 'eng',
        )
        
        for events in q.execQuery(self.er, sortBy= 'date', sortByAsc= False, maxItems=20): # => Latest / New Events
            self.events_result.append(events)

        for events in q.execQuery(self.er, sortBy='socialScore', sortByAsc= False, maxItems=10): # -> Events which are sorted by a Popularity Score
            self.events_result.append(events)
    
    def set_concepts(self, concepts = []):
        """
        Sets or extracts high-relevance concepts from the fetched events.

        Parameters:
        - concepts (list): Optional manual list of concept names.

        If no manual list is provided, the method automatically extracts concepts 
        from the fetched events with a score > 50.
        """

        if len(concepts) > 0:
            self.concepts = concepts

        elif len(self.events_result) > 0:
            concepts = set()
            for event in self.events_result:
                for concept in event['concepts']:
                    if concept['score'] > 50:
                        concepts.add(concept['label']['eng'])

            self.concepts = list(concepts)
            return self.concepts
        else:
            return None
    
    def fetch_articles(self, max_concept = 15, country = "United States", maxItems = 1):
        """
        Fetches news articles related to the identified concepts from a specific country.

        Parameters:
        - max_concept (int): Number of concepts to use per query batch.
        - country (str): Country to restrict the source location of articles.
        - maxItems (int): Max articles to retrieve per query.

        This method builds batches of concept URIs and queries EventRegistry for
        relevant articles.
        """
        for idxs in range(0 , len(self.concepts), max_concept): 
    
            chunk = [f'http://en.wikipedia.org/wiki/{self.concepts[i].replace(" ", "_")}' for i in range(idxs, min(len(self.concepts), idxs + max_concept))]
            
            # [f'http://en.wikipedia.org/wiki/{concept}']
            
            q = QueryArticlesIter(
                conceptUri= QueryItems.OR(chunk),
                sourceLocationUri = f'http://en.wikipedia.org/wiki/{country.replace(" ", "_")}',
                ignoreSourceGroupUri="paywall/paywalled_sources",
                lang = 'eng',
                isDuplicateFilter = 'skipDuplicates',
                dataType = ["news", "pr", "blog"]
            )

            for article in q.execQuery(self.er, sortBy="date", sortByAsc=False, 
                returnInfo = ReturnInfo(
                    articleInfo = ArticleInfoFlags(concepts = True, categories = True, location=True, eventUri=True, socialScore=True), 
                    sourceInfo= SourceInfoFlags(location=True)),
                maxItems= maxItems):
                if article['uri'] not in self.result_uri:
                    self.result.append(article)
                    self.result_uri.add(article['uri'])

    def get_articles(self):
        """
        Yields each unique article fetched.

        Returns:
        - Generator yielding one article dictionary at a time.
        """
        for article in self.result:
            yield article

# api = APISource()
# api.set_concepts('NYU')
# api.fetch_articles()
# raw_data = api.get_articles()
