from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import secrets


class Organization(models.Model):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=190, unique=True, blank=True)
    code = models.CharField(max_length=30, unique=True, blank=True)
    legal_name = models.CharField(max_length=220, blank=True)
    tin = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=20, default='ACTIVE', choices=[('ACTIVE','Faol'),('SUSPENDED','To‘xtatilgan'),('ARCHIVED','Arxiv')])
    max_companies = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['status','name'])]
    def __str__(self): return self.name


class OrganizationMembership(models.Model):
    ROLE_OWNER='OWNER'; ROLE_ADMIN='ADMIN'; ROLE_FINANCE='FINANCE'; ROLE_AUDITOR='AUDITOR'; ROLE_VIEWER='VIEWER'
    ROLE_CHOICES=[(ROLE_OWNER,'Owner'),(ROLE_ADMIN,'Organization Admin'),(ROLE_FINANCE,'Finance'),(ROLE_AUDITOR,'Auditor'),(ROLE_VIEWER,'Viewer')]
    STATUS_ACTIVE='ACTIVE'; STATUS_SUSPENDED='SUSPENDED'; STATUS_REMOVED='REMOVED'
    STATUS_CHOICES=[(STATUS_ACTIVE,'Faol'),(STATUS_SUSPENDED,'Bloklangan'),(STATUS_REMOVED,'Chiqarilgan')]
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='organization_memberships')
    organization=models.ForeignKey('Organization',on_delete=models.CASCADE,related_name='memberships')
    role=models.CharField(max_length=20,choices=ROLE_CHOICES,default=ROLE_VIEWER)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default=STATUS_ACTIVE)
    permissions=models.JSONField(default=dict,blank=True)
    is_default=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','organization'],name='uniq_org_membership_user_org')]
        indexes=[models.Index(fields=['user','status']),models.Index(fields=['organization','status'])]


class Company(models.Model):
    organization = models.ForeignKey('Organization', on_delete=models.PROTECT, related_name='companies', null=True, blank=True)
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=190, unique=True, blank=True)
    code = models.CharField(max_length=30, unique=True, blank=True)
    industry = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, default='ACTIVE', choices=[('ACTIVE','Faol'),('SUSPENDED','To‘xtatilgan'),('ARCHIVED','Arxiv')])
    max_users = models.PositiveIntegerField(default=10)
    max_vehicles = models.PositiveIntegerField(default=50)
    legal_name = models.CharField(max_length=220, blank=True)
    tin = models.CharField('STIR', max_length=30, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to='companies/logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    trial_ends_at = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=10, default='UZS')
    website = models.URLField(blank=True)
    default_branch = models.ForeignKey('Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_companies')
    description = models.TextField(blank=True)
    timezone_name = models.CharField(max_length=64, default='Asia/Tashkent')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'Kompaniya'
        verbose_name_plural = 'Kompaniyalar'
        ordering = ['name']
    def __str__(self): return self.name



class Branch(models.Model):
    company=models.ForeignKey('Company',on_delete=models.CASCADE,related_name='branches')
    name=models.CharField(max_length=150)
    code=models.CharField(max_length=30)
    address=models.CharField(max_length=255,blank=True)
    phone=models.CharField(max_length=40,blank=True)
    manager_name=models.CharField(max_length=150,blank=True)
    is_active=models.BooleanField(default=True)
    is_headquarters=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-is_headquarters','name']
        constraints=[models.UniqueConstraint(fields=['company','code'],name='uniq_branch_company_code')]
        indexes=[models.Index(fields=['company','is_active']),models.Index(fields=['company','code'])]
    def __str__(self): return f'{self.company} · {self.name}'


class BranchMembership(models.Model):
    ROLE_MANAGER='MANAGER'; ROLE_OPERATOR='OPERATOR'; ROLE_VIEWER='VIEWER'
    ROLE_CHOICES=[(ROLE_MANAGER,'Filial rahbari'),(ROLE_OPERATOR,'Operator'),(ROLE_VIEWER,'Kuzatuvchi')]
    STATUS_ACTIVE='ACTIVE'; STATUS_SUSPENDED='SUSPENDED'; STATUS_REMOVED='REMOVED'
    STATUS_CHOICES=[(STATUS_ACTIVE,'Faol'),(STATUS_SUSPENDED,'Bloklangan'),(STATUS_REMOVED,'Chiqarilgan')]
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='branch_memberships')
    branch=models.ForeignKey('Branch',on_delete=models.CASCADE,related_name='memberships')
    role=models.CharField(max_length=20,choices=ROLE_CHOICES,default=ROLE_VIEWER)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default=STATUS_ACTIVE)
    permissions=models.JSONField(default=dict,blank=True)
    is_default=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','branch'],name='uniq_branch_membership_user_branch')]
        indexes=[models.Index(fields=['user','status']),models.Index(fields=['branch','status'])]


