from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class TenantUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            from django.contrib.auth.models import Group

            g = Group.objects.filter(name="editor_fazenda").first()
            if g is not None:
                user.groups.add(g)
        return user
