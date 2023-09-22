from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from .models import *


# class ModelSerializerVerboseNames(serializers.ModelSerializer):
#     def __init__(self, *args, **kwargs):
#         super(ModelSerializerVerboseNames, self).__init__(*args, **kwargs)

#         if 'labels' in self.fields:
#             raise RuntimeError(
#                 'You cant have labels field defined '
#                 'while using ModelSerializerVerboseNames'
#             )

#         self.fields['labels'] = SerializerMethodField()

#     def get_labels(self, *args):
#         labels = {}

#         for field in self.Meta.model._meta.get_fields():
#             if field.name in self.fields:
#                 labels[field.name] = {'label': field.verbose_name, 'help_text': field.help_text}

#         return labels    


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule 
        fields = '__all__'


class RuleFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleFamily 
        fields = (
            'name', 
            'abbreviation', 
            'description', 
            'elements'
        )


class RuleFamilyFullSerializer(serializers.ModelSerializer):
    elements = RuleSerializer(many=True, read_only=True)
    class Meta:
        model = RuleFamily 
        fields = (
            'name', 
            'abbreviation', 
            'description', 
            'elements'
        )


class BallotTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BallotType 
        fields = ['name', 'description']


class ElectionSerializer(serializers.ModelSerializer):
    budget = serializers.DecimalField(max_digits=50,
                                      decimal_places=2,
                                      coerce_to_string=False)
    class Meta:
        model = Election 
        fields = Election.public_fields        


class ElectionMetadataSerializer(serializers.ModelSerializer):
    # applies_to = BallotTypeSerializer(many=True, read_only=True)
    class Meta:
        model = ElectionMetadata
        fields = ['name', 'short_name', 'description', 'inner_type']


class ElectionDataPropertySerializer(serializers.ModelSerializer):
    metadata = ElectionMetadataSerializer(many=False, read_only=True)
    class Meta:
        model = ElectionDataProperty 
        fields = '__all__'



class RuleResultMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleResultMetadata 
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    rules_selected_by = serializers.SerializerMethodField()
    cost = serializers.DecimalField(max_digits=50,
                                    decimal_places=2,
                                    coerce_to_string=False)
    
    def get_rules_selected_by(self, obj):
        return obj.rule_results_selected_by.all().values_list('rule__abbreviation', flat=True) 

    class Meta:
        model = Project 
        fields = '__all__'


class RuleResultSerializer(serializers.ModelSerializer):
    selected_projects = ProjectSerializer(many=True, read_only=True)
    class Meta:
        model = RuleResult 
        fields = '__all__'
        


class VoterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voter 
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category 
        fields = '__all__'


class TargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target 
        fields = '__all__'


class NeighborhoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Neighborhood 
        fields = '__all__'


class VotingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = VotingMethod 
        fields = '__all__'


