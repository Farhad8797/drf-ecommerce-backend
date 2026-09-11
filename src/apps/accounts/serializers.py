from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation
from utils.imagekit import imagekit
from django.db import transaction
from django.conf import settings
from utils.stripe import is_merchant_account_ready

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
    image_file = serializers.ImageField(allow_null=True, required=False, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'image', 'type', 'image_id', 'image_file', 'created_at']
        read_only_fields = ['image', 'image_id', 'status']

    def validate(self, attrs:dict) -> dict:
        image_file = attrs.get('image_file', None)
        type = attrs.get('type')

        if type == User.UserType.MERCHANT:
            if not image_file:
                raise serializers.ValidationError({
                    'image': 'An image is required when registering as a merchant.'
                })

        return attrs
    
    def create(self, validated_data: dict):
        image_file = validated_data.pop('image_file', None)
        if image_file:
            try:
                upload_response = imagekit.files.upload(
                    file=image_file.read(),
                    folder='/users/avatars',
                    file_name=image_file.name
                )
                validated_data['image'] = upload_response.url
                validated_data['image_id'] = upload_response.file_id
            except Exception as e:
                raise serializers.ValidationError({
                    'image': f'Image upload failed: {str(e)}'
                })

        try:
            with transaction.atomic():
                user = User.objects.create_user(**validated_data)
                return user
            
        except Exception as db_error:
            if image_file:
                imagekit.files.delete(file_id=validated_data['image_id'])
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
    image_file = serializers.ImageField(write_only=True, allow_null=True, required=False)
    class Meta:
        model = User
        fields = ['username', 'image', 'type', 'stripe_account_id', 'paypal_account_id', 'image_id', 'image_file', 'status']
        read_only_fields = ['image', 'image_id', 'status']

    def validate(self, attrs : dict) -> dict:
        user_type = attrs.get('type', getattr(self.instance, 'type', None))
        new_image = attrs.get('image_file', None)
        existing_image = getattr(self.instance, 'image', None)
        new_stripe_id = attrs.get('stripe_account_id', None)
        new_paypal_id = attrs.get('paypal_account_id', None)
        stripe_id = new_stripe_id or getattr(self.instance, 'stripe_account_id', None)
        paypal_id = new_paypal_id or getattr(self.instance, 'paypal_account_id', None)
        user_status = getattr(self.instance, 'status', None)

        if user_type == User.UserType.MERCHANT:
            if not (new_image or existing_image):
                raise serializers.ValidationError({'error':'No image provided and no existing image found for this user. A merchant must have at least one image.'})
            
            if user_status == User.UserStatus.VERIFIED:
                if not stripe_id and not paypal_id:
                    raise serializers.ValidationError({'error': 'No payment method id provided! A merchant must provide paypal or stripe id.'})
                
                if new_stripe_id:
                    if not is_merchant_account_ready(stripe_id):
                        raise serializers.ValidationError({
                            'stripe_account_id': 'This Stripe account is not fully verified or ready for payouts yet.'
                        })
        return attrs
    
    def update(self, instance, validated_data: dict):
        new_image = validated_data.pop('image_file', None)
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
            if old_image_url and new_image_url:
                imagekit.files.delete(file_id=old_image_id)
            if new_image_url:
                instance.image, instance.image_id = new_image_url, new_image_id
            with transaction.atomic():
                instance.save()
        except Exception as db_error:
            if new_image_url:
                imagekit.files.delete(file_id=new_image_id)
            raise serializers.ValidationError({'Error': f'Could not create user; {db_error}'})
                
        return instance