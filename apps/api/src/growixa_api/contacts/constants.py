try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        pass



class SegmentRuleField(StrEnum):
    STATUS = "status"
    EMAIL = "email"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    PHONE = "phone"
    SOURCE = "source"
    TAG = "tag"
    CREATED_AT = "created_at"
    LIFECYCLE_STAGE = "lifecycle_stage"
    JOB_TITLE = "job_title"
    COMPANY = "company"


class SegmentRuleOperator(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    BEFORE = "before"
    AFTER = "after"
    WITHIN_DAYS = "within_days"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    HAS_TAG = "has_tag"
    HAS_NOT_TAG = "has_not_tag"


TEXT_OPERATORS: set[str] = {
    SegmentRuleOperator.EQUALS,
    SegmentRuleOperator.NOT_EQUALS,
    SegmentRuleOperator.CONTAINS,
    SegmentRuleOperator.STARTS_WITH,
    SegmentRuleOperator.ENDS_WITH,
    SegmentRuleOperator.IS_EMPTY,
    SegmentRuleOperator.IS_NOT_EMPTY,
}

DATE_OPERATORS: set[str] = {
    SegmentRuleOperator.BEFORE,
    SegmentRuleOperator.AFTER,
    SegmentRuleOperator.WITHIN_DAYS,
    SegmentRuleOperator.IS_EMPTY,
    SegmentRuleOperator.IS_NOT_EMPTY,
}

NUMBER_OPERATORS: set[str] = {
    SegmentRuleOperator.EQUALS,
    SegmentRuleOperator.NOT_EQUALS,
    SegmentRuleOperator.GREATER_THAN,
    SegmentRuleOperator.LESS_THAN,
    SegmentRuleOperator.GREATER_THAN_OR_EQUAL,
    SegmentRuleOperator.LESS_THAN_OR_EQUAL,
    SegmentRuleOperator.IS_EMPTY,
    SegmentRuleOperator.IS_NOT_EMPTY,
}

TAG_OPERATORS: set[str] = {
    SegmentRuleOperator.EQUALS,
    SegmentRuleOperator.CONTAINS,
    SegmentRuleOperator.HAS_TAG,
    SegmentRuleOperator.HAS_NOT_TAG,
}

SEGMENT_RULE_FIELD_OPERATORS: dict[str, set[str]] = {
    SegmentRuleField.STATUS: {SegmentRuleOperator.EQUALS, SegmentRuleOperator.NOT_EQUALS},
    SegmentRuleField.EMAIL: TEXT_OPERATORS,
    SegmentRuleField.FIRST_NAME: TEXT_OPERATORS,
    SegmentRuleField.LAST_NAME: TEXT_OPERATORS,
    SegmentRuleField.PHONE: TEXT_OPERATORS,
    SegmentRuleField.SOURCE: {
        SegmentRuleOperator.EQUALS,
        SegmentRuleOperator.NOT_EQUALS,
        SegmentRuleOperator.IS_EMPTY,
        SegmentRuleOperator.IS_NOT_EMPTY,
    },
    SegmentRuleField.TAG: TAG_OPERATORS,
    SegmentRuleField.CREATED_AT: DATE_OPERATORS,
    SegmentRuleField.LIFECYCLE_STAGE: {
        SegmentRuleOperator.EQUALS,
        SegmentRuleOperator.NOT_EQUALS,
        SegmentRuleOperator.IS_EMPTY,
        SegmentRuleOperator.IS_NOT_EMPTY,
    },
    SegmentRuleField.JOB_TITLE: TEXT_OPERATORS,
    SegmentRuleField.COMPANY: TEXT_OPERATORS,
}

CUSTOM_FIELD_RULE_OPERATORS: set[str] = TEXT_OPERATORS | NUMBER_OPERATORS | DATE_OPERATORS
