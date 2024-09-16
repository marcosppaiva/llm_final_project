from typing import Dict, List, Optional

from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

import chromadb


class LangChainChromaRAG:
    """A class to manage game reviews using Chroma and LangChain for
    retrieval-augmented generation (RAG). It leverages embeddings
    to add, search, update, and delete game reviews.

    Attributes:
        collection_name (str): The name of the collection used in the Chroma vector store.
        embedding_model_name (str): The name of the HuggingFace embedding model.
        persist_directory (str): Directory to perscist Chroma vector store data.
        embeddings (HuggingFaceEmbeddings): Embedding model instance.
        vectorstore (Chroma): Vector store instance for storing and searching vectors.
        text_splitter (RecursiveCharacterTextSplitter): Used to split text into smaller chunks.
    """

    def __init__(
        self,
        collection_name: str,
        chroma_host: str = 'localhost',
        embedding_model_name: str = 'sentence-transformers/all-MiniLM-L6-v2',
    ):
        """Initializes the LangChainChromaRAG class with the specified collection name,
        embedding model, and persistent directory.

        Args:
            collection_name (str): Name of the collection in the Chroma vector store.
            embedding_model_name (str, optional): The name of the embedding model from HuggingFace. Defaults to "sentence-transformers/all-MiniLM-L6-v2".
        """
        self.collection_name = collection_name
        self.chroma_client = chromadb.HttpClient(
            host=chroma_host,
            port=8000,
            settings=Settings(allow_reset=True, anonymized_telemetry=False),
        )

        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

        self.vectorstore = Chroma(
            client=self.chroma_client,
            collection_name=collection_name,
            embedding_function=self.embeddings,
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=256, chunk_overlap=50, length_function=len
        )

    def add_game_reviews(self, reviews: List[Dict[str, str]]):
        """Adds new game reviews to the vector store. Reviews are split into chunks before storing.

        Args:
            reviews (list): A list of review dictionaries. Each dictionary should contain:
                - 'recommendationid' (str): Unique ID for the review.
                - 'language' (str): The language of the review.
                - 'game' (str): The name of the game being reviewed.
                - 'review' (str): The text of the review.
        """
        new_reviews = []
        for review in reviews:
            if not self._review_exists(review["recommendationid"]):
                new_reviews.append(review)
            else:
                print(
                    f"Review with ID {review['recommendationid']} already exists. Skipping."
                )

        for review in new_reviews:
            chunks = self.text_splitter.split_text(review["review"])
            metadatas = [
                {
                    "recommendationid": review["recommendationid"],
                    "language": review["language"],
                    "game": review["game"],
                    "chunk_index": i,  # Add chunk index to metadata
                }
                for i in range(len(chunks))
            ]

            self.vectorstore.add_texts(texts=chunks, metadatas=metadatas)

    def _review_exists(self, recommendationid: str):
        """Checks if a review with the given recommendation ID already exists in the vector store.

        Args:
            recommendationid (str): The unique recommendation ID of the review.

        Returns:
            bool: True if the review exists, False otherwise.
        """
        # Check if any document exists with the given recommendationid
        results = self.vectorstore.similarity_search(
            "dummy query",  # The query doesn't matter here
            k=1,
            filter={"recommendationid": recommendationid},
        )
        return len(results) > 0

    def search(
        self,
        query: str,
        n_results: Optional[int] = 5,
        filter: Optional[Dict[str, str]] = None,
    ):
        """Searches the vector store for reviews similar to the query.

        Args:
            query (str): The search query.
            n_results (int, optional): The number of results to return. Defaults to 5.
            filter (dict, optional): Additional filters for the search (e.g., by recommendation ID). Defaults to None.

        Returns:
            list: A list of matching documents with their metadata and contents.
        """
        return self.vectorstore.similarity_search(query, k=n_results, filter=filter)  # type: ignore

    def get_review(self, recommendationid: str):
        """Retrieves the full text of a review using the recommendation ID by concatenating all relevant chunks.

        Args:
            recommendationid (str): The unique recommendation ID of the review.

        Returns:
            str: The full review text reconstructed from chunks.
        """
        chunks = self.vectorstore.similarity_search(
            "dummy query",  # The query doesn't matter here
            k=100,  # Set a high number to retrieve all chunks
            filter={"recommendationid": recommendationid},
        )
        # Sort chunks by chunk_index and concatenate
        sorted_chunks = sorted(chunks, key=lambda x: x.metadata["chunk_index"])
        full_review = " ".join(chunk.page_content for chunk in sorted_chunks)
        return full_review

    def update_review(self, review: Dict[str, str]):
        """Updates an existing review by deleting the old one and adding the new one.

        Args:
            review (dict): The updated review dictionary. It should contain:
                - 'recommendationid' (str): Unique ID of the review.
                - 'language' (str): Language of the review.
                - 'game' (str): Name of the game being reviewed.
                - 'review' (str): The updated review text.
        """
        # First, remove the existing review
        self.delete_review(review["recommendationid"])
        # Then add the updated review
        self.add_game_reviews([review])

    def delete_review(self, recommendationid: str):
        """Deletes a review from the vector store based on its recommendation ID.

        Args:
            recommendationid (str): The unique recommendation ID of the review.
        """
        # Get the underlying Chroma collection
        collection = self.vectorstore._collection

        # Query for documents with the given recommendationid
        results = collection.get(
            where={"recommendationid": recommendationid}, include=["metadatas"]
        )

        # Extract the ids from the metadatas
        ids_to_delete = [id for id in results["ids"] if id]

        # Delete the documents by their ids
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
        else:
            print(f"No documents found with recommendationid: {recommendationid}")
