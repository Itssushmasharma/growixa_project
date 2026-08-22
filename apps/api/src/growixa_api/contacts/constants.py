from enum import StrEnum


class SegmentRuleField(StrEnum):
    STATUS = "status"
    EMAIL = "email"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    PHONE = "phone"
    SOURCE = "source"
    TAG = "tag"
    CREATED_AT = "created_at"


class SegmentRuleOperator(StrEnum):
    EQUALS = "equals"
    CONTAINS = "contains"
    BEFORE = "before"
    AFTER = "after"


# Field -> allowed operators for segment rules.
SEGMENT_RULE_FIELD_OPERATORS: dict[str, set[str]] = {
    SegmentRuleField.STATUS: {SegmentRuleOperator.EQUALS},
    SegmentRuleField.EMAIL: {SegmentRuleOperator.EQUALS, SegmentRuleOperator.CONTAINS},
    SegmentRuleField.FIRST_NAME: {SegmentRuleOperator.EQUALS, SegmentRuleOperator.CONTAINS},
    SegmentRuleField.LAST_NAME: {SegmentRuleOperator.EQUALS, SegmentRuleOperator.CONTAINS},
    SegmentRuleField.PHONE: {SegmentRuleOperator.EQUALS, SegmentRuleOperator.CONTAINS},
    SegmentRuleField.SOURCE: {SegmentRuleOperator.EQUALS},
    SegmentRuleField.TAG: {SegmentRuleOperator.EQUALS, SegmentRuleOperator.CONTAINS},
    SegmentRuleField.CREATED_AT: {SegmentRuleOperator.BEFORE, SegmentRuleOperator.AFTER},
}

CUSTOM_FIELD_RULE_OPERATORS: set[str] = {
    SegmentRuleOperator.EQUALS,
    SegmentRuleOperator.CONTAINS,
}
