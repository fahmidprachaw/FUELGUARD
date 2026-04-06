# """
# OCR Utility Module
# ==================
# Extracts vehicle registration numbers from images using:
#   - OpenCV  : Image reading and preprocessing (grayscale, thresholding)
#   - pytesseract : OCR engine wrapper for Tesseract

# Flow:
#   read image bytes → numpy array → grayscale → threshold → OCR → clean text
# """

# import re
# import numpy as np
# import pytesseract

# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# def extract_vehicle_number(image_file):
    
#     try:
#         import cv2
        
#     except ImportError as e:
#         print(f"[OCR] Import error: {e}. Install opencv-python and pytesseract.")
#         return None

#     try:
#         image_bytes = image_file.read()
#         np_array = np.frombuffer(image_bytes, dtype=np.uint8)
#         img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

#         if img is None:
#             print("[OCR] Could not decode image. Unsupported format?")
#             return None

#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        
#         thresh = cv2.adaptiveThreshold(
#             gray,
#             255,                                  
#             cv2.ADAPTIVE_THRESH_GAUSSIAN_C,       
#             cv2.THRESH_BINARY,                    
#             11,                                   
#             2                                     
#         )

        
#         height, width = thresh.shape
#         if width < 300:
#             thresh = cv2.resize(thresh, (width * 2, height * 2),
#                                 interpolation=cv2.INTER_LINEAR)

        
#         config = '--psm 8 --oem 3'
#         raw_text = pytesseract.image_to_string(thresh, config=config)

#         print(f"[OCR] Raw OCR output: {repr(raw_text)}")

        
#         cleaned = clean_vehicle_number(raw_text)
#         print(f"[OCR] Cleaned number: {cleaned}")

#         return cleaned if cleaned else None

#     except Exception as e:
#         print(f"[OCR] Unexpected error during OCR: {e}")
#         return None


# def clean_vehicle_number(raw_text):
    
#     if not raw_text:
#         return ''

#     cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
#     return cleaned



"""
OCR Utility Module — Bangladeshi Number Plate Edition
=====================================================
Supports both:
  - English plates  : DHA-META-11-0156
  - Bangla plates   : ঢাকা মেট্রো-গ ১১-০১৫৬

Strategy:
  1. Try English OCR first (fast, reliable for EN plates)
  2. Try Bangla OCR (for Bengali script plates)
  3. Convert Bangla digits → English digits
  4. Map common Bangla city/region names → short codes
  5. Clean and return final plate number
"""

import re
import numpy as np
import pytesseract

# ── Windows: set Tesseract path ───────────────────────────────────────────────
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = 'tesseract'


# ── Bangla digit → English digit mapping ─────────────────────────────────────
BANGLA_DIGITS = {
    '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
    '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9',
}

