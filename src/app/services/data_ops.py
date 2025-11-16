"""
Data Operations Service

Handles data transformations: merge, group-by, cleaning, standardization, outlier detection.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Callable
from rapidfuzz import fuzz
from rapidfuzz.utils import default_process

# Import utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.app.utils.exceptions import OperationalError


def merge_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    on: str | List[str],
    how: str = "inner",
    similarity_threshold: float = 0.8,
    use_similarity: bool = False,
    similarity_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Merge two DataFrames with optional similarity matching.
    
    Args:
        df1: First DataFrame (original)
        df2: Second DataFrame (incoming)
        on: Column(s) to merge on
        how: Join type (inner, outer, left, right)
        similarity_threshold: Threshold for similarity matching (0-1)
        use_similarity: Enable fuzzy matching via rapidfuzz
        similarity_columns: Columns to apply similarity matching (if None, uses 'on' columns)
    
    Returns:
        Merged DataFrame
    
    Raises:
        OperationalError: If merge fails
    """
    try:
        if use_similarity:
            # Perform similarity-based merge
            if similarity_columns is None:
                similarity_columns = on if isinstance(on, list) else [on]
            
            # Create similarity-matched merge
            result = _merge_with_similarity(
                df1, df2, on, how, similarity_threshold, similarity_columns
            )
        else:
            # Standard pandas merge
            result = pd.merge(df1, df2, on=on, how=how)
        
        return result
    except Exception as e:
        raise OperationalError(
            f"Merge failed: {e}",
            user_message="Failed to merge dataframes",
            suggestion="Check column names and data types match"
        ) from e


def _merge_with_similarity(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    on: str | List[str],
    how: str,
    threshold: float,
    similarity_columns: List[str]
) -> pd.DataFrame:
    """Internal function for similarity-based merge."""
    on_cols = on if isinstance(on, list) else [on]
    
    # First try exact match
    exact_match = pd.merge(df1, df2, on=on_cols, how=how, suffixes=('_x', '_y'))
    
    # Find non-matching rows
    if how in ["inner", "left"]:
        unmatched_df1 = df1[~df1[on_cols[0]].isin(df2[on_cols[0]])]
    else:
        unmatched_df1 = pd.DataFrame()
    
    if how in ["inner", "right", "outer"]:
        unmatched_df2 = df2[~df2[on_cols[0]].isin(df1[on_cols[0]])]
    else:
        unmatched_df2 = pd.DataFrame()
    
    # Perform similarity matching on unmatched rows
    if len(unmatched_df1) > 0 and len(unmatched_df2) > 0:
        similarity_matches = []
        
        for idx1, row1 in unmatched_df1.iterrows():
            best_match = None
            best_score = 0
            
            for idx2, row2 in unmatched_df2.iterrows():
                # Calculate similarity for specified columns
                scores = []
                for col in similarity_columns:
                    if col in row1 and col in row2:
                        val1 = str(row1[col]) if pd.notna(row1[col]) else ""
                        val2 = str(row2[col]) if pd.notna(row2[col]) else ""
                        score = fuzz.token_set_ratio(val1, val2) / 100.0
                        scores.append(score)
                
                avg_score = np.mean(scores) if scores else 0
                
                if avg_score >= threshold and avg_score > best_score:
                    best_score = avg_score
                    best_match = idx2
            
            if best_match is not None:
                similarity_matches.append((idx1, best_match, best_score))
        
        # Merge similarity-matched rows
        if similarity_matches:
            matched_indices_df1 = [m[0] for m in similarity_matches]
            matched_indices_df2 = [m[1] for m in similarity_matches]
            
            matched_df1 = unmatched_df1.loc[matched_indices_df1].reset_index(drop=True)
            matched_df2 = unmatched_df2.loc[matched_indices_df2].reset_index(drop=True)
            
            similarity_merged = pd.concat([matched_df1, matched_df2], axis=1)
            # Combine with exact matches
            result = pd.concat([exact_match, similarity_merged], ignore_index=True)
        else:
            result = exact_match
    else:
        result = exact_match
    
    return result


def group_by_dataframe(
    df: pd.DataFrame,
    by: str | List[str],
    aggregations: Dict[str, List[str]]
) -> pd.DataFrame:
    """
    Group DataFrame with multiple aggregations.
    
    Args:
        df: Input DataFrame
        by: Column(s) to group by
        aggregations: Dict of {column: [functions]} where functions are
                      'count', 'sum', 'mean', 'min', 'max', 'median',
                      'std', 'first', 'last', 'nunique'
    
    Returns:
        Grouped DataFrame
    
    Raises:
        OperationalError: If grouping fails
    """
    try:
        by_cols = by if isinstance(by, list) else [by]
        
        # Build aggregation dict
        agg_dict = {}
        for col, funcs in aggregations.items():
            if col not in df.columns:
                raise OperationalError(
                    f"Column not found: {col}",
                    user_message=f"Column '{col}' not found in data",
                    suggestion="Check column name spelling"
                )
            
            agg_dict[col] = funcs
        
        # Perform group by
        grouped = df.groupby(by_cols).agg(agg_dict)
        
        # Flatten column names if multi-index
        if isinstance(grouped.columns, pd.MultiIndex):
            grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
        
        return grouped.reset_index()
    except Exception as e:
        if isinstance(e, OperationalError):
            raise
        raise OperationalError(
            f"Group by failed: {e}",
            user_message="Failed to group data",
            suggestion="Check column names and data types"
        ) from e


