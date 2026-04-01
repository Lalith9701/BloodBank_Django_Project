from django.db import migrations, models


def make_emails_unique(apps, schema_editor):
    """
    Existing users with blank/duplicate emails get a placeholder
    so the unique constraint can be applied cleanly.
    Format: noemail_<pk>@bloodbank.local
    """
    User = apps.get_model('accounts', 'User')
    seen = set()
    for user in User.objects.all().order_by('pk'):
        email = (user.email or '').strip().lower()
        if not email or email in seen:
            user.email = f'noemail_{user.pk}@bloodbank.local'
            user.save(update_fields=['email'])
            email = user.email
        seen.add(email)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_replace_otp_with_security_profile'),
    ]

    operations = [
        # Step 1: deduplicate existing data
        migrations.RunPython(make_emails_unique, migrations.RunPython.noop),
        # Step 2: apply unique constraint
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=254, unique=True),
        ),
    ]
