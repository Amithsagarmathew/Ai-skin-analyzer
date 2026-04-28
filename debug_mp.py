import sys
import os

print(f"Python Executable: {sys.executable}")

try:
    import mediapipe as mp
    print(f"MediaPipe Version: {getattr(mp, '__version__', 'Unknown')}")
    print(f"MediaPipe Location: {os.path.dirname(mp.__file__)}")
    
    if hasattr(mp, 'solutions'):
        print("mp.solutions found!")
    else:
        print("mp.solutions NOT found in dir(mp)")
        print(f"Contents of mp: {dir(mp)}")
        
        # Try manual import of solutions
        try:
            from mediapipe.python import solutions
            print("Successfully imported mediapipe.python.solutions manually")
        except ImportError as e:
            print(f"Failed manual import: {e}")

except ImportError as e:
    print(f"Detailed ImportError: {e}")
