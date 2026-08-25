from rest_framework import serializers
from .models import (
    Category,
    Product,
    ProductVariant
)
from utils.imagekit import imagekit
from accounts.serializers import UserSerializer
from django.db import transaction

class CategorySerializer(serializers.ModelSerializer):
    class Mwta:
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
            'variants'
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
            'seller'
        ]

    def create(self, validated_data):
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class ProductVariantCreateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=False, required=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'product',
            'image',
            'expiry_in_months',
            'manufacturing_data',
            'created_at',
            'price',
            'stock_quantity',
            'product_image_id'
        ]
        read_only_fields = ['id', 'created_at', 'product_image_id']

    def create(self, validated_data: dict):
        image = validated_data.pop('image', None)
        image_id, image_url = None, None
        try:
            if image:
                upload_response = imagekit.files.upload(
                    file=image,
                    folder='/product',
                    file_name=image.name
                )
                image_url = upload_response.url
                image_id = upload_response.file_id
                validated_data['image_url'] = image_url
                validated_data['image_id'] = image_id
        except Exception as image_upload_error:
            raise serializers.ValidationError(f'Could not upload image. Error: {image_upload_error}')
        
        try:
            with transaction.atomic():
                created_variant = ProductVariant.objects.create(**validated_data)
        except Exception as db_error:
            if image:
                imagekit.files.delete(image_id)
            raise serializers.ValidationError(f'Failed to create product. Error: {db_error}')
    
        return created_variant
        

class ProductVariantUpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=True, required=False)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'product',
            'image',
            'expiry_in_months',
            'manufacturing_data',
            'created_at',
            'price',
            'stock_quantity',
            'product_image_id'
        ]
        read_only_fields = ['id', 'created_at', 'product_image_id']

    def update(self, instance, validated_data: dict):
        image = validated_data.pop('image', None)
        existing_image_id = getattr(instance, 'product_image_id', None)
        new_image_id, new_image_url = None, None
        if image:
            try:
                imagekit.files.delete(existing_image_id)
                upload_response = imagekit.files.upload(
                    file=image,
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
