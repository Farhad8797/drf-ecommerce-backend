from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation
from utils.imagekit import imagekit
from django.db import transaction

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
    image = serializers.ImageField(allow_null=True, required=False, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'image', 'type', 'image_id']

    def validate(self, attrs:dict) -> dict:
        image = attrs.get('image', None)
        type = attrs.get('type')

        if type == User.UserType.MERCHANT and not image:
            raise serializers.ValidationError({
                'image': 'An image is required when registering as a merchant.'
            })
        
        return attrs
    
    def create(self, validated_data: dict):
        image = validated_data.pop('image', None)
        image_url, image_id = None, None
        if image:
            try:
                upload_response = imagekit.files.upload(
                    file=image.read(),
                    folder='/users/avatars',
                    file_name=image.name
                )
                image_url = upload_response.url
                image_id = upload_response.file_id
                validated_data['image'] = image_url
            except Exception as e:
                raise serializers.ValidationError({
                    'image': f'Image upload failed: {str(e)}'
                })

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=validated_data['email'],
                    username=validated_data['username'],
                    password=validated_data['password'],
                    type=validated_data.get('type', User.UserType.CUSTOMER),
                    image=image_url or None,
                    image_id=image_id or None
                )
                return user
            
        except Exception as db_error:
            if image_id:
                imagekit.files.delete(file_id=image_id)
            raise serializers.ValidationError({'Error': f'Could not create user; {db_error}'})

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
    image = serializers.ImageField(write_only=True, allow_null=True, required=False)
    class Meta:
        model = User
        fields = ['username', 'image', 'type']

    def validate(self, attrs : dict) -> dict:
        user_type = attrs.get('type', getattr(self.instance, 'type', None))
        new_image = attrs.get('image', None)
        existing_image = getattr(self.instance, 'image', None)
        if(user_type == User.UserType.MERCHANT and not (new_image or existing_image)):
            raise serializers.ValidationError('Merchant must have an image')
        return attrs
    
    def update(self, instance, validated_data: dict):
        new_image = validated_data.pop('image', None)
        new_image_url, new_image_id  = None, None
        old_image_url, old_image_id = getattr(instance, 'image', None), getattr(instance, 'image_id', None)

        if new_image:
            try:
                upload_response = imagekit.files.upload(
                    file=new_image.read(),
                    folder='/users/avatars',
                    file_name=new_image.name
                )
                new_image_url = upload_response.url
                new_image_id = upload_response.file_id
    
            except Exception as e:
                raise serializers.ValidationError({
                    'image': f'Image upload failed: {str(e)}'
                })
            
        for key, val in validated_data.items():
            setattr(instance, key, val)

        try:
            if old_image_url and new_image:
                imagekit.files.delete(file_id=old_image_id)
            if new_image_url:
                instance.image, instance.image_id = new_image_url, new_image_id
            with transaction.atomic():
                instance.save()
        except Exception as db_error:
            if new_image_url:
                imagekit.files.delete(file_id=new_image_id)
            raise serializers.ValidationError({'Error': f'Could not create user; {db_error}'})
                