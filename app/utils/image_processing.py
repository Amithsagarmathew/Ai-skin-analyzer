import cv2
import numpy as np
import mediapipe as mp
import os
from transformers import pipeline, ViTImageProcessor, ViTForImageClassification
from PIL import Image as PILImage

# Import Tasks API
try:
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
except ImportError:
    print("MediaPipe Tasks API not found. Please ensure mediapipe is installed.")

class SkinImageProcessor:
    def __init__(self):
        # 1. Initialize MediaPipe Face Landmarker
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'face_landmarker.task')
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}. Please run download_model.py.")
            
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1)
        self.detector = vision.FaceLandmarker.create_from_options(options)

        # 2. Initialize Hugging Face Pipeline (Explicit Load)
        print("Loading HF Model...")
        try:
            model_name = "varun1505/face-characteristics"
            processor = ViTImageProcessor.from_pretrained(model_name)
            model = ViTForImageClassification.from_pretrained(model_name)
            self.hf_classifier = pipeline("image-classification", model=model, image_processor=processor)
            print("HF Model Loaded Successfully.")
        except Exception as e:
            print(f"Warning: Failed to load HF Model: {e}")
            self.hf_classifier = None

        # Region Indices
        self.IDX_FOREHEAD = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
        self.IDX_NOSE = [168, 6, 197, 195, 5, 4, 1, 19, 94, 2]
        self.IDX_CHEEK_L = [330, 347, 346, 352, 450, 427, 434, 430, 431, 266, 425]
        self.IDX_CHEEK_R = [101, 118, 117, 123, 230, 207, 214, 210, 211, 36, 205]
        self.IDX_UNDER_EYE_L = [33, 246, 161, 160, 159, 158, 157, 173, 133]
        self.IDX_UNDER_EYE_R = [362, 398, 384, 385, 386, 387, 388, 466, 263]

    def load_image(self, file_stream):
        try:
            if hasattr(file_stream, 'seek'):
                file_stream.seek(0)
            file_bytes = np.asarray(bytearray(file_stream.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            print(f"Error loading image: {e}")
            return None

    def detect_face_mesh(self, image):
        if image is None: return None
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.detector.detect(mp_image)
        if result.face_landmarks:
            return result.face_landmarks[0]
        return None

    def _crop_face(self, image, landmarks):
        h, w = image.shape[:2]
        xs = [l.x * w for l in landmarks]
        ys = [l.y * h for l in landmarks]
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        
        # Add Padding (20%)
        pad_x = (x2 - x1) * 0.2
        pad_y = (y2 - y1) * 0.2
        x1 = max(0, int(x1 - pad_x))
        y1 = max(0, int(y1 - pad_y))
        x2 = min(w, int(x2 + pad_x))
        y2 = min(h, int(y2 + pad_y))
        
        crop = image[y1:y2, x1:x2]
        # Convert to PIL for HF
        return PILImage.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))

    def _get_mask(self, image, landmarks, indices):
        h, w = image.shape[:2]
        points = []
        for i in indices:
            if i < len(landmarks):
                pt = landmarks[i]
                points.append((int(pt.x * w), int(pt.y * h)))
        mask = np.zeros((h, w), dtype=np.uint8)
        if points:
            hull = cv2.convexHull(np.array(points))
            cv2.fillConvexPoly(mask, hull, 255)
        return mask

    def validate_quality(self, image):
        if image is None: return False, "Invalid image."
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if cv2.Laplacian(gray, cv2.CV_64F).var() < 50: return False, "Image too blurry."
        return True, "Quality OK"

    def preprocess(self, image):
        target_width = 512
        h, w = image.shape[:2]
        ratio = target_width / float(w)
        target_height = int(h * ratio)
        resized = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)
        return cv2.fastNlMeansDenoisingColored(resized, None, 5, 5, 7, 21)

    def process_pipeline(self, file_stream):
        img = self.load_image(file_stream)
        if img is None: return False, "Failed to decode."
        is_val, msg = self.validate_quality(img)
        if not is_val: return False, msg
        processed = self.preprocess(img)
        if not self.detect_face_mesh(processed):
            return False, "No face detected."
        return True, processed

    def _get_severity(self, score):
        if score < 25: return "Low"
        if score < 50: return "Mild"
        if score < 75: return "Moderate"
        return "Severe"

    def analyze_skin(self, image):
        lms = self.detect_face_mesh(image)
        if not lms: return {'scores': {}, 'health_score': 0}

        # --- HYBRID ANALYTICS ---
        
        # 1. Hugging Face AI Analysis
        hf_scores = {}
        if self.hf_classifier:
            try:
                pil_face = self._crop_face(image, lms)
                ai_results = self.hf_classifier(pil_face)
                # Parse results: [{'label': 'acne', 'score': 0.9}, ...]
                for res in ai_results:
                    label = res['label'].lower().replace(' ', '_')
                    score = res['score'] * 100
                    hf_scores[label] = score
                print(f"HF Scores: {hf_scores}")
            except Exception as e:
                print(f"HF Inference Error: {e}")

        # 2. Rule-Based Analysis (OpenCV)
        
        # Rule: Acne (LAB Hybrid)
        mask_cheek_l = self._get_mask(image, lms, self.IDX_CHEEK_L)
        mask_cheek_r = self._get_mask(image, lms, self.IDX_CHEEK_R)
        cheek_mask = cv2.bitwise_or(mask_cheek_l, mask_cheek_r)
        
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        a_blur = cv2.medianBlur(a, 21)
        a_diff = cv2.subtract(a, a_blur)
        _, acne_spots_lab = cv2.threshold(a_diff, 5, 255, cv2.THRESH_BINARY)
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask_red1 = cv2.inRange(hsv, np.array([0, 80, 50]), np.array([10, 255, 255]))
        mask_red2 = cv2.inRange(hsv, np.array([170, 80, 50]), np.array([180, 255, 255]))
        acne_spots_hsv = cv2.bitwise_or(mask_red1, mask_red2)
        
        acne_combined = cv2.bitwise_or(acne_spots_lab, acne_spots_hsv)
        acne_region = cv2.bitwise_and(acne_combined, acne_combined, mask=cheek_mask)
        rule_acne = min(int((np.count_nonzero(acne_region) / (np.count_nonzero(cheek_mask)+1)) * 100 * 25), 100)

        # Rule: Oiliness (Specular)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mask_forehead = self._get_mask(image, lms, self.IDX_FOREHEAD)
        mask_nose = self._get_mask(image, lms, self.IDX_NOSE)
        t_zone_mask = cv2.bitwise_or(mask_forehead, mask_nose)
        
        l_channel = l # from LAB
        l_blur = cv2.GaussianBlur(l_channel, (21, 21), 0)
        l_diff = cv2.subtract(l_channel, l_blur)
        _, oil_spots = cv2.threshold(l_diff, 10, 255, cv2.THRESH_BINARY)
        _, high_bright = cv2.threshold(l_channel, 200, 255, cv2.THRESH_BINARY)
        real_shine = cv2.bitwise_and(oil_spots, high_bright)
        
        # Add Low Saturation Check for Oil (Oil is usually white specular, not colored)
        s_channel = hsv[:,:,1]
        _, low_sat = cv2.threshold(s_channel, 100, 255, cv2.THRESH_BINARY_INV) # Sat < 100
        true_oil = cv2.bitwise_and(real_shine, low_sat)
        
        oily_region = cv2.bitwise_and(true_oil, true_oil, mask=t_zone_mask)
        rule_oiliness = min(int((np.count_nonzero(oily_region) / (np.count_nonzero(t_zone_mask)+1)) * 100 * 20), 100)

        # Rule: Wrinkles (Edges)
        edges = cv2.Canny(gray, 50, 150)
        wrinkle_region = cv2.bitwise_and(edges, edges, mask=mask_forehead)
        rule_wrinkles = min(int((np.count_nonzero(wrinkle_region) / (np.count_nonzero(mask_forehead)+1)) * 100 * 10), 100)

        # Rule: Dark Circles
        v_channel = hsv[:,:,2]
        mask_under_l = self._get_mask(image, lms, self.IDX_UNDER_EYE_L)
        under_mean = cv2.mean(v_channel, mask=mask_under_l)[0]
        cheek_mean = cv2.mean(v_channel, mask=mask_cheek_l)[0]
        rule_dark_circles = 0
        # Increased threshold from 5 to 15 to avoid false positives on normal shadows
        if cheek_mean > 0 and (cheek_mean - under_mean) > 15:
             rule_dark_circles = min(int((cheek_mean - under_mean) * 3), 100)

        # --- BLENDING LOGIC ---
        
        # Acne: Smart Blend
        hf_acne = hf_scores.get('acne', 0)
        # If AI says "Clean" (<30) but Rule says "Severe" (>80), Rule is likely detecting Pink Skin.
        if hf_acne < 30 and rule_acne > 80:
            final_acne = (hf_acne + rule_acne) / 3 # Suppress false positive
        else:
            final_acne = max(rule_acne, hf_acne) # Otherwise trust the stronger signal (e.g. synthetic dots)
        
        # Pigmentation: Pure AI
        final_pigmentation = hf_scores.get('skin_pigmentation', 0)
        
        # Redness: Pure AI
        final_redness = hf_scores.get('skin_redness', hf_scores.get('rosacea', 0))
        
        # Oiliness: Weighted Blend
        hf_oily = hf_scores.get('oily_skin', 0)
        # Rule is better for shine, AI matches "oily texture"
        final_oiliness = (rule_oiliness * 0.6) + (hf_oily * 0.4)
        
        # Wrinkles: Blend
        hf_wrinkles = hf_scores.get('wrinkles', hf_scores.get('wrinkled_face', 0))
        final_wrinkles = max(rule_wrinkles, hf_wrinkles)
        
        # Dark Circles: Blend
        hf_circles = hf_scores.get('dark_circles', hf_scores.get('bags_under_eyes', 0))
        # Logically average them to avoid extreme outliers
        final_dark_circles = (rule_dark_circles + hf_circles) / 2

        # Dryness: Composite Metric
        # Dry skin = High Wrinkles + Low Oil + High Pigmentation/Texture
        final_dryness = (final_wrinkles * 0.4) + (max(0, 100 - final_oiliness) * 0.3) + (final_pigmentation * 0.3)
        
        # Hydration (Inverse of dryness/issues)
        hydration = max(0, 100 - final_dryness)

        # Health Score
        # Weights: Acne (high), Pigmentation (med), Wrinkles (med), Redness (med)
        defects = (final_acne * 1.5) + (final_pigmentation * 1.0) + (final_wrinkles * 1.0) + (final_redness * 1.0) + (final_dark_circles * 0.5) + (max(0, final_oiliness-50) * 0.5)
        health_score = max(0, int(100 - (defects / 5.5))) # divider adjusted sum of weights approx
        
        # Severities
        severities = {
            'acne': self._get_severity(final_acne),
            'oiliness': self._get_severity(final_oiliness),
            'wrinkles': self._get_severity(final_wrinkles),
            'dark_circles': self._get_severity(final_dark_circles),
            'pigmentation': self._get_severity(final_pigmentation),
            'redness': self._get_severity(final_redness),
            'dryness': self._get_severity(final_dryness),
            'hydration': "Good" if hydration > 60 else "Poor"
        }
        
        # Skin Type
        skin_type = "Normal"
        if final_oiliness > 60: skin_type = "Oily"
        elif final_dryness > 60: skin_type = "Dry"
        elif final_oiliness > 40 and final_dryness < 40: skin_type = "Combination"
        if final_acne > 50 or final_redness > 50: skin_type += " / Sensitive"

        return {
            'scores': {
                'acne': int(final_acne),
                'oiliness': int(final_oiliness),
                'wrinkles': int(final_wrinkles),
                'hydration': int(hydration),
                'dark_circles': int(final_dark_circles),
                'pigmentation': int(final_pigmentation),
                'redness': int(final_redness),
                'dryness': int(final_dryness)
            },
            'severities': severities,
            'skin_type': skin_type,
            'health_score': health_score
        }
