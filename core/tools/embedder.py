# core/tools/embedder.py

from typing import List, Optional, Union
import logging
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "SentenceTransformer not found. Please install it:\n"
        "    pip install sentence-transformers"
    )

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class EmbeddingService:
    """
    Service for creating text embeddings using Sentence-Transformers.
    Supports both single texts and batches, with configurable parameters.

    Example usage:
        service = EmbeddingService(model_name="all-MiniLM-L6-v2", device="cpu")
        single_vec = service.embed_text("Example text")
        batch_vecs = service.embed_batch(["Text 1", "Text 2", "Text 3"])
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        normalize_embeddings: bool = True,
        **model_kwargs
    ):
        """
        Initialize the embedding service.

        Args:
            model_name: Name of the pretrained SentenceTransformer model.
            device: Device to run the model on ("cpu" or "cuda").
            normalize_embeddings: Whether to normalize embeddings to unit length.
            **model_kwargs: Additional arguments for SentenceTransformer.
        """
        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        self.model_kwargs = model_kwargs

        logger.info(f"Loading embedding model '{model_name}' on device '{device}'...")
        try:
            self.model = SentenceTransformer(
                model_name,
                device=device,
                **model_kwargs
            )
            # Test the model with a simple input
            test_embedding = self.model.encode(
                "test",
                normalize_embeddings=normalize_embeddings,
                convert_to_tensor=False
            )
            self.embedding_dim = test_embedding.shape[0]
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def embed_text(
        self,
        text: str,
        normalize: Optional[bool] = None,
        convert_to_numpy: bool = True
    ) -> Union[List[float], np.ndarray]:
        """
        Convert a single text into its vector representation.

        Args:
            text: Input text to embed.
            normalize: Override for instance-wide normalize_embeddings setting.
            convert_to_numpy: Whether to return numpy array or list.

        Returns:
            Embedding vector as list or numpy array.
        """
        if not isinstance(text, str):
            raise ValueError("Input text must be a string.")
        if not text.strip():
            raise ValueError("Input text cannot be empty.")

        normalize = self.normalize_embeddings if normalize is None else normalize

        try:
            vec = self.model.encode(
                text,
                normalize_embeddings=normalize,
                convert_to_tensor=False,
                show_progress_bar=False
            )
            return vec.tolist() if convert_to_numpy else vec
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: Optional[bool] = None,
        convert_to_numpy: bool = True
    ) -> Union[List[List[float]], np.ndarray]:
        """
        Convert a list of texts into their vector representations.

        Args:
            texts: List of texts to embed.
            batch_size: Batch size for processing.
            normalize: Override for instance-wide normalize_embeddings setting.
            convert_to_numpy: Whether to return numpy array or list of lists.

        Returns:
            List of embeddings or 2D numpy array.
        """
        if not isinstance(texts, list):
            raise ValueError("Input must be a list of texts.")
        if not all(isinstance(t, str) for t in texts):
            raise ValueError("All items in texts must be strings.")

        normalize = self.normalize_embeddings if normalize is None else normalize

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                convert_to_tensor=False,
                show_progress_bar=False
            )
            return embeddings.tolist() if convert_to_numpy else embeddings
        except Exception as e:
            logger.error(f"Failed to embed batch: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced by this model."""
        return self.embedding_dim

    def __repr__(self):
        return (
            f"<EmbeddingService(model_name={self.model_name!r}, "
            f"device={self.device!r}, "
            f"embedding_dim={self.embedding_dim})>"
        )
