🧴 AI Skin Analyzer

An intelligent web-based application that analyzes facial skin conditions using Artificial Intelligence and Computer Vision. The system detects multiple skin attributes such as acne, oiliness, wrinkles, pigmentation, and provides personalized skincare insights.

🚀 Features

📸 Upload facial image for analysis
🤖 AI-based skin condition detection
🧠 Hybrid analysis (Deep Learning + Image Processing)
📊 Detailed skin metrics:
Acne detection
Oiliness level
Wrinkle estimation
Dark circles detection
Pigmentation & redness
🧾 Skin type classification:
Oily / Dry / Normal / Combination / Sensitive
📈 Skin health score calculation
🧴 Personalized skincare recommendations
🗂️ Analysis history tracking
👤 User profile dashboard
🧠 AI Implementation

This project uses a Hybrid AI Approach:

🔹 1. Deep Learning (Machine Learning)
Vision Transformer (ViT) model via Hugging Face
Detects:
Acne
Pigmentation
Redness
Wrinkles

🔹 2. MediaPipe (ML-based Face Detection)
Detects facial landmarks
Extracts regions like:
Forehead
Cheeks
Nose
Under-eye area

🔹 3. Rule-Based Computer Vision (OpenCV)
Oiliness detection (brightness analysis)
Acne spot detection (color segmentation)
Wrinkle detection (edge detection)
Dark circle detection (intensity comparison)

🔹 4. Hybrid Decision System
Combines AI predictions + rule-based analysis
Improves accuracy and reduces false positives


🛠️ Tech Stack

🔹 Frontend
HTML5, CSS3
Bootstrap 5
JavaScript
Chart.js

🔹 Backend
Python
Django

🔹 AI & Computer Vision
OpenCV
MediaPipe
TensorFlow / Keras
Hugging Face Transformers
