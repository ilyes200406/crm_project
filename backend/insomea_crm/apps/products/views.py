from rest_framework import viewsets
from .models import Product
from .serializers import (
    ProductListSerializer, ProductDetailSerializer,
    ProductCreateSerializer
)

from .selectors import get_products_queryset
from .services import create_product, update_product
from .permessions import ProductPermission
from .filters import ProductFilter

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [ProductPermission]
    filterset_class = ProductFilter
    search_fields = ['sku', 'name']
    ordering_fields = ['name', 'sku', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        return get_products_queryset(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'create':
            return ProductCreateSerializer
        return ProductDetailSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product = create_product(data=serializer.validated_data, user=request.user)
        
        output = ProductDetailSerializer(product)
        return Response(output.data, status=201)