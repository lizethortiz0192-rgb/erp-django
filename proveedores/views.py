
"""Vistas de la aplicación proveedores — W07 y W08."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import ProveedorForm
from .models import Proveedor


def inicio(request):
    """Vista de inicio compatible con las pruebas de W02."""
    return render(request, 'proveedores/index.html')


class ProveedorListView(ListView):
    """Lista paginada de proveedores activos."""

    model = Proveedor
    template_name = 'proveedores/lista.html'
    context_object_name = 'proveedores'
    paginate_by = 20

    def get_queryset(self):
        return Proveedor.objects.filter(activo=True).order_by('nombre')


class ProveedorDetailView(DetailView):
    """Muestra un proveedor y sus productos asociados."""

    model = Proveedor
    template_name = 'proveedores/detalle.html'
    context_object_name = 'proveedor'
    pk_url_kwarg = 'proveedor_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['productos'] = (
            self.object.productos
            .select_related('categoria')
            .filter(activo=True)
            .order_by('nombre')
        )
        return context


class ProveedorCreateView(LoginRequiredMixin, CreateView):
    """Crea un proveedor nuevo."""

    model = Proveedor
    form_class = ProveedorForm
    template_name = 'proveedores/crear.html'
    success_url = reverse_lazy('proveedores:lista')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Proveedor "{self.object.nombre}" creado exitosamente.'
        )
        return response


class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
    """Actualiza un proveedor existente."""

    model = Proveedor
    form_class = ProveedorForm
    template_name = 'proveedores/editar.html'
    pk_url_kwarg = 'proveedor_id'
    success_url = reverse_lazy('proveedores:lista')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Proveedor "{self.object.nombre}" actualizado.'
        )
        return response


class ProveedorDeleteView(LoginRequiredMixin, DeleteView):
    """Elimina un proveedor."""

    model = Proveedor
    template_name = 'proveedores/eliminar.html'
    pk_url_kwarg = 'proveedor_id'
    success_url = reverse_lazy('proveedores:lista')

    def form_valid(self, form):
        nombre = self.object.nombre
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Proveedor "{nombre}" eliminado.'
        )
        return response
