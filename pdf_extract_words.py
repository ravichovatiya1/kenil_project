import pdfplumber
import re
from collections import defaultdict

# ----------------------------
# MAIN ANALYSIS FUNCTION
# ----------------------------
def analyze_pdf(pdf_path, words, min_qty):
    word_results = {word: [] for word in words}
    qty_results = []
    name_counts = defaultdict(int)
    name_pages = defaultdict(list)   # 👈 NEW (store page numbers)

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
                        name_pages[name].append(page_number)  # 👈 store page

            # ----------------------------
            # WORD SEARCH
            # ----------------------------
            for word in words:
                if word.lower() in text.lower():
                    word_results[word].append(page_number)

            # ----------------------------
            # QTY EXTRACTION (FINAL FIX)
            # ----------------------------
            for idx, line in enumerate(lines):

                # Case 1: Qty is on SAME line (most common in your PDF)
                match = re.search(r'Free\s+Size\s+(\d+)', line)
                if match:
                    qty = int(match.group(1))

                    if qty >= min_qty:
                        qty_results.append({
                            "page": page_number,
                            "qty": qty
                        })
                    continue  # move to next line

                # Case 2: Qty is on NEXT line (fallback layout)
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
# FULL NAME FUNCTION
# ----------------------------
def get_full_name_counts(name_counts, name_pages, name_min):
    result = {}

    for name, count in name_counts.items():
        if count > name_min:
            pages = sorted(set(name_pages[name]))
            page_str = ",".join(map(str, pages))
            result[name] = {"count": count, "pages": page_str}

    return result


# ----------------------------
# FIRST NAME GROUPING FUNCTION
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
            page_str = ",".join(map(str, pages))
            result[name] = {"count": count, "pages": page_str}

    return result


# ----------------------------
# USAGE
# ----------------------------
pdf_path = "Sub_Order_Labels.pdf"

words = ["Gowtham", "ganga marathi", "Navsari"]
min_qty = 2
name_min = 1

word_results, qty_results, name_counts, name_pages = analyze_pdf(pdf_path, words, min_qty)


# ----------------------------
# OUTPUT
# ----------------------------
print("\nWORD RESULTS:")
for word, pages in word_results.items():
    print(f"{word}: {pages}")

print("\nQTY RESULTS:")
for item in qty_results:
    print(f"Page {item['page']} → Qty {item['qty']}")

# ----------------------------
# FULL NAME OUTPUT
# ----------------------------
full_name_result = get_full_name_counts(name_counts, name_pages, name_min)

print("\nFULL NAME COUNTS:")
for name, data in full_name_result.items():
    print(f"{name} → Count: {data['count']} | Pages: {data['pages']}")

# ----------------------------
# FIRST NAME GROUPED OUTPUT
# ----------------------------
first_name_result = get_first_name_counts(name_counts, name_pages, name_min)

print("\nFIRST NAME COUNTS (GROUPED):")
for name, data in first_name_result.items():
    print(f"{name} → Count: {data['count']} | Pages: {data['pages']}")