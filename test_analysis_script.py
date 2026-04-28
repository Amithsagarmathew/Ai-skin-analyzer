import os
import sys
import cv2

# Setup path to import from app
sys.path.append(os.getcwd())

try:
    from app.utils.image_processing import SkinImageProcessor
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

TEST_DIR = r"c:\projects\LCC\Skin Care\project\test_images"

def run_tests():
    processor = SkinImageProcessor()
    
    print("\nStarting Skin Analysis Validation...")
    print(f"{'Image':<25} | {'Result':<10} | {'Acne':<5} | {'Oil':<5} | {'Wrnk':<5} | {'Hydra':<5}")
    print("-" * 75)

    test_cases = [
        ('acne.png', 'high_acne'),
        ('oily.png', 'high_oil'),
        ('wrinkles.png', 'high_wrinkle'),
        ('normal.png', 'balanced'),
        ('5_no_face_noise.jpg', 'fail')
    ]

    for filename, expectation in test_cases:
        filepath = os.path.join(TEST_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"{filename:<25} | MISSING")
            continue
            
        # Simulate Django File Upload by opening as binary
        with open(filepath, 'rb') as f:
            # We can use processor.process_pipeline directly!
            success, result = processor.process_pipeline(f)
            
            if not success:
                if expectation == 'fail':
                     print(f"{filename:<25} | PASSED (Expected Fail: {result})")
                     continue
                else:
                     # Force analysis for synthetic images that fail detection
                     # This helps us verify the SCORING logic (redness/dots) even if face detection misses
                     status_msg = "NO FACE (Forced)"
                     f.seek(0)
                     img_raw = processor.load_image(f)
                     result = processor.preprocess(img_raw) # Preprocess manually

            # If success, result is the processed image. Run analysis.
            scores = processor.analyze_skin(result)
            
            # Validation Logic
            if not success and expectation != 'fail':
                 # Use the status_msg set above
                 pass
            else:
                 status_msg = "OK"

            if expectation == 'high_acne' and scores['acne'] < 20: status_msg += " LOW ACNE?"
            if expectation == 'high_oil' and scores['oiliness'] < 20: status_msg += " LOW OIL?"
            
            print(f"{filename:<25} | {status_msg:<16} | {scores['acne']:<5} | {scores['oiliness']:<5} | {scores['wrinkles']:<5} | {scores['hydration']:<5}")

if __name__ == "__main__":
    run_tests()
