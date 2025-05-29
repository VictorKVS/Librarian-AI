# 📄 core/processor.py

class DocumentProcessor:
    def __init__(
        self,
        vector_store=None,
        embedder=None,
        extractor=None,
        cache_client=None,
        metrics_registry=None,
        max_retries: int = 3,
        health_check_interval: int = 60,
        cache_ttl: int = 3600
    ):
        """
        Full-cycle industrial document processor.
        """
        self.vector_store = vector_store
        self.embedder = embedder or Embedder()
        self.extractor = extractor or EntityExtractor(lang="ru")
        self.cache = cache_client
        self.max_retries = max_retries
        self.health_check_interval = health_check_interval
        self.cache_ttl = cache_ttl
        self._setup_metrics(metrics_registry)
        self.health_status = HealthStatus()
        self._processing_lock = asyncio.Lock()

    def _setup_metrics(self, registry=None):
        """Initialize monitoring system."""
        self.metrics = {
            'embed_ops': Counter(
                'embed_operations_total',
                'Total embedding operations',
                ['status', 'source'],
                registry=registry
            ),
            'entities': Counter(
                'entities_extracted_total',
                'Total extracted entities',
                ['entity_type', 'status'],
                registry=registry
            ),
            'processing_time': Histogram(
                'processing_time_seconds',
                'Document processing time',
                ['stage'],
                registry=registry
            ),
            'queue_size': Gauge(
                'processing_queue_size',
                'Current processing queue size',
                registry=registry
            ),
            'health_status': Gauge(
                'component_health_status',
                'Health status of components',
                ['component'],
                registry=registry
            )
        }

    @asynccontextmanager
    async def _health_check_context(self):
        """Context manager for health checking."""
        async with self._processing_lock:
            if (datetime.utcnow() - self.health_status.last_checked).seconds >= self.health_check_interval:
                await self._update_health_status()
            yield

    async def _update_health_status(self):
        """Update the health status of components."""
        self.health_status = HealthStatus(
            vector_store=await self._check_component('vector_store'),
            cache=await self._check_component('cache'),
            embedder=await self._check_component('embedder'),
            extractor=await self._check_component('extractor'),
            last_checked=datetime.utcnow()
        )
        
        # Update metrics
        for component, status in self.health_status.dict().items():
            if component != 'last_checked':
                self.metrics['health_status'].labels(component=component).set(int(status))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type()
    )
    async def _check_component(self, component: str) -> bool:
        """Check individual component's health."""
        try:
            if component == 'vector_store':
                return await self.vector_store.ping()
            elif component == 'cache':
                return bool(await self.cache.ping())
            elif component == 'embedder':
                test_vec = await self.embedder.aencode("test")
                return len(test_vec) > 0
            elif component == 'extractor':
                test_ent = await self.extractor.aextract("test")
                return True
            return False
        except Exception as e:
            logger.warning(f"Health check failed for {component}: {str(e)}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def process_document(
        self,
        chunks: List[str],
        source_path: str,
        session_id: str = None,
        **kwargs
    ) -> Tuple[List[Tuple[np.ndarray, Dict]], List[EntityRecord]]:
        """
        Complete cycle of document processing.
        """
        async with self._health_check_context():
            self.metrics['queue_size'].inc()
            
            try:
                # Vectorization
                embeddings = []
                async for emb in self._embed_chunks_safe(chunks, source_path, **kwargs):
                    embeddings.append(emb)
                
                # Entity Extraction
                entities = await self._extract_entities_safe(
                    chunks,
                    session_id=session_id,
                    **kwargs.get('extract_params', {})
                )
                
                logger.info(
                    f"Processed: {len(embeddings)} chunks, {len(entities)} entities"
                )
                
                return embeddings, entities
                
            except Exception as e:
                logger.error(f"Processing failed: {str(e)}")
                raise
            finally:
                self.metrics['queue_size'].dec()

    async def _embed_chunks_safe(self, chunks: List[str], source_path: str, **kwargs) -> AsyncIterator:
        """Safe streaming embedding generation."""
        for idx, chunk in enumerate(chunks):
            start_time = datetime.utcnow()
            try:
                text_hash = hashlib.sha256(chunk.encode()).hexdigest()
                cache_key = f"emb:{text_hash}"
                
                # Try reading from cache
                if self.health_status.cache:
                    cached = await self._get_from_cache(cache_key)
                    if cached:
                        yield cached['vector'], cached['meta']
                        continue
                
                # Generate embedding
                vector = await self.embedder.aencode(chunk)
                
                # Metadata creation
                meta = ChunkMetadata(
                    source_path=source_path,
                    text_hash=text_hash,
                    chunk_index=idx,
                    custom_fields=kwargs
                ).dict()
                
                # Save to store/cache
                await self._persist_embedding(vector, meta, cache_key)
                
                yield vector, meta
                
            except Exception as e:
                logger.error(f"Chunk processing failed: {str(e)}")
                continue
            finally:
                duration = (datetime.utcnow() - start_time).total_seconds()
                self.metrics['processing_time'].labels(stage='embedding').observe(duration)

    async def _extract_entities_safe(self, chunks: List[str], **kwargs) -> List[EntityRecord]:
        """Safe entity extraction."""
        start_time = datetime.utcnow()
        try:
            extract_params = {
                'filters': kwargs.get('filters'),
                'min_confidence': kwargs.get('min_confidence', 0.7),
                'normalize': kwargs.get('normalize', True)
            }
            
            results = []
            async for entities in self.extractor.abatch_extract(chunks, **extract_params):
                batch = [
                    EntityRecord(
                        id=uuid.uuid4(),
                        **entity.to_dict(),
                        session_id=kwargs.get('session_id'),
                        processed_at=datetime.utcnow()
                    )
                    for entity in entities
                ]
                results.extend(batch)
                
                # Update metrics
                for entity in entities:
                    self.metrics['entities'].labels(
                        entity_type=entity.label,
                        status='processed'
                    ).inc()
            
            return results
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            self.metrics['entities'].labels(status='failed').inc()
            return []
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics['processing_time'].labels(stage='extraction').observe(duration)