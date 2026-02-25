"""
Partner Contact Management Views
عروض إدارة جهات اتصال الشريك
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django import forms

from users.mixins import ApprovedPartnerRequiredMixin
from places.models import Establishment, EstablishmentContact
from places.services.contact_service import ContactService
from ibb_guide.core_utils import get_client_ip


class ContactForm(forms.ModelForm):
    """Form for adding/editing contacts."""
    
    class Meta:
        model = EstablishmentContact
        fields = ['type', 'carrier', 'label', 'value', 'is_primary', 'is_visible']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select', 'id': 'contact-type'}),
            'carrier': forms.Select(attrs={'class': 'form-select', 'id': 'contact-carrier'}),
            'label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: الرقم الرئيسي'
            }),
            'value': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف أو الرابط'
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ContactListView(LoginRequiredMixin, ApprovedPartnerRequiredMixin, View):
    """List and manage contacts for an establishment."""
    template_name = 'partners/contacts/contact_list.html'
    
    def get(self, request, pk):
        establishment = get_object_or_404(
            Establishment, pk=pk, owner=request.user
        )
        contacts = EstablishmentContact.objects.filter(
            establishment=establishment
        ).order_by('display_order')
        
        return render(request, self.template_name, {
            'establishment': establishment,
            'contacts': contacts,
            'contact_types': EstablishmentContact.CONTACT_TYPE_CHOICES,
            'carrier_choices': EstablishmentContact.CARRIER_CHOICES,
        })


class ContactCreateView(LoginRequiredMixin, ApprovedPartnerRequiredMixin, View):
    """Add a new contact to establishment."""
    template_name = 'partners/contacts/contact_form.html'
    
    def get(self, request, pk):
        establishment = get_object_or_404(
            Establishment, pk=pk, owner=request.user
        )
        form = ContactForm()
        
        return render(request, self.template_name, {
            'establishment': establishment,
            'form': form,
            'is_edit': False,
        })
    
    def post(self, request, pk):
        establishment = get_object_or_404(
            Establishment, pk=pk, owner=request.user
        )
        form = ContactForm(request.POST)
        
        if form.is_valid():
            contact, success, message = ContactService.add_contact(
                user=request.user,
                establishment=establishment,
                data=form.cleaned_data,
                ip=get_client_ip(request)
            )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                if success:
                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'contact': {
                            'id': str(contact.id),
                            'type': contact.get_type_display(),
                            'value': contact.value,
                            'label': contact.label,
                            'icon_class': contact.icon_class,
                            'carrier_icon': contact.carrier_icon_class,
                        }
                    })
                else:
                    return JsonResponse({'success': False, 'message': message})

            if success:
                messages.success(request, message)
                return redirect('partner_contact_list', pk=establishment.pk)
            else:
                messages.error(request, message)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
             return JsonResponse({'success': False, 'errors': form.errors}, status=400)

        return render(request, self.template_name, {
            'establishment': establishment,
            'form': form,
            'is_edit': False,
        })


class ContactUpdateView(LoginRequiredMixin, ApprovedPartnerRequiredMixin, View):
    """Edit an existing contact."""
    template_name = 'partners/contacts/contact_form.html'
    
    def get(self, request, pk, contact_id):
        establishment = get_object_or_404(
            Establishment, pk=pk, owner=request.user
        )
        contact = get_object_or_404(
            EstablishmentContact, pk=contact_id, establishment=establishment
        )
        form = ContactForm(instance=contact)
        
        return render(request, self.template_name, {
            'establishment': establishment,
            'form': form,
            'contact': contact,
            'is_edit': True,
        })
    
    def post(self, request, pk, contact_id):
        establishment = get_object_or_404(
            Establishment, pk=pk, owner=request.user
        )
        contact = get_object_or_404(
            EstablishmentContact, pk=contact_id, establishment=establishment
        )
        form = ContactForm(request.POST, instance=contact)
        
        if form.is_valid():
            contact, success, message = ContactService.update_contact(
                user=request.user,
                contact=contact,
                data=form.cleaned_data,
                ip=get_client_ip(request)
            )
            
            if success:
                messages.success(request, message)
                return redirect('partner_contact_list', pk=establishment.pk)
            else:
                messages.error(request, message)
        
        return render(request, self.template_name, {
            'establishment': establishment,
            'form': form,
            'contact': contact,
            'is_edit': True,
        })


class ContactDeleteView(LoginRequiredMixin, ApprovedPartnerRequiredMixin, View):
    """Delete a contact."""
    
    def post(self, request, pk, contact_id):
        establishment = get_object_or_404(
            Establishment, pk=pk, owner=request.user
        )
        contact = get_object_or_404(
            EstablishmentContact, pk=contact_id, establishment=establishment
        )
        
        success, message = ContactService.delete_contact(
            user=request.user,
            contact=contact,
            ip=get_client_ip(request)
        )
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
             return JsonResponse({'success': success, 'message': message})

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect('partner_contact_list', pk=establishment.pk)


class ContactToggleVisibilityView(LoginRequiredMixin, ApprovedPartnerRequiredMixin, View):
    """Toggle contact visibility (AJAX)."""
    
    def post(self, request, pk, contact_id):
        establishment = get_object_or_404(
            Establishment, pk=pk, owner=request.user
        )
        contact = get_object_or_404(
            EstablishmentContact, pk=contact_id, establishment=establishment
        )
        
        is_visible = ContactService.toggle_visibility(
            user=request.user,
            contact=contact,
            ip=get_client_ip(request)
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'is_visible': is_visible})
        
        return redirect('partner_contact_list', pk=establishment.pk)


class ContactReorderView(LoginRequiredMixin, ApprovedPartnerRequiredMixin, View):
    """Reorder contacts (AJAX)."""
    
    def post(self, request, pk):
        import json
        
        establishment = get_object_or_404(
            Establishment, pk=pk, owner=request.user
        )
        
        try:
            data = json.loads(request.body)
            ordered_ids = data.get('order', [])
            
            success, message = ContactService.reorder_contacts(
                user=request.user,
                establishment=establishment,
                ordered_ids=ordered_ids,
                ip=get_client_ip(request)
            )
            
            return JsonResponse({'success': success, 'message': message})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
