from django.urls import path

from .views import (FileUploadView, ListFilesView, FileDeleteView, DownloadFileView, ChangeCommentView,
                    ChangeNameView, ShareLinkView, SpecialLinkView, UserFilesView)

urlpatterns = [
    path('', ListFilesView.as_view(), name='list'),
    path('<int:user_id>/', UserFilesView.as_view(), name='user_files'),
    path('upload/', FileUploadView.as_view(), name='upload'),
    path('delete/<int:file_id>/', FileDeleteView.as_view(), name='file-delete'),
    path('download/<int:file_id>/', DownloadFileView.as_view(), name='download-file'),
    path('comment/', ChangeCommentView.as_view(), name='change-comment'),
    path('changename/', ChangeNameView.as_view(), name='change-name'),
    path('sharelink/<int:file_id>/', ShareLinkView.as_view(), name='share-link'),
    path('<str:special_link>/', SpecialLinkView.as_view(), name='special_link'),
]