class CompanyMembership(models.Model):
    ROLE_DIRECTOR = 'DIRECTOR'
    ROLE_MANAGER = 'MANAGER'
    ROLE_DRIVER = 'DRIVER'
    ROLE_ACCOUNTANT = 'ACCOUNTANT'
    ROLE_WAREHOUSE = 'WAREHOUSE'
    ROLE_DISPATCHER = 'DISPATCHER'
    ROLE_VIEWER = 'VIEWER'
    ROLE_CHOICES = [
        (ROLE_DIRECTOR, 'Direktor'), (ROLE_MANAGER, 'Manager'), (ROLE_DRIVER, 'Haydovchi'),
        (ROLE_ACCOUNTANT, 'Buxgalter'), (ROLE_WAREHOUSE, 'Omborchi'),
        (ROLE_DISPATCHER, 'Dispetcher'), (ROLE_VIEWER, 'Kuzatuvchi'),
    ]
    STATUS_ACTIVE = 'ACTIVE'; STATUS_INVITED = 'INVITED'; STATUS_SUSPENDED = 'SUSPENDED'; STATUS_REMOVED = 'REMOVED'
    STATUS_CHOICES = [(STATUS_ACTIVE,'Faol'),(STATUS_INVITED,'Taklif qilingan'),(STATUS_SUSPENDED,'Bloklangan'),(STATUS_REMOVED,'Chiqarilgan')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company_memberships')
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_VIEWER)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    is_default = models.BooleanField(default=False)
    permissions = models.JSONField(default=dict, blank=True)
    custom_role = models.ForeignKey('CompanyRole', on_delete=models.SET_NULL, null=True, blank=True, related_name='memberships')
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_company_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name='Kompaniya a’zoligi'; verbose_name_plural='Kompaniya a’zoliklari'
        constraints=[models.UniqueConstraint(fields=['user','company'], name='uniq_company_membership_user_company')]
        indexes=[models.Index(fields=['user','status']), models.Index(fields=['company','status']), models.Index(fields=['company','role'])]
    def __str__(self): return f'{self.user} @ {self.company} ({self.role})'


class CompanyRole(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='custom_roles')
    key = models.SlugField(max_length=60)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    permissions = models.JSONField(default=list, blank=True)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['name']
        constraints=[models.UniqueConstraint(fields=['company','key'],name='uniq_company_role_key')]


class CompanyInvitation(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=CompanyMembership.ROLE_CHOICES, default=CompanyMembership.ROLE_VIEWER)
    token_hash = models.CharField(max_length=128, unique=True)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='company_invitations')
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-created_at']; indexes=[models.Index(fields=['company','email']),models.Index(fields=['company','expires_at'])]
    @property
    def is_usable(self):
        return not self.accepted_at and not self.revoked_at and self.expires_at > timezone.now()