def detect_outliers(
    df: pd.DataFrame,
    columns: List[str],
    method: str = "zscore",
    threshold: float = 3.0
) -> pd.DataFrame:
    """
    Detect outliers using z-score or IQR method.
    
    Args:
        df: Input DataFrame
        columns: Numeric columns to analyze
        method: 'zscore' or 'iqr'
        threshold: Z-score threshold (default: 3.0) or IQR multiplier (default: 1.5)
    
    Returns:
        DataFrame with outlier flags added as columns
    """
    result_df = df.copy()
    
    for col in columns:
        if col not in df.columns:
            continue
        
        # Skip non-numeric columns
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        
        if method == "zscore":
            # Z-score method
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            result_df[f"{col}_outlier"] = z_scores > threshold
        else:
            # IQR method
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - (threshold * IQR)
            upper_bound = Q3 + (threshold * IQR)
            result_df[f"{col}_outlier"] = (df[col] < lower_bound) | (df[col] > upper_bound)
    
    return result_df


def remove_empty_rows_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """
    Remove rows and columns where ALL cells are empty or whitespace-only.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Tuple of (cleaned DataFrame, rows_removed, columns_removed)
    """
    original_rows = len(df)
    original_cols = len(df.columns)
    
    # Remove rows where all values are empty/whitespace
    df_cleaned = df.copy()
    df_cleaned = df_cleaned.dropna(how='all')
    
    # Remove rows where all values are whitespace strings
    mask = df_cleaned.apply(
        lambda row: row.astype(str).str.strip().eq('').all() | 
                   row.astype(str).str.strip().eq('nan').all(),
        axis=1
    )
    df_cleaned = df_cleaned[~mask]
    
    # Remove columns where all values are empty/whitespace
    df_cleaned = df_cleaned.dropna(axis=1, how='all')
    
    # Remove columns where all values are whitespace strings
    mask = df_cleaned.apply(
        lambda col: col.astype(str).str.strip().eq('').all() | 
                   col.astype(str).str.strip().eq('nan').all(),
        axis=0
    )
    df_cleaned = df_cleaned.loc[:, ~mask]
    
    rows_removed = original_rows - len(df_cleaned)
    cols_removed = original_cols - len(df_cleaned.columns)
    
    return df_cleaned, rows_removed, cols_removed


def handle_missing_values(
    df: pd.DataFrame,
    columns: List[str],
    strategy: str = "fill_na",
    fill_value: Any = "N/A"
) -> pd.DataFrame:
    """
    Handle missing values in specified columns.
    
    Args:
        df: Input DataFrame
        columns: Columns to process
        strategy: Strategy ('fill_na', 'forward_fill', 'backward_fill', 'mean', 'median', 'drop')
        fill_value: Value to fill (for 'fill_na' strategy)
    
    Returns:
        DataFrame with missing values handled
    """
    result_df = df.copy()
    
    for col in columns:
        if col not in result_df.columns:
            continue
        
        if strategy == "fill_na":
            result_df[col] = result_df[col].fillna(fill_value)
        elif strategy == "forward_fill":
            result_df[col] = result_df[col].ffill()
        elif strategy == "backward_fill":
            result_df[col] = result_df[col].bfill()
        elif strategy == "mean" and pd.api.types.is_numeric_dtype(result_df[col]):
            result_df[col] = result_df[col].fillna(result_df[col].mean())
        elif strategy == "median" and pd.api.types.is_numeric_dtype(result_df[col]):
            result_df[col] = result_df[col].fillna(result_df[col].median())
        elif strategy == "drop":
            result_df = result_df.dropna(subset=[col])
    
    return result_df


def remove_duplicates(
    df: pd.DataFrame,
    columns: List[str],
    keep: str = "first"
) -> tuple[pd.DataFrame, int]:
    """
    Remove duplicate rows based on specified columns.
    
    Args:
        df: Input DataFrame
        columns: Columns to check for duplicates (all must match)
        keep: Which duplicates to keep ('first', 'last', False for all)
    
    Returns:
        Tuple of (cleaned DataFrame, duplicates_removed)
    """
    original_len = len(df)
    result_df = df.drop_duplicates(subset=columns, keep=keep)
    duplicates_removed = original_len - len(result_df)
    
    return result_df, duplicates_removed


