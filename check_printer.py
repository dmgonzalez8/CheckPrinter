from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import inflect
import re
import os
from PIL import Image, ImageOps, ImageFilter


def process_signatures(directory):
    """
    Gets all png files in ./ and resizes and pads them to the right dimensions.
    Sorts images alphanumerically.
    """
    files = []
    for filename in os.listdir(directory):
        if filename.endswith('.png'):
            files.append('./'+filename)
    files.sort()
    
    processed_images = []
    for png in files:
        with Image.open(png) as img:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            background = Image.new('RGBA', img.size, (255, 255, 255))
            combined = Image.alpha_composite(background, img)
            combined = combined.convert('RGB')
                        
            # Calculate new size preserving aspect ratio
            aspect_ratio = combined.width / combined.height
            new_width = int(250 * aspect_ratio)
            
            # Check if width is greater than 1500px, if so adjust the height accordingly
            if new_width > 1500:
                new_width = 1500
                new_height = int(new_width / aspect_ratio)
                resized_image = combined.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                resized_image = combined.resize((new_width, 250), Image.Resampling.LANCZOS)

            # Pad the image to make it exactly 1500px wide if needed
            if new_width < 1500:
                padded_image = ImageOps.pad(resized_image, (1500, 250), color="white", centering=(0, 1))  # Padding applied to the right
            else:
                padded_image = resized_image  # No padding needed, already at or below target width

            # Optionally flip the image vertically
            flipped = ImageOps.flip(padded_image)
            
            # Append the path of the saved image to the list
            processed_images.append(flipped)

    return processed_images


def get_user_info(file_path):
    """ 
    Gets the static information that is printed on all checks.
    """
    details = {}
    with open(file_path, 'r') as file:
        for line in file:
            # Ignore lines that are comments or empty
            if line.startswith('#') or not line.strip():
                continue
            # Split the line into key and value at the first colon
            key, value = line.strip().split(':', 1)
            # Remove any leading/trailing whitespace and correct the key if necessary
            key = key.strip().replace("'", "")
            value = value.strip()
            details[key] = value
    return details


def get_checks_info(file_path):
    checks = []
    headers_processed = False
    headers = []
    
    with open(file_path, 'r') as file:
        for line in file:
            # Skip empty lines and comments
            if line.strip() == '' or line.startswith('#'):
                continue
            
            # Process headers
            if not headers_processed:
                # Use regex to split on any number of tabs
                headers = [header.strip() for header in re.split(r'\t+', line) if header.strip()]
                headers_processed = True
                continue
            
            # Split the line into values using regex to handle multiple tabs
            values = [value.strip() for value in re.split(r'\t+', line)]

            # Replace '.' with empty strings and ensure each field has an entry
            values = ['' if value == '.' else value for value in values]
                
            check_info = dict(zip(headers, values))
            checks.append(check_info)

    return checks