# ── Common Bangladeshi city/region names → short code ─────────────────────────
BANGLA_CITY_MAP = {
    # Dhaka Division
    'ঢাকা':         'DHAKA',
    'ঢাকামেট্রো':   'DHAKAMET',
    'মেট্রো':       'MET',
    'নারায়ণগঞ্জ':  'NARAYANGANJ',
    'গাজীপুর':      'GAZIPUR',
    'মুন্সীগঞ্জ':   'MUNSHIGANJ',
    'মানিকগঞ্জ':    'MANIKGANJ',
    'নরসিংদী':      'NARSINGDI',
    'কিশোরগঞ্জ':    'KISHOREGANJ',
    'ফরিদপুর':      'FARIDPUR',
    'রাজবাড়ী':     'RAJBARI',
    'শরীয়তপুর':    'SHARIATPUR',
    'মাদারীপুর':    'MADARIPUR',
    'টাঙ্গাইল':     'TANGAIL',
    'গোপালগঞ্জ':    'GOPALGANJ',

    # Chittagong Division
    'চট্টগ্রাম':    'CTG',
    'কক্সবাজার':    'COXSBAZAR',
    'ব্রাহ্মণবাড়িয়া': 'BRAHMANBARIA',
    'কুমিল্লা':     'CUMILLA',
    'চাঁদপুর':      'CHANDPUR',
    'ফেনী':         'FENI',
    'নোয়াখালী':    'NOAKHALI',
    'লক্ষ্মীপুর':   'LAKSHMIPUR',

    # Sylhet Division
    'সিলেট':        'SYLHET',
    'হবিগঞ্জ':      'HABIGANJ',
    'মৌলভীবাজার':   'MOULVIBAZAR',
    'সুনামগঞ্জ':    'SUNAMGANJ',

    # Rajshahi Division
    'রাজশাহী':      'RAJSHAHI',
    'বগুড়া':       'BOGURA',
    'নাটোর':        'NATORE',
    'নওগাঁ':        'NAOGAON',
    'চাঁপাইনবাবগঞ্জ': 'CHAPAI',
    'পাবনা':        'PABNA',
    'সিরাজগঞ্জ':    'SIRAJGANJ',
    'জয়পুরহাট':    'JOYPURHAT',

    # Khulna Division
    'খুলনা':        'KHULNA',
    'বাগেরহাট':     'BAGERHAT',
    'সাতক্ষীরা':    'SATKHIRA',
    'যশোর':         'JASHORE',
    'ঝিনাইদহ':      'JHENAIDAH',
    'নড়াইল':       'NARAIL',
    'মাগুরা':       'MAGURA',
    'কুষ্টিয়া':    'KUSHTIA',
    'মেহেরপুর':     'MEHERPUR',
    'চুয়াডাঙ্গা':   'CHUADANGA',

    # Barisal Division
    'বরিশাল':       'BARISAL',
    'পটুয়াখালী':   'PATUAKHALI',
    'ভোলা':         'BHOLA',
    'পিরোজপুর':     'PIROJPUR',
    'ঝালকাঠি':      'JHALOKATI',
    'বরগুনা':       'BARGUNA',

    # Rangpur Division
    'রংপুর':        'RANGPUR',
    'দিনাজপুর':     'DINAJPUR',
    'কুড়িগ্রাম':    'KURIGRAM',
    'গাইবান্ধা':    'GAIBANDHA',
    'নীলফামারী':    'NILPHAMARI',
    'লালমনিরহাট':   'LALMONIRHAT',
    'ঠাকুরগাঁও':    'THAKURGAON',
    'পঞ্চগড়':      'PANCHAGARH',

    # Mymensingh Division
    'ময়মনসিংহ':    'MYMENSINGH',
    'জামালপুর':     'JAMALPUR',
    'শেরপুর':       'SHERPUR',
    'নেত্রকোণা':    'NETROKONA',
}

# ── Bangla letter/series → English equivalent ────────────────────────────────
BANGLA_LETTERS = {
    'ক': 'KA', 'খ': 'KHA', 'গ': 'GA', 'ঘ': 'GHA',
    'ঙ': 'NGA', 'চ': 'CHA', 'ছ': 'CHHA', 'জ': 'JA',
    'ঝ': 'JHA', 'ট': 'TA', 'ঠ': 'THA', 'ড': 'DA',
    'ঢ': 'DHA', 'ণ': 'NA', 'ত': 'TA', 'থ': 'THA',
    'দ': 'DA', 'ধ': 'DHA', 'ন': 'NA', 'প': 'PA',
    'ফ': 'PHA', 'ব': 'BA', 'ভ': 'BHA', 'ম': 'MA',
    'য': 'JA', 'র': 'RA', 'ল': 'LA', 'শ': 'SHA',
    'ষ': 'SHA', 'স': 'SA', 'হ': 'HA', 'ড়': 'RA',
    'ঢ়': 'RHA', 'য়': 'YA', 'ৎ': 'T',
}


def bangla_to_english(text):
    """
    Convert Bangla digits and city names to English equivalents.

    Example:
        'ঢাকা মেট্রো-গ ১১-০১৫৬'  →  'DHAKAMET GA 11-0156'
    """
    if not text:
        return text

    # Step 1: Replace Bangla digits with English digits
    for bangla, english in BANGLA_DIGITS.items():
        text = text.replace(bangla, english)

    # Step 2: Replace city names (longest match first to avoid partial matches)
    sorted_cities = sorted(BANGLA_CITY_MAP.keys(), key=len, reverse=True)
    for bangla_city in sorted_cities:
        if bangla_city in text:
            text = text.replace(bangla_city, BANGLA_CITY_MAP[bangla_city])

    # Step 3: Replace Bangla letters (series letters like গ, ঘ, etc.)
    for bangla_letter, english_letter in BANGLA_LETTERS.items():
        text = text.replace(bangla_letter, english_letter)

    return text