def standardize_phone_numbers(
    df: pd.DataFrame,
    column: str,
    format_type: str = "E.164",
    output_column: Optional[str] = None
) -> pd.DataFrame:
    """
    Standardize phone numbers to specified format.
    
    Args:
        df: Input DataFrame
        column: Column containing phone numbers
        format_type: Format type ('E.164', 'National', 'International', 'Dashed', 'Custom')
        output_column: Output column name (default: {column}_formatted)
    
    Returns:
        DataFrame with formatted phone numbers
    """
    try:
        import phonenumbers
        from phonenumbers import NumberParseException
    except ImportError:
        raise OperationalError(
            "phonenumbers library not installed",
            user_message="Phone number formatting requires phonenumbers package",
            suggestion="Install with: pip install phonenumbers"
        )
    
    result_df = df.copy()
    
    if output_column is None:
        output_column = f"{column}_formatted"
    
    def format_phone(phone_str, fmt):
        """Format single phone number."""
        if pd.isna(phone_str) or phone_str == "":
            return ""
        
        try:
            phone_str = str(phone_str).strip()
            # Try to parse as international first
            parsed = phonenumbers.parse(phone_str, None)
            
            if fmt == "E.164":
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            elif fmt == "National":
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
            elif fmt == "International":
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            elif fmt == "Dashed":
                national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
                return national.replace(" ", "-")
            else:
                return phone_str
        except (NumberParseException, Exception):
            # If parsing fails, return original
            return phone_str
    
    result_df[output_column] = result_df[column].apply(
        lambda x: format_phone(x, format_type)
    )
    
    return result_df


def standardize_urls(
    df: pd.DataFrame,
    column: str,
    include_protocol: bool = True,
    include_path: bool = True,
    include_query: bool = False,
    include_fragment: bool = False,
    base_domain_only: bool = False,
    output_column: Optional[str] = None
) -> pd.DataFrame:
    """
    Standardize URLs to specified format.
    
    Args:
        df: Input DataFrame
        column: Column containing URLs
        include_protocol: Include protocol (https://)
        include_path: Include path component
        include_query: Include query string
        include_fragment: Include fragment (#)
        base_domain_only: Return only base domain
        output_column: Output column name (default: {column}_formatted)
    
    Returns:
        DataFrame with formatted URLs
    """
    from urllib.parse import urlparse, urlunparse
    
    result_df = df.copy()
    
    if output_column is None:
        output_column = f"{column}_formatted"
    
    def format_url(url_str):
        """Format single URL."""
        if pd.isna(url_str) or url_str == "":
            return ""
        
        try:
            url_str = str(url_str).strip()
            
            # If no protocol, add https://
            if not url_str.startswith(('http://', 'https://')):
                url_str = 'https://' + url_str
            
            parsed = urlparse(url_str)
            
            if base_domain_only:
                return parsed.netloc.lower().replace('www.', '')
            
            # Build URL from components
            scheme = parsed.scheme if include_protocol else ""
            netloc = parsed.netloc.lower().replace('www.', '')
            path = parsed.path if include_path else ""
            query = parsed.query if include_query else ""
            fragment = parsed.fragment if include_fragment else ""
            
            return urlunparse((scheme, netloc, path, "", query, fragment))
        except Exception:
            return url_str
    
    result_df[output_column] = result_df[column].apply(format_url)
    
    return result_df


def remove_characters(
    df: pd.DataFrame,
    columns: List[str],
    characters: str,
    use_regex: bool = False
) -> pd.DataFrame:
    """
    Remove specified characters from columns.
    
    Args:
        df: Input DataFrame
        columns: Columns to process
        characters: Characters to remove (comma-separated or regex pattern)
        use_regex: Whether characters string is a regex pattern
    
    Returns:
        DataFrame with characters removed
    """
    import re
    
    result_df = df.copy()
    
    for col in columns:
        if col not in result_df.columns:
            continue
        
        if use_regex:
            result_df[col] = result_df[col].astype(str).str.replace(
                characters, '', regex=True
            )
        else:
            # Split comma or space-separated characters
            chars_to_remove = re.split(r'[, ]+', characters)
            for char in chars_to_remove:
                if char:
                    result_df[col] = result_df[col].astype(str).str.replace(char, '')
    
    return result_df


def trim_whitespace(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Trim leading/trailing whitespace from specified columns.
    
    Args:
        df: Input DataFrame
        columns: Columns to process
    
    Returns:
        DataFrame with whitespace trimmed
    """
    result_df = df.copy()
    
    for col in columns:
        if col in result_df.columns and result_df[col].dtype == 'object':
            result_df[col] = result_df[col].astype(str).str.strip()
    
    return result_df


def standardize_format(
    df: pd.DataFrame,
    column: str,
    decimal_places: Optional[int] = None,
    scientific_notation: bool = False
) -> pd.DataFrame:
    """
    Standardize numeric format (decimal places or scientific notation).
    
    Args:
        df: Input DataFrame
        column: Numeric column to format
        decimal_places: Number of decimal places (None = no rounding)
        scientific_notation: Use scientific notation
    
    Returns:
        DataFrame with formatted column
    """
    result_df = df.copy()
    
    if column not in result_df.columns:
        return result_df
    
    if not pd.api.types.is_numeric_dtype(result_df[column]):
        return result_df
    
    if scientific_notation:
        result_df[column] = result_df[column].apply(lambda x: f"{x:.2e}")
    elif decimal_places is not None:
        result_df[column] = result_df[column].round(decimal_places)
    
    return result_df

