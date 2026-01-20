"""
Query Preprocessor

Extracts structured entities from natural language queries before SQL generation.
This reduces reliance on system prompt rules and makes the system more maintainable.

Extracts:
- Company names and branch names (handles compound names)
- Make/brand names (maps to database codes)
- Validates against database values
"""

import re
from typing import Dict, Optional, List, Tuple
from app.config import get_logger

logger = get_logger(__name__)


class QueryPreprocessor:
    """
    Preprocesses natural language queries to extract structured entities.
    
    Benefits:
    1. Reduces system prompt complexity
    2. Validates entities against database
    3. Handles compound names intelligently
    4. Maps brand names to codes
    """
    
    # Known branch names (cities) - can be loaded from DB dynamically
    KNOWN_BRANCH_NAMES = {
        "mumbai", "bangalore", "bengaluru", "chennai", "delhi", "pune", 
        "hyderabad", "kolkata", "kolkatta", "indore", "baroda", "coimbatore",
        "jaipur", "lucknow", "secunderabad", "guwahati", "hubli", "hosur",
        "belgaum", "kolhapur", "mysuru", "mangaluru", "raipur", "rajkot",
        "solapur", "vijayawada", "bhubaneswar", "aurangabad", "hospet",
        "kalaburagi", "kanpur", "nashik", "cuttack"
    }
    
    # Make/Brand name mappings (common brands to database codes)
    # This should ideally come from a configuration file or database
    MAKE_MAPPINGS = {
        "polycab": "POL",
        "poly cab": "POL",
        "schneider": "SNI",
        "abb": "ABB",
        "legrand": "LEG",
        "hager": "HAG",
        "siemens": "SIE",
        "havells": "HAV",
        "anchor": "ANC",
        "crompton": "CRO",
        "orient": "ORI",
        "bajaj": "BAJ",
        "finolex": "FIN",
        "rr": "RR",
        "delton": "DEL",
    }
    
    # Company name patterns (to identify full company names vs partial)
    COMPANY_SUFFIXES = ["ltd", "llp", "limited", "private limited", "pvt ltd", "inc", "corp"]
    
    def __init__(self, branch_names: Optional[List[str]] = None, make_mappings: Optional[Dict[str, str]] = None):
        """
        Initialize preprocessor.
        
        Args:
            branch_names: Optional list of valid branch names from database
            make_mappings: Optional dict of brand name to code mappings
        """
        if branch_names:
            self.KNOWN_BRANCH_NAMES = {name.lower() for name in branch_names}
        if make_mappings:
            self.MAKE_MAPPINGS.update({k.lower(): v for k, v in make_mappings.items()})
    
    def extract_entities(self, question: str) -> Dict[str, any]:
        """
        Extract structured entities from natural language query.
        
        Returns:
            {
                "company_name": Optional[str],  # Extracted company name
                "branch_name": Optional[str],    # Extracted branch name (validated)
                "make": Optional[str],           # Extracted make/brand (mapped to code)
                "original_question": str,         # Original question
                "enhanced_question": str,        # Question with hints for AI
            }
        """
        question_lower = question.lower()
        
        # Extract company and branch
        company_name, branch_name = self._extract_company_and_branch(question)
        
        # Extract make/brand
        make = self._extract_make(question)
        
        # Build enhanced question with hints
        enhanced_question = self._build_enhanced_question(question, company_name, branch_name, make)
        
        return {
            "company_name": company_name,
            "branch_name": branch_name,
            "make": make,
            "original_question": question,
            "enhanced_question": enhanced_question,
        }
    
    def _extract_company_and_branch(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract company name and branch name from query.
        
        Handles patterns like:
        - "Shree NM Mumbai branch" → company="Shree NM", branch="Mumbai"
        - "in Shree NM Mumbai" → company="Shree NM", branch="Mumbai"
        - "Shree NM Electricals Ltd" → company="Shree NM Electricals Ltd", branch=None
        """
        question_lower = question.lower()
        company_name = None
        branch_name = None
        
        # Pattern 1: "[Company] [Location] branch" or "[Location] branch"
        # Match: "Shree NM Mumbai branch" or "in Shree NM Mumbai branch"
        # Also handle: "list of X items in [Company] [Location] branch"
        # First, try to find pattern with "in" keyword before company
        in_branch_match = re.search(r'in\s+([^,]+?)\s+(\w+)\s+branch', question_lower, re.IGNORECASE)
        if in_branch_match:
            potential_company = in_branch_match.group(1).strip()
            potential_branch = in_branch_match.group(2).strip()
            
            # Check if potential_branch is a known city
            if potential_branch.lower() in self.KNOWN_BRANCH_NAMES:
                branch_name = potential_branch
                # Extract company name (remove common prefixes and query words)
                # Remove common query words from the beginning
                company_clean = re.sub(r'^(list of|items?|products?|show|get|find|all)\s+', '', potential_company, flags=re.IGNORECASE).strip()
                # Remove "items" or "products" from anywhere
                company_clean = re.sub(r'\s+items?\s+', ' ', company_clean, flags=re.IGNORECASE).strip()
                company_clean = re.sub(r'\s+items?$', '', company_clean, flags=re.IGNORECASE).strip()
                # Check if remaining is not just a city and has meaningful content
                if company_clean and company_clean.lower() not in self.KNOWN_BRANCH_NAMES and len(company_clean.split()) <= 5:
                    company_name = company_clean
                return company_name, branch_name
        
        # Pattern 1b: Without "in" keyword
        branch_match = re.search(r'([^,]+?)\s+(\w+)\s+branch', question_lower, re.IGNORECASE)
        if branch_match:
            potential_company = branch_match.group(1).strip()
            potential_branch = branch_match.group(2).strip()
            
            # Check if potential_branch is a known city
            if potential_branch.lower() in self.KNOWN_BRANCH_NAMES:
                branch_name = potential_branch
                # Extract company name (remove common prefixes and query words)
                company_clean = re.sub(r'^(list of|items?|products?|show|get|find|all)\s+', '', potential_company, flags=re.IGNORECASE).strip()
                company_clean = re.sub(r'\s+items?\s+', ' ', company_clean, flags=re.IGNORECASE).strip()
                company_clean = re.sub(r'\s+items?$', '', company_clean, flags=re.IGNORECASE).strip()
                if company_clean and company_clean.lower() not in self.KNOWN_BRANCH_NAMES and len(company_clean.split()) <= 5:
                    company_name = company_clean
                return company_name, branch_name
        
        # Pattern 2: "in [Company] [Location]" or "in [Location]"
        # Match: "in Shree NM Mumbai" (without "branch" keyword)
        # Also handle: "list of X items in [Company] [Location]"
        in_match = re.search(r'in\s+([^,]+?)\s+(\w+)(?:\s|$|branch)', question_lower, re.IGNORECASE)
        if in_match:
            potential_company = in_match.group(1).strip()
            potential_branch = in_match.group(2).strip()
            
            # Check if potential_branch is a known city
            if potential_branch.lower() in self.KNOWN_BRANCH_NAMES:
                branch_name = potential_branch
                # Remove common query words
                company_clean = re.sub(r'^(list of|items?|products?|show|get|find|all)\s+', '', potential_company, flags=re.IGNORECASE).strip()
                company_clean = re.sub(r'\s+(items?|products?)$', '', company_clean, flags=re.IGNORECASE).strip()
                if company_clean and company_clean.lower() not in self.KNOWN_BRANCH_NAMES and len(company_clean.split()) <= 5:
                    company_name = company_clean
                return company_name, branch_name
        
        # Pattern 3: "[Location] branch" (standalone)
        standalone_branch = re.search(r'(\w+)\s+branch', question_lower, re.IGNORECASE)
        if standalone_branch:
            potential_branch = standalone_branch.group(1).strip()
            if potential_branch.lower() in self.KNOWN_BRANCH_NAMES:
                branch_name = potential_branch
                return company_name, branch_name
        
        # Pattern 4: Look for company names with suffixes (Ltd, LLP, etc.)
        company_with_suffix = re.search(
            r'(\w+(?:\s+\w+)*?\s+(?:' + '|'.join(self.COMPANY_SUFFIXES) + '))',
            question_lower,
            re.IGNORECASE
        )
        if company_with_suffix:
            full_company = company_with_suffix.group(1).strip()
            company_name = full_company
            return company_name, branch_name
        
        # Pattern 5: Look for known company patterns (Shree NM, Delton, etc.)
        # This is a fallback - extract potential company names
        common_companies = ["shree nm", "delton", "techmech", "poojapower", "vraj"]
        for company_pattern in common_companies:
            if company_pattern in question_lower:
                # Check if followed by a city name
                pattern_with_city = re.search(
                    rf'{re.escape(company_pattern)}\s+(\w+)',
                    question_lower,
                    re.IGNORECASE
                )
                if pattern_with_city:
                    potential_branch = pattern_with_city.group(1).strip()
                    if potential_branch.lower() in self.KNOWN_BRANCH_NAMES:
                        company_name = company_pattern
                        branch_name = potential_branch
                        return company_name, branch_name
                else:
                    # Just company, no branch
                    company_name = company_pattern
                    return company_name, branch_name
        
        return company_name, branch_name
    
    def _extract_make(self, question: str) -> Optional[str]:
        """
        Extract make/brand name and map to database code.
        
        Returns the database code (e.g., "POL" for "Polycab").
        """
        question_lower = question.lower()
        
        # Check for known brand names
        for brand_name, code in self.MAKE_MAPPINGS.items():
            if brand_name in question_lower:
                return code
        
        return None
    
    def _build_enhanced_question(self, original: str, company: Optional[str], branch: Optional[str], make: Optional[str]) -> str:
        """
        Build enhanced question with extracted entity hints.
        
        This helps the AI understand what entities were extracted without
        changing the original question too much.
        """
        hints = []
        
        if company:
            hints.append(f"Company: {company}")
        if branch:
            hints.append(f"Branch: {branch}")
        if make:
            hints.append(f"Make/Brand code: {make}")
        
        if hints:
            return f"{original} [Extracted entities: {', '.join(hints)}]"
        
        return original

