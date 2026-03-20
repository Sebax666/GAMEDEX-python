# Módulo principal de vistas para GAMEDEX (usuarios, carrito, productos, facturación)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from .models import Perfil, Producto
from django.shortcuts import redirect, get_object_or_404
from .models import Producto
from django.http import HttpResponse
from reportlab.pdfgen import canvas


# =====================================
# REGISTRO ADMIN (usa UserCreationForm)
# =====================================
def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            grupo, _ = Group.objects.get_or_create(name='Usuario')
            user.groups.add(grupo)

            messages.success(request, "Usuario registrado correctamente.")
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'registro.html', {'form': form})


# =====================================
# DASHBOARDS
# =====================================

@login_required
@never_cache
def dashboard_usuario(request):

     # productos publicados por vendedores
    productos = Producto.objects.filter(publicado=True)

    # contador carrito usando session
    total_carrito = 0

    carrito = request.session.get("carrito")

    if carrito:
        total_carrito = sum(carrito.values())


    return render(request, "dashboard_usuario.html", {
        "productos": productos,
        "total_carrito": total_carrito
    })

    #===================================== 
    # Agregar al carrito (POST)
    #===================================== 

def agregar_carrito(request, producto_id):

    producto = get_object_or_404(Producto, id=producto_id)

    cantidad = int(request.POST.get("cantidad", 1))

    carrito = request.session.get("carrito", {})

    cantidad_actual = carrito.get(str(producto_id), 0)

    if cantidad_actual + cantidad > producto.cantidad:
        messages.error(request, "No hay suficiente cantidad disponible.")
        return redirect("dashboard_usuario")

    if str(producto_id) in carrito:
        carrito[str(producto_id)] += cantidad
    else:
        carrito[str(producto_id)] = cantidad

    request.session["carrito"] = carrito

    messages.success(request, "Producto agregado al carrito.")

    return redirect("dashboard_usuario")

#=====================================  
#   vista carrito 
#=====================================

def ver_carrito(request):

    carrito = request.session.get("carrito", {})

    productos_carrito = []
    total = 0

    for producto_id, cantidad in carrito.items():

        producto = get_object_or_404(Producto, id=producto_id)

        subtotal = producto.precio * cantidad
        total += subtotal

        productos_carrito.append({
            "producto": producto,
            "cantidad": cantidad,
            "subtotal": subtotal
        })

    return render(request, "carrito.html", {
        "productos_carrito": productos_carrito,
        "total": total
    })

#=====================================  
#quitar productos del carrito del usuario
#=====================================

def quitar_unidad(request, producto_id):

    carrito = request.session.get("carrito", {})

    if str(producto_id) in carrito:

        carrito[str(producto_id)] -= 1

        if carrito[str(producto_id)] <= 0:
            del carrito[str(producto_id)]

    request.session["carrito"] = carrito

    return redirect("ver_carrito")


def eliminar_producto(request, producto_id):

    carrito = request.session.get("carrito", {})

    if str(producto_id) in carrito:
        del carrito[str(producto_id)]

    request.session["carrito"] = carrito

    return redirect("ver_carrito")


#=====================================
#boton comprar 
#=====================================

def comprar_carrito(request):

    carrito = request.session.get("carrito", {})

    if not carrito:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("ver_carrito")

    for producto_id, cantidad in carrito.items():

        producto = get_object_or_404(Producto, id=producto_id)

        if cantidad > producto.cantidad:
            messages.error(request, f"No hay suficiente stock de {producto.nombre}")
            return redirect("ver_carrito")

        # descontar stock
        producto.cantidad -= cantidad
        producto.save()

    # vaciar carrito
    request.session["carrito"] = {}

    messages.success(request, "Compra realizada con éxito.")

    return redirect("dashboard_usuario")


#=====================================
#facturacion 
#=====================================



def factura(request):

    carrito = request.session.get("carrito", {})

    if not carrito:
        messages.error(request, "No hay productos para generar factura.")
        return redirect("dashboard_usuario")

    productos_factura = []
    total = 0

    for producto_id, cantidad in carrito.items():

        producto = get_object_or_404(Producto, id=producto_id)

        subtotal = producto.precio * cantidad
        total += subtotal

        productos_factura.append({
            "producto": producto,
            "cantidad": cantidad,
            "subtotal": subtotal
        })

    context = {
        "productos": productos_factura,
        "total": total,
        "usuario": request.user
    }

    return render(request, "factura.html", context)



