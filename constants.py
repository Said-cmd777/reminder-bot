
"""Constants for callback data and configuration values."""


CALLBACK_HW_DONE = "hw_done:"
CALLBACK_HW_UNDONE = "hw_undone:"
CALLBACK_HW_PDF = "hw_pdf:"
CALLBACK_HW_VIEW = "hw_view:"
CALLBACK_HW_EDIT_ID = "hw_edit_id:"
CALLBACK_HW_DELETE_ID = "hw_delete_id:"
CALLBACK_HW_CONFIRM_DELETE = "hw_confirm_delete:"
CALLBACK_HW_EDIT_FIELD = "hw_edit_field:"
CALLBACK_HW_CANCEL = "hw_cancel_add"
CALLBACK_HW_BACK = "hw_back"
CALLBACK_HW_LIST = "hw_list"
CALLBACK_HW_ADD = "hw_add"
CALLBACK_HW_EDIT = "hw_edit"
CALLBACK_HW_DELETE = "hw_delete"
CALLBACK_MANUAL_REMINDER = "manual_reminder"
CALLBACK_MANUAL_SEND_NOW = "manual_send_now"
CALLBACK_MANUAL_SCHEDULE = "manual_schedule"
CALLBACK_MANUAL_TARGET_ALL = "manual_target_all"
CALLBACK_MANUAL_TARGET_USER = "manual_target_user"
CALLBACK_MANUAL_TARGET_CHAT = "manual_target_chat"
CALLBACK_MANUAL_TARGET_CHAT_TOPIC = "manual_target_chat_topic"

CALLBACK_CUSTOM_REMINDER = "custom_reminder"
CALLBACK_CUSTOM_REMINDER_ADD = "custom_reminder_add"
CALLBACK_CUSTOM_REMINDER_LIST = "custom_reminder_list"
CALLBACK_CUSTOM_REMINDER_DELETE = "custom_reminder_delete:"
CALLBACK_CUSTOM_REMINDER_CONFIRM_DELETE = "custom_reminder_confirm_delete:"
CALLBACK_CUSTOM_REMINDER_DONE = "custom_reminder_done:"
CALLBACK_CUSTOM_REMINDER_UNDONE = "custom_reminder_undone:"


CALLBACK_FAQ_LIST = "faq_list"
CALLBACK_FAQ_VIEW = "faq_view:"
CALLBACK_FAQ_ADMIN = "faq_admin"
CALLBACK_FAQ_ADMIN_ADD = "faq_admin_add"
CALLBACK_FAQ_ADMIN_EDIT = "faq_admin_edit"
CALLBACK_FAQ_ADMIN_DELETE = "faq_admin_delete"
CALLBACK_FAQ_ADMIN_EDIT_SELECT = "faq_admin_edit_select:"
CALLBACK_FAQ_ADMIN_DELETE_SELECT = "faq_admin_delete_select:"
CALLBACK_FAQ_ADMIN_DELETE_CONFIRM = "faq_admin_delete_confirm:"
CALLBACK_FAQ_BACK = "faq_back"


CALLBACK_WEEKLY_SCHEDULE = "weekly_schedule"
CALLBACK_WEEKLY_SCHEDULE_GROUP_01 = "weekly_schedule_group_01"
CALLBACK_WEEKLY_SCHEDULE_GROUP_02 = "weekly_schedule_group_02"
CALLBACK_WEEKLY_SCHEDULE_GROUP_03 = "weekly_schedule_group_03"
CALLBACK_WEEKLY_SCHEDULE_GROUP_04 = "weekly_schedule_group_04"
CALLBACK_WEEKLY_SCHEDULE_TODAY = "weekly_schedule_today:"
CALLBACK_WEEKLY_SCHEDULE_TOMORROW = "weekly_schedule_tomorrow:"
CALLBACK_WEEKLY_SCHEDULE_WEEK = "weekly_schedule_week:"
CALLBACK_WEEKLY_SCHEDULE_LOCATION = "weekly_schedule_location:"


