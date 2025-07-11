from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])

@register.filter
def get_range(start, end):
    return range(start, end)

@register.filter
def avatar_color(user):
    # Retourne une couleur Bootstrap selon la première lettre du prénom ou username
    if not user:
        return 'bg-secondary'
    initial = (user.first_name or user.username or '').strip().upper()[:1]
    if initial in 'AEIOU':
        return 'bg-info'
    elif initial in 'BCDFG':
        return 'bg-success'
    elif initial in 'HJKLM':
        return 'bg-primary'
    elif initial in 'NPQRST':
        return 'bg-warning'
    else:
        return 'bg-secondary' 