def main():

    # define layout info
    static_info = {
    'date': 'DATE: _______________' , 
    'pay_line': 'PAY _______________________________________________________ AND _____ / 100 DOLLARS' , 
    'pay_box': '$' , 
    'pay_to1': 'TO THE' , 
    'pay_to2': 'ORDER OF _________________________________________________' ,
    'memo': 'MEMO:____________________________________________', 
    'signature1': "|AUTHORIZED|SIGNATURE|PYTHON|CHECK|PRINTER|SCRIPT|BY|DANIEL|M|GONZALEZ|2024|AUTHORIZED|SIGNATURE|FREE|AND|OPEN|SOURCE|SOFTWARE|NOT|FOR|RESALE|AUTHORIZED|SIGNATURE|LINE|",
    'signature2': 'AUTHORIZED SIGNATURE' ,
    }
    static_coords = {
    'Name': (36,38) , 
    'Address Line1': (36,50) , 
    'Address Line2': (36,62) , 
    'Bank Name': (240,38) , 
    'Bank Address Line1': (240,50) , 
    'Bank Address Line2': (240,62) , 
    'date': (420,62) , 
    'pay_line': (36,110) , 
    'pay_box': (485,110) , 
    'pay_to1': (36,138) , 
    'pay_to2': (36,150) , 
    'memo': (36,200) , 
    'signature1': (388,200) , 
    'signature2': (430,210) ,  
    }
    font_size = {
    'Name': 14 , 
    'Address Line1': 10 , 
    'Address Line2': 10 , 
    'Bank Name': 10 , 
    'Bank Address Line1': 10 , 
    'Bank Address Line2': 10 , 
    'date': 10 , 
    'pay_line': 10 , 
    'pay_box': 14 , 
    'pay_to1': 10 , 
    'pay_to2': 10 , 
    'memo': 10 , 
    'signature1': 2 , 
    'signature2': 8 ,
    'bottom_line': 10 ,
    'Number': 10 , 
    'Date': 10 , 
    'Amount': 10 , 
    'Payee': 10 , 
    'Memo': 10 ,
    'amount_text': 10 , 
    'decimal': 10 , 
    }
    check_data_coords = {
    'Number': (540,36) , 
    'Date': (452,59) , 
    'Amount': (504,108) , 
    'Payee': (94,147) , 
    'Memo': (76,198),
    'amount_text': (62,108) , 
    'decimal': (336,108) , 
    }

    # get user input from text files
    user_info = get_user_info('./user_info.txt')
    static_info.update(user_info)
    check_data = get_checks_info('./check_info.txt')

    # update info with calculated fields    
    infl = inflect.engine()
    for check in check_data:
        try:
            text = infl.number_to_words(int(float(check['Amount'])))
            check['amount_text'] = text.replace(' and','').replace(',','').replace('-',' ')
            check['decimal'] = str(int(float(check['Amount'])*100%100))
            if check['decimal'] == '0': check['decimal'] = '00'
        except:
            check['amount_text'] = ''
            check['decimal'] = ''
        text_len = len(check['amount_text'])
        if text_len > 1:
            num_dashes = 48 - text_len
            check['amount_text'] = check['amount_text'] + ' ' + '-' * num_dashes

    # register fonts
    pdfmetrics.registerFont(TTFont('Micr', './fonts/GnuMICR.ttf'))
    pdfmetrics.registerFont(TTFont('Sans', './fonts/Roboto-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('SansBold', './fonts/Roboto-Black.ttf'))

    # produce checks
    for check in check_data:
    
        # setup 
        cv = canvas.Canvas(f"./output/{check['Number']}.pdf", pagesize=letter, bottomup=0)
        width, height = letter
        cv.line(36, 270, 576, 270)
        
        # place micr text 
        micr_text = f"C{check['Number']}C   A{static_info['Routing Number']}A {static_info['Account Number']}C"
        micr_coords = (36,230)
        cv.setFont('Micr', 12)
        cv.drawString(micr_coords[0], micr_coords[1], micr_text)
        
        # place box
        x1, y1, x2, y2 = 476, 90, 574, 120
        cv.line(x1, y1, x1, y2)
        cv.line(x2, y1, x2, y2)
        cv.line(x1, y1, x2, y1)
        cv.line(x1, y2, x2, y2)
        
        # place signature
        sig_images = process_signatures('./')
        if len(sig_images)>0:  
            cv.drawInlineImage(image=sig_images[0],
                        x=390,y=144, height=30, width=180)
        if len(sig_images)>1 and user_info['Signatures Required'] != '1':
            cv.drawInlineImage(image=sig_images[1],
                        x=390, y=104, height=30, width=180)
            
        # check if 2 signatures required
        if user_info['Signatures Required'] != '1':
            static_info['signature2'] = 'NOT VALID WITHOUT TWO SIGNATURES'
            static_info['signature3'] = static_info['signature1']
            static_info['signature4'] = 'AUTHORIZED SIGNATURES'
            font_size['signature3'] = font_size['signature1']
            font_size['signature4'] = font_size['signature2']
            static_coords['signature4'] = static_coords['signature1'][0]+42, static_coords['signature1'][1]-30 
            static_coords['signature3'] = static_coords['signature1'][0], static_coords['signature1'][1]-40 
            static_coords['signature2'] = static_coords['signature1'][0]+20, static_coords['signature1'][1]+10
        
        # place static text
        cv.setFont('Sans', 10)
        for key in static_coords:
            
            if key == 'Name':
                cv.setFont('SansBold', font_size[key])
            else:
                cv.setFont('Sans', font_size[key])

            cv.drawString(static_coords[key][0], 
                        static_coords[key][1], 
                        static_info[key])
            
        # place dynamic text
        for key in check:
            
            cv.setFont('Sans', font_size[key])
            
            cv.drawString(check_data_coords[key][0], 
                        check_data_coords[key][1], 
                        str(check[key]))
        
        cv.save()
        
if __name__ == '__main__':
    main()
