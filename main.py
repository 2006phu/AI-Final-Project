import os
import sys

# Them thu muc source vao duong dan tim kiem module
source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source")
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)

from source.main import main

if __name__ == "__main__":
    main()
