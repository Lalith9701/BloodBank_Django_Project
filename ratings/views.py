from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from requests_app.models import BloodRequest
from .models import Rating

@login_required
def rate_blood_request(request, request_id):
    blood_request = get_object_or_404(BloodRequest, id=request_id, user=request.user)
    
    if blood_request.status != 'APPROVED':
        messages.error(request, "You can only rate approved requests.")
        return redirect('my_requests')
        
    if hasattr(blood_request, 'rating'):
        messages.warning(request, "You have already rated this request.")
        return redirect('my_requests')
        
    if request.method == 'POST':
        donor_rating = int(request.POST.get('donor_rating', 5))
        service_rating = int(request.POST.get('service_rating', 5))
        feedback = request.POST.get('feedback', '')
        
        Rating.objects.create(
            blood_request=blood_request,
            rater=request.user,
            donor_rating=donor_rating,
            service_rating=service_rating,
            feedback=feedback
        )
        messages.success(request, "Thank you for your feedback!")
        return redirect('my_requests')
        
    return render(request, 'rate_blood_request.html', {'blood_request': blood_request})
