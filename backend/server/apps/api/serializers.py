from rest_framework import serializers
from idcinfo.models import DeviceInfo
from testing.models import TestItem,TestCase
import cerberus

class DeviceInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceInfo

class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase


class DeviceTestCaseSerializer(serializers.Serializer):
    devices = DeviceInfoSerializer(many=True)
    TestCases = TestCaseSerializer(many=True)



'''
class TaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Task
        read_only_fields = ('id', 'state', 'result', 'task_id',)
        fields = ('id', 'state', 'params', 'result', 'task_id')

    def validate_params(self, params):
        if params is None or params == '':
            raise serializers.ValidationError("Params cannot be empty")

        schema = {'arg1': {'type': 'string', 'required': True},
                  'arg2': {'type': 'string', 'required': True}}
        validator = cerberus.Validator(schema)

        if not validator.validate(params):
            raise serializers.ValidationError(validator.errors)
        return params
'''
