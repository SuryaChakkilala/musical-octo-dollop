from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
import csv
from django.http import HttpResponse
from django.contrib.auth.models import User, Group
import datetime
import random
import string
from django.db.models import Q
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string

# Create your views here.
def home(request):
    image = AppImage.objects.filter(name='home_image').first()
    if image:
        context = {'image': image}
    else:
        context = {'image': ''}
    return render(request, 'pages/home.html', context=context)

def feedback(request):
    if request.method == "POST":
        feedback = Feedback()
        feedback.room = Room.objects.get(number=request.POST['room'])
        feedback.issue_type = request.POST['it']
        feedback.issue = request.POST['issue']
        feedback.save()

        emailaddr = ''
        template = ''

        if Group.objects.get(name='STUDENT') in request.user.groups.all():
            emailaddr = request.user.username + '@kluniversity.in'
            template = render_to_string('pages/feedback_email.html', {'registration_no': request.user.username,'role': 'Student', 'issue_type': feedback.issue_type, 'issue': feedback.issue, 'room': feedback.room.number})


        email = EmailMultiAlternatives(
            'Feedback Submission Acknowledgement',
            '',
            settings.EMAIL_HOST_USER,
            [emailaddr],
        )
        email.attach_alternative(template, 'text/html')
        email.send()

        return redirect('home')

    issue_types = (
        'Faculty Absent',
        'Web Application Issue',
        'WIFI issue',
        'Others',
    )
    instructions = ''
    feedback_content = ''
    rooms = Room.objects.all()
    context = {'issue_types': issue_types, 'rooms': rooms, 'instructions': instructions, 'feedback_content': feedback_content}
    return render(request, 'pages/feedback.html', context=context)

def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Username (or) Password is incorrect')

    context = {}
    return render(request, 'pages/login.html', context)

def logoutUser(request):
    if not request.user.is_authenticated:
        return redirect('home')
    messages.success(request, f'{request.user} has been succesfully logged out.')
    logout(request)
    return redirect('login')

def update_rooms(request):
    teams = Team.objects.all()
    reviews = Review.objects.all()
    for team in teams:
        for review in reviews:
            trr = TeamReviewRoom()
            trr.team = team
            trr.review = review
            trr.save()
    with open('rooms_ranges.csv') as file:
        csv_reader = csv.reader(file)
        c = 0
        for row in csv_reader:
            if c == 0:
                c += 1
            else:
                course = row[0]
                cluster = int(row[1])
                min_team = int(row[2])
                max_team = int(row[3])
                room_no = row[4]
                room = Room.objects.get(number=room_no)
                teams = Team.objects.filter(cluster=cluster, course=course, number__gte=min_team, number__lte=max_team)
                trrs = TeamReviewRoom.objects.filter(team__in=teams)
                trrs.update(room=room)
    return HttpResponse('done')

def faculty_upload(request):
    group = Group.objects.get(name='FACULTY')
    with open('faculty.csv', 'r+') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            user = User()
            user.username = row[0]
            user.set_password(f'klu_{row[0]}')
            user.first_name = row[1]
            try:
                user.save()
                user.groups.add(group)
                user.save()
            except:
                print(user.username)
    return HttpResponse('done')

def attendance_status(request):
    rooms = Room.objects.all()
    reviews = Review.objects.all()
    response = HttpResponse()
    response['Content-Disposition'] = f'attachment; filename=attendance_status_{datetime.datetime.now()}.csv'
    writer = csv.writer(response)
    header = ['room']
    for review in reviews:
        header.append(f'review-{review.number}')
    writer.writerow(header)
    for room in rooms:
        row = [f'{room.number}']
        for review in reviews:
            trrs = TeamReviewRoom.objects.filter(room=room, review=review).first()
            team = trrs.team
            if StudentReviewAttendance.objects.filter(student__team=team, review=review).count():
                row.append('YES')
            else:
                row.append('NO')
        writer.writerow(row)
    return response

