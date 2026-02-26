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

class SearchPipeline:
    """
    Dual-index search pipeline for Beauty Lounge.

    Two separate Pinecone indexes:
    - Services (INDEX_NAME_SERVICE): Beauty services the company offers
      (treatments, permanent makeup, wellness, massages)
    - Products (INDEX_NAME): Retail products users can buy from the company
    """

    def __init__(self):
        self._setup_logging()
        self._load_config()
        self._initialize_pinecone()
        self._initialize_embedding_model()
        self.service_vectorizer = joblib.load('tfidf_vectorizer_service.joblib')
        self.product_vectorizer = joblib.load('tfidf_vectorizer.joblib')
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

        # Two separate index names for services and products
        self.service_index_name = os.getenv("INDEX_NAME_SERVICE", "beauty-services")
        self.product_index_name = os.getenv("INDEX_NAME", "beauty-products")
        self.dimension = int(os.getenv("DIMENSION", "3072"))

    def _initialize_pinecone(self):
        """Initialize both service and product indexes."""
        self.logger.info("Initializing Pinecone indexes...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                pc = Pinecone(api_key=self.pinecone_api_key)

                # Initialize service index
                self.service_index = self._get_or_create_index(pc, self.service_index_name)
                self.logger.info(f"Connected to SERVICE index: {self.service_index_name}")

                # Initialize product index
                self.product_index = self._get_or_create_index(pc, self.product_index_name)
                self.logger.info(f"Connected to PRODUCT index: {self.product_index_name}")

                return
            except Exception as e:
                self.logger.error(f"Pinecone init attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                else:
                    raise

    def _get_or_create_index(self, pc, index_name: str):
        """Get or create a Pinecone index."""
        if index_name not in pc.list_indexes().names():
            self.logger.info(f"Creating Pinecone index: {index_name}")
            pc.create_index(
                name=index_name,
                vector_type="dense",
                dimension=self.dimension,
                metric='dotproduct',
                spec=ServerlessSpec(
                    cloud='gcp',
                    region=self.pinecone_region
                )
            )
        return pc.Index(index_name)

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

    def process_query(self, query: str, vectorizer=None) -> tuple:
        self.logger.info("Step 4: Processing query...")
        start_time = time.time()
        try:
            query_emb = self.embedding_model.encode([query])[0]
            # Use provided vectorizer or default to product vectorizer for backward compatibility
            tfidf = vectorizer if vectorizer else self.product_vectorizer
            sparse_embedding = tfidf.transform([query])[0]
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

    def _retrieve(self, index, dense_emb: np.ndarray, sparse_vec: Dict, top_k: int = 5, alpha: float = 0.7) -> List[Dict]:
        """Core retrieval logic - used by both search_services and search_products."""
        start_time = time.time()
        try:
            hdense, hsparse = self.hybrid_score_norm(dense_emb.tolist(), sparse_vec, alpha)

            if not hsparse['values']:
                self.logger.info("Sparse vector empty - falling back to dense-only search")
                results = index.query(
                    vector=hdense,
                    top_k=top_k,
                    include_metadata=True
                )
            else:
                results = index.query(
                    vector=hdense,
                    sparse_vector=hsparse,
                    top_k=top_k,
                    include_metadata=True
                )

            retrieved = [{"id": match['id'], "score": match['score'], "metadata": match['metadata']} for match in results['matches']]

            for i, item in enumerate(retrieved):
                item_name = item['metadata'].get('name', item['metadata'].get('question', 'Unknown'))
                self.logger.info(f"Retrieved item {i+1}: ID={item['id']}, Score={item['score']}, Name={item_name}")

            self.logger.info(f"Retrieval completed: Retrieved {len(retrieved)} items in {time.time() - start_time:.2f} seconds")
            return retrieved
        except Exception as e:
            self.logger.error(f"Retrieval failed: {e}")
            raise

    def search_services(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search beauty SERVICES (treatments, permanent makeup, wellness).
        Uses INDEX_NAME_SERVICE and service-specific TF-IDF vectorizer.

        Args:
            query: The search query
            top_k: Number of results to return

        Returns:
            List of service metadata dicts
        """
        self.logger.info(f"Searching SERVICES: {query}")
        query_emb, sparse_vec = self.process_query(query, vectorizer=self.service_vectorizer)
        retrieved = self._retrieve(self.service_index, query_emb, sparse_vec, top_k=top_k, alpha=HYBRID_SEARCH_ALPHA)
        return [item["metadata"] for item in retrieved]

    def search_products(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search retail PRODUCTS (items users can buy).
        Uses INDEX_NAME and product-specific TF-IDF vectorizer.

        Args:
            query: The search query
            top_k: Number of results to return

        Returns:
            List of product metadata dicts
        """
        self.logger.info(f"Searching PRODUCTS: {query}")
        query_emb, sparse_vec = self.process_query(query, vectorizer=self.product_vectorizer)
        retrieved = self._retrieve(self.product_index, query_emb, sparse_vec, top_k=top_k, alpha=HYBRID_SEARCH_ALPHA)
        return [item["metadata"] for item in retrieved]

    def run(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Run the search pipeline on SERVICES index (backward compatibility).
        Returns: results: List[dict]
        """
        self.logger.info(f"Starting pipeline execution on {self.current_date}...")
        return self.search_services(query, top_k=top_k)

    def get_featured_services(
        self,
        treatments_count: int = 3,
        pmu_count: int = 2,
        wellness_count: int = 2,
    ) -> List[Dict]:
        """
        Get featured SERVICES for initial showcase.
        Queries the SERVICES index with category-specific queries.

        Args:
            treatments_count: Number of facial/body treatments to return
            pmu_count: Number of permanent makeup items to return
            wellness_count: Number of wellness/massage items to return

        Returns:
            List of service metadata dicts with category field included
        """
        featured = []

        # Query facial/body treatments (semantic search already returns relevant results)
        try:
            treatments = self.search_services("Gesichtsbehandlung Kosmetik Pflege", top_k=treatments_count)
            for item in treatments[:treatments_count]:
                item["category"] = "treatments"
                featured.append(item)
            self.logger.info(f"Featured treatments: {len(treatments[:treatments_count])} items")
        except Exception as e:
            self.logger.error(f"Failed to get featured treatments: {e}")

        # Query permanent makeup
        try:
            pmu = self.search_services("Permanent Make-Up Augenbrauen Lippen", top_k=pmu_count)
            for item in pmu[:pmu_count]:
                item["category"] = "permanent_makeup"
                featured.append(item)
            self.logger.info(f"Featured PMU: {len(pmu[:pmu_count])} items")
        except Exception as e:
            self.logger.error(f"Failed to get featured PMU: {e}")

        # Query wellness/massage
        try:
            wellness = self.search_services("Massage Wellness Entspannung", top_k=wellness_count)
            for item in wellness[:wellness_count]:
                item["category"] = "wellness"
                featured.append(item)
            self.logger.info(f"Featured wellness: {len(wellness[:wellness_count])} items")
        except Exception as e:
            self.logger.error(f"Failed to get featured wellness: {e}")

        self.logger.info(f"Total featured services: {len(featured)}")
        return featured

    # Backward compatibility alias
    get_featured_products = get_featured_services


# Backward compatibility alias for class name
ProductSearchPipeline = SearchPipeline

if __name__ == "__main__":
    from flask import Flask, request, jsonify
    from config.search import FLASK_PORT

    app = Flask(__name__)
    pipeline = SearchPipeline()

    @app.route('/search', methods=['POST'])
    def search():
        try:
            data = request.json
            if not data or 'query' not in data:
                return jsonify({"error": "Missing 'query' in request body"}), 400

            query = data['query']
            top_k = data.get('top_k', 5)
            search_type = data.get('type', 'services')  # 'services' or 'products'

            if search_type == 'products':
                results = pipeline.search_products(query, top_k)
            else:
                results = pipeline.search_services(query, top_k)

            return jsonify({"results": results})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/health')
    def health():
        try:
            service_stats = pipeline.service_index.describe_index_stats()
            product_stats = pipeline.product_index.describe_index_stats()
            return jsonify({
                "status": "ok",
                "service_index": pipeline.service_index_name,
                "service_vectors": service_stats.get("total_vector_count", "unknown"),
                "product_index": pipeline.product_index_name,
                "product_vectors": product_stats.get("total_vector_count", "unknown"),
            }), 200
        except Exception as e:
            return jsonify({"status": "error", "detail": str(e)}), 503

    app.run(port=FLASK_PORT)