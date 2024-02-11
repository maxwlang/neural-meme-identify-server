from flask import Flask, request, jsonify
import cv2
import json
import numpy as np
import os

app = Flask(__name__)

def hex_to_bgr(hex_color):
    # Convert hex color code to BGR format
    hex_color = hex_color.lstrip('#')
    bgr_color = tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0))
    return bgr_color

def replace_color_with_black(image, color_hex, tolerance=20):
    # Convert the image to BGR format
    bgr_color = hex_to_bgr(color_hex)
    
    # Convert BGR color to HSV format for better color matching
    hsv_color = cv2.cvtColor(np.uint8([[bgr_color]]), cv2.COLOR_BGR2HSV)[0][0]

    # Define lower and upper bounds for the specified color with a tolerance range
    lower_color = np.array([hsv_color[0] - tolerance, 220, 220])
    upper_color = np.array([hsv_color[0] + tolerance, 255, 255])

    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Threshold the image to get only pixels with the specified color
    mask = cv2.inRange(hsv_image, lower_color, upper_color)

    # Find contours of objects with the specified color in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    processed_info = []

    # Draw black rectangles in place of objects with the specified color
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)
        word_wrap = x-h

        if word_wrap < 0:
            word_wrap = word_wrap * -1

        processed_info.append({
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "word_wrap": word_wrap,
            "color": color_hex,
            "tolerance": tolerance
        })

    return processed_info

@app.route('/process_image', methods=['POST'])
def process_image():
    if 'file' not in request.files:
        print("Received request without file part")
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    print("Processing file: ", file.filename)

    if file.filename == '':
        print("No selected file")
        return jsonify({"error": "No selected file"}), 400

    image = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    if image is None:
        print("Failed to decode image")
        return jsonify({"error": "Failed to decode image"}), 400

    rectangles = []
    for color in json.loads(request.form['colors']):
        processed = replace_color_with_black(image, color["color"], tolerance=color["tolerance"])
        rectangles.extend(processed)

    print("Image processed")
    return jsonify(rectangles), 200

if __name__ == '__main__':
    is_debug = os.environ.get('DEBUG', False)
    port = os.environ.get('PORT', 8338)
    app.run(debug=is_debug, port=port, host='0.0.0.0')