def descargar_factura_pdf(request):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="factura.pdf"'

    p = canvas.Canvas(response)

    p.drawString(100, 800, "Factura de compra")
    p.drawString(100, 780, f"Cliente: {request.user.username}")

    y = 740

    carrito = request.session.get("carrito", {})
    total = 0

    for producto_id, cantidad in carrito.items():

        producto = Producto.objects.get(id=producto_id)
        subtotal = producto.precio * cantidad
        total += subtotal

        p.drawString(100, y, f"{producto.nombre} - Cantidad: {cantidad} - ${subtotal}")
        y -= 20

    p.drawString(100, y-20, f"Total: ${total}")

    p.showPage()
    p.save()

    return response




#=====================================
#dashboard admin
#=====================================

@login_required
@never_cache
def dashboard_admin(request):

    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "No tienes permisos para acceder.")
        return redirect("redireccion_dashboard")

    query = request.GET.get("q")

    usuarios_list = User.objects.prefetch_related("groups").all()

    if query:
        usuarios_list = usuarios_list.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )

    paginator = Paginator(usuarios_list.order_by("username"), 5)
    page_number = request.GET.get("page")
    usuarios = paginator.get_page(page_number)

    total_usuarios = User.objects.filter(groups__name="Usuario").count()
    total_vendedores = User.objects.filter(groups__name="Vendedor").count()
    total_admins = User.objects.filter(groups__name="Administrador").count()

    return render(request, "dashboard_admin.html", {
        "usuarios": usuarios,
        "total_usuarios": total_usuarios,
        "total_vendedores": total_vendedores,
        "total_admins": total_admins,
        "query": query
    })

#===================================== 
#inventario admin
#===================================== 

def inventario_admin(request):

    productos = Producto.objects.all()

    return render(request, "inventario_admin.html", {
        "productos": productos
    })

def eliminar_producto_admin(request, id):

    producto = get_object_or_404(Producto, id=id)
    producto.delete()

    return redirect("inventario_admin")

#===================================== 
# dashboard vendedor
#===================================== 

@login_required
@never_cache
def dashboard_vendedor(request):

    if not request.user.groups.filter(name="Vendedor").exists():
        messages.error(request, "No tienes permiso para acceder.")
        return redirect("redireccion_dashboard")

    # TODOS los productos del vendedor
    productos_vendedor = Producto.objects.filter(vendedor=request.user)

    # 📊 Estadísticas
    total_productos = productos_vendedor.count()

    total_publicados = productos_vendedor.filter(publicado=True).count()

    total_borradores = productos_vendedor.filter(publicado=False).count()

    productos_activos = productos_vendedor.filter(
        publicado=True,
        cantidad__gt=0
    ).count()

    # 🔎 Buscador
    productos_list = productos_vendedor

    query = request.GET.get("q")
    if query:
        productos_list = productos_list.filter(nombre__icontains=query)

    # 📄 Paginación
    paginator = Paginator(productos_list, 5)
    page_number = request.GET.get("page")
    productos = paginator.get_page(page_number)

    return render(request, "dashboard_vendedor.html", {
        "productos": productos,
        "total_productos": total_productos,
        "total_publicados": total_publicados,
        "total_borradores": total_borradores,
        "productos_activos": productos_activos,
        "query": query,
    })


# =====================================
# REDIRECCIÓN SEGÚN ROL
# =====================================

@login_required
@never_cache
def redireccion_dashboard(request):

    user = request.user

    if user.groups.filter(name="Administrador").exists():
        return redirect("dashboard_admin")
    elif user.groups.filter(name="Vendedor").exists():
        return redirect("dashboard_vendedor")
    elif user.groups.filter(name="Usuario").exists():
        return redirect("dashboard_usuario")
    else:
        messages.error(request, "No tienes un rol asignado.")
        return redirect("login")


# =====================================
# CRUD USUARIOS (ADMIN)
# =====================================

