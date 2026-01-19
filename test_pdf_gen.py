from utils import create_pdf_file

items = [
    {
        "name": "Cool 🆒 Place",
        "address": "123 Street 🗺️",
        "description": "A very nice place with emojis 😊 like this.",
        "start_time": "10:00 AM",
        "end_time": "12:00 PM"
    }
]
summary = "This is a summary with formatted text and an emoji 🚀."

try:
    pdf_bytes = create_pdf_file(items, summary)
    print("PDF generated successfully. Bytes length:", len(pdf_bytes))
    with open("test_output.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("PDF saved to test_output.pdf")
except Exception as e:
    print(f"Error generating PDF: {e}")
