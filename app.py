from flask import Flask, render_template, request
import pdfplumber
import re
from collections import defaultdict
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ----------------------------
# CONFIG
# ----------------------------
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ✅ Ensure uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ----------------------------
# PDF ANALYSIS FUNCTION
# ----------------------------
def analyze_pdf(pdf_path, words, min_qty):
    word_results = {word: [] for word in words}
    qty_results = []
    name_counts = defaultdict(int)
    name_pages = defaultdict(list)

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_number = i + 1
            text = page.extract_text()

            if not text:
                continue

            lines = text.split("\n")

            # ----------------------------
            # NAME EXTRACTION
            # ----------------------------
            for idx, line in enumerate(lines):
                if "Customer Address" in line:
                    j = idx + 1
                    while j < len(lines) and lines[j].strip() == "":
                        j += 1

                    if j < len(lines):
                        name = lines[j].strip()
                        name_counts[name] += 1
                        name_pages[name].append(page_number)

            # ----------------------------
            # WORD SEARCH
            # ----------------------------
            for word in words:
                if word.lower() in text.lower():
                    word_results[word].append(page_number)

            # ----------------------------
            # QTY EXTRACTION
            # ----------------------------
            for idx, line in enumerate(lines):

                # Case 1: Same line
                match = re.search(r'Free\s+Size\s+(\d+)', line)
                if match:
                    qty = int(match.group(1))
                    if qty >= min_qty:
                        qty_results.append({
                            "page": page_number,
                            "qty": qty
                        })
                    continue

                # Case 2: Next line
                if "Free Size" in line and idx + 1 < len(lines):
                    next_line = lines[idx + 1].strip()
                    if next_line.isdigit():
                        qty = int(next_line)
                        if qty >= min_qty:
                            qty_results.append({
                                "page": page_number,
                                "qty": qty
                            })

    return word_results, qty_results, dict(name_counts), dict(name_pages)


# ----------------------------
# FULL NAME
# ----------------------------
def get_full_name_counts(name_counts, name_pages, name_min):
    result = {}

    for name, count in name_counts.items():
        if count > name_min:
            pages = sorted(set(name_pages[name]))
            result[name] = {
                "count": count,
                "pages": ",".join(map(str, pages))
            }

    return result


# ----------------------------
# FIRST NAME GROUPING
# ----------------------------
def get_first_name_counts(name_counts, name_pages, name_min):
    first_name_counts = defaultdict(int)
    first_name_pages = defaultdict(list)

    for full_name, count in name_counts.items():
        parts = full_name.split()
        if parts:
            first_name = parts[0]
            first_name_counts[first_name] += count
            first_name_pages[first_name].extend(name_pages[full_name])

    result = {}

    for name, count in first_name_counts.items():
        if count > name_min:
            pages = sorted(set(first_name_pages[name]))
            result[name] = {
                "count": count,
                "pages": ",".join(map(str, pages))
            }

    return result


# ----------------------------
# ROUTE
# ----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("pdf")

        if file and file.filename != "":
            # ✅ Secure filename
            filename = secure_filename(file.filename)

            # ✅ Save path
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            # Save file
            file.save(file_path)

            # Get inputs
            words = request.form.get("words", "").split(",")
            words = [w.strip() for w in words if w.strip()]

            min_qty = int(request.form.get("min_qty", 1))
            name_min = int(request.form.get("name_min", 1))

            # Process PDF
            word_results, qty_results, name_counts, name_pages = analyze_pdf(
                file_path, words, min_qty
            )

            full_name_result = get_full_name_counts(name_counts, name_pages, name_min)
            first_name_result = get_first_name_counts(name_counts, name_pages, name_min)

            return render_template(
                "result.html",
                word_results=word_results,
                qty_results=qty_results,
                full_name_result=full_name_result,
                first_name_result=first_name_result
            )

    return render_template("index.html")


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)