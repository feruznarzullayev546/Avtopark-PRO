import re
from django.http import JsonResponse
from django.urls import resolve

class BranchContextMiddleware:
    """
    Resolve the requested branch only when the user has access to it.
    A stale/unauthorized browser branch ID must not block login, dashboard,
    or context endpoints. Branch-scoped permissions remain enforced by views
    and the permission middleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.active_branch = None

        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            raw = request.headers.get("X-Branch-ID")
            bid = None

            if raw:
                try:
                    bid = int(raw)
                except (TypeError, ValueError):
                    bid = None

            from core.models import (
                Branch,
                CompanyMembership,
                BranchMembership,
                UserProfile,
            )

            is_super = (
                user.is_superuser
                or UserProfile.objects.filter(
                    user=user, role=UserProfile.ROLE_SUPER_ADMIN
                ).exists()
            )

            branch = None
            if bid:
                branch = (
                    Branch.objects.filter(
                        pk=bid,
                        is_active=True,
                        company__is_active=True,
                        company__status="ACTIVE",
                    )
                    .select_related("company", "company__organization")
                    .first()
                )

            if branch:
                company_membership = CompanyMembership.objects.filter(
                    user=user,
                    company=branch.company,
                    status=CompanyMembership.STATUS_ACTIVE,
                ).first()

                has_branch_membership = BranchMembership.objects.filter(
                    user=user,
                    branch=branch,
                    status=BranchMembership.STATUS_ACTIVE,
                ).exists()

                # Company directors may manage/access branches within their
                # own company; other members need explicit branch membership.
                is_company_director = bool(
                    company_membership
                    and company_membership.role == CompanyMembership.ROLE_DIRECTOR
                )

                allowed = is_super or (
                    company_membership is not None
                    and (has_branch_membership or is_company_director)
                )

                if allowed:
                    request.session["active_company_id"] = branch.company_id
                    request.session["active_org_id"] = branch.company.organization_id
                    request.session["active_branch_id"] = branch.id
                    request.active_branch = branch
                    request.session.modified = True

            # Do not return 403 just because the browser sent an old or
            # unauthorized branch ID. Endpoints that require a branch must
            # validate the active branch and permissions themselves.

        return self.get_response(request)

RU_TEXT = {
    'Boshqaruv paneli':'Панель управления','Avtomobillar':'Автомобили','Mening reyslarim':'Мои рейсы','Bildirishnomalar':'Уведомления','Yoqilg‘i':'Топливо','Sklad':'Склад','Kirim':'Приход','Chiqim':'Расход','Servis':'Сервис','Almashtirishlar tarixi':'История замен','Xarajatlar':'Расходы','Xodimlar va rollar':'Сотрудники и роли','Yo‘nalishlar':'Маршруты','Kompaniya profili':'Профиль компании','Tarif va billing':'Тариф и биллинг','Super Admin':'Супер-администратор','Tariflar':'Тарифы','Billing':'Биллинг','Kompaniya boshqaruvi':'Управление компанией','Chiqish':'Выйти','Kirish':'Войти','Saqlash':'Сохранить','Yangilash':'Обновить','Bekor qilish':'Отмена','Tahrir':'Изменить','Barchasi →':'Все →','Batafsil →':'Подробнее →','＋ Ehtiyot qism qo‘shish':'＋ Добавить запчасть','Ehtiyot qism qo‘shish':'Добавить запчасть','Ehtiyot qismlar':'Запчасти','Ehtiyot qismlar kiritilmagan.':'Запчасти не добавлены.','Almashtirishlar':'Замены','Almashtirishlar yo‘q.':'Замен нет.','Almashtirish tarixi yo‘q.':'История замен отсутствует.','Servis nazorati':'Контроль сервиса','Texnik xizmat va almashtirishlar':'Техническое обслуживание и замены','Texnik xizmat':'Техническое обслуживание','Servis nazorati qo‘shish':'Добавление контроля сервиса','Avtomobil modeli':'Модель автомобиля','Yangi haydovchi':'Новый водитель','Haydovchi':'Водитель','Haydovchilar':'Водители','Jamoa':'Команда','Jamoa a’zolari':'Участники команды','Reyslar':'Рейсы','Reyslar tarixi':'История рейсов','Reys yaratish':'Создание рейса','Yangi reys':'Новый рейс','Qabul qilish':'Принять','Bajarildi':'Выполнено','Bajarilgan':'Выполнено','Rejalashtirilgan':'Запланирован','Tasdiqlangan':'Подтвержден','Bekor qilingan':'Отменен','Kompaniya':'Компания','Davlat raqami':'Гос. номер','Joriy probeg':'Текущий пробег','Hujjat turi':'Тип документа','Sana':'Дата','Vaqt':'Время','Qayerdan':'Откуда','Qayerga':'Куда','Masofa':'Расстояние','Miqdor':'Количество','Birlik':'Единица','Birlik narxi':'Цена за единицу','Narx':'Цена','Jami':'Итого','Jami summa':'Итоговая сумма','JAMI':'ИТОГО','Izoh':'Примечание','Artikul':'Артикул','Kategoriya':'Категория','Nomi':'Название','Kod':'Код','Holat':'Статус','FAOL':'АКТИВЕН','NOFAOL':'НЕАКТИВЕН','QIZIL':'КРАСНЫЙ','SARIQ':'ЖЕЛТЫЙ','YASHIL':'ЗЕЛЕНЫЙ','Oylik reja':'Месячный план','OYLIK REJA':'МЕСЯЧНЫЙ ПЛАН','BAJARILGAN':'ВЫПОЛНЕНО','QOLGAN':'ОСТАЛОСЬ','KUNLIK O‘RTACHA':'СРЕДНЕЕ В ДЕНЬ','JORIY PROBEG':'ТЕКУЩИЙ ПРОБЕГ','YUK SIG‘IMI':'ГРУЗОПОДЪЕМНОСТЬ','AVTOMOBIL':'АВТОМОБИЛЬ','HAYDOVCHI':'ВОДИТЕЛЬ','XABARLAR':'УВЕДОМЛЕНИЯ','o‘qilmagan':'непрочитано','km / kun':'км / день','kun':'дн.','dona':'шт.','tonna':'тонн','Boshqaruv':'Управление','Kompaniya profili':'Профиль компании','Asosiy ma’lumotlar':'Основные данные','Ko‘rinish':'Предпросмотр','O‘zgarishlarni saqlash':'Сохранить изменения','Kompaniya nomi':'Название компании','Direktor F.I.Sh.':'Ф.И.О. директора','Telefon':'Телефон','Email':'Email','Login':'Логин','Parol':'Пароль','Parolni tasdiqlang':'Подтвердите пароль','Rol':'Роль','Manager':'Менеджер','Direktor':'Директор','Super Admin':'Супер-администратор','Audit log':'Журнал аудита','O‘zgarishlar jurnali':'Журнал изменений','Amal':'Действие','Obyekt':'Объект','Foydalanuvchi':'Пользователь','Yangi operatsiya':'Новая операция','Operatsion xarajatlar':'Операционные расходы','Haqiqiy tushum':'Фактические поступления','Kutilayotgan tushum':'Ожидаемые поступления','Muddati o‘tgan qarz':'Просроченная задолженность','Kutilmoqda':'Ожидается','MUDDATI O‘TGAN':'ПРОСРОЧЕНО','To‘lov':'Платеж','Hisob-fakturalar':'Счета','Kompaniyalar':'Компании','Faol kompaniyalar':'Активные компании','Kutilayotgan to‘lovlar':'Ожидаемые платежи','Jami tushgan':'Получено всего','BU OY':'В ЭТОМ МЕСЯЦЕ','KOMPANIYA':'КОМПАНИЯ','OPERATSIYA':'ОПЕРАЦИИ','BOSHQARUV':'УПРАВЛЕНИЕ','ASOSIY':'ОСНОВНОЕ','PLATFORMA':'ПЛАТФОРМА','O‘zbekiston vaqti ·':'Время Узбекистана ·','jonli':'онлайн','Avtopark':'Автопарк','Avtoparkdagi transport vositasi':'Транспортное средство автопарка','Avtoparkka yangi transport qo‘shish':'Добавление транспорта в автопарк','Avtomobil profili':'Профиль автомобиля','Excel nakladnoy':'Excel накладная','Yangi servis nazorati':'Новый контроль сервиса','Ehtiyot qismlarni almashtirish nakladnoyi':'Накладная на замену запчастей','Operatsion markaz':'Операционный центр','Avtopark, reyslar va operatsion ko‘rsatkichlarni bir oynadan boshqaring.':'Управляйте автопарком, рейсами и операционными показателями из одного окна.','Reysni saqlash →':'Сохранить рейс →','Reysni yaratish →':'Создать рейс →','Yo‘nalishlarni boshqarish →':'Управление маршрутами →','Avtotransport':'Автотранспорт','Yuk sig‘imi':'Грузоподъемность','Haydovchi tanlanmagan':'Водитель не выбран','Yuk sig‘imi —':'Грузоподъемность —','Avtomobil':'Автомобиль','Avtomobil modeli':'Модель автомобиля','Avtomobillar':'Автомобили','Avtopark':'Автопарк','Faol transport':'Активный транспорт','Faol xodim':'Активные сотрудники','Bugungi reyslar':'Рейсы сегодня','Faol reyslar':'Активные рейсы','Diqqat':'Внимание','Joriy oy':'Текущий месяц','Umumiy xarajat':'Общие расходы','Bajarilgan km':'Выполнено км','1 km narxi':'Стоимость 1 км','Texnik nazorat':'Технический контроль','Tezkor ogohlantirishlar':'Быстрые предупреждения','Yangi va avvalgi xabarlar':'Новые и предыдущие сообщения','Barchasini o‘qilgan qilish':'Отметить все прочитанными','o‘qilgan':'прочитано','YANGI':'НОВОЕ','O‘QILGAN':'ПРОЧИТАНО','Yo‘nalishlar':'Маршруты','Saqlangan marshrutlar':'Сохраненные маршруты','Operatsiya uchun mavjud':'Доступны для операций','Avtomatik to‘ldirish':'Автозаполнение','Qo‘lda yo‘nalish':'Маршрут вручную','Qayerdan maydoni majburiy.':'Поле «Откуда» обязательно.','Qayerga maydoni majburiy.':'Поле «Куда» обязательно.','Masofa 0 dan katta bo‘lishi kerak.':'Расстояние должно быть больше 0.','Yo‘nalish tanlang yoki qo‘lda kiriting.':'Выберите маршрут или введите вручную.','Avval haydovchiga avtomobil biriktiring.':'Сначала назначьте автомобиль водителю.','Avtomobil biriktirildi':'Автомобиль назначен','Yangi reys':'Новый рейс','Reys yaratildi.':'Рейс создан.','Reys qabul qilindi.':'Рейс принят.','Reys yakunlandi.':'Рейс завершен.','Barcha bildirishnomalar o‘qilgan deb belgilandi.':'Все уведомления отмечены как прочитанные.','Barcha':'Все','O‘qilmagan':'Непрочитанные','Nazorat':'Контроль','Sklad':'Склад','Kam':'Мало','Kritik':'Критично','Yangi':'Новое','Oldingi':'Предыдущие','Jami reyslar':'Всего рейсов','Jami xarajat':'Общие расходы','Moliya':'Финансы','Logistika':'Логистика','Nazorat markazi':'Центр контроля','Tizim':'Система','Yo‘lda':'В пути','Yakunlangan':'Завершен','Rejalashtirilgan + yo‘lda':'Запланировано + в пути','Servis rejalari':'Планы обслуживания','Sklad qoldig‘i':'Остаток склада','Professional boshqaruv':'Профессиональное управление',
}

class RussianResponseMiddleware:
    def __init__(self, get_response): self.get_response=get_response
    def __call__(self, request):
        response=self.get_response(request)
        if request.session.get('site_language')!='ru' or 'text/html' not in response.get('Content-Type',''): return response
        try: text=response.content.decode(response.charset or 'utf-8')
        except Exception: return response
        def repl(m):
            raw=m.group(1); stripped=raw.strip(); translated=RU_TEXT.get(stripped)
            if translated is None: return m.group(0)
            return raw[:len(raw)-len(raw.lstrip())]+translated+raw[len(raw.rstrip()):]
        text=re.sub(r'>([^<>]+)<',repl,text)
        text=text.replace('<html lang="uz">','<html lang="ru">')
        response.content=text.encode(response.charset or 'utf-8')
        return response

class EnterprisePermissionMiddleware:
    """Central server-side RBAC gate for API mutations. View code remains business-focused."""
    RULES = [
        ('POST','/api/v1/vehicles/create/','fleet.manage'),('PATCH','/api/v1/vehicles/','fleet.manage'),
        ('POST','/api/v1/drivers/create/','drivers.manage'),('PATCH','/api/v1/drivers/','drivers.manage'),
        ('POST','/api/v1/trips/create/','trips.manage'),
        ('POST','/api/v1/routes/create/','routes.manage'),('PATCH','/api/v1/routes/','routes.manage'),
        ('POST','/api/v1/fuel/create/','fuel.manage'),('PATCH','/api/v1/fuel/','fuel.manage'),
        ('POST','/api/v1/warehouse/parts/create/','warehouse.manage'),('PATCH','/api/v1/warehouse/parts/','warehouse.manage'),
        ('POST','/api/v1/warehouse/receipts/create/','warehouse.manage'),('PATCH','/api/v1/warehouse/receipts/','warehouse.manage'),
        ('POST','/api/v1/warehouse/issues/create/','warehouse.manage'),('PATCH','/api/v1/warehouse/issues/','warehouse.manage'),
        ('POST','/api/v1/warehouse/returns/create/','warehouse.manage'),('POST','/api/v1/warehouse/adjustments/create/','warehouse.manage'),
        ('POST','/api/v1/maintenance/create/','maintenance.manage'),('PATCH','/api/v1/maintenance/','maintenance.manage'),
        ('POST','/api/v1/finance/other/create/','finance.manage'),
    ]
    BRANCH_REQUIRED_PREFIXES=('/api/v1/vehicles/','/api/v1/drivers/','/api/v1/trips/','/api/v1/routes/','/api/v1/fuel/','/api/v1/warehouse/','/api/v1/maintenance/','/api/v1/finance/')
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        if request.user.is_authenticated and request.path.startswith('/api/v1/'):
            # Manager is update-only: they may edit operational records but may not create/delete.
            # Director and Super Admin retain full mutation rights.
            is_create_request = request.method.upper() == 'POST' and ('/create/' in request.path or request.path.endswith('/create'))
            is_delete_request = request.method.upper() == 'DELETE' or '/delete/' in request.path
            if (is_create_request or is_delete_request) and not request.path.startswith('/api/v1/auth/'):
                from core.models import UserProfile
                is_super = request.user.is_superuser or UserProfile.objects.filter(user=request.user, role='SUPER_ADMIN').exists()
                if not is_super:
                    profile=UserProfile.objects.filter(user=request.user).only('role').first()
                    if profile and profile.role == UserProfile.ROLE_MANAGER:
                        return JsonResponse({'error':'Manager faqat ma’lumotlarni o‘zgartira oladi; qo‘shish yoki o‘chirish huquqi yo‘q','code':'MANAGER_UPDATE_ONLY'},status=403)
            required=None
            method=request.method.upper()
            for m,p,perm in self.RULES:
                if method==m and request.path.startswith(p): required=perm; break
            if required:
                from api.access import has_permission
                if not has_permission(request,required):
                    return JsonResponse({'error':f'Ruxsat yetarli emas: {required}','code':'PERMISSION_DENIED'},status=403)
                from core.models import UserProfile
                is_super = request.user.is_superuser or UserProfile.objects.filter(
                    user=request.user, role=UserProfile.ROLE_SUPER_ADMIN, is_active=True
                ).exists()
                if not getattr(request, 'active_branch', None) and not is_super:
                    return JsonResponse({'error':'Operatsiya uchun faol filial tanlang','code':'BRANCH_REQUIRED'},status=409)
        return self.get_response(request)
