from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    path('admin/', admin.site.urls),
    
    #inventario admin
    path("inventario-admin/", views.inventario_admin, name="inventario_admin"),
    path("eliminar-producto/<int:id>/", views.eliminar_producto_admin, name="eliminar_producto_admin"),


    # Login y Logout
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),

    # Redirección inteligente después del login
    path('dashboard/', views.redireccion_dashboard, name='dashboard'),

    # Dashboards por rol
    path('dashboard-usuario/', views.dashboard_usuario, name='dashboard_usuario'),
    path('dashboard-vendedor/', views.dashboard_vendedor, name='dashboard_vendedor'),
    path('dashboard-admin/', views.dashboard_admin, name='dashboard_admin'),

    # Administración de usuarios
    path('editar-usuario/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('crear-usuario/', views.crear_usuario, name='crear_usuario'),
    path('registro/', views.registro_publico, name='registro_publico'),

    # Panel vendedor
    path('crear-producto/', views.crear_producto, name='crear_producto'),
    path("editar-producto/<int:producto_id>/", views.editar_producto, name="editar_producto"),
    path('publicar/<int:producto_id>/', views.toggle_publicacion, name='toggle_publicacion'),


    #agregar al carrito
    path("agregar_carrito/<int:producto_id>/", views.agregar_carrito, name="agregar_carrito"),

    #quitar productos del carrito del usuario
    path("carrito/", views.ver_carrito, name="ver_carrito"),
    path("quitar_unidad/<int:producto_id>/", views.quitar_unidad, name="quitar_unidad"),
    path("eliminar_producto/<int:producto_id>/", views.eliminar_producto, name="eliminar_producto"),

    #comprar carrito
    path("comprar/", views.comprar_carrito, name="comprar_carrito"),
    path("factura/", views.factura, name="factura"),
    path("factura/pdf/", views.descargar_factura_pdf, name="descargar_factura_pdf"),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
