# core/models.py
from django.db import models
from django.templatetags.static import static
from django.utils.html import escape
import base64
from .utils import bytes_to_data_uri

class ThemeMaster(models.Model):
    theme_id = models.AutoField(primary_key=True, db_column='ThemeID')
    theme_name = models.CharField(max_length=100, db_column='ThemeName')
    theme_key = models.CharField(max_length=50, db_column='ThemeKey')
    primary_color = models.CharField(max_length=20, db_column='PrimaryColor')
    primary_hover = models.CharField(max_length=20, db_column='PrimaryHover')
    is_active = models.BooleanField(default=True, db_column='IsActive')
    display_order = models.IntegerField(db_column='DisplayOrder', default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    class Meta:
        db_table = 'ThemeMaster'
        managed = False

    def __str__(self):
        return self.theme_name


class ProfileMaster(models.Model):
    PROFILE_CHOICES = [
        (1, 'Super Admin'),
        (2, 'School Admin'),
        (3, 'Teacher'),
        (4, 'Student'),
        (5, 'Accountant'),
        (6, 'Driver'),
        (7, 'Librarian')
    ]
    profile_id = models.IntegerField(choices=PROFILE_CHOICES, primary_key=True, db_column='ProfileID')
    profile_name = models.CharField(max_length=100, db_column='ProfileName')
    description = models.CharField(max_length=255, null=True, blank=True, db_column='Description')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'ProfileMaster'
        managed = False

    def __str__(self):
        return self.profile_name


class SchoolMaster(models.Model):
    school_id = models.AutoField(primary_key=True, db_column='SchoolID')
    school_code = models.CharField(max_length=20, db_column='SchoolCode', null=True, blank=True)
    school_name = models.CharField(max_length=100, db_column='SchoolName')
    registration_number = models.CharField(max_length=50, db_column='RegistrationNumber', null=True, blank=True)
    address = models.TextField(db_column='Address', null=True, blank=True)
    district = models.CharField(max_length=100, db_column='District', null=True, blank=True)
    state = models.CharField(max_length=100, db_column='State', null=True, blank=True)
    country = models.CharField(max_length=100, db_column='Country', null=True, blank=True)
    pincode = models.CharField(max_length=10, db_column='Pincode', null=True, blank=True)
    phone = models.CharField(max_length=20, db_column='Phone', null=True, blank=True)
    email = models.CharField(max_length=100, db_column='Email', null=True, blank=True)
    website = models.CharField(max_length=100, db_column='Website', null=True, blank=True)
    logo_path = models.CharField(max_length=255, db_column='LogoPath', null=True, blank=True)
    school_logo = models.BinaryField(null=True, blank=True, db_column='SchoolLogo')  # New column
    created_by = models.ForeignKey('UserMaster', on_delete=models.SET_NULL, null=True, db_column='CreatedBy', related_name='school_created_by')
    created_at = models.DateTimeField(null=True, blank=True, db_column='CreatedAt')
    updated_by = models.ForeignKey('UserMaster', on_delete=models.SET_NULL, null=True, db_column='UpdatedBy', related_name='school_updated_by')
    updated_at = models.DateTimeField(null=True, blank=True, db_column='UpdatedAt')
    deleted_by = models.ForeignKey('UserMaster', on_delete=models.SET_NULL, null=True, db_column='DeletedBy', related_name='school_deleted_by')
    deleted_at = models.DateTimeField(null=True, blank=True, db_column='DeletedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')
    theme = models.ForeignKey(ThemeMaster, on_delete=models.SET_NULL, null=True, blank=True, db_column='ThemeID')

    class Meta:
        db_table = 'SchoolMaster'
        managed = False

    def __str__(self):
        return self.school_name

    def get_school_logo(self):
        """Return Base64 encoded school logo or fallback image."""
        if self.school_logo:
            return bytes_to_data_uri(self.school_logo)
        elif self.logo_path:
            return self.logo_path
        return '/static/images/default-school-logo.png'


class UserMaster(models.Model):
    user_id = models.AutoField(primary_key=True, db_column='UserID')
    user_code = models.CharField(max_length=20, unique=True, db_column='UserCode')
    user_name = models.CharField(max_length=100, db_column='UserName')
    password = models.CharField(max_length=255, db_column='PasswordHash')
    email = models.CharField(max_length=100, null=True, blank=True, db_column='Email')
    phone = models.CharField(max_length=20, null=True, blank=True, db_column='Phone')
    profile = models.ForeignKey(ProfileMaster, on_delete=models.PROTECT, db_column='ProfileID')
    school = models.ForeignKey(SchoolMaster, on_delete=models.SET_NULL, null=True, blank=True, db_column='SchoolID')
    user_photo = models.BinaryField(null=True, blank=True, db_column='UserPhoto')
    is_active = models.BooleanField(default=True, db_column='IsActive')
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, db_column='CreatedBy', related_name='user_created_by')
    created_at = models.DateTimeField(null=True, blank=True, db_column='CreatedAt')
    updated_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, db_column='UpdatedBy', related_name='user_updated_by')
    updated_at = models.DateTimeField(null=True, blank=True, db_column='UpdatedAt')
    deleted_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, db_column='DeletedBy', related_name='user_deleted_by')
    deleted_at = models.DateTimeField(null=True, blank=True, db_column='DeletedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')
    theme = models.ForeignKey(ThemeMaster, on_delete=models.SET_NULL, null=True, blank=True, db_column='ThemeID')
    failed_login_attempts = models.IntegerField(default=0, db_column='FailedLoginAttempts')
    last_failed_login = models.DateTimeField(null=True, blank=True, db_column='LastFailedLogin')
    blocked_until = models.DateTimeField(null=True, blank=True, db_column='BlockedUntil')

    class Meta:
        db_table = 'UserMaster'
        managed = False

    def __str__(self):
        return self.user_code

    def get_user_logo(self):
        """Return Base64 encoded user photo or fallback image."""
        if self.user_photo:
            return bytes_to_data_uri(self.user_photo)
        elif self.profile_id == 1:
            return '/static/images/ShikshaWave_Logo.png'
        elif self.school and self.school.get_school_logo():
            return self.school.get_school_logo()
        return '/static/images/default-user.png'

    def get_full_name(self):
        return self.user_name

    @property
    def username(self):
        return self.user_name
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False

