from flask import Flask, render_template, request
import fitz
import re
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def extract_invoice_data(file_path):

    document = fitz.open(file_path)
    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    data = {}

    match = re.search(r'Place of Supply\s*:\s*(.*?)\nBill To', text, re.S)
    if match:
            place = match.group(1).replace("\n", " ")
            place = place.replace("India", "")
            place = " ".join(place.split())
            data["From City"] = place

        # Consignee name & address
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for i, line in enumerate(lines):
            if line == "Ship To":
                name = lines[i+1]
                address = ""

                for j in range(i+2, len(lines)):
                    if lines[j] != name:
                        address = lines[j].replace("India", "").strip()
                        break

                data["Consignee Name"] = name
                data["To City & Consignee Address"] = address
                break

        # Cargo Value
    match = re.search(r'Total\s*Rs\.\s*([\d,]+\.\d+)', text)
    if match:
            data["Cargo Value"] = match.group(1)

        # Invoice Number
    match = re.search(r'Invoice Number\s*:\s*(\S+)', text)
    if match:
            data["Invoice Number"] = match.group(1)

        # Invoice Date
    match = re.search(r'Invoice Date\s*:\s*(\S+)', text)
    if match:
            data["Invoice Date"] = match.group(1)

        # Vehicle Number
    match = re.search(r'Vehicle No\s*:\s*(\S+)', text)
    if match:
            data["Vehicle Number"] = match.group(1)

        # Item
    match = re.search(r'1\s+(.*?)\s+080\d+', text)
    if match:
            data["Subject Matter insured"] = match.group(1)

        # Quantity
    match = re.search(r'080\d+\s+(\d+)', text)
    if match:
            data["Marks and Numbers"] = match.group(1)

        # Domestic Purchase
    match = re.search(
            r'([\w\s]+?)\s+shall\s+be\s+treated\s+as\s+the\s+insured\s+person',
            text,
            re.IGNORECASE
        )

    if match:
            purchase = " ".join(match.group(1).split())
            data["Domestic Purchase"] = purchase

        # Consignee check
    if "Consignee Name" in data and "Domestic Purchase" in data:

            if data["Consignee Name"].lower() == data["Domestic Purchase"].lower():
                data["Consignee = Purchase"] = "Yes, you can use Domestic Purchase"
            else:
                data["Consignee = Purchase"] = "No, you can Use Domestic Sales"


    return data


@app.route("/", methods=["GET", "POST"])
def index():

    data = None

    if request.method == "POST":

        file = request.files["pdf"]

        if file:
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)

            data = extract_invoice_data(path)

    return render_template("index.html", data=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)