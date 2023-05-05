from django.urls import path
from .views import home, feedback, loginPage, logoutUser, update_rooms, faculty_upload, attendance_status, reports_page, update_it_attendance, make_announcement, generate_student_users, allocate_rooms, allocate_rooms2, faculty_user_generation, faculty_room_allocation, update_faculty_credentials

urlpatterns = [
    path('', home, name='home'),
    path('feedback/', feedback, name='feedback'),
    path('login/', loginPage, name='login'),
    path('logout/', logoutUser, name='logout'),
    path('room_allocation/', update_rooms, name='update-rooms'),
    path('faculty_upload', faculty_upload, name='faculty-upload'),
    path('attendance_status/', attendance_status, name='attendance-status'),
    path('reports_page', reports_page, name='report-form'),
    path('att_upt', update_it_attendance, name='t-att'),
    path('make_announcement/', make_announcement, name='make-announcement'),
    path('generate_students', generate_student_users, name='generate-student-users'),
    path('allocate_rooms/', allocate_rooms, name='allocate-rooms'),
    path('allocate_rooms2/', allocate_rooms2, name='allocate-rooms-2'),
    path('faculty_user_generation/', faculty_user_generation, name='faculty_user_generation'),
    path('faculty_room_allocation/', faculty_room_allocation, name='faculty_room_allocation'),
    path('update_faculty_credentials/', update_faculty_credentials, name='update_faculty_credentials'),
]