class MenuMaster(models.Model):
    menu_id = models.AutoField(primary_key=True, db_column='MenuID')
    menu_name = models.CharField(max_length=100, db_column='MenuName')
    display_order = models.IntegerField(db_column='DisplayOrder')
    parent_menu_id = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, db_column='ParentMenuID')
    menu_url = models.CharField(max_length=255, db_column='MenuURL', null=True, blank=True)  # Changed from 'url' to 'menu_url'
    icon = models.CharField(max_length=50, db_column='Icon', null=True, blank=True)
    is_active = models.BooleanField(default=True, db_column='IsActive')
    created_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='CreatedBy', related_name='menu_created_by')
    created_at = models.DateTimeField(null=True, blank=True, db_column='CreatedAt')
    updated_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='UpdatedBy', related_name='menu_updated_by')
    updated_at = models.DateTimeField(null=True, blank=True, db_column='UpdatedAt')
    deleted_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='DeletedBy', related_name='menu_deleted_by')
    deleted_at = models.DateTimeField(null=True, blank=True, db_column='DeletedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'MenuMaster'
        managed = False

    def __str__(self):
        return self.menu_name

class ProfileMenuMapping(models.Model):
    id = models.AutoField(primary_key=True, db_column='MappingID')  # Changed from 'profile_menu_id' to 'id'
    profile = models.ForeignKey(ProfileMaster, on_delete=models.PROTECT, db_column='ProfileID')
    menu = models.ForeignKey(MenuMaster, on_delete=models.PROTECT, db_column='MenuID')
    can_view = models.BooleanField(default=True, db_column='CanView')
    can_add = models.BooleanField(default=False, db_column='CanAdd')
    can_edit = models.BooleanField(default=False, db_column='CanEdit')
    can_delete = models.BooleanField(default=False, db_column='CanDelete')
    created_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='CreatedBy', related_name='profilemenu_created_by')
    created_at = models.DateTimeField(null=True, blank=True, db_column='CreatedAt')
    deleted_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='DeletedBy', related_name='profilemenu_deleted_by')
    deleted_at = models.DateTimeField(null=True, blank=True, db_column='DeletedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'ProfileMenuMapping'
        managed = False
        unique_together = ('profile', 'menu')

    def __str__(self):
        return f"{self.profile} - {self.menu}"


class OTPRecord(models.Model):
    id = models.AutoField(primary_key=True)
    identifier = models.CharField(max_length=255)
    otp = models.CharField(max_length=10)
    purpose = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.CharField(max_length=45, null=True)
    device_info = models.TextField(null=True)

    class Meta:
        db_table = 'OTPRecords'
        managed = False


class FaceTemplate(models.Model):
    id = models.AutoField(primary_key=True, db_column='FaceTemplateID')
    user = models.ForeignKey(UserMaster, on_delete=models.CASCADE, db_column='UserID', related_name='face_templates')
    face_descriptor = models.TextField(db_column='FaceDescriptor')  # JSON string of face descriptor array
    template_version = models.CharField(max_length=10, default='1.0', db_column='TemplateVersion')
    is_active = models.BooleanField(default=True, db_column='IsActive')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')
    created_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='CreatedBy', related_name='face_template_created_by')
    updated_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='UpdatedBy', related_name='face_template_updated_by')

    class Meta:
        db_table = 'FaceTemplates'
        managed = False

    def __str__(self):
        return f"Face Template for {self.user.user_code}"

    def get_face_descriptor_array(self):
        """Convert stored JSON string back to Float32Array for face comparison"""
        import json
        try:
            descriptor_list = json.loads(self.face_descriptor)
            return descriptor_list
        except (json.JSONDecodeError, TypeError):
            return None

    def set_face_descriptor_array(self, descriptor_array):
        """Convert Float32Array to JSON string for storage"""
        import json
        try:
            # Convert Float32Array to regular list for JSON serialization
            descriptor_list = descriptor_array.tolist() if hasattr(descriptor_array, 'tolist') else list(descriptor_array)
            self.face_descriptor = json.dumps(descriptor_list)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid face descriptor format: {e}")


