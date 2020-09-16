from django.contrib import admin
from lookglass.models import TaskStatus, Task, TaskDetail, TaskReport


class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "enabled")


class TaskAdmin(admin.ModelAdmin):
    list_display = ("cid", "uid","name","periodictask_id","starttime","perodic","command"
                    ,"status","enabled","created_by","created_time")
    def perodic(self, obj):
        return "{}-{}:{}".format(obj.every,obj.period,obj.times)

class TaskDetailAdmin(admin.ModelAdmin):
    list_display = ("id", "taskname","task_request_id","enabled","created_by","created_time")

    def taskname(self,obj):
        return obj.task.name

class TaskReportAdmin(admin.ModelAdmin):
    list_display = ("id", "taskname","instaince_id","history_id","enabled","created_by","created_time")

    def taskname(self, obj):
        return obj.detail.task.name

admin.site.register(TaskStatus,TaskStatusAdmin)
admin.site.register(Task,TaskAdmin)
admin.site.register(TaskDetail,TaskDetailAdmin)
admin.site.register(TaskReport,TaskReportAdmin)