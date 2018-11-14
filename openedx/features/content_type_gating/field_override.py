"""
FieldOverride that forces graded components to be only accessible to
students in the Unlocked Group of the ContentTypeGating partition.
"""
from django.conf import settings

from lms.djangoapps.courseware.field_overrides import FieldOverrideProvider, disable_overrides
from openedx.features.content_type_gating.partitions import CONTENT_GATING_PARTITION_ID
from openedx.features.content_type_gating.models import ContentTypeGatingConfig


class ContentTypeGatingFieldOverride(FieldOverrideProvider):
    """
    A concrete implementation of
    :class:`~courseware.field_overrides.FieldOverrideProvider` which forces
    graded content to only be accessible to the Full Access group
    """
    def get(self, block, name, default):
        if name != 'group_access':
            return default

        graded = getattr(block, 'graded', False)
        has_score = block.has_score
        weight_not_zero = getattr(block, 'weight', 0) != 0
        problem_eligible_for_content_gating = graded and has_score and weight_not_zero
        if not problem_eligible_for_content_gating:
            return default

        # Read the group_access from the fallback field-data service
        with disable_overrides():
            original_group_access = block.group_access

        if original_group_access is None:
            original_group_access = {}
        original_group_access.setdefault(
            CONTENT_GATING_PARTITION_ID,
            [settings.CONTENT_TYPE_GATE_GROUP_IDS['full_access']]
        )

        return original_group_access

    @classmethod
    def enabled_for(cls, block):
        """This simple override provider is always enabled"""
        return ContentTypeGatingConfig.enabled_for_course(course_key=block.scope_ids.usage_id.course_key)