class SalaryComponentMaster(models.Model):
    component_id = models.AutoField(primary_key=True, db_column='ComponentID')
    school = models.ForeignKey(SchoolMaster, on_delete=models.CASCADE, db_column='SchoolID')
    component_name = models.CharField(max_length=100, db_column='ComponentName')
    component_type = models.CharField(max_length=20, choices=[('Earning', 'Earning'), ('Deduction', 'Deduction')], db_column='ComponentType')
    created_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='CreatedBy', related_name='salary_component_created_by')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'SalaryComponentMaster'
        managed = False

    def __str__(self):
        return f"{self.component_name} ({self.component_type})"


class EmployeeSalaryBreakup(models.Model):
    breakup_id = models.AutoField(primary_key=True, db_column='BreakupID')
    school_id = models.IntegerField(db_column='SchoolID')
    employee_id = models.IntegerField(db_column='EmployeeID')
    component = models.ForeignKey(SalaryComponentMaster, on_delete=models.CASCADE, db_column='ComponentID')
    amount = models.DecimalField(max_digits=18, decimal_places=2, db_column='Amount')
    created_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='CreatedBy', related_name='salary_breakup_created_by')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='UpdatedBy', related_name='salary_breakup_updated_by')
    updated_at = models.DateTimeField(null=True, blank=True, db_column='UpdatedAt')
    deleted_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='DeletedBy', related_name='salary_breakup_deleted_by')
    deleted_at = models.DateTimeField(null=True, blank=True, db_column='DeletedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'EmployeeSalaryBreakup'
        managed = False

    def __str__(self):
        return f"Employee {self.employee_id} - {self.component.component_name}: ₹{self.amount}"


class ClassMaster(models.Model):
    class_id = models.AutoField(primary_key=True, db_column='ClassID')
    school = models.ForeignKey(SchoolMaster, on_delete=models.CASCADE, db_column='SchoolID')
    class_name = models.CharField(max_length=50, db_column='ClassName')
    class_code = models.CharField(max_length=20, db_column='ClassCode')
    education_level = models.CharField(max_length=50, db_column='EducationLevel', null=True, blank=True)
    description = models.CharField(max_length=255, db_column='Description', null=True, blank=True)
    is_active = models.BooleanField(default=True, db_column='IsActive')
    created_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='CreatedBy', related_name='class_created_by')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='UpdatedBy', related_name='class_updated_by')
    updated_at = models.DateTimeField(null=True, blank=True, db_column='UpdatedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'ClassMaster'
        managed = False

    def __str__(self):
        return f"{self.class_name} ({self.class_code})"


class SectionMaster(models.Model):
    section_id = models.AutoField(primary_key=True, db_column='SectionID')
    class_master = models.ForeignKey(ClassMaster, on_delete=models.CASCADE, db_column='ClassID')
    section_name = models.CharField(max_length=20, db_column='SectionName')
    capacity = models.IntegerField(db_column='Capacity', null=True, blank=True)
    room_number = models.CharField(max_length=20, db_column='RoomNumber', null=True, blank=True)
    is_active = models.BooleanField(default=True, db_column='IsActive')
    created_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='CreatedBy', related_name='section_created_by')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='UpdatedBy', related_name='section_updated_by')
    updated_at = models.DateTimeField(null=True, blank=True, db_column='UpdatedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'SectionMaster'
        managed = False

    def __str__(self):
        return f"{self.class_master.class_name} - {self.section_name}"


class FeeTypeMaster(models.Model):
    fee_type_id = models.AutoField(primary_key=True, db_column='FeeTypeId')
    school = models.ForeignKey(SchoolMaster, on_delete=models.CASCADE, db_column='SchoolId')
    fee_type_name = models.CharField(max_length=100, db_column='FeeTypeName')
    default_amount = models.DecimalField(max_digits=10, decimal_places=2, db_column='DefaultAmount')
    is_active = models.BooleanField(default=True, db_column='IsActive')
    created_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='CreatedBy', related_name='feetype_created_by')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='UpdatedBy', related_name='feetype_updated_by')
    updated_at = models.DateTimeField(null=True, blank=True, db_column='UpdatedAt')
    class_master = models.ForeignKey(ClassMaster, on_delete=models.SET_NULL, null=True, blank=True, db_column='ClassId')

    class Meta:
        db_table = 'FeeType_Master'
        managed = False

    def __str__(self):
        return f"{self.fee_type_name} - {self.school.school_name}"


