import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from app_gradio_demo import demo

if __name__ == "__main__":
    demo.launch()
