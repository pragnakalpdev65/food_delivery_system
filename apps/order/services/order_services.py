VALID_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["preparing", "cancelled"],
    "preparing": ["ready"],
    "ready": ["picked_up"],
    "picked_up": ["delivered"],
}