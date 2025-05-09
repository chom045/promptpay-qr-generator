import os
import crcmod
import qrcode
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, send_file

app = Flask(__name__)

# Ensure the static folder exists to store generated QR codes
STATIC_DIR = os.path.join(app.root_path, 'static')
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

def calculate_crc16(data):
    """Calculate CRC-16/CCITT-FALSE checksum for the QR code string."""
    crc16 = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, xorOut=0x0000)
    return crc16(data.encode())

def generate_promptpay_qr(amount):
    """Generate a Thai PromptPay QR code with the specified amount and text overlay."""
    # Original QR code string (excluding the checksum part)
    base_string = (
        "00020101021130490016A000000677010112011509940002448431402060431015303764"
        "54{:02d}{}"  # Placeholder for amount length and value
        "5802TH5919EGAT (BHUMIBOL DAM)62240720614020262304282111326304"
    )

    # Format the amount with two decimal places
    amount_str = f"{float(amount):.2f}"
    amount_len = len(amount_str)

    # Create the string with the amount
    qr_string_without_checksum = base_string.format(amount_len, amount_str)

    # Calculate the CRC-16 checksum
    checksum = calculate_crc16(qr_string_without_checksum)
    checksum_hex = f"{checksum:04X}"

    # Append the checksum to complete the QR code string
    final_qr_string = f"{qr_string_without_checksum}{checksum_hex}"

    # Generate the QR code
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(final_qr_string)
    qr.make(fit=True)

    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Calculate dimensions for the new image with space for text
    qr_width, qr_height = qr_img.size
    text_height = 100
    new_img = Image.new("RGB", (qr_width, qr_height + text_height), "white")
    new_img.paste(qr_img, (0, 0))

    # Add text to the image
    draw = ImageDraw.Draw(new_img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()

    text = f"{amount_str} THB"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (qr_width - text_width) // 2
    text_y = qr_height + (50 - text_height) // 2

    draw.text((text_x, text_y), text, fill="black", font=font)

    # Save the image to the static folder
    filename = f"promptpay_qr_{amount_str}.png"
    filepath = os.path.join(STATIC_DIR, filename)
    new_img.save(filepath)

    return filename, final_qr_string

@app.route('/', methods=['GET', 'POST'])
def index():
    qr_image = None
    qr_string = None
    error = None

    if request.method == 'POST':
        try:
            amount = request.form['amount']
            amount = float(amount.strip())
            if amount <= 0:
                error = "Amount must be greater than 0."
            else:
                # Generate the QR code
                qr_filename, qr_string = generate_promptpay_qr(amount)
                qr_image = qr_filename
        except ValueError:
            error = "Invalid amount. Please enter a valid number (e.g., 50.00)."

    return render_template('index.html', qr_image=qr_image, qr_string=qr_string, error=error)

#ถ้าอยาก run local
#if __name__ == "__main__":
#    app.run(debug=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