class UserProfile(models.Model):
    ROLE_SUPER_ADMIN = 'SUPER_ADMIN'
    ROLE_DIRECTOR = 'DIRECTOR'
    ROLE_MANAGER = 'MANAGER'
    ROLE_DRIVER = 'DRIVER'
    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin'),
        (ROLE_DIRECTOR, 'Direktor'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_DRIVER, 'Haydovchi'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_DRIVER)
    full_name = models.CharField(max_length=180, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'Foydalanuvchi profili'
        verbose_name_plural = 'Foydalanuvchi profillari'
    def __str__(self): return self.full_name or self.user.get_username()
    @property
    def is_company_admin(self): return self.role in {self.ROLE_DIRECTOR, self.ROLE_MANAGER}
    @property
    def is_driver(self): return self.role == self.ROLE_DRIVER

class ChatConversation(models.Model):
    user_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_conversations_a')
    user_b = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_conversations_b')
    company = models.ForeignKey('Company', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user_a','user_b'],name='uniq_chat_conversation_pair')]
        indexes=[models.Index(fields=['user_a','updated_at']),models.Index(fields=['user_b','updated_at'])]
    def __str__(self): return f'Chat {self.user_a_id} ↔ {self.user_b_id}'

class ChatMessage(models.Model):
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    body = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering=['created_at']
        indexes=[models.Index(fields=['conversation','created_at']),models.Index(fields=['conversation','read_at'])]

class VehicleModelCatalog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='vehicle_models')
    name = models.CharField(max_length=100)
    tonnage = models.FloatField(default=0)
    active = models.BooleanField(default=True)
    class Meta:
        verbose_name = 'Avtomobil modeli'
        verbose_name_plural = 'Avtomobil modellari'
        constraints = [models.UniqueConstraint(fields=['company','name'], name='uniq_vehicle_model_company_name')]
        ordering = ['name']
    def __str__(self): return f'{self.name} — {self.tonnage:g} t'

class Vehicle(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='vehicles')
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='branch_vehicles')
    number = models.CharField(max_length=30)
    model = models.CharField(max_length=80)
    model_catalog = models.ForeignKey(VehicleModelCatalog, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')
    current_mileage = models.FloatField(default=0)
    avg_daily_km = models.FloatField(default=0)
    tonnage = models.FloatField(default=0)
    note = models.TextField(blank=True)
    image = models.ImageField(upload_to='vehicles/', blank=True, null=True)
    start_date = models.DateField(default=timezone.localdate)
    active = models.BooleanField(default=True)
    class Meta:
        verbose_name = 'Avtomobil'
        verbose_name_plural = 'Avtomobillar'
        constraints = [models.UniqueConstraint(fields=['company','number'], name='uniq_vehicle_company_number'), models.CheckConstraint(condition=models.Q(current_mileage__gte=0), name='vehicle_mileage_nonnegative'), models.CheckConstraint(condition=models.Q(avg_daily_km__gte=0), name='vehicle_avg_km_nonnegative'), models.CheckConstraint(condition=models.Q(tonnage__gte=0), name='vehicle_tonnage_nonnegative')]
        ordering = ['model','number']
    def projected_mileage(self):
        days = (timezone.localdate() - self.start_date).days
        return self.current_mileage + max(days, 0) * self.avg_daily_km
    def __str__(self): return f'{self.model} — {self.number}'

class DriverProfile(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='drivers')
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='branch_drivers')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='driver_profile')
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=40, blank=True)
    vehicle = models.OneToOneField(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver')
    active = models.BooleanField(default=True)
    monthly_km_target = models.FloatField(default=10000)
    note = models.TextField(blank=True)
    suspended_until = models.DateField(null=True, blank=True)
    last_assigned_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        verbose_name = 'Haydovchi'
        verbose_name_plural = 'Haydovchilar'
    @property
    def is_suspended(self):
        return bool(self.suspended_until and self.suspended_until >= timezone.localdate())
    def workload_km(self):
        return float(self.trips.filter(status__in=['PLANNED','CONFIRMED','DONE']).aggregate(v=models.Sum('km'))['v'] or 0)
    def completed_km(self):
        return float(self.trips.filter(status='DONE').aggregate(v=models.Sum('km'))['v'] or 0)
    def rating(self):
        resolved=self.trips.filter(status__in=['DONE','CANCELLED']).count()
        done=self.trips.filter(status='DONE').count()
        cancelled=self.trips.filter(status='CANCELLED').count()
        unjustified=self.trips.filter(status='CANCELLED', cancellation_review='UNJUSTIFIED').count()
        completion=(done/resolved*100) if resolved else 100
        discipline=max(0,100-(unjustified*15)-max(cancelled-unjustified,0)*3)
        return round((completion*0.65)+(discipline*0.35),1)
    def __str__(self): return self.full_name

class Part(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='parts')
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='branch_parts')
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=80, blank=True)
    model = models.CharField(max_length=80, blank=True)
    unit = models.CharField(max_length=20, default='dona')
    min_stock = models.FloatField(default=0)
    unit_price = models.FloatField(default=0)
    class Meta:
        verbose_name = 'Ehtiyot qism'
        verbose_name_plural = 'Ehtiyot qismlar'
        ordering = ['name', 'code']
        indexes = [models.Index(fields=['company','category']), models.Index(fields=['company','name'])]
        constraints = [models.UniqueConstraint(fields=['company','code'], name='uniq_part_company_code'), models.CheckConstraint(condition=models.Q(min_stock__gte=0), name='part_min_stock_nonnegative'), models.CheckConstraint(condition=models.Q(unit_price__gte=0), name='part_unit_price_nonnegative')]
    def incoming(self):
        qs=self.receipts.all()
        if self.branch_id: qs=qs.filter(branch_id=self.branch_id)
        return qs.aggregate(v=models.Sum('quantity'))['v'] or 0
    def outgoing(self):
        qs=self.issues.all()
        if self.branch_id: qs=qs.filter(branch_id=self.branch_id)
        return qs.aggregate(v=models.Sum('quantity'))['v'] or 0
    def stock(self):
        ret=self.returns.all(); adj=self.adjustments.all()
        if self.branch_id: ret=ret.filter(branch_id=self.branch_id); adj=adj.filter(branch_id=self.branch_id)
        return self.incoming() + (ret.aggregate(v=models.Sum('quantity'))['v'] or 0) + (adj.aggregate(v=models.Sum('quantity'))['v'] or 0) - self.outgoing()
    @property
    def stock_value(self): return self.stock() * self.unit_price
    def status(self): return 'KAM QOLDI' if self.stock() <= self.min_stock else 'OK'
    def __str__(self): return f'{self.code} — {self.name}'