def student_marks_report(request):
    students = Student.objects.all()
    reviews = Review.objects.all()
    response = HttpResponse()
    response['Content-Disposition'] = f'attachment; filename=student_marks_{datetime.datetime.now()}.csv'
    writer = csv.writer(response)
    header = ['registration_no']
    for review in reviews:
        if not review.score_required:
            continue
        header.append(f'review-{review.number}-score')
    header.append('Overall Score (Out of 50)')
    writer.writerow(header)
    for student in students:
        row = [student.registration_no]
        for review in reviews:
            if not review.score_required:
                continue
            score = StudentReviewScore.objects.filter(student=student, review=review).first()
            if score:
                row.append(score.score)
            else:
                row.append(0)
        row.append(student.score)
        writer.writerow(row)
    return response

def student_attendance_report(request):
    students = Student.objects.all()
    reviews = Review.objects.all()
    response = HttpResponse()
    response['Content-Disposition'] = f'attachment; filename=student-attendance-{datetime.datetime.now()}.csv'
    writer = csv.writer(response)
    header = ['registration_no']
    for review in reviews:
        header.append(f'review-{review.number}')
    header.append('Overall Attendance %')
    writer.writerow(header)
    for student in students:
        row = [student.registration_no]
        for review in reviews:
            att = StudentReviewAttendance.objects.filter(student=student, review=review).first()
            if att and not att.absent:
                row.append('YES')
            else:
                row.append('NO')
        row.append(student.attendance)
        writer.writerow(row)
    return response

def review_status(request):
    rooms = Room.objects.all()
    reviews = Review.objects.all()
    response = HttpResponse()
    response['Content-Disposition'] = f'attachment; filename=review-status-{datetime.datetime.now()}.csv'
    writer = csv.writer(response)
    header = ['room']
    for review in reviews:
        header.append(f'review-{review.number}')
    writer.writerow(header)
    for room in rooms:
        row = [f'{room.number}']
        for review in reviews:
            trrs = TeamReviewRoom.objects.filter(room=room, review=review).first()
            team = trrs.team
            scr = StudentReviewScore.objects.filter(student__team=team, review=review)
            if scr.count():
                row.append('YES')
            else:
                row.append('NO')
        writer.writerow(row)
    return response

def get_zero_score_review(request):
    reviews = Review.objects.all()
    response = HttpResponse()
    response['Content-Disposition'] = f'attachment; filename=zero-score-report-{datetime.datetime.now()}.csv'
    writer = csv.writer(response)
    writer.writerow(['registration_no', 'review_no'])
    students = Student.objects.all()
    for review in reviews:
        absentees = StudentReviewAttendance.objects.filter(absent=True, review=review)
        stus = []
        for a in absentees:
            stus.append(a.student)
        for student in students:
            if absentees.filter(student=student).count():
                continue
            zero_score = StudentReviewScore.objects.filter(review=review, student=student).first()
            if (not zero_score) or (zero_score.score == 0):
                writer.writerow([student.registration_no, review.number])
    return response

def reports_page(request):
    if request.method == "POST":
        report_type = request.POST['report_type']
        if report_type == "room_attendance":
            return attendance_status(request)
        elif report_type == "review_status":
            return review_status(request)
        elif report_type == "student_attendance":
            return student_attendance_report(request)
        elif report_type == "student_score":
            return student_marks_report(request)
        elif report_type == "review_zero_score":
            return get_zero_score_review(request)
    context = {}
    return render(request, 'pages/report_form.html', context=context)

def update_it_attendance(request):
    reviews = Review.objects.all()
    rooms = Room.objects.all()
    trrs = TeamReviewRoom.objects.filter(review__number=2, team__name__contains='t200')
    for t in trrs:
        for r in reviews:
            if r.number == 2:
                continue
            tr = TeamReviewRoom()
            tr.team = t.team
            tr.review = r
            tr.room = trrs.filter(team=t.team).first().room
            tr.save()
    return HttpResponse('done')


def student_score_form(request):
    if request.method == "POST":
        reg_no = request.POST['reg_no']
        student = Student.objects.filter(registration_no=reg_no).first()
        scores = StudentReviewScore.objects.filter(student=student).order_by('review__number')

        context = {'scores': scores, 'student': student}
        return render(request, 'learnathon/student_form.html', context=context)
    context = {}
    return render(request, 'learnathon/student_form.html', context=context)


