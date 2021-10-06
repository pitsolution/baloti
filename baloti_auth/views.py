from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def login(request):
  """Login View

    Args:
        request (Request): Http request object

    Returns:
        html : returns login.html html file
    """
  return render(request, 'login.html')

@login_required
def home(request):
  """Home View

    Args:
        request (Request): Http request object

    Returns:
        html : returns home.html html file
    """
  return render(request, 'home.html')

def baloti_disclaimer(request):
    """Disclaimer View

    Args:
        request (Request): Http request object

    Returns:
        html : returns baloti_disclaimer.html html file
    """
    return render(request, 'baloti/baloti_disclaimer.html',{'name':request.user, 'title':'Disclaimer'})