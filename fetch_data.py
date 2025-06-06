#!/usr/bin/env python3
"""
ENTSO-E Data Fetcher - Convenience Wrapper

This is a simple wrapper script that transparently passes all command-line arguments
to the main data retriever located in src/entso_py_retriever.py. This allows users
to run data fetching from the root directory without needing to remember the src/ path.

Usage:
    python fetch_data.py [all arguments for entso_py_retriever.py]

Examples:
    python fetch_data.py --countries NL --years 3 --local-time
    python fetch_data.py --countries NL,DE,FR --years 5 --combined
    python fetch_data.py --help

This wrapper is equivalent to running:
    python src/entso_py_retriever.py [arguments]
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """
    Main wrapper function that passes all arguments to the data retriever.
    """
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Path to the actual data retriever
    retriever_path = script_dir / "src" / "entso_py_retriever.py"
    
    # Check if the retriever exists
    if not retriever_path.exists():
        print(f"Error: Data retriever not found at {retriever_path}")
        print("Please ensure the project structure is correct.")
        sys.exit(1)
    
    # Build the command to execute
    cmd = [sys.executable, str(retriever_path)] + sys.argv[1:]
    
    # Show what we're executing (for transparency)
    print(f"→ Executing: python {retriever_path.relative_to(script_dir)} {' '.join(sys.argv[1:])}")
    print()
    
    try:
        # Execute the data retriever with all passed arguments
        result = subprocess.run(cmd, cwd=script_dir, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\nData fetching interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error executing data retriever: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
