import os
import sys
import logging
import time
from datetime import datetime

# Ensure project root is in sys.path (needed when run as subprocess)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from pinecone import Pinecone, ServerlessSpec
import numpy as np
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
import joblib
from config.search import HYBRID_SEARCH_ALPHA

load_dotenv()

class ProductSearchPipeline:
    def __init__(self):
        self._setup_logging()
        self._load_config()
        self._initialize_pinecone()
        self._initialize_embedding_model()
        self.vectorizer = joblib.load('tfidf_vectorizer.joblib')
        self.current_date = datetime.now().strftime("%B %d, %Y")

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s',  
            handlers=[
                logging.StreamHandler(),  
                logging.FileHandler('pipeline.log')  
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self):
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
        if not self.pinecone_api_key:
            raise ValueError("Missing PINECONE_API_KEY environment variable")
        
        self.pinecone_region = os.getenv('PINECONE_REGION', "us-east-1")
        
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("Missing OPENAI_API_KEY environment variable")
        
        self.embedding_model_name = os.getenv('EMBEDDING_MODEL', "text-embedding-3-large")
        
        self.index_name = os.getenv("INDEX_NAME", "test")
        self.dimension = int(os.getenv("DIMENSION", "3072"))

    def _initialize_pinecone(self):
        self.logger.info("Initializing Pinecone...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                pc = Pinecone(api_key=self.pinecone_api_key)

                if self.index_name not in pc.list_indexes().names():
                    self.logger.info(f"Creating Pinecone index: {self.index_name}")
                    pc.create_index(
                        name=self.index_name,
                        vector_type="dense",
                        dimension=self.dimension,
                        metric='dotproduct',
                        spec=ServerlessSpec(
                            cloud='gcp',
                            region=self.pinecone_region
                        )
                    )
                self.index = pc.Index(self.index_name)

                self.logger.info(f"Connected to Pinecone index: {self.index_name}")
                return
            except Exception as e:
                self.logger.error(f"Pinecone init attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                else:
                    raise

    def _initialize_embedding_model(self):
        self.logger.info("Loading embedding model...")
        try:
            class OpenAIEmbedder:
                def __init__(self, model, api_key):
                    self.model = model
                    self.client = OpenAI(api_key=api_key)

                def encode(self, sentences):
                    for attempt in range(3):
                        try:
                            response = self.client.embeddings.create(input=sentences, model=self.model)
                            embeddings = [r.embedding for r in response.data]
                            embeddings = [emb / np.linalg.norm(emb) for emb in embeddings]
                            return np.array(embeddings)
                        except Exception as e:
                            if attempt < 2:
                                time.sleep(1 * (attempt + 1))
                            else:
                                raise

            self.embedding_model = OpenAIEmbedder(self.embedding_model_name, self.openai_api_key)
            self.logger.info("Model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            raise

    def process_query(self, query: str) -> tuple:
        self.logger.info("Step 4: Processing query...")
        start_time = time.time()
        try:
            query_emb = self.embedding_model.encode([query])[0]
            sparse_embedding = self.vectorizer.transform([query])[0]
            indices = sparse_embedding.indices.tolist()
            values = sparse_embedding.data.tolist()
            sparse_vec = {"indices": indices, "values": values}
            self.logger.info(f"Query: {query}")
            self.logger.info(f"Dense embedding shape: {query_emb.shape}, first 5 values: {query_emb[:5]}")
            self.logger.info(f"Sparse vector: indices={indices[:5]}..., values={values[:5]}...")
            self.logger.info(f"Step 4 completed in {time.time() - start_time:.2f} seconds")
            return query_emb, sparse_vec
        except Exception as e:
            self.logger.error(f"Step 4 failed: {e}")
            raise

    def hybrid_score_norm(self, dense: List[float], sparse: Dict[str, List], alpha: float) -> tuple:
        if alpha < 0 or alpha > 1:
            raise ValueError("Alpha must be between 0 and 1")
        hsparse = {
            'indices': sparse['indices'],
            'values': [v * (1 - alpha) for v in sparse['values']]
        }
        hdense = [v * alpha for v in dense]
        return hdense, hsparse

    def retrieve_products(self, dense_emb: np.ndarray, sparse_vec: Dict, top_k: int = 20, alpha: float = 0.7) -> List[Dict]:
        self.logger.info("Step 5: Retrieving products with hybrid search...")
        start_time = time.time()
        try:
            hdense, hsparse = self.hybrid_score_norm(dense_emb.tolist(), sparse_vec, alpha)

            if not hsparse['values']:
                self.logger.info("Sparse vector empty - falling back to dense-only search")
                results = self.index.query(
                    vector=hdense,
                    top_k=top_k,
                    include_metadata=True
                )
            else:
                results = self.index.query(
                    vector=hdense,
                    sparse_vector=hsparse,
                    top_k=top_k,
                    include_metadata=True
                )

            retrieved = [{"id": match['id'], "score": match['score'], "metadata": match['metadata']} for match in results['matches']]

            for i, item in enumerate(retrieved):
                product_name = item['metadata'].get('name', item['metadata'].get('question', 'Unknown'))
                self.logger.info(f"Retrieved product {i+1}: ID={item['id']}, Score={item['score']}, Name={product_name}")

            self.logger.info(f"Step 5 completed: Retrieved {len(retrieved)} products in {time.time() - start_time:.2f} seconds")
            return retrieved
        except Exception as e:
            self.logger.error(f"Step 5 failed: {e}")
            raise

    def run(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Run the search pipeline.
        Returns: results: List[dict]
        """
        self.logger.info(f"Starting pipeline execution on {self.current_date}...")

        query_emb, sparse_vec = self.process_query(query)

        retrieved = self.retrieve_products(query_emb, sparse_vec, top_k=top_k, alpha=HYBRID_SEARCH_ALPHA)

        data = [item["metadata"] for item in retrieved]

        return data

if __name__ == "__main__":
    from flask import Flask, request, jsonify
    from config.search import FLASK_PORT

    app = Flask(__name__)
    pipeline = ProductSearchPipeline()

    @app.route('/search', methods=['POST'])
    def search():
        try:
            data = request.json
            if not data or 'query' not in data:
                return jsonify({"error": "Missing 'query' in request body"}), 400

            query = data['query']
            top_k = data.get('top_k', 5)

            results = pipeline.run(query, top_k)
            return jsonify({"results": results})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/health')
    def health():
        try:
            stats = pipeline.index.describe_index_stats()
            return jsonify({
                "status": "ok",
                "index": pipeline.index_name,
                "vectors": stats.get("total_vector_count", "unknown"),
            }), 200
        except Exception as e:
            return jsonify({"status": "error", "detail": str(e)}), 503

    app.run(port=FLASK_PORT)