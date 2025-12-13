import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import qrcode
import random
from django.http import HttpResponse
import textwrap
from django.utils.encoding import force_str
from django.conf import settings

class StudentIDCardGenerator:
    """
    A class to generate a stylish, modern, and professional ID card for students.
    Features include custom fonts, icons, a dynamic layout with wave elements,
    and a QR code.
    """
    def __init__(self, student, logo_path=None):
        self.student = student
        self.logo_path = logo_path
        self.width = 600   # 2 inches at 300 DPI
        self.height = 900  # 3 inches at 300 DPI
        
        # Load color configuration
        self.colors = self._get_color_config()
        
        # Font Awesome 6 Free Solid Unicode characters
        self.ICON_MAP = {
            'id': '\uf2c2',        # address-card
            'dob': '\uf1fd',       # birthday-cake
            'blood': '\uf475',     # tint
            'phone': '\uf095',     # phone
            'email': '\uf0e0',     # envelope
            'class': '\uf19d',     # graduation-cap
            'roll': '\uf022',      # file-alt (for roll number)
            'address': '\uf3c5',   # map-marker-alt
        }

        # Load fonts
        self._load_fonts()
    
    def _get_color_config(self):
        """Get color configuration from model or settings with fallback to defaults."""
        # Default color palette
        default_colors = {
            'primary': '#0D47A1',    # Deep Blue
            'secondary': '#1976D2',  # Lighter Blue
            'accent': '#42A5F5',     # Accent Blue
            'text_dark': '#212121',  # Almost Black
            'text_light': '#FFFFFF', # White
            'text_muted': '#757575', # Grey,
        }
        
        # Try to get colors from organization model
        try:
            # Import here to avoid circular imports
            from apps.organization.models import Institution as OrganizationSettings
            
            org_settings = OrganizationSettings.objects.first()
            if org_settings:
                return org_settings.get_id_card_colors()
        except (ImportError, AttributeError):
            # Organization model not available, try settings
            pass
        
        # Try to get colors from Django settings
        if hasattr(settings, 'ID_CARD_COLORS'):
            return {**default_colors, **settings.ID_CARD_COLORS}
        
        # Fallback to default colors
        return default_colors

    def _load_fonts(self):
        """Loads all necessary fonts with fallbacks."""
        try:
            # absolute path to static/fonts/
            base_dir = os.path.dirname(os.path.abspath(__file__))
            font_dir = os.path.join(base_dir, "student_static", "fonts")
            
            # Debug: Print the paths to verify
            print(f"Font directory: {font_dir}")
            
            # Check if files exist
            font_paths = {
                'org_name': os.path.join(font_dir, "poppins", "Poppins-ExtraBold.ttf"),
                'bold': os.path.join(font_dir, "poppins", "Poppins-Bold.ttf"),
                'medium': os.path.join(font_dir, "poppins", "Poppins-Medium.ttf"),
                'regular': os.path.join(font_dir, "poppins", "Poppins-Regular.ttf"),
                'icon': os.path.join(font_dir, "Font Awesome 6 Free-Solid-900.ttf")
            }
            
            for name, path in font_paths.items():
                if not os.path.exists(path):
                    print(f"❌ Font file not found: {path}")
                else:
                    print(f"✅ Font file found: {path}")
            
            self.font_org_name = ImageFont.truetype(font_paths['org_name'], 24)
            self.font_bold = ImageFont.truetype(font_paths['bold'], 38)
            self.font_medium = ImageFont.truetype(font_paths['medium'], 20)
            self.font_regular = ImageFont.truetype(font_paths['regular'], 16)
            self.font_small = ImageFont.truetype(font_paths['regular'], 16)
            self.font_icon = ImageFont.truetype(font_paths['icon'], 20)
            self.font_icon_large = ImageFont.truetype(font_paths['icon'], 60)

        except IOError as e:
            print(f"⚠️ Font loading failed: {e}. Falling back to system fonts.")
            # Fallback to default fonts
            self._set_default_fonts()

    def _set_default_fonts(self):
        """Set default fallback fonts"""
        default_font = ImageFont.load_default()
        self.font_org_name = default_font
        self.font_bold = default_font
        self.font_medium = default_font
        self.font_regular = default_font
        self.font_small = default_font
        self.font_icon = default_font
        self.font_icon_large = default_font

    def _ensure_string(self, text):
        """Ensure text is a string, not bytes or lazy translation object"""
        if text is None:
            return ""
        if isinstance(text, bytes):
            return text.decode('utf-8')
        return force_str(text)

    def _ensure_string_path(self, path):
        """Convert bytes path to string if necessary"""
        if path is None:
            return None
        if isinstance(path, bytes):
            return path.decode('utf-8')
        return path
        
    def _create_background(self):
        """Creates a base image with a gradient and subtle noise pattern."""
        img = Image.new('RGB', (self.width, self.height), self.colors['primary'])
        draw = ImageDraw.Draw(img)

        # Gradient
        for i in range(self.height):
            ratio = i / self.height
            # Convert hex colors to RGB components
            primary_rgb = self._hex_to_rgb(self.colors['primary'])
            secondary_rgb = self._hex_to_rgb(self.colors['secondary'])
            
            r = int(primary_rgb[0] * (1 - ratio) + secondary_rgb[0] * ratio)
            g = int(primary_rgb[1] * (1 - ratio) + secondary_rgb[1] * ratio)
            b = int(primary_rgb[2] * (1 - ratio) + secondary_rgb[2] * ratio)
            draw.line([(0, i), (self.width, i)], fill=(r, g, b))

        # Subtle noise
        for _ in range(self.width * self.height // 20):
            x, y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            draw.point((x, y), fill=(255, 255, 255, 10))

        return img, draw

    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _draw_wave_header_footer(self, draw):
        """Draws stylish wave shapes for the header and footer."""
        # Header
        header_path = [(0, 0), (self.width, 0), (self.width, 200), (0, 150)]
        draw.polygon(header_path, fill=self.colors['primary'])
        draw.ellipse([150, 120, self.width + 100, 280], fill=self.colors['primary'])

        # Footer
        footer_path = [(0, self.height), (self.width, self.height), (self.width, self.height - 150), (0, self.height - 200)]
        draw.polygon(footer_path, fill=self.colors['primary'])
        draw.ellipse([-100, self.height - 280, 450, self.height - 120], fill=self.colors['primary'])

    def _draw_info_line(self, draw, y, icon_key, label, value):
        """Helper to draw a line of information with an icon."""
        icon = self.ICON_MAP.get(icon_key, '?')
        draw.text((80, y), icon, font=self.font_icon, fill=self.colors['accent'], anchor='lm')
        
        # Ensure label and value are strings
        label_str = self._ensure_string(label)
        value_str = self._ensure_string(value)
        
        # Handle long values (like address) by truncating
        if len(value_str) > 25:
             value_str = value_str[:22] + "..."
             
        draw.text((115, y), f"{label_str}:", font=self.font_regular, fill=self.colors['text_muted'], anchor='lm')
        draw.text((230, y), value_str, font=self.font_medium, fill=self.colors['text_dark'], anchor='lm')

    def generate_id_card(self):
        """Generates the final ID card image."""
        base_img, draw = self._create_background()
        self._draw_wave_header_footer(draw)

        # Main white card area
        card_x0, card_y0 = 40, 40
        card_x1, card_y1 = self.width - 40, self.height - 50
        shadow_offset = 8
        draw.rounded_rectangle(
            (card_x0 + shadow_offset, card_y0 + shadow_offset, card_x1 + shadow_offset, card_y1 + shadow_offset),
            radius=20, fill=(0, 0, 0, 50)
        )
        draw.rounded_rectangle(
            (card_x0, card_y0, card_x1, card_y1),
            radius=20, fill=self.colors['text_light']
        )

        # --------------------------
        # Logo (top-center) + Institute Name + Card Title
        # --------------------------
        if self.logo_path:
            logo_path_str = self._ensure_string_path(self.logo_path)
            if logo_path_str and os.path.exists(logo_path_str):
                try:
                    logo = Image.open(logo_path_str).convert("RGBA")
                    logo.thumbnail((120, 120), Image.LANCZOS)
                    logo_x = (self.width - logo.width) // 2
                    logo_y = 50
                    base_img.paste(logo, (logo_x, logo_y), logo)
                    text_y_offset = logo_y + logo.height + 15
                except (IOError, OSError):
                    text_y_offset = 60
            else:
                text_y_offset = 60
        else:
            text_y_offset = 60

        # Handle long institution names with text wrapping
        if hasattr(self.student, 'institution') and hasattr(self.student.institution, 'name'):
            institution_name = self._ensure_string(self.student.institution.name)
        else:
            institution_name = "EDUCATIONAL INSTITUTE"
        
        institution_name = institution_name.upper()
        
        # Wrap institution name if too long
        institution_lines = textwrap.wrap(institution_name, width=30)
        
        # Draw each line of the institution name
        line_height = 35
        for i, line in enumerate(institution_lines):
            y_pos = text_y_offset + (i * line_height) + 15
            draw.text((self.width / 2, y_pos), line, font=self.font_org_name, 
                     fill=self.colors['primary'], anchor='mm')
        
        # Adjust the card title position based on number of institution lines
        card_title_y = text_y_offset + (len(institution_lines) * line_height) + 25
        draw.text((self.width / 2, card_title_y), "STUDENT IDENTITY CARD", 
                 font=self.font_small, fill=self.colors['text_dark'], anchor='mm')

        # Adjust photo position based on institution name height
        photo_size = 180
        photo_x = self.width // 2 - photo_size // 2
        photo_y = card_title_y + 50

        # Handle student photo
        # Get the photo document
        photo_doc = self.student.documents.filter(doc_type="PHOTO").first()

        if photo_doc and hasattr(photo_doc.file, 'path'):
            try:
                # Ensure the path is a string
                photo_path = self._ensure_string_path(photo_doc.file.path)
                
                if photo_path and os.path.exists(photo_path):
                    photo_img = Image.open(photo_path).convert("RGBA")
                    photo_img = photo_img.resize((photo_size, photo_size), Image.LANCZOS)

                    mask = Image.new('L', (photo_size, photo_size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse((0, 0, photo_size, photo_size), fill=255)

                    base_img.paste(photo_img, (photo_x, photo_y), mask)
                else:
                    self._draw_placeholder_photo(draw, photo_x, photo_y, photo_size)
            except (IOError, OSError, ValueError):
                self._draw_placeholder_photo(draw, photo_x, photo_y, photo_size)
        else:
            self._draw_placeholder_photo(draw, photo_x, photo_y, photo_size)

        # Ring around photo
        draw.ellipse((photo_x - 4, photo_y - 4, photo_x + photo_size + 4, photo_y + photo_size + 4),
                     outline=self.colors['accent'], width=4)

        # Student Name
        info_y = photo_y + photo_size + 45
        full_name = self._ensure_string(self.student.full_name).upper()
        
        # Wrap student name if too long
        name_lines = textwrap.wrap(full_name, width=30)
        
        # Draw each line of the student name
        name_line_height = 40
        for i, line in enumerate(name_lines):
            y_pos = info_y + (i * name_line_height)
            draw.text((self.width / 2, y_pos), line, font=self.font_bold, 
                     fill=self.colors['text_dark'], anchor='mm')
        
        # Class/Grade + Section information
        class_y = info_y + (len(name_lines) * name_line_height) + 15

        # --- Section only (center aligned below name area) ---
        section_text = self._ensure_string(self.student.section) or ""

        if section_text:
            draw.text(
                (self.width / 2, class_y),
                section_text,
                font=self.font_medium,
                fill=self.colors['text_muted'],
                anchor='mm'
            )
        # Information Section (Shifted up slightly to fit address)
        details_y = class_y + 40 
                
        # Ensure all values are strings
        admission_number = self._ensure_string(self.student.admission_number)
        roll_number = self._ensure_string(getattr(self.student, 'roll_number', 'N/A'))
        mobile = self._ensure_string(self.student.mobile_primary) # Updated field name
        dob = self.student.date_of_birth.strftime('%d-%m-%Y') if self.student.date_of_birth else "N/A"
        blood_group = self._ensure_string(self.student.blood_group) if self.student.blood_group else None
        
        # Address logic
        address = self.student.current_address
        if not address and hasattr(self.student, 'city'):
             address = f"{self.student.city}, {self.student.state}"
        elif not address:
             address = "N/A"
        
        address = self._ensure_string(address)

        # Select guardian name dynamically
        father = self.student.guardians.filter(relation="FATHER").first()
        mother = self.student.guardians.filter(relation="MOTHER").first()
        guardian = self.student.guardians.filter(is_primary=True).first()

        if father:
            guardian_label = "Father"
            guardian_name = self._ensure_string(father.full_name) # Updated field name
        elif mother:
            guardian_label = "Mother"
            guardian_name = self._ensure_string(mother.full_name) # Updated field name
        elif guardian:
            guardian_label = "Guardian"
            guardian_name = self._ensure_string(guardian.full_name) # Updated field name
        else:
            guardian_label = "Guardian"
            guardian_name = "N/A"

        line_height = 32

        # Draw in logical order
        self._draw_info_line(draw, details_y, 'id', 'Admission No', admission_number)
        self._draw_info_line(draw, details_y + line_height, 'roll', 'Roll No', roll_number)
        self._draw_info_line(draw, details_y + line_height * 2, 'phone', 'Phone', mobile)
        self._draw_info_line(draw, details_y + line_height * 3, 'dob', 'DOB', dob)
        
        # Father/Mother/Guardian
        self._draw_info_line(draw, details_y + line_height * 4, 'id', guardian_label, guardian_name)
        
        # Blood Group (if exists)
        current_y = details_y + line_height * 5
        if blood_group:
            self._draw_info_line(draw, current_y, 'blood', 'Blood Group', blood_group)
            current_y += line_height
            
        # Address (New)
        self._draw_info_line(draw, current_y, 'address', 'Address', address)


        # QR Code - include roll number in QR data
        qr_size = 100
        qr_data = f"Admission No: {admission_number}\nRoll No: {roll_number}\nName: {full_name}\nClass: {section_text}"
        qr_img = qrcode.make(qr_data, box_size=4).resize((qr_size, qr_size))
        qr_y = self.height - 260
        base_img.paste(qr_img, (self.width - qr_size - 60, qr_y))

        # Authorized Signature - Right side
        sig_y = self.height - 80
        draw.line((self.width - 280, sig_y, self.width - 90, sig_y), fill=self.colors['text_muted'], width=2)
        draw.text((self.width - 180, sig_y + 10), "Authorized Signature", font=self.font_small, 
                fill=self.colors['text_dark'], anchor='mm')

        # Save to buffer
        img_buffer = BytesIO()
        base_img.save(img_buffer, format='PNG', dpi=(300, 300))
        img_buffer.seek(0)

        return img_buffer

    def _draw_placeholder_photo(self, draw, x, y, size):
        """Draw a placeholder photo circle based on gender"""
        draw.ellipse((x, y, x + size, y + size), fill='#E0E0E0')
        
        # Determine icon based on gender
        gender = getattr(self.student, 'gender', 'U')
        if gender == 'M':
            icon = '\uf183' # male
        elif gender == 'F':
            icon = '\uf182' # female
        else:
            icon = '\uf007' # user (neutral)
            
        draw.text((x + size/2, y + size/2), icon, font=self.font_icon_large, 
                 fill=self.colors['text_muted'], anchor='mm')

    def get_id_card_response(self):
        """Return an HTTP response with the ID card PNG."""
        img_buffer = self.generate_id_card()
        response = HttpResponse(img_buffer.getvalue(), content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="{self.student.admission_number}_id_card.png"'
        return response