class Receipt(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='receipts')
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='branch_receipts')
    date = models.DateField(default=timezone.localdate)
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name='receipts')
    compatible_model = models.CharField(max_length=80, blank=True)
    quantity = models.FloatField()
    unit_price = models.FloatField(default=0)
    supplier = models.CharField(max_length=150, blank=True)
    document_no = models.CharField(max_length=80, blank=True)
    note = models.TextField(blank=True)
    class Meta:
        verbose_name = 'Sklad kirimi'
        verbose_name_plural = 'Sklad kirimlari'
        ordering = ['-date', '-id']
        indexes = [models.Index(fields=['company','part','date']), models.Index(fields=['company','date'])]
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gt=0), name='receipt_quantity_positive'), models.CheckConstraint(condition=models.Q(unit_price__gte=0), name='receipt_unit_price_nonnegative')]
    @property
    def total(self): return self.quantity * self.unit_price

class Issue(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='issues')
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='branch_issues')
    date = models.DateField(default=timezone.localdate)
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name='issues')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='issues')
    driver = models.ForeignKey(DriverProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_parts')
    maintenance = models.ForeignKey('MaintenanceSchedule', on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    odometer = models.FloatField(default=0)
    quantity = models.FloatField()
    unit_price = models.FloatField(default=0)
    part_name_snapshot = models.CharField(max_length=150, blank=True)
    part_code_snapshot = models.CharField(max_length=30, blank=True)
    unit_snapshot = models.CharField(max_length=20, blank=True)
    driver_name_snapshot = models.CharField(max_length=150, blank=True)
    service_type = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    expense = models.ForeignKey('OtherExpense', on_delete=models.SET_NULL, null=True, blank=True, related_name='warehouse_issue')
    class Meta:
        verbose_name = 'Sklad chiqimi'
        verbose_name_plural = 'Sklad chiqimlari'
        ordering = ['-date', '-id']
        indexes = [models.Index(fields=['company','part','date']), models.Index(fields=['company','vehicle','date']), models.Index(fields=['company','date'])]
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gt=0), name='issue_quantity_positive'), models.CheckConstraint(condition=models.Q(unit_price__gte=0), name='issue_unit_price_nonnegative')]
    @property
    def total(self): return self.quantity * self.unit_price
    @property
    def historical_part_name(self): return self.part_name_snapshot or self.part.name
    @property
    def historical_part_code(self): return self.part_code_snapshot or self.part.code
    @property
    def historical_unit(self): return self.unit_snapshot or self.part.unit
    @property
    def historical_driver_name(self): return self.driver_name_snapshot or (self.driver.full_name if self.driver_id else '')


class WarehouseReturn(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouse_returns')
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='branch_returns')
    date = models.DateField(default=timezone.localdate)
    issue = models.ForeignKey(Issue, on_delete=models.PROTECT, related_name='returns')
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name='returns')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='warehouse_returns')
    quantity = models.FloatField()
    unit_price = models.FloatField(default=0)
    document_no = models.CharField(max_length=80, blank=True)
    reason = models.CharField(max_length=180, blank=True)
    note = models.TextField(blank=True)
    class Meta:
        verbose_name = 'Sklad qaytarishi'
        verbose_name_plural = 'Sklad qaytarishlari'
        ordering = ['-date','-id']
        indexes = [
            models.Index(fields=['company','date']),
            models.Index(fields=['company','part','date']),
            models.Index(fields=['company','vehicle','date']),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name='warehouse_return_quantity_positive'),
            models.CheckConstraint(condition=models.Q(unit_price__gte=0), name='warehouse_return_price_nonnegative'),
        ]
    @property
    def total(self): return self.quantity * self.unit_price

