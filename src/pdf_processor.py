import pymupdf
import os


def _crop_and_resize(image_path):
    from PIL import Image, ImageChops

    image = Image.open(image_path).convert("RGB")
    difference = ImageChops.difference(
        image,
        Image.new("RGB", image.size, "white"),
    ).convert("L")
    bounds = difference.point(
        lambda value: 255 if value > 50 else 0
    ).getbbox()

    if bounds is None:
        return

    left, top, right, bottom = bounds
    margin = 24
    bounds = (
        max(0, left - margin),
        max(0, top - margin),
        min(image.width, right + margin),
        min(image.height, bottom + margin),
    )
    cropped = image.crop(bounds)

    if cropped.width * cropped.height >= image.width * image.height * 0.8:
        return

    size = (
        max(1, round(cropped.width * 0.75)),
        max(1, round(cropped.height * 0.75)),
    )
    cropped.resize(size, Image.Resampling.LANCZOS).save(image_path)


def pdf_to_images(
    pdf_path,
    output_folder="input/pdf_pages",
    page_numbers=None,
):

    os.makedirs(output_folder, exist_ok=True)

    pdf = pymupdf.open(pdf_path)

    image_paths = []

    selected_pages = (
        enumerate(pdf)
        if page_numbers is None
        else ((page_number, pdf[page_number]) for page_number in page_numbers)
    )

    for page_number, page in selected_pages:

        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(1, 1)
        )

        image_path = os.path.join(
            output_folder,
            f"page_{page_number + 1}.png"
        )

        pix.save(image_path)
        _crop_and_resize(image_path)

        image_paths.append(image_path)

    pdf.close()

    return image_paths