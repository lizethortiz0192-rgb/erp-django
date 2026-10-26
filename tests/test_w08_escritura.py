
"""Suite de pruebas W08 — Vistas de escritura: Create, Update, Delete.

Verifica: redirección sin auth, GET con auth, POST válido,
POST inválido y borrado con redirect.

Ejecutar con:
    python manage.py test tests.test_w08_escritura --verbosity=2
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from productos.models import Categoria, Producto
from proveedores.models import Proveedor
from ventas.models import Venta


class ProductoEscrituraTest(TestCase):
    """Pruebas de creación y eliminación de productos."""

    def setUp(self):
        self.user = User.objects.create_user(
            'testuser', password='testpass123'
        )
        self.cat = Categoria.objects.create(nombre='Cat Test')
        self.prod = Producto.objects.create(
            nombre='Laptop',
            precio=Decimal('10000.00'),
            stock=5,
            categoria=self.cat,
        )

    def test_crear_sin_auth_redirige_a_login(self):
        """Sin iniciar sesión, redirige al login."""
        r = self.client.get(reverse('productos:crear'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_editar_sin_auth_redirige_a_login(self):
        """Editar sin iniciar sesión redirige al login."""
        r = self.client.get(
            reverse('productos:editar', args=[self.prod.pk])
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_crear_con_auth_http_200(self):
        """El formulario de creación carga con sesión iniciada."""
        self.client.force_login(self.user)
        r = self.client.get(reverse('productos:crear'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'productos/crear.html')

    def test_post_valido_crea_producto(self):
        """Un POST válido crea el producto y redirige."""
        self.client.force_login(self.user)
        datos = {
            'nombre': 'Monitor 4K',
            'precio': '5500.00',
            'stock': '3',
            'categoria': self.cat.pk,
            'activo': True,
        }
        r = self.client.post(reverse('productos:crear'), datos)

        self.assertRedirects(r, reverse('productos:lista'))
        self.assertTrue(
            Producto.objects.filter(nombre='Monitor 4K').exists()
        )

    def test_post_invalido_muestra_errores(self):
        """Un precio negativo debe producir un error de formulario."""
        self.client.force_login(self.user)
        datos = {
            'nombre': 'Producto mal',
            'precio': '-100.00',
            'stock': '5',
            'categoria': self.cat.pk,
        }
        r = self.client.post(reverse('productos:crear'), datos)

        self.assertEqual(r.status_code, 200)
        self.assertIn('form', r.context)
        self.assertIn('precio', r.context['form'].errors)

    def test_delete_elimina_producto(self):
        """Eliminar un producto lo borra y redirige a la lista."""
        self.client.force_login(self.user)
        pk = self.prod.pk

        r = self.client.post(
            reverse('productos:eliminar', args=[pk])
        )

        self.assertRedirects(r, reverse('productos:lista'))
        self.assertFalse(Producto.objects.filter(pk=pk).exists())


class ClienteEscrituraTest(TestCase):
    """Pruebas de creación de clientes."""

    def setUp(self):
        self.user = User.objects.create_user(
            'userC', password='pass'
        )

    def test_crear_cliente_sin_auth_redirige(self):
        """Crear un cliente sin sesión redirige al login."""
        r = self.client.get(reverse('clientes:crear'))
        self.assertEqual(r.status_code, 302)

    def test_post_valido_crea_cliente(self):
        """Un POST válido crea el cliente y redirige."""
        self.client.force_login(self.user)
        r = self.client.post(reverse('clientes:crear'), {
            'nombre': 'María López',
            'correo': 'maria@test.com',
            'activo': True,
        })

        self.assertRedirects(r, reverse('clientes:lista'))
        self.assertTrue(
            Cliente.objects.filter(correo='maria@test.com').exists()
        )

    def test_post_correo_duplicado_muestra_error(self):
        """Un correo duplicado muestra un error en el formulario."""
        Cliente.objects.create(
            nombre='Ana',
            correo='dup@test.com',
        )
        self.client.force_login(self.user)

        r = self.client.post(reverse('clientes:crear'), {
            'nombre': 'Otro',
            'correo': 'dup@test.com',
            'activo': True,
        })

        self.assertEqual(r.status_code, 200)
        self.assertIn('form', r.context)
        self.assertIn('correo', r.context['form'].errors)
        self.assertTrue(
            any(
                'ya existe' in error.lower()
                for error in r.context['form'].errors['correo']
            ),
            'El formulario debe indicar que el correo ya existe.',
        )


class ProveedorEscrituraTest(TestCase):
    """Pruebas de creación y eliminación de proveedores."""

    def setUp(self):
        self.user = User.objects.create_user(
            'userP', password='pass'
        )
        self.prov = Proveedor.objects.create(
            nombre='Prov Test',
            correo='prov@test.com',
        )

    def test_crear_proveedor_sin_auth_redirige(self):
        """Crear proveedor sin sesión redirige al login."""
        r = self.client.get(reverse('proveedores:crear'))
        self.assertEqual(r.status_code, 302)

    def test_delete_proveedor_con_auth(self):
        """Eliminar proveedor borra el registro y redirige."""
        self.client.force_login(self.user)
        pk = self.prov.pk

        r = self.client.post(
            reverse('proveedores:eliminar', args=[pk])
        )

        self.assertRedirects(r, reverse('proveedores:lista'))
        self.assertFalse(
            Proveedor.objects.filter(pk=pk).exists()
        )


class VentaEscrituraTest(TestCase):
    """Pruebas de creación de ventas."""

    def setUp(self):
        self.user = User.objects.create_user(
            'userV', password='pass'
        )
        cat = Categoria.objects.create(nombre='Cat')
        self.prod = Producto.objects.create(
            nombre='P',
            precio=Decimal('100.00'),
            stock=5,
            categoria=cat,
        )
        self.cli = Cliente.objects.create(
            nombre='C',
            correo='c@t.com',
        )

    def test_crear_venta_sin_auth_redirige(self):
        """Crear una venta sin sesión redirige al login."""
        r = self.client.get(reverse('ventas:crear'))
        self.assertEqual(r.status_code, 302)

    def test_post_valido_crea_venta(self):
        """Un POST válido crea la venta y redirige al detalle."""
        self.client.force_login(self.user)

        r = self.client.post(reverse('ventas:crear'), {
            'cliente': self.cli.pk,
            'producto': self.prod.pk,
            'cantidad': 2,
            'precio_unitario': '100.00',
        })

        self.assertEqual(r.status_code, 302)
        self.assertEqual(Venta.objects.count(), 1)

        venta = Venta.objects.first()
        self.assertEqual(venta.total, Decimal('200.00'))
