"""
Semantic Repository - Semantic Layer Data Access

Purpose: Load and manage semantic layer configuration from JSON files.
This repository handles reading semantic.json and converting it to domain models.

Design Pattern: Repository Pattern
- Separates file I/O from business logic
- Makes it easy to switch sources (file → database → API)
- Provides caching for performance
"""

import json
from pathlib import Path
from typing import Optional, List
from app.core.models.semantic import SemanticLayer
from app.repositories.base import SemanticRepository
from app.config import get_settings, get_logger
from app.core.exceptions import SemanticLayerError

logger = get_logger(__name__)


class FileSemanticRepository(SemanticRepository):
    """
    Repository that loads semantic layer from JSON file
    
    This implementation reads semantic.json from the filesystem.
    Future: Could add database-backed or API-backed implementations.
    """
    
    def __init__(self, semantic_json_path: Optional[str] = None):
        """
        Initialize repository with semantic JSON file path
        
        Args:
            semantic_json_path: Path to semantic.json file.
                              If None, uses path from settings.
        """
        if semantic_json_path is None:
            settings = get_settings()
            semantic_json_path = settings.semantic_json_path
        
        # Handle both absolute and relative paths
        self.semantic_json_path = Path(semantic_json_path)
        if not self.semantic_json_path.is_absolute():
            # If relative, try from project root
            project_root = Path(__file__).parent.parent.parent.parent
            potential_path = project_root / self.semantic_json_path
            if potential_path.exists():
                self.semantic_json_path = potential_path
            # If still doesn't exist, try from backend directory
            elif not self.semantic_json_path.exists():
                backend_dir = Path(__file__).parent.parent.parent
                potential_path = backend_dir.parent / self.semantic_json_path
                if potential_path.exists():
                    self.semantic_json_path = potential_path
        self._cached_semantic: Optional[SemanticLayer] = None
    
    async def load_semantic(self) -> SemanticLayer:
        """
        Load semantic layer from JSON file
        
        Returns:
            SemanticLayer: Domain model representing the semantic layer
            
        Raises:
            SemanticLayerError: If file doesn't exist or is invalid
            
        Example:
            repo = FileSemanticRepository()
            semantic = await repo.load_semantic()
            table = semantic.get_table("customers")
        """
        # Check if file exists
        if not self.semantic_json_path.exists():
            raise SemanticLayerError(
                f"Semantic JSON file not found: {self.semantic_json_path}. "
                "Please create semantic.json or set SEMANTIC_JSON path."
            )
        
        try:
            # Read JSON file
            with open(self.semantic_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to domain model
            semantic = SemanticLayer.from_dict(data)
            
            # Cache it for performance
            self._cached_semantic = semantic
            
            return semantic
            
        except json.JSONDecodeError as e:
            raise SemanticLayerError(
                f"Invalid JSON in semantic file: {e}"
            ) from e
        except Exception as e:
            raise SemanticLayerError(
                f"Failed to load semantic layer: {e}"
            ) from e
    
    async def reload_semantic(self) -> SemanticLayer:
        """
        Reload semantic layer from file (clears cache)
        
        Useful when semantic.json is updated and you want fresh data.
        
        Returns:
            SemanticLayer: Freshly loaded semantic layer
            
        Example:
            # After updating semantic.json
            semantic = await repo.reload_semantic()
        """
        # Clear cache
        self._cached_semantic = None
        
        # Load fresh
        return await self.load_semantic()
    
    def get_cached_semantic(self) -> Optional[SemanticLayer]:
        """
        Get cached semantic layer if available
        
        Returns:
            SemanticLayer if cached, None otherwise
            
        Note: This is synchronous and doesn't load from file.
        Use load_semantic() to ensure data is loaded.
        """
        return self._cached_semantic


class MultiFileSemanticRepository(SemanticRepository):
    """
    Repository that loads semantic layers from multiple JSON files
    
    This implementation:
    1. Discovers all *.json files in metadata/ directory
    2. Loads each file as a SemanticLayer
    3. Merges all layers into one
    4. Caches the merged result
    
    This allows you to split semantic definitions across multiple files
    (e.g., one file per table or domain).
    """
    
    def __init__(self, semantic_dir: Optional[str] = None):
        """
        Initialize repository with semantic directory path
        
        Args:
            semantic_dir: Path to directory containing semantic JSON files.
                         If None, uses path from settings or defaults to backend/metadata/
        """
        if semantic_dir is None:
            settings = get_settings()
            # Try to get semantic_dir from settings, or use default
            semantic_dir = getattr(settings, 'semantic_dir', None)
            if semantic_dir is None:
                # Default to backend/metadata/
                backend_dir = Path(__file__).parent.parent.parent
                semantic_dir = backend_dir / "metadata"
            else:
                semantic_dir = Path(semantic_dir)
        else:
            semantic_dir = Path(semantic_dir)
        
        # Handle relative paths
        if not semantic_dir.is_absolute():
            project_root = Path(__file__).parent.parent.parent.parent
            potential_path = project_root / semantic_dir
            if potential_path.exists():
                semantic_dir = potential_path
            else:
                backend_dir = Path(__file__).parent.parent.parent
                potential_path = backend_dir / semantic_dir
                if potential_path.exists():
                    semantic_dir = potential_path
        
        self.semantic_dir = semantic_dir
        self._cached_semantic: Optional[SemanticLayer] = None
        logger.info(f"MultiFileSemanticRepository initialized with directory: {self.semantic_dir}")
    
    def _discover_semantic_files(self) -> List[Path]:
        """
        Discover all semantic JSON files in the directory
        
        Returns:
            List of paths to JSON files (excluding .example files)
            
        Raises:
            SemanticLayerError: If directory doesn't exist
        """
        if not self.semantic_dir.exists():
            raise SemanticLayerError(
                f"Semantic directory not found: {self.semantic_dir}. "
                "Please create the directory or set SEMANTIC_DIR path."
            )
        
        if not self.semantic_dir.is_dir():
            raise SemanticLayerError(
                f"Semantic path is not a directory: {self.semantic_dir}"
            )
        
        # Find all JSON files, excluding .example files
        json_files = [
            f for f in self.semantic_dir.glob("*.json")
            if not f.name.endswith(".example")
        ]
        
        if not json_files:
            raise SemanticLayerError(
                f"No semantic JSON files found in {self.semantic_dir}. "
                "Please add at least one semantic JSON file."
            )
        
        # Sort for consistent ordering
        json_files.sort()
        logger.debug(f"Discovered {len(json_files)} semantic files: {[f.name for f in json_files]}")
        return json_files
    
    def _load_single_file(self, file_path: Path) -> SemanticLayer:
        """
        Load a single semantic JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            SemanticLayer loaded from the file
            
        Raises:
            SemanticLayerError: If file is invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            semantic = SemanticLayer.from_dict(data)
            logger.debug(f"Loaded {len(semantic.tables)} tables from {file_path.name}")
            return semantic
            
        except json.JSONDecodeError as e:
            raise SemanticLayerError(
                f"Invalid JSON in semantic file {file_path.name}: {e}"
            ) from e
        except Exception as e:
            raise SemanticLayerError(
                f"Failed to load semantic file {file_path.name}: {e}"
            ) from e
    
    async def load_semantic(self) -> SemanticLayer:
        """
        Load and merge semantic layers from all JSON files in directory
        
        Returns:
            SemanticLayer: Merged semantic layer containing all tables from all files
            
        Raises:
            SemanticLayerError: If no files found or files are invalid
            
        Example:
            repo = MultiFileSemanticRepository()
            semantic = await repo.load_semantic()
            # semantic now contains tables from all JSON files
        """
        # Return cached if available
        if self._cached_semantic is not None:
            logger.debug("Returning cached semantic layer")
            return self._cached_semantic
        
        # Discover all semantic files
        json_files = self._discover_semantic_files()
        
        # Load each file
        layers = []
        for file_path in json_files:
            layer = self._load_single_file(file_path)
            layers.append(layer)
        
        # Merge all layers into one
        merged = layers[0]
        for layer in layers[1:]:
            merged = merged.merge(layer)
        
        logger.info(
            f"Loaded and merged {len(json_files)} semantic files: "
            f"{len(merged.tables)} total tables"
        )
        
        # Cache the result
        self._cached_semantic = merged
        
        return merged
    
    async def reload_semantic(self) -> SemanticLayer:
        """
        Reload semantic layers from all files (clears cache)
        
        Useful when semantic files are updated and you want fresh data.
        
        Returns:
            SemanticLayer: Freshly loaded and merged semantic layer
        """
        # Clear cache
        self._cached_semantic = None
        
        # Load fresh
        return await self.load_semantic()
    
    def get_cached_semantic(self) -> Optional[SemanticLayer]:
        """
        Get cached semantic layer if available
        
        Returns:
            SemanticLayer if cached, None otherwise
            
        Note: This is synchronous and doesn't load from files.
        Use load_semantic() to ensure data is loaded.
        """
        return self._cached_semantic

