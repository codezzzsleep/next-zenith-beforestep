"""CLI for independently versioned learned navigation, outside frozen src/."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experimental.navigation.cli import main

if __name__ == '__main__':
    main()