CALLBACK_WEEKLY_SCHEDULE_ADMIN = "weekly_schedule_admin"
CALLBACK_WEEKLY_SCHEDULE_ADMIN_GROUP = "weekly_schedule_admin_group:"
CALLBACK_WEEKLY_SCHEDULE_ADMIN_DAY = "weekly_schedule_admin_day:"
CALLBACK_WEEKLY_SCHEDULE_ADMIN_VIEW = "weekly_schedule_admin_view:"
CALLBACK_WEEKLY_SCHEDULE_ADMIN_ADD = "weekly_schedule_admin_add:"
CALLBACK_WEEKLY_SCHEDULE_ADMIN_EDIT = "weekly_schedule_admin_edit:"
CALLBACK_WEEKLY_SCHEDULE_ADMIN_DELETE = "weekly_schedule_admin_delete:"
CALLBACK_WEEKLY_SCHEDULE_ADMIN_CONFIRM_DELETE = "weekly_schedule_admin_confirm_delete:"
CALLBACK_WEEKLY_SCHEDULE_ADMIN_LOCATIONS = "weekly_schedule_admin_locations"
CALLBACK_WEEKLY_SCHEDULE_ADMIN_ALTERNATING = "weekly_schedule_admin_alternating"

CALLBACK_SCHEDULE_EDIT_FIELD = "schedule_edit_field:"
CALLBACK_SCHEDULE_EDIT_TIME_START = "schedule_edit_time_start:"
CALLBACK_SCHEDULE_EDIT_TIME_END = "schedule_edit_time_end:"
CALLBACK_SCHEDULE_EDIT_COURSE = "schedule_edit_course:"
CALLBACK_SCHEDULE_EDIT_LOCATION = "schedule_edit_location:"
CALLBACK_SCHEDULE_EDIT_TYPE = "schedule_edit_type:"
CALLBACK_SCHEDULE_EDIT_ALTERNATING = "schedule_edit_alternating:"

CALLBACK_ALTERNATING_LIST = "alternating_list"
CALLBACK_ALTERNATING_EDIT = "alternating_edit:"
CALLBACK_ALTERNATING_EDIT_DATE = "alternating_edit_date:"
CALLBACK_ALTERNATING_ADD = "alternating_add"


CALLBACK_NOTIFICATION_SETTINGS = "notification_settings"
CALLBACK_NOTIFICATION_DISABLE_HOMEWORK = "notification_disable_homework"
CALLBACK_NOTIFICATION_ENABLE_HOMEWORK = "notification_enable_homework"
CALLBACK_NOTIFICATION_DISABLE_MANUAL = "notification_disable_manual"
CALLBACK_NOTIFICATION_ENABLE_MANUAL = "notification_enable_manual"
CALLBACK_NOTIFICATION_DISABLE_CUSTOM = "notification_disable_custom"
CALLBACK_NOTIFICATION_ENABLE_CUSTOM = "notification_enable_custom"
CALLBACK_NOTIFICATION_DISABLE_ALL = "notification_disable_all"
CALLBACK_NOTIFICATION_ENABLE_ALL = "notification_enable_all"


DEFAULT_REMINDERS = "3,2,1"
MAX_INPUT_LENGTH = 2000
MAX_DESCRIPTION_LENGTH = 5000
MAIN_MENU_BUTTONS = ("Homeworks", "Weekly Schedule", "FAQ", "Update Info")
REGISTRATION_GROUP_OPTIONS = ("Group 1", "Group 2", "Group 3", "Group 4")
REGISTRATION_GROUP_NORMALIZATION = {
    option.casefold(): f"{index:02d}"
    for index, option in enumerate(REGISTRATION_GROUP_OPTIONS, start=1)
}


PENDING_STEP_TARGET_TYPE = "target_type"
PENDING_STEP_ENTER_TARGET = "enter_target"
PENDING_STEP_ENTER_TEXT = "enter_text"
PENDING_STEP_ENTER_CONTENT = "enter_content"  
PENDING_STEP_ENTER_CHAT = "enter_chat"
PENDING_STEP_ENTER_THREAD = "enter_thread_or_reply"
PENDING_STEP_ENTER_DATETIME = "enter_datetime"
