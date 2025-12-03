"""
Data Source RAG Pipeline for Avalon

This module provides a complete RAG (Retrieval-Augmented Generation) pipeline
for ingesting, embedding, and retrieving content from user-uploaded data sources.

Components:
- data_sources_ingest: Text extraction and chunking from various file formats
- data_sources_embedder: Vector embedding using sentence-transformers (CPU-based)
- data_sources_retriever: Semantic search and chunk retrieval

FEATURE FLAG:
DATA_SOURCE_RAG_ENABLED = False by default
Works with Mistral 7B for retrieval-augmented generation.
"""

from .data_sources_ingest import DataSourceIngester
from .data_sources_embedder import DataSourceEmbedder
from .data_sources_retriever import DataSourceRetriever

__all__ = [
    "DataSourceIngester",
    "DataSourceEmbedder",
    "DataSourceRetriever"
]
