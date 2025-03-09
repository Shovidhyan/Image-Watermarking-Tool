from flask import Flask, request, render_template, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import os
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['WATERMARK_FOLDER'] = 'watermarked'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['WATERMARK_FOLDER']):
    os.makedirs(app.config['WATERMARK_FOLDER'])

def add_watermark_text(image, watermark_text, position, font_size, font_color):
    # Create a transparent layer for the watermark
    watermark = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark)

    # Load a font (you may need to adjust the path to a font file)
    font = ImageFont.truetype("arial.ttf", font_size)

    # Calculate text position
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    if position == "top-left":
        x, y = 10, 10
    elif position == "top-right":
        x, y = image.width - text_width - 10, 10
    elif position == "bottom-left":
        x, y = 10, image.height - text_height - 10
    elif position == "bottom-right":
        x, y = image.width - text_width - 10, image.height - text_height - 10
    else:  # center
        x = (image.width - text_width) // 2
        y = (image.height - text_height) // 2

    # Convert hex color to RGB tuple
    if font_color.startswith('#'):
        font_color = font_color.lstrip('#')
        font_color = tuple(int(font_color[i:i+2], 16) for i in (0, 2, 4))

    # Add the watermark text with the selected color
    draw.text((x, y), watermark_text, font=font, fill=font_color + (128,))  # Add alpha for transparency

    # Combine the image and watermark
    return Image.alpha_composite(image, watermark)

def add_watermark_image(image, watermark_image_path, position):
    # Open the watermark image
    watermark_image = Image.open(watermark_image_path).convert("RGBA")

    # Resize watermark image to fit within the main image
    watermark_size = (min(watermark_image.width, image.width // 4), min(watermark_image.height, image.height // 4))
    watermark_image = watermark_image.resize(watermark_size, Image.Resampling.LANCZOS)

    # Calculate watermark position
    if position == "top-left":
        x, y = 10, 10
    elif position == "top-right":
        x, y = image.width - watermark_image.width - 10, 10
    elif position == "bottom-left":
        x, y = 10, image.height - watermark_image.height - 10
    elif position == "bottom-right":
        x, y = image.width - watermark_image.width - 10, image.height - watermark_image.height - 10
    else:  # center
        x = (image.width - watermark_image.width) // 2
        y = (image.height - watermark_image.height) // 2

    # Paste the watermark image onto the main image
    image.paste(watermark_image, (x, y), watermark_image)

    return image

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/preview', methods=['POST'])
def preview():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    watermark_text = request.form.get('watermark_text', '')
    watermark_image = request.files.get('watermark_image')
    text_position = request.form.get('text_position', 'center')
    image_position = request.form.get('image_position', 'center')
    font_size = int(request.form.get('font_size', 40))
    font_color = request.form.get('font_color', '#FFFFFF')  # Default to white

    if file:
        # Open the main image
        image = Image.open(file.stream).convert("RGBA")

        # Apply text watermark if provided
        if watermark_text:
            image = add_watermark_text(image, watermark_text, text_position, font_size, font_color)

        # Apply image watermark if provided
        if watermark_image:
            watermark_image_path = os.path.join(app.config['UPLOAD_FOLDER'], watermark_image.filename)
            watermark_image.save(watermark_image_path)
            image = add_watermark_image(image, watermark_image_path, image_position)

        # Save the preview to a bytes buffer
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        # Return the preview image
        return send_file(buffer, mimetype='image/png')

    return jsonify({"error": "Invalid request"}), 400

@app.route('/download', methods=['POST'])
def download():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    watermark_text = request.form.get('watermark_text', '')
    watermark_image = request.files.get('watermark_image')
    text_position = request.form.get('text_position', 'center')
    image_position = request.form.get('image_position', 'center')
    font_size = int(request.form.get('font_size', 40))
    font_color = request.form.get('font_color', '#FFFFFF')  # Default to white

    if file:
        # Save the uploaded file
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(image_path)

        # Open the main image
        image = Image.open(image_path).convert("RGBA")

        # Apply text watermark if provided
        if watermark_text:
            image = add_watermark_text(image, watermark_text, text_position, font_size, font_color)

        # Apply image watermark if provided
        if watermark_image:
            watermark_image_path = os.path.join(app.config['UPLOAD_FOLDER'], watermark_image.filename)
            watermark_image.save(watermark_image_path)
            image = add_watermark_image(image, watermark_image_path, image_position)

        # Save the watermarked image
        output_path = os.path.join(app.config['WATERMARK_FOLDER'], file.filename)
        image.save(output_path, "PNG")

        # Return the watermarked image for download
        return send_file(output_path, as_attachment=True)

    return jsonify({"error": "Invalid request"}), 400

if __name__ == '__main__':
    app.run(debug=True)