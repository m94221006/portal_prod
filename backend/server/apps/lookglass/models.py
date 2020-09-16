from django.db import models

# Create your models here.
class TaskStatus(models.Model):
    name = models.CharField(max_length=50)
    enabled = models.BooleanField(default=True)

    objects = models.Manager()  # The default manager.

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'task_status'
    
class Task(models.Model):
    cid = models.IntegerField(default=0)
    uid = models.IntegerField(default=0)
    periodictask_id = models.IntegerField(default=1)
    name = models.CharField(max_length=50)
    starttime = models.DateTimeField()
    period = models.CharField(max_length=50)
    every = models.IntegerField(default=1)
    times = models.IntegerField(default=3)
    command = models.CharField(max_length=50)
    command_host =  models.CharField(max_length=200,default='')
    command_postdata = models.TextField()
    nodes =  models.TextField()
    status = models.ForeignKey(TaskStatus, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=True)
    created_by= models.CharField(max_length =50,default="system")
    created_time = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length =50,default="system")
    updated_time = models.DateTimeField(auto_now=True)

    objects = models.Manager()  # The default manager.

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'task'

class TaskDetail(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    task_request_id = models.CharField(max_length=200 ,default="")
    enabled = models.BooleanField(default=True)
    created_by= models.CharField(max_length =50,default="system")
    created_time = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()  # The default manager.

    def __str__(self):
        return self.task.name

    class Meta:
        db_table = 'taskdetail'


class TaskReport(models.Model):
    detail = models.ForeignKey(TaskDetail,default =1 ,on_delete=models.CASCADE)
    instaince_id = models.IntegerField(default = 1)
    history_id = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)
    created_by= models.CharField(max_length =50,default="system")
    created_time = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()  # The default manager.

    def __str__(self):
        return self.detail.task_request_id

    class Meta:
        db_table = 'taskreport'














