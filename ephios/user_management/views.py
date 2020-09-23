from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin
from guardian.shortcuts import get_objects_for_group

from ephios.user_management import mail
from ephios.user_management.forms import GroupForm, QualificationGrantFormset, UserProfileForm
from ephios.user_management.models import UserProfile


class ProfileView(LoginRequiredMixin, DetailView):
    def get_object(self, queryset=None):
        return self.request.user


class UserProfileListView(PermissionRequiredMixin, ListView):
    model = UserProfile
    permission_required = "user_management.view_userprofile"


class UserProfileCreateView(PermissionRequiredMixin, TemplateView):
    template_name = "user_management/userprofile_form.html"
    permission_required = "user_management.add_userprofile"
    model = UserProfile

    def get_context_data(self, **kwargs):
        kwargs.setdefault("userprofile_form", UserProfileForm(self.request.POST or None))
        kwargs.setdefault(
            "qualification_formset", QualificationGrantFormset(self.request.POST or None)
        )
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        userprofile_form = UserProfileForm(self.request.POST)
        qualification_formset = QualificationGrantFormset(self.request.POST)
        if all((userprofile_form.is_valid(), qualification_formset.is_valid())):
            userprofile = userprofile_form.save()
            qualification_formset.instance = userprofile
            qualification_formset.save()
            messages.success(self.request, _("User added successfully."))
            if userprofile.is_active:
                mail.send_account_creation_info(userprofile)
            return redirect(reverse("user_management:userprofile_list"))
        else:
            return self.render_to_response(
                self.get_context_data(
                    userprofile_form=userprofile_form, qualification_formset=qualification_formset
                )
            )


class UserProfileUpdateView(PermissionRequiredMixin, SingleObjectMixin, TemplateView):
    model = UserProfile
    permission_required = "user_management.change_userprofile"
    template_name = "user_management/userprofile_form.html"

    def get_userprofile_form(self):
        return UserProfileForm(
            self.request.POST or None,
            initial={"groups": self.get_object().groups.all(),},
            instance=self.object,
        )

    def get_qualification_formset(self):
        return QualificationGrantFormset(self.request.POST or None, instance=self.object)

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        kwargs.setdefault("userprofile_form", self.get_userprofile_form())
        kwargs.setdefault("qualification_formset", self.get_qualification_formset())
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        userprofile_form = self.get_userprofile_form()
        qualification_formset = self.get_qualification_formset()
        if all((userprofile_form.is_valid(), qualification_formset.is_valid())):
            userprofile = userprofile_form.save()
            qualification_formset.save()
            messages.success(self.request, _("User updated successfully."))
            if userprofile.is_active:
                mail.send_account_update_info(userprofile)
            return redirect(reverse("user_management:userprofile_list"))
        else:
            return self.render_to_response(
                self.get_context_data(
                    userprofile_form=userprofile_form, qualification_formset=qualification_formset
                )
            )


class GroupListView(PermissionRequiredMixin, ListView):
    model = Group
    permission_required = "auth.view_group"
    template_name = "user_management/group_list.html"


class GroupCreateView(PermissionRequiredMixin, CreateView):
    model = Group
    permission_required = "auth.add_group"
    template_name = "user_management/group_form.html"
    form_class = GroupForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = {
            "users": UserProfile.objects.none(),
            "can_add_event": False,
            "publish_event_for_group": Group.objects.none(),
        }
        return kwargs

    def get_success_url(self):
        messages.success(self.request, _("Group created successfully."))
        return reverse("user_management:group_list")


class GroupUpdateView(PermissionRequiredMixin, UpdateView):
    model = Group
    permission_required = "auth.change_group"
    template_name = "user_management/group_form.html"
    form_class = GroupForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = {
            "users": self.object.user_set.all(),
            "can_view_past_event": self.object.permissions.filter(
                codename="view_past_event"
            ).exists(),
            "can_add_event": self.object.permissions.filter(codename="add_event").exists(),
            "publish_event_for_group": get_objects_for_group(
                self.object, "publish_event_for_group", klass=Group
            ),
        }
        return kwargs

    def get_success_url(self):
        messages.success(self.request, _("Group updated successfully."))
        return reverse("user_management:group_list")


class GroupDeleteView(PermissionRequiredMixin, DeleteView):
    model = Group
    permission_required = "auth.delete_group"
    template_name = "user_management/group_confirm_delete.html"

    def get_success_url(self):
        return reverse("user_management:group_list")
