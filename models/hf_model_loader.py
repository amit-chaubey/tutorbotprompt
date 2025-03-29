import os
import pickle
import logging
from typing import Tuple, Dict, Any, Optional, Union, List
import time
import threading

# Import torch and transformers (with fallback)
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logging.warning("Transformers library not found. Please install with 'pip install transformers'")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cache for loaded models
MODEL_CACHE = {}
CACHE_LOCK = threading.Lock()

class ModelConfig:
    """Configuration for model loading"""
    def __init__(
        self,
        model_name: str = "gpt2",
        tokenizer_name: Optional[str] = None,
        device: Optional[str] = None,
        use_cache: bool = True,
        cache_dir: Optional[str] = None,
        model_kwargs: Optional[Dict[str, Any]] = None,
        tokenizer_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize model configuration
        
        Args:
            model_name: Name or path of the model to load
            tokenizer_name: Name or path of the tokenizer (defaults to model_name)
            device: Device to load the model on (e.g., 'cuda', 'cpu')
            use_cache: Whether to cache the model in memory
            cache_dir: Directory to cache models
            model_kwargs: Additional kwargs for model loading
            tokenizer_kwargs: Additional kwargs for tokenizer loading
        """
        self.model_name = model_name
        self.tokenizer_name = tokenizer_name or model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu') if HAS_TRANSFORMERS else 'cpu'
        self.use_cache = use_cache
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), 'cache')
        self.model_kwargs = model_kwargs or {}
        self.tokenizer_kwargs = tokenizer_kwargs or {}
        
        # Ensure cache directory exists
        if self.use_cache and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_cache_path(self) -> str:
        """Get the path to the cached model"""
        # Create a unique identifier based on model config
        config_str = f"{self.model_name}_{self.device}"
        return os.path.join(self.cache_dir, f"{config_str}.pkl")


def load_model(config: Optional[Union[ModelConfig, Dict[str, Any]]] = None) -> Tuple:
    """
    Load a model and tokenizer based on configuration
    
    Args:
        config: Model configuration (dict or ModelConfig)
        
    Returns:
        Tuple of (tokenizer, model)
    """
    if not HAS_TRANSFORMERS:
        raise ImportError("Transformers library is required but not installed")
    
    # Convert dict config to ModelConfig if needed
    if isinstance(config, dict):
        config = ModelConfig(**config)
    elif config is None:
        config = ModelConfig()
    
    # Check if model is in memory cache
    cache_key = f"{config.model_name}_{config.device}"
    with CACHE_LOCK:
        if config.use_cache and cache_key in MODEL_CACHE:
            logger.info(f"Using cached model: {config.model_name}")
            return MODEL_CACHE[cache_key]
    
    # Check if model is in disk cache
    cache_path = config.get_cache_path()
    if config.use_cache and os.path.exists(cache_path):
        try:
            logger.info(f"Loading model from cache: {cache_path}")
            with open(cache_path, 'rb') as f:
                tokenizer, model = pickle.load(f)
            
            # Move model to the correct device
            if hasattr(model, 'to'):
                model = model.to(config.device)
                
            # Store in memory cache
            with CACHE_LOCK:
                MODEL_CACHE[cache_key] = (tokenizer, model)
                
            return tokenizer, model
        except Exception as e:
            logger.error(f"Failed to load model from cache: {str(e)}")
            # Fall back to loading from HuggingFace
    
    # Load model and tokenizer from HuggingFace
    start_time = time.time()
    logger.info(f"Loading model from HuggingFace: {config.model_name}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            config.tokenizer_name, 
            **config.tokenizer_kwargs
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            config.model_name,
            device_map=config.device,
            **config.model_kwargs
        )
        
        # Cache the model
        if config.use_cache:
            # In-memory cache
            with CACHE_LOCK:
                MODEL_CACHE[cache_key] = (tokenizer, model)
            
            # Disk cache
            try:
                with open(cache_path, 'wb') as f:
                    # Store a CPU version for caching
                    cpu_model = model.to('cpu') if hasattr(model, 'to') else model
                    pickle.dump((tokenizer, cpu_model), f)
                
                # Move model back to original device
                if hasattr(model, 'to'):
                    model = model.to(config.device)
            except Exception as e:
                logger.error(f"Failed to cache model to disk: {str(e)}")
        
        logger.info(f"Model loaded in {time.time() - start_time:.2f} seconds")
        return tokenizer, model
    
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise


def create_pipeline(
    task: str = "text-generation",
    model_config: Optional[Union[ModelConfig, Dict[str, Any]]] = None,
    pipeline_kwargs: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Create a HuggingFace pipeline for a specific task
    
    Args:
        task: The task for the pipeline (e.g., 'text-generation', 'question-answering')
        model_config: Configuration for model loading
        pipeline_kwargs: Additional arguments for the pipeline
        
    Returns:
        HuggingFace pipeline
    """
    if not HAS_TRANSFORMERS:
        raise ImportError("Transformers library is required but not installed")
    
    # Load the model and tokenizer
    tokenizer, model = load_model(model_config)
    
    # Create the pipeline
    pipe = pipeline(
        task,
        model=model,
        tokenizer=tokenizer,
        **(pipeline_kwargs or {})
    )
    
    return pipe


def unload_model(model_name: Optional[str] = None, device: Optional[str] = None) -> None:
    """
    Unload a model from memory to free up resources
    
    Args:
        model_name: Name of the model to unload (None to unload all)
        device: Device of the model to unload
    """
    with CACHE_LOCK:
        if model_name is None:
            # Unload all models
            MODEL_CACHE.clear()
            logger.info("All models unloaded from memory")
        else:
            # Unload specific model
            device = device or ('cuda' if torch.cuda.is_available() else 'cpu') if HAS_TRANSFORMERS else 'cpu'
            cache_key = f"{model_name}_{device}"
            if cache_key in MODEL_CACHE:
                del MODEL_CACHE[cache_key]
                logger.info(f"Model {model_name} unloaded from memory")
            else:
                logger.warning(f"Model {model_name} not found in cache") 