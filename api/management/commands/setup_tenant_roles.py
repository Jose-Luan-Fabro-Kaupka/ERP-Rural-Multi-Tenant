from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Cria grupos gestor_fazenda, editor_fazenda e leitor_fazenda com permissões "
        "sobre os models do app api (executar em cada schema de tenant)."
    )

    def handle(self, *args, **options):
        gestor, _ = Group.objects.get_or_create(name="gestor_fazenda")
        editor, _ = Group.objects.get_or_create(name="editor_fazenda")
        leitor, _ = Group.objects.get_or_create(name="leitor_fazenda")

        api_perms = Permission.objects.filter(content_type__app_label="api")
        gestor.permissions.set(api_perms)

        leitor.permissions.set(api_perms.filter(codename__startswith="view_"))

        editor.permissions.set(api_perms.exclude(codename__startswith="delete_"))

        self.stdout.write(self.style.SUCCESS("Grupos de papel (RBAC) atualizados."))
