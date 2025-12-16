import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageColor
import qrcode
from django.conf import settings
from django.http import HttpResponse
from django.utils.encoding import force_str

# It's good practice to handle potential missing modules gracefully
try:
    from typing import Tuple
except ImportError:
    Tuple = None


class StaffIDCardGenerator:
    """
    Generates an attractive and stylish ID card for a staff member.

    This class features a modern dark theme with geometric accents,
    refreshed icons, and a clean, professional layout.
    """
    # --- Configuration Constants for Easy Styling ---

    # Card Dimensions
    WIDTH, HEIGHT = 600, 900
    MARGIN = 10

    # New stylish color palette (can be overridden by Django settings)
    DEFAULT_COLORS = {
        'background': '#2C3E50',  # Dark Slate Blue
        'primary': '#1ABC9C',     # Teal
        'secondary': '#F39C12',   # Gold/Orange
        'text_light': '#ECF0F1',  # Light Grey/Off-white
        'text_dark': '#2C3E50',   # Used for text on light backgrounds if any
        'text_muted': '#95A5A6',  # Muted Grey
    }

    # Refreshed Font Awesome 6 Solid Icons
    ICON_MAP = {
        'employee_id': '\uf2c1',  # ID Badge
        'designation': '\uf554',  # User Tie
        'phone': '\uf879',        # Mobile Alt
        'dob': '\uf1fd',          # Birthday Cake
        'email': '\uf1fa',        # Paper Plane
    }

    def __init__(self, staff, logo_path=None, stamp_path=None):
        """
        Initializes the generator.
        """
        self.staff = staff
        self.logo_path = logo_path
        self.stamp_path = stamp_path
        self.colors = self._get_color_config()
        self._load_fonts()

    def _get_color_config(self):
        """Loads colors from Django settings, falling back to defaults."""
        if hasattr(settings, 'ID_CARD_COLORS'):
            return {**self.DEFAULT_COLORS, **settings.ID_CARD_COLORS}
        return self.DEFAULT_COLORS

    def _load_fonts(self):
        """Loads fonts, with a fallback. Unchanged logic."""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # Use teacher_static/fonts as shared resource, or move to common location
            font_dir = os.path.join(base_dir, "teacher_static", "fonts")
            self.fonts = {
                'org_name': ImageFont.truetype(os.path.join(font_dir, "poppins", "Poppins-ExtraBold.ttf"), 26),
                'title': ImageFont.truetype(os.path.join(font_dir, "poppins", "Poppins-Regular.ttf"), 16),
                'name': ImageFont.truetype(os.path.join(font_dir, "poppins", "Poppins-Bold.ttf"), 34),
                'department': ImageFont.truetype(os.path.join(font_dir, "poppins", "Poppins-Medium.ttf"), 20),
                'details_label': ImageFont.truetype(os.path.join(font_dir, "poppins", "Poppins-Regular.ttf"), 16),
                'details_value': ImageFont.truetype(os.path.join(font_dir, "poppins", "Poppins-Medium.ttf"), 18),
                'footer': ImageFont.truetype(os.path.join(font_dir, "poppins", "Poppins-Regular.ttf"), 16),
                'icon': ImageFont.truetype(os.path.join(font_dir, "Font Awesome 6 Free-Solid-900.ttf"), 20),
            }
        except (IOError, KeyError):
            default_font = ImageFont.load_default()
            font_keys = ['org_name', 'title', 'name', 'department', 'details_label', 'details_value', 'footer', 'icon']
            self.fonts = {key: default_font for key in font_keys}

    def _create_canvas(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        """Creates the base image with a dark background and geometric shapes."""
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.colors['background'])
        draw = ImageDraw.Draw(img)

        # Draw stylish geometric shapes for header and footer
        # Header shape
        draw.polygon([(0, 0), (self.WIDTH, 0), (self.WIDTH, 220), (0, 150)], fill=self.colors['primary'])
        # Footer shape
        draw.polygon([(0, self.HEIGHT - 150), (self.WIDTH, self.HEIGHT - 220), (self.WIDTH, self.HEIGHT), (0, self.HEIGHT)], fill=self.colors['primary'])
        
        return img, draw

    def _draw_header(self, draw, base_img):
        """Draws the header with logo and institution name."""
        y_cursor = 40
        if self.logo_path and os.path.exists(self.logo_path):
            logo = Image.open(self.logo_path).convert("RGBA")
            logo.thumbnail((100, 100), Image.LANCZOS)
            logo_x = (self.WIDTH - logo.width) // 2
            base_img.paste(logo, (logo_x, y_cursor), logo)
            y_cursor += logo.height + 15
        else:
            y_cursor += 30 # Placeholder space

        # Retrieve institution name safely (assume on tenant or hardcoded)
        institution_name = "INSTITUTE NAME" 
        if hasattr(self.staff, 'tenant') and self.staff.tenant:
             institution_name = self.staff.tenant.name.upper()
             
        draw.text((self.WIDTH / 2, y_cursor), institution_name, font=self.fonts['org_name'], fill=self.colors['text_light'], anchor='mm')
        y_cursor += 35
        draw.text((self.WIDTH / 2, y_cursor), "STAFF IDENTITY CARD", font=self.fonts['title'], fill=self.colors['text_light'], anchor='mm')
        
        return y_cursor + 30

    def _draw_photo(self, draw, base_img, y_pos, extra_padding=30):
        """Draws the photo with a stylish circular border."""
        size = 180
        x = self.WIDTH // 2 - size // 2
        
        # Decorative borders
        draw.ellipse((x - 5, y_pos - 5, x + size + 5, y_pos + size + 5), fill=self.colors['primary'])
        draw.ellipse((x - 2, y_pos - 2, x + size + 2, y_pos + size + 2), fill=self.colors['background'])

        # Use profile_image property
        photo_file = self.staff.profile_image
        if photo_file and hasattr(photo_file, 'path') and os.path.exists(photo_file.path):
            try:
                photo_img = Image.open(photo_file.path).convert("RGBA").resize((size, size), Image.LANCZOS)
                mask = Image.new('L', (size, size), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
                base_img.paste(photo_img, (x, y_pos), mask)
            except Exception:
                # Fallback if image load fails
                self._draw_placeholder_photo(draw, x, y_pos, size)
        else:
           self._draw_placeholder_photo(draw, x, y_pos, size)
        
        return y_pos + size + extra_padding

    def _draw_placeholder_photo(self, draw, x, y, size):
        draw.ellipse((x, y, x + size, y + size), fill=self.colors['text_muted'])
        initials = self.staff.initials if hasattr(self.staff, 'initials') else "ST"
        draw.text((x + size / 2, y + size / 2), initials, font=self.fonts['name'], fill=self.colors['text_light'], anchor='mm')

    def _draw_identity(self, draw, y_start, extra_padding=40):
        """Draws the staff's name and department."""
        full_name = self.staff.full_name.upper()
        draw.text((self.WIDTH / 2, y_start), full_name, font=self.fonts['name'], fill=self.colors['text_light'], anchor='mm')
        
        y_cursor = y_start + 50
        
        department = getattr(self.staff, 'department', None)
        if department:
            draw.text((self.WIDTH / 2, y_cursor), str(department.name).upper(), font=self.fonts['department'], fill=self.colors['secondary'], anchor='mm')
        
        return y_cursor + 50

    def _draw_details(self, draw, y_start):
        """Draws the detailed information section."""
        # Use safe access or default values
        dob = self.staff.date_of_birth.strftime('%d %b, %Y') if self.staff.date_of_birth else 'N/A'
        phone = self.staff.personal_phone or self.staff.work_phone or 'N/A'
        email = self.staff.user.email
        
        details = [
            ('employee_id', 'Employee ID', self.staff.employee_id),
            ('designation', 'Designation', self.staff.designation.title if self.staff.designation else 'Staff'),
            ('phone', 'Phone', phone),
            ('dob', 'Date of Birth', dob),
            ('email', 'Email', email),
        ]
        line_height = 45 
        for i, (icon, label, value) in enumerate(details):
            self._draw_info_line(draw, y_start + i * line_height, icon, label, value)

    def _draw_info_line(self, draw, y, icon_key, label, value):
        """Helper to draw a single line of information."""
        icon = self.ICON_MAP.get(icon_key, '?')
        safe_value = force_str(value) if value else ""
        x_icon, x_label, x_value = 80, 115, 260
        draw.text((x_icon, y), icon, font=self.fonts['icon'], fill=self.colors['primary'], anchor='lm')
        draw.text((x_label, y), f"{label}:", font=self.fonts['details_label'], fill=self.colors['text_muted'], anchor='lm')
        draw.text((x_value, y), safe_value, font=self.fonts['details_value'], fill=self.colors['text_light'], anchor='lm')

    def _draw_footer(self, draw, base_img):
        """Draws the QR code, stamp, and signature line."""
        y_bottom = self.HEIGHT - 170
        qr_size = 100
        
        qr_data = f"ID: {self.staff.employee_id}\nName: {self.staff.full_name}\nRole: {self.staff.user.role}"
        
        # Styled QR Code
        qr_img = qrcode.make(
            qr_data, box_size=4, border=2
        ).convert('RGBA')
        
        # Recolor QR
        qr_data_pixels = qr_img.getdata()
        new_qr_data = []
        for item in qr_data_pixels:
            if item[0] < 200: # Dark pixels
                new_qr_data.append(tuple(int(c * 255) for c in ImageColor.getrgb(self.colors['primary'])))
            else: # White/Light pixels
                new_qr_data.append((255, 255, 255, 0)) # Transparent
        qr_img.putdata(new_qr_data)
        
        qr_img = qr_img.resize((qr_size, qr_size))
        base_img.paste(qr_img, (self.MARGIN + 20, y_bottom), qr_img)

        # Authorized Signature
        sig_x_start, sig_x_end = self.WIDTH - 250, self.WIDTH - self.MARGIN - 20
        sig_y = y_bottom + qr_size
        draw.text((sig_x_start + (sig_x_end - sig_x_start) / 2, sig_y),
                  "Authorized Signature", font=self.fonts['footer'],
                  fill=self.colors['text_light'], anchor='ms')
        draw.line((sig_x_start, sig_y - 15, sig_x_end, sig_y - 15), fill=self.colors['primary'], width=2)

        # Stamp
        stamp_y = sig_y - 110
        stamp_x = sig_x_start + 40
        if self.stamp_path and os.path.exists(self.stamp_path):
            stamp_img = Image.open(self.stamp_path).convert("RGBA")
            stamp_img.thumbnail((100, 100), Image.LANCZOS)
            base_img.paste(stamp_img, (stamp_x, stamp_y), stamp_img)
        else:
            # Placeholder stamp
            draw.ellipse((stamp_x, stamp_y, stamp_x + 80, stamp_y + 80), outline=self.colors['secondary'], width=3)
            draw.text((stamp_x + 40, stamp_y + 40), "STAMP", font=self.fonts['department'],
                      fill=self.colors['secondary'], anchor='mm')

    def generate_id_card(self):
        """Orchestrates drawing."""
        base_img, draw = self._create_canvas()

        # 1️⃣ Header
        y_cursor = self._draw_header(draw, base_img)

        # 2️⃣ Photo (with gap after header)
        y_cursor = self._draw_photo(draw, base_img, y_cursor, extra_padding=40)  # Increased gap after photo

        # 3️⃣ Name & Department (with gap after photo)
        y_cursor = self._draw_identity(draw, y_cursor, extra_padding=40)  # Increased gap after identity

        # 4️⃣ Details section (with gap after identity)
        self._draw_details(draw, y_cursor + 20)  # Added gap before details start

        # 5️⃣ Footer
        self._draw_footer(draw, base_img)

        # Save image
        img_buffer = BytesIO()
        base_img.save(img_buffer, format='PNG', dpi=(300, 300))
        img_buffer.seek(0)
        return img_buffer

    def get_id_card_response(self):
        """Generates the ID card and returns a Django HttpResponse."""
        img_buffer = self.generate_id_card()
        response = HttpResponse(img_buffer.getvalue(), content_type='image/png')
        safe_id = "".join(c for c in str(self.staff.employee_id) if c.isalnum())
        response['Content-Disposition'] = f'attachment; filename="{safe_id}_id_card.png"'
        return response