class BrandProfile(models.Model):
    profile_id = models.AutoField(primary_key=True, db_column='ProfileID')
    brand_name = models.CharField(max_length=100, db_column='BrandName')
    brand_logo = models.BinaryField(null=True, blank=True, db_column='BrandLogo')
    tagline = models.CharField(max_length=255, null=True, blank=True, db_column='Tagline')
    gstin = models.CharField(max_length=15, null=True, blank=True, db_column='GSTIN')
    pan = models.CharField(max_length=10, null=True, blank=True, db_column='PAN')
    address = models.TextField(null=True, blank=True, db_column='Address')
    state = models.CharField(max_length=100, null=True, blank=True, db_column='State')
    state_code = models.CharField(max_length=5, null=True, blank=True, db_column='StateCode')
    phone = models.CharField(max_length=20, null=True, blank=True, db_column='Phone')
    email = models.CharField(max_length=100, null=True, blank=True, db_column='Email')
    website = models.CharField(max_length=100, null=True, blank=True, db_column='Website')
    authorized_signature = models.BinaryField(null=True, blank=True, db_column='AuthorizedSignature')
    authorized_signatory = models.CharField(max_length=100, null=True, blank=True, db_column='AuthorizedSignatory')
    organization_stamp = models.BinaryField(null=True, blank=True, db_column='OrganizationStamp')
    is_active = models.BooleanField(default=True, db_column='IsActive')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')
    created_at = models.DateTimeField(null=True, blank=True, db_column='CreatedAt')
    updated_at = models.DateTimeField(null=True, blank=True, db_column='UpdatedAt')
    created_by = models.IntegerField(null=True, blank=True, db_column='CreatedBy')
    updated_by = models.IntegerField(null=True, blank=True, db_column='UpdatedBy')

    class Meta:
        db_table = 'BrandProfile'
        managed = False

    def __str__(self):
        return self.brand_name

    def get_brand_logo(self):
        """Return Base64 encoded brand logo or fallback image."""
        if self.brand_logo:
            return bytes_to_data_uri(self.brand_logo)
        return '/static/images/ShikshaWave_Logo.png'

    def get_authorized_signature(self):
        """Return Base64 encoded signature if exists."""
        if self.authorized_signature:
            return bytes_to_data_uri(self.authorized_signature)
        return None

    def get_organization_stamp(self):
        """Return Base64 encoded organization stamp if exists."""
        if self.organization_stamp:
            return bytes_to_data_uri(self.organization_stamp)
        return None

class HolidayMaster(models.Model):
    holiday_id = models.AutoField(primary_key=True, db_column='HolidayID')
    school = models.ForeignKey(SchoolMaster, on_delete=models.CASCADE, db_column='SchoolID')
    holiday_date = models.DateField(db_column='HolidayDate', null=True, blank=True)
    holiday_name = models.CharField(max_length=200, db_column='HolidayName')
    holiday_type = models.CharField(max_length=50, default='Public', db_column='HolidayType')
    description = models.TextField(null=True, blank=True, db_column='Description')
    is_recurring = models.BooleanField(default=False, db_column='IsRecurring')
    day_of_week = models.IntegerField(null=True, blank=True, db_column='DayOfWeek')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')
    created_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='CreatedBy', related_name='holiday_created_by')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='UpdatedBy', related_name='holiday_updated_by')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')

    class Meta:
        db_table = 'HolidayMaster'
        managed = False

    def __str__(self):
        return f"{self.holiday_name} ({self.holiday_date})"