class WarehouseAdjustment(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouse_adjustments')
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='branch_adjustments')
    date = models.DateField(default=timezone.localdate)
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name='adjustments')
    quantity = models.FloatField()  # + surplus, - shortage
    unit_price = models.FloatField(default=0)
    reason = models.CharField(max_length=180)
    document_no = models.CharField(max_length=80, blank=True)
    note = models.TextField(blank=True)
    class Meta:
        verbose_name = 'Sklad inventarizatsiyasi'
        verbose_name_plural = 'Sklad inventarizatsiyalari'
        ordering = ['-date','-id']
        indexes = [models.Index(fields=['company','date']), models.Index(fields=['company','part','date'])]
        constraints = [
            models.CheckConstraint(condition=models.Q(unit_price__gte=0), name='warehouse_adjustment_price_nonnegative'),
        ]
    @property
    def total(self): return abs(self.quantity) * self.unit_price

class MaintenanceSchedule(models.Model):
    STATUS_GREEN = 'YASHIL'
    STATUS_YELLOW = 'SARIQ'
    STATUS_RED = 'QIZIL'
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_schedules')
    part = models.ForeignKey(Part, on_delete=models.PROTECT, null=True, blank=True, related_name='maintenance_schedules')
    name = models.CharField(max_length=120)
    interval_km = models.FloatField(default=0)
    last_mileage = models.FloatField(default=0)
    last_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    class Meta:
        verbose_name = 'Texnik xizmat rejasi'
        verbose_name_plural = 'Texnik xizmat rejalari'
        constraints = [models.UniqueConstraint(fields=['vehicle','name'], name='uniq_maintenance_vehicle_name')]
        ordering = ['vehicle_id','name']
    @property
    def avg_daily_km(self):
        return max(float(self.vehicle.avg_daily_km or 0), 0)
    @property
    def due_mileage(self):
        return float(self.last_mileage or 0) + float(self.interval_km or 0)
    @property
    def projected_mileage(self):
        if not self.last_date or not self.avg_daily_km:
            return float(self.vehicle.current_mileage or 0)
        days = max((timezone.localdate() - self.last_date).days, 0)
        return float(self.last_mileage or 0) + days * self.avg_daily_km
    @property
    def remaining_km(self):
        return self.due_mileage - self.projected_mileage
    @property
    def remaining_days(self):
        if self.avg_daily_km <= 0:
            return None
        return int(self.remaining_km // self.avg_daily_km)
    @property
    def status_code(self):
        days = self.remaining_days
        if days is None:
            return self.STATUS_GREEN if self.remaining_km > 0 else self.STATUS_RED
        if days > 5: return self.STATUS_GREEN
        if days > 2: return self.STATUS_YELLOW
        return self.STATUS_RED
    @property
    def needs_notification(self):
        return self.status_code in {self.STATUS_YELLOW, self.STATUS_RED}

class ServiceRecord(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='services')
    service_type = models.CharField(max_length=100)
    last_date = models.DateField(null=True, blank=True)
    last_mileage = models.FloatField(default=0)
    interval = models.FloatField(default=0)
    kind = models.CharField(max_length=10, default='KM')
    class Meta:
        verbose_name = 'Servis yozuvi'
        verbose_name_plural = 'Servis yozuvlari'
        unique_together = [('vehicle','service_type')]
    def status(self):
        if self.kind == 'DAY':
            if not self.last_date: return ('KIRITILMAGAN', None, None)
            due = self.last_date + timedelta(days=int(self.interval)); days = (due-timezone.localdate()).days
            return ('QIZIL' if days < 0 else 'SARIQ' if days <= 15 else 'YASHIL', None, days)
        remaining = self.last_mileage + self.interval - self.vehicle.projected_mileage()
        return ('QIZIL' if remaining < 0 else 'SARIQ' if remaining <= 1500 else 'YASHIL', remaining, None)

class Route(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='routes')
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='branch_routes')
    name = models.CharField(max_length=100)
    from_location = models.CharField(max_length=150, blank=True)
    to_location = models.CharField(max_length=150, blank=True)
    distance_km = models.FloatField(default=0)
    one_way_km = models.FloatField(default=0)
    round_trip_km = models.FloatField(default=0)
    active = models.BooleanField(default=True)
    standard_tonnage = models.FloatField(null=True, blank=True)
    class Meta:
        verbose_name = 'Yo‘nalish'
        verbose_name_plural = 'Yo‘nalishlar'
        constraints = [models.UniqueConstraint(fields=['company','branch','name'], name='uniq_route_company_branch_name')]
    def __str__(self): return self.name

