from django import template

register = template.Library() 

@register.filter(name='has_group') 
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists() 

@register.filter(name='announcement_has_group')
def announcement_has_group(announcement, group_name):
    return announcement.groups.filter(name=group_name).exists() 