"""
Semantic Layer Domain Model

Represents the semantic layer that defines available tables, columns, and business logic.
This is a pure domain model - no framework dependencies.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Column:
    """Represents a column in a table"""
    name: str
    type: str  # "dimension", "measure", "date"
    description: Optional[str] = None
    role: Optional[str] = None  # "name", "code", "id"
    preferred: bool = False
    aliases: List[str] = field(default_factory=list)  # Alternative names for this column
    
    def is_dimension(self) -> bool:
        """Check if column is a dimension"""
        return self.type == "dimension"
    
    def is_measure(self) -> bool:
        """Check if column is a measure"""
        return self.type == "measure"
    
    def is_date(self) -> bool:
        """Check if column is a date"""
        return self.type == "date"


@dataclass
class DerivedMeasure:
    """Represents a derived measure (calculated metric)"""
    name: str
    expression: str  # SQL expression
    type: str  # "ratio", "sum", "average", etc.
    description: Optional[str] = None


@dataclass
class Table:
    """Represents a table in the semantic layer"""
    name: str
    description: Optional[str] = None
    columns: Dict[str, Column] = field(default_factory=dict)
    dimensions: List[str] = field(default_factory=list)
    measures: List[str] = field(default_factory=list)
    time_columns: List[str] = field(default_factory=list)
    derived_measures: List[DerivedMeasure] = field(default_factory=list)
    quality_rules: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_column(self, column_name: str) -> Optional[Column]:
        """Get a column by name"""
        return self.columns.get(column_name)
    
    def has_column(self, column_name: str) -> bool:
        """Check if table has a column"""
        return column_name in self.columns
    
    def is_dimension(self, column_name: str) -> bool:
        """Check if a column is a dimension"""
        return column_name in self.dimensions
    
    def is_measure(self, column_name: str) -> bool:
        """Check if a column is a measure"""
        return column_name in self.measures
    
    def is_time_column(self, column_name: str) -> bool:
        """Check if a column is a time column"""
        return column_name in self.time_columns


@dataclass
class SemanticLayer:
    """
    Represents the complete semantic layer
    
    This defines what tables, columns, and business logic are available.
    """
    tables: Dict[str, Table] = field(default_factory=dict)
    
    def get_table(self, table_name: str) -> Optional[Table]:
        """Get a table by name"""
        return self.tables.get(table_name)
    
    def has_table(self, table_name: str) -> bool:
        """Check if semantic layer has a table"""
        return table_name in self.tables
    
    def get_all_table_names(self) -> List[str]:
        """Get all table names"""
        return list(self.tables.keys())
    
    def validate_column_exists(self, table_name: str, column_name: str) -> bool:
        """Validate that a column exists in a table"""
        table = self.get_table(table_name)
        if not table:
            return False
        return table.has_column(column_name)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SemanticLayer":
        """
        Create SemanticLayer from dictionary (e.g., from JSON)
        
        This is how we load semantic.json into domain models.
        """
        tables = {}
        
        for table_name, table_data in data.get("tables", {}).items():
            # Build columns
            columns = {}
            for col_name, col_data in table_data.get("columns", {}).items():
                columns[col_name] = Column(
                    name=col_name,
                    type=col_data.get("type", "dimension"),
                    description=col_data.get("description"),
                    role=col_data.get("role"),
                    preferred=col_data.get("preferred", False),
                    aliases=col_data.get("aliases", [])  # Load aliases from JSON
                )
            
            # Build derived measures
            derived_measures = []
            for dm_data in table_data.get("derived_measures", []):
                derived_measures.append(DerivedMeasure(
                    name=dm_data.get("name"),
                    expression=dm_data.get("expression"),
                    type=dm_data.get("type", "sum"),
                    description=dm_data.get("description")
                ))
            
            tables[table_name] = Table(
                name=table_name,
                description=table_data.get("description"),
                columns=columns,
                dimensions=table_data.get("dimensions", []),
                measures=table_data.get("measures", []),
                time_columns=table_data.get("time_columns", []),
                derived_measures=derived_measures,
                quality_rules=table_data.get("quality_rules", [])
            )
        
        return cls(tables=tables)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert SemanticLayer back to dictionary (e.g., for JSON serialization)
        
        This is useful when we need to send semantic layer to AI as context.
        """
        return {
            "tables": {
                table_name: {
                    "description": table.description,
                    "columns": {
                        col_name: {
                            "type": col.type,
                            "description": col.description,
                            "role": col.role,
                            "preferred": col.preferred,
                            "aliases": col.aliases  # Include aliases so AI can use them
                        }
                        for col_name, col in table.columns.items()
                    },
                    "dimensions": table.dimensions,
                    "measures": table.measures,
                    "time_columns": table.time_columns,
                    "derived_measures": [
                        {
                            "name": dm.name,
                            "expression": dm.expression,
                            "type": dm.type,
                            "description": dm.description
                        }
                        for dm in table.derived_measures
                    ],
                    "quality_rules": table.quality_rules
                }
                for table_name, table in self.tables.items()
            }
        }

