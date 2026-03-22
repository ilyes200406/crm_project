"""
VALIDATORS - APP SUPPLIERS

Validation :
- Nom fournisseur (unicité, format)
- URL site web
- Email/téléphone support
- Type fournisseur
"""

import re
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator as DjangoURLValidator
from django.utils.translation import gettext_lazy as _


# ═══════════════════════════════════════════════════════════
# NAME VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_supplier_name(value):
    """
    Valide nom fournisseur
    
    Règles :
    - Minimum 2 caractères
    - Pas que des espaces
    - Caractères valides : lettres, chiffres, espaces, tirets
    """
    if not value or len(value.strip()) < 2:
        raise ValidationError(
            _('Le nom du fournisseur doit contenir au moins 2 caractères'),
            code='name_too_short'
        )
    
    # Pattern : lettres, chiffres, espaces, tirets, points
    pattern = r'^[a-zA-Z0-9\s\-\.&]+$'
    
    if not re.match(pattern, value):
        raise ValidationError(
            _('Le nom contient des caractères non autorisés'),
            code='invalid_characters'
        )


def validate_supplier_unique_name(name, exclude_id=None):
    """
    Valide unicité du nom
    
    Args:
        name: Nom à vérifier
        exclude_id: ID fournisseur à exclure (pour update)
    """
    from .models import Supplier
    
    # Normalise nom (case-insensitive)
    name_normalized = name.strip().lower()
    
    query = Supplier.objects.filter(name__iexact=name_normalized)
    
    if exclude_id:
        query = query.exclude(id=exclude_id)
    
    if query.exists():
        raise ValidationError(
            _('Un fournisseur avec ce nom existe déjà'),
            code='duplicate_name'
        )


# ═══════════════════════════════════════════════════════════
# CONTACT VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_support_email(value):
    """
    Valide email support
    
    Règles :
    - Format email valide
    - Pas d'emails personnels (optionnel)
    """
    if not value:
        return
    
    from django.core.validators import validate_email
    
    try:
        validate_email(value)
    except ValidationError:
        raise ValidationError(
            _('Email support invalide'),
            code='invalid_email'
        )


def validate_support_phone(value):
    """
    Valide téléphone support
    
    Format accepté :
    - International : +XXX XX XX XX XX
    - Local : XX XX XX XX
    """
    if not value:
        return
    
    # Nettoie espaces/tirets
    cleaned = re.sub(r'[\s\-\(\)]', '', value)
    
    # Pattern flexible téléphone
    pattern = r'^(\+?[0-9]{8,15})$'
    
    if not re.match(pattern, cleaned):
        raise ValidationError(
            _('Numéro de téléphone invalide'),
            code='invalid_phone'
        )


def validate_website_url(value):
    """
    Valide URL site web
    
    Règles :
    - Format URL valide
    - Protocole http/https
    """
    if not value:
        return
    
    validator = DjangoURLValidator(schemes=['http', 'https'])
    
    try:
        validator(value)
    except ValidationError:
        raise ValidationError(
            _('URL invalide. Format attendu : https://example.com'),
            code='invalid_url'
        )


# ═══════════════════════════════════════════════════════════
# TYPE VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_supplier_type(value):
    """
    Valide type fournisseur
    
    Vérifie que le type est dans les choix autorisés
    """
    from .models import SupplierType
    
    valid_types = [choice[0] for choice in SupplierType.choices]
    
    if value not in valid_types:
        raise ValidationError(
            _(f'Type invalide. Valeurs autorisées : {", ".join(valid_types)}'),
            code='invalid_type'
        )


# ═══════════════════════════════════════════════════════════
# COMPOSITE VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_supplier_data(data, supplier=None):
    """
    Validation composite de toutes les données fournisseur
    
    Args:
        data: Données fournisseur (dict)
        supplier: Instance Supplier existante (pour update)
    
    Returns:
        dict: Données validées
    
    Raises:
        ValidationError: Si données invalides
    """
    errors = {}
    
    # Valide nom
    if 'name' in data:
        try:
            validate_supplier_name(data['name'])
        except ValidationError as e:
            errors['name'] = e.messages
        
        # Valide unicité
        try:
            exclude_id = supplier.id if supplier else None
            validate_supplier_unique_name(data['name'], exclude_id)
        except ValidationError as e:
            errors['name'] = e.messages
    
    # Valide type
    if 'type' in data:
        try:
            validate_supplier_type(data['type'])
        except ValidationError as e:
            errors['type'] = e.messages
    
    # Valide email
    if 'support_email' in data and data['support_email']:
        try:
            validate_support_email(data['support_email'])
        except ValidationError as e:
            errors['support_email'] = e.messages
    
    # Valide téléphone
    if 'support_phone' in data and data['support_phone']:
        try:
            validate_support_phone(data['support_phone'])
        except ValidationError as e:
            errors['support_phone'] = e.messages
    
    # Valide website
    if 'website' in data and data['website']:
        try:
            validate_website_url(data['website'])
        except ValidationError as e:
            errors['website'] = e.messages
    
    if errors:
        raise ValidationError(errors)
    
    return data


# ═══════════════════════════════════════════════════════════
# NORMALIZER HELPERS
# ═══════════════════════════════════════════════════════════

def normalize_supplier_name(name):
    """
    Normalise nom fournisseur
    
    - Trim espaces
    - Capitalise première lettre de chaque mot
    
    Input : "  microsoft corporation  "
    Output : "Microsoft Corporation"
    """
    if not name:
        return name
    
    # Trim + title case
    return ' '.join(word.capitalize() for word in name.strip().split())


def normalize_phone_number(phone):
    """
    Normalise téléphone
    
    Input : "+216 12 345 678"
    Output : "+21612345678"
    """
    if not phone:
        return phone
    
    # Retire espaces/tirets
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Ajoute + si manquant et commence par chiffre
    if cleaned and cleaned[0].isdigit() and not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    return cleaned


def normalize_url(url):
    """
    Normalise URL
    
    - Ajoute https:// si manquant
    - Lowercase domain
    
    Input : "Microsoft.com"
    Output : "https://microsoft.com"
    """
    if not url:
        return url
    
    url = url.strip().lower()
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url