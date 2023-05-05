from django.shortcuts import render, redirect
from pages.models import Review, Room, TeamReviewRoom, Student, Team, StudentReviewAttendance, StudentReviewScore, AppImage, Announcement, TeamProgress
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.template.loader import render_to_string
import datetime
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.conf import settings

# Create your views here.
def home(request):
    user_groups = request.user.groups.all()
    announcements = Announcement.objects.filter(groups__in=user_groups).order_by('-recorded_date', '-recorded_time')
    reviews = Review.objects.all()
    attendance = ''
    score = ''
    context = {'reviews': reviews}
    if Group.objects.get(name='STUDENT') in user_groups:
        student = Student.objects.get(registration_no=request.user.username)
        attendance = student.attendance
        score = student.score
        team = student.team
        team_review_rooms = TeamReviewRoom.objects.filter(team=team)
        context['review_rooms'] = team_review_rooms
        context['team_no'] = student.team
    context['announcements'] = announcements[:4]
    context['attendance'] = attendance
    context['score'] = score
    return render(request, 'learnathon/home.html', context)


def rooms(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_groups = request.user.groups.all()
    faculty_group = Group.objects.filter(name='FACULTY').first()
    if faculty_group not in user_groups:
        return redirect('home')
    rooms = Room.objects.all().order_by('number')
    f0 = rooms.filter(floor='Ground Floor')
    f1 = rooms.filter(floor='First Floor')
    f2 = rooms.filter(floor='Second Floor')
    f3 = rooms.filter(floor='Third Floor')
    f4 = rooms.filter(floor='Fourth Floor')
    f5 = rooms.filter(floor='Fifth Floor')
    f6 = rooms.filter(floor='Sixth Floor')

    context = {'f0': f0, 'f1': f1, 'f2': f2, 'f3': f3, 'f4': f4, 'f5': f5, 'f6': f6}

    return render(request, 'learnathon/rooms.html', context=context)

def review_page(request, room_no):
    if not request.user.is_authenticated:
        return redirect('login')
    user_groups = request.user.groups.all()
    faculty_group = Group.objects.filter(name='FACULTY').first()
    if faculty_group not in user_groups:
        return redirect('home')
    reviews = Review.objects.all()
    room = Room.objects.get(number=room_no)
    context = {'room': room, 'reviews': reviews}

    return render(request, 'learnathon/review_page.html', context=context)

def review_room_attendance(request, number, room_no):
    if not request.user.is_authenticated:
        return redirect('login')
    user_groups = request.user.groups.all()
    faculty_group = Group.objects.filter(name='FACULTY').first()
    if faculty_group not in user_groups:
        return redirect('home')
    review = Review.objects.get(number=number)
    if not review.attendance_open:
        return redirect('learnathon_review_page', room_no=room_no)
    room = Room.objects.get(number=room_no)
    teams = TeamReviewRoom.get_teams_with_review_room(review, room)
    students = Student.objects.filter(team__in=teams).order_by('-team')
    if request.method == "POST":
        absentees = request.POST.getlist('absentees')
        StudentReviewAttendance.objects.filter(student__in=students, review=review).update(posted_by=request.user, absent=False)
        StudentReviewAttendance.objects.filter(review=review, student__registration_no__in=absentees).update(posted_by=request.user, absent=True)

        return redirect('learnathon_review_page', room_no=room_no)
    
    it = students.iterator()

    students_attendance = []
    for student in it:
        stu, created = StudentReviewAttendance.objects.get_or_create(student=student, review=review)
        students_attendance.append(stu)

    context = {'review_no': number, 'room_no': room_no, 'students_attendance': students_attendance}
    return render(request, 'learnathon/attendance.html', context=context)

def student_form(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_groups = request.user.groups.all()
    faculty_group = Group.objects.filter(name='FACULTY').first()
    if faculty_group not in user_groups:
        return redirect('home')
    if request.method == "POST":
        reg_no = request.POST['reg_no']
        student = Student.objects.filter(registration_no=reg_no).first()
        attendances = StudentReviewAttendance.objects.filter(student=student).order_by('review__number')

        context = {'attendances': attendances, 'student': student}
        return render(request, 'learnathon/student_form.html', context=context)
    context = {}
    return render(request, 'learnathon/student_form.html', context=context)

def student_score_form(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_groups = request.user.groups.all()
    faculty_group = Group.objects.filter(name='FACULTY').first()
    if faculty_group not in user_groups:
        return redirect('home')
    if request.method == "POST":
        reg_no = request.POST['reg_no']
        student = Student.objects.filter(registration_no=reg_no).first()
        scores = StudentReviewScore.objects.filter(student=student).order_by('review__number')

        context = {'scores': scores, 'student': student}
        return render(request, 'learnathon/student_score_form.html', context=context)
    context = {}
    return render(request, 'learnathon/student_score_form.html', context=context)

def review_score_post(request, review_no, room_no):
    if not request.user.is_authenticated:
        return redirect('login')
    user_groups = request.user.groups.all()
    faculty_group = Group.objects.filter(name='FACULTY').first()
    if faculty_group not in user_groups:
        return redirect('home')
    room = Room.objects.get(number=room_no)
    review = Review.objects.get(number=review_no)
    if not review.scoring_open:
        return redirect('learnathon_review_page', room_no=room_no)
    trrs = TeamReviewRoom.objects.filter(room=room, review=review).first()
    context = {'review_no': review_no, 'room_no': room_no}
    if trrs:
        context['teams'] = TeamReviewRoom.get_teams_with_review_room(review, room)
    else:
        context['teams'] = []
    
    return render(request, 'learnathon/review_post_score.html', context=context)

def review_score_post_form(request, review_no, team_no):
    if not request.user.is_authenticated:
        return redirect('login')
    user_groups = request.user.groups.all()
    faculty_group = Group.objects.filter(name='FACULTY').first()
    if faculty_group not in user_groups:
        return redirect('home')
    review = Review.objects.get(number=review_no)
    team = Team.objects.get(name=team_no)
    students = Student.objects.filter(team=team).order_by('registration_no')
    room = TeamReviewRoom.objects.get(team=team, review=review).room

    team_progress = TeamProgress.objects.filter(team=team, review=review).first()

    if (not review.scoring_open) or (not review.score_required):
        return redirect('learnathon_review_page', room_no=room.number)

    v = StudentReviewScore.objects.filter(student=students.first(), review=review).first()
    if v and v.comments:
        context = {'prev_page_url': reverse('learnathon_review_page', args=[room.number]), 'room_no': room.number, 'message': 'Score has already been posted'}
        return render(request, 'learnathon/access_denied.html', context=context)
    
    if request.method == "POST":
        student_review_scores = StudentReviewScore.objects.filter(student__in=students, review=review)
        it = student_review_scores.iterator()
        for student_score in it:
            student_score.posted_by = request.user
            student_score.score = request.POST[f'score_{student_score.student.registration_no}']
            student_score.comments = request.POST[f'comments_{student_score.student.registration_no}']
            student_score.save()
        return redirect('learnathon_review_page', room_no=room.number)

    student_review_scores = []
    student_review_absentees = []
    for student in students:
        student_review_scores.append(StudentReviewScore.objects.get_or_create(review=review, student=student)[0])
    for student in students:
        sra = StudentReviewAttendance.objects.filter(student=student, review=review).first()
        if not sra or sra.absent:
            student_review_absentees.append(student)
    context = {'student_review_scores': student_review_scores, 'instructions': review.instructions.split('\n'), 'questions': review.questions.split('\n'), 'team_no': team.name, 'course': team.course, 'review_no': review_no, 'absentees': student_review_absentees, 'team_progress': team_progress}
    return render(request, 'learnathon/review_post_score_form.html', context=context)

def report(request):
    if not request.user.is_superuser:
        return redirect('learnathon_home')
    context = {}
    return render(request, 'learnathon/report.html', context=context)

def leaderboard(request):
    stus = Student.objects.all()
    d = {}
    mv = -1
    for i in stus:
        if i.score not in d:
            d[i.score] = set()
        d[i.score].add(i)
        mv = max(mv, i.score)
    students = []
    curr = 1
    while len(students) < 100 and mv >= 0:
        if mv not in d:
            mv -= 1
            continue
        for i in d[mv]:
            students.append((curr, i))
        mv -= 1
        curr += 1

    context = {'students': students}
    return render(request, 'learnathon/leaderboard.html', context=context)


def update_attendance_absent(request):
    
    reviews = Review.objects.all()
    for review in reviews:
        students_attendance = StudentReviewAttendance.objects.filter(absent=True, review=review)
        students_list = []
        for s in students_attendance:
            students_list.append(s.student)
        student_review_marks = StudentReviewScore.objects.filter(student__in=students_list, review=review).update(score=0)
    return HttpResponse('done')

def student_attendance_report(request):
    if not request.user.is_authenticated:
        return redirect('home')
    student_group = Group.objects.get(name='STUDENT')
    if not student_group in request.user.groups.all():
        return redirect('home')

    student = Student.objects.filter(registration_no=request.user.username).first()
    attendances = StudentReviewAttendance.objects.filter(student=student).order_by('review__number')

    context = {'attendances': attendances, 'student': student}
    return render(request, 'learnathon/student_attendance_report.html', context=context)

def student_score_report(request):
    if not request.user.is_authenticated:
        return redirect('login')
    student_group = Group.objects.get(name='STUDENT')
    if not student_group in request.user.groups.all():
        return redirect('home')
    student = Student.objects.filter(registration_no=request.user.username).first()
    scores = StudentReviewScore.objects.filter(student=student).order_by('review__number')

    context = {'student': student, 'scores': scores}
    return render(request, 'learnathon/student_score_report.html', context=context)


def announcements(request):
    user_groups = request.user.groups.all()
    announcements = Announcement.objects.filter(groups__in=user_groups).order_by('-recorded_date', '-recorded_time')
    context = {'announcements': announcements}
    return render(request, 'learnathon/announcements.html', context)


def team_progress(request):
    student_group = Group.objects.get(name='STUDENT')
    if student_group not in request.user.groups.all():
        return redirect('learnathon_home')

    reviews = Review.objects.order_by('number')
    team = Student.objects.get(registration_no=request.user.username).team
    progress = [(0, False)] * len(reviews)
    for i in range(len(reviews)):
        obj = TeamProgress.objects.filter(review=reviews[i], team=team).first()
        if obj:
            progress[i] = (reviews[i], False)
        else:
            progress[i] = (reviews[i], True)
    context = {'progress': progress}
    return render(request, 'learnathon/team_progress.html', context=context)

def team_progress_form(request, review_no):
    student_group = Group.objects.get(name='STUDENT')
    if student_group not in request.user.groups.all():
        return redirect('learnathon_home')
    student = Student.objects.get(registration_no=request.user.username)
    team = student.team
    review = Review.objects.get(number=review_no)
    if not review.team_progress_open:
        return redirect('learathon_home')
    if TeamProgress.objects.filter(team=team, review=review).count():
        return redirect('learnathon_home')
    if request.method == "POST":
        team_progress = TeamProgress()
        team_progress.team = team
        team_progress.description = request.POST['description']
        team_progress.review = review
        team_progress.self_rating = int(request.POST['self_rating'])
        team_progress.save()

        emailaddr = request.user.email
        print(emailaddr)

        context = {'registration_no': request.user.username, 'role': 'Student', 'team': team, 'description': team_progress.description, 'review': team_progress.review, 'self_rating': team_progress.self_rating, 'submission_time': datetime.datetime.now()}

        email = EmailMultiAlternatives(
            'Team Progress Form Submission Acknowledgement',
            '',
            settings.EMAIL_HOST_USER,
            [emailaddr],
        )
        template = render_to_string('learnathon/team_progress_email.html', context=context)
        email.attach_alternative(template, 'text/html')
        email.send()

        return redirect('learnathon_home')
        
    context = {}
    return render(request, 'learnathon/team_progress_form.html', context=context)

def rubrics(request):
    reviews = Review.objects.all()
    context = {'reviews': reviews}
    return render(request, 'learnathon/rubrics.html', context=context)