def make_announcement(request):
    if not request.user.is_superuser:
        return redirect('home')
    if request.method == "POST":
        selected_groups = request.POST.getlist('groups')
        ann_groups = Group.objects.filter(name__in=selected_groups)
        ann = Announcement()
        ann.title = request.POST['title']
        ann.content = request.POST['content']
        ann.type = request.POST['type']
        ann.important = True if request.POST['important'] == 'YES' else False
        ann.save()

        for grp in ann_groups:
            ann.groups.add(grp)
        ann.save()

        student_group = Group.objects.get(name='STUDENT')
        if student_group in ann_groups:
            emails = []
            users = Student.objects.all()
            for student in users:
                emails.append(f'{student.registration_no}@kluniversity.in')
            email = EmailMultiAlternatives(
                'Announcement Alert!',
                f'An Announcement has been made regarding: {ann.title}. Please check the dashboard for more information.',
                settings.EMAIL_HOST_USER,
                emails,
            )
            email.send()
        return redirect('home')
    context = {}
    return render(request, 'pages/announcement.html', context=context)


def generate_password():
    res = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    return res


def generate_student_users(request):
    if not request.user.is_superuser:
        return redirect('home')
    student_group = Group.objects.get(name='STUDENT')
    response = HttpResponse()
    response['Content-Disposition'] = f'attachment; filename=review-status-{datetime.datetime.now()}.csv'
    writer = csv.writer(response)
    header_row = ['Username', 'Password']
    writer.writerow(header_row)
    students = Student.objects.all()
    for student in students:
        user = User()
        user.username = student.registration_no
        user.email = student.registration_no + '@kluniversity.in'
        password = generate_password()
        user.set_password(password)
        try:
            user.save()
            user.groups.add(student_group)
            user.save()
            writer.writerow([user.username, password])
        except:
            print(student.registration_no)
    return response

def allocate_rooms(request):
    teams = Team.objects.all()
    reviews = Review.objects.all()
    for team in teams:
        for review in reviews:
            trr = TeamReviewRoom()
            trr.team = team
            trr.review = review
            trr.save()
    with open('room_allocation.csv') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            room_no = row[0]
            room = Room.objects.get(number=room_no)
            teams_list = row[1].split(',')
            for i in range(len(teams_list)):
                teams_list[i] = 'MSWD-'+teams_list[i][4:]
            teams = Team.objects.filter(name__in=teams_list)
            trrs = TeamReviewRoom.objects.filter(team__in=teams).update(room=room)
    return HttpResponse('done')

def allocate_rooms2(request):
    teams = Team.objects.all()
    reviews = Review.objects.all()
    with open('room_allocation2.csv') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            room_no = row[0]
            room = Room.objects.get(number=room_no)
            teams_list = row[1][:-1].split(',')
            for i in range(len(teams_list)):
                teams_list[i] = 'PFSD-'+teams_list[i][4:]
            teams = Team.objects.filter(name__in=teams_list)
            trrs = TeamReviewRoom.objects.filter(team__in=teams).update(room=room)
    return HttpResponse('done')

def faculty_user_generation(request):
    response = HttpResponse()
    response['Content-Disposition'] = f'attachment; filename=faculty-credentials-{datetime.datetime.now()}.csv'
    writer = csv.writer(response)
    header_row = ['username', 'password']
    with open('faculty_users.csv') as file:
        csv_reader = csv.reader(file)
        faculty_group = Group.objects.get(name='FACULTY')
        for row in csv_reader:
            emp_id = row[0]
            name = row[1]
            user = User()
            user.username = emp_id
            user.first_name = name
            password = generate_password()
            user.set_password(password)
            try:
                user.save()
                user.groups.add(faculty_group)
                user.save()
                writer.writerow([emp_id, password])
            except:
                print(emp_id)
    return response

def faculty_room_allocation(request):
    with open('faculty_users.csv') as file:
        csv_reader = csv.reader(file)
        faculty_group = Group.objects.get(name='FACULTY')
        for row in csv_reader:
            emp_id = row[0]
            room_no = row[2]
            user = User.objects.get(username=emp_id)
            reviews = Review.objects.all()
            room = Room.objects.get(number=room_no)
            for review in reviews:
                frr = FacultyReviewRoom()
                frr.user = user
                frr.review = review
                frr.room = room
                frr.save()
    return HttpResponse('done')