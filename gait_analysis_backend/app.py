from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import os
import time
import logging
import subprocess

app = Flask(__name__)
CORS(app)

# Logging configuration
logging.basicConfig(filename='app.log', level=logging.DEBUG)

@app.route('/')
def index():
    return "Gait Analysis Backend is running!"

UPLOAD_FOLDER = 'gait_analysis_backend/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No video file selected"}), 400
    if file and allowed_file(file.filename):
        unique_filename = str(int(time.time())) + "_" + file.filename
        filename = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filename)
        # Process the video using the unique filename
        processed_video_path = process_video(filename)
        # TODO: Process the video using OpenCV/OpenPose here
        return jsonify({"message": "Video Uploaded and Processed", "processed_video": processed_video_path}), 200
    else:
        return jsonify({"error": "Invalid file format"}), 400

def process_video(video_path):
    try:
        # Load the video
        cap = cv2.VideoCapture(video_path)

        # Check if video opened successfully
        if not cap.isOpened():
            print("Error: Could not open video.")
            return

        # Get video properties
        width = int(cap.get(3))
        height = int(cap.get(4))
        fps = cap.get(cv2.CAP_PROP_FPS)  # Get the original video's FPS

        # Extract the base name of the input video (filename without extension)
        base_name = os.path.basename(video_path).rsplit('.', 1)[0]
        
        # Create the filename for the processed video
        processed_filename = base_name + "_processed.mp4"

        # Define the output path for the processed video
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
        
        # Define the codec and create VideoWriter object for .mp4 format
        # Using 'avc1' codec for .mp4 format
        out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'avc1'), fps, (width, height), isColor=False)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Write the frame to the output video
            out.write(gray)

        # Release everything
        cap.release()
        out.release()

        return output_path
    except Exception as e:
        logging.error(f"Error processing video {video_path}: {str(e)}")
        return None
if __name__ == '__main__':
    app.run(debug=True)

def process_openpose(video_path):
    try:
        # Define the path to the OpenPose binary and the output directory
        openpose_bin = "/path/to/openpose/bin"
        output_dir = "/path/to/output/directory"

        # Call OpenPose with the desired arguments
        cmd = [
            openpose_bin,
            "--video", video_path,
            "--write_video", os.path.join(output_dir, "openpose_output.avi"),
            # Add other OpenPose arguments as needed
        ]
        subprocess.run(cmd, check=True)

        # Return the path to the processed video
        return os.path.join(output_dir, "openpose_output.avi")

    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing video with OpenPose: {str(e)}")
        return None