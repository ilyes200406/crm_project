"""
EXPLICATION :

Validators réutilisables pour validation métier

Architecture :
- Validation indépendante de Django (pure Python)
- Réutilisable dans serializers, models, services
- Messages d'erreur clairs et en français
- Validation stricte (fail fast)

Avantages :
- DRY (Don't Repeat Yourself)
- Testable isolément
- Réutilisable partout
- Séparation des responsabilités
"""

import re
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator as DjangoURLValidator
from django.utils.translation import gettext_lazy as _


# ═══════════════════════════════════════════════════════════
# PHONE NUMBER VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_phone_number(value):
    """
    Valide un numéro de téléphone tunisien
    
    Formats acceptés :
    - +216 12 345 678 (international)
    - 00216 12 345 678 (international)
    - 12 345 678 (local)
    - 12345678 (sans espaces)
    - 12-345-678 (avec tirets)
    
    Règles :
    - Doit commencer par +216, 00216, ou chiffres locaux
    - 8 chiffres pour numéros locaux (après indicatif)
    - Accepte espaces, tirets, parenthèses comme séparateurs
    
    Explication regex :
    ^\+?216?[- ]? : Optionnel +216 ou 00216
    (\d{2}[- ]?){3}\d{2}$ : 8 chiffres au format XX XX XX XX
    """
    if not value:
        return
    
    # Nettoie les espaces/tirets pour validation
    cleaned = re.sub(r'[\s\-\(\)]', '', value)
    
    # Pattern pour téléphone tunisien
    # Accepte : +216XXXXXXXX, 00216XXXXXXXX, ou XXXXXXXX (8 chiffres)
    pattern = r'^(\+?216|00216)?[2-9]\d{7}$'
    # Explication :
    # (\+?216|00216)? : Indicatif optionnel
    # [2-9] : Premier chiffre (pas 0 ou 1)
    # \d{7} : 7 chiffres suivants (total 8)
    
    if not re.match(pattern, cleaned):
        raise ValidationError(
            _('Numéro de téléphone invalide. Format attendu : +216 12 345 678 ou 12 345 678'),
            code='invalid_phone'
        )


# ═══════════════════════════════════════════════════════════
# EMAIL VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_business_email(value):
    """
    Valide un email professionnel (pas de domaines publics)
    
    Explication :
    Rejette emails avec domaines grand public
    Force utilisation email entreprise
    
    Domaines rejetés :
    - gmail.com, yahoo.com, hotmail.com
    - outlook.com, live.com
    - etc.
    
    Use case :
    Client professionnel doit avoir email @entreprise.com
    Pas ahmed@gmail.com
    """
    if not value:
        return
    
    # Liste domaines publics à rejeter
    public_domains = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 
        'outlook.com', 'live.com', 'aol.com',
        'icloud.com', 'mail.com', 'protonmail.com',
        'yopmail.com', 'tempmail.com', 'guerrillamail.com'
    ]
    
    domain = value.split('@')[-1].lower()
    
    if domain in public_domains:
        raise ValidationError(
            _(f'Veuillez utiliser un email professionnel. '
              f'Les domaines publics ({domain}) ne sont pas acceptés.'),
            code='public_email_domain'
        )


# ═══════════════════════════════════════════════════════════
# URL VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_website_url(value):
    """
    Valide une URL de site web
    
    Explication :
    - Utilise validator Django de base
    - Ajoute validation protocole (http/https)
    - Messages d'erreur personnalisés
    
    Formats acceptés :
    - https://example.com
    - http://www.example.com
    - https://subdomain.example.com
    
    Formats rejetés :
    - example.com (pas de protocole)
    - ftp://example.com (mauvais protocole)
    - javascript:... (XSS attempt)
    """
    if not value:
        return
    
    # Utilise validator Django
    django_validator = DjangoURLValidator(
        schemes=['http', 'https']  # Seulement http/https
    )
    
    try:
        django_validator(value)
    except ValidationError:
        raise ValidationError(
            _('URL invalide. Format attendu : https://example.com'),
            code='invalid_url'
        )
    
    # Validation additionnelle : doit commencer par http:// ou https://
    if not value.startswith(('http://', 'https://')):
        raise ValidationError(
            _('L\'URL doit commencer par http:// ou https://'),
            code='missing_protocol'
        )


