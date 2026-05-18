from apps.order.models.notification import Notification


class NotificationService:

    @staticmethod
    def notify_restaurant_rating(restaurant, rating):
        recipient = getattr(restaurant, "owner", None)

        if not recipient:
            return

        Notification.objects.create(
            recipient=recipient,
            title="New Rating Received",
            message=(
                f"New rating {rating.overall_rating}/5 "
                f"for Order #{rating.order.order_number}"
            )
        )