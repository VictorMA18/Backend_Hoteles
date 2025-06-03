from django.urls import path
from .views import (
    home, 
    # --- AUTENTICACIÓN --------------------
    login_view,
    # --- HUÉSPEDES ------------------------
    HuespedListCreateView, HuespedDetailView,
    huesped_search, huesped_history,
    # --- HABITACIONES ---------------------
    HabitacionListView, habitacion_update_status, habitaciones_disponibles,
    # --- RESERVAS -------------------------
    ReservaListCreateView, ReservaDetailView, confirmar_reserva,
    # --- CHECK-IN/OUT & DESCUENTOS --------
    checkin_huesped, checkout_huesped, get_discount_for_guest,
    # --- DASHBOARD ------------------------
    dashboard_realtime, current_guests,
    # --- REPORTES -------------------------
    reporte_ocupacion_mensual, reporte_ingresos,
)

urlpatterns = [
    path('', home, name='home'),
    # ------------------- AUT -------------------
    path('auth/login/',                    login_view,             name='login'),
    # ------------------- HUÉSPEDES -------------
    path('huespedes/',                     HuespedListCreateView.as_view(),   name='huesped-list'),
    path('huespedes/<str:dni>/',           HuespedDetailView.as_view(),       name='huesped-detail'),
    path('huespedes/search/',              huesped_search,                    name='huesped-search'),
    path('huespedes/<str:dni>/historial/', huesped_history,                   name='huesped-hist'),
    path('huespedes/<str:dni>/descuento/', get_discount_for_guest,            name='huesped-descuento'),
    # ------------------- HABITACIONES ----------
    path('habitaciones/',                  HabitacionListView.as_view(),      name='habitacion-list'),
    path('habitaciones/disponibles/',      habitaciones_disponibles,          name='hab-disponibles'),
    path('habitaciones/<str:codigo>/estado/', habitacion_update_status,       name='hab-update'),
    # ------------------- RESERVAS --------------
    path('reservas/',                      ReservaListCreateView.as_view(),   name='reserva-list'),
    path('reservas/<int:codigo>/',         ReservaDetailView.as_view(),       name='reserva-detail'),
    path('reservas/<int:codigo>/confirmar/', confirmar_reserva,               name='reserva-confirmar'),
    # ------------------- CHECK-IN/OUT ----------
    path('estancias/checkin/',             checkin_huesped,                   name='checkin'),
    path('estancias/checkout/',            checkout_huesped,                  name='checkout'),
    # ------------------- DASHBOARD -------------
    path('dashboard/',                     dashboard_realtime,                name='dashboard'),
    path('dashboard/huespedes/',           current_guests,                    name='dashboard-huespedes'),
    # ------------------- REPORTES --------------
    path('reportes/ocupacion/',            reporte_ocupacion_mensual,         name='rep-ocupacion'),
    path('reportes/ingresos/',             reporte_ingresos,                  name='rep-ingresos'),
]

