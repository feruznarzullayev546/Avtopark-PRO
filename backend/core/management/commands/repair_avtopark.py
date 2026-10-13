from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from core.models import (
    UserProfile, Company, CompanyMembership, Organization, OrganizationMembership,
    Branch, BranchMembership, SubscriptionPlan, Subscription,
)

class Command(BaseCommand):
    help = "AVTOPARK PRO auth/tenant data repair: missing profiles, memberships, branches and trial subscriptions."

    def _code(self, model, prefix, name, current_id=None):
        base = (slugify(name) or prefix).upper().replace('-', '_')[:18]
        candidate = base
        i = 1
        while model.objects.filter(code=candidate).exclude(pk=current_id).exists():
            i += 1
            candidate = f"{base[:14]}_{i}"
        return candidate

    @transaction.atomic
    def handle(self, *args, **kwargs):
        User = get_user_model()
        repaired = 0
        created_profiles = 0
        created_subscriptions = 0

        # Ensure standard plans exist. This is safe to run repeatedly.
        plans = [
            ("START", "start", 299000, 2990000, 10, 5, 1),
            ("BUSINESS", "business", 499000, 4990000, 50, 20, 2),
            ("PRO", "pro", 999000, 9990000, 200, 100, 3),
            ("ENTERPRISE", "enterprise", 0, 0, 10000, 1000, 4),
        ]
        for name, code, monthly, yearly, vehicles, users, order in plans:
            SubscriptionPlan.objects.get_or_create(
                code=code,
                defaults={
                    "name": name, "price_monthly": monthly, "price_yearly": yearly,
                    "vehicle_limit": vehicles, "user_limit": users,
                    "features": [], "is_active": True, "sort_order": order,
                },
            )
        start_plan = SubscriptionPlan.objects.get(code="start", is_active=True)

        for user in User.objects.filter(is_active=True).order_by("id"):
            profile = UserProfile.objects.filter(user=user).first()
            membership = CompanyMembership.objects.filter(
                user=user, status=CompanyMembership.STATUS_ACTIVE
            ).select_related("company").order_by("-is_default", "id").first()
            company = membership.company if membership else (profile.company if profile else None)

            if company:
                if not company.organization:
                    org = Organization.objects.create(
                        name=company.name,
                        legal_name=company.legal_name or company.name,
                        tin=company.tin,
                        email=company.email,
                        phone=company.phone,
                        code=self._code(Organization, "ORG", company.name),
                    )
                    company.organization = org
                    company.save(update_fields=["organization"])
                else:
                    org = company.organization

                if not profile:
                    role = membership.role if membership else UserProfile.ROLE_DIRECTOR
                    if role not in {
                        UserProfile.ROLE_SUPER_ADMIN,
                        UserProfile.ROLE_DIRECTOR,
                        UserProfile.ROLE_MANAGER,
                        UserProfile.ROLE_DRIVER,
                    }:
                        role = UserProfile.ROLE_DIRECTOR
                    profile = UserProfile.objects.create(
                        user=user,
                        company=company,
                        role=role,
                        full_name=user.get_full_name() or user.username,
                        phone=company.phone,
                    )
                    created_profiles += 1
                elif not profile.company_id:
                    profile.company = company
                    profile.save(update_fields=["company"])

                if not membership:
                    membership = CompanyMembership.objects.create(
                        user=user, company=company,
                        role=CompanyMembership.ROLE_DIRECTOR,
                        status=CompanyMembership.STATUS_ACTIVE,
                        is_default=True,
                    )
                    repaired += 1

                branch = Branch.objects.filter(company=company).order_by("-is_headquarters", "id").first()
                if not branch:
                    branch = Branch.objects.create(
                        company=company,
                        name="Bosh filial",
                        code="HQ",
                        phone=company.phone,
                        is_headquarters=True,
                    )
                    company.default_branch = branch
                    company.save(update_fields=["default_branch"])
                    repaired += 1
                elif not company.default_branch_id:
                    company.default_branch = branch
                    company.save(update_fields=["default_branch"])

                OrganizationMembership.objects.get_or_create(
                    user=user,
                    organization=org,
                    defaults={
                        "role": OrganizationMembership.ROLE_OWNER,
                        "status": OrganizationMembership.STATUS_ACTIVE,
                        "is_default": True,
                    },
                )
                BranchMembership.objects.get_or_create(
                    user=user,
                    branch=branch,
                    defaults={
                        "role": BranchMembership.ROLE_MANAGER,
                        "status": BranchMembership.STATUS_ACTIVE,
                        "is_default": True,
                    },
                )

                sub = Subscription.objects.filter(company=company).first()
                if not sub:
                    trial_end = company.trial_ends_at or (timezone.localdate() + timezone.timedelta(days=14))
                    if not company.trial_ends_at:
                        company.trial_ends_at = trial_end
                        company.save(update_fields=["trial_ends_at"])
                    Subscription.objects.create(
                        company=company,
                        plan=start_plan,
                        status=Subscription.STATUS_TRIAL,
                        started_at=timezone.localdate(),
                        current_period_start=timezone.localdate(),
                        current_period_end=trial_end,
                    )
                    created_subscriptions += 1

        self.stdout.write(self.style.SUCCESS(
            f"AVTOPARK PRO repair tugadi. Profiles: +{created_profiles}, subscriptions: +{created_subscriptions}, boshqa tuzatishlar: {repaired}."
        ))
