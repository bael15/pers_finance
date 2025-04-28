from rest_framework import viewsets, permissions
from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
import csv
from django.http import HttpResponse
from reportlab.pdfgen import canvas

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        queryset = self.queryset.filter(owner=self.request.user)
        # Фильтрация
        category = self.request.query_params.get('category')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')

        if category:
            queryset = queryset.filter(category__name=category)
        if date_from and date_to:
            queryset = queryset.filter(date__range=[date_from, date_to])
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)
        return queryset

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        transactions = self.get_queryset()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

        writer = csv.writer(response)
        writer.writerow(['Type', 'Category', 'Amount', 'Date', 'Description'])

        for t in transactions:
            writer.writerow([t.type, t.category.name, t.amount, t.date, t.description])

        return response

    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        transactions = self.get_queryset()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="transactions.pdf"'

        p = canvas.Canvas(response)
        y = 800
        for t in transactions:
            p.drawString(100, y, f"{t.type} | {t.category.name} | {t.amount} | {t.date} | {t.description}")
            y -= 20
        p.showPage()
        p.save()

        return response
