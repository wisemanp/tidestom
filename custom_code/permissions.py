from guardian.shortcuts import get_objects_for_user

def strict_targets_for_user(user, qs, perm):
    """
    Return only objects for which the user has explicit object-level permissions.
    """
    return get_objects_for_user(
        user,
        f"tom_targets.{perm}",
        qs,
        accept_global_perms=False
    )