class Trip(models.Model):
    STATUS_CHOICES = [('PLANNED','Rejalashtirilgan'),('CONFIRMED','Qabul qilingan'),('IN_PROGRESS','Yo‘lda'),('DONE','Bajarilgan'),('CANCELLED','Bekor qilingan')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='trips')
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='branch_trips')
    trip_no = models.PositiveIntegerField(null=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    trip_time = models.TimeField(default='08:00')
    route = models.ForeignKey(Route, on_delete=models.PROTECT, null=True, blank=True, related_name='trips')
    driver = models.ForeignKey(DriverProfile, on_delete=models.PROTECT, related_name='trips')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='trips')
    from_location = models.CharField(max_length=150, blank=True)
    to_location = models.CharField(max_length=150, blank=True)
    manual_route = models.BooleanField(default=False)
    km = models.FloatField(default=0)
    cargo_t = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    cancellation_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    CANCELLATION_REVIEW_CHOICES = [('PENDING','Ko‘rib chiqilmoqda'),('JUSTIFIED','Asosli'),('UNJUSTIFIED','Asossiz')]
    cancellation_review = models.CharField(max_length=20, choices=CANCELLATION_REVIEW_CHOICES, default='PENDING')
    cancellation_review_note = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_trip_cancellations')
    accepted_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'Reys'
        verbose_name_plural = 'Reyslar'
        ordering = ['-date','-id']
        indexes = [models.Index(fields=['company','date','status']), models.Index(fields=['company','driver','date']), models.Index(fields=['company','route','date'])]
    def __str__(self): return f'Reys {self.trip_no or self.pk} — {(self.route.name if self.route_id else f"{self.from_location} → {self.to_location}")}'

class Notification(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    title = models.CharField(max_length=180)
    message = models.TextField()
    url = models.CharField(max_length=255, blank=True)
    dedupe_key = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        verbose_name = 'Bildirishnoma'
        verbose_name_plural = 'Bildirishnomalar'
        ordering=['-created_at']
        indexes=[models.Index(fields=['recipient','read_at','created_at']),models.Index(fields=['driver','read_at','created_at']),models.Index(fields=['company','created_at'])]
    @property
    def is_read(self): return self.read_at is not None

class ApprovalPolicy(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='approval_policies')
    branch=models.ForeignKey(Branch,on_delete=models.CASCADE,null=True,blank=True,related_name='approval_policies')
    action=models.CharField(max_length=80)
    threshold=models.DecimalField(max_digits=18,decimal_places=2,default=0)
    required_role=models.CharField(max_length=30,default='DIRECTOR')
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['company','branch','action'],name='uniq_approval_policy_scope_action')]

class ApprovalRequest(models.Model):
    STATUS_CHOICES=[('PENDING','Kutilmoqda'),('APPROVED','Tasdiqlangan'),('REJECTED','Rad etilgan'),('CANCELLED','Bekor qilingan')]
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='approval_requests')
    branch=models.ForeignKey(Branch,on_delete=models.PROTECT,null=True,blank=True,related_name='approval_requests')
    requester=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='approval_requests')
    decided_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='decided_approval_requests')
    action=models.CharField(max_length=80)
    object_type=models.CharField(max_length=100)
    object_id=models.CharField(max_length=60)
    amount=models.DecimalField(max_digits=18,decimal_places=2,default=0)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default='PENDING')
    reason=models.TextField(blank=True)
    decision_note=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    decided_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        ordering=['-created_at']
        indexes=[models.Index(fields=['company','status','created_at']),models.Index(fields=['branch','status','created_at'])]


class AuditLog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=30)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=255)
    branch = models.ForeignKey('Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'Audit yozuvi'
        verbose_name_plural = 'Audit yozuvlari'
        ordering=['-created_at']
        indexes=[models.Index(fields=['company','created_at']),models.Index(fields=['company','action','created_at'])]

class GasStation(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='gas_stations')
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='gas_stations')
    name = models.CharField(max_length=180)
    address = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(fields=['company', 'name'], name='uniq_gas_station_company_name')]
        indexes = [models.Index(fields=['company', 'active'])]
    def __str__(self): return self.name


class FuelEntry(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='fuel_entries')
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='branch_fuel_entries')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_entries')
    date = models.DateField(default=timezone.localdate)
    odometer = models.FloatField(default=0)
    liters = models.FloatField()
    price_per_liter = models.FloatField(default=0)
    station = models.CharField(max_length=150, blank=True)
    fuel_type = models.CharField(max_length=50, blank=True)
    document_no = models.CharField(max_length=80, blank=True)
    receipt_image = models.FileField(upload_to='fuel_receipts/%Y/%m/', blank=True, null=True)
    quantity_unit = models.CharField(max_length=10, default='L', choices=[('L', 'Litr'), ('M3', 'Kub metr')])
    submitted_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, blank=True, null=True, related_name='fuel_submissions')
    gas_station = models.ForeignKey('GasStation', on_delete=models.SET_NULL, blank=True, null=True, related_name='fuel_entries')
    submitted_at = models.DateTimeField(null=True, blank=True)
    ocr_text = models.TextField(blank=True)
    ocr_quantity_m3 = models.FloatField(null=True, blank=True)
    ocr_status = models.CharField(max_length=20, default='PENDING', choices=[('PENDING','Tekshirilmagan'),('MATCH','Mos'),('MISMATCH','Farq bor'),('UNREADABLE','O‘qilmadi')])
    class Meta:
        verbose_name = 'Yoqilg‘i yozuvi'
        verbose_name_plural = 'Yoqilg‘i yozuvlari'
        indexes = [models.Index(fields=['company','date']), models.Index(fields=['company','vehicle','date'])]
        constraints = [models.CheckConstraint(condition=models.Q(liters__gt=0), name='fuel_liters_positive'), models.CheckConstraint(condition=models.Q(price_per_liter__gte=0), name='fuel_price_nonnegative')]
    @property
    def total(self): return self.liters * self.price_per_liter

class SubscriptionPlan(models.Model):
    BILLING_MONTHLY = 'MONTHLY'
    BILLING_YEARLY = 'YEARLY'
    BILLING_CHOICES = [(BILLING_MONTHLY, 'Oyiga'), (BILLING_YEARLY, 'Yiliga')]
    name = models.CharField(max_length=80, unique=True)
    code = models.SlugField(max_length=40, unique=True)
    price_monthly = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price_yearly = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vehicle_limit = models.PositiveIntegerField(default=10)
    user_limit = models.PositiveIntegerField(default=5)
    features = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'Tarif'
        verbose_name_plural = 'Tariflar'
        ordering = ['sort_order', 'price_monthly', 'name']
    def __str__(self): return self.name

class Subscription(models.Model):
    STATUS_TRIAL = 'TRIAL'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_PAST_DUE = 'PAST_DUE'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_EXPIRED = 'EXPIRED'
    STATUS_CHOICES = [
        (STATUS_TRIAL, 'Sinov'), (STATUS_ACTIVE, 'Faol'),
        (STATUS_PAST_DUE, 'To‘lov kutilmoqda'), (STATUS_CANCELLED, 'Bekor qilingan'),
        (STATUS_EXPIRED, 'Muddati tugagan'),
    ]
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TRIAL)
    billing_cycle = models.CharField(max_length=10, choices=SubscriptionPlan.BILLING_CHOICES, default=SubscriptionPlan.BILLING_MONTHLY)
    started_at = models.DateField(default=timezone.localdate)
    current_period_start = models.DateField(default=timezone.localdate)
    current_period_end = models.DateField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = 'Obuna'
        verbose_name_plural = 'Obunalar'
    def price(self):
        return self.plan.price_yearly if self.billing_cycle == SubscriptionPlan.BILLING_YEARLY else self.plan.price_monthly
    def __str__(self): return f'{self.company} — {self.plan}'

