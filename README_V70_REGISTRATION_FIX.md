# AVTOPARK PRO V70 — Registration Fix

## Fixed
- Registration no longer fails on the second company because `Organization.slug` and `Company.slug` are unique fields.
- Registration now generates unique slugs from company name.
- Duplicate-login errors are separated from slug/database uniqueness errors.
- Existing database records with blank slugs remain compatible; new registrations receive real unique slugs.
- Username remains case-insensitive at form validation.

## Flow
React registration -> POST /api/v1/auth/register/ -> Django transaction -> Organization -> Company -> Branch -> User -> memberships -> START trial.

The previous misleading message `Bu login yoki kompaniya ma'lumotlari allaqachon mavjud` is no longer used for every IntegrityError.
