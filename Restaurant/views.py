from django.shortcuts import render, HttpResponse

from .forms import BookingForm
from .models import Menu

# Create your views here.
def home(request):
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


def book(request):
    form = BookingForm()
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
    context = {'form': form}
    return render(request, 'book.html', context)


def menu(request):
    menu_items = Menu.objects.all().order_by('name')
    main_data = {'menu': menu_items}
    return render(request, 'menu.html', main_data)


def display_menu_items(request, pk=None):
    if pk:
        menu_item = Menu.objects.get(id=pk)
    else:
        menu_item = ''
    
    return render(request, 'menu_item.html', {"menu_item": menu_item})