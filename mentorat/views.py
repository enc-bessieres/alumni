from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from membres.droits import reserve_aux_membres_valides

from .forms import PreferencesMentorat
from .models import ProfilMentorat, Sujet


@require_http_methods(["GET", "POST"])
@reserve_aux_membres_valides
def mes_preferences(request):
    """Un membre validé se déclare mentor ou mentoré, ou arrête le mentorat (règle 3)."""
    # Toujours le profil du membre connecté : on ne peut pas modifier celui d'un autre.
    profil = ProfilMentorat.objects.filter(membre=request.user).first()
    donnees = request.POST if request.method == "POST" else None
    formulaire = PreferencesMentorat(donnees, instance=profil)

    if request.method == "POST" and formulaire.is_valid():
        role = formulaire.cleaned_data["role"]
        if role:
            profil = formulaire.save(commit=False)
            profil.membre = request.user
            profil.role = role
            profil.save()
            formulaire.save_m2m()  # les sujets, enregistrés une fois le profil créé
            messages.success(request, "Vos préférences de mentorat sont enregistrées.")
        else:
            if profil:
                profil.delete()
            messages.success(request, "Vous ne participez pas au mentorat.")
        # Après un envoi, on revient sur la page : un rechargement ne renvoie pas le formulaire.
        return redirect("mentorat:mes_preferences")

    contexte = {"formulaire": formulaire, "sujets_existent": Sujet.objects.exists()}
    return render(request, "mentorat/mes_preferences.html", contexte)