@login_required
def crear_usuario(request):

    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "No tienes permisos.")
        return redirect("redireccion_dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        rol = request.POST.get("rol")

        if not username or not password or not rol:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect("crear_usuario")

        if User.objects.filter(username=username).exists():
            messages.error(request, "El usuario ya existe.")
            return redirect("crear_usuario")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        grupo, _ = Group.objects.get_or_create(name=rol)
        user.groups.add(grupo)

        messages.success(request, "Usuario creado correctamente.")
        return redirect("dashboard_admin")

    grupos = Group.objects.all()
    return render(request, "crear_usuario.html", {"grupos": grupos})


@login_required
def editar_usuario(request, user_id):

    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "No tienes permisos.")
        return redirect("redireccion_dashboard")

    usuario = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        rol = request.POST.get("rol")
        nueva_password = request.POST.get("password")

        if not username or not rol:
            messages.error(request, "Usuario y rol son obligatorios.")
            return redirect("editar_usuario", user_id=user_id)

        if usuario == request.user and rol != "Administrador":
            messages.error(request, "No puedes quitarte tu rol.")
            return redirect("dashboard_admin")

        usuario.username = username
        usuario.email = email

        if nueva_password:
            usuario.set_password(nueva_password)

        usuario.save()

        usuario.groups.clear()
        grupo, _ = Group.objects.get_or_create(name=rol)
        usuario.groups.add(grupo)

        messages.success(request, "Usuario actualizado correctamente.")
        return redirect("dashboard_admin")

    grupos = Group.objects.all()
    return render(request, "editar_usuario.html", {
        "usuario": usuario,
        "grupos": grupos
    })


# =====================================
# PRODUCTOS (VENDEDOR)
# ===================================== 


@login_required
def crear_producto(request):

    perfil = Perfil.objects.get(user=request.user)

    if perfil.rol.strip().lower() != "vendedor":
        return redirect("dashboard")

    if request.method == "POST":
        Producto.objects.create(
            vendedor=request.user,
            nombre=request.POST.get("nombre"),
            descripcion=request.POST.get("descripcion"),
            precio=request.POST.get("precio"),
            cantidad=request.POST.get("cantidad"),
            dias_garantia=request.POST.get("dias_garantia"),
            imagen=request.FILES.get("imagen")
        )

        messages.success(request, "Producto creado correctamente.")
        return redirect("dashboard_vendedor")

    return render(request, "crear_producto.html")


@login_required
def editar_producto(request, producto_id):

    perfil = getattr(request.user, "perfil", None)

    if not perfil or perfil.rol != "Vendedor":
        return redirect("login")

    producto = get_object_or_404(Producto, id=producto_id, vendedor=request.user)

    if request.method == "POST":
        producto.nombre = request.POST.get("nombre")
        producto.descripcion = request.POST.get("descripcion")
        producto.precio = request.POST.get("precio")
        producto.cantidad = request.POST.get("cantidad")
        producto.dias_garantia = request.POST.get("dias_garantia")

        if request.FILES.get("imagen"):
            producto.imagen = request.FILES.get("imagen")

        producto.save()

        messages.success(request, "Producto actualizado correctamente.")
        return redirect("dashboard_vendedor")

    return render(request, "editar_producto.html", {"producto": producto})

@login_required
def toggle_publicacion(request, producto_id):

    perfil = getattr(request.user, "perfil", None)

    if not perfil or perfil.rol != "Vendedor":
        return redirect("dashboard_vendedor")

    producto = get_object_or_404(
        Producto,
        id=producto_id,
        vendedor=request.user
    )

    producto.publicado = not producto.publicado
    producto.save()

    messages.success(request, "Estado actualizado.")
    return redirect("dashboard_vendedor")

# =====================================
# CERRAR SESIÓN
# =====================================

@login_required
def cerrar_sesion(request):
    logout(request)
    return redirect("login")


# =====================================
# REGISTRO PÚBLICO
# =====================================
def registro_publico(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        rol = request.POST.get("rol")

        if User.objects.filter(username=username).exists():
            messages.error(request, "El usuario ya existe")
            return redirect("registro_publico")

        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Obtener el perfil que Django creó automáticamente
        perfil = user.perfil
        perfil.rol = rol
        perfil.save()

        # Agregar al grupo
        grupo, created = Group.objects.get_or_create(name=rol)
        user.groups.add(grupo)

        messages.success(request, "Cuenta creada correctamente")
        return redirect("login")

    return render(request, "registro_publico.html")
