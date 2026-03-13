from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User


# Modelo de perfil para extender el modelo de usuario
class Perfil(models.Model):

    ROLES = (
        ('Usuario', 'Usuario'),
        ('Vendedor', 'Vendedor'),
        ('Administrador', 'Administrador'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil"
    )

    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='Usuario'
    )

    def __str__(self):
        return f"{self.user.username} - {self.rol}"

#vendedor 

class Producto(models.Model):
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE)

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    cantidad = models.PositiveIntegerField(default=1)
    dias_garantia = models.PositiveIntegerField(default=0)

    imagen = models.ImageField(upload_to="productos/", null=True, blank=True)

    publicado = models.BooleanField(default=False)

    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre
