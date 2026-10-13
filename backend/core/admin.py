from django.contrib import admin
from .models import Company, UserProfile, VehicleModelCatalog, Vehicle, DriverProfile, Part, Receipt, Issue, MaintenanceSchedule, ServiceRecord, Route, Trip, Notification, AuditLog, FuelEntry, SubscriptionPlan, Subscription, Invoice, Payment
admin.site.site_header='AVTOPARK PRO • Super Admin'; admin.site.site_title='AVTOPARK PRO'; admin.site.index_title='Platforma boshqaruvi'
for model in [Company,UserProfile,VehicleModelCatalog,Vehicle,DriverProfile,Part,Receipt,Issue,MaintenanceSchedule,ServiceRecord,Route,Trip,Notification,AuditLog,FuelEntry,SubscriptionPlan,Subscription,Invoice,Payment]:
    admin.site.register(model)

from .models import CompanyMembership, CompanyInvitation
try:
    admin.site.register(CompanyMembership)
    admin.site.register(CompanyInvitation)
except admin.sites.AlreadyRegistered:
    pass
