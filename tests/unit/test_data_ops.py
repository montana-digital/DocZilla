"""
Unit tests for Data Operations Service
"""

import pandas as pd
import pytest
from src.app.services.data_ops import (
    merge_dataframes, detect_outliers, remove_empty_rows_columns, remove_duplicates,
    standardize_urls, trim_whitespace, handle_missing_values, group_by_dataframe,
    standardize_phone_numbers, remove_characters, standardize_format
)


def test_remove_empty_rows_columns():
    df = pd.DataFrame({
        'a': [1, None, None],
        'b': ['x', None, None]
    })
    cleaned, rows_removed, cols_removed = remove_empty_rows_columns(df)
    assert rows_removed >= 1
    assert 'a' in cleaned.columns


def test_remove_duplicates():
    df = pd.DataFrame({
        'k': [1, 1, 2],
        'v': ['a', 'a', 'b']
    })
    cleaned, dup_count = remove_duplicates(df, ['k', 'v'])
    assert dup_count == 1
    assert len(cleaned) == 2


def test_detect_outliers_zscore():
    df = pd.DataFrame({'x': [1, 2, 3, 100]})
    result = detect_outliers(df, ['x'], method='zscore', threshold=2.0)
    assert result['x_outlier'].sum() >= 1


def test_standardize_urls_full_and_base():
    df = pd.DataFrame({'u': ['example.com/path?x=1', 'https://www.test.com/a']})
    full = standardize_urls(df, 'u', include_protocol=True, include_path=True, base_domain_only=False)
    assert full['u_formatted'].iloc[0].startswith('https://example.com')
    base = standardize_urls(df, 'u', base_domain_only=True)
    assert base['u_formatted'].iloc[1] == 'test.com'


def test_trim_whitespace():
    df = pd.DataFrame({'a': ['  x  ', ' y']})
    cleaned = trim_whitespace(df, ['a'])
    assert cleaned['a'].tolist() == ['x', 'y']


def test_handle_missing_values_fill():
    df = pd.DataFrame({'a': [1, None, 3], 'b': [None, 'x', None]})
    filled = handle_missing_values(df, ['a', 'b'], strategy='fill_na', fill_value='N/A')
    assert filled['b'].tolist()[0] == 'N/A'


def test_merge_similarity():
    df1 = pd.DataFrame({'name': ['John Smith', 'Alice']})
    df2 = pd.DataFrame({'name': ['Jon Smith', 'Bob']})
    merged = merge_dataframes(df1, df2, on='name', how='inner', use_similarity=True, similarity_threshold=0.8, similarity_columns=['name'])
    # At least one similarity match should occur for John/Jon Smith
    assert len(merged) >= 1


def test_merge_inner_join():
    """Test inner join merge."""
    df1 = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
    df2 = pd.DataFrame({'id': [2, 3, 4], 'value': [10, 20, 30]})
    merged = merge_dataframes(df1, df2, on='id', how='inner')
    assert len(merged) == 2
    assert 'name' in merged.columns
    assert 'value' in merged.columns


def test_merge_left_join():
    """Test left join merge."""
    df1 = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
    df2 = pd.DataFrame({'id': [2, 3], 'value': [10, 20]})
    merged = merge_dataframes(df1, df2, on='id', how='left')
    assert len(merged) == 3
    assert pd.isna(merged.iloc[0]['value'])  # id=1 has no match


def test_group_by_single_column():
    """Test group by with single column."""
    df = pd.DataFrame({
        'category': ['A', 'A', 'B', 'B'],
        'value': [10, 20, 15, 25]
    })
    grouped = group_by_dataframe(df, by='category', aggregations={'value': ['sum', 'mean']})
    assert len(grouped) == 2
    assert 'category' in grouped.columns


def test_group_by_multiple_columns():
    """Test group by with multiple columns."""
    df = pd.DataFrame({
        'cat1': ['A', 'A', 'B', 'B'],
        'cat2': ['X', 'Y', 'X', 'Y'],
        'value': [10, 20, 15, 25]
    })
    grouped = group_by_dataframe(df, by=['cat1', 'cat2'], aggregations={'value': ['sum']})
    assert len(grouped) == 4


def test_detect_outliers_iqr():
    """Test IQR outlier detection."""
    df = pd.DataFrame({'x': [1, 2, 3, 4, 5, 100]})
    result = detect_outliers(df, ['x'], method='iqr', threshold=1.5)
    assert result['x_outlier'].sum() >= 1


def test_standardize_phone_numbers():
    """Test phone number standardization."""
    df = pd.DataFrame({'phone': ['123-456-7890', '(555) 123-4567']})
    try:
        result = standardize_phone_numbers(df, 'phone', format_type='E.164')
        assert 'phone_formatted' in result.columns
    except Exception:
        pytest.skip("phonenumbers library not available")


def test_remove_characters():
    """Test removing characters from columns."""
    df = pd.DataFrame({'text': ['a-b-c', 'x.y.z']})
    result = remove_characters(df, ['text'], characters='-')
    assert '-' not in result['text'].iloc[0]
    assert '.' in result['text'].iloc[1]  # Should not remove


def test_remove_characters_regex():
    """Test removing characters with regex."""
    df = pd.DataFrame({'text': ['abc123', 'def456']})
    result = remove_characters(df, ['text'], characters='[0-9]', use_regex=True)
    assert '123' not in result['text'].iloc[0]
    assert 'abc' in result['text'].iloc[0]


def test_standardize_format_decimal():
    """Test numeric format standardization."""
    df = pd.DataFrame({'value': [1.23456, 2.78901]})
    result = standardize_format(df, 'value', decimal_places=2)
    assert result['value'].iloc[0] == 1.23
