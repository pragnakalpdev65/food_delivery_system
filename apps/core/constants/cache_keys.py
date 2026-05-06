class CacheKey:
    LOGIN_ATTEMPTS_PREFIX = "login_attempts:%s"
    LOGIN_LOCK_PREFIX = "login_lock:%s"
    EMAIL_CHANGE = "email_change:%s"
    OLD_TOKEN = "old_token:%s"
    NEW_TOKEN = "new_token:%s"

    RESTAURANT_LIST = "restaurant_list"
    RESTAURANT_DETAIL = "restaurant_detail:%s"
    RESTAURANT_MENU = "restaurant_menu:%s"
    POPULAR_RESTAURANTS = "popular_restaurants"