# ═══════════════════════════════════════════════════════════
# INDUSTRY VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_industry(value):
    """
    Valide le secteur d'activité
    
    Explication :
    Vérifie que le secteur est dans la liste prédéfinie
    """
    from .models import Industry
    
    valid_industries = [choice[0] for choice in Industry.choices]
    
    if value not in valid_industries:
        raise ValidationError(
            _(f'Secteur d\'activité invalide. Valeurs autorisées : {", ".join(valid_industries)}'),
            code='invalid_industry'
        )


# ═══════════════════════════════════════════════════════════
# COMPOSITE VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_client_data(data):
    """
    Validation composite de toutes les données client
    
    Explication :
    Valide plusieurs champs ensemble
    Vérifie cohérence globale
    
    Use case :
    Appelé avant création/mise à jour client
    Valide tout en une fois
    
    Returns:
        dict: Données nettoyées et validées
    
    Raises:
        ValidationError: Si données invalides
    """
    errors = {}
    
    # Valide email (si fourni)
    if 'email' in data and data['email']:
        try:
            validate_business_email(data['email'])
        except ValidationError as e:
            errors['email'] = e.messages
    
    # Valide téléphone (si fourni)
    if 'phone' in data and data['phone']:
        try:
            validate_phone_number(data['phone'])
        except ValidationError as e:
            errors['phone'] = e.messages
    
    # Valide site web (si fourni)
    if 'website' in data and data['website']:
        try:
            validate_website_url(data['website'])
        except ValidationError as e:
            errors['website'] = e.messages

    # Valide secteur (si fourni)
    if 'industry' in data and data['industry']:
        try:
            validate_industry(data['industry'])
        except ValidationError as e:
            errors['industry'] = e.messages
    
    # Si erreurs, lève ValidationError avec tous les messages
    if errors:
        raise ValidationError(errors)
    
    return data


# ═══════════════════════════════════════════════════════════
# CONTACT VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_contact_data(data, client=None):
    """
    Valide les données d'un contact
    
    Args:
        data: Données du contact
        client: Client associé (pour validation is_primary)
    
    Explication :
    - Valide email, téléphone
    - Vérifie qu'il n'y a qu'un seul contact principal
    """
    errors = {}
    
    # Valide email
    if 'email' in data and data['email']:
        try:
            # Contact peut avoir email public (moins strict)
            from django.core.validators import validate_email
            validate_email(data['email'])
        except ValidationError as e:
            errors['email'] = e.messages
    
    # Valide téléphone (si fourni)
    if 'phone' in data and data['phone']:
        try:
            validate_phone_number(data['phone'])
        except ValidationError as e:
            errors['phone'] = e.messages
    
    # Valide contact principal unique
    if data.get('is_primary') and client:
        from .models import Contact
        
        # Vérifie s'il existe déjà un contact principal
        existing_primary = Contact.objects.filter(
            client=client,
            is_primary=True
        ).exclude(
            id=data.get('id')  # Exclut contact actuel si update
        ).exists()
        
        if existing_primary:
            errors['is_primary'] = [
                _('Un contact principal existe déjà pour ce client')
            ]
    
    if errors:
        raise ValidationError(errors)
    
    return data


# ═══════════════════════════════════════════════════════════
# UTILITY VALIDATORS
# ═══════════════════════════════════════════════════════════

def normalize_phone_number(value):
    """
    Normalise un numéro de téléphone
    
    Explication :
    Transforme différents formats vers format standard
    
    Input : "+216 12 345 678", "12-345-678", "12345678"
    Output : "+21612345678"
    
    Use case :
    Avant stockage en DB
    Facilite comparaisons et recherches
    """
    if not value:
        return value
    
    # Nettoie tous les séparateurs
    cleaned = re.sub(r'[\s\-\(\)]', '', value)
    
    # Ajoute +216 si manquant
    if not cleaned.startswith('+'):
        if cleaned.startswith('00'):
            cleaned = '+' + cleaned[2:]
        elif cleaned.startswith('216'):
            cleaned = '+' + cleaned
        else:
            cleaned = '+216' + cleaned
    
    return cleaned


