from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    image = serializers.URLField(allow_null=True, allow_blank=True, required=False, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'image', 'type']

    def validate(self, attrs:dict) -> dict:
        image = attrs.get('image')
        type = attrs.get('type')

        if type == User.UserType.MERCHANT and not image:
            raise serializers.ValidationError({
                'image': 'An image is required when registering as a merchant.'
            })
        
        return attrs
    
    def create(self, validated_data: dict):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            type=validated_data.get('type', User.UserType.CUSTOMER),
            image=validated_data.get('image', None)
        )

        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, data):
        user: User = self.context['request'].user
        if not user.check_password(data):
            raise serializers.ValidationError('Old password is incorrect')
        return data
    
    def validate_new_password(self, data):
        password_validation.validate_password(data, user=self.context['request'].user)
        return data
    
    def validate(self, attrs: dict) -> dict:
        if attrs.get('old_password') == attrs.get('new_password'):
            raise serializers.ValidationError('passwords must be distinct')
        return attrs
    

class UpdateAccountInfoSerializer(serializers.ModelSerializer):
    image = serializers.URLField(write_only=True, allow_null=True, allow_blank=True, required=False)
    class Meta:
        model = User
        fields = ['username', 'image', 'type']

    def validate(self, attrs : dict):
        image = attrs.get('image')
        if(attrs.get('type') == User.UserType.MERCHANT and not image):
            raise serializers.ValidationError('Merchant must have an image')
        return attrs