class Invoice(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_PAID = 'PAID'
    STATUS_VOID = 'VOID'
    STATUS_CHOICES = [(STATUS_PENDING, 'Kutilmoqda'), (STATUS_PAID, 'To‘langan'), (STATUS_VOID, 'Bekor qilingan')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    assigned_card = models.ForeignKey('PaymentCard', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    number = models.CharField(max_length=40, unique=True)
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'Hisob-faktura'
        verbose_name_plural = 'Hisob-fakturalar'
        ordering = ['-issue_date', '-id']
    def __str__(self): return self.number




class PaymentCard(models.Model):
    company_name = models.CharField(max_length=180, blank=True, default='AVTOPARK PRO')
    card_number = models.CharField(max_length=32)
    holder_name = models.CharField(max_length=180, blank=True)
    bank_name = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering=['sort_order','id']
    @property
    def masked_number(self):
        digits=''.join(ch for ch in self.card_number if ch.isdigit())
        if len(digits) <= 8: return self.card_number
        return f"{digits[:4]} **** **** {digits[-4:]}"

class Payment(models.Model):
    METHOD_CASH = 'CASH'
    METHOD_CARD = 'CARD'
    METHOD_BANK = 'BANK'
    METHOD_CLICK = 'CLICK'
    METHOD_PAYME = 'PAYME'
    METHOD_UZUM = 'UZUM'
    METHOD_OTHER = 'OTHER'
    METHOD_CHOICES = [
        (METHOD_CASH, 'Naqd'), (METHOD_CARD, 'Bank karta'), (METHOD_BANK, 'Bank o‘tkazmasi'),
        (METHOD_CLICK, 'Click'), (METHOD_PAYME, 'Payme'), (METHOD_UZUM, 'Uzum'), (METHOD_OTHER, 'Boshqa'),
    ]
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_PENDING = 'PENDING'
    STATUS_REFUNDED = 'REFUNDED'
    STATUS_CHOICES = [(STATUS_COMPLETED, 'Qabul qilindi'), (STATUS_PENDING, 'Tekshirilmoqda'), (STATUS_REFUNDED, 'Qaytarildi')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    method = models.CharField(max_length=12, choices=METHOD_CHOICES, default=METHOD_BANK)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_COMPLETED)
    transaction_id = models.CharField(max_length=120, blank=True)
    payer_name = models.CharField(max_length=180, blank=True)
    note = models.CharField(max_length=255, blank=True)
    payment_card = models.ForeignKey('PaymentCard', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    receipt = models.FileField(upload_to='billing/receipts/', null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_payments')
    review_note = models.CharField(max_length=500, blank=True)
    received_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'To‘lov'
        verbose_name_plural = 'To‘lovlar'
        ordering = ['-received_at', '-id']
        indexes = [models.Index(fields=['company','received_at']), models.Index(fields=['status','received_at'])]
    def __str__(self): return f'{self.company} — {self.amount} — {self.transaction_id or self.pk}'

class OtherExpense(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='other_expenses')
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True, related_name='branch_other_expenses')
    date = models.DateField(default=timezone.localdate)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='other_expenses')
    category = models.CharField(max_length=100, default='Boshqa')
    description = models.CharField(max_length=180)
    amount = models.FloatField(default=0)
    document_no = models.CharField(max_length=80, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'Boshqa xarajat'
        verbose_name_plural = 'Boshqa xarajatlar'
        ordering = ['-date','-id']
        indexes = [models.Index(fields=['company','date']), models.Index(fields=['company','vehicle','date'])]
        constraints = [models.CheckConstraint(condition=models.Q(amount__gte=0), name='other_expense_amount_nonnegative')]

class FeatureFlag(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE,related_name='feature_flags')
    key = models.SlugField(max_length=80)
    enabled = models.BooleanField(default=True)
    rollout_percent = models.PositiveSmallIntegerField(default=100)
    config = models.JSONField(default=dict,blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['company','key'],name='uniq_company_feature_flag')]
        indexes=[models.Index(fields=['company','enabled'])]

class UsageMetric(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE,related_name='usage_metrics')
    metric = models.SlugField(max_length=80)
    value = models.PositiveBigIntegerField(default=0)
    limit = models.PositiveBigIntegerField(default=0)
    period_start = models.DateField(default=timezone.localdate)
    period_end = models.DateField(null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['company','metric','period_start'],name='uniq_company_metric_period')]
        indexes=[models.Index(fields=['company','metric','period_end'])]
class PlatformSecurityEvent(models.Model):
    SEVERITY_INFO = 'INFO'
    SEVERITY_WARNING = 'WARNING'
    SEVERITY_CRITICAL = 'CRITICAL'

    SEVERITY_CHOICES = [
        (SEVERITY_INFO, 'Info'),
        (SEVERITY_WARNING, 'Warning'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    event_type = models.CharField(max_length=60)
    severity = models.CharField(
        max_length=20,
        default=SEVERITY_INFO,
        choices=SEVERITY_CHOICES
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='platform_security_events'
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='platform_security_events'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='platform_security_events'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['event_type', 'created_at']),
        ]

    def __str__(self):
        return f'{self.event_type} — {self.severity}'


class PlatformSession(models.Model):
    session_key_hash = models.CharField(max_length=128, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_label = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='platform_sessions'
    )

    class Meta:
        ordering = ['-last_seen_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['last_seen_at']),
        ]

    def __str__(self):
        return f'{self.user} — {self.device_label or "Unknown device"}'