import json
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView, CreateView
from rest_framework.generics import ListAPIView, RetrieveAPIView, DestroyAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from ads.models import Ad, Category
from ads.permissions import IsCreatedByOrAdminOrModerator
from ads.serializers import AdSerializer, AdUpdateSerializer
from users.models import User


class AdListView(ListAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer

    def get(self, request, *args, **kwargs):

        categories = request.GET.getlist('cat', None)
        cat_query = None

        for cat_id in categories:
            if cat_query is None:
                cat_query = Q(category__id__exact=cat_id)
            else:
                cat_query |= Q(category__id__exact=cat_id)

        if cat_query:
            self.queryset = self.queryset.filter(cat_query)

        ad_name = request.GET.get('text', None)
        if ad_name:
            self.queryset = self.queryset.filter(
                name__icontains=ad_name
            )

        user_location = request.GET.get('location', None)
        if user_location:
            self.queryset = self.queryset.filter(
                author__location__name__icontains=user_location
            )

        price_from = request.GET.get('price_from', None)
        price_to = request.GET.get('price_to', None)
        if price_from:
            self.queryset = self.queryset.filter(
                price__gte=price_from
            )
        if price_to:
            self.queryset = self.queryset.filter(
                price__lte=price_to
            )

        return super().get(request, *args, **kwargs)


class AdDetailView(RetrieveAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
    permission_classes = [IsAuthenticated]


@method_decorator(csrf_exempt, name='dispatch')
class AdCreateView(CreateView):
    model = Ad
    fields = ['name', 'author', 'price', 'description', 'is_published', 'image', 'category']

    def post(self, request, *args, **kwargs):
        ad_data = json.loads(request.body)
        ad = Ad.objects.create(
            name=ad_data.get('name'),
            price=ad_data.get('price'),
            description=ad_data.get('description'),
            is_published=ad_data.get('is_published')
        )

        ad.author = get_object_or_404(User, pk=ad_data.get('author_id'))
        ad.category = get_object_or_404(Category, pk=ad_data.get('category_id'))
        ad.save()

        response = {
            'id': ad.id,
            'author_id': ad.author_id,
            'author': str(ad.author),
            'name': ad.name,
            'price': ad.price,
            'description': ad.description,
            'is_published': ad.is_published,
            'image': ad.image.url if ad.image else None,
            'category_id': ad.category_id,
            'category': str(ad.category)
        }

        return JsonResponse(response,
                            json_dumps_params={"ensure_ascii": False})


class AdUpdateView(UpdateAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdUpdateSerializer
    permission_classes = [IsAuthenticated, IsCreatedByOrAdminOrModerator]


@method_decorator(csrf_exempt, name="dispatch")
class AdImageView(UpdateView):
    model = Ad
    fields = ["name", "image"]

    def post(self, request, *args, **kwargs):

        ad = self.get_object()
        ad.image = request.FILES["image"]
        ad.save()

        response = {
            "id": ad.id,
            "author_id": ad.author_id,
            "author": str(ad.author),
            "name": ad.name,
            "price": ad.price,
            "description": ad.description,
            "is_published": ad.is_published,
            "image": ad.image.url if ad.image else None,
            "category_id": ad.category_id,
            "category": str(ad.category),
        }

        return JsonResponse(response, json_dumps_params={"ensure_ascii": False})


class AdDeleteView(DestroyAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
    permission_classes = [IsAuthenticated, IsCreatedByOrAdminOrModerator]
