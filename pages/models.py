from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class AppImage(models.Model):
    name = models.CharField(max_length=255, unique=True)
    image = models.ImageField()

    def __str__(self):
        return self.name

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url
    

class BusinessSystem(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name
    

class Room(models.Model):
    choices = (
        ('Ground Floor', 'Ground Floor'),
        ('First Floor', 'First Floor'),
        ('Second Floor', 'Second Floor'),
        ('Third Floor', 'Third Floor'),
        ('Fourth Floor', 'Fourth Floor'),
        ('Fifth Floor', 'Fifth Floor'),
        ('Sixth Floor', 'Sixth Floor'),
        ('NIL', 'NIL'),
    )
    number = models.CharField(max_length=10, unique=True)
    floor = models.CharField(choices=choices, max_length=255)

    def __str__(self):
        return self.number
    

class Team(models.Model):
    name = models.CharField(max_length=1024)
    cluster = models.IntegerField(default=1, blank=True)
    business_system = models.ForeignKey(to=BusinessSystem, db_column='bs_name', on_delete=models.CASCADE, null=True)
    course = models.CharField(max_length=4)
    number = models.IntegerField()

    def __str__(self):
        return self.name + '_' + self.course

    def save(self, *args, **kwargs):
        team = Team.objects.filter(name=self.name, course=self.course).count()
        if team:
            raise ValidationError(message=f'There already exists a team with the name {self.name} in the course {self.course}')
        super(Team, self).save(*args, **kwargs)


class Review(models.Model):
    number = models.IntegerField()
    instructions = models.TextField()
    questions = models.TextField()
    score_required = models.BooleanField(default=True)
    time_of_attendance = models.TimeField(null=True)
    time_of_review = models.TimeField()
    date_of_review = models.DateField()
    attendance_open = models.BooleanField(default=True)
    scoring_open = models.BooleanField(default=True)
    team_progress_open = models.BooleanField(default=True)

    def __str__(self):
        return str(self.number)

class TeamReviewRoom(models.Model):
    team = models.ForeignKey(to=Team, on_delete=models.CASCADE)
    review = models.ForeignKey(to=Review, on_delete=models.CASCADE)
    room = models.ForeignKey(to=Room, on_delete=models.CASCADE, null=True)

    def save(self, *args, **kwargs):
        if TeamReviewRoom.objects.filter(team=self.team, review=self.review).count():
            raise ValidationError(message='Already exists')
        super(TeamReviewRoom, self).save(*args, **kwargs)

    @property
    def get_students(self):
        students = Student.objects.filter(team=self)
        return list(students)

    def get_teams_with_review_room(review, room):
        trrs = TeamReviewRoom.objects.filter(review=review, room=room)
        teams = []
        it = trrs.iterator()
        for i in it:
            teams.append(i.team)
        return teams

    def __str__(self):
        return self.team.name + '_' + self.team.course + '_' + str(self.review.number)

class StudentReviewScore(models.Model):
    student = models.ForeignKey(to='Student', on_delete=models.CASCADE)
    review = models.ForeignKey(to=Review, on_delete=models.CASCADE)
    comments = models.TextField(max_length=2000)
    score = models.IntegerField(default=0)

    # def save(self, *args, **kwargs):
    #     if StudentReviewScore.objects.filter(student=self.student, review=self.review).count():
    #         raise ValidationError(message='Cannot have duplicate scoring for a review')
    #     super(StudentReviewScore, self).save(*args, **kwargs)

    def __str__(self):
        return self.student.registration_no + '_' + str(self.review.number)

class StudentReviewAttendance(models.Model):
    posted_by = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, blank=True)
    student = models.ForeignKey(to='Student', on_delete=models.CASCADE)
    review = models.ForeignKey(to=Review, on_delete=models.CASCADE)
    absent = models.BooleanField(default=False)

    # def save(self, *args, **kwargs):
    #     if StudentReviewAttendance.objects.filter(student=self.student, review=self.review).count():
    #         raise ValidationError(message='Cannot have duplicate scoring for a review')
    #     super(StudentReviewAttendance, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.student.registration_no + '_review: ' + str(self.review.number)
    
class Student(models.Model):
    registration_no = models.CharField(max_length=10, unique=True)
    team = models.ForeignKey(to=Team, on_delete=models.CASCADE)
    
    @property
    def attendance(self):
        sras = StudentReviewAttendance.objects.filter(student=self)
        attended = sras.filter(absent=False).count()
        total = sras.count()
        if total == 0:
            return '0%'    
        return str((attended / total) * 100) + '%'

    @property
    def score(self):
        srcs = StudentReviewScore.objects.filter(student=self)
        score = 0
        for s in srcs:
            score += s.score
        return score
    def __str__(self):
        return str(self.registration_no)


class Feedback(models.Model):
    issue_types = (
        ('Faculty Absent', 'Faculty Absent'),
        ('Web Application Issue', 'Web Application Issue'),
        ('WIFI issue', 'Network Connectivity'),
        ('Others', 'Others'),
    )

    registration_no = models.CharField(max_length=10)
    room = models.ForeignKey(to=Room, on_delete=models.CASCADE)
    issue_type = models.CharField(choices=issue_types, max_length=500)
    issue = models.TextField(max_length=10000)
    complaint_raised_time = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return self.issue
    
class Announcement(models.Model):
    announcement_types = (
        ('Room Change', 'Room Change'),
        ('Disciplinary Activities', 'Disciplinary Activities'),
        ('Facilities', 'Facilities'),
        ('Others', 'Others')
    )
    title = models.CharField(max_length=300)
    content = models.CharField(max_length=1025)
    type = models.CharField(max_length=1000, null=True, blank=True, choices=announcement_types)
    recorded_date = models.DateField(auto_now_add=True)
    recorded_time = models.TimeField(auto_now_add=True)
    groups = models.ManyToManyField(to=Group)
    important = models.BooleanField(default=False)

    def __str__(self):
        return self.title + '_' + str(self.recorded_time)
    
class TeamProgress(models.Model):
    team = models.ForeignKey(to=Team, on_delete=models.CASCADE)
    description = models.TextField(blank=False)
    review = models.ForeignKey(to=Review, on_delete=models.CASCADE)
    self_rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    submission_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.team) + '_' + str(self.review.number)

    class Meta:
        unique_together = ('team', 'review')
        managed = True

class FacultyReviewRoom(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.user) + '_' + str(self.review)

    class Meta:
        unique_together = ('user', 'review')