def preprocess_image(img):
    """
    Apply multiple preprocessing steps to improve OCR accuracy.
    Returns a list of processed image variants to try.
    """
    import cv2

    variants = []

    # ── Variant 1: Grayscale + adaptive threshold (default) ──────────────────
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh1 = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    variants.append(('adaptive_thresh', thresh1))

    # ── Variant 2: Grayscale + Otsu threshold ─────────────────────────────────
    _, thresh2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(('otsu_thresh', thresh2))

    # ── Variant 3: Upscaled + sharpened ───────────────────────────────────────
    h, w = gray.shape
    upscaled = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])  # Sharpen kernel
    sharpened = cv2.filter2D(upscaled, -1, kernel)
    _, thresh3 = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(('upscaled_sharp', thresh3))

    # ── Variant 4: Inverted (white text on dark plate) ────────────────────────
    inverted = cv2.bitwise_not(thresh1)
    variants.append(('inverted', inverted))

    return variants


def extract_vehicle_number(image_file):
    """
    Extract vehicle number from image.
    Tries English OCR first, then Bangla OCR.
    Converts Bangla script to readable English code.

    Returns cleaned vehicle number string or None.
    """
    try:
        import cv2
    except ImportError:
        print("[OCR] opencv-python not installed.")
        return None

    try:
        # ── Read image ────────────────────────────────────────────────────────
        image_bytes = image_file.read()
        np_array    = np.frombuffer(image_bytes, dtype=np.uint8)
        img         = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if img is None:
            print("[OCR] Could not decode image.")
            return None

        # Get all preprocessed variants
        variants = preprocess_image(img)

        best_result = None

        # ── Pass 1: Try English OCR on all variants ───────────────────────────
        for variant_name, processed_img in variants:
            for psm in ['8', '7', '6']:
                config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'
                try:
                    raw = pytesseract.image_to_string(processed_img, lang='eng', config=config)
                    cleaned = clean_vehicle_number(raw)
                    print(f"[OCR] EN/{variant_name}/psm{psm}: {repr(raw.strip())} → {cleaned}")

                    if cleaned and len(cleaned) >= 4:
                        best_result = cleaned
                        break
                except Exception as e:
                    print(f"[OCR] EN error ({variant_name}/psm{psm}): {e}")

            if best_result:
                break

        # ── Pass 2: Try Bangla OCR if English failed ──────────────────────────
        if not best_result:
            print("[OCR] English OCR failed, trying Bangla OCR...")

            # Check if Bengali language pack is installed
            try:
                available_langs = pytesseract.get_languages()
                has_bengali = 'ben' in available_langs
            except Exception:
                has_bengali = False

            if has_bengali:
                for variant_name, processed_img in variants[:2]:  # Try first 2 variants
                    for psm in ['6', '7', '8']:
                        config = f'--psm {psm} --oem 3'
                        try:
                            raw_bangla = pytesseract.image_to_string(
                                processed_img, lang='ben', config=config
                            )
                            print(f"[OCR] BN/{variant_name}/psm{psm}: {repr(raw_bangla.strip())}")

                            if raw_bangla.strip():
                                # Convert Bangla → English
                                converted = bangla_to_english(raw_bangla)
                                cleaned   = clean_vehicle_number(converted)
                                print(f"[OCR] BN converted: {cleaned}")

                                if cleaned and len(cleaned) >= 4:
                                    best_result = cleaned
                                    break
                        except Exception as e:
                            print(f"[OCR] BN error ({variant_name}/psm{psm}): {e}")

                    if best_result:
                        break
            else:
                print("[OCR] Bengali language pack not installed. Run:")
                print("      sudo apt-get install tesseract-ocr-ben")
                print("      (Windows: download ben.traineddata from GitHub)")

        print(f"[OCR] Final result: {best_result}")
        return best_result

    except Exception as e:
        print(f"[OCR] Unexpected error: {e}")
        return None


def clean_vehicle_number(raw_text):
    """
    Remove everything except A-Z and 0-9.
    Also removes common OCR noise characters.
    """
    if not raw_text:
        return ''
    cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
    return cleaned