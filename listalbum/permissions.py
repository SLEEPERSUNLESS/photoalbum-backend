from rest_framework.permissions import BasePermission


class IsOwnerOrStaff(BasePermission):
    def has_permission(self, request, view):
        # require authentication at least
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # staff can do anything
        if request.user.is_staff:
            return True
        # support objects that have an `owner` attribute or related album.owner
        owner = getattr(obj, 'owner', None)
        if owner is not None:
            return owner == request.user
        # if object is Photo, check its album owner
        album = getattr(obj, 'album', None)
        if album is not None:
            return getattr(album, 'owner', None) == request.user
        return False
