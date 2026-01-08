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
from typing import Optional
from app.core.models.semantic import SemanticLayer
from app.repositories.base import SemanticRepository
from app.config import get_settings
from app.core.exceptions import SemanticLayerError


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
    Repository that loads semantic layer from multiple JSON files.
    
    Discovers all *.json files in a directory and merges them into a single SemanticLayer.
    This allows you to have separate semantic files per table.
    """
    
    def __init__(self, semantic_dir: Optional[str] = None):
        """
        Initialize repository with semantic directory path.
        
        Args:
            semantic_dir: Directory containing semantic JSON files.
                         If None, uses metadata/ directory from settings.
        """
        if semantic_dir is None:
            settings = get_settings()
            # Default to metadata/ directory in backend
            semantic_dir = 'metadata'
        
        # Handle both absolute and relative paths
        self.semantic_dir = Path(semantic_dir)
        if not self.semantic_dir.is_absolute():
            # Try from backend directory
            backend_dir = Path(__file__).parent.parent.parent
            potential_path = backend_dir / self.semantic_dir
            if potential_path.exists():
                self.semantic_dir = potential_path
            else:
                # Try from project root
                project_root = backend_dir.parent
                potential_path = project_root / self.semantic_dir
                if potential_path.exists():
                    self.semantic_dir = potential_path
        
        self._cached_semantic: Optional[SemanticLayer] = None
    
    def _discover_semantic_files(self) -> list[Path]:
        """Discover all JSON files in semantic directory"""
        if not self.semantic_dir.exists():
            return []
        
        # Find all .json files, excluding .example files
        json_files = [
            f for f in self.semantic_dir.glob("*.json")
            if not f.name.endswith(".example")
        ]
        return sorted(json_files)
    
    async def load_semantic(self) -> SemanticLayer:
        """
        Load semantic layer from all JSON files in directory and merge them.
        
        Returns:
            SemanticLayer: Merged semantic layer from all files
            
        Raises:
            SemanticLayerError: If directory doesn't exist or files are invalid
        """
        if self._cached_semantic is not None:
            return self._cached_semantic
        
        if not self.semantic_dir.exists():
            raise SemanticLayerError(
                f"Semantic directory not found: {self.semantic_dir}"
            )
        
        json_files = self._discover_semantic_files()
        
        if not json_files:
            raise SemanticLayerError(
                f"No JSON files found in semantic directory: {self.semantic_dir}"
            )
        
        # Load and merge all files
        merged_semantic = None
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                semantic = SemanticLayer.from_dict(data)
                
                if merged_semantic is None:
                    merged_semantic = semantic
                else:
                    # Merge: later files overwrite earlier ones if same table name
                    merged_semantic = merged_semantic.merge(semantic)
                    
            except json.JSONDecodeError as e:
                raise SemanticLayerError(
                    f"Invalid JSON in {json_file}: {e}"
                ) from e
            except Exception as e:
                raise SemanticLayerError(
                    f"Failed to load {json_file}: {e}"
                ) from e
        
        if merged_semantic is None:
            raise SemanticLayerError("No valid semantic data loaded")
        
        # Cache it
        self._cached_semantic = merged_semantic
        
        return merged_semantic
    
    async def reload_semantic(self) -> SemanticLayer:
        """Reload semantic layer (clears cache)"""
        self._cached_semantic = None
        return await self.load_semantic()
    
    def get_cached_semantic(self) -> Optional[SemanticLayer]:
        """Get cached semantic layer if available"""
        return self._cached_semantic

