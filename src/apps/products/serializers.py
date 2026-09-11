from rest_framework import serializers
from .models import (
    Category,
    Product,
    ProductVariant
)
from utils.imagekit import imagekit
from apps.accounts.serializers import UserSerializer
from django.db import transaction

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id',
            'product_type'
        ]

class ProductVariantReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'image',
            'expiry_in_months',
            'manufacturing_data',
            'created_at',
            'price',
            'stock_quantity',
            'product_image_id'
        ]

class ProductReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    variants = ProductVariantReadSerializer(many=True, read_only=True)

    class Meta: 
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'brand',
            'category',
            'seller',
            'variants',
            'slug'
        ]

class ProductCreateOrUpdateSerializer(serializers.ModelSerializer):
    seller = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Product
        fields  = [
            'id',
            'name',
            'description',
            'brand',
            'category',
            'seller',
            'slug'
        ]


class ProductVariantCreateSerializer(serializers.ModelSerializer):
    image_file = serializers.ImageField(allow_null=False, required=True, write_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'image_file',
            'product',
            'image',
            'expiry_in_months',
            'manufacturing_date',
            'created_at',
            'price',
            'stock_quantity',
            'product_image_id',
        ]
        read_only_fields = ['id', 'created_at', 'product_image_id', 'image']

    def create(self, validated_data: dict):
        image = validated_data.pop('image_file', None)
        image_id, image_url = None, None
        try:
            if image:
                upload_response = imagekit.files.upload(
                    file=image.read(),
                    folder='/product',
                    file_name=image.name
                )
                image_url = upload_response.url
                image_id = upload_response.file_id
                validated_data['image'] = image_url
                validated_data['product_image_id'] = image_id
        except Exception as image_upload_error:
            raise serializers.ValidationError(f'Could not upload image. Error: {image_upload_error}')
        
        try:
            with transaction.atomic():
                created_variant = ProductVariant.objects.create(**validated_data)
        except Exception as db_error:
            if image_id:
                imagekit.files.delete(image_id)
            raise serializers.ValidationError(f'Failed to create product. Error: {db_error}')
    
        return created_variant

class ProductVariantUpdateSerializer(serializers.ModelSerializer):
    image_file = serializers.ImageField(allow_null=True, required=False, write_only=True)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'product',
            'image_file',
            'image',
            'expiry_in_months',
            'manufacturing_date',
            'created_at',
            'price',
            'stock_quantity',
            'product_image_id'
        ]
        read_only_fields = ['id', 'created_at', 'product_image_id', 'image']

    def update(self, instance, validated_data: dict):
        image = validated_data.pop('image_file', None)
        existing_image_id = getattr(instance, 'product_image_id', None)
        new_image_id, new_image_url = None, None
        if image:
            try:
                imagekit.files.delete(existing_image_id)
                upload_response = imagekit.files.upload(
                    file=image.read(),
                    file_name=image.name,
                    folder='/product'
                )
                new_image_id = upload_response.file_id
                new_image_url = upload_response.url
                instance.image = new_image_url
                instance.product_image_id = new_image_id
            except Exception as image_deletion_error:
                raise serializers.ValidationError(f'failed to delete image: {image_deletion_error}')

        for key, val in validated_data.items():
            setattr(instance, key, val)

        try:
            instance.save()
        except Exception as db_error:
            if new_image_id:
                imagekit.files.delete(new_image_id)
            raise serializers.ValidationError(f'Failed to create product. Error: {db_error}')
        
        return instance
