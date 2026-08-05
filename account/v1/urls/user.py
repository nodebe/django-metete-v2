from django.urls import path
from account.v1.views.user import ListCreateUsersAPIView, ListCreatableUsersRoles, RetrieveUpdateUserAPIView, \
    ActivateDeactivateUserAPIView

urlpatterns = [
    path("", ListCreateUsersAPIView.as_view(), name='users'),
    path("creatable-user-roles", ListCreatableUsersRoles.as_view(), name='creatable_user_roles'),
    path("<str:user_id>/activate-or-deactivate", ActivateDeactivateUserAPIView.as_view(),
         name='activate_or_deactivate_users'),
    path("<str:user_id>", RetrieveUpdateUserAPIView.as_view(), name='retrieve_update_users')
]
