from flask import Flask, jsonify, send_file, request
import os
import datetime
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch


app = Flask(__name__)


@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    """
    Generate a dummy PDF file.
    """
    try:
        payload = request.json
        generate_invoice(payload['issuer_details'], payload['buyer_details'], payload['items'], payload['invoice_number'] + '.pdf', payload['invoice_number'])
        return jsonify({"message": "PDF generated successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/view-pdf', methods=['GET'])
def view_pdf():
    """
    Serve the generated PDF file.
    """
    pdf_file_path = request.args['filename']
    if os.path.exists(pdf_file_path):
        return send_file(pdf_file_path, as_attachment=False, mimetype='application/pdf')
    else:
        return jsonify({"error": "PDF file not found. Please generate it first!"}), 404


def add_header(canvas, doc, invoice_number):
    """Add custom header with title and invoice number."""
    # Draw the rectangle for the invoice number
    rect_width = 2 * inch
    rect_height = 0.5 * inch
    rect_x = doc.width + doc.leftMargin - rect_width
    rect_y = doc.height + doc.topMargin - rect_height

    # Draw black rectangle
    canvas.setFillColor(colors.black)
    canvas.rect(rect_x, rect_y, rect_width, rect_height, fill=1)

    # Add white text for the invoice number
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 12)
    text_x = rect_x + 0.1 * inch
    text_y = rect_y + 0.2 * inch
    canvas.drawString(text_x, text_y, f"Invoice: {invoice_number}")

    # Add the title "GULAB BEEJ BHANDAR"
    canvas.setFillColor(colors.black)
    canvas.setFont("Helvetica-Bold", 22)
    title_x = doc.leftMargin
    title_y = rect_y + rect_height / 2 - 10
    canvas.drawString(title_x, title_y, "GULAB BEEJ BHANDAR")

def generate_invoice(issuer_details, buyer_details, items, filename, invoice_number):
    """Generates a PDF invoice."""
    height, width = A4

    doc = SimpleDocTemplate(
        filename,
        pagesize=(height, width),
        topMargin=0.1 * inch,
        bottomMargin=0.1 * inch,
        rightMargin=1 * inch,
        leftMargin=1 * inch,
    )

    styles = getSampleStyleSheet()
    background_style = ParagraphStyle(
        name="transparent_background",
        textColor=colors.black,
        fontSize=12,
        fontName="Helvetica-Bold",
        alignment=1,
    )

    # Generate the table and content as before
    table_style = TableStyle(
        [
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("LINEBELOW", (0, -1), (-1, -1), 2, colors.black),
            ("VALIGN", (0, 1), (-1, -1), "TOP"),
        ]
    )
    issuer_data = [['Issuer', 'Issued To']]
    name_style = ParagraphStyle(
        name="wrapped_name",
        fontName="Helvetica",
        fontSize=10,
        leading=12,
    )
    wrapped_name = Paragraph('<br/>'.join(issuer_details), name_style)
    wrap_issuer_name = Paragraph('<br/>'.join(buyer_details) + f"<br/>Date {datetime.date.today().strftime('%d-%m-%Y')}", name_style)
    issuer_data.append([wrapped_name, wrap_issuer_name])
    issuer_table = Table(issuer_data, colWidths=[(width/3)-0.5*inch, (width/3)-0.5*inch], style=table_style)

    item_table_data = [["S.No.", "Product Name", "HSN Code", "Tax Slab", "Quantity", "Price", "Total"]]
    for item in items:
        wrapped_name = Paragraph(item["name"], name_style)
        wrapped_quantity = Paragraph(str(item["quantity"]), name_style)
        wrapped_price = Paragraph(str(item["price"]), name_style)
        wrapped_total = Paragraph(str(item["total"]), name_style)

        item_table_data.append(
            [
                item["sno"],
                wrapped_name,
                item["hsn_code"],
                item["tax_slab"],
                wrapped_quantity,
                wrapped_price,
                wrapped_total,
            ]
        )
    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ("LINEBELOW", (0, -1), (-1, -1), 2, colors.black),
            ("VALIGN", (0, 1), (-1, -1), "TOP"),
        ]
    )
    item_table = Table(item_table_data, colWidths=[0.75 * inch, 2.5 * inch, 0.75 * inch, 0.75 * inch, 0.75 * inch, 0.75 * inch, 0.75 * inch], style=table_style)

    total_price = sum(item["total"] for item in items)
    total_price_style = ParagraphStyle(alignment=TA_RIGHT, name="wrapped_name")
    total_price_paragraph = Paragraph(f"<b>Total:</b> {total_price}", total_price_style)

    elements = [
        Spacer(1, 0.6 * inch),
        issuer_table,
        Spacer(1, 0.45 * inch),
        item_table,
        Spacer(1, 0.25 * inch),
        total_price_paragraph,
    ]

    # Build the PDF with the custom header
    doc.build(elements, onFirstPage=lambda canvas, doc: add_header(canvas, doc, invoice_number))


if __name__ == '__main__':
    app.run()
