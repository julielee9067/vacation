from django.contrib.auth.mixins import LoginRequiredMixin


class IsSuperuserMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        return super().handle_no_permission()
