from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import re

class RAGPipeline:
    def __init__(self, texts):
        self.texts = texts
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.embeddings = self.embedder.encode(texts, convert_to_tensor=True)
        
        # Use a simpler approach to avoid memory issues
        self.model_type = 'extraction'  # Use extraction instead of generation

    def query(self, question, top_k=5):  # Increase top_k to get more relevant chunks
        question_embedding = self.embedder.encode([question], convert_to_tensor=True)
        similarities = cosine_similarity(question_embedding.cpu(), self.embeddings.cpu())[0]
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        # Get all relevant chunks (no truncation)
        relevant_chunks = [self.texts[i] for i in top_indices]
        
        # Extract answer from relevant chunks without losing data
        return relevant_chunks