from rest_framework.pagination import CursorPagination

class MessageCursorPagination(CursorPagination):
    page_size = 20
    ordering = 'timestamp'
