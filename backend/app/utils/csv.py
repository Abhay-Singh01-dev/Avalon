from typing import IO, List, Dict, Any, Union
import csv
import logging
import io
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)

async def read_csv(
    file: Union[IO[bytes], str], 
    delimiter: str = ',', 
    encoding: str = 'utf-8',
    sample_size: int = 5
) -> Dict[str, Any]:
    """
    Read and parse a CSV file.
    
    Args:
        file: File-like object or file path
        delimiter: CSV delimiter
        encoding: File encoding
        sample_size: Number of rows to include in the sample
        
    Returns:
        Dictionary containing the parsed CSV data
    """
    try:
        # If file is bytes, decode it
        if isinstance(file, bytes):
            file = io.StringIO(file.decode(encoding))
        
        # Read the CSV file with pandas for better handling of different formats
        df = pd.read_csv(file, delimiter=delimiter, encoding=encoding, nrows=1000)  # Limit to 1000 rows for preview
        
        # Get sample data
        sample = df.head(sample_size).fillna('').to_dict(orient='records')
        
        # Get column information
        columns = [{
            'name': col,
            'type': str(df[col].dtype),
            'non_null_count': int(df[col].count()),
            'unique_count': int(df[col].nunique()),
            'sample_values': df[col].dropna().head(3).tolist()
        } for col in df.columns]
        
        return {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': columns,
            'sample_data': sample,
            'file_info': {
                'encoding': encoding,
                'delimiter': delimiter,
            }
        }
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        raise ValueError(f"Could not read CSV file: {e}")

async def write_csv(
    data: List[Dict[str, Any]], 
    output_file: Optional[IO] = None,
    delimiter: str = ',',
    encoding: str = 'utf-8'
) -> Optional[str]:
    """
    Write data to a CSV file or return as string.
    
    Args:
        data: List of dictionaries to write as CSV rows
        output_file: Optional file-like object to write to
        delimiter: CSV delimiter
        encoding: Output encoding
        
    Returns:
        If no output_file is provided, returns the CSV data as a string.
        Otherwise, writes to the file and returns None.
    """
    if not data:
        return "" if output_file is None else None
    
    try:
        # Get all unique keys from the data
        fieldnames = set()
        for row in data:
            fieldnames.update(row.keys())
        fieldnames = sorted(fieldnames)
        
        if output_file is None:
            # Return as string
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue()
        else:
            # Write to file
            writer = csv.DictWriter(output_file, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
            return None
    except Exception as e:
        logger.error(f"Error writing CSV: {e}")
        raise ValueError(f"Could not write CSV: {e}")
