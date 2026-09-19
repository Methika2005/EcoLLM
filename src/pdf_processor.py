import pymupdf
import os


def pdf_to_images(pdf_path, output_folder="input/pdf_pages"):

    os.makedirs(output_folder, exist_ok=True)

    pdf = pymupdf.open(pdf_path)

    image_paths = []

    for page_number, page in enumerate(pdf):

        print(f"Converting page {page_number + 1}...")

        # Render page at 150 DPI approximately
        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(2, 2)
        )

        image_path = os.path.join(
            output_folder,
            f"page_{page_number + 1}.png"
        )

        pix.save(image_path)

        image_paths.append(image_path)

    pdf.close()

    return image_paths