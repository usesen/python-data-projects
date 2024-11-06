from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import traceback

class Engine:
    def _filter_data_by_model(self, model):
        return self.df[self.df['model'] == model].copy()

    def _calculate_similarities(self, filtered_data, problem):
        self.vectorizer = TfidfVectorizer()
        problems = filtered_data['problem_description'].tolist()
        problems.append(problem)
        
        tfidf_matrix = self.vectorizer.fit_transform(problems)
        
        similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
        
        filtered_data['similarity'] = similarities
        
        results = filtered_data[filtered_data['similarity'] > self.min_similarity]
        top_solutions = results.nlargest(3, 'similarity')[
            ['Ticket_ID', 'customer_id', 'model', 'problem_description', 'solution_description']
        ]
        
        return top_solutions.to_dict('records')

    def get_similar_tickets(self, problem, model):
        try:
            filtered_data = self._filter_data_by_model(model)
            
            if filtered_data.empty:
                return []

            return self._calculate_similarities(filtered_data, problem)
            
        except Exception as e:
            print(f"❌ Benzer ticket arama hatası: {str(e)}")
            traceback.print_exc()
            return [] 