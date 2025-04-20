"""
RAG (Retrieval-Augmented Generation) Module for Finance Accountant Agent

This module implements a vector store-based retrieval system that enhances
LLM responses with relevant financial information from company documents.

Features:
- Document chunking and embedding using sentence-transformers
- FAISS vector store for efficient similarity search
- Document metadata tracking and filtering
- Context assembly for LLM prompting
- Query expansion and rewriting
- Finance-specific document processing

Dependencies:
- sentence-transformers: For document and query embedding
- faiss-cpu: For vector storage and retrieval
- langchain: For document processing utilities
- file_manager: For document ingestion
"""

import asyncio
import json
import logging
import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a document chunk with text content and metadata."""
    text: str
    metadata: Dict


class RAGModule:
    """
    Retrieval-Augmented Generation module for enhancing LLM responses
    with relevant financial information.
    """

    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.documents = []
        self.initialized = False

    async def initialize(self):
        """Initialize the RAG module by loading models and indexes."""
        if self.initialized:
            return

        try:
            # Load embedding model in a separate thread
            loop = asyncio.get_event_loop()
            self.embedding_model = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer(settings.RAG_EMBEDDING_MODEL)
            )

            # Load or create FAISS index
            index_path = settings.RAG_VECTOR_STORE_PATH / "faiss_index.bin"
            documents_path = settings.RAG_VECTOR_STORE_PATH / "documents.pkl"

            if index_path.exists() and documents_path.exists():
                # Load existing index and documents
                self.index = await loop.run_in_executor(
                    None,
                    lambda: faiss.read_index(str(index_path))
                )
                with open(documents_path, "rb") as f:
                    self.documents = pickle.load(f)
                logger.info(f"Loaded existing FAISS index with {len(self.documents)} documents")
            else:
                # Create new index
                embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
                self.index = faiss.IndexFlatL2(embedding_dim)
                logger.info(f"Created new FAISS index with dimension {embedding_dim}")

            self.initialized = True

        except Exception as e:
            logger.error(f"Error initializing RAG module: {str(e)}")
            raise

    async def add_documents(self, documents: List[Document]) -> int:
        """
        Add documents to the vector store.

        Args:
            documents: List of Document objects to add

        Returns:
            Number of documents added
        """
        await self.initialize()

        if not documents:
            return 0

        try:
            # Get embeddings for all documents
            texts = [doc.text for doc in documents]

            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.embedding_model.encode(texts, convert_to_numpy=True)
            )

            # Add to FAISS index
            self.index.add(np.array(embeddings))

            # Update document store
            start_idx = len(self.documents)
            self.documents.extend(documents)

            # Save index and documents
            await self._save_index_and_documents()

            logger.info(f"Added {len(documents)} documents to RAG index")
            return len(documents)

        except Exception as e:
            logger.error(f"Error adding documents to RAG index: {str(e)}")
            raise

    async def _save_index_and_documents(self):
        """Save the FAISS index and documents to disk."""
        index_path = settings.RAG_VECTOR_STORE_PATH / "faiss_index.bin"
        documents_path = settings.RAG_VECTOR_STORE_PATH / "documents.pkl"

        loop = asyncio.get_event_loop()

        # Save FAISS index
        await loop.run_in_executor(
            None,
            lambda: faiss.write_index(self.index, str(index_path))
        )

        # Save documents
        await loop.run_in_executor(
            None,
            lambda: pickle.dump(self.documents, open(documents_path, "wb"))
        )

    async def search(
        self, query: str, top_k: Optional[int] = None, filter_criteria: Optional[Dict] = None
    ) -> List[Document]:
        """
        Search for relevant documents based on a query.

        Args:
            query: The search query
            top_k: Number of results to return (defaults to RAG_TOP_K setting)
            filter_criteria: Optional metadata filtering criteria

        Returns:
            List of relevant Document objects
        """
        await self.initialize()

        if not self.documents:
            logger.warning("No documents in RAG index")
            return []

        if top_k is None:
            top_k = settings.RAG_TOP_K

        try:
            # Encode query
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                None,
                lambda: self.embedding_model.encode([query], convert_to_numpy=True)
            )

            # Search in FAISS
            distances, indices = self.index.search(query_embedding, top_k * 2)  # Get more than needed for filtering

            # Get corresponding documents
            results = []
            for idx in indices[0]:
                if idx < len(self.documents):
                    doc = self.documents[idx]

                    # Apply metadata filtering if specified
                    if filter_criteria:
                        if self._matches_filter(doc.metadata, filter_criteria):
                            results.append(doc)
                    else:
                        results.append(doc)

                if len(results) >= top_k:
                    break

            return results

        except Exception as e:
            logger.error(f"Error searching RAG index: {str(e)}")
            return []

    def _matches_filter(self, metadata: Dict, filter_criteria: Dict) -> bool:
        """Check if document metadata matches filter criteria."""
        for key, value in filter_criteria.items():
            if key not in metadata:
                return False

            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            elif metadata[key] != value:
                return False

        return True

    async def generate_context(self, query: str, filter_criteria: Optional[Dict] = None) -> str:
        """
        Generate context for LLM based on query and relevant documents.

        Args:
            query: User query
            filter_criteria: Optional metadata filtering criteria

        Returns:
            Formatted context string for LLM prompt
        """
        relevant_docs = await self.search(query, filter_criteria=filter_criteria)

        if not relevant_docs:
            return ""

        # Format context with document content and sources
        context_parts = []
        for i, doc in enumerate(relevant_docs):
            source_info = ""
            if "source" in doc.metadata:
                source_info = f" (Source: {doc.metadata['source']})"
            if "date" in doc.metadata:
                source_info += f", {doc.metadata['date']}"

            context_parts.append(f"[Document {i+1}]{source_info}\n{doc.text}\n")

        context = "\n".join(context_parts)
        return context

    async def augment_prompt(self, query: str, system_prompt: str, filter_criteria: Optional[Dict] = None) -> str:
        """
        Augment system prompt with relevant context for RAG.

        Args:
            query: User query
            system_prompt: Original system prompt
            filter_criteria: Optional metadata filtering criteria

        Returns:
            Augmented system prompt with context
        """
        if not settings.RAG_ENABLED:
            return system_prompt

        context = await self.generate_context(query, filter_criteria)
        if not context:
            return system_prompt

        # Add context to system prompt
        augmented_prompt = f"""
{system_prompt}

Use the following financial documents as context for your response:

{context}

Focus on providing accurate information based on these documents when relevant to the query.
"""
        return augmented_prompt


# Create singleton instance
rag_module = RAGModule()
