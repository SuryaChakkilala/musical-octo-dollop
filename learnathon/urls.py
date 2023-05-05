from django.urls import path
from .views import home, rooms, review_page, review_room_attendance, student_form, review_score_post, review_score_post_form, student_score_form, leaderboard, update_attendance_absent, student_attendance_report, student_score_report, announcements, team_progress_form, team_progress, rubrics

urlpatterns = [
    path('', home, name='learnathon_home'),
    path('rubrics/', rubrics, name='rubrics'),
    path('rooms/', rooms, name='learnathon_rooms'),
    path('rooms/<str:room_no>', review_page, name='learnathon_review_page'),
    path('rooms/attendance/<int:number>/<str:room_no>', review_room_attendance, name='learnathon_review_room_attendance'),
    path('rooms/review/<int:review_no>/<str:room_no>', review_score_post, name='learnathon_review_score_post'),
    path('rooms/review/form/<int:review_no>/<str:team_no>', review_score_post_form, name='learnathon_review_score_post_form'),
    path('student_form/', student_form, name='student_form'),
    path('student_score_form/', student_score_form, name='student_score_form'),
    path('leaderboard/', leaderboard, name='leaderboard'),
    path('update_absent/', update_attendance_absent, name='update'),
    path('student_attendance_report/', student_attendance_report, name='student_attendance_report'),
    path('student_score_report/', student_score_report, name='student_score_report'),
    path('announcements/', announcements, name='announcements'),
    path('team_progress/', team_progress, name='team_progress'),
    path('team_progress/<int:review_no>', team_progress_form, name='team_progress_form')
]
