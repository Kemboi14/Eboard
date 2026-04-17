from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import Language


class Command(BaseCommand):
    help = 'Populate initial language data for the platform'

    def handle(self, *args, **options):
        languages = [
            {
                'code': 'en',
                'name': 'English',
                'native_name': 'English',
                'locale_code': 'en_US',
                'direction': 'ltr',
                'status': 'active',
                'is_default': True,
            },
            {
                'code': 'fr',
                'name': 'French',
                'native_name': 'Français',
                'locale_code': 'fr_FR',
                'direction': 'ltr',
                'status': 'active',
                'is_default': False,
            },
            {
                'code': 'sw',
                'name': 'Swahili',
                'native_name': 'Kiswahili',
                'locale_code': 'sw_KE',
                'direction': 'ltr',
                'status': 'active',
                'is_default': False,
            },
            {
                'code': 'ar',
                'name': 'Arabic',
                'native_name': 'العربية',
                'locale_code': 'ar_EG',
                'direction': 'rtl',
                'status': 'active',
                'is_default': False,
            },
            {
                'code': 'pt',
                'name': 'Portuguese',
                'native_name': 'Português',
                'locale_code': 'pt_MZ',
                'direction': 'ltr',
                'status': 'active',
                'is_default': False,
            },
            {
                'code': 'es',
                'name': 'Spanish',
                'native_name': 'Español',
                'locale_code': 'es_ES',
                'direction': 'ltr',
                'status': 'beta',
                'is_default': False,
            },
            {
                'code': 'de',
                'name': 'German',
                'native_name': 'Deutsch',
                'locale_code': 'de_DE',
                'direction': 'ltr',
                'status': 'beta',
                'is_default': False,
            },
            {
                'code': 'am',
                'name': 'Amharic',
                'native_name': 'አማርኛ',
                'locale_code': 'am_ET',
                'direction': 'ltr',
                'status': 'beta',
                'is_default': False,
            },
            {
                'code': 'ha',
                'name': 'Hausa',
                'native_name': 'Hausa',
                'locale_code': 'ha_NG',
                'direction': 'ltr',
                'status': 'beta',
                'is_default': False,
            },
            {
                'code': 'yo',
                'name': 'Yoruba',
                'native_name': 'Yorùbá',
                'locale_code': 'yo_NG',
                'direction': 'ltr',
                'status': 'beta',
                'is_default': False,
            },
            {
                'code': 'zu',
                'name': 'Zulu',
                'native_name': 'isiZulu',
                'locale_code': 'zu_ZA',
                'direction': 'ltr',
                'status': 'beta',
                'is_default': False,
            },
            {
                'code': 'xh',
                'name': 'Xhosa',
                'native_name': 'isiXhosa',
                'locale_code': 'xh_ZA',
                'direction': 'ltr',
                'status': 'beta',
                'is_default': False,
            },
        ]

        created_count = 0
        updated_count = 0

        for lang_data in languages:
            code = lang_data.pop('code')
            language, created = Language.objects.update_or_create(
                code=code,
                defaults=lang_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created language: {language.name} ({language.code})')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated language: {language.name} ({language.code})')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully populated languages: {created_count} created, {updated_count} updated